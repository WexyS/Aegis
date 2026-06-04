from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping

from aegis.core.approval_semantics import DecisionStatus


POLICY_BOUNDARY_VERSION = "policy-boundary/1"
POST_FOUNDATION_POLICY_VERSION = "post-foundation-policy-extension/1"
POLICY_EXTENSION_EXECUTION_PERMISSION = "not_granted_by_policy_extension"

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

POLICY_SUBJECT_KINDS = {
    "runtime_command",
    "tool_action",
    "memory_operation",
    "context_operation",
    "model_operation",
    "vector_operation",
    "web_research_operation",
    "repo_audit_operation",
    "external_agent_operation",
    "plugin_operation",
    "vertical_pack_operation",
    "capability_lease_operation",
    "playbook_operation",
    "rollback_operation",
    "frontend_request",
    "mcp_output",
    "unknown",
}

POLICY_ACTION_KINDS = {
    "read_only_observation",
    "metadata_validation",
    "proposal_only",
    "simulate",
    "dry_run_preview",
    "memory_write",
    "memory_retrieve",
    "memory_delete",
    "memory_export",
    "context_retrieve",
    "context_package",
    "vector_index",
    "embedding_generate",
    "rerank",
    "model_call",
    "cloud_model_call",
    "web_query",
    "repo_file_read",
    "repo_inventory_run",
    "external_agent_observe",
    "external_agent_track",
    "plugin_load",
    "plugin_execute",
    "lease_create",
    "lease_use",
    "playbook_record",
    "playbook_replay",
    "rollback_snapshot",
    "rollback_execute",
    "frontend_authority_claim",
    "mcp_authority_claim",
    "unknown",
}

POLICY_OUTCOMES = {
    "allowed_metadata_only",
    "allowed_proposal_only",
    "requires_approval",
    "requires_capability_lease",
    "requires_human_review",
    "requires_identity_scope",
    "requires_memory_governance",
    "requires_context_policy",
    "requires_provider_policy",
    "requires_evidence_plan",
    "requires_verifier_plan",
    "blocked_by_policy",
    "blocked_by_privacy",
    "blocked_by_unknown_scope",
    "blocked_by_missing_governance",
    "blocked_by_sensitive_data",
    "blocked_by_frontend_authority",
    "blocked_by_mcp_authority",
    "blocked_by_unimplemented_feature",
    "unsupported",
    "unknown",
}

METADATA_ONLY_ACTIONS = {
    "read_only_observation",
    "metadata_validation",
    "simulate",
    "dry_run_preview",
}

PROPOSAL_ONLY_ACTIONS = {
    "proposal_only",
    "context_package",
    "repo_inventory_run",
    "external_agent_observe",
    "playbook_record",
}

MEMORY_ACTIONS = {
    "memory_write",
    "memory_retrieve",
    "memory_delete",
    "memory_export",
}

MODEL_ACTIONS = {
    "model_call",
    "cloud_model_call",
}

VECTOR_ACTIONS = {
    "vector_index",
    "embedding_generate",
    "rerank",
}

REPO_FILE_READ_ACTIONS = {
    "repo_file_read",
}

UNIMPLEMENTED_ACTIONS = {
    "context_retrieve",
    "web_query",
    "external_agent_track",
    "plugin_load",
    "plugin_execute",
    "lease_create",
    "lease_use",
    "playbook_replay",
    "rollback_snapshot",
    "rollback_execute",
}

SENSITIVE_CLASSES_BLOCKED_BY_DEFAULT = {
    "secret_like",
    "credential_like",
}

