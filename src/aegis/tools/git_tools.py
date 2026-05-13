from __future__ import annotations

import logging
from pathlib import Path
import shutil
import subprocess
from typing import Any

from aegis.tools.base import BaseTool

logger = logging.getLogger(__name__)

WINDOWS_GIT_CANDIDATES = (
    Path(r"C:\Program Files\Git\cmd\git.exe"),
    Path(r"C:\Program Files\Git\bin\git.exe"),
    Path(r"C:\Program Files (x86)\Git\cmd\git.exe"),
    Path(r"C:\Program Files (x86)\Git\bin\git.exe"),
)


def _resolve_git_executable() -> str | None:
    git_from_path = shutil.which("git")
    if git_from_path:
        return git_from_path

    for candidate in WINDOWS_GIT_CANDIDATES:
        if candidate.exists():
            return str(candidate)

    return None


class GitActionTool(BaseTool):
    """Read-only git tool surface."""

    def __init__(self):
        self.name = "git_action"
        self.description = "Execute verified read-only git commands."

    async def run(self, git_cmd: str, **kwargs: Any) -> str:
        cmd_map = {
            "pushla": "push",
            "cek": "pull",
            "guncelle": "fetch",
            "commit'le": "commit",
            "commit-le": "commit",
        }
        actual_cmd = cmd_map.get(str(git_cmd).lower().strip(), str(git_cmd).lower().strip())
        self.log_action(git_cmd=actual_cmd)

        if actual_cmd != "status":
            return f"Error: Git action '{actual_cmd}' is blocked until verified git mutations are implemented."

        git_executable = _resolve_git_executable()
        if git_executable is None:
            return (
                "Git status system error: git executable not found. "
                "Install Git for Windows or add Git to PATH."
            )

        full_command = [git_executable, "status", "--short", "--branch"]

        try:
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                output = result.stdout if result.stdout else "Success"
                return f"Git status successful:\n{output}"
            return f"Git status failed (exit {result.returncode}):\n{result.stderr}"
        except Exception as e:
            return f"Git status system error: {str(e)}"
