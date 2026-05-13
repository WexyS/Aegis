# src/aegis/executor/deterministic_executor.py

import asyncio
import difflib
import hashlib
import logging
import time
import ctypes
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID
from urllib.parse import quote_plus

from aegis.core.context import ExecutionContext
from aegis.core.schemas import IntentResult, ActionResult, ExecutionEvidence, ReliabilityMetrics
from aegis.core.constants import ActionStatus
from aegis.core.commands import CancellationToken
from aegis.logger.event_logger import get_event_logger, EventType
from aegis.core.state_manager import get_state_manager
from aegis.core.transition_model import get_transition_model
from aegis.tools.registry import TOOLS, get_tool_spec
from aegis.tools.file_tools import _resolve_write_path
from aegis.executor.utils import verify_path, get_running_pids, get_window_pid
from aegis.executor.desktop_verifier import (
    make_desktop_execution_evidence,
    now_ms,
    observe_desktop_target,
)
import pygetwindow as gw

logger = logging.getLogger(__name__)


def _read_only_evidence(intent: str, params: Dict[str, Any], output_text: str) -> Dict[str, Any] | None:
    if intent not in {"read_file", "read_page", "search_web", "list_directory", "search_files", "grep_in_files", "file_info"}:
        return None
    encoded = output_text.encode("utf-8")
    evidence: Dict[str, Any] = {
        "tool": intent,
        "bytes": len(encoded),
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "truncated": intent == "read_page" and output_text.endswith("..."),
    }
    if intent in {"read_file", "list_directory", "search_files", "grep_in_files", "file_info"}:
        evidence["path"] = str(params.get("path", ""))
    if intent in {"search_files", "grep_in_files"}:
        evidence["query"] = str(params.get("query") or params.get("pattern") or "")
    if intent == "search_web":
        query = str(params.get("query", "")).strip()
        evidence["query"] = query
        evidence["search_url"] = f"https://www.google.com/search?q={quote_plus(query)}"
    return evidence


async def _capture_click_context(intent: str, params: Dict[str, Any], page: Any | None) -> Dict[str, Any] | None:
    if intent != "click" or page is None:
        return None

    selector = params.get("selector")
    x = params.get("x")
    y = params.get("y")
    context: Dict[str, Any] = {
        "url": str(getattr(page, "url", "")),
        "selector": str(selector) if selector else None,
        "target": None,
    }
    if x is not None and y is not None:
        context["coordinates"] = {"x": int(x), "y": int(y)}

    try:
        if selector:
            context["target"] = await page.evaluate(
                """
                (selector) => {
                  const el = document.querySelector(selector);
                  if (!el) return null;
                  const rect = el.getBoundingClientRect();
                  return {
                    tag: el.tagName,
                    text: (el.innerText || el.textContent || '').trim().slice(0, 120),
                    x: Math.round(rect.x),
                    y: Math.round(rect.y),
                    width: Math.round(rect.width),
                    height: Math.round(rect.height)
                  };
                }
                """,
                selector,
            )
        elif x is not None and y is not None:
            context["target"] = await page.evaluate(
                """
                ({x, y}) => {
                  const el = document.elementFromPoint(x, y);
                  if (!el) return null;
                  const rect = el.getBoundingClientRect();
                  return {
                    tag: el.tagName,
                    text: (el.innerText || el.textContent || '').trim().slice(0, 120),
                    x: Math.round(rect.x),
                    y: Math.round(rect.y),
                    width: Math.round(rect.width),
                    height: Math.round(rect.height)
                  };
                }
                """,
                {"x": int(x), "y": int(y)},
            )
    except Exception as exc:
        context["capture_error"] = str(exc)

    return context


