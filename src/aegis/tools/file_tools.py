import difflib
import json
import logging
import os
import re
import tempfile
from pathlib import Path

from aegis.core.config import PROJECT_ROOT
from aegis.tools.base import BaseTool

logger = logging.getLogger(__name__)


FORBIDDEN_WRITE_DIRS = ["C:\\Windows", "C:\\Users\\Public"]
ALLOWED_WRITE_ROOTS = [str(PROJECT_ROOT)]
SKIPPED_DIR_NAMES = {".git", ".pytest_cache", ".venv", "__pycache__", "node_modules", ".next"}
MAX_TEXT_FILE_BYTES = 1_000_000


def _resolve_write_path(path: str) -> str:
    if os.path.isabs(path):
        return os.path.abspath(path)
    return os.path.abspath(os.path.join(str(PROJECT_ROOT), path))


def _resolve_read_path(path: str) -> Path:
    if not path:
        return PROJECT_ROOT
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return candidate.resolve()


def _is_forbidden_write_path(abs_path: str) -> str | None:
    normalized_path = os.path.normcase(_resolve_write_path(abs_path))
    for forbidden in FORBIDDEN_WRITE_DIRS:
        normalized_forbidden = os.path.normcase(os.path.abspath(forbidden))
        try:
            if os.path.commonpath([normalized_path, normalized_forbidden]) == normalized_forbidden:
                return forbidden
        except ValueError:
            continue
    return None


def _is_allowed_write_path(abs_path: str) -> bool:
    normalized_path = os.path.normcase(_resolve_write_path(abs_path))
    for root in ALLOWED_WRITE_ROOTS:
        normalized_root = os.path.normcase(os.path.abspath(root))
        try:
            if os.path.commonpath([normalized_path, normalized_root]) == normalized_root:
                return True
        except ValueError:
            continue
    return False


def _json_response(**payload) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _is_text_file(path: Path, max_bytes: int = MAX_TEXT_FILE_BYTES) -> bool:
    try:
        return path.is_file() and path.stat().st_size <= max_bytes
    except OSError:
        return False


def _safe_walk(root: Path, recursive: bool):
    if recursive:
        iterator = root.rglob("*")
    else:
        iterator = root.iterdir()
    for item in iterator:
        if any(part in SKIPPED_DIR_NAMES for part in item.parts):
            continue
        yield item


def _diff_preview(before: str, after: str, *, fromfile: str = "before", tofile: str = "after") -> str:
    diff = difflib.unified_diff(
        before.splitlines(keepends=True),
        after.splitlines(keepends=True),
        fromfile=fromfile,
        tofile=tofile,
        lineterm="",
    )
    return "\n".join(list(diff)[:160])


def _atomic_write(abs_path: str, content: str) -> None:
    parent = os.path.dirname(abs_path)
    os.makedirs(parent, exist_ok=True)

    tmp_path = None
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=parent,
        delete=False,
        prefix=".aegis-write-",
        suffix=".tmp",
    ) as f:
        tmp_path = f.name
        f.write(content)
        f.flush()
        os.fsync(f.fileno())

    try:
        os.replace(tmp_path, abs_path)
    except Exception:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def _ensure_allowed_write(path: str) -> tuple[str | None, str | None]:
    abs_path = _resolve_write_path(path)
    forbidden = _is_forbidden_write_path(abs_path)
    if forbidden:
        return None, f"Error: Writing to {forbidden} is forbidden for security reasons."
    if not _is_allowed_write_path(abs_path):
        return None, "Error: Writing outside allowed roots is forbidden for security reasons."
    return abs_path, None


