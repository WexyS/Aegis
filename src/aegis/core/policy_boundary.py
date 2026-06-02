from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping

from aegis.core.approval_semantics import DecisionStatus


POLICY_BOUNDARY_VERSION = "policy-boundary/1"
POST_FOUNDATION_POLICY_VERSION = "post-foundation-policy-extension/1"

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
    "type",
    "open_app",
    "focus_app",
    "close_app",
    "run_command",
    "git_action",
    "general_chat",
}

SIDE_EFFECTING_TOOL_NAMES = {
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

POST_FOUNDATION_RISK_TIERS = {
    "read_only",
    "local_state_read",
    "local_file_write",
    "app_launch",
    "app_focus",
    "ui_click",
    "external_network",
    "tool_execution",
    "memory_write",
    "model_routing",
    "plugin_execution",
    "cleanup_archive",
    "cleanup_compaction",
    "destructive_system_change",
}

SIDE_EFFECTING_RISK_TIERS = {
    "local_file_write",
    "app_launch",
    "app_focus",
    "ui_click",
    "external_network",
    "tool_execution",
    "memory_write",
    "model_routing",
    "plugin_execution",
    "cleanup_archive",
    "cleanup_compaction",
    "destructive_system_change",
}

EVIDENCE_REQUIRED_RISK_TIERS = SIDE_EFFECTING_RISK_TIERS - {
    "memory_write",
    "model_routing",
}

OPERATOR_BOUNDARY_REQUIRED_RISK_TIERS = {
    "cleanup_archive",
    "cleanup_compaction",
    "destructive_system_change",
}

POST_FOUNDATION_CAPABILITY_CATEGORIES = {
    "context_compilation",
    "memory_read",
    "memory_write",
    "local_tool_read",
    "local_tool_write",
    "app_discovery",
    "app_launch",
    "desktop_verification",
    "mcp_tool_call",
    "model_provider_selection",
    "plugin_action",
    "vertical_pack_read",
    "vertical_pack_write",
    "cleanup_inventory",
    "cleanup_archive",
    "cleanup_compaction",
}

CAPABILITY_ALLOWED_RISK_TIERS = {
    "context_compilation": {"read_only"},
    "memory_read": {"local_state_read"},
    "memory_write": {"memory_write"},
    "local_tool_read": {"local_state_read"},
    "local_tool_write": {"local_file_write"},
    "app_discovery": {"read_only", "local_state_read"},
    "app_launch": {"app_launch"},
    "desktop_verification": {"read_only", "local_state_read"},
    "mcp_tool_call": {"tool_execution", "external_network"},
    "model_provider_selection": {"model_routing"},
    "plugin_action": {"plugin_execution"},
    "vertical_pack_read": {"read_only", "local_state_read"},
    "vertical_pack_write": {"local_file_write", "tool_execution", "plugin_execution"},
    "cleanup_inventory": {"read_only", "local_state_read"},
    "cleanup_archive": {"cleanup_archive"},
    "cleanup_compaction": {"cleanup_compaction"},
}

UNTRUSTED_PERMISSION_AUTHORITIES = {
    "context_compiler",
    "frontend_projection",
    "memory",
    "model_output",
    "plugin_manifest",
    "skill_manifest",
    "retrieval",
}

TRUSTED_POLICY_AUTHORITIES = {
    "backend_policy",
    "operator_approval",
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


@dataclass(frozen=True)
class CapabilityPolicyDecision:
    policy_version: str
    capability_category: str
    risk_tier: str
    source_authority: str
    known_capability: bool
    known_risk_tier: bool
    policy_rule_present: bool
    approval_required: bool
    approval_granted: bool
    evidence_required: bool
    evidence_expectation_present: bool
    operator_boundary_required: bool
    operator_boundary_approved: bool
    contract_ready: bool
    runtime_dispatch_allowed: bool
    execution_permission: str
    decision_status: str
    blocked_reasons: tuple[str, ...]
    audit_required: bool = True
    context_may_grant_permission: bool = False
    memory_may_grant_permission: bool = False
    model_may_grant_permission: bool = False
    plugin_manifest_may_grant_permission: bool = False
    frontend_may_grant_permission: bool = False


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


def evaluate_capability_policy_contract(
    capability_category: str,
    risk_tier: str,
    *,
    source_authority: str = "backend_policy",
    policy_rule: str | None = None,
    approval_granted: bool = False,
    evidence_expectation: Mapping[str, Any] | None = None,
    operator_boundary_approved: bool = False,
) -> CapabilityPolicyDecision:
    """Read-only future capability contract evaluator.

    This helper classifies whether a future capability request has enough
    policy metadata for design-time review. It never grants runtime dispatch
    permission and is not wired into the executor.
    """

    capability = str(capability_category or "")
    tier = str(risk_tier or "")
    authority = str(source_authority or "")
    known_capability = capability in POST_FOUNDATION_CAPABILITY_CATEGORIES
    known_risk_tier = tier in POST_FOUNDATION_RISK_TIERS
    allowed_tiers = CAPABILITY_ALLOWED_RISK_TIERS.get(capability, set())
    tier_matches_capability = known_capability and known_risk_tier and tier in allowed_tiers
    policy_rule_present = bool(policy_rule)
    source_authority_allowed = authority in TRUSTED_POLICY_AUTHORITIES
    source_authority_untrusted = authority in UNTRUSTED_PERMISSION_AUTHORITIES
    approval_required = tier in SIDE_EFFECTING_RISK_TIERS
    evidence_required = tier in EVIDENCE_REQUIRED_RISK_TIERS
    evidence_expectation_present = isinstance(evidence_expectation, Mapping) and bool(evidence_expectation)
    operator_boundary_required = tier in OPERATOR_BOUNDARY_REQUIRED_RISK_TIERS

    blocked: list[str] = []
    if not known_capability:
        blocked.append("unknown_capability")
    if not known_risk_tier:
        blocked.append("unknown_risk_tier")
    if known_capability and known_risk_tier and not tier_matches_capability:
        blocked.append("risk_tier_not_allowed_for_capability")
    if not policy_rule_present:
        blocked.append("missing_policy_rule")
    if source_authority_untrusted:
        blocked.append(f"{authority}_cannot_grant_permission")
    elif not source_authority_allowed:
        blocked.append("untrusted_policy_authority")
    if approval_required and not approval_granted:
        blocked.append("approval_required")
    if evidence_required and not evidence_expectation_present:
        blocked.append("missing_evidence_expectation")
    if operator_boundary_required and not operator_boundary_approved:
        blocked.append("operator_boundary_required")

    metadata_ready = not blocked
    non_executing_review_only = tier in {"read_only", "local_state_read"} and metadata_ready
    decision_status = "review_ready" if non_executing_review_only else "denied"
    return CapabilityPolicyDecision(
        policy_version=POST_FOUNDATION_POLICY_VERSION,
        capability_category=capability,
        risk_tier=tier,
        source_authority=authority,
        known_capability=known_capability,
        known_risk_tier=known_risk_tier,
        policy_rule_present=policy_rule_present,
        approval_required=approval_required,
        approval_granted=approval_granted,
        evidence_required=evidence_required,
        evidence_expectation_present=evidence_expectation_present,
        operator_boundary_required=operator_boundary_required,
        operator_boundary_approved=operator_boundary_approved,
        contract_ready=metadata_ready,
        runtime_dispatch_allowed=False,
        execution_permission="not_granted_by_policy_extension",
        decision_status=decision_status,
        blocked_reasons=tuple(blocked),
    )


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