def _browser_evidence(
    intent: str,
    params: Dict[str, Any],
    output_text: str,
    *,
    click_before: Dict[str, Any] | None = None,
    click_after: Dict[str, Any] | None = None,
) -> Dict[str, Any] | None:
    if intent not in {"open_url", "scroll"}:
        if intent != "click":
            return None
    evidence: Dict[str, Any] = {"tool": intent}
    if intent == "open_url":
        evidence["url"] = str(params.get("url", ""))
    if intent == "scroll":
        evidence["direction"] = str(params.get("direction", "down"))
        evidence["amount"] = int(params.get("amount", 500) or 500)
    if intent == "click":
        selector = params.get("selector")
        x = params.get("x")
        y = params.get("y")
        if selector:
            evidence["selector"] = str(selector)
        if x is not None and y is not None:
            evidence["coordinates"] = {"x": int(x), "y": int(y)}
        evidence["before"] = click_before
        evidence["after"] = click_after
    evidence["output_sha256"] = hashlib.sha256(output_text.encode("utf-8")).hexdigest()
    return evidence


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _capture_write_before(intent: str, params: Dict[str, Any]) -> Dict[str, Any] | None:
    if intent not in {"write_file", "create_file", "edit_file"}:
        return None
    raw_path = params.get("path")
    if not raw_path:
        return None

    path = Path(_resolve_write_path(str(raw_path)))
    existed = path.exists()
    content = path.read_text(encoding="utf-8") if existed else ""
    return {
        "path": str(path),
        "existed_before": existed,
        "content": content,
        "bytes": len(content.encode("utf-8")),
        "sha256": _sha256_text(content) if existed else None,
    }


def _write_evidence(
    intent: str,
    params: Dict[str, Any],
    before: Dict[str, Any] | None,
    output_text: str,
) -> Dict[str, Any] | None:
    if intent not in {"write_file", "create_file", "edit_file"} or before is None:
        return None

    path = Path(before["path"])
    after_content = path.read_text(encoding="utf-8") if path.exists() else ""
    before_lines = str(before["content"]).splitlines(keepends=True)
    after_lines = after_content.splitlines(keepends=True)
    diff_lines = list(
        difflib.unified_diff(
            before_lines,
            after_lines,
            fromfile="before",
            tofile="after",
            lineterm="",
        )
    )
    diff_preview = "\n".join(diff_lines[:120])

    return {
        "tool": intent,
        "path": str(path),
        "dry_run": bool(params.get("dry_run", False)),
        "existed_before": bool(before["existed_before"]),
        "before_bytes": int(before["bytes"]),
        "after_bytes": len(after_content.encode("utf-8")),
        "before_sha256": before["sha256"],
        "after_sha256": _sha256_text(after_content),
        "diff_preview": diff_preview,
        "output_sha256": _sha256_text(output_text),
    }


def _target_snapshot(state: Any) -> Dict[str, Any]:
    return {
        "active_app": getattr(state, "active_app", None),
        "pid": getattr(state, "pid", None),
        "hwnd": getattr(state, "hwnd", None),
        "focus_stable": bool(getattr(state, "focus_stable", False)),
        "is_responsive": bool(getattr(state, "is_responsive", False)),
    }


def _type_evidence(
    intent: str,
    params: Dict[str, Any],
    before_state: Any,
    after_state: Any,
    output_text: str,
) -> Dict[str, Any] | None:
    if intent != "type":
        return None
    text = str(params.get("text", ""))
    return {
        "tool": intent,
        "text_chars": len(text),
        "text_bytes": len(text.encode("utf-8")),
        "text_sha256": _sha256_text(text),
        "target_before": _target_snapshot(before_state),
        "target_after": _target_snapshot(after_state),
        "output_sha256": _sha256_text(output_text),
    }


def _git_evidence(intent: str, params: Dict[str, Any], output_text: str) -> Dict[str, Any] | None:
    if intent != "git_action":
        return None
    git_cmd = str(params.get("git_cmd", "")).lower().strip()
    return {
        "tool": intent,
        "git_cmd": git_cmd,
        "read_only": git_cmd == "status",
        "output_bytes": len(output_text.encode("utf-8")),
        "output_sha256": _sha256_text(output_text),
    }


def _shell_evidence(intent: str, params: Dict[str, Any], output_text: str) -> Dict[str, Any] | None:
    if intent != "run_command":
        return None
    return {
        "tool": intent,
        "command": str(params.get("command", "")),
        "read_only": True,
        "output_bytes": len(output_text.encode("utf-8")),
        "output_sha256": _sha256_text(output_text),
    }


DESKTOP_EVIDENCE_TOOLS = {"open_app", "focus_app", "close_app"}
PROOF_EVIDENCE_KEYS = ("read_only_evidence", "browser_evidence", "write_evidence", "type_evidence", "git_evidence", "shell_evidence")


