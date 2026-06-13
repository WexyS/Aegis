from __future__ import annotations

import fnmatch
import logging
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath
from typing import Any, Callable, Iterable

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

from aegis.core.config import PROJECT_ROOT


logger = logging.getLogger(__name__)

BRIDGE_EXECUTION_PERMISSION = "not_granted_by_read_only_chatgpt_bridge"
MAX_FILE_BYTES = 128 * 1024
MAX_TREE_NODES = 500
MAX_SEARCH_RESULTS = 100
MAX_CONTEXT_CHARS = 50_000
MAX_GIT_LOG_LIMIT = 50

DENIED_PARTS = {
    ".git",
    "node_modules",
    ".next",
    "logs",
    "archive",
    ".venv",
    ".pytest_cache",
    "__pycache__",
    "dist",
    "build",
    "cache",
    ".cache",
}
DENIED_EXACT_NAMES = {
    ".env",
    "runtime_events.jsonl",
    "runtime_events.lock",
}
DENIED_NAME_PREFIXES = (".env.",)
SECRET_NAME_FRAGMENTS = (
    "secret",
    "token",
    "credential",
    "credentials",
    "apikey",
    "api_key",
    "private_key",
    "password",
)
BINARY_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".pdf",
    ".zip",
    ".7z",
    ".gz",
    ".tar",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".pyc",
    ".mp3",
    ".mp4",
    ".mov",
    ".avi",
    ".sqlite",
    ".db",
}


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=200)
    globs: list[str] = Field(default_factory=list, max_length=20)
    max_results: int = Field(default=25, ge=1, le=MAX_SEARCH_RESULTS)


class ContextPackRequest(BaseModel):
    topic: str | None = Field(default=None, max_length=200)
    file_paths: list[str] = Field(default_factory=list, max_length=20)
    max_files: int = Field(default=8, ge=1, le=25)
    max_chars: int = Field(default=12_000, ge=1, le=MAX_CONTEXT_CHARS)


@dataclass(frozen=True)
class SafePath:
    requested_path: str
    relative_path: str
    absolute_path: Path


GitRunner = Callable[[list[str], Path], str]


