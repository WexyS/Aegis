from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable

from aegis.core.approval_semantics import DecisionStatus


POLICY_BOUNDARY_VERSION = "policy-boundary/1"

POLICY_DISPATCHABLE_TOOL_NAMES = {
    "read_file",
    "list_directory",
    "search_files",
    "grep_in_files",
    "file_info",
    "write_file",
    "create_file",
    "edit_file",
    "read_page",
    "scroll",
    "search_web",
    "open_url",
    "click",
    "type",
    "open_app",
    "focus_app",
    "close_app",
    "run_command",
    "git_action",
    "general_chat",
}

SIDE_EFFECTING_TOOL_NAMES = {
    "click",
    "type",
    "write_file",
    "create_file",
    "edit_file",
    "git_action",
    "open_url",
    "open_app",
    "close_app",
    "focus_app",
}

NON_RESUMABLE_APPROVAL_TOOLS = {"click", "browser_click", "desktop_click"}
NON_RESUMABLE_POLICY_MARKERS = {
    "generic_click.quarantined",
    "target_resolution_missing",
}


@dataclass(frozen=True)
class PolicyBoundaryDecision:
    boundary_version: str
    dispatch_allowed: bool
    decision_status: str
    policy_rule: str
    reason: str
    requires_approval: bool = False
    requires_clarification: bool = False
    blocked: bool = False
    approval_granted: bool = False
    resume_allowed: bool = False
    not_executed: bool = True


def approval_resolution_can_resume(guard_decision: Any) -> bool:
    """Return whether an approved policy decision is allowed to re-enter dispatch.

    Approval is a lifecycle transition, not execution permission by itself. This
    helper only answers whether the already classified decision is eligible to
    continue into the normal executor boundary after the orchestrator re-runs
    policy classification.
    """

    request = getattr(guard_decision, "approval_request", None)
    proposed_action = getattr(request, "proposed_action", None)
    tool = str(getattr(proposed_action, "tool", "") or "")
    policy_rule = str(getattr(guard_decision, "policy_rule", "") or "")
    if tool in NON_RESUMABLE_APPROVAL_TOOLS:
        return False
    if any(marker in policy_rule for marker in NON_RESUMABLE_POLICY_MARKERS):
        return False
    return True


def evaluate_policy_boundary(
    guard_decision: Any,
    *,
    approval_granted: bool = False,
) -> PolicyBoundaryDecision:
    status_value = _decision_status_value(guard_decision)
    resume_allowed = (
        status_value == DecisionStatus.APPROVAL_REQUIRED.value
        and approval_granted
        and approval_resolution_can_resume(guard_decision)
    )
    dispatch_allowed = status_value == DecisionStatus.READY.value or resume_allowed
    return PolicyBoundaryDecision(
        boundary_version=POLICY_BOUNDARY_VERSION,
        dispatch_allowed=dispatch_allowed,
        decision_status=status_value,
        policy_rule=str(getattr(guard_decision, "policy_rule", "") or ""),
        reason=str(getattr(guard_decision, "reason", "") or ""),
        requires_approval=bool(getattr(guard_decision, "requires_approval", False)),
        requires_clarification=bool(getattr(guard_decision, "requires_clarification", False)),
        blocked=bool(getattr(guard_decision, "blocked", False)),
        approval_granted=approval_granted,
        resume_allowed=resume_allowed,
        not_executed=not dispatch_allowed,
    )


def side_effects_missing_dispatch_contract(
    plan: Iterable[Any],
    *,
    tool_spec_lookup: Callable[[str], Any | None] | None = None,
    dispatchable_tool_names: set[str] | None = None,
) -> list[str]:
    dispatchable = dispatchable_tool_names if dispatchable_tool_names is not None else POLICY_DISPATCHABLE_TOOL_NAMES
    missing: list[str] = []
    for intent in plan:
        tool_name = str(getattr(intent, "intent", "") or "")
        spec = tool_spec_lookup(tool_name) if tool_spec_lookup is not None else None
        side_effecting = bool(getattr(spec, "side_effecting", False)) if spec else tool_name in SIDE_EFFECTING_TOOL_NAMES
        if side_effecting and tool_name not in dispatchable:
            missing.append(tool_name)
    return missing


def _decision_status_value(guard_decision: Any) -> str:
    status = getattr(guard_decision, "decision_status", None)
    if isinstance(status, DecisionStatus):
        return status.value
    return str(status or "")
