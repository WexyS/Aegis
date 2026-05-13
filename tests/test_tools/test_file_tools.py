from __future__ import annotations

import json

import pytest

from aegis.core.config import PROJECT_ROOT
from aegis.tools.file_tools import (
    CreateFileTool,
    DeleteFileTool,
    EditFileTool,
    FileInfoTool,
    GrepInFilesTool,
    ListDirectoryTool,
    MoveFileTool,
    SearchFilesTool,
    WriteFileTool,
)


@pytest.mark.asyncio
async def test_write_file_blocks_windows_directory_case_insensitively() -> None:
    result = await WriteFileTool().run("c:\\windows\\temp\\aegis-test.txt", "nope")

    assert result.startswith("Error: Writing to C:\\Windows is forbidden")


@pytest.mark.asyncio
async def test_write_file_blocks_public_user_directory_case_insensitively() -> None:
    result = await WriteFileTool().run("c:\\users\\public\\aegis-test.txt", "nope")

    assert result.startswith("Error: Writing to C:\\Users\\Public is forbidden")


@pytest.mark.asyncio
async def test_write_file_allows_project_root_scratch() -> None:
    path = PROJECT_ROOT / "scratch" / "write-allowlist-test.txt"
    if path.exists():
        path.unlink()

    result = await WriteFileTool().run(str(path), "ok")

    try:
        assert result == f"Successfully written to {path}"
        assert path.read_text(encoding="utf-8") == "ok"
    finally:
        if path.exists():
            path.unlink()


@pytest.mark.asyncio
async def test_write_file_blocks_outside_project_root(tmp_path) -> None:
    path = tmp_path / "outside.txt"

    result = await WriteFileTool().run(str(path), "nope")

    assert result.startswith("Error: Writing outside allowed roots is forbidden")
    assert not path.exists()


@pytest.mark.asyncio
async def test_low_risk_file_inspection_tools_return_read_only_reports(tmp_path, monkeypatch) -> None:
    workspace_file = PROJECT_ROOT / "scratch" / "registry-readme-test.txt"
    workspace_file.write_text("alpha\nbeta\n", encoding="utf-8")
    try:
        directory = json.loads(await ListDirectoryTool().run("scratch", max_entries=20))
        search = json.loads(await SearchFilesTool().run(query="registry-readme-test", path="scratch"))
        grep = json.loads(await GrepInFilesTool().run(query="alpha", path=str(workspace_file)))
        info = json.loads(await FileInfoTool().run(str(workspace_file)))

        assert directory["path"].endswith("scratch")
        assert search["match_count"] == 1
        assert grep["match_count"] == 1
        assert info["type"] == "file"
        assert info["size_bytes"] > 0
    finally:
        workspace_file.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_create_file_dry_run_returns_diff_without_writing() -> None:
    path = PROJECT_ROOT / "scratch" / "create-preview-test.txt"
    path.unlink(missing_ok=True)

    result = json.loads(await CreateFileTool().run(str(path), "hello", dry_run=True))

    assert result["dry_run"] is True
    assert result["would_create"] is True
    assert "hello" in result["diff_preview"]
    assert not path.exists()


@pytest.mark.asyncio
async def test_edit_file_blocks_path_traversal_before_preview(tmp_path) -> None:
    outside = tmp_path / "outside.txt"
    outside.write_text("old", encoding="utf-8")

    result = await EditFileTool().run(str(outside), target="old", replacement="new", dry_run=True)

    assert result.startswith("Error: Writing outside allowed roots is forbidden")
    assert outside.read_text(encoding="utf-8") == "old"


@pytest.mark.asyncio
async def test_critical_delete_and_move_tools_are_dumb_blocked_hands() -> None:
    delete_result = await DeleteFileTool().run("scratch/anything.txt")
    move_result = await MoveFileTool().run("scratch/a.txt", "scratch/b.txt")

    assert "blocked" in delete_result.lower()
    assert "blocked" in move_result.lower()
