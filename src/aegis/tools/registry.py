from __future__ import annotations

from typing import Any

from aegis.core.config import CONFIG_DIR, load_yaml
from aegis.core.constants import RiskLevel
from aegis.tools.base import ToolSpec
from aegis.tools.desktop_tools import CloseAppTool, FocusTool, OpenAppTool, TypeTool
from aegis.tools.file_tools import (
    CreateFileTool,
    DeleteFileTool,
    EditFileTool,
    FileInfoTool,
    GrepInFilesTool,
    ListDirectoryTool,
    MoveFileTool,
    ReadFileTool,
    SearchFilesTool,
    WriteFileTool,
)
from aegis.tools.git_tools import GitActionTool
from aegis.tools.shell_tools import RunCommandTool
from aegis.tools.system_tools import GeneralChatTool
from aegis.tools.web_tools import ClickTool, OpenURLTool, ReadPageTool, ScrollTool, SearchWebTool


TOOLS = {
    # Desktop
    "open_app": OpenAppTool(),
    "close_app": CloseAppTool(),
    "focus_app": FocusTool(),
    "type": TypeTool(),
    # Web
    "open_url": OpenURLTool(),
    "search_web": SearchWebTool(),
    "click": ClickTool(),
    "scroll": ScrollTool(),
    "read_page": ReadPageTool(),
    # File
    "list_directory": ListDirectoryTool(),
    "search_files": SearchFilesTool(),
    "grep_in_files": GrepInFilesTool(),
    "file_info": FileInfoTool(),
    "read_file": ReadFileTool(),
    "write_file": WriteFileTool(),
    "create_file": CreateFileTool(),
    "edit_file": EditFileTool(),
    "delete_file": DeleteFileTool(),
    "move_file": MoveFileTool(),
    # Shell
    "run_command": RunCommandTool(),
    # Git
    "git_action": GitActionTool(),
    # System
    "general_chat": GeneralChatTool(),
}


