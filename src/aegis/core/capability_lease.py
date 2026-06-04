from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping


CAPABILITY_LEASE_VERSION = "capability-lease-design/1"
CAPABILITY_LEASE_EXECUTION_PERMISSION = "not_granted_by_capability_lease"

LEASE_SUBJECTS = {
    "local_provider_health_probe_future",
    "repo_audit_read_future",
    "repo_inventory_run_future",
    "context_retrieval_future",
    "memory_operation_future",
    "model_call_future",
    "embedding_generation_future",
    "reranking_future",
    "web_research_query_future",
    "document_parse_future",
    "external_agent_observation_future",
    "plugin_operation_future",
    "vertical_pack_operation_future",
    "playbook_record_future",
    "playbook_replay_future",
    "rollback_snapshot_future",
    "low_risk_file_write_future",
    "tool_action_future",
    "unknown",
}

RISK_TIERS = {
    "metadata_only",
    "read_only",
    "low_risk_local",
    "medium_risk_local",
    "high_risk",
    "destructive",
    "external_network",
    "cloud_data_transfer",
    "sensitive_data",
    "unknown",
}

LEASE_SCOPES = {
    "session_scoped",
    "project_scoped",
    "repository_scoped",
    "path_scoped",
    "tool_scoped",
    "provider_scoped",
    "model_scoped",
    "context_scoped",
    "memory_scoped",
    "web_domain_scoped_future",
    "external_agent_scoped_future",
    "disabled",
    "unknown",
}

LIFECYCLE_STATES = {
    "proposed",
    "requires_policy",
    "requires_identity_scope",
    "requires_context_policy",
    "requires_memory_governance",
    "requires_provider_health",
    "requires_human_approval",
    "ready_for_operator_review",
    "active_future_only",
    "denied",
    "expired",
    "revoked",
    "superseded",
    "blocked",
    "unknown",
}

IDENTITY_SCOPES = {"session_scoped", "project_scoped", "repository_scoped", "path_scoped"}
PATH_SCOPES = {"path_scoped"}
PROVIDER_SUBJECTS = {"local_provider_health_probe_future"}
MODEL_SUBJECTS = {"model_call_future", "embedding_generation_future", "reranking_future"}
CONTEXT_SUBJECTS = {"context_retrieval_future"}
MEMORY_SUBJECTS = {"memory_operation_future"}
REPO_SUBJECTS = {"repo_audit_read_future", "repo_inventory_run_future"}
WEB_SUBJECTS = {"web_research_query_future"}
PLUGIN_SUBJECTS = {"plugin_operation_future", "vertical_pack_operation_future"}
PLAYBOOK_SUBJECTS = {"playbook_replay_future", "playbook_record_future"}
ROLLBACK_SUBJECTS = {"rollback_snapshot_future"}
EXTERNAL_AGENT_SUBJECTS = {"external_agent_observation_future"}

BLOCKED_RISK_TIERS = {"destructive", "unknown"}
FUTURE_POLICY_RISK_TIERS = {"external_network", "cloud_data_transfer"}
BROAD_VALUES = {"*", "all", "any", "global", "everything", "unbounded"}
SECRET_MARKERS = ("secret", "credential", "token", "api_key", "apikey", ".env")
SURVEILLANCE_MARKERS = ("surveillance", "productivity_score", "productivity-scoring", "employee_monitoring")
MAX_DURATION_SECONDS = 24 * 60 * 60
MAX_ACTIONS = 100