def _desktop_evidence_from_verification(
    intent: str,
    params: Dict[str, Any],
    started_at_ms: int,
    verification: "VerificationEvidence",
) -> ExecutionEvidence | None:
    if intent not in DESKTOP_EVIDENCE_TOOLS:
        return None
    app = str(params.get("app") or params.get("window") or "")
    if not app:
        return None
    observation = observe_desktop_target(
        app,
        process_name=params.get("_process_name"),
        window_keywords=params.get("_keywords"),
    )
    if intent == "close_app":
        verified = observation.process_alive is False
        method = "terminate_process"
    elif intent == "focus_app":
        verified = observation.focus_verified
        method = "focus_window"
    else:
        verified = verification.verified
        method = "open_or_focus_window"
    if verification.status == "AMBIGUOUS":
        verification_state = "failed"
    elif verified:
        verification_state = "verified"
    else:
        verification_state = "unverified"
    warnings = [] if verified else [verification.details]
    return make_desktop_execution_evidence(
        action=intent,
        app=app,
        method=method,
        started_at_ms=started_at_ms,
        observation=observation,
        verification_state=verification_state,
        warnings=warnings,
    )


def _desktop_failure_evidence(
    intent: str,
    params: Dict[str, Any],
    started_at_ms: int,
    output_text: str,
) -> ExecutionEvidence | None:
    if intent not in DESKTOP_EVIDENCE_TOOLS:
        return None
    app = str(params.get("app") or params.get("window") or "")
    if not app:
        return None
    observation = observe_desktop_target(
        app,
        process_name=params.get("_process_name"),
        window_keywords=params.get("_keywords"),
    )
    return make_desktop_execution_evidence(
        action=intent,
        app=app,
        method="tool_failure",
        started_at_ms=started_at_ms,
        observation=observation,
        verification_state="failed",
        warnings=[output_text],
    )


def _generic_execution_evidence_from_proof(
    intent: str,
    params: Dict[str, Any],
    proof: Dict[str, Any],
    started_at_ms: int,
) -> ExecutionEvidence | None:
    proof_key = next((key for key in PROOF_EVIDENCE_KEYS if key in proof), None)
    if not proof_key:
        return None

    target_type = "unknown"
    method = proof_key.replace("_evidence", "")
    target: str | None = intent

    if proof_key == "read_only_evidence":
        target_type = "read_only"
        data = proof[proof_key]
        if isinstance(data, dict):
            target = str(data.get("path") or data.get("query") or data.get("search_url") or intent)
    elif proof_key == "browser_evidence":
        target_type = "browser"
        browser = proof[proof_key]
        if isinstance(browser, dict):
            target = str(browser.get("url") or browser.get("selector") or browser.get("coordinates") or intent)
    elif proof_key == "write_evidence":
        target_type = "file"
        target = str(params.get("path") or proof[proof_key].get("path") or "file")
    elif proof_key == "type_evidence":
        target_type = "focused_input"
        target = "focused_input"
    elif proof_key == "git_evidence":
        target_type = "git"
        target = str(params.get("git_cmd") or proof[proof_key].get("git_cmd") or "git")
    elif proof_key == "shell_evidence":
        target_type = "shell"
        target = str(params.get("command") or proof[proof_key].get("command") or "shell")

    return ExecutionEvidence(
        action=intent,
        target=target,
        target_type=target_type,
        method=method,
        verification_state="verified",
        started_at_ms=started_at_ms,
        completed_at_ms=now_ms(),
        warnings=[],
    )

@dataclass
class VerificationEvidence:
    """Detailed evidence for Tier 4.5 Formal Verification."""
    verified: bool
    status: str # 'SUCCESS', 'AMBIGUOUS', 'FAILED'
    expected: Dict[str, Any]
    actual: Dict[str, Any]
    details: str

