# src/aegis/tools/desktop_tools.py

import subprocess
import asyncio
import os
import pygetwindow as gw
from aegis.core.app_map import get_app_config, resolve_app_name
from aegis.executor.utils import get_running_pids
from aegis.executor.utils import get_window_pid
from aegis.tools.base import BaseTool


def _app_config(app: str) -> tuple[str, dict | None]:
    app_id = resolve_app_name(app) or app.lower().strip()
    return app_id, get_app_config(app_id)


def _window_keywords(app: str) -> list[str]:
    app_id, config = _app_config(app)
    if config and config.get("window_keywords"):
        return list(config["window_keywords"])
    return [app_id, app]


def _process_name(app: str) -> str:
    app_id, config = _app_config(app)
    if config and config.get("process_name"):
        return str(config["process_name"])
    return app_id if app_id.lower().endswith(".exe") else f"{app_id}.exe"


def _process_pid(proc) -> int | None:
    pid = getattr(proc, "pid", None)
    if pid is None and hasattr(proc, "info"):
        pid = proc.info.get("pid")
    try:
        return int(pid) if pid is not None else None
    except (TypeError, ValueError):
        return None


def _expected_pid_set(raw) -> set[int]:
    if not raw:
        return set()
    pids = raw if isinstance(raw, (list, tuple, set)) else [raw]
    result = set()
    for pid in pids:
        try:
            result.add(int(pid))
        except (TypeError, ValueError):
            continue
    return result


def _window_snapshot(window) -> dict:
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
        "visible": bool(getattr(window, "visible", True)),
        "is_minimized": bool(getattr(window, "isMinimized", False)),
    }


def _record_evidence(sink, entry: dict) -> None:
    if isinstance(sink, list):
        sink.append(entry)

class OpenAppTool(BaseTool):
    name = "open_app"
    description = "Launch a local Windows application with deep verification and process monitoring."

    async def run(self, app: str, **kwargs) -> str:
        path = kwargs.get("_resolved_path", app)
        keywords = kwargs.get("_keywords", [app])
        process_name = kwargs.get("_process_name")

        try:
            # 0. IDEMPOTENCY CHECK (Elite Hardening)
            # If the app is already open and responsive, we don't need to launch a new one.
            if process_name:
                pids = get_running_pids(process_name)
                if pids:
                    for w in gw.getAllWindows():
                        if w.visible:
                            import ctypes
                            pid = ctypes.c_ulong()
                            ctypes.windll.user32.GetWindowThreadProcessId(w._hWnd, ctypes.byref(pid))
                            if pid.value in pids:
                                title = (w.title or "").lower()
                                if any(k.lower() in title for k in keywords):
                                    # Already open! Just focus it.
                                    w.activate()
                                    return f"App '{app}' is already running and verified (PID: {pid.value})."

            print(f"[LAUNCH] {app} -> {path}")

            # 1. ATOMIC LAUNCH (os.startfile)
            proc = None
            try:
                os.startfile(path)
            except Exception as e:
                print(f"[LAUNCH] os.startfile failed: {e}. Falling back to subprocess.")
                proc = subprocess.Popen([path], shell=False)

            # 2. DEEP VERIFICATION LOOP (UI + Process Survival)
            for i in range(100):  # ~10 seconds total
                await asyncio.sleep(0.1)

                # A. Process Survival Check (Essential for Elite stability)
                # If the app starts but crashes, we must catch it early.
                if process_name:
                    pids = get_running_pids(process_name)
                    # If we had a process_name but after 2s it's gone, it's a crash.
                    if i > 20 and not pids:
                        return f"Error: '{app}' process vanished after launch (Crash detected)."

                # B. UI Manifestation Check
                for w in gw.getAllWindows():
                    title = (w.title or "").lower()
                    if any(k.lower() in title for k in keywords):
                        # Verify PID ownership if process_name is known
                        if process_name:
                            pids = get_running_pids(process_name)
                            import ctypes
                            pid = ctypes.c_ulong()
                            ctypes.windll.user32.GetWindowThreadProcessId(w._hWnd, ctypes.byref(pid))
                            if pid.value in pids:
                                # FOUND! Add micro-delay for input readiness (Elite fix)
                                await asyncio.sleep(0.2)
                                return f"Successfully launched '{app}' (Verified PID: {pid.value})."
                        else:
                            await asyncio.sleep(0.2)
                            return f"Successfully launched '{app}'."

                # C. Early Exit Check (for subprocess fallback)
                if proc and proc.poll() is not None and proc.poll() != 0:
                    return f"Error: '{app}' failed to start (Return Code: {proc.poll()})."

            return f"WARNING: '{app}' initiated, but UI not detected within 10s."

        except Exception as e:
            return f"Error launching '{app}': {str(e)}"

class TypeTool(BaseTool):
    name = "type"
    description = "Type text into the focused window with reliability checks."

    async def run(self, text: str, **kwargs) -> str:
        try:
            import pyautogui
            from aegis.core.state_manager import get_state_manager
            state_manager = get_state_manager()
            
            # Planner'ın enjekte ettiği focus gereksinimini karşıla
            required_app = kwargs.get("_require_focus")
            if required_app:
                for w in gw.getAllWindows():
                    if required_app.lower() in (w.title or "").lower():
                        if w.isMinimized: w.restore()
                        w.activate()
                        await asyncio.sleep(0.3)
                        break

            # TRIPLE-PULSE FOCUS VERIFICATION (Elite Stability)
            # Ensure focus isn't fluttering before sending keystrokes
            for _ in range(3):
                await state_manager.sync_with_os(kwargs.get("trace_id"), kwargs.get("span_id"))
                state = state_manager.get_state()
                if state.focus_stable and state.hwnd:
                    break
                await asyncio.sleep(0.2)
            else:
                return "Error: Focus is unstable or no window is active. Aborting type action for safety."

            pyautogui.write(text, interval=0.02)
            return f"Typed: '{text}'"
        except ImportError:
            return "Error: pyautogui required."
        except Exception as e:
            return f"Error: {str(e)}"