FORBIDDEN_TRUTHY_FIELDS = {
    "authority": "authority_must_be_false",
    "runtime_dispatch_allowed": "runtime_dispatch_not_allowed",
    "approval_grant": "approval_grant_not_allowed",
    "capability_grant": "capability_grant_not_allowed",
    "lease_grant": "lease_grant_not_allowed",
    "lease_active": "lease_active_claim_denied",
    "lease_created": "lease_creation_claim_denied",
    "lease_used": "lease_use_claim_denied",
    "evidence_provided_by_lease": "lease_cannot_provide_evidence",
    "evidence_created": "lease_cannot_provide_evidence",
    "verifier_success": "lease_cannot_mark_verifier_success",
    "verified_success": "lease_cannot_mark_verifier_success",
    "success": "success_claim_denied",
    "proof": "proof_claim_denied",
    "certification_claim": "certification_claim_denied",
    "frontend_authority": "frontend_authority_not_allowed",
    "mcp_authority": "mcp_authority_not_allowed",
    "tool_output_is_authority": "tool_output_authority_claim_denied",
    "model_output_is_authority": "model_output_authority_claim_denied",
    "model_output_is_truth": "model_output_truth_claim_denied",
}

FORBIDDEN_ALLOWED_FIELDS = {
    "model_call_allowed": "model_call_permission_denied",
    "provider_probe_allowed": "provider_probe_permission_denied",
    "repo_file_read_allowed": "repo_file_read_permission_denied",
    "memory_write_allowed": "memory_write_permission_denied",
    "memory_retrieval_allowed": "memory_retrieval_permission_denied",
    "context_retrieval_allowed": "context_retrieval_permission_denied",
    "web_query_allowed": "web_query_permission_denied",
    "plugin_execution_allowed": "plugin_execution_permission_denied",
    "playbook_execution_allowed": "playbook_execution_permission_denied",
    "rollback_execution_allowed": "rollback_execution_permission_denied",
    "external_agent_tracking_allowed": "external_agent_tracking_permission_denied",
    "data_sent_external": "external_data_transfer_denied",
}

FORBIDDEN_BEHAVIOR_FIELDS = {
    "model_call_performed": "model_call_request_denied",
    "provider_probe_performed": "provider_probe_request_denied",
    "repo_file_read_performed": "repo_file_read_request_denied",
    "memory_write_performed": "memory_write_request_denied",
    "memory_retrieval_performed": "memory_retrieval_request_denied",
    "context_retrieval_performed": "context_retrieval_request_denied",
    "web_query_performed": "web_query_request_denied",
    "plugin_execution_performed": "plugin_execution_request_denied",
    "playbook_execution_performed": "playbook_execution_request_denied",
    "rollback_execution_performed": "rollback_execution_request_denied",
    "api_call_performed": "api_call_request_denied",
    "mcp_call_performed": "mcp_call_request_denied",
    "tool_call_performed": "tool_call_request_denied",
}


@dataclass(frozen=True)
class CapabilityLeaseFailure:
    reason: str
    field: str
    message: str


@dataclass(frozen=True)
class CapabilityLeaseInput:
    request_id: str | None
    lease_id: str | None
    lease_subject: str | None
    lease_scope: str | None
    risk_tier: str | None
    namespace: str | None
    project_ref: str | None
    repository_ref: str | None
    session_ref: str | None
    path_prefixes: tuple[str, ...]
    allowed_tools: tuple[str, ...]
    allowed_provider_classes: tuple[str, ...]
    allowed_model_roles: tuple[str, ...]
    allowed_context_categories: tuple[str, ...]
    allowed_memory_categories: tuple[str, ...]
    allowed_domains_future: tuple[str, ...]
    max_actions: int | None
    max_duration_seconds: int | None
    expires_at_metadata: str | None
    requires_evidence_plan: bool
    requires_verifier_plan: bool
    requires_negative_evidence_on_failure: bool
    requires_redaction: bool
    requires_secret_safe_logging: bool
    requires_operator_review: bool
    revocable: bool
    source_refs: tuple[Mapping[str, Any], ...]
    provenance: tuple[Mapping[str, Any], ...]
    limitations: tuple[str, ...]
    unknowns: tuple[str, ...]


