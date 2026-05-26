from __future__ import annotations

import os
from typing import Any

import pygetwindow as gw

from aegis.core.app_map import APP_REGISTRY
from aegis.executor.utils import get_running_pids, get_window_pid, verify_path

SMOKE_VERSION = "app-discovery-smoke/1"


def build_configured_app_discovery_smoke(app_ids: list[str] | None = None) -> dict[str, Any]:
    """Read-only desktop/app discovery diagnostics for configured registry entries."""
    requested = app_ids or sorted(APP_REGISTRY)
    windows, observation_errors = _read_window_candidates()
    process_pid_cache: dict[str, list[int]] = {}
    entries = [
        _diagnose_configured_app(app_id, windows, process_pid_cache)
        for app_id in requested
    ]
    return {
        "scan_version": SMOKE_VERSION,
        "read_only": True,
        "actions_performed": [],
        "entry_count": len(entries),
        "entries": entries,
        "observation_errors": observation_errors,
    }


def _diagnose_configured_app(
    app_id: str,
    windows: list[dict[str, Any]],
    process_pid_cache: dict[str, list[int]],
) -> dict[str, Any]:
    config = APP_REGISTRY.get(app_id)
    if not config:
        return {
            "app_id": app_id,
            "known": False,
            "read_only": True,
            "diagnostic_state": "unknown",
            "deterministic_verification_possible": False,
            "verification_blockers": ["unknown_configured_app"],
            "actions_performed": [],
        }

    process_names = _process_name_candidates(config)
    running_processes = [_running_process_report(process_name, process_pid_cache) for process_name in process_names]
    running_pids = sorted({
        pid
        for process in running_processes
        for pid in process["pids"]
        if isinstance(pid, int)
    })
    window_keywords = [str(keyword) for keyword in config.get("window_keywords", []) if str(keyword).strip()]
    matching_windows = [
        _window_match_report(window, running_pids, process_pid_cache)
        for window in windows
        if _title_matches(window.get("title"), window_keywords)
    ]
    pid_matched_windows = [window for window in matching_windows if window["pid_matches_process"] is True]
    ambiguous_title_windows = [
        window
        for window in matching_windows
        if len(window.get("matching_configured_app_ids", [])) > 1
    ]
    process_supported_title_overlap_windows = [
        window
        for window in ambiguous_title_windows
        if app_id in window.get("process_supported_configured_app_ids", [])
    ]
    title_only_overlap_windows = [
        window
        for window in ambiguous_title_windows
        if app_id not in window.get("process_supported_configured_app_ids", [])
    ]
    pid_supported_other_app_windows = [
        window
        for window in ambiguous_title_windows
        if app_id not in window.get("process_supported_configured_app_ids", [])
        and bool(window.get("process_supported_configured_app_ids"))
    ]
    blockers = _verification_blockers(
        process_names=process_names,
        running_pids=running_pids,
        matching_windows=matching_windows,
        pid_matched_windows=pid_matched_windows,
        ambiguous_title_windows=ambiguous_title_windows,
        process_supported_title_overlap_windows=process_supported_title_overlap_windows,
        title_only_overlap_windows=title_only_overlap_windows,
        pid_supported_other_app_windows=pid_supported_other_app_windows,
    )
    deterministic_possible = not blockers
    ambiguity_status = "ambiguous" if any(
        blocker.startswith("ambiguous_") for blocker in blockers
    ) else "not_ambiguous"

    return {
        "app_id": app_id,
        "known": True,
        "read_only": True,
        "display_name": config.get("display_name") or app_id,
        "source": config.get("source", "configured"),
        "aliases": list(config.get("aliases", [])),
        "executable_candidates": _executable_candidates(config),
        "process_name_candidates": process_names,
        "running_processes": running_processes,
        "process_alive": bool(running_pids) if process_names else None,
        "window_keywords": window_keywords,
        "matching_windows": matching_windows,
        "matching_window_count": len(matching_windows),
        "pid_matched_window_count": len(pid_matched_windows),
        "ambiguous_title_windows": ambiguous_title_windows,
        "process_supported_title_overlap_windows": process_supported_title_overlap_windows,
        "title_only_overlap_windows": title_only_overlap_windows,
        "pid_supported_other_app_windows": pid_supported_other_app_windows,
        "identity_diagnostics": {
            "process_pid_window_match_supports_this_app": bool(pid_matched_windows),
            "title_only_overlap_without_process_identity": bool(title_only_overlap_windows),
            "pid_supports_different_configured_app": bool(pid_supported_other_app_windows),
            "process_supported_title_overlap": bool(process_supported_title_overlap_windows),
        },
        "ambiguity_status": ambiguity_status,
        "deterministic_verification_possible": deterministic_possible,
        "verification_blockers": blockers,
        "diagnostic_state": _diagnostic_state(deterministic_possible, blockers, matching_windows, running_pids),
        "actions_performed": [],
    }


def _executable_candidates(config: dict[str, Any]) -> list[dict[str, Any]]:
    path = str(config.get("path") or "").strip()
    if not path:
        return []
    expanded = os.path.expandvars(path)
    has_filesystem_shape = "\\" in expanded or "/" in expanded or os.path.isabs(expanded)
    path_exists = os.path.exists(expanded) if has_filesystem_shape else None
    resolved, resolved_path = verify_path(path)
    return [{
        "configured": path,
        "expanded": expanded,
        "path_exists": path_exists,
        "resolved_read_only": resolved,
        "resolved_path": resolved_path,
    }]


