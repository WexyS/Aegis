from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import psutil
import pygetwindow as gw

from aegis.core.app_map import get_app_config, resolve_app_name
from aegis.core.schemas import ExecutionEvidence
from aegis.executor.utils import get_running_pids, get_window_pid

VERIFIER_VERSION = "process-window-verifier/2"


def now_ms() -> int:
    return int(time.time() * 1000)


@dataclass(frozen=True)
class DesktopTarget:
    app_id: str
    display_name: str
    process_name: str | None
    window_keywords: list[str]


@dataclass(frozen=True)
class DesktopObservation:
    target: DesktopTarget
    pids: list[int] = field(default_factory=list)
    process_alive: bool | None = None
    matching_windows: list[dict[str, Any]] = field(default_factory=list)
    active_window: dict[str, Any] | None = None
    focus_verified: bool = False
    observation_errors: list[str] = field(default_factory=list)

    @property
    def primary_window(self) -> dict[str, Any] | None:
        if self.focus_verified and self.active_window:
            return self.active_window
        return self.matching_windows[0] if self.matching_windows else None


@dataclass(frozen=True)
class DesktopVerificationResult:
    action: str
    method: str
    observation: DesktopObservation
    verification_state: str
    reason: str
    checks: list[dict[str, Any]]

    @property
    def verified(self) -> bool:
        return self.verification_state == "verified"

    @property
    def ambiguous(self) -> bool:
        return self.verification_state == "failed" and "ambiguous" in self.reason.lower()


def resolve_desktop_target(
    app: str,
    *,
    process_name: str | None = None,
    window_keywords: list[str] | None = None,
) -> DesktopTarget:
    app_id = resolve_app_name(app) or app.lower().strip()
    config = get_app_config(app_id) or {}
    configured_process = process_name or config.get("process_name")
    keywords = window_keywords or config.get("window_keywords") or [app_id, app]
    if not configured_process and app_id.endswith(".exe"):
        configured_process = app_id
    elif not configured_process and app_id:
        configured_process = f"{app_id}.exe"
    return DesktopTarget(
        app_id=app_id,
        display_name=app,
        process_name=str(configured_process) if configured_process else None,
        window_keywords=[str(keyword) for keyword in keywords if str(keyword).strip()],
    )


def window_evidence(window: Any) -> dict[str, Any] | None:
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
        "visible": bool(getattr(window, "visible", True)),
    }


def observe_desktop_target(
    app: str,
    *,
    process_name: str | None = None,
    window_keywords: list[str] | None = None,
    expected_pids: list[int] | None = None,
) -> DesktopObservation:
    target = resolve_desktop_target(app, process_name=process_name, window_keywords=window_keywords)
    expected_pid_set = {
        int(pid)
        for pid in expected_pids or []
        if isinstance(pid, int) or (isinstance(pid, str) and pid.isdigit())
    }
    if expected_pid_set:
        pids = sorted(pid for pid in expected_pid_set if psutil.pid_exists(pid))
    else:
        pids = get_running_pids(target.process_name) if target.process_name else []
    keywords = [keyword.lower() for keyword in target.window_keywords]
    active = None
    matching: list[dict[str, Any]] = []
    observation_errors: list[str] = []

    try:
        active = gw.getActiveWindow()
    except Exception as exc:
        active = None
        observation_errors.append(f"active_window_unavailable: {exc}")
    active_evidence = window_evidence(active)

    try:
        windows = gw.getAllWindows()
    except Exception as exc:
        windows = []
        observation_errors.append(f"window_list_unavailable: {exc}")

    for window in windows:
        title = (getattr(window, "title", "") or "").lower()
        if keywords and not any(keyword in title for keyword in keywords):
            continue
        evidence = window_evidence(window)
        if not evidence:
            continue
        if pids and evidence.get("pid") not in pids:
            continue
        matching.append(evidence)

    focus_verified = False
    if active_evidence:
        active_hwnd = active_evidence.get("hwnd")
        active_pid = active_evidence.get("pid")
        active_title = str(active_evidence.get("title") or "").lower()
        title_matches = not keywords or any(keyword in active_title for keyword in keywords)
        pid_matches = not pids or active_pid in pids
        focus_verified = bool(active_hwnd and title_matches and pid_matches)

    return DesktopObservation(
        target=target,
        pids=pids,
        process_alive=bool(pids) if target.process_name or expected_pid_set else None,
        matching_windows=matching,
        active_window=active_evidence,
        focus_verified=focus_verified,
        observation_errors=observation_errors,
    )