@dataclass(frozen=True)
class CapabilityLeaseDecision:
    contract_version: str
    lifecycle_state: str
    request_id: str | None
    lease_id: str | None
    lease_subject: str | None
    lease_scope: str | None
    risk_tier: str | None
    namespace: str | None
    required_future_gates: tuple[str, ...]
    blockers: tuple[str, ...]
    failure_reasons: tuple[str, ...]
    failures: tuple[CapabilityLeaseFailure, ...]
    lease_input: CapabilityLeaseInput | None
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = CAPABILITY_LEASE_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    lease_active: bool = False
    lease_created: bool = False
    lease_used: bool = False
    evidence_provided_by_lease: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    frontend_authority: bool = False
    model_call_allowed: bool = False
    provider_probe_allowed: bool = False
    repo_file_read_allowed: bool = False
    memory_write_allowed: bool = False
    memory_retrieval_allowed: bool = False
    context_retrieval_allowed: bool = False
    web_query_allowed: bool = False
    plugin_execution_allowed: bool = False
    playbook_execution_allowed: bool = False
    rollback_execution_allowed: bool = False
    external_agent_tracking_allowed: bool = False
    data_sent_external: bool = False
    requires_backend_validation: bool = True
    requires_policy_check: bool = True
    requires_human_review_for_unknowns: bool = True


def validate_capability_lease_request(
    request: Mapping[str, Any] | None,
    *,
    identity_scope_decision: Any | None = None,
    memory_governance_decision: Any | None = None,
    context_policy_decision: Any | None = None,
    policy_extension_decision: Any | None = None,
    model_auto_mode_decision: Any | None = None,
    local_provider_health_decision: Any | None = None,
    local_model_inventory_decision: Any | None = None,
    mission_control_decision: Any | None = None,
    tool_simulation_decision: Any | None = None,
    repo_audit_decision: Any | None = None,
    compliance_evidence_decision: Any | None = None,
    developer_work_passport_decision: Any | None = None,
    plugin_review_decision: Any | None = None,
) -> CapabilityLeaseDecision:
    """Validate a future capability lease candidate without issuing or using it."""

    if not isinstance(request, Mapping):
        failure = CapabilityLeaseFailure(
            reason="missing_request",
            field="request",
            message="capability lease request must be caller-supplied metadata",
        )
        return _decision(
            lifecycle_state="unknown",
            request_id=None,
            lease_id=None,
            lease_subject=None,
            lease_scope=None,
            risk_tier=None,
            namespace=None,
            required_future_gates=(),
            failures=(failure,),
            lease_input=None,
        )

    data = deepcopy(dict(request))
    failures: list[CapabilityLeaseFailure] = []
    _validate_forbidden_claims("request", data, failures)
    for label, decision in {
        "identity_scope": identity_scope_decision,
        "memory_governance": memory_governance_decision,
        "context_policy": context_policy_decision,
        "policy_extension": policy_extension_decision,
        "model_auto_mode": model_auto_mode_decision,
        "local_provider_health": local_provider_health_decision,
        "local_model_inventory": local_model_inventory_decision,
        "mission_control": mission_control_decision,
        "tool_simulation": tool_simulation_decision,
        "repo_audit": repo_audit_decision,
        "compliance_evidence": compliance_evidence_decision,
        "developer_work_passport": developer_work_passport_decision,
        "plugin_review": plugin_review_decision,
    }.items():
        _validate_related_decision(label, decision, failures)

    lease_input = CapabilityLeaseInput(
        request_id=_text(data.get("request_id")),
        lease_id=_text(data.get("lease_id")),
        lease_subject=_text(data.get("lease_subject")),
        lease_scope=_text(data.get("lease_scope")),
        risk_tier=_text(data.get("risk_tier")),
        namespace=_text(data.get("namespace")),
        project_ref=_text(data.get("project_ref")),
        repository_ref=_text(data.get("repository_ref")),
        session_ref=_text(data.get("session_ref")),
        path_prefixes=_text_tuple(data.get("path_prefixes")),
        allowed_tools=_text_tuple(data.get("allowed_tools")),
        allowed_provider_classes=_text_tuple(data.get("allowed_provider_classes")),
        allowed_model_roles=_text_tuple(data.get("allowed_model_roles")),
        allowed_context_categories=_text_tuple(data.get("allowed_context_categories")),
        allowed_memory_categories=_text_tuple(data.get("allowed_memory_categories")),
        allowed_domains_future=_text_tuple(data.get("allowed_domains_future")),
        max_actions=_int(data.get("max_actions")),
        max_duration_seconds=_int(data.get("max_duration_seconds")),
        expires_at_metadata=_text(data.get("expires_at_metadata")),
        requires_evidence_plan=_truthy(data.get("requires_evidence_plan")),
        requires_verifier_plan=_truthy(data.get("requires_verifier_plan")),
        requires_negative_evidence_on_failure=_truthy(data.get("requires_negative_evidence_on_failure")),
        requires_redaction=_truthy(data.get("requires_redaction")),
        requires_secret_safe_logging=_truthy(data.get("requires_secret_safe_logging")),
        requires_operator_review=_truthy(data.get("requires_operator_review")),
        revocable=_truthy(data.get("revocable")),
        source_refs=_mapping_tuple(data.get("source_refs")),
        provenance=_mapping_tuple(data.get("provenance")),
        limitations=_text_tuple(data.get("limitations")),
        unknowns=_text_tuple(data.get("unknowns")),
    )

    _validate_required_fields(lease_input, failures)
    _validate_scope_and_risk(lease_input, failures)
    _validate_scope_constraints(lease_input, failures)
    _validate_related_requirements(
        lease_input,
        identity_scope_decision=identity_scope_decision,
        memory_governance_decision=memory_governance_decision,
        context_policy_decision=context_policy_decision,
        policy_extension_decision=policy_extension_decision,
        model_auto_mode_decision=model_auto_mode_decision,
        local_provider_health_decision=local_provider_health_decision,
        repo_audit_decision=repo_audit_decision,
        failures=failures,
    )

    gates = _future_gates(lease_input, failures)
    return _decision(
        lifecycle_state=_lifecycle_state(lease_input, failures, gates),
        request_id=lease_input.request_id,
        lease_id=lease_input.lease_id,
        lease_subject=lease_input.lease_subject,
        lease_scope=lease_input.lease_scope,
        risk_tier=lease_input.risk_tier,
        namespace=lease_input.namespace,
        required_future_gates=gates,
        failures=tuple(failures),
        lease_input=lease_input,
    )


