# src/aegis/tools/desktop_tools.py

import subprocess
import asyncio
import os
import pygetwindow as gw
from aegis.core.app_map import get_app_config, resolve_app_name
from aegis.executor.utils import get_running_pids
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
        matched = []
        for proc in psutil.process_iter(["name"]):
            proc_name = str(proc.info.get("name") or "").lower()
            if proc_name == target_process:
                proc.terminate()
                matched.append(proc)

        if not matched:
            return f"No running process found for {app}."

        gone, alive = psutil.wait_procs(matched, timeout=float(kwargs.get("timeout", 3.0)))
        for proc in alive:
            proc.kill()
        closed = len(gone) + len(alive)
        return f"Closed {closed} instance(s) of {app}."

class FocusTool(BaseTool):
    name = "focus_app"
    description = "Focus an existing application window."

    async def run(self, app: str, **kwargs) -> str:
        keywords = [k.lower() for k in _window_keywords(app)]
        candidates = []
        for window in gw.getAllWindows():
            if not getattr(window, "visible", False):
                continue
            title = (getattr(window, "title", "") or "").lower()
            if any(keyword in title for keyword in keywords):
                candidates.append(window)

        if not candidates:
            return f"Error: No visible window found for '{app}'."
        if len(candidates) > 1:
            titles = [getattr(w, "title", "") for w in candidates[:3]]
            return f"Error: Ambiguous focus target for '{app}' ({len(candidates)} windows: {titles})."

        window = candidates[0]
        if getattr(window, "isMinimized", False):
            window.restore()
            await asyncio.sleep(0.1)
        window.activate()
        await asyncio.sleep(0.1)
        return f"Focused '{app}' (HWND: {getattr(window, '_hWnd', 'unknown')})."