def _check(name: str, passed: bool | None, expected: Any, observed: Any, reason: str) -> dict[str, Any]:
    return {
        "check_name": name,
        "name": name,
        "passed": passed,
        "expected": expected,
        "observed": observed,
        "actual": observed,
        "reason": reason,
        "detail": reason,
    }


def _observed_snapshot(observation: DesktopObservation) -> dict[str, Any]:
    primary = observation.primary_window or {}
    active = observation.active_window or {}
    return {
        "process_alive": observation.process_alive,
        "pids": list(observation.pids),
        "active_hwnd": active.get("hwnd"),
        "active_pid": active.get("pid"),
        "active_title": active.get("title"),
        "primary_hwnd": primary.get("hwnd"),
        "primary_pid": primary.get("pid"),
        "primary_title": primary.get("title"),
        "matching_window_count": len(observation.matching_windows),
        "focus_verified": observation.focus_verified,
        "observation_errors": list(observation.observation_errors),
    }


def verify_desktop_action(
    *,
    action: str,
    app: str,
    method: str | None = None,
    process_name: str | None = None,
    window_keywords: list[str] | None = None,
    expected_pids: list[int] | None = None,
) -> DesktopVerificationResult:
    """Verify a desktop side effect from process and window observations only."""
    observation = observe_desktop_target(
        app,
        process_name=process_name,
        window_keywords=window_keywords,
        expected_pids=expected_pids,
    )
    target = observation.target
    primary = observation.primary_window
    checks: list[dict[str, Any]] = []
    method = method or {
        "open_app": "open_or_focus_window",
        "focus_app": "focus_window",
        "close_app": "terminate_process",
    }.get(action, "desktop_observation")

    process_known = bool(target.process_name)
    checks.append(_check(
        "process_name_known",
        process_known,
        "configured or inferred process name",
        target.process_name,
        "Process identity is required for deterministic PID/process-alive evidence.",
    ))

    if action == "close_app":
        process_dead = observation.process_alive is False if process_known else None
        checks.append(_check(
            "process_not_alive",
            process_dead,
            False,
            observation.process_alive,
            "Close is verified only when no target process remains alive.",
        ))
        if process_known and process_dead:
            return DesktopVerificationResult(action, method, observation, "verified", "target process is no longer alive", checks)
        reason = "process_name is not configured" if not process_known else "target process is still alive"
        return DesktopVerificationResult(action, method, observation, "unverified", reason, checks)

    window_count = len(observation.matching_windows)
    ambiguous = window_count > 1
    checks.append(_check(
        "single_matching_window",
        not ambiguous,
        "0 or 1 matching window",
        window_count,
        "Multiple matching windows make the desktop target ambiguous.",
    ))

    if action == "focus_app":
        active = observation.active_window or {}
        active_title = str(active.get("title") or "").lower()
        active_pid = active.get("pid")
        active_hwnd = active.get("hwnd")
        title_matches = not target.window_keywords or any(
            keyword.lower() in active_title for keyword in target.window_keywords
        )
        pid_matches = active_pid in observation.pids if observation.pids else None
        checks.append(_check(
            "foreground_hwnd_present",
            bool(active_hwnd),
            "foreground HWND",
            active_hwnd,
            "Focus requires an observable foreground HWND after activation.",
        ))
        checks.append(_check(
            "foreground_title_matches_target",
            title_matches,
            target.window_keywords,
            active.get("title"),
            "Foreground window title must match the target window keywords.",
        ))
        checks.append(_check(
            "foreground_pid_matches_target_process",
            pid_matches,
            observation.pids,
            active_pid,
            "Foreground window PID must belong to the target process PID set.",
        ))
        checks.append(_check(
            "foreground_window_matches_target",
            observation.focus_verified,
            {"title_keywords": target.window_keywords, "pids": observation.pids},
            {"hwnd": active_hwnd, "pid": active_pid, "title": active.get("title")},
            "Focus is verified by foreground HWND, title match, and PID match.",
        ))
        if ambiguous:
            return DesktopVerificationResult(action, method, observation, "failed", f"ambiguous target: {window_count} matching windows", checks)
        if process_known and observation.focus_verified:
            return DesktopVerificationResult(action, method, observation, "verified", "active window matches target process and title", checks)
        reason = "process_name is not configured" if not process_known else "active window did not match target"
        return DesktopVerificationResult(action, method, observation, "unverified", reason, checks)

    process_alive = observation.process_alive is True if process_known else None
    window_present = primary is not None
    checks.append(_check(
        "process_alive",
        process_alive,
        True,
        observation.process_alive,
        "Open is process-verified only when the target process is alive.",
    ))
    checks.append(_check(
        "window_manifested",
        window_present,
        "matching HWND/title",
        {"hwnd": primary.get("hwnd"), "pid": primary.get("pid"), "title": primary.get("title")} if primary else None,
        "Open is window-verified only when a matching HWND/title is observed.",
    ))
    checks.append(_check(
        "window_pid_matches_target_process",
        primary.get("pid") in observation.pids if primary and observation.pids else None,
        observation.pids,
        primary.get("pid") if primary else None,
        "Observed window PID must belong to the target process PID set.",
    ))

    if ambiguous:
        return DesktopVerificationResult(action, method, observation, "failed", f"ambiguous target: {window_count} matching windows", checks)
    if process_known and process_alive and window_present:
        return DesktopVerificationResult(action, method, observation, "verified", "target process is alive and a matching window is present", checks)
    if not process_known:
        reason = "process_name is not configured"
    elif not process_alive:
        reason = "target process is not alive"
    else:
        reason = "matching window was not observed"
    return DesktopVerificationResult(action, method, observation, "unverified", reason, checks)