def _decision(
    *,
    lifecycle_state: str,
    request_id: str | None,
    lease_id: str | None,
    lease_subject: str | None,
    lease_scope: str | None,
    risk_tier: str | None,
    namespace: str | None,
    required_future_gates: tuple[str, ...],
    failures: tuple[CapabilityLeaseFailure, ...],
    lease_input: CapabilityLeaseInput | None,
) -> CapabilityLeaseDecision:
    return CapabilityLeaseDecision(
        contract_version=CAPABILITY_LEASE_VERSION,
        lifecycle_state=lifecycle_state,
        request_id=request_id,
        lease_id=lease_id,
        lease_subject=lease_subject,
        lease_scope=lease_scope,
        risk_tier=risk_tier,
        namespace=namespace,
        required_future_gates=required_future_gates,
        blockers=tuple(dict.fromkeys(f.reason for f in failures)),
        failure_reasons=tuple(dict.fromkeys(f.reason for f in failures)),
        failures=failures,
        lease_input=lease_input,
    )


def _validate_required_fields(
    lease_input: CapabilityLeaseInput,
    failures: list[CapabilityLeaseFailure],
) -> None:
    required = {
        "request_id": lease_input.request_id,
        "lease_subject": lease_input.lease_subject,
        "lease_scope": lease_input.lease_scope,
        "risk_tier": lease_input.risk_tier,
        "namespace": lease_input.namespace,
        "max_duration_seconds": lease_input.max_duration_seconds,
        "max_actions": lease_input.max_actions,
    }
    for field, value in required.items():
        if value is None or value == "":
            _add_failure(failures, f"missing_{field}", field, f"{field} is required")
    if not lease_input.revocable:
        _add_failure(failures, "lease_must_be_revocable", "revocable", "lease candidates must be revocable")
    if not (lease_input.source_refs or lease_input.provenance):
        _add_failure(failures, "missing_source_refs_or_provenance", "source_refs", "lease candidates require audit/source refs or provenance")
    if lease_input.lease_subject and lease_input.lease_subject not in LEASE_SUBJECTS:
        _add_failure(failures, "unsupported_lease_subject", "lease_subject", "lease subject is not recognized")
    if lease_input.lease_scope and lease_input.lease_scope not in LEASE_SCOPES:
        _add_failure(failures, "unsupported_lease_scope", "lease_scope", "lease scope is not recognized")
    if lease_input.risk_tier and lease_input.risk_tier not in RISK_TIERS:
        _add_failure(failures, "unsupported_risk_tier", "risk_tier", "risk tier is not recognized")