def _default_git_runner(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        shell=False,
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result.stdout.strip()


def create_bridge_app(
    *,
    repo_root: Path | None = None,
    token: str | None = None,
    git_runner: GitRunner | None = None,
) -> FastAPI:
    root = (repo_root or PROJECT_ROOT).resolve()
    bridge_token = token if token is not None else os.getenv("AEGIS_BRIDGE_TOKEN", "")
    runner = git_runner or _default_git_runner

    app = FastAPI(
        title="Aegis Read-Only ChatGPT Bridge",
        version="1.0.0",
        description="Read-only repository inspection bridge for Aegis Architect.",
        docs_url="/docs",
        redoc_url=None,
    )
    app.state.audit_events = []

    def require_token(x_aegis_bridge_token: str | None = Header(default=None)) -> None:
        if not bridge_token:
            raise HTTPException(status_code=503, detail="bridge token is not configured")
        if x_aegis_bridge_token != bridge_token:
            _record_audit(app, "auth_failed", None, "invalid_or_missing_token")
            raise HTTPException(status_code=401, detail="invalid or missing bridge token")

    auth_dependency = Depends(require_token)

    @app.get("/health", dependencies=[auth_dependency])
    async def health() -> dict[str, Any]:
        head = _safe_git_value(runner, ["rev-parse", "HEAD"], root)
        _record_audit(app, "health", None, "ok")
        return {
            "status": "ok",
            "bridge": "aegis_read_only_chatgpt_bridge",
            "repo_root": str(root),
            "read_only": True,
            "runtime_dispatch_allowed": False,
            "execution_permission": BRIDGE_EXECUTION_PERMISSION,
            "write_endpoints": False,
            "command_execution_endpoint": False,
            "denied_path_policy": denied_path_policy_summary(),
            "current_head": head,
        }

    @app.get("/repo/status", dependencies=[auth_dependency])
    async def repo_status() -> dict[str, Any]:
        status_text = _safe_git_value(runner, ["status", "--porcelain"], root, default="")
        changed_files = [
            line[3:].strip()
            for line in status_text.splitlines()
            if len(line) >= 3 and not _is_denied_relative_path(line[3:].strip())[0]
        ]
        data = {
            "read_only": True,
            "runtime_dispatch_allowed": False,
            "execution_permission": BRIDGE_EXECUTION_PERMISSION,
            "branch": _safe_git_value(runner, ["branch", "--show-current"], root),
            "head": _safe_git_value(runner, ["rev-parse", "HEAD"], root),
            "clean": len(changed_files) == 0,
            "changed_files": changed_files,
            "ignored_runtime_artifacts_exposed_as_content": False,
            "secrets_exposed": False,
        }
        _record_audit(app, "repo_status", None, "ok")
        return data

    @app.get("/repo/tree", dependencies=[auth_dependency])
    async def repo_tree(
        path: str = Query(default="."),
        max_depth: int = Query(default=2, ge=0, le=5),
    ) -> dict[str, Any]:
        safe = _resolve_safe_path(root, path)
        if not safe.absolute_path.exists() or not safe.absolute_path.is_dir():
            raise HTTPException(status_code=404, detail="directory not found")
        nodes: list[dict[str, Any]] = []
        truncated = _collect_tree_nodes(root, safe.absolute_path, max_depth, nodes)
        _record_audit(app, "repo_tree", safe.relative_path, "ok")
        return {
            "read_only": True,
            "path": safe.relative_path,
            "max_depth": max_depth,
            "nodes": nodes,
            "node_count": len(nodes),
            "truncated": truncated,
            "denylist_enforced": True,
        }

    @app.get("/repo/file", dependencies=[auth_dependency])
    async def repo_file(path: str = Query(..., min_length=1)) -> dict[str, Any]:
        safe = _resolve_safe_path(root, path)
        content, size = _read_safe_text_file(safe.absolute_path)
        _record_audit(app, "repo_file", safe.relative_path, "ok")
        return {
            "read_only": True,
            "path": safe.relative_path,
            "size": size,
            "line_count": _line_count(content),
            "content": content,
            "truncated": False,
        }

    @app.post("/repo/search", dependencies=[auth_dependency])
    async def repo_search(request: SearchRequest) -> dict[str, Any]:
        results = _search_files(root, request.query, request.globs, request.max_results)
        _record_audit(app, "repo_search", None, "ok")
        return {
            "read_only": True,
            "query": request.query,
            "results": results,
            "result_count": len(results),
            "max_results": request.max_results,
            "denylist_enforced": True,
        }

    @app.post("/repo/context-pack", dependencies=[auth_dependency])
    async def repo_context_pack(request: ContextPackRequest) -> dict[str, Any]:
        snippets = _build_context_pack(root, request)
        total_chars = sum(len(str(item.get("content", ""))) for item in snippets)
        _record_audit(app, "repo_context_pack", None, "ok")
        return {
            "read_only": True,
            "context_package_is_permission": False,
            "topic": request.topic,
            "snippets": snippets,
            "file_count": len({item["path"] for item in snippets}),
            "total_chars": total_chars,
            "max_chars": request.max_chars,
            "truncated": total_chars >= request.max_chars,
            "denylist_enforced": True,
        }

    @app.get("/repo/git-log", dependencies=[auth_dependency])
    async def repo_git_log(limit: int = Query(default=10, ge=1, le=MAX_GIT_LOG_LIMIT)) -> dict[str, Any]:
        output = _safe_git_value(
            runner,
            [
                "log",
                f"-n{limit}",
                "--pretty=format:%H%x1f%ad%x1f%s",
                "--date=iso-strict",
            ],
            root,
            default="",
        )
        commits = []
        for line in output.splitlines():
            parts = line.split("\x1f", 2)
            if len(parts) == 3:
                commits.append({"hash": parts[0], "date": parts[1], "message": parts[2]})
        _record_audit(app, "repo_git_log", None, "ok")
        return {
            "read_only": True,
            "limit": limit,
            "commits": commits,
            "diff_content_included": False,
        }

    return app


def denied_path_policy_summary() -> dict[str, Any]:
    return {
        "denied_parts": sorted(DENIED_PARTS),
        "denied_exact_names": sorted(DENIED_EXACT_NAMES),
        "denied_name_prefixes": list(DENIED_NAME_PREFIXES),
        "secret_name_fragments": list(SECRET_NAME_FRAGMENTS),
        "binary_extensions_rejected_by_default": sorted(BINARY_EXTENSIONS),
        "outside_repo_blocked": True,
        "path_traversal_blocked": True,
        "absolute_paths_blocked": True,
    }


def _record_audit(app: FastAPI, operation: str, path: str | None, result: str) -> None:
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "operation": operation,
        "path": path,
        "result": result,
        "file_content_logged": False,
    }
    audit_events = app.state.audit_events
    audit_events.append(event)
    if len(audit_events) > 200:
        del audit_events[:-200]
    logger.info("read_only_bridge_request operation=%s path=%s result=%s", operation, path, result)