def _process_name_candidates(config: dict[str, Any]) -> list[str]:
    process_name = config.get("process_name")
    if not process_name:
        return []
    return [str(process_name)]


def _running_pids_for_process(process_name: str, process_pid_cache: dict[str, list[int]]) -> list[int]:
    if process_name not in process_pid_cache:
        process_pid_cache[process_name] = list(get_running_pids(process_name))
    return list(process_pid_cache[process_name])


def _running_process_report(process_name: str, process_pid_cache: dict[str, list[int]]) -> dict[str, Any]:
    pids = _running_pids_for_process(process_name, process_pid_cache)
    return {
        "process_name": process_name,
        "pids": list(pids),
        "process_alive": bool(pids),
    }


def _read_window_candidates() -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    try:
        raw_windows = gw.getAllWindows()
    except Exception as exc:
        return [], [f"window_list_unavailable: {exc}"]

    windows: list[dict[str, Any]] = []
    for window in raw_windows:
        title = getattr(window, "title", "") or ""
        hwnd = getattr(window, "_hWnd", None)
        pid = None
        if hwnd is not None:
            try:
                pid = get_window_pid(hwnd)
            except Exception as exc:
                errors.append(f"window_pid_unavailable: {exc}")
        windows.append({
            "title": title,
            "hwnd": hwnd,
            "pid": pid,
            "visible": bool(getattr(window, "visible", True)),
            "is_minimized": bool(getattr(window, "isMinimized", False)),
            "matching_configured_app_ids": _matching_configured_app_ids(title),
        })
    return windows, errors


def _window_match_report(
    window: dict[str, Any],
    running_pids: list[int],
    process_pid_cache: dict[str, list[int]],
) -> dict[str, Any]:
    pid = window.get("pid")
    process_supported_ids = _process_supported_configured_app_ids(window, process_pid_cache)
    matching_ids = list(window.get("matching_configured_app_ids", []))
    return {
        "title": window.get("title"),
        "hwnd": window.get("hwnd"),
        "pid": pid,
        "visible": window.get("visible"),
        "is_minimized": window.get("is_minimized"),
        "pid_matches_process": pid in running_pids if running_pids and pid is not None else None,
        "matching_configured_app_ids": matching_ids,
        "process_supported_configured_app_ids": process_supported_ids,
        "title_only_matching_configured_app_ids": [
            app_id for app_id in matching_ids if app_id not in process_supported_ids
        ],
    }


def _process_supported_configured_app_ids(
    window: dict[str, Any],
    process_pid_cache: dict[str, list[int]],
) -> list[str]:
    pid = window.get("pid")
    if pid is None:
        return []
    supported: list[str] = []
    for app_id in window.get("matching_configured_app_ids", []):
        config = APP_REGISTRY.get(str(app_id))
        if not config:
            continue
        process_names = _process_name_candidates(config)
        if any(pid in _running_pids_for_process(process_name, process_pid_cache) for process_name in process_names):
            supported.append(str(app_id))
    return supported


def _matching_configured_app_ids(title: str) -> list[str]:
    matches: list[str] = []
    for app_id, config in APP_REGISTRY.items():
        keywords = [str(keyword) for keyword in config.get("window_keywords", []) if str(keyword).strip()]
        if _title_matches(title, keywords):
            matches.append(app_id)
    return matches


def _title_matches(title: Any, keywords: list[str]) -> bool:
    text = str(title or "").lower()
    return bool(text and keywords and any(keyword.lower() in text for keyword in keywords))


def _verification_blockers(
    *,
    process_names: list[str],
    running_pids: list[int],
    matching_windows: list[dict[str, Any]],
    pid_matched_windows: list[dict[str, Any]],
    ambiguous_title_windows: list[dict[str, Any]],
    process_supported_title_overlap_windows: list[dict[str, Any]],
    title_only_overlap_windows: list[dict[str, Any]],
    pid_supported_other_app_windows: list[dict[str, Any]],
) -> list[str]:
    blockers: list[str] = []
    if not process_names:
        blockers.append("process_name_unconfigured")
    if process_names and not running_pids:
        blockers.append("running_process_not_observed")
    if not matching_windows:
        blockers.append("matching_window_not_observed")
    if running_pids and matching_windows and not pid_matched_windows:
        blockers.append("window_pid_not_matched")
    if len(pid_matched_windows) > 1:
        blockers.append("ambiguous_pid_matched_windows")
    if ambiguous_title_windows:
        blockers.append("ambiguous_title_matches_multiple_configured_apps")
    if process_supported_title_overlap_windows:
        blockers.append("title_overlaps_other_configured_app")
    if title_only_overlap_windows:
        blockers.append("title_only_overlap_without_process_identity")
    if pid_supported_other_app_windows:
        blockers.append("pid_supports_different_configured_app")
    return blockers


def _diagnostic_state(
    deterministic_possible: bool,
    blockers: list[str],
    matching_windows: list[dict[str, Any]],
    running_pids: list[int],
) -> str:
    if deterministic_possible:
        return "deterministic_verification_possible"
    if any(blocker.startswith("ambiguous_") for blocker in blockers):
        return "ambiguous"
    if matching_windows or running_pids:
        return "partially_observed"
    return "not_observed"