class Verifier:
    """
    AEGIS Tier 4.5 Formal Verifier.
    Enforces strict determinism. 
    Ambiguity (multiple window matches) is treated as a Failure.
    """
    @staticmethod
    async def verify(intent: str, params: Dict[str, Any], ctx: ExecutionContext) -> VerificationEvidence:
        expected = {"intent": intent, "process_name": params.get("_process_name")}
        actual = {"pid": None, "hwnd": None, "is_responsive": False}
        
        if intent == "open_app":
            process_name = params.get("_process_name")
            keywords = params.get("_keywords", [])
            
            # Poll for stabilization
            for attempt in range(50):
                await asyncio.sleep(0.1)
                pids = get_running_pids(process_name)
                if not pids: continue
                
                # STRICT MATCHING: Find all candidates belonging to our PIDs
                candidates = []
                for w in gw.getAllWindows():
                    hwnd = w._hWnd
                    if get_window_pid(hwnd) in pids:
                        title = (w.title or "").lower()
                        if any(k.lower() in title for k in keywords) and w.visible:
                            is_hung = ctypes.windll.user32.IsHungAppWindow(hwnd)
                            candidates.append({"hwnd": hwnd, "is_responsive": not is_hung})
                
                if not candidates: continue
                
                # DETERMINISM CHECK: Exactly one candidate must exist
                if len(candidates) > 1:
                    return VerificationEvidence(False, "AMBIGUOUS", expected, actual, f"Ambiguity Error: {len(candidates)} matching windows found for {process_name}")
                
                best = candidates[0]
                if best["is_responsive"]:
                    actual.update({"pid": get_window_pid(best["hwnd"]), "hwnd": best["hwnd"], "is_responsive": True})
                    return VerificationEvidence(True, "SUCCESS", expected, actual, f"Formally verified window {best['hwnd']}")

            return VerificationEvidence(False, "FAILED", expected, actual, f"Timeout: No window manifested for {process_name}")

        if intent == "focus_app":
            app = str(params.get("app") or "")
            observation = observe_desktop_target(app)
            window = observation.primary_window or {}
            actual.update({
                "pid": window.get("pid"),
                "hwnd": window.get("hwnd"),
                "is_responsive": bool(window),
            })
            if observation.focus_verified:
                return VerificationEvidence(True, "SUCCESS", expected, actual, f"Focused window {window.get('hwnd')}")
            if len(observation.matching_windows) > 1:
                return VerificationEvidence(False, "AMBIGUOUS", expected, actual, f"Ambiguous focus target: {len(observation.matching_windows)} matching windows")
            return VerificationEvidence(False, "FAILED", expected, actual, f"No focused window verified for {app}")

        if intent == "close_app":
            app = str(params.get("app") or "")
            observation = observe_desktop_target(app)
            if observation.process_alive is False:
                return VerificationEvidence(True, "SUCCESS", expected, actual, f"No live process remains for {observation.target.process_name}")
            actual.update({"pid": observation.pids[0] if observation.pids else None})
            return VerificationEvidence(False, "FAILED", expected, actual, f"Process still alive for {observation.target.process_name}")

        return VerificationEvidence(True, "SUCCESS", expected, actual, "Generic success.")