def _resolve_safe_path(root: Path, requested_path: str) -> SafePath:
    if _has_control_char(requested_path):
        raise HTTPException(status_code=400, detail="path contains control characters")
    if requested_path.strip().startswith("~"):
        raise HTTPException(status_code=403, detail="home-relative paths are denied")
    pure = PureWindowsPath(requested_path)
    if pure.is_absolute() or requested_path.startswith("\\\\"):
        raise HTTPException(status_code=403, detail="absolute or UNC paths are denied")
    raw_parts = [part for part in requested_path.replace("\\", "/").split("/") if part not in {"", "."}]
    if any(part == ".." for part in raw_parts):
        raise HTTPException(status_code=403, detail="path traversal is denied")
    normalized = "/".join(raw_parts) if raw_parts else "."
    denied, reason = _is_denied_relative_path(normalized)
    if denied:
        raise HTTPException(status_code=403, detail=reason)
    absolute = (root / normalized).resolve()
    try:
        absolute.relative_to(root)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail="path outside repo is denied") from exc
    if absolute.is_symlink():
        raise HTTPException(status_code=403, detail="symlink paths are denied")
    return SafePath(requested_path=requested_path, relative_path=normalized, absolute_path=absolute)


def _is_denied_relative_path(relative_path: str) -> tuple[bool, str]:
    parts = [part for part in relative_path.replace("\\", "/").split("/") if part and part != "."]
    lowered_parts = [part.lower() for part in parts]
    for part in lowered_parts:
        if part in DENIED_PARTS:
            return True, f"denied path component: {part}"
    if lowered_parts:
        name = lowered_parts[-1]
        if name in DENIED_EXACT_NAMES:
            return True, f"denied file name: {name}"
        if any(name.startswith(prefix) for prefix in DENIED_NAME_PREFIXES):
            return True, f"denied file name prefix: {name}"
        if any(fragment in name for fragment in SECRET_NAME_FRAGMENTS):
            return True, f"secret-like file name denied: {name}"
        if name.endswith(".log") or name.endswith(".jsonl"):
            return True, f"runtime/log-like file denied: {name}"
    return False, ""


def _has_control_char(value: str) -> bool:
    return any(ord(char) < 32 for char in value)


def _read_safe_text_file(path: Path) -> tuple[str, int]:
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="file not found")
    if path.suffix.lower() in BINARY_EXTENSIONS:
        raise HTTPException(status_code=415, detail="binary/media files are denied")
    size = path.stat().st_size
    if size > MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail="file exceeds bridge size limit")
    data = path.read_bytes()
    if b"\x00" in data:
        raise HTTPException(status_code=415, detail="binary files are denied")
    try:
        return data.decode("utf-8"), size
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=415, detail="non-utf8 file is denied") from exc