def _object(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    return {"type": "object", "properties": properties, "required": required or []}


def _spec(
    name: str,
    category: str,
    description: str,
    risk: RiskLevel,
    *,
    requires_approval: bool | None = None,
    timeout_seconds: float = 30.0,
    cancellation_supported: bool = False,
    evidence_policy: str = "none",
    dry_run_supported: bool = False,
    side_effecting: bool = False,
    input_schema: dict[str, Any] | None = None,
    output_schema: dict[str, Any] | None = None,
) -> ToolSpec:
    return ToolSpec(
        name=name,
        category=category,
        description=description,
        input_schema=input_schema or _object({}),
        output_schema=output_schema or _object({"result": {"type": "string"}}),
        risk_level=risk,
        requires_approval=risk.requires_approval if requires_approval is None else requires_approval,
        timeout_seconds=timeout_seconds,
        cancellation_supported=cancellation_supported,
        evidence_policy=evidence_policy,
        dry_run_supported=dry_run_supported,
        side_effecting=side_effecting,
    )


TOOL_SPECS: dict[str, ToolSpec] = {
    "open_app": _spec("open_app", "desktop", "Open or focus a local application.", RiskLevel.MEDIUM, timeout_seconds=15, evidence_policy="desktop_verifier", side_effecting=True, input_schema=_object({"app": {"type": "string"}}, ["app"])),
    "close_app": _spec("close_app", "desktop", "Close a running application.", RiskLevel.MEDIUM, timeout_seconds=10, evidence_policy="desktop_verifier", side_effecting=True, input_schema=_object({"app": {"type": "string"}}, ["app"])),
    "focus_app": _spec("focus_app", "desktop", "Focus an existing application window.", RiskLevel.MEDIUM, timeout_seconds=8, evidence_policy="desktop_verifier", side_effecting=True, input_schema=_object({"app": {"type": "string"}}, ["app"])),
    "type": _spec("type", "desktop", "Type text into the focused target.", RiskLevel.MEDIUM, timeout_seconds=10, evidence_policy="desktop_verifier", side_effecting=True, input_schema=_object({"text": {"type": "string"}}, ["text"])),
    "open_url": _spec("open_url", "web", "Open a URL in the controlled browser.", RiskLevel.LOW, timeout_seconds=15, evidence_policy="browser_context", side_effecting=True, input_schema=_object({"url": {"type": "string"}}, ["url"])),
    "search_web": _spec("search_web", "web", "Search the web in the controlled browser.", RiskLevel.LOW, timeout_seconds=20, evidence_policy="read_only_hash", input_schema=_object({"query": {"type": "string"}}, ["query"])),
    "click": _spec("click", "web", "Click a browser element or coordinate.", RiskLevel.MEDIUM, timeout_seconds=8, evidence_policy="browser_context", side_effecting=True),
    "scroll": _spec("scroll", "web", "Scroll the active browser page.", RiskLevel.LOW, timeout_seconds=5, evidence_policy="browser_context", side_effecting=True),
    "read_page": _spec("read_page", "web", "Read the active browser page text.", RiskLevel.LOW, timeout_seconds=10, evidence_policy="read_only_hash"),
    "list_directory": _spec("list_directory", "file", "List files and folders under a directory.", RiskLevel.LOW, timeout_seconds=10, evidence_policy="read_only_hash"),
    "search_files": _spec("search_files", "file", "Search file names by glob or regex.", RiskLevel.LOW, timeout_seconds=15, evidence_policy="read_only_hash"),
    "grep_in_files": _spec("grep_in_files", "file", "Search text in bounded local files.", RiskLevel.LOW, timeout_seconds=20, evidence_policy="read_only_hash", input_schema=_object({"query": {"type": "string"}}, ["query"])),
    "file_info": _spec("file_info", "file", "Read file metadata.", RiskLevel.LOW, timeout_seconds=5, evidence_policy="read_only_hash", input_schema=_object({"path": {"type": "string"}}, ["path"])),
    "read_file": _spec("read_file", "file", "Read a local file.", RiskLevel.LOW, timeout_seconds=10, evidence_policy="read_only_hash", input_schema=_object({"path": {"type": "string"}}, ["path"])),
    "write_file": _spec("write_file", "file", "Write a complete file inside the workspace boundary.", RiskLevel.MEDIUM, timeout_seconds=10, evidence_policy="file_diff", side_effecting=True, dry_run_supported=True, input_schema=_object({"path": {"type": "string"}, "content": {"type": "string"}}, ["path", "content"])),
    "create_file": _spec("create_file", "file", "Create a new file inside the workspace boundary.", RiskLevel.MEDIUM, timeout_seconds=10, evidence_policy="file_diff", side_effecting=True, dry_run_supported=True, input_schema=_object({"path": {"type": "string"}, "content": {"type": "string"}}, ["path"])),
    "edit_file": _spec("edit_file", "file", "Apply an exact text replacement inside the workspace boundary.", RiskLevel.MEDIUM, timeout_seconds=10, evidence_policy="file_diff", side_effecting=True, dry_run_supported=True, input_schema=_object({"path": {"type": "string"}, "target": {"type": "string"}, "replacement": {"type": "string"}}, ["path", "target", "replacement"])),
    "delete_file": _spec("delete_file", "file", "Critical-risk delete placeholder; blocked in v1.", RiskLevel.CRITICAL, timeout_seconds=5, requires_approval=False, evidence_policy="blocked", side_effecting=True, input_schema=_object({"path": {"type": "string"}}, ["path"])),
    "move_file": _spec("move_file", "file", "Critical-risk move placeholder; blocked in v1.", RiskLevel.CRITICAL, timeout_seconds=5, requires_approval=False, evidence_policy="blocked", side_effecting=True, input_schema=_object({"path": {"type": "string"}, "destination": {"type": "string"}}, ["path", "destination"])),
    "run_command": _spec("run_command", "shell", "Run allowlisted read-only shell introspection.", RiskLevel.LOW, timeout_seconds=10, cancellation_supported=True, evidence_policy="shell_result", input_schema=_object({"command": {"type": "string"}}, ["command"])),
    "git_action": _spec("git_action", "git", "Run verified git status only in v1.", RiskLevel.LOW, timeout_seconds=10, evidence_policy="git_status", input_schema=_object({"git_cmd": {"type": "string"}}, ["git_cmd"])),
    "general_chat": _spec("general_chat", "system", "Return a bounded local help response.", RiskLevel.NONE, timeout_seconds=5, evidence_policy="none"),
}


def get_tool(name: str):
    """Retrieve a tool by its registered name."""
    return TOOLS.get(name)


def get_tool_spec(name: str) -> ToolSpec | None:
    return TOOL_SPECS.get(name)


def list_tools() -> list[str]:
    """Return registered tool names."""
    return sorted(TOOLS.keys())


def list_tool_specs() -> list[ToolSpec]:
    return [TOOL_SPECS[name] for name in sorted(TOOL_SPECS)]


def load_tool_config() -> dict[str, Any]:
    return load_yaml(CONFIG_DIR / "tools.yaml").get("tools", {})


def validate_registry_drift() -> dict[str, Any]:
    config_tools = load_tool_config()
    code_names = set(TOOLS)
    spec_names = set(TOOL_SPECS)
    config_names = set(config_tools)
    mismatches: list[dict[str, Any]] = []

    for name in sorted(code_names & spec_names & config_names):
        cfg = config_tools[name] or {}
        spec = TOOL_SPECS[name]
        expected = {
            "risk": spec.risk_level.value if isinstance(spec.risk_level, RiskLevel) else str(spec.risk_level),
            "requires_approval": spec.requires_approval,
            "timeout_seconds": spec.timeout_seconds,
            "category": spec.category,
            "evidence_policy": spec.evidence_policy,
            "dry_run_supported": spec.dry_run_supported,
            "cancellation_supported": spec.cancellation_supported,
        }
        for key, expected_value in expected.items():
            if key in cfg and cfg[key] != expected_value:
                mismatches.append({
                    "tool": name,
                    "field": key,
                    "config": cfg[key],
                    "code": expected_value,
                })

    missing_in_config = sorted(code_names - config_names)
    missing_in_code = sorted(config_names - code_names)
    missing_specs = sorted(code_names - spec_names)
    status = "ok" if not (missing_in_config or missing_in_code or missing_specs or mismatches) else "warning"

    return {
        "status": status,
        "missing_in_config": missing_in_config,
        "missing_in_code": missing_in_code,
        "missing_specs": missing_specs,
        "mismatches": mismatches,
    }


def get_tool_registry_snapshot() -> dict[str, Any]:
    drift = validate_registry_drift()
    specs = [spec.public_dict() for spec in list_tool_specs()]
    return {
        "scan_version": "tool-registry/1",
        "read_only": True,
        "status": drift["status"],
        "registered_count": len(TOOLS),
        "configured_count": len(load_tool_config()),
        "spec_count": len(TOOL_SPECS),
        "drift": drift,
        "tools": specs,
    }