class ListDirectoryTool(BaseTool):
    name = "list_directory"
    description = "List files and folders under a local directory."

    async def run(self, path: str = ".", recursive: bool = False, max_entries: int = 200, **kwargs) -> str:
        self.log_action(path=path, recursive=recursive, max_entries=max_entries)
        root = _resolve_read_path(path)
        if not root.exists():
            return f"Error: Directory not found at {root}"
        if not root.is_dir():
            return f"Error: Path is not a directory: {root}"

        entries = []
        for item in _safe_walk(root, recursive=bool(recursive)):
            if len(entries) >= max_entries:
                break
            try:
                stat = item.stat()
                entries.append({
                    "path": str(item),
                    "relative_path": str(item.relative_to(root)),
                    "type": "directory" if item.is_dir() else "file",
                    "size_bytes": 0 if item.is_dir() else stat.st_size,
                    "modified_at": int(stat.st_mtime * 1000),
                })
            except OSError as exc:
                entries.append({"path": str(item), "type": "error", "error": str(exc)})

        return _json_response(
            path=str(root),
            recursive=bool(recursive),
            entry_count=len(entries),
            truncated=len(entries) >= max_entries,
            entries=entries,
        )


class SearchFilesTool(BaseTool):
    name = "search_files"
    description = "Search for file names by glob or regular expression."

    async def run(
        self,
        query: str | None = None,
        path: str = ".",
        pattern: str | None = None,
        regex: bool = False,
        max_results: int = 100,
        **kwargs,
    ) -> str:
        needle = pattern or query or "*"
        self.log_action(path=path, pattern=needle, regex=regex, max_results=max_results)
        root = _resolve_read_path(path)
        if not root.exists():
            return f"Error: Search root not found at {root}"
        if not root.is_dir():
            return f"Error: Search root is not a directory: {root}"

        matcher = re.compile(needle, re.IGNORECASE) if regex else None
        matches = []
        for item in _safe_walk(root, recursive=True):
            if len(matches) >= max_results:
                break
            name = item.name
            hit = bool(matcher.search(name)) if matcher else item.match(needle) or needle.lower() in name.lower()
            if not hit:
                continue
            matches.append({
                "path": str(item),
                "relative_path": str(item.relative_to(root)),
                "type": "directory" if item.is_dir() else "file",
            })

        return _json_response(
            path=str(root),
            pattern=needle,
            regex=bool(regex),
            match_count=len(matches),
            truncated=len(matches) >= max_results,
            matches=matches,
        )


