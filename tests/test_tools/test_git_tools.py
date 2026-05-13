from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from aegis.tools import git_tools
from aegis.tools.git_tools import GitActionTool


def test_resolve_git_executable_prefers_path(monkeypatch) -> None:
    monkeypatch.setattr(git_tools.shutil, "which", lambda name: r"C:\Git\cmd\git.exe")

    assert git_tools._resolve_git_executable() == r"C:\Git\cmd\git.exe"


def test_resolve_git_executable_falls_back_to_windows_install(monkeypatch) -> None:
    git_path = Path(r"C:\Program Files\Git\cmd\git.exe")
    monkeypatch.setattr(git_tools.shutil, "which", lambda name: None)
    monkeypatch.setattr(git_tools, "WINDOWS_GIT_CANDIDATES", (git_path,))
    monkeypatch.setattr(Path, "exists", lambda self: self == git_path)

    assert git_tools._resolve_git_executable() == str(git_path)


@pytest.mark.asyncio
async def test_git_status_runs_read_only_status(monkeypatch) -> None:
    calls = []

    def fake_run(command, capture_output, text, check):
        calls.append(command)
        return SimpleNamespace(returncode=0, stdout="## main\n", stderr="")

    monkeypatch.setattr(git_tools, "_resolve_git_executable", lambda: r"C:\Git\cmd\git.exe")
    monkeypatch.setattr("subprocess.run", fake_run)

    result = await GitActionTool().run("status")

    assert calls == [[r"C:\Git\cmd\git.exe", "status", "--short", "--branch"]]
    assert "Git status" in result
    assert "## main" in result


@pytest.mark.asyncio
async def test_git_status_reports_clear_error_when_git_missing(monkeypatch) -> None:
    monkeypatch.setattr(git_tools, "_resolve_git_executable", lambda: None)

    result = await GitActionTool().run("status")

    assert result == (
        "Git status system error: git executable not found. "
        "Install Git for Windows or add Git to PATH."
    )


@pytest.mark.asyncio
async def test_git_tool_blocks_mutating_commands(monkeypatch) -> None:
    def fake_run(*args, **kwargs):
        raise AssertionError("mutating git command should not be executed")

    monkeypatch.setattr("subprocess.run", fake_run)

    result = await GitActionTool().run("push")

    assert result.startswith("Error: Git action 'push' is blocked")
