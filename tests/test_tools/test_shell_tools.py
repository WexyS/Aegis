from __future__ import annotations

import json

import pytest

from aegis.tools.shell_tools import RunCommandTool, is_allowlisted_shell_command, is_destructive_shell_command


def test_shell_allowlist_accepts_only_read_only_introspection() -> None:
    assert is_allowlisted_shell_command("python --version") is True
    assert is_allowlisted_shell_command("git status") is True
    assert is_allowlisted_shell_command("python -c print(1)") is False


def test_shell_destructive_detector_blocks_common_mutations() -> None:
    assert is_destructive_shell_command("del C:\\temp\\x.txt") is True
    assert is_destructive_shell_command("Remove-Item C:\\temp\\x.txt") is True
    assert is_destructive_shell_command("python --version") is False


@pytest.mark.asyncio
async def test_run_command_executes_allowlisted_command_with_bounded_report() -> None:
    result = json.loads(await RunCommandTool().run("python --version"))

    assert result["command"] == "python --version"
    assert result["read_only"] is True
    assert result["timed_out"] is False
    assert "stdout" in result
    assert "stderr" in result


@pytest.mark.asyncio
async def test_run_command_blocks_non_allowlisted_command() -> None:
    result = await RunCommandTool().run("python -c print(1)")

    assert result.startswith("Error: Shell command is not in the read-only allowlist")


@pytest.mark.asyncio
async def test_run_command_blocks_destructive_command() -> None:
    result = await RunCommandTool().run("del C:\\temp\\x.txt")

    assert result.startswith("Error: Destructive shell command blocked")