class GrepInFilesTool(BaseTool):
    name = "grep_in_files"
    description = "Search text contents in bounded local files."

    async def run(
        self,
        query: str,
        path: str = ".",
        regex: bool = False,
        max_matches: int = 100,
        **kwargs,
    ) -> str:
        self.log_action(path=path, query=query, regex=regex, max_matches=max_matches)
        root = _resolve_read_path(path)
        if not root.exists():
            return f"Error: Grep root not found at {root}"
        if root.is_file():
            candidates = [root]
        else:
            candidates = [item for item in _safe_walk(root, recursive=True) if _is_text_file(item)]

        matcher = re.compile(query, re.IGNORECASE) if regex else None
        matches = []
        for file_path in candidates:
            if len(matches) >= max_matches:
                break
            try:
                for line_no, line in enumerate(file_path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
                    hit = bool(matcher.search(line)) if matcher else query.lower() in line.lower()
                    if hit:
                        matches.append({
                            "path": str(file_path),
                            "line": line_no,
                            "text": line[:500],
                        })
                        if len(matches) >= max_matches:
                            break
            except OSError as exc:
                matches.append({"path": str(file_path), "line": 0, "text": f"Error: {exc}"})

        return _json_response(
            path=str(root),
            query=query,
            regex=bool(regex),
            match_count=len(matches),
            truncated=len(matches) >= max_matches,
            matches=matches,
        )


class FileInfoTool(BaseTool):
    name = "file_info"
    description = "Return bounded file metadata."

    async def run(self, path: str, **kwargs) -> str:
        self.log_action(path=path)
        target = _resolve_read_path(path)
        if not target.exists():
            return f"Error: Path not found at {target}"
        stat = target.stat()
        return _json_response(
            path=str(target),
            exists=True,
            type="directory" if target.is_dir() else "file",
            size_bytes=0 if target.is_dir() else stat.st_size,
            modified_at=int(stat.st_mtime * 1000),
            suffix=target.suffix,
        )

class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Read the contents of a local file."

    async def run(self, path: str, **kwargs) -> str:
        self.log_action(path=path)
        target = _resolve_read_path(path)
        if not target.exists():
            return f"Error: File not found at {target}"
        if not target.is_file():
            return f"Error: Path is not a file: {target}"
        try:
            if target.stat().st_size > 10 * 1024 * 1024:
                return "Error: File exceeds 10 MB read limit"
        except OSError as exc:
            return f"Read error: {str(exc)}"
        
        try:
            with open(target, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Read error: {str(e)}"

class WriteFileTool(BaseTool):
    name = "write_file"
    description = "Write content to a local file."

    async def run(self, path: str, content: str, **kwargs) -> str:
        self.log_action(path=path)
        
        abs_path, error = _ensure_allowed_write(path)
        if error:
            return error

        try:
            _atomic_write(abs_path, content)
            return f"Successfully written to {path}"
        except Exception as e:
            return f"Write error: {str(e)}"


class CreateFileTool(BaseTool):
    name = "create_file"
    description = "Create a new file after workspace-boundary validation."

    async def run(self, path: str, content: str = "", dry_run: bool = False, **kwargs) -> str:
        self.log_action(path=path, dry_run=dry_run)
        abs_path, error = _ensure_allowed_write(path)
        if error:
            return error
        if os.path.exists(abs_path):
            return f"Error: File already exists at {abs_path}"

        diff_preview = _diff_preview("", content, fromfile="new-file", tofile=str(abs_path))
        if dry_run:
            return _json_response(
                dry_run=True,
                path=abs_path,
                would_create=True,
                bytes=len(content.encode("utf-8")),
                diff_preview=diff_preview,
            )

        try:
            _atomic_write(abs_path, content)
            return f"Successfully created {abs_path}"
        except Exception as exc:
            return f"Create error: {exc}"


class EditFileTool(BaseTool):
    name = "edit_file"
    description = "Apply a deterministic text replacement after diff preview support."

    async def run(
        self,
        path: str,
        target: str,
        replacement: str,
        dry_run: bool = False,
        **kwargs,
    ) -> str:
        self.log_action(path=path, dry_run=dry_run)
        abs_path, error = _ensure_allowed_write(path)
        if error:
            return error
        if not os.path.exists(abs_path):
            return f"Error: File not found at {abs_path}"

        try:
            before = Path(abs_path).read_text(encoding="utf-8")
        except Exception as exc:
            return f"Edit error: {exc}"

        if target not in before:
            return "Error: Target text not found; edit_file requires an exact target match."

        after = before.replace(target, replacement, 1)
        diff_preview = _diff_preview(before, after, fromfile=str(abs_path), tofile=str(abs_path))
        if dry_run:
            return _json_response(
                dry_run=True,
                path=abs_path,
                would_edit=True,
                diff_preview=diff_preview,
            )

        try:
            _atomic_write(abs_path, after)
            return f"Successfully edited {abs_path}"
        except Exception as exc:
            return f"Edit error: {exc}"


class DeleteFileTool(BaseTool):
    name = "delete_file"
    description = "Blocked placeholder for future verified delete workflow."

    async def run(self, path: str, **kwargs) -> str:
        self.log_action(path=path)
        return "Error: delete_file is critical-risk and blocked in Tool Contract & Sandbox v1."


class MoveFileTool(BaseTool):
    name = "move_file"
    description = "Blocked placeholder for future verified move workflow."

    async def run(self, path: str, destination: str, **kwargs) -> str:
        self.log_action(path=path, destination=destination)
        return "Error: move_file is critical-risk and blocked in Tool Contract & Sandbox v1."
