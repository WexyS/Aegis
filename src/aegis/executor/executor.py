# src/aegis/executor/executor.py

import time
import asyncio
import pygetwindow as gw
import logging

from aegis.core.app_map import get_app_config, refresh_installed_app_registry, resolve_app_name
from aegis.executor.utils import (
    smart_match_app,
    verify_path,
    get_running_pids,
    score_window,
    is_process_alive,
    get_window_pid,
)
from aegis.core.schemas import IntentResult, ActionResult, ExecutionEvidence, ReliabilityMetrics
from aegis.core.constants import ActionStatus, ExecutionMode
from aegis.tools.registry import TOOLS

logger = logging.getLogger(__name__)


def _now_ms() -> int:
    return int(time.time() * 1000)


def _window_evidence(window) -> dict | None:
    if window is None:
        return None
    hwnd = getattr(window, "_hWnd", None)
    pid = None
    if hwnd is not None:
        try:
            pid = get_window_pid(hwnd)
        except Exception:
            pid = None
    return {
        "title": getattr(window, "title", "") or "",
        "hwnd": hwnd,
        "pid": pid,
        "is_minimized": bool(getattr(window, "isMinimized", False)),
    }


def _make_open_app_evidence(
    *,
    target: str,
    method: str,
    started_at_ms: int,
    launch_target: str | None,
    resolved_path: str | None,
    process_name: str | None,
    pids: list[int] | None = None,
    process_alive: bool | None = None,
    window: dict | None = None,
    verification_state: str = "unverified",
    retry_count: int = 0,
    recovery_triggered: bool = False,
    attempts: list[dict] | None = None,
    fallback_chain: list[dict] | None = None,
    warnings: list[str] | None = None,
) -> ExecutionEvidence:
    return ExecutionEvidence(
        action="open_app",
        target=target,
        target_type="application",
        method=method,
        verification_state=verification_state,
        started_at_ms=started_at_ms,
        completed_at_ms=_now_ms(),
        launch_target=launch_target,
        resolved_path=resolved_path,
        process_name=process_name,
        pids=list(pids or []),
        process_alive=process_alive,
        window=window,
        retry_count=retry_count,
        recovery_triggered=recovery_triggered,
        attempts=list(attempts or []),
        fallback_chain=list(fallback_chain or []),
        warnings=list(warnings or []),
    )


def _result_with_evidence(
    *,
    action: str,
    params: dict,
    status: ActionStatus,
    success: bool,
    output: str,
    evidence: ExecutionEvidence,
    focus_verified: bool = False,
    metrics: ReliabilityMetrics | None = None,
) -> ActionResult:
    return ActionResult(
        action=action,
        params=params,
        status=status,
        success=success,
        output=output,
        focus_verified=focus_verified,
        proof={"execution_evidence": evidence.model_dump()},
        execution_evidence=evidence,
        metrics=metrics or ReliabilityMetrics(),
    )


def _standard_tool_evidence(
    *,
    action: str,
    params: dict,
    output: str,
    status: ActionStatus,
    started_at_ms: int,
) -> ExecutionEvidence:
    target = (
        params.get("path")
        or params.get("url")
        or params.get("query")
        or params.get("selector")
        or params.get("command")
        or action
    )
    read_only_actions = {"read_file", "list_directory", "search_files", "grep_in_files", "file_info", "read_page", "search_web"}
    verification_state = "failed" if status == ActionStatus.FAILED else "verified" if action in read_only_actions else "unverified"
    warnings = [] if verification_state == "verified" else ["Legacy executor output is not treated as verified side-effect proof."]
    return ExecutionEvidence(
        action=action,
        target=str(target),
        target_type="read_only" if action in read_only_actions else "tool",
        method="legacy_tool_output",
        verification_state=verification_state,
        started_at_ms=started_at_ms,
        completed_at_ms=_now_ms(),
        warnings=warnings,
        observed={
            "output_bytes": len(output.encode("utf-8")),
            "output_prefix": output[:120],
        },
    )