def _line_count(content: str) -> int:
    if not content:
        return 0
    return content.count("\n") + (0 if content.endswith("\n") else 1)


def _collect_tree_nodes(root: Path, directory: Path, max_depth: int, nodes: list[dict[str, Any]]) -> bool:
    truncated = False
    if len(nodes) >= MAX_TREE_NODES:
        return True
    try:
        children = sorted(directory.iterdir(), key=lambda path: (not path.is_dir(), path.name.lower()))
    except OSError:
        return truncated
    for child in children:
        if len(nodes) >= MAX_TREE_NODES:
            return True
        try:
            relative = child.resolve().relative_to(root).as_posix()
        except ValueError:
            continue
        denied, _reason = _is_denied_relative_path(relative)
        if denied or child.is_symlink():
            continue
        is_dir = child.is_dir()
        nodes.append(
            {
                "path": relative,
                "name": child.name,
                "type": "directory" if is_dir else "file",
            }
        )
        if is_dir and max_depth > 0:
            truncated = _collect_tree_nodes(root, child, max_depth - 1, nodes) or truncated
    return truncated


def _iter_safe_files(root: Path) -> Iterable[Path]:
    stack = [root]
    while stack:
        directory = stack.pop()
        try:
            children = sorted(directory.iterdir(), key=lambda path: path.name.lower(), reverse=True)
        except OSError:
            continue
        for child in children:
            try:
                relative = child.resolve().relative_to(root).as_posix()
            except ValueError:
                continue
            denied, _reason = _is_denied_relative_path(relative)
            if denied or child.is_symlink():
                continue
            if child.is_dir():
                stack.append(child)
            elif child.is_file():
                yield child


def _search_files(root: Path, query: str, globs: list[str], max_results: int) -> list[dict[str, Any]]:
    lowered_query = query.lower()
    results: list[dict[str, Any]] = []
    for path in _iter_safe_files(root):
        relative = path.resolve().relative_to(root).as_posix()
        if globs and not any(fnmatch.fnmatch(relative, pattern) for pattern in globs):
            continue
        try:
            content, _size = _read_safe_text_file(path)
        except HTTPException:
            continue
        for index, line in enumerate(content.splitlines(), start=1):
            if lowered_query in line.lower():
                results.append(
                    {
                        "path": relative,
                        "line_start": index,
                        "line_end": index,
                        "snippet": line[:500],
                    }
                )
                if len(results) >= max_results:
                    return results
    return results


def _build_context_pack(root: Path, request: ContextPackRequest) -> list[dict[str, Any]]:
    snippets: list[dict[str, Any]] = []
    remaining = request.max_chars
    candidate_paths: list[str] = []
    if request.file_paths:
        candidate_paths = request.file_paths[: request.max_files]
    elif request.topic:
        search_results = _search_files(root, request.topic, [], request.max_files)
        candidate_paths = list(dict.fromkeys(result["path"] for result in search_results))[: request.max_files]

    for requested_path in candidate_paths:
        safe = _resolve_safe_path(root, requested_path)
        content, _size = _read_safe_text_file(safe.absolute_path)
        if remaining <= 0:
            break
        selected = content[:remaining]
        snippets.append(
            {
                "path": safe.relative_path,
                "line_start": 1,
                "line_end": _line_count(selected),
                "content": selected,
                "truncated": len(selected) < len(content),
            }
        )
        remaining -= len(selected)
    return snippets


def _safe_git_value(
    runner: GitRunner,
    args: list[str],
    root: Path,
    *,
    default: str | None = None,
) -> str | None:
    try:
        return runner(args, root)
    except Exception as exc:
        logger.warning("read-only bridge git metadata unavailable for %s: %s", args, exc)
        return default
