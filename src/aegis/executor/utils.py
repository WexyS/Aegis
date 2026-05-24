# src/aegis/executor/utils.py

import os
import shutil
import difflib
import ctypes
import logging
from pathlib import Path
from aegis.core.app_map import all_app_configs

logger = logging.getLogger(__name__)

def verify_path(path: str) -> tuple[bool, str | None]:
    """
    Elite-Grade Path Validation (Hardened Runtime).
    Returns (is_valid, resolved_path).
    Proactively resolves bare names to absolute paths to eliminate Shell PATH dependency.
    """
    if not path:
        return False, None

    path = os.path.expandvars(path.strip())
    if path.startswith(("steam://", "com.epicgames.launcher://")):
        return True, path

    # 1. FULL PATH Check (Contains slashes or absolute)
    if "\\" in path or "/" in path or os.path.isabs(path):
        if os.path.exists(path):
            return True, path
        return False, None

    # 2. SYSTEM BINARY MAPPING (Zero-Trust Environment)
    system_root = os.environ.get("SystemRoot", "C:\\Windows")
    system32 = os.path.join(system_root, "System32")
    syswow64 = os.path.join(system_root, "SysWOW64")
    
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")

    # Common system binary overrides
    hardened_bins = {
        "cmd": os.path.join(system32, "cmd.exe"),
        "tasklist": os.path.join(system32, "tasklist.exe"),
        "timeout": os.path.join(system32, "timeout.exe"),
        "explorer": os.path.join(system_root, "explorer.exe"),
        "notepad": os.path.join(system32, "notepad.exe"),
        "calc": os.path.join(system32, "calc.exe"),
        "powershell": os.path.join(system32, "WindowsPowerShell\\v1.0\\powershell.exe"),
    }
    
    clean_name = path.lower().replace(".exe", "")
    if clean_name in hardened_bins:
        bin_path = hardened_bins[clean_name]
        if os.path.exists(bin_path):
            return True, bin_path

    browser_candidates = {
        "chrome": [
            Path(program_files) / "Google" / "Chrome" / "Application" / "chrome.exe",
            Path(program_files_x86) / "Google" / "Chrome" / "Application" / "chrome.exe",
            Path(local_app_data) / "Google" / "Chrome" / "Application" / "chrome.exe",
        ],
        "brave": [
            Path(program_files) / "BraveSoftware" / "Brave-Browser" / "Application" / "brave.exe",
            Path(program_files_x86) / "BraveSoftware" / "Brave-Browser" / "Application" / "brave.exe",
            Path(local_app_data) / "BraveSoftware" / "Brave-Browser" / "Application" / "brave.exe",
        ],
    }
    for candidate in browser_candidates.get(clean_name, []):
        if candidate.exists():
            return True, str(candidate)

    # 3. SHUTIL.WHICH (PATH resolution as a fallback)
    resolved = shutil.which(path)
    if resolved:
        return True, resolved
        
    # 4. SYSTEM32 FALLBACK
    bin_exe = path if path.lower().endswith(".exe") else path + ".exe"
    direct_sys32 = os.path.join(system32, bin_exe)
    if os.path.exists(direct_sys32):
        return True, direct_sys32

    return False, None

def smart_match_app(name: str, cutoff: float = 0.65) -> str | None:
    """Alias-aware fuzzy matching against the application registry."""
    name = name.lower().strip()
    if not name: return None

    candidates = {}
    for key, val in all_app_configs().items():
        candidates[key] = key
        for alias in val.get("aliases", []):
            candidates[alias] = key

    matches = difflib.get_close_matches(name, list(candidates.keys()), n=1, cutoff=cutoff)
    if matches:
        matched = matches[0]
        resolved = candidates[matched]
        logger.debug("[SMART MATCH] %s -> %s", name, resolved)
        return resolved

    return None

def get_running_pids(process_name: str) -> list[int]:
    """
    Retrieves all PIDs for a given process name.
    Deterministic via psutil, fallback to tasklist if psutil is unavailable.
    """
    result = []
    
    # 1. Preferred Method: psutil
    try:
        import psutil
        for p in psutil.process_iter(['pid', 'name']):
            try:
                if p.info['name'] and p.info['name'].lower() == process_name.lower():
                    result.append(p.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return result
    except ImportError:
        pass

    # 2. Fallback Method: tasklist (Native Windows)
    try:
        import subprocess
        tasklist = r'C:\Windows\System32\tasklist.exe'
        completed = subprocess.run(
            [tasklist, "/FI", f"IMAGENAME eq {process_name}", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            check=False,
            shell=False,
        )
        output = completed.stdout
        for line in output.splitlines():
            if not line.strip(): continue
            parts = line.split('","')
            if len(parts) > 1:
                pid_str = parts[1].replace('"', '')
                if pid_str.isdigit():
                    result.append(int(pid_str))
    except Exception:
        pass
        
    return result

def get_window_pid(hwnd) -> int:
    """Extracts the PID from a window handle using native Windows API."""
    pid = ctypes.c_ulong()
    ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value

def score_window(w, valid_pids: list[int]) -> int:
    """Ranks windows based on process identity, visibility, and title quality."""
    score = 0
    try:
        hwnd = w._hWnd
        pid = get_window_pid(hwnd)

        if pid in valid_pids:
            score += 100

        if not w.isMinimized:
            score += 40

        title = (w.title or "").lower()
        if len(title) > 15:
            score += 10
        
        if any(x in title for x in ["settings", "preferences", "dialog", "help", "update"]):
            score -= 50

    except Exception:
        return -999 # Window lost or inaccessible

    return score

def is_process_alive(process_name: str) -> bool:
    """
    Checks if any process with the given name is currently running.
    Reuses the psutil/tasklist high-reliability discovery logic.
    """
    if not process_name: return False
    pids = get_running_pids(process_name)
    return len(pids) > 0
