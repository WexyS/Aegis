from __future__ import annotations

import importlib.util
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from aegis.core.config import PROJECT_ROOT
from aegis.tools.git_tools import _resolve_git_executable


def collect_environment_diagnostics(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    """Read-only diagnostics for local developer/runtime environment."""
    root = Path(project_root)
    frontend_dir = root / "frontend"
    checks: dict[str, Any] = {
        "python": _python_check(),
        "pytest": _python_module_check("pytest", command=_pytest_command(root)),
        "playwright": _python_module_check("playwright"),
        "git": _git_check(root),
        "node": _executable_check("node", version_command=["node", "-v"]),
        "npm": _npm_check(),
        "frontend": _frontend_check(frontend_dir),
    }
    recommendations = _recommendations(checks)
    return {
        "scan_version": "environment-diagnostics/1",
        "read_only": True,
        "started_at": int(time.time() * 1000),
        "overall_status": "ok" if not recommendations else "warning",
        "checks": checks,
        "recommendations": recommendations,
        "completed_at": int(time.time() * 1000),
    }


def _python_check() -> dict[str, Any]:
    executable = sys.executable
    in_virtualenv = ".venv" in executable.lower() or sys.prefix != sys.base_prefix
    return {
        "status": "ok" if in_virtualenv else "warning",
        "executable": executable,
        "version": platform.python_version(),
        "in_virtualenv": in_virtualenv,
    }


def _pytest_command(project_root: Path) -> str:
    venv_python = project_root / ".venv" / "Scripts" / "python.exe"
    if venv_python.exists():
        return r".\.venv\Scripts\python.exe -m pytest -q"
    return "python -m pytest -q"


def _python_module_check(module_name: str, command: str | None = None) -> dict[str, Any]:
    available = _module_available(module_name)
    check: dict[str, Any] = {
        "status": "ok" if available else "warning",
        "module": module_name,
        "available": available,
    }
    if command:
        check["recommended_command"] = command
    return check


def _module_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def _git_check(project_root: Path) -> dict[str, Any]:
    executable = _resolve_git_executable()
    repository_present = (project_root / ".git").exists()
    return {
        "status": "ok" if executable and repository_present else "warning",
        "executable": executable,
        "repository_present": repository_present,
        "repository_path": str(project_root / ".git"),
        "path_available": shutil.which("git") is not None,
    }


def _executable_check(command: str, *, version_command: list[str] | None = None) -> dict[str, Any]:
    executable = shutil.which(command)
    return {
        "status": "ok" if executable else "warning",
        "command": command,
        "executable": executable,
        "version": _run_version(version_command or [command, "--version"]) if executable else None,
    }


def _npm_check() -> dict[str, Any]:
    preferred = "npm.cmd" if platform.system().lower() == "windows" else "npm"
    executable = shutil.which(preferred) or shutil.which("npm")
    command = preferred if shutil.which(preferred) else "npm"
    return {
        "status": "ok" if executable else "warning",
        "preferred_command": preferred,
        "command": command,
        "executable": executable,
        "version": _run_version([command, "-v"]) if executable else None,
    }


def _run_version(command: list[str]) -> str | None:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except Exception:
        return None
    output = (result.stdout or result.stderr).strip()
    return output.splitlines()[0] if output else None


def _frontend_check(frontend_dir: Path) -> dict[str, Any]:
    package_json = frontend_dir / "package.json"
    package_lock = frontend_dir / "package-lock.json"
    return {
        "status": "ok" if package_json.exists() else "warning",
        "directory": str(frontend_dir),
        "package_json": package_json.exists(),
        "package_lock": package_lock.exists(),
        "build_command": "npm.cmd run build",
    }


def _recommendations(checks: dict[str, Any]) -> list[str]:
    recommendations: list[str] = []
    if checks["python"]["status"] != "ok":
        recommendations.append(r"Use the project virtualenv: .\.venv\Scripts\python.exe -m pytest -q")
    if checks["pytest"]["status"] != "ok":
        recommendations.append("Install dev dependencies in the virtualenv: pip install -e .[dev]")
    if checks["git"]["executable"] is None:
        recommendations.append(r"Install Git for Windows or add C:\Program Files\Git\cmd to PATH.")
    elif not checks["git"]["path_available"]:
        recommendations.append(r"Git is installed but not on PATH; add C:\Program Files\Git\cmd to user PATH.")
    if not checks["git"]["repository_present"]:
        recommendations.append("This folder is not initialized as a Git repository; run git init if desired.")
    if checks["node"]["status"] != "ok":
        recommendations.append("Install Node.js 20+ and reopen the terminal.")
    if checks["npm"]["status"] != "ok":
        recommendations.append("Install npm with Node.js and prefer npm.cmd on Windows.")
    if checks["frontend"]["status"] != "ok":
        recommendations.append("Run frontend checks from the project frontend directory.")
    if checks["playwright"]["status"] != "ok":
        recommendations.append("Install the Python Playwright dependency in the virtualenv.")
    return recommendations