def _validate_scope_and_risk(
    lease_input: CapabilityLeaseInput,
    failures: list[CapabilityLeaseFailure],
) -> None:
    if lease_input.lease_scope in {None, "unknown", "disabled"}:
        _add_failure(failures, "unknown_or_disabled_scope_blocked", "lease_scope", "unknown or disabled lease scope is blocked")
    if lease_input.lease_subject == "unknown":
        _add_failure(failures, "unknown_subject_blocked", "lease_subject", "unknown lease subject is blocked")
    if lease_input.risk_tier in BLOCKED_RISK_TIERS:
        _add_failure(failures, f"{lease_input.risk_tier}_risk_blocked", "risk_tier", "unknown or destructive risk is blocked")
    if lease_input.risk_tier in FUTURE_POLICY_RISK_TIERS:
        _add_failure(failures, f"{lease_input.risk_tier}_requires_future_policy", "risk_tier", "external/cloud transfer risk requires future policy")
    if lease_input.risk_tier == "high_risk":
        _add_failure(failures, "high_risk_lease_activation_blocked", "risk_tier", "high risk lease activation is blocked in this contract")
    if lease_input.risk_tier == "sensitive_data" and not lease_input.requires_operator_review:
        _add_failure(failures, "sensitive_data_requires_human_review", "risk_tier", "sensitive data lease candidates require operator review")
    if lease_input.max_duration_seconds is not None:
        if lease_input.max_duration_seconds <= 0:
            _add_failure(failures, "invalid_max_duration", "max_duration_seconds", "max duration must be positive")
        elif lease_input.max_duration_seconds > MAX_DURATION_SECONDS:
            _add_failure(failures, "excessive_duration_blocked", "max_duration_seconds", "max duration is too broad")
    if lease_input.max_actions is not None:
        if lease_input.max_actions <= 0:
            _add_failure(failures, "invalid_max_actions", "max_actions", "max actions must be positive")
        elif lease_input.max_actions > MAX_ACTIONS:
            _add_failure(failures, "excessive_action_count_blocked", "max_actions", "max action count is too broad")


