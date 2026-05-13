from __future__ import annotations

import asyncio
import json
import re
import shlex
import time
from typing import Any

from aegis.core.config import PROJECT_ROOT
from aegis.tools.base import BaseTool


DESTRUCTIVE_PATTERNS = [
    r"\brm\s+-rf\b",
    r"\bdel\b",
    r"\brmdir\b",
    r"\berase\b",
    r"\bformat\b",
    r"\bshutdown\b",
    r"\breboot\b",
    r"\breg\s+delete\b",
    r"\bRemove-Item\b",
    r"\bStop-Computer\b",
]

ALLOWED_COMMANDS = {
    ("git", "status"),
    ("python", "--version"),
    ("python", "-V"),
    ("py", "--version"),
    ("node", "--version"),
    ("npm", "--version"),
    ("npm.cmd", "--version"),
    ("pip", "--version"),
    ("where", "python"),
    ("where", "node"),
    ("where", "npm"),
    ("where.exe", "python"),
    ("where.exe", "node"),
    ("where.exe", "npm"),
    ("whoami",),
    ("hostname",),
}

MAX_CAPTURE_CHARS = 12_000


def is_destructive_shell_command(command: str) -> bool:
    return any(re.search(pattern, command, re.IGNORECASE) for pattern in DESTRUCTIVE_PATTERNS)


def normalize_command(command: str) -> tuple[str, ...]:
    return tuple(shlex.split(command.strip(), posix=False))


def is_allowlisted_shell_command(command: str) -> bool:
    try:
        normalized = normalize_command(command)
    except ValueError:
        return False
    normalized_lower = tuple(part.lower() for part in normalized)
    return normalized_lower in ALLOWED_COMMANDS


def _truncate(text: str) -> tuple[str, bool]:
    if len(text) <= MAX_CAPTURE_CHARS:
        return text, False
    return text[:MAX_CAPTURE_CHARS], True


class RunCommandTool(BaseTool):
    name = "run_command"
    description = "Run allowlisted, read-only shell introspection commands."

    async def run(
        self,
        command: str,
        timeout_seconds: float = 10.0,
        cancellation_token: Any | None = None,
        **kwargs,
    ) -> str:
        self.log_action(command=command, timeout_seconds=timeout_seconds)
        command = command.strip()
        if not command:
            return "Error: run_command requires a non-empty command."
        if is_destructive_shell_command(command):
            return "Error: Destructive shell command blocked by policy."
        if not is_allowlisted_shell_command(command):
            return "Error: Shell command is not in the read-only allowlist."

        args = normalize_command(command)
        started = time.perf_counter()
        process = await asyncio.create_subprocess_exec(
            *args,
            cwd=str(PROJECT_ROOT),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        timed_out = False
        while True:
            if cancellation_token is not None and getattr(cancellation_token, "cancelled", False):
                process.kill()
                await process.wait()
                return "Error: Command cancelled."
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=0.05)
                break
            except asyncio.TimeoutError:
                if (time.perf_counter() - started) >= timeout_seconds:
                    timed_out = True
                    process.kill()
                    stdout, stderr = await process.communicate()
                    break

        stdout_text, stdout_truncated = _truncate(stdout.decode("utf-8", errors="replace"))
        stderr_text, stderr_truncated = _truncate(stderr.decode("utf-8", errors="replace"))
        payload = {
            "command": command,
            "exit_code": process.returncode,
            "stdout": stdout_text,
            "stderr": stderr_text,
            "stdout_truncated": stdout_truncated,
            "stderr_truncated": stderr_truncated,
            "timed_out": timed_out,
            "duration_ms": round((time.perf_counter() - started) * 1000, 2),
            "read_only": True,
        }
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)
