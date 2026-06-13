from __future__ import annotations

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from aegis.api.read_only_bridge import (
    BRIDGE_EXECUTION_PERMISSION,
    MAX_FILE_BYTES,
    create_bridge_app,
)


TOKEN = "test-bridge-token"


def _git_runner(args: list[str], cwd: Path) -> str:
    if args == ["rev-parse", "HEAD"]:
        return "abc123def456"
    if args == ["branch", "--show-current"]:
        return "main"
    if args == ["status", "--porcelain"]:
        return " M docs/readme.md\n?? frontend/next-env.d.ts"
    if args[:1] == ["log"]:
        return "abc123def456\x1f2026-06-13T12:00:00+00:00\x1fTest commit"
    raise AssertionError(f"unexpected git args: {args}")


@pytest.fixture
def bridge_repo(tmp_path: Path) -> Path:
    (tmp_path / "docs").mkdir()
    (tmp_path / "src" / "aegis").mkdir(parents=True)
    (tmp_path / "frontend").mkdir()
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "logs" / "archive").mkdir(parents=True)
    (tmp_path / ".git").mkdir()

    (tmp_path / "README.md").write_text("Aegis Mission Control\nBridge safe text\n", encoding="utf-8")
    (tmp_path / "docs" / "readme.md").write_text("ChatGPT bridge documentation\n", encoding="utf-8")
    (tmp_path / "src" / "aegis" / "module.py").write_text(
        "def bridge_marker():\n    return 'safe bridge marker'\n",
        encoding="utf-8",
    )
    (tmp_path / ".env").write_text("AEGIS_BRIDGE_TOKEN=secret\n", encoding="utf-8")
    (tmp_path / ".git" / "config").write_text("[core]\n", encoding="utf-8")
    (tmp_path / "node_modules" / "package.js").write_text("secret package\n", encoding="utf-8")
    (tmp_path / "logs" / "runtime_events.jsonl").write_text('{"event":"original"}\n', encoding="utf-8")
    (tmp_path / "logs" / "archive" / "old.jsonl").write_text('{"event":"old"}\n', encoding="utf-8")
    (tmp_path / "secret-token.txt").write_text("secret\n", encoding="utf-8")
    (tmp_path / "binary.bin").write_bytes(b"\x00\x01\x02")
    (tmp_path / "large.txt").write_text("x" * (MAX_FILE_BYTES + 1), encoding="utf-8")
    return tmp_path


@pytest.fixture
def app(bridge_repo: Path):
    return create_bridge_app(repo_root=bridge_repo, token=TOKEN, git_runner=_git_runner)


async def _client(app):
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def _headers(token: str = TOKEN) -> dict[str, str]:
    return {"X-Aegis-Bridge-Token": token}


def _assert_read_only_health(data: dict[str, object]) -> None:
    assert data["read_only"] is True
    assert data["runtime_dispatch_allowed"] is False
    assert data["execution_permission"] == BRIDGE_EXECUTION_PERMISSION
    assert data["write_endpoints"] is False
    assert data["command_execution_endpoint"] is False


def test_gitignore_excludes_local_bridge_token_path() -> None:
    gitignore = Path(".gitignore").read_text(encoding="utf-8")

    assert ".local/" in gitignore
    assert "*bridge-token*" in gitignore
    assert "*bridge-audit*" in gitignore


def test_committed_launcher_scripts_do_not_contain_real_token() -> None:
    script_paths = [
        Path("scripts/start-aegis-bridge.bat"),
        Path("scripts/start-aegis-bridge.ps1"),
        Path("scripts/show-aegis-bridge-token.ps1"),
    ]
    forbidden_literals = [
        "replace-with-local-random-token",
        "test-bridge-token",
        "sk-",
        "ghp_",
        "github_pat_",
    ]

    for script_path in script_paths:
        content = script_path.read_text(encoding="utf-8")
        for literal in forbidden_literals:
            assert literal not in content


def test_normal_launcher_does_not_print_bridge_token() -> None:
    content = Path("scripts/start-aegis-bridge.ps1").read_text(encoding="utf-8")

    assert "Write-Host $token" not in content
    assert "show-aegis-bridge-token.ps1" in content
    assert "AEGIS_BRIDGE_TOKEN" in content


@pytest.mark.asyncio
async def test_token_required(app) -> None:
    async with await _client(app) as client:
        response = await client.get("/health")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_invalid_token_rejected(app) -> None:
    async with await _client(app) as client:
        response = await client.get("/health", headers=_headers("wrong"))

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_health_returns_read_only_bridge_metadata(app, bridge_repo: Path) -> None:
    async with await _client(app) as client:
        response = await client.get("/health", headers=_headers())

    assert response.status_code == 200
    data = response.json()
    assert data["repo_root"] == str(bridge_repo.resolve())
    assert data["current_head"] == "abc123def456"
    assert ".git" in data["denied_path_policy"]["denied_parts"]
    _assert_read_only_health(data)


@pytest.mark.asyncio
async def test_allowed_docs_source_read_works(app) -> None:
    async with await _client(app) as client:
        response = await client.get("/repo/file", params={"path": "README.md"}, headers=_headers())

    assert response.status_code == 200
    data = response.json()
    assert data["read_only"] is True
    assert data["path"] == "README.md"
    assert data["line_count"] == 2
    assert "Aegis Mission Control" in data["content"]