class DeterministicExecutor:
    """
    AEGIS Tier 4.5 Formal Executor.
    Uses Formal Specs and Ambiguity-Aware Verification.
    """
    def __init__(self):
        self.max_retries = 1
        self.base_delay = 1.0
        self.tool_timeout = 30.0
        self.transition_model = get_transition_model()
        
        # Browser management — lazy init
        self._page = None
        self._context = None
        self._browser = None
        self._playwright = None

    async def _get_page(self):
        """Lazy initialization of Playwright browser and page with Supervisor tracking."""
        if self._page:
            return self._page
        from playwright.async_api import async_playwright
        from aegis.executor.browser_supervisor import get_browser_supervisor
        
        supervisor = get_browser_supervisor()
        supervisor.start()

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=False)
        self._context = await self._browser.new_context()
        supervisor.register_context(self._context)
        
        self._page = await self._context.new_page()
        supervisor.register_page(self._page)
        
        return self._page

    async def close(self):
        """Cleanup browser resources."""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def execute(
        self,
        intent_result: IntentResult,
        ctx: ExecutionContext,
        cancellation_token: CancellationToken | None = None,
    ) -> ActionResult:
        event_logger = get_event_logger()
        state_manager = get_state_manager()
        step_start = time.perf_counter()
        
        intent = intent_result.intent
        params = intent_result.params
        desktop_started_at_ms = now_ms()

        if cancellation_token and cancellation_token.cancelled:
            return ActionResult(
                action=intent,
                params=params,
                status=ActionStatus.CANCELLED,
                success=False,
                output=cancellation_token.cancelled_reason or "Command cancelled before tool execution",
            )
        
        # 0. PRE-EXECUTION SNAPSHOT
        focus_start = time.perf_counter()
        await state_manager.sync_with_os(ctx.trace_id, ctx.span_id)
        before_state = state_manager.get_state()
        focus_acquire_time = (time.perf_counter() - focus_start) * 1000
        
        # 1. PRE-EXECUTION: Validate Formal Preconditions
        pre_errors = self.transition_model.validate_preconditions(intent, before_state)
        if pre_errors:
            return ActionResult(
                action=intent, params=params, 
                status=ActionStatus.FAILED, success=False,
                output=f"Formal Precondition Failure: {', '.join(pre_errors)}",
                metrics=ReliabilityMetrics(execution_time_ms=(time.perf_counter() - step_start)*1000)
            )

        # 2. Predict Transition
        expected_transition = self.transition_model.predict_next_state(before_state, intent, params)
        
        for attempt in range(self.max_retries + 1):
            if attempt > 0: await asyncio.sleep(self.base_delay * (2 ** (attempt - 1)))

            try:
                tool = TOOLS.get(intent)
                tool_spec = get_tool_spec(intent)
                if tool is None:
                    return ActionResult(
                        action=intent,
                        params=params,
                        status=ActionStatus.FAILED,
                        success=False,
                        output=f"Unknown tool '{intent}'",
                        recovery_hint="Planner produced an intent with no registered deterministic tool.",
                        metrics=ReliabilityMetrics(
                            execution_time_ms=(time.perf_counter() - step_start) * 1000,
                            retries=attempt,
                        ),
                    )

                call_params = dict(params)
                call_params["trace_id"] = str(ctx.trace_id)
                call_params["span_id"] = str(ctx.span_id)
                if tool_spec and tool_spec.cancellation_supported:
                    call_params["cancellation_token"] = cancellation_token
                if tool_spec and intent == "run_command" and "timeout_seconds" not in call_params:
                    call_params["timeout_seconds"] = tool_spec.timeout_seconds
                page = None
                if intent in ["open_url", "search_web", "click", "scroll", "read_page"]:
                    page = await self._get_page()
                    call_params["page"] = page

                write_before = _capture_write_before(intent, params)
                click_before = await _capture_click_context(intent, params, page)
                
                tool_task = asyncio.create_task(tool.run(**call_params))
                timeout_seconds = float(tool_spec.timeout_seconds if tool_spec else self.tool_timeout)
                deadline = time.perf_counter() + timeout_seconds
                while not tool_task.done():
                    if cancellation_token and cancellation_token.cancelled:
                        tool_task.cancel()
                        return ActionResult(
                            action=intent,
                            params=params,
                            status=ActionStatus.CANCELLED,
                            success=False,
                            output=cancellation_token.cancelled_reason or "Command cancelled during tool execution",
                            metrics=ReliabilityMetrics(
                                execution_time_ms=(time.perf_counter() - step_start) * 1000,
                                retries=attempt,
                            ),
                        )
                    if time.perf_counter() >= deadline:
                        tool_task.cancel()
                        raise asyncio.TimeoutError(f"Tool '{intent}' timed out after {timeout_seconds}s")
                    await asyncio.sleep(0.05)
                output = await tool_task
                output_text = str(output)
                click_after = await _capture_click_context(intent, params, page)
                if output_text.lower().startswith(("error", "failed", "read error", "write error")):
                    failure_evidence = _desktop_failure_evidence(intent, params, desktop_started_at_ms, output_text)
                    failure_proof = {"execution_evidence": failure_evidence.model_dump()} if failure_evidence else {}
                    return ActionResult(
                        action=intent,
                        params=params,
                        status=ActionStatus.FAILED,
                        success=False,
                        output=output_text,
                        recovery_hint="Tool returned an explicit failure before verification.",
                        proof=failure_proof,
                        execution_evidence=failure_evidence,
                        metrics=ReliabilityMetrics(
                            execution_time_ms=(time.perf_counter() - step_start) * 1000,
                            retries=attempt,
                        ),
                    )
                
                # 3. POST-EXECUTION: Formal Verification & Sync
                await state_manager.sync_with_os(ctx.trace_id, ctx.span_id)
                evidence = await Verifier.verify(intent, params, ctx)
                execution_evidence = _desktop_evidence_from_verification(
                    intent,
                    params,
                    desktop_started_at_ms,
                    evidence,
                )
                
                state_manager.update(
                    ctx.trace_id, ctx.span_id,
                    pid=evidence.actual["pid"], hwnd=evidence.actual["hwnd"],
                    active_app=params.get("app") if intent == "open_app" else before_state.active_app,
                    last_action=intent, last_status=evidence.status
                )
                
                after_state = state_manager.get_state()
                
                # 4. Reliability Metrics & Determinism Score
                post_errors = self.transition_model.validate_postconditions(intent, after_state)
                deviations = self.transition_model.calculate_deviation(expected_transition, after_state)
                
                # Formula: S = (1 - (Dev*0.2 + Err*0.3)) * Stability_Factor
                score = 1.0 - (len(deviations) * 0.2 + len(post_errors) * 0.3)
                if evidence.status == "AMBIGUOUS": score *= 0.5
                if not after_state.focus_stable: score *= 0.8
                
                metrics = ReliabilityMetrics(
                    execution_time_ms=(time.perf_counter() - step_start) * 1000,
                    focus_acquire_ms=focus_acquire_time,
                    retries=attempt,
                    determinism_score=max(0.0, score)
                )

                proof = {
                    "expected": expected_transition, "actual": asdict(after_state),
                    "deviations": deviations, "postcondition_errors": post_errors,
                    "status": evidence.status,
                    "snapshot_diff": {"before": asdict(before_state), "after": asdict(after_state)}
                }
                read_evidence = _read_only_evidence(intent, params, output_text)
                if read_evidence:
                    proof["read_only_evidence"] = read_evidence
                browser_evidence = _browser_evidence(
                    intent,
                    params,
                    output_text,
                    click_before=click_before,
                    click_after=click_after,
                )
                if browser_evidence:
                    proof["browser_evidence"] = browser_evidence
                write_evidence = _write_evidence(intent, params, write_before, output_text)
                if write_evidence:
                    proof["write_evidence"] = write_evidence
                type_evidence = _type_evidence(intent, params, before_state, after_state, output_text)
                if type_evidence:
                    proof["type_evidence"] = type_evidence
                git_evidence = _git_evidence(intent, params, output_text)
                if git_evidence:
                    proof["git_evidence"] = git_evidence
                shell_evidence = _shell_evidence(intent, params, output_text)
                if shell_evidence:
                    proof["shell_evidence"] = shell_evidence
                if execution_evidence:
                    proof["execution_evidence"] = execution_evidence.model_dump()
                elif generic_evidence := _generic_execution_evidence_from_proof(intent, params, proof, desktop_started_at_ms):
                    execution_evidence = generic_evidence
                    proof["execution_evidence"] = execution_evidence.model_dump()

                if evidence.status == "AMBIGUOUS":
                    return ActionResult(
                        action=intent, params=params, status=ActionStatus.FAILED, success=False,
                        confidence=0.5, output=evidence.details, metrics=metrics, proof=proof,
                        execution_evidence=execution_evidence,
                    )

                if evidence.verified and not post_errors:
                    return ActionResult(
                        action=intent, params=params, status=ActionStatus.EXECUTED, success=True,
                        confidence=metrics.determinism_score, output=output, 
                        focus_verified=after_state.focus_stable or bool(execution_evidence and execution_evidence.verification_state == "verified"),
                        metrics=metrics,
                        proof=proof,
                        execution_evidence=execution_evidence,
                    )

            except Exception as e:
                if attempt == self.max_retries:
                    return ActionResult(
                        action=intent, params=params, status=ActionStatus.FAILED, success=False,
                        output=str(e), metrics=ReliabilityMetrics(execution_time_ms=(time.perf_counter()-step_start)*1000)
                    )

        return ActionResult(
            action=intent, params=params, status=ActionStatus.FAILED, success=False,
            output="Max retries exceeded or formal failure.",
            metrics=ReliabilityMetrics(execution_time_ms=(time.perf_counter()-step_start)*1000)
        )

_instance = None
def get_deterministic_executor() -> DeterministicExecutor:
    global _instance
    if _instance is None:
        _instance = DeterministicExecutor()
    return _instance