class CloseAppTool(BaseTool):
    name = "close_app"
    description = "Close an application by name."

    async def run(self, app: str, **kwargs) -> str:
        import psutil
        target_process = _process_name(app).lower()
        timeout = float(kwargs.get("timeout", 3.0))
        evidence_sink = kwargs.get("_close_evidence")
        expected_pids = _expected_pid_set(kwargs.get("_expected_pids"))
        matched = []
        if expected_pids:
            for pid in sorted(expected_pids):
                try:
                    proc = psutil.Process(pid)
                    if str(proc.name() or "").lower() == target_process:
                        matched.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        else:
            for proc in psutil.process_iter(["name"]):
                proc_name = str(proc.info.get("name") or "").lower()
                if proc_name == target_process:
                    matched.append(proc)

        close_attempt = {
            "action": "close_app",
            "process_name": target_process,
            "initial_pids": [pid for proc in matched if (pid := _process_pid(proc)) is not None],
            "terminate_sent_pids": [],
            "graceful_timeout_seconds": timeout,
            "graceful_terminated_pids": [],
            "kill_sent_pids": [],
            "killed_pids": [],
            "remaining_pids": [],
            "outcome": "not_found",
        }

        if not matched:
            _record_evidence(evidence_sink, close_attempt)
            return f"No running process found for {app}."

        for proc in matched:
            proc.terminate()
            if (pid := _process_pid(proc)) is not None:
                close_attempt["terminate_sent_pids"].append(pid)

        gone, alive = psutil.wait_procs(matched, timeout=timeout)
        close_attempt["graceful_terminated_pids"] = [
            pid for proc in gone if (pid := _process_pid(proc)) is not None
        ]
        for proc in alive:
            if (pid := _process_pid(proc)) is not None:
                close_attempt["kill_sent_pids"].append(pid)
            proc.kill()
        if alive:
            killed, remaining = psutil.wait_procs(alive, timeout=1.0)
            close_attempt["killed_pids"] = [
                pid for proc in killed if (pid := _process_pid(proc)) is not None
            ]
            close_attempt["remaining_pids"] = [
                pid for proc in remaining if (pid := _process_pid(proc)) is not None
            ]
        else:
            remaining = []

        close_attempt["outcome"] = "killed" if close_attempt["kill_sent_pids"] else "graceful_terminated"
        if close_attempt["remaining_pids"]:
            close_attempt["outcome"] = "remaining_after_kill"
        _record_evidence(evidence_sink, close_attempt)
        closed = len(gone) + len(alive)
        return f"Closed {closed} instance(s) of {app}."

class FocusTool(BaseTool):
    name = "focus_app"
    description = "Focus an existing application window."

    async def run(self, app: str, **kwargs) -> str:
        keywords = [str(k).lower() for k in (kwargs.get("_keywords") or _window_keywords(app))]
        expected_pids = _expected_pid_set(kwargs.get("_expected_pids"))
        evidence_sink = kwargs.get("_focus_evidence")
        focus_attempt = {
            "action": "focus_app",
            "app": app,
            "keywords": list(keywords),
            "candidate_count": 0,
            "candidates": [],
            "selected_window": None,
            "restored": False,
            "activate_called": False,
            "foreground_after": None,
            "outcome": "not_found",
        }
        candidates = []
        for window in gw.getAllWindows():
            if not getattr(window, "visible", False):
                continue
            title = (getattr(window, "title", "") or "").lower()
            if any(keyword in title for keyword in keywords):
                snapshot = _window_snapshot(window)
                if expected_pids and snapshot.get("pid") not in expected_pids:
                    continue
                candidates.append(window)
                focus_attempt["candidates"].append(snapshot)

        focus_attempt["candidate_count"] = len(candidates)

        if not candidates:
            _record_evidence(evidence_sink, focus_attempt)
            return f"Error: No visible window found for '{app}'."
        if len(candidates) > 1:
            titles = [getattr(w, "title", "") for w in candidates[:3]]
            focus_attempt["outcome"] = "ambiguous"
            _record_evidence(evidence_sink, focus_attempt)
            return f"Error: Ambiguous focus target for '{app}' ({len(candidates)} windows: {titles})."

        window = candidates[0]
        focus_attempt["selected_window"] = _window_snapshot(window)
        if getattr(window, "isMinimized", False):
            window.restore()
            focus_attempt["restored"] = True
            await asyncio.sleep(0.1)
        window.activate()
        focus_attempt["activate_called"] = True
        await asyncio.sleep(0.1)
        try:
            focus_attempt["foreground_after"] = _window_snapshot(gw.getActiveWindow())
        except Exception as exc:
            focus_attempt["foreground_after"] = {"error": str(exc)}
        focus_attempt["outcome"] = "focused"
        _record_evidence(evidence_sink, focus_attempt)
        return f"Focused '{app}' (HWND: {getattr(window, '_hWnd', 'unknown')})."
