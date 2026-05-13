from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import pygetwindow as gw

from aegis.core.app_map import get_app_config, resolve_app_name
from aegis.core.schemas import ExecutionEvidence
from aegis.executor.utils import get_running_pids, get_window_pid


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

    @property
    def primary_window(self) -> dict[str, Any] | None:
        if self.focus_verified and self.active_window:
            return self.active_window
        return self.matching_windows[0] if self.matching_windows else None


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
) -> DesktopObservation:
    target = resolve_desktop_target(app, process_name=process_name, window_keywords=window_keywords)
    pids = get_running_pids(target.process_name) if target.process_name else []
    keywords = [keyword.lower() for keyword in target.window_keywords]
    active = None
    matching: list[dict[str, Any]] = []

    try:
        active = gw.getActiveWindow()
    except Exception:
        active = None
    active_evidence = window_evidence(active)

    try:
        windows = gw.getAllWindows()
    except Exception:
        windows = []

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
        process_alive=bool(pids) if target.process_name else None,
        matching_windows=matching,
        active_window=active_evidence,
        focus_verified=focus_verified,
    )


def make_desktop_execution_evidence(
    *,
    action: str,
    app: str,
    method: str,
    started_at_ms: int,
    observation: DesktopObservation,
    verification_state: str,
    warnings: list[str] | None = None,
) -> ExecutionEvidence:
    return ExecutionEvidence(
        action=action,
        target=observation.target.app_id or app,
        target_type="application",
        method=method,
        verification_state=verification_state,
        started_at_ms=started_at_ms,
        completed_at_ms=now_ms(),
        process_name=observation.target.process_name,
        pids=list(observation.pids),
        process_alive=observation.process_alive,
        window=observation.primary_window,
        warnings=list(warnings or []),
    )