def _validate_scope_constraints(
    lease_input: CapabilityLeaseInput,
    failures: list[CapabilityLeaseFailure],
) -> None:
    if lease_input.lease_scope == "session_scoped" and not lease_input.session_ref:
        _add_failure(failures, "missing_session_ref", "session_ref", "session-scoped leases require session_ref")
    if lease_input.lease_scope in {"project_scoped", "repository_scoped", "path_scoped"} and not lease_input.project_ref:
        _add_failure(failures, "missing_project_ref", "project_ref", "project/repository/path scopes require project_ref")
    if lease_input.lease_scope in {"repository_scoped", "path_scoped"} and not lease_input.repository_ref:
        _add_failure(failures, "missing_repository_ref", "repository_ref", "repository/path scopes require repository_ref")
    if lease_input.lease_scope == "path_scoped" and not lease_input.path_prefixes:
        _add_failure(failures, "missing_path_prefixes", "path_prefixes", "path-scoped leases require bounded path prefixes")

    for field, values in {
        "allowed_tools": lease_input.allowed_tools,
        "allowed_provider_classes": lease_input.allowed_provider_classes,
        "allowed_model_roles": lease_input.allowed_model_roles,
        "allowed_context_categories": lease_input.allowed_context_categories,
        "allowed_memory_categories": lease_input.allowed_memory_categories,
        "allowed_domains_future": lease_input.allowed_domains_future,
    }.items():
        if _contains_broad_value(values):
            _add_failure(failures, f"wildcard_{field}_blocked", field, "wildcard/all values are blocked")
        if any(_contains_secret_marker(value) for value in values):
            _add_failure(failures, "secret_or_credential_scope_blocked", field, "secret and credential scope is blocked")
        if any(_contains_surveillance_marker(value) for value in values):
            _add_failure(failures, "surveillance_or_productivity_scoring_blocked", field, "surveillance/productivity scoring is blocked")

    for path in lease_input.path_prefixes:
        _validate_path_prefix(path, failures)

    if lease_input.lease_subject in PROVIDER_SUBJECTS and not lease_input.allowed_provider_classes:
        _add_failure(failures, "missing_provider_scope", "allowed_provider_classes", "provider lease candidates require provider scope")
    if lease_input.lease_subject in MODEL_SUBJECTS and not lease_input.allowed_model_roles:
        _add_failure(failures, "missing_model_scope", "allowed_model_roles", "model lease candidates require model role scope")
    if lease_input.lease_subject in CONTEXT_SUBJECTS and not lease_input.allowed_context_categories:
        _add_failure(failures, "missing_context_scope", "allowed_context_categories", "context lease candidates require context category scope")
    if lease_input.lease_subject in MEMORY_SUBJECTS and not lease_input.allowed_memory_categories:
        _add_failure(failures, "missing_memory_scope", "allowed_memory_categories", "memory lease candidates require memory category scope")
    if lease_input.lease_scope == "tool_scoped" and not lease_input.allowed_tools:
        _add_failure(failures, "missing_tool_scope", "allowed_tools", "tool-scoped leases require allowed tools")


def _validate_path_prefix(path: str, failures: list[CapabilityLeaseFailure]) -> None:
    normalized = path.strip().replace("\\", "/")
    lowered = normalized.lower()
    if not normalized:
        _add_failure(failures, "empty_path_prefix_blocked", "path_prefixes", "empty path prefix is blocked")
    if normalized in {".", "/", "~"} or lowered in {"c:", "c:/", "root", "home", "users"}:
        _add_failure(failures, "broad_filesystem_scope_blocked", "path_prefixes", "broad filesystem scope is blocked")
    if normalized.startswith("/") or normalized.startswith("//") or normalized.startswith("~") or ":/" in normalized:
        _add_failure(failures, "absolute_or_external_path_blocked", "path_prefixes", "absolute/external paths are blocked")
    if ".." in normalized.split("/"):
        _add_failure(failures, "path_traversal_blocked", "path_prefixes", "path traversal is blocked")
    if _contains_broad_value((normalized,)):
        _add_failure(failures, "broad_wildcard_path_blocked", "path_prefixes", "broad wildcard path is blocked")
    if _contains_secret_marker(normalized):
        _add_failure(failures, "secret_or_credential_scope_blocked", "path_prefixes", "secret and credential paths are blocked")