def make_desktop_execution_evidence(
    *,
    action: str,
    app: str,
    method: str,
    started_at_ms: int,
    observation: DesktopObservation,
    verification_state: str,
    verification_reason: str | None = None,
    verification_checks: list[dict[str, Any]] | None = None,
    attempts: list[dict[str, Any]] | None = None,
    fallback_chain: list[dict[str, Any]] | None = None,
    recovery_triggered: bool = False,
    warnings: list[str] | None = None,
) -> ExecutionEvidence:
    primary = observation.primary_window
    return ExecutionEvidence(
        action=action,
        target=observation.target.app_id or app,
        target_type="application",
        method=method,
        verifier=VERIFIER_VERSION,
        verification_state=verification_state,
        verification_reason=verification_reason,
        started_at_ms=started_at_ms,
        completed_at_ms=now_ms(),
        process_name=observation.target.process_name,
        pids=list(observation.pids),
        process_alive=observation.process_alive,
        window=primary,
        expected={
            "app_id": observation.target.app_id,
            "display_name": observation.target.display_name,
            "process_name": observation.target.process_name,
            "window_keywords": list(observation.target.window_keywords),
        },
        observed=_observed_snapshot(observation),
        verification_checks=list(verification_checks or []),
        matching_windows=list(observation.matching_windows),
        attempts=list(attempts or []),
        fallback_chain=list(fallback_chain or []),
        recovery_triggered=recovery_triggered,
        warnings=list(warnings or []),
    )


def verification_to_execution_evidence(
    *,
    verification: DesktopVerificationResult,
    app: str,
    started_at_ms: int,
    attempts: list[dict[str, Any]] | None = None,
    fallback_chain: list[dict[str, Any]] | None = None,
    recovery_triggered: bool = False,
    warnings: list[str] | None = None,
) -> ExecutionEvidence:
    merged_warnings = list(warnings or [])
    if verification.reason and verification.verification_state != "verified":
        merged_warnings.append(verification.reason)
    merged_warnings.extend(verification.observation.observation_errors)
    return make_desktop_execution_evidence(
        action=verification.action,
        app=app,
        method=verification.method,
        started_at_ms=started_at_ms,
        observation=verification.observation,
        verification_state=verification.verification_state,
        verification_reason=verification.reason,
        verification_checks=verification.checks,
        attempts=attempts,
        fallback_chain=fallback_chain,
        recovery_triggered=recovery_triggered,
        warnings=merged_warnings,
    )