@pytest.mark.asyncio
async def test_path_traversal_blocked(app) -> None:
    async with await _client(app) as client:
        response = await client.get("/repo/file", params={"path": "../outside.txt"}, headers=_headers())

    assert response.status_code == 403
    assert "traversal" in response.text


@pytest.mark.asyncio
@pytest.mark.parametrize("path", [".env", ".git/config", "node_modules/package.js", "logs/runtime_events.jsonl", "logs/archive/old.jsonl"])
async def test_denied_paths_blocked(app, path: str) -> None:
    async with await _client(app) as client:
        response = await client.get("/repo/file", params={"path": path}, headers=_headers())

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_file_outside_repo_blocked(app, tmp_path: Path) -> None:
    outside = tmp_path / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")

    async with await _client(app) as client:
        response = await client.get("/repo/file", params={"path": str(outside)}, headers=_headers())

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_binary_file_blocked(app) -> None:
    async with await _client(app) as client:
        response = await client.get("/repo/file", params={"path": "binary.bin"}, headers=_headers())

    assert response.status_code == 415


@pytest.mark.asyncio
async def test_oversized_file_blocked(app) -> None:
    async with await _client(app) as client:
        response = await client.get("/repo/file", params={"path": "large.txt"}, headers=_headers())

    assert response.status_code == 413


@pytest.mark.asyncio
async def test_secret_looking_path_blocked(app) -> None:
    async with await _client(app) as client:
        response = await client.get("/repo/file", params={"path": "secret-token.txt"}, headers=_headers())

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_repo_tree_works_and_enforces_denylist(app) -> None:
    async with await _client(app) as client:
        response = await client.get("/repo/tree", params={"path": ".", "max_depth": 2}, headers=_headers())

    assert response.status_code == 200
    data = response.json()
    paths = {node["path"] for node in data["nodes"]}
    assert "README.md" in paths
    assert "docs" in paths
    assert ".env" not in paths
    assert ".git" not in paths
    assert "node_modules" not in paths
    assert "logs" not in paths
    assert data["denylist_enforced"] is True


@pytest.mark.asyncio
async def test_search_works_and_enforces_denylist(app) -> None:
    async with await _client(app) as client:
        response = await client.post(
            "/repo/search",
            json={"query": "bridge", "globs": ["**/*.md", "*.md"], "max_results": 10},
            headers=_headers(),
        )

    assert response.status_code == 200
    data = response.json()
    paths = {result["path"] for result in data["results"]}
    assert "README.md" in paths or "docs/readme.md" in paths
    assert all(not path.startswith("logs/") for path in paths)
    assert all(".env" not in path for path in paths)
    assert data["denylist_enforced"] is True


@pytest.mark.asyncio
async def test_context_pack_respects_size_limits(app) -> None:
    async with await _client(app) as client:
        response = await client.post(
            "/repo/context-pack",
            json={"file_paths": ["README.md", "docs/readme.md"], "max_files": 2, "max_chars": 30},
            headers=_headers(),
        )

    assert response.status_code == 200
    data = response.json()
    assert data["read_only"] is True
    assert data["context_package_is_permission"] is False
    assert data["total_chars"] <= 30
    assert data["file_count"] >= 1


@pytest.mark.asyncio
async def test_git_status_endpoint_returns_metadata_without_content(app) -> None:
    async with await _client(app) as client:
        response = await client.get("/repo/status", headers=_headers())

    assert response.status_code == 200
    data = response.json()
    assert data["branch"] == "main"
    assert data["head"] == "abc123def456"
    assert data["clean"] is False
    assert "docs/readme.md" in data["changed_files"]
    assert data["ignored_runtime_artifacts_exposed_as_content"] is False
    assert data["secrets_exposed"] is False


@pytest.mark.asyncio
async def test_git_log_endpoint_returns_recent_metadata_without_diff(app) -> None:
    async with await _client(app) as client:
        response = await client.get("/repo/git-log", params={"limit": 1}, headers=_headers())

    assert response.status_code == 200
    data = response.json()
    assert data["commits"] == [
        {
            "hash": "abc123def456",
            "date": "2026-06-13T12:00:00+00:00",
            "message": "Test commit",
        }
    ]
    assert data["diff_content_included"] is False


@pytest.mark.asyncio
async def test_no_write_or_execute_endpoints_exist(app) -> None:
    async with await _client(app) as client:
        assert (await client.post("/repo/file", headers=_headers())).status_code == 405
        assert (await client.post("/execute", headers=_headers())).status_code == 404
        assert (await client.post("/command", headers=_headers())).status_code == 404


@pytest.mark.asyncio
async def test_bridge_does_not_mutate_runtime_journal_or_repo_files(app, bridge_repo: Path) -> None:
    journal = bridge_repo / "logs" / "runtime_events.jsonl"
    readme = bridge_repo / "README.md"
    journal_before = journal.read_text(encoding="utf-8")
    readme_before = readme.read_text(encoding="utf-8")

    async with await _client(app) as client:
        await client.get("/health", headers=_headers())
        await client.get("/repo/file", params={"path": "README.md"}, headers=_headers())
        await client.post("/repo/search", json={"query": "Aegis"}, headers=_headers())
        blocked = await client.get("/repo/file", params={"path": "logs/runtime_events.jsonl"}, headers=_headers())

    assert blocked.status_code == 403
    assert journal.read_text(encoding="utf-8") == journal_before
    assert readme.read_text(encoding="utf-8") == readme_before