def _validate_related_requirements(
    lease_input: CapabilityLeaseInput,
    *,
    identity_scope_decision: Any | None,
    memory_governance_decision: Any | None,
    context_policy_decision: Any | None,
    policy_extension_decision: Any | None,
    model_auto_mode_decision: Any | None,
    local_provider_health_decision: Any | None,
    repo_audit_decision: Any | None,
    failures: list[CapabilityLeaseFailure],
) -> None:
    if lease_input.lease_scope in IDENTITY_SCOPES:
        _require_related("identity_scope", identity_scope_decision, "scope_status", failures)
    if lease_input.lease_subject in MEMORY_SUBJECTS:
        _require_related("memory_governance", memory_governance_decision, "governance_status", failures)
    if lease_input.lease_subject in CONTEXT_SUBJECTS:
        _require_related("context_policy", context_policy_decision, "policy_status", failures)
    if lease_input.lease_subject in PROVIDER_SUBJECTS:
        _require_related("local_provider_health", local_provider_health_decision, "readiness_status", failures)
    if lease_input.lease_subject in MODEL_SUBJECTS:
        _require_related("model_auto_mode", model_auto_mode_decision, "selection_mode", failures)
        _require_related("local_provider_health", local_provider_health_decision, "readiness_status", failures)
    if lease_input.lease_subject in REPO_SUBJECTS:
        _require_related("repo_audit", repo_audit_decision, "readiness_status", failures)
    if policy_extension_decision is None:
        _add_failure(failures, "missing_policy_extension", "policy_extension_decision", "capability leases require policy-as-code metadata")
    else:
        outcome = str(_field_value(policy_extension_decision, "policy_outcome") or "")
        if outcome.startswith("blocked") or outcome in {"unsupported", "unknown"}:
            _add_failure(failures, "policy_extension_not_ready", "policy_extension_decision.policy_outcome", "blocked policy extension cannot be contradicted")


def _require_related(
    label: str,
    decision: Any | None,
    status_field: str,
    failures: list[CapabilityLeaseFailure],
) -> None:
    if decision is None:
        _add_failure(failures, f"missing_{label}", f"{label}_decision", f"{label} decision is required")
        return
    status = str(_field_value(decision, status_field) or "")
    if status.startswith("blocked") or status in {"unsupported", "unknown", "clarification_required"}:
        _add_failure(failures, f"{label}_not_ready", f"{label}_decision.{status_field}", f"{label} decision is not ready")


def _validate_related_decision(
    label: str,
    decision: Any | None,
    failures: list[CapabilityLeaseFailure],
) -> None:
    if decision is None:
        return
    before = len(failures)
    _validate_forbidden_claims(label, decision, failures)
    if len(failures) > before:
        _add_failure(
            failures,
            "unsafe_related_decision",
            label,
            f"{label} cannot grant lease authority, dispatch, approval, evidence, verifier success, or feature execution",
        )


def _validate_forbidden_claims(
    label: str,
    source: Any,
    failures: list[CapabilityLeaseFailure],
) -> None:
    for field, reason in FORBIDDEN_TRUTHY_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(failures, reason, f"{label}.{field}", "authority, grant, active lease, evidence, verifier, proof, or frontend/MCP/model authority claims are denied")
    for field, reason in FORBIDDEN_ALLOWED_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(failures, reason, f"{label}.{field}", "lease candidates cannot allow feature execution")
    for field, reason in FORBIDDEN_BEHAVIOR_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(failures, reason, f"{label}.{field}", "lease candidates cannot perform runtime, model, repo, memory, context, web, plugin, playbook, rollback, API, MCP, or tool behavior")
    execution_permission = _field_value(source, "execution_permission")
    if execution_permission not in (None, "", CAPABILITY_LEASE_EXECUTION_PERMISSION):
        permission_text = str(execution_permission)
        if not permission_text.startswith("not_granted"):
            _add_failure(failures, "execution_permission_claim_denied", f"{label}.execution_permission", "capability lease candidates cannot grant execution permission")