FORBIDDEN_POLICY_EXTENSION_TRUTHY_FIELDS = {
    "authority": "authority_must_be_false",
    "runtime_dispatch_allowed": "runtime_dispatch_not_allowed",
    "approval_grant": "approval_grant_not_allowed",
    "capability_grant": "capability_grant_not_allowed",
    "lease_grant": "lease_grant_not_allowed",
    "evidence_provided_by_policy": "policy_cannot_provide_evidence",
    "evidence_provided_by_identity_scope": "policy_cannot_provide_evidence",
    "evidence_provided_by_memory_governance": "policy_cannot_provide_evidence",
    "evidence_provided_by_inventory": "policy_cannot_provide_evidence",
    "evidence_provided_by_model": "policy_cannot_provide_evidence",
    "evidence_provided_by_output": "policy_cannot_provide_evidence",
    "evidence_created": "policy_cannot_provide_evidence",
    "verifier_success": "policy_cannot_mark_verifier_success",
    "verified_success": "policy_cannot_mark_verifier_success",
    "success": "success_claim_denied",
    "proof": "proof_claim_denied",
    "certification_claim": "certification_claim_denied",
    "model_output_is_truth": "model_output_truth_claim_denied",
    "model_output_as_evidence": "model_output_evidence_claim_denied",
    "model_output_as_policy": "model_output_policy_claim_denied",
    "model_output_as_compliance_proof": "model_output_compliance_claim_denied",
    "frontend_authority": "frontend_authority_not_allowed",
    "output_is_authority": "output_authority_not_allowed",
    "router_decision_final": "router_decision_not_final",
    "auto_mode_execution_allowed": "auto_mode_execution_not_allowed",
    "model_call_allowed": "model_call_not_allowed",
    "memory_write_allowed": "memory_write_not_allowed",
    "memory_retrieval_allowed": "memory_retrieval_not_allowed",
    "context_retrieval_allowed": "context_retrieval_not_allowed",
    "vector_index_allowed": "vector_index_not_allowed",
    "web_query_allowed": "web_query_not_allowed",
    "repo_file_read_allowed": "repo_file_read_not_allowed",
    "external_agent_tracking_allowed": "external_agent_tracking_not_allowed",
    "plugin_execution_allowed": "plugin_execution_not_allowed",
    "playbook_execution_allowed": "playbook_execution_not_allowed",
    "rollback_execution_allowed": "rollback_execution_not_allowed",
}