class Executor:
    def __init__(self, safety, dry_run_default=None):
        from aegis.core.config import get_settings
        settings = get_settings()
        
        self._safety = safety
        # Pull from config with a safe fallback
        self._safe_mode = getattr(settings.safety, "safe_mode", True)
        
        # If dry_run_default not provided, pull from config
        if dry_run_default is None:
            self._dry_run_default = getattr(settings.safety, "dry_run_default", True)
        else:
            self._dry_run_default = dry_run_default
            
        self._page = None
        self._browser = None
        self._playwright = None

    async def execute(self, intent: IntentResult, mode: ExecutionMode) -> list[ActionResult]:
        """Generic execution entry point with single-source-of-truth logic."""
        dry_run = self._resolve_mode(mode)
        tool_name = intent.intent
        params = intent.params or {}
        
        # Resolve context early to prevent NameError in open_app branch
        context = {"dry_run": dry_run}
        if tool_name in ["open_url", "click", "scroll", "read_page"]:
            context["page"] = await self._get_page()

        logger.debug("[EXECUTOR] Action requested: %s %s", tool_name, params)

        # 0. SAFETY CHECK
        guard_result = self._safety.evaluate(intent)
        if not guard_result.allowed:
            logger.warning("[EXECUTOR] Safety Block: %s", guard_result.reason)
            return [ActionResult(
                action=tool_name, params=params, status=ActionStatus.BLOCKED,
                success=False,
                output=f"Safety Violation: {guard_result.reason}"
            )]

        # ---------------------------------------------------------
        # 1. SPECIAL CASE: open_app (High-Reliability Pipeline)
        # ---------------------------------------------------------
        if tool_name == "open_app" and "app" in params:
            original_query = params["app"]
            visited = set()
            started_at_ms = _now_ms()
            fallback_chain: list[dict] = []
            
            # Resolution Loop (alias + fuzzy + fallback)
            resolved = resolve_app_name(original_query) or smart_match_app(original_query)
            if not resolved:
                refresh_installed_app_registry()
                resolved = resolve_app_name(original_query) or smart_match_app(original_query)
            
            while resolved:
                if resolved in visited:
                    return [ActionResult(action=tool_name, params=params, status=ActionStatus.FAILED, 
                                        success=False,
                                        output=f"Error: Fallback loop detected for '{resolved}'")]
                visited.add(resolved)
                
                config = get_app_config(resolved)
                if not config:
                    return [ActionResult(action=tool_name, params=params, status=ActionStatus.FAILED, 
                                        success=False,
                                        output=f"Error: Unknown application metadata for '{resolved}'")]
                
                path = config.get("path")
                process_name = config.get("process_name")
                keywords = config.get("window_keywords", [resolved])
                fallback = config.get("fallback")
                
                # A. Path Verification (Senior Model: Resolve Real Path)
                is_valid, resolved_path = verify_path(path)
                logger.debug("[EXECUTOR] verify_path result: %s | resolved: %s", is_valid, resolved_path)
                
                if not is_valid:
                    if fallback:
                        logger.info("[EXECUTOR] Fallback: %s -> %s", resolved, fallback)
                        fallback_chain.append({
                            "from": resolved,
                            "to": fallback,
                            "reason": "invalid_path",
                            "path": path,
                        })
                        resolved = fallback
                        continue
                    return [ActionResult(action=tool_name, params=params, status=ActionStatus.FAILED, 
                                        success=False,
                                        output=f"Error: Application path invalid and no fallback found for '{resolved}'")]
                
                # Update path with the resolved absolute path
                if resolved_path:
                    path = resolved_path
                
                # B. Focus-First (Ranked & PID-Verified)
                pids = get_running_pids(process_name) if process_name else []
                candidates = []
                for w in gw.getAllWindows():
                    if any(k.lower() in (w.title or "").lower() for k in keywords):
                        score = score_window(w, pids)
                        if score > 0:
                            candidates.append((score, w))
                
                candidates.sort(key=lambda x: x[0], reverse=True)
                
                if candidates:
                    best_win = candidates[0][1]
                    logger.debug("[EXECUTOR] Ranking match: %r (score=%s)", best_win.title, candidates[0][0])
                    
                    try:
                        if best_win.isMinimized: best_win.restore()
                        best_win.activate()
                        
                        # Elite Stabilization (Race Condition Fix)
                        for _ in range(10):
                            active = gw.getActiveWindow()
                            if active and active._hWnd == best_win._hWnd:
                                break
                            await asyncio.sleep(0.15)
                        
                        # Micro delay for input readiness
                        await asyncio.sleep(0.1)

                        current_pids = get_running_pids(process_name) if process_name else []
                        window = _window_evidence(best_win)
                        evidence = _make_open_app_evidence(
                            target=resolved,
                            method="focus_existing_window",
                            started_at_ms=started_at_ms,
                            launch_target=path,
                            resolved_path=resolved_path,
                            process_name=process_name,
                            pids=current_pids,
                            process_alive=bool(current_pids) if process_name else None,
                            window=window,
                            verification_state="verified",
                            recovery_triggered=bool(fallback_chain),
                            fallback_chain=fallback_chain,
                        )
                        return [_result_with_evidence(
                            action=tool_name,
                            params=params,
                            status=ActionStatus.EXECUTED,
                            success=True,
                            output=f"I've found and focused your open '{resolved}' window.",
                            evidence=evidence,
                            focus_verified=True,
                            metrics=ReliabilityMetrics(recovery_triggered=bool(fallback_chain)),
                        )]
                    except Exception as e:
                        logger.warning("[EXECUTOR] Focus failed: %s", e)

                # C. Launch Handover (Dumb Tool Call)
                params["_resolved_path"] = path
                params["_keywords"] = keywords
                params["_process_name"] = process_name
                params["app"] = resolved 
                
                tool = TOOLS.get(tool_name)
                logger.debug("[EXECUTOR] Calling tool: %s", tool_name)
                
                # Use Self-Healing Engine to wrap the tool execution
                from aegis.core.self_healing import get_self_healer
                max_launch_attempts = 2 if process_name else 1
                launch_attempts: list[dict] = []
                warnings: list[str] = []
                output_str = ""
                post_launch_pids: list[int] = []
                process_alive = None
                is_failed = False
                verification_state = "unverified"
                retry_count = 0

                for launch_attempt in range(max_launch_attempts):
                    results = await get_self_healer().run(tool.run, **params, **context)
                    output_str = results if isinstance(results, str) else results[0].output

                    # Post-launch survival check
                    await asyncio.sleep(0.3)
                    post_launch_pids = get_running_pids(process_name) if process_name else []
                    process_alive = None
                    if process_name:
                        process_alive = bool(post_launch_pids) or is_process_alive(process_name)
                    elif "No process_name configured; launch cannot be process-verified." not in warnings:
                        warnings.append("No process_name configured; launch cannot be process-verified.")

                    if process_name and not process_alive:
                        output_str = f"Error: '{resolved}' process crashed after launch."

                    # Elite Inclusive Failure Check
                    is_failed = "error" in output_str.lower() or "failed" in output_str.lower()
                    verification_state = "failed" if is_failed else "unverified"
                    if not is_failed and process_alive:
                        verification_state = "verified"

                    launch_attempts.append({
                        "attempt": launch_attempt + 1,
                        "target": resolved,
                        "process_name": process_name,
                        "pids": list(post_launch_pids),
                        "process_alive": process_alive,
                        "verification_state": verification_state,
                        "output": output_str,
                    })

                    if process_name and not process_alive and launch_attempt < max_launch_attempts - 1:
                        retry_count += 1
                        warnings.append("Retrying launch after missing process verification.")
                        continue
                    break

                if is_failed and fallback:
                    logger.info("[EXECUTOR] Runtime fallback: %s -> %s", resolved, fallback)
                    fallback_chain.append({
                        "from": resolved,
                        "to": fallback,
                        "reason": "launch_failed",
                        "path": path,
                    })
                    resolved = fallback
                    continue

                status = ActionStatus.FAILED if is_failed else ActionStatus.EXECUTED
                recovery_triggered = retry_count > 0 or bool(fallback_chain)
                evidence = _make_open_app_evidence(
                    target=resolved,
                    method="launch",
                    started_at_ms=started_at_ms,
                    launch_target=path,
                    resolved_path=resolved_path,
                    process_name=process_name,
                    pids=post_launch_pids,
                    process_alive=process_alive,
                    window=None,
                    verification_state=verification_state,
                    retry_count=retry_count,
                    recovery_triggered=recovery_triggered,
                    attempts=launch_attempts,
                    fallback_chain=fallback_chain,
                    warnings=warnings,
                )
                return [_result_with_evidence(
                    action=tool_name,
                    params=params,
                    status=status,
                    success=status == ActionStatus.EXECUTED,
                    output=output_str,
                    evidence=evidence,
                    metrics=ReliabilityMetrics(retries=retry_count, recovery_triggered=recovery_triggered),
                )]
            
            return [ActionResult(action=tool_name, params=params, status=ActionStatus.FAILED, 
                                success=False,
                                output=f"Error: Could not resolve or launch '{original_query}'")]

        # 2. STANDARD TOOL EXECUTION
        # ---------------------------------------------------------
        tool = TOOLS.get(tool_name)
        if not tool:
            return [ActionResult(action=tool_name, params=params, status=ActionStatus.FAILED, 
                                success=False,
                                output=f"Error: Unknown tool '{tool_name}'")]

        try:
            logger.info("[EXECUTOR] Running tool: %s", tool_name)
            started_at_ms = _now_ms()
            output = await tool.run(**params, **context)
            output_text = str(output)
            
            status = ActionStatus.FAILED if output_text.strip().lower().startswith(("error", "failed", "read error", "write error")) else ActionStatus.EXECUTED
            evidence = _standard_tool_evidence(
                action=tool_name,
                params=params,
                output=output_text,
                status=status,
                started_at_ms=started_at_ms,
            )
            return [ActionResult(
                action=tool_name,
                params=params,
                status=status,
                success=status == ActionStatus.EXECUTED,
                output=output_text,
                proof={"execution_evidence": evidence.model_dump()},
                execution_evidence=evidence,
            )]
            
        except Exception as e:
            logger.error("[EXECUTOR] Fatal error in tool %s: %s", tool_name, e)
            evidence = _standard_tool_evidence(
                action=tool_name,
                params=params,
                output=str(e),
                status=ActionStatus.FAILED,
                started_at_ms=_now_ms(),
            )
            return [ActionResult(
                action=tool_name,
                params=params,
                status=ActionStatus.FAILED,
                success=False,
                output=str(e),
                proof={"execution_evidence": evidence.model_dump()},
                execution_evidence=evidence,
            )]

    async def _get_page(self):
        if self._page: return self._page
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

    def _resolve_mode(self, mode: ExecutionMode) -> bool:
        if self._safe_mode or mode == ExecutionMode.DRY_RUN: return True
        if mode == ExecutionMode.LIVE: return False
        return self._dry_run_default

    async def close(self):
        if hasattr(self, '_context') and self._context:
            await self._context.close()
        if self._browser: await self._browser.close()
        if self._playwright: await self._playwright.stop()


# Singleton
_executor: Executor | None = None


def get_executor() -> Executor:
    """DEPRECATED: Use get_deterministic_executor() instead.

    This redirects to the DeterministicExecutor to prevent any code path
    from accidentally bypassing formal verification, transition model,
    and evidence-based execution guarantees.
    """
    import warnings
    from aegis.executor.deterministic_executor import get_deterministic_executor
    warnings.warn(
        "get_executor() is deprecated. Use get_deterministic_executor() for "
        "formal verification and deterministic execution guarantees.",
        DeprecationWarning,
        stacklevel=2,
    )
    return get_deterministic_executor()