def _future_gates(
    lease_input: CapabilityLeaseInput,
    failures: list[CapabilityLeaseFailure],
) -> tuple[str, ...]:
    gates: list[str] = []
    subject = lease_input.lease_subject
    if subject in PROVIDER_SUBJECTS:
        gates.append("requires_future_provider_probe_boundary")
    if subject in MODEL_SUBJECTS:
        gates.append("requires_future_model_call_boundary")
    if subject in CONTEXT_SUBJECTS:
        gates.append("requires_future_context_retrieval_boundary")
    if subject in MEMORY_SUBJECTS:
        gates.append("requires_future_memory_operation_boundary")
    if subject in REPO_SUBJECTS:
        gates.append("requires_future_repo_runner_boundary")
    if subject in WEB_SUBJECTS:
        gates.append("requires_future_web_research_gateway")
    if subject in EXTERNAL_AGENT_SUBJECTS:
        gates.append("requires_future_external_agent_oversight_boundary")
    if subject in PLUGIN_SUBJECTS:
        gates.append("requires_future_plugin_or_vertical_pack_boundary")
    if subject in PLAYBOOK_SUBJECTS:
        gates.append("requires_future_playbook_boundary")
    if subject in ROLLBACK_SUBJECTS:
        gates.append("requires_future_rollback_boundary")
    if lease_input.risk_tier in FUTURE_POLICY_RISK_TIERS:
        gates.append("requires_future_external_or_cloud_policy")
    if any("unknown" in failure.reason for failure in failures):
        gates.append("unknown_metadata_requires_human_review")
    return tuple(dict.fromkeys(gates))


def _lifecycle_state(
    lease_input: CapabilityLeaseInput,
    failures: list[CapabilityLeaseFailure],
    gates: tuple[str, ...],
) -> str:
    reasons = {failure.reason for failure in failures}
    if reasons:
        if "unsafe_related_decision" in reasons:
            return "blocked"
        if "missing_policy_extension" in reasons:
            return "requires_policy"
        if any(reason in {"missing_identity_scope", "identity_scope_not_ready"} for reason in reasons):
            return "requires_identity_scope"
        if any(reason in {"missing_memory_governance", "memory_governance_not_ready"} for reason in reasons):
            return "requires_memory_governance"
        if any(reason in {"missing_context_policy", "context_policy_not_ready"} for reason in reasons):
            return "requires_context_policy"
        if any(reason in {"missing_local_provider_health", "local_provider_health_not_ready"} for reason in reasons):
            return "requires_provider_health"
        if "sensitive_data_requires_human_review" in reasons:
            return "requires_human_approval"
        return "blocked"
    if lease_input.requires_operator_review or lease_input.risk_tier in {"sensitive_data", "medium_risk_local", "low_risk_local", "read_only"}:
        return "ready_for_operator_review"
    if gates:
        return "ready_for_operator_review"
    return "proposed"


def _contains_broad_value(values: tuple[str, ...]) -> bool:
    return any(value.strip().lower() in BROAD_VALUES or value.strip() == "*" for value in values)


def _contains_secret_marker(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in SECRET_MARKERS)


def _contains_surveillance_marker(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in SURVEILLANCE_MARKERS)


def _mapping_tuple(value: Any) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(deepcopy(item) for item in value if isinstance(item, Mapping))


def _text_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item).strip() for item in value if str(item).strip())
    return (str(value).strip(),) if str(value).strip() else ()


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _field_bool(source: Any, field: str) -> bool:
    return _truthy(_field_value(source, field))


def _field_value(source: Any, field: str) -> Any:
    if isinstance(source, Mapping):
        return source.get(field)
    return getattr(source, field, None)


def _truthy(value: Any, *, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on", "allowed", "grant"}
    return bool(value)


def _add_failure(
    failures: list[CapabilityLeaseFailure],
    reason: str,
    field: str,
    message: str,
) -> None:
    failures.append(CapabilityLeaseFailure(reason=reason, field=field, message=message))