FORBIDDEN_POLICY_EXTENSION_BEHAVIOR_FIELDS = {
    "memory_write_performed": "memory_write_request_denied",
    "memory_retrieval_performed": "memory_retrieval_request_denied",
    "context_retrieval_performed": "context_retrieval_request_denied",
    "vector_index_touched": "vector_index_request_denied",
    "embedding_generated": "embedding_generation_request_denied",
    "reranking_performed": "reranking_request_denied",
    "model_call_performed": "model_call_request_denied",
    "web_query_performed": "web_query_request_denied",
    "repo_file_read_performed": "repo_file_read_request_denied",
    "external_agent_tracking_performed": "external_agent_tracking_request_denied",
    "plugin_execution_performed": "plugin_execution_request_denied",
    "lease_created": "lease_creation_request_denied",
    "lease_used": "lease_use_request_denied",
    "playbook_execution_performed": "playbook_execution_request_denied",
    "rollback_execution_performed": "rollback_execution_request_denied",
    "api_call_performed": "api_call_request_denied",
    "mcp_call_performed": "mcp_call_request_denied",
    "tool_call_performed": "tool_call_request_denied",
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


@dataclass(frozen=True)
class PolicyExtensionDecision:
    policy_version: str
    subject_kind: str
    action_kind: str
    policy_outcome: str
    blocked_reasons: tuple[str, ...]
    required_gates: tuple[str, ...]
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = POLICY_EXTENSION_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_policy: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    frontend_authority: bool = False
    model_call_allowed: bool = False
    memory_write_allowed: bool = False
    memory_retrieval_allowed: bool = False
    context_retrieval_allowed: bool = False
    vector_index_allowed: bool = False
    web_query_allowed: bool = False
    repo_file_read_allowed: bool = False
    external_agent_tracking_allowed: bool = False
    plugin_execution_allowed: bool = False
    playbook_execution_allowed: bool = False
    rollback_execution_allowed: bool = False
    requires_backend_validation: bool = True


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


def evaluate_policy_extension_request(
    request: Mapping[str, Any],
    *,
    identity_scope_decision: Any | None = None,
    memory_governance_decision: Any | None = None,
    local_model_inventory_decision: Any | None = None,
    model_auto_mode_decision: Any | None = None,
    context_compiler_decision: Any | None = None,
    repo_audit_decision: Any | None = None,
    tool_simulation_decision: Any | None = None,
    mission_control_decision: Any | None = None,
    plugin_review_decision: Any | None = None,
) -> PolicyExtensionDecision:
    """Evaluate future policy subject/action metadata without granting execution.

    The extension is intentionally pure and deny-by-default for unimplemented
    feature families. It does not change the existing runtime guard path.
    """

    data = deepcopy(dict(request))
    subject = _text(data.get("subject_kind")) or "unknown"
    action = _text(data.get("action_kind")) or "unknown"
    blocked: list[str] = []
    gates: list[str] = []

    _validate_policy_extension_claims("request", data, blocked)
    for label, decision in {
        "identity_scope": identity_scope_decision,
        "memory_governance": memory_governance_decision,
        "local_model_inventory": local_model_inventory_decision,
        "model_auto_mode": model_auto_mode_decision,
        "context_compiler": context_compiler_decision,
        "repo_audit": repo_audit_decision,
        "tool_simulation": tool_simulation_decision,
        "mission_control": mission_control_decision,
        "plugin_review": plugin_review_decision,
    }.items():
        _validate_related_policy_extension_decision(label, decision, blocked)

    if subject not in POLICY_SUBJECT_KINDS:
        blocked.append("unknown_subject_kind")
        gates.append("requires_human_review")
    if action not in POLICY_ACTION_KINDS:
        blocked.append("unknown_action_kind")
        gates.append("requires_human_review")
    if subject == "unknown":
        blocked.append("unknown_subject_kind")
        gates.append("requires_human_review")
    if action == "unknown":
        blocked.append("unknown_action_kind")
        gates.append("requires_human_review")

    sensitivity = _text(data.get("sensitivity_class")) or _text(data.get("privacy_class")) or ""
    if sensitivity in SENSITIVE_CLASSES_BLOCKED_BY_DEFAULT:
        blocked.append("sensitive_data_blocked_by_default")
        gates.append("requires_human_review")

    if action == "frontend_authority_claim" or subject == "frontend_request" and _truthy(
        data.get("authority_claimed")
    ):
        blocked.append("frontend_authority_claim_blocked")
        gates.append("requires_backend_validation")
    if action == "mcp_authority_claim" or subject == "mcp_output" and _truthy(data.get("authority_claimed")):
        blocked.append("mcp_authority_claim_blocked")
        gates.append("requires_backend_validation")

    if action in MEMORY_ACTIONS:
        gates.append("requires_memory_governance")
        if memory_governance_decision is None:
            blocked.append("missing_memory_governance")
        elif _is_blocked_related(memory_governance_decision, "governance_status"):
            blocked.append("memory_governance_not_ready")
    if action in MODEL_ACTIONS:
        gates.extend(("requires_provider_policy", "requires_model_auto_mode", "requires_provider_health_check"))
        blocked.append("model_execution_unimplemented")
        if local_model_inventory_decision is not None and model_auto_mode_decision is None:
            blocked.append("local_model_inventory_metadata_is_not_model_permission")
        if _text(data.get("legacy_router_model_hint")) or _text(data.get("planner_model")):
            blocked.append("legacy_router_hint_not_model_permission")
        if action == "cloud_model_call":
            gates.extend(("requires_region_policy", "requires_terms_policy", "requires_secret_policy"))
            blocked.append("cloud_model_policy_missing")
    if action in VECTOR_ACTIONS:
        gates.extend(("requires_memory_governance", "requires_context_policy", "requires_vector_policy"))
        blocked.append("vector_embedding_policy_unimplemented")
    if action in REPO_FILE_READ_ACTIONS:
        gates.extend(("requires_repo_audit_runner_policy", "requires_source_read_plan", "requires_evidence_plan"))
        blocked.append("repo_file_read_unimplemented")
    if action in UNIMPLEMENTED_ACTIONS:
        blocked.append(f"{action}_unimplemented")
        gates.append("requires_future_policy_contract")
    if action == "context_retrieve":
        gates.append("requires_context_policy")
    if action == "web_query":
        gates.append("requires_web_research_gateway_policy")
    if action in {"repo_inventory_run", "repo_file_read"}:
        gates.append("requires_repo_audit_runner_policy")
    if action in {"external_agent_observe", "external_agent_track"}:
        gates.extend(("requires_identity_scope", "requires_external_agent_oversight_policy"))
    if action in {"plugin_load", "plugin_execute"} or subject in {"plugin_operation", "vertical_pack_operation"}:
        gates.append("requires_plugin_policy")
    if action in {"lease_create", "lease_use"}:
        gates.append("requires_capability_lease_policy")
    if action in {"playbook_record", "playbook_replay"}:
        gates.append("requires_playbook_policy")
    if action in {"rollback_snapshot", "rollback_execute"}:
        gates.append("requires_rollback_contract")

    if _requires_identity(action, subject):
        gates.append("requires_identity_scope")
        if identity_scope_decision is None:
            blocked.append("missing_identity_scope")
        elif _is_blocked_related(identity_scope_decision, "scope_status"):
            blocked.append("identity_scope_not_ready")

    outcome = _policy_extension_outcome(action, blocked)
    return PolicyExtensionDecision(
        policy_version=POST_FOUNDATION_POLICY_VERSION,
        subject_kind=subject,
        action_kind=action,
        policy_outcome=outcome,
        blocked_reasons=tuple(dict.fromkeys(blocked)),
        required_gates=tuple(dict.fromkeys(gates)),
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


def _validate_related_policy_extension_decision(
    label: str,
    decision: Any | None,
    blocked: list[str],
) -> None:
    if decision is None:
        return
    before = len(blocked)
    _validate_policy_extension_claims(label, decision, blocked)
    if len(blocked) > before:
        blocked.append("unsafe_related_decision")


def _validate_policy_extension_claims(label: str, source: Any, blocked: list[str]) -> None:
    for field, reason in FORBIDDEN_POLICY_EXTENSION_TRUTHY_FIELDS.items():
        if _field_bool(source, field):
            blocked.append(reason)
    for field, reason in FORBIDDEN_POLICY_EXTENSION_BEHAVIOR_FIELDS.items():
        if _field_bool(source, field):
            blocked.append(reason)
    execution_permission = _field_value(source, "execution_permission")
    if execution_permission not in (None, "", POLICY_EXTENSION_EXECUTION_PERMISSION):
        permission_text = str(execution_permission)
        if not permission_text.startswith("not_granted"):
            blocked.append("execution_permission_claim_denied")
    if label in {"context_compiler", "memory_governance", "local_model_inventory", "repo_audit"}:
        if _field_bool(source, "success") or _field_bool(source, "proof") or _field_bool(source, "certification_claim"):
            blocked.append(f"{label}_cannot_provide_policy_truth")


def _requires_identity(action: str, subject: str) -> bool:
    if action in METADATA_ONLY_ACTIONS:
        return False
    return action in {
        "memory_write",
        "memory_retrieve",
        "memory_delete",
        "memory_export",
        "context_retrieve",
        "context_package",
        "cloud_model_call",
        "repo_file_read",
        "repo_inventory_run",
        "external_agent_observe",
        "external_agent_track",
        "playbook_record",
        "playbook_replay",
        "rollback_snapshot",
        "rollback_execute",
    } or subject in {
        "memory_operation",
        "context_operation",
        "repo_audit_operation",
        "external_agent_operation",
        "playbook_operation",
        "rollback_operation",
    }


def _is_blocked_related(decision: Any, status_field: str) -> bool:
    status = str(_field_value(decision, status_field) or "")
    return status.startswith("blocked") or status in {"clarification_required", "unknown"}


def _policy_extension_outcome(action: str, blocked: list[str]) -> str:
    reasons = set(blocked)
    if "frontend_authority_claim_blocked" in reasons or "frontend_authority_not_allowed" in reasons:
        return "blocked_by_frontend_authority"
    if "mcp_authority_claim_blocked" in reasons or "mcp_authority_not_allowed" in reasons:
        return "blocked_by_mcp_authority"
    if "sensitive_data_blocked_by_default" in reasons:
        return "blocked_by_sensitive_data"
    if "missing_identity_scope" in reasons or "identity_scope_not_ready" in reasons:
        return "blocked_by_unknown_scope"
    if "missing_memory_governance" in reasons or "memory_governance_not_ready" in reasons:
        return "blocked_by_missing_governance"
    if any(reason.endswith("_unimplemented") or "unimplemented" in reason for reason in reasons):
        return "blocked_by_unimplemented_feature"
    if any(reason.startswith("unknown_") for reason in reasons):
        return "unsupported"
    if reasons:
        return "blocked_by_policy"
    if action in METADATA_ONLY_ACTIONS:
        return "allowed_metadata_only"
    if action in PROPOSAL_ONLY_ACTIONS or action in MEMORY_ACTIONS:
        return "allowed_proposal_only"
    return "blocked_by_unimplemented_feature"


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _field_bool(source: Any, field: str) -> bool:
    return _truthy(_field_value(source, field))


def _field_value(source: Any, field: str) -> Any:
    if isinstance(source, Mapping):
        return source.get(field)
    return getattr(source, field, None)


def _truthy(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on", "allowed", "grant"}
    return bool(value)
