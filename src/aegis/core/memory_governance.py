from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping


MEMORY_GOVERNANCE_CONTRACT_VERSION = "memory-governance-memory-os-contract/1"
MEMORY_GOVERNANCE_EXECUTION_PERMISSION = "not_granted_by_memory_governance"

MEMORY_CATEGORIES = {
    "user_preference",
    "project_preference",
    "repo_memory",
    "task_session_memory",
    "operator_decision_history",
    "approval_denial_history",
    "policy_decision_summary",
    "model_provider_preference",
    "ui_ux_preference",
    "vertical_pack_memory",
    "plugin_review_memory",
    "entity_memory",
    "organization_team_memory_future",
    "tool_provider_reliability",
    "failure_negative_evidence_summary",
    "source_citation_memory",
    "web_research_memory",
    "document_memory",
    "conversation_summary",
    "personal_private_memory",
    "temporary_scratch",
    "quarantine_memory",
    "stale_deprecated_memory",
    "unknown",
}

MEMORY_STATUSES = {
    "proposed",
    "active",
    "tentative",
    "inferred",
    "user_confirmed",
    "stale",
    "superseded",
    "quarantined",
    "deleted",
    "expired",
    "conflict",
    "sensitive_requires_review",
    "private_local_only",
    "rejected",
    "unknown",
}

MEMORY_SCOPES = {
    "session_only",
    "project_scoped",
    "repository_scoped",
    "user_profile_scoped",
    "workspace_scoped",
    "tenant_scoped_future",
    "machine_local_only",
    "disabled",
    "unknown",
}

MEMORY_OPERATIONS = {
    "propose_write",
    "propose_retrieve",
    "propose_update",
    "propose_delete",
    "propose_forget",
    "propose_export",
    "propose_quarantine",
    "propose_supersede",
    "propose_expire",
    "propose_rebuild_index_future",
    "unknown",
}

RETENTION_POLICIES = {
    "no_persistence",
    "session_ttl",
    "project_ttl",
    "user_confirmed_until_deleted",
    "explicit_expiry",
    "quarantined_until_review",
    "disabled",
    "unknown",
}

SENSITIVITY_CLASSES = {
    "public",
    "internal",
    "private",
    "sensitive",
    "secret_like",
    "credential_like",
    "health_or_personal_sensitive",
    "unknown",
}

DURABLE_SCOPES = {
    "project_scoped",
    "repository_scoped",
    "user_profile_scoped",
    "workspace_scoped",
    "tenant_scoped_future",
    "machine_local_only",
}

PERSISTENCE_OPERATIONS = {
    "propose_write",
    "propose_update",
    "propose_export",
    "propose_rebuild_index_future",
}

NON_CURRENT_STATUSES = {
    "stale",
    "superseded",
    "quarantined",
    "deleted",
    "expired",
    "conflict",
    "rejected",
    "unknown",
}

LOW_TRUST_SOURCE_FIELDS = {
    "inferred_by_model",
    "generated_by_model",
    "source_is_model_output",
    "source_is_web",
    "source_is_mcp",
    "source_is_tool",
    "source_is_frontend",
}

FORBIDDEN_TRUTHY_FIELDS = {
    "authority": "authority_must_be_false",
    "runtime_dispatch_allowed": "runtime_dispatch_not_allowed",
    "approval_grant": "approval_grant_not_allowed",
    "capability_grant": "capability_grant_not_allowed",
    "lease_grant": "lease_grant_not_allowed",
    "frontend_authority": "frontend_authority_not_allowed",
    "evidence_provided_by_memory_governance": "memory_governance_cannot_provide_evidence",
    "evidence_created": "memory_governance_cannot_provide_evidence",
    "verifier_success": "memory_governance_cannot_mark_verifier_success",
    "verified_success": "memory_governance_cannot_mark_verifier_success",
    "success": "success_claim_denied",
    "memory_write_allowed": "memory_write_not_allowed",
    "memory_retrieval_allowed": "memory_retrieval_not_allowed",
    "memory_delete_allowed": "memory_delete_not_allowed",
    "memory_export_allowed": "memory_export_not_allowed",
    "surveillance_allowed": "surveillance_not_allowed",
    "productivity_scoring_allowed": "productivity_scoring_not_allowed",
}

FORBIDDEN_BEHAVIOR_FIELDS = {
    "memory_write_performed": "memory_write_request_denied",
    "memory_write_requested": "memory_write_request_denied",
    "memory_retrieval_performed": "memory_retrieval_request_denied",
    "memory_retrieval_requested": "memory_retrieval_request_denied",
    "memory_delete_performed": "memory_delete_request_denied",
    "memory_delete_requested": "memory_delete_request_denied",
    "memory_export_performed": "memory_export_request_denied",
    "memory_export_requested": "memory_export_request_denied",
    "vector_index_touched": "vector_index_request_denied",
    "vector_index_requested": "vector_index_request_denied",
    "embedding_generated": "embedding_generation_request_denied",
    "embedding_requested": "embedding_generation_request_denied",
    "reranking_performed": "reranking_request_denied",
    "reranking_requested": "reranking_request_denied",
    "model_call_performed": "model_call_request_denied",
    "model_call_requested": "model_call_request_denied",
    "cloud_sync_performed": "cloud_sync_request_denied",
    "cloud_sync_requested": "cloud_sync_request_denied",
    "data_sent_external": "external_data_transfer_denied",
    "api_call_performed": "api_call_request_denied",
    "api_call_requested": "api_call_request_denied",
    "mcp_call_performed": "mcp_call_request_denied",
    "mcp_call_requested": "mcp_call_request_denied",
    "tool_call_performed": "tool_call_request_denied",
    "tool_call_requested": "tool_call_request_denied",
}

RELATED_DECISION_LABELS = {
    "identity_scope_decision": "identity_scope",
    "local_model_inventory_decision": "local_model_inventory",
    "model_auto_mode_decision": "model_auto_mode",
    "context_compiler_decision": "context_compiler",
    "repo_audit_decision": "repo_audit",
    "developer_work_passport_decision": "developer_work_passport",
    "compliance_evidence_decision": "compliance_evidence",
    "mission_control_decision": "mission_control",
    "tool_simulation_decision": "tool_simulation",
    "plugin_review_decision": "plugin_review",
}


@dataclass(frozen=True)
class MemoryGovernanceFailure:
    reason: str
    field: str
    message: str


@dataclass(frozen=True)
class MemoryGovernanceContract:
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = MEMORY_GOVERNANCE_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_memory_governance: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    frontend_authority: bool = False
    memory_write_performed: bool = False
    memory_retrieval_performed: bool = False
    memory_delete_performed: bool = False
    memory_export_performed: bool = False
    vector_index_touched: bool = False
    embedding_generated: bool = False
    reranking_performed: bool = False
    model_call_performed: bool = False
    cloud_sync_performed: bool = False
    data_sent_external: bool = False
    surveillance_allowed: bool = False
    productivity_scoring_allowed: bool = False
    memory_write_allowed: bool = False
    memory_retrieval_allowed: bool = False
    memory_delete_allowed: bool = False
    memory_export_allowed: bool = False
    requires_backend_validation: bool = True
    requires_policy_check: bool = True
    requires_human_review_for_unknowns: bool = True


@dataclass(frozen=True)
class MemoryGovernanceInput:
    request_id: str | None
    memory_id: str | None
    memory_category: str | None
    memory_status: str
    memory_scope: str | None
    operation: str | None
    identity_scope_ref: str | None
    project_ref: str | None
    repository_ref: str | None
    session_ref: str | None
    tenant_ref: str | None
    workspace_ref: str | None
    profile_ref: str | None
    user_ref: str | None
    namespace: str | None
    data_boundary: str | None
    privacy_class: str | None
    sensitivity_class: str | None
    retention_policy: str
    ttl_seconds: int | None
    source_refs: tuple[Mapping[str, Any], ...]
    provenance: tuple[Mapping[str, Any], ...]
    confidence: float | None
    freshness: str | None
    explicit_user_confirmation: bool
    low_trust_sources: tuple[str, ...]
    limitations: tuple[str, ...]
    unknowns: tuple[str, ...]
    human_review_required: bool


@dataclass(frozen=True)
class MemoryGovernanceDecision:
    contract_version: str
    governance_status: str
    request_id: str | None
    memory_id: str | None
    memory_category: str | None
    memory_status: str
    memory_scope: str | None
    operation: str | None
    namespace: str | None
    project_ref: str | None
    repository_ref: str | None
    session_ref: str | None
    sensitivity_class: str | None
    retention_policy: str
    operation_status: str
    source_trust: str
    current_memory_candidate: bool
    failure_reasons: tuple[str, ...]
    failures: tuple[MemoryGovernanceFailure, ...]
    memory_input: MemoryGovernanceInput | None
    memory_contract: MemoryGovernanceContract
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = MEMORY_GOVERNANCE_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_memory_governance: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    frontend_authority: bool = False
    memory_write_performed: bool = False
    memory_retrieval_performed: bool = False
    memory_delete_performed: bool = False
    memory_export_performed: bool = False
    vector_index_touched: bool = False
    embedding_generated: bool = False
    reranking_performed: bool = False
    model_call_performed: bool = False
    cloud_sync_performed: bool = False
    data_sent_external: bool = False
    surveillance_allowed: bool = False
    productivity_scoring_allowed: bool = False
    memory_write_allowed: bool = False
    memory_retrieval_allowed: bool = False
    memory_delete_allowed: bool = False
    memory_export_allowed: bool = False
    requires_backend_validation: bool = True
    requires_policy_check: bool = True
    requires_human_review_for_unknowns: bool = True


def validate_memory_governance_request(
    request: Mapping[str, Any],
    *,
    identity_scope_decision: Any | None = None,
    local_model_inventory_decision: Any | None = None,
    model_auto_mode_decision: Any | None = None,
    context_compiler_decision: Any | None = None,
    repo_audit_decision: Any | None = None,
    developer_work_passport_decision: Any | None = None,
    compliance_evidence_decision: Any | None = None,
    mission_control_decision: Any | None = None,
    tool_simulation_decision: Any | None = None,
    plugin_review_decision: Any | None = None,
) -> MemoryGovernanceDecision:
    """Validate caller-supplied memory governance metadata.

    This helper is pure. It does not store, retrieve, delete, export, index,
    embed, rerank, call models, sync cloud data, or mutate runtime state.
    """

    data = deepcopy(dict(request))
    failures: list[MemoryGovernanceFailure] = []
    _validate_forbidden_claims("request", data, failures)

    request_id = _text(data.get("request_id"))
    memory_id = _text(data.get("memory_id"))
    memory_category = _text(data.get("memory_category"))
    memory_status = _text(data.get("memory_status")) or "proposed"
    memory_scope = _text(data.get("memory_scope"))
    operation = _text(data.get("operation"))
    namespace = _text(data.get("namespace"))
    privacy_class = _text(data.get("privacy_class"))
    sensitivity_class = _text(data.get("sensitivity_class"))
    retention_policy = _text(data.get("retention_policy")) or "no_persistence"
    project_ref = _text(data.get("project_ref"))
    repository_ref = _text(data.get("repository_ref"))
    session_ref = _text(data.get("session_ref"))
    source_refs = _mapping_tuple(data.get("source_refs"))
    provenance = _mapping_tuple(data.get("provenance"))
    explicit_user_confirmation = _truthy(data.get("explicit_user_confirmation"))
    low_trust_sources = tuple(field for field in LOW_TRUST_SOURCE_FIELDS if _truthy(data.get(field)))

    if not request_id:
        _add_failure(failures, "missing_request_id", "request_id", "request_id is required")
    if not memory_category:
        _add_failure(failures, "missing_memory_category", "memory_category", "memory_category is required")
    elif memory_category not in MEMORY_CATEGORIES:
        _add_failure(failures, "unsupported_memory_category", "memory_category", "memory_category is unknown")
    if not operation:
        _add_failure(failures, "missing_operation", "operation", "operation is required")
    elif operation not in MEMORY_OPERATIONS:
        _add_failure(failures, "unsupported_operation", "operation", "operation is unknown")
    if not memory_scope:
        _add_failure(failures, "missing_memory_scope", "memory_scope", "memory_scope is required")
    elif memory_scope not in MEMORY_SCOPES:
        _add_failure(failures, "unsupported_memory_scope", "memory_scope", "memory_scope is unknown")
    if not namespace:
        _add_failure(failures, "missing_namespace", "namespace", "namespace is required")
    if not privacy_class and not sensitivity_class:
        _add_failure(
            failures,
            "missing_privacy_or_sensitivity",
            "privacy_class",
            "privacy_class or sensitivity_class is required",
        )
    if memory_status not in MEMORY_STATUSES:
        _add_failure(failures, "unsupported_memory_status", "memory_status", "memory_status is unknown")
    if retention_policy not in RETENTION_POLICIES:
        _add_failure(failures, "unsupported_retention_policy", "retention_policy", "retention_policy is unknown")
    if sensitivity_class and sensitivity_class not in SENSITIVITY_CLASSES:
        _add_failure(failures, "unsupported_sensitivity_class", "sensitivity_class", "sensitivity_class is unknown")

    durable = memory_scope in DURABLE_SCOPES if memory_scope else False
    if durable and not (source_refs or provenance):
        _add_failure(
            failures,
            "missing_provenance_for_durable_memory",
            "source_refs",
            "durable memory proposals require source_refs or provenance",
        )
    if memory_scope == "session_only" and not session_ref:
        _add_failure(failures, "missing_session_ref", "session_ref", "session_only memory requires session_ref")
    if memory_scope in {"project_scoped", "repository_scoped"} and not project_ref:
        _add_failure(failures, "missing_project_ref", "project_ref", "project/repo memory requires project_ref")
    if memory_scope == "repository_scoped" and not repository_ref:
        _add_failure(
            failures,
            "missing_repository_ref",
            "repository_ref",
            "repository_scoped memory requires repository_ref",
        )
    if memory_scope == "user_profile_scoped" and not (
        _text(data.get("profile_ref")) and _text(data.get("user_ref"))
    ):
        _add_failure(
            failures,
            "missing_user_profile_scope",
            "profile_ref",
            "user_profile_scoped memory requires explicit user_ref and profile_ref",
        )
    if sensitivity_class in {"secret_like", "credential_like"} and operation in PERSISTENCE_OPERATIONS:
        _add_failure(
            failures,
            "sensitive_secret_memory_blocked",
            "sensitivity_class",
            "secret_like and credential_like memory persistence is blocked by default",
        )
    if sensitivity_class == "unknown" and operation in PERSISTENCE_OPERATIONS:
        _add_failure(
            failures,
            "unknown_sensitivity_blocks_persistence",
            "sensitivity_class",
            "unknown sensitivity blocks persistent memory proposals",
        )
    if sensitivity_class == "health_or_personal_sensitive" and not _truthy(data.get("human_review_required")):
        _add_failure(
            failures,
            "health_or_personal_sensitive_requires_review",
            "sensitivity_class",
            "health or personal sensitive memory requires explicit human review",
        )
    if memory_category == "personal_private_memory" and not explicit_user_confirmation:
        _add_failure(
            failures,
            "personal_private_memory_requires_confirmation",
            "explicit_user_confirmation",
            "personal/private memory requires explicit user confirmation",
        )
    if (
        memory_category == "personal_private_memory"
        and (_truthy(data.get("inferred_by_model")) or _truthy(data.get("generated_by_model")))
        and memory_status in {"active", "user_confirmed"}
        and not explicit_user_confirmation
    ):
        _add_failure(
            failures,
            "model_inferred_personal_memory_requires_confirmation",
            "inferred_by_model",
            "model-inferred personal memory cannot become active without confirmation",
        )

    if memory_status in NON_CURRENT_STATUSES and _truthy(data.get("treat_as_current")):
        _add_failure(
            failures,
            "non_current_memory_cannot_be_current",
            "memory_status",
            "stale, quarantined, superseded, deleted, expired, conflict, and rejected memory cannot be current",
        )

    if _has_cross_project_mixing(data, project_ref):
        _add_failure(
            failures,
            "cross_project_memory_mixing_denied",
            "project_ref",
            "cross-project memory mixing is denied by default",
        )
    if _mixes_aegis_and_ultron(data, project_ref):
        _add_failure(
            failures,
            "aegis_ultron_memory_merge_denied",
            "project_ref",
            "Aegis and Ultron memory scopes must remain distinct",
        )
    if _truthy(data.get("local_account_is_human_identity")) or _truthy(
        data.get("os_username_is_human_identity")
    ):
        _add_failure(
            failures,
            "local_account_not_human_identity",
            "local_account_ref",
            "local machine account metadata cannot prove human identity",
        )

    _validate_identity_scope(identity_scope_decision, memory_scope, project_ref, repository_ref, failures)
    for label, decision in {
        "local_model_inventory_decision": local_model_inventory_decision,
        "model_auto_mode_decision": model_auto_mode_decision,
        "context_compiler_decision": context_compiler_decision,
        "repo_audit_decision": repo_audit_decision,
        "developer_work_passport_decision": developer_work_passport_decision,
        "compliance_evidence_decision": compliance_evidence_decision,
        "mission_control_decision": mission_control_decision,
        "tool_simulation_decision": tool_simulation_decision,
        "plugin_review_decision": plugin_review_decision,
    }.items():
        _validate_related_decision(RELATED_DECISION_LABELS[label], decision, failures)

    human_review_required = bool(data.get("human_review_required")) or bool(low_trust_sources) or (
        sensitivity_class in {"sensitive", "health_or_personal_sensitive", "unknown"}
    )
    unknowns = tuple(dict.fromkeys((*_text_tuple(data.get("unknowns")), *low_trust_sources)))
    memory_input = MemoryGovernanceInput(
        request_id=request_id,
        memory_id=memory_id,
        memory_category=memory_category,
        memory_status=memory_status,
        memory_scope=memory_scope,
        operation=operation,
        identity_scope_ref=_text(data.get("identity_scope_ref")),
        project_ref=project_ref,
        repository_ref=repository_ref,
        session_ref=session_ref,
        tenant_ref=_text(data.get("tenant_ref")),
        workspace_ref=_text(data.get("workspace_ref")),
        profile_ref=_text(data.get("profile_ref")),
        user_ref=_text(data.get("user_ref")),
        namespace=namespace,
        data_boundary=_text(data.get("data_boundary")),
        privacy_class=privacy_class,
        sensitivity_class=sensitivity_class,
        retention_policy=retention_policy,
        ttl_seconds=_int_or_none(data.get("ttl_seconds")),
        source_refs=source_refs,
        provenance=provenance,
        confidence=_float_or_none(data.get("confidence")),
        freshness=_text(data.get("freshness")),
        explicit_user_confirmation=explicit_user_confirmation,
        low_trust_sources=low_trust_sources,
        limitations=_text_tuple(data.get("limitations")),
        unknowns=unknowns,
        human_review_required=human_review_required,
    )

    failure_reasons = tuple(dict.fromkeys(f.reason for f in failures))
    return MemoryGovernanceDecision(
        contract_version=MEMORY_GOVERNANCE_CONTRACT_VERSION,
        governance_status=_governance_status(memory_input, failure_reasons),
        request_id=request_id,
        memory_id=memory_id,
        memory_category=memory_category,
        memory_status=memory_status,
        memory_scope=memory_scope,
        operation=operation,
        namespace=namespace,
        project_ref=project_ref,
        repository_ref=repository_ref,
        session_ref=session_ref,
        sensitivity_class=sensitivity_class,
        retention_policy=retention_policy,
        operation_status=_operation_status(memory_input, failure_reasons),
        source_trust="lower_trust_source_material" if low_trust_sources else "caller_supplied_metadata",
        current_memory_candidate=memory_status not in NON_CURRENT_STATUSES and not failure_reasons,
        failure_reasons=failure_reasons,
        failures=tuple(failures),
        memory_input=memory_input,
        memory_contract=MemoryGovernanceContract(),
    )


def _validate_identity_scope(
    decision: Any | None,
    memory_scope: str | None,
    project_ref: str | None,
    repository_ref: str | None,
    failures: list[MemoryGovernanceFailure],
) -> None:
    if decision is None:
        if memory_scope in DURABLE_SCOPES:
            _add_failure(
                failures,
                "missing_identity_scope_for_persistent_memory",
                "identity_scope_decision",
                "persistent memory proposals require identity scope metadata",
            )
        return
    _validate_related_decision("identity_scope", decision, failures)
    status = str(_field_value(decision, "scope_status") or "")
    if status.startswith("blocked") or status == "clarification_required":
        _add_failure(
            failures,
            "identity_scope_not_ready",
            "identity_scope_decision.scope_status",
            "memory governance cannot proceed with blocked or unknown identity scope",
        )
    identity_project = _text(_field_value(decision, "project_ref"))
    identity_repo = _text(_field_value(decision, "repository_ref"))
    if memory_scope in {"project_scoped", "repository_scoped"} and project_ref and identity_project:
        if project_ref != identity_project:
            _add_failure(
                failures,
                "identity_project_scope_mismatch",
                "project_ref",
                "memory project_ref must match identity scope project_ref",
            )
    if memory_scope == "repository_scoped" and repository_ref and identity_repo:
        if repository_ref != identity_repo:
            _add_failure(
                failures,
                "identity_repository_scope_mismatch",
                "repository_ref",
                "memory repository_ref must match identity scope repository_ref",
            )


def _validate_related_decision(
    label: str,
    decision: Any | None,
    failures: list[MemoryGovernanceFailure],
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
            f"{label} cannot override memory governance with authority, execution, grants, evidence, verifier, memory, model, cloud, vector, tool, API, MCP, or scoring claims",
        )


def _validate_forbidden_claims(
    label: str,
    source: Any,
    failures: list[MemoryGovernanceFailure],
) -> None:
    for field, reason in FORBIDDEN_TRUTHY_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(
                failures,
                reason,
                f"{label}.{field}",
                f"{label} cannot claim memory authority, grants, permissions, evidence, verifier success, or scoring",
            )
    for field, reason in FORBIDDEN_BEHAVIOR_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(
                failures,
                reason,
                f"{label}.{field}",
                f"{label} cannot perform or request memory, vector, model, cloud, API, MCP, or tool behavior",
            )
    execution_permission = _field_value(source, "execution_permission")
    if execution_permission not in (None, "", MEMORY_GOVERNANCE_EXECUTION_PERMISSION):
        permission_text = str(execution_permission)
        if not permission_text.startswith("not_granted"):
            _add_failure(
                failures,
                "execution_permission_claim_denied",
                f"{label}.execution_permission",
                "memory governance metadata cannot grant execution permission",
            )


def _governance_status(
    memory_input: MemoryGovernanceInput,
    failure_reasons: tuple[str, ...],
) -> str:
    reasons = set(failure_reasons)
    if reasons:
        if "unsafe_related_decision" in reasons:
            return "blocked_by_unsafe_related_decision"
        if any(reason in reasons for reason in ("missing_project_ref", "missing_repository_ref", "missing_session_ref")):
            return "blocked_by_missing_scope"
        if "missing_identity_scope_for_persistent_memory" in reasons or "identity_scope_not_ready" in reasons:
            return "blocked_by_identity_scope"
        if any("sensitive" in reason or "credential" in reason or "secret" in reason for reason in reasons):
            return "blocked_by_sensitivity_policy"
        if any("cross_project" in reason or "aegis_ultron" in reason for reason in reasons):
            return "blocked_by_cross_project_scope"
        return "blocked_by_policy"
    if memory_input.human_review_required:
        return "proposal_requires_human_review"
    if memory_input.operation == "propose_rebuild_index_future":
        return "future_gated"
    return "proposal_ready"


def _operation_status(
    memory_input: MemoryGovernanceInput,
    failure_reasons: tuple[str, ...],
) -> str:
    if failure_reasons:
        return "blocked"
    if memory_input.operation == "propose_rebuild_index_future":
        return "future_gated_no_vector_touch"
    if memory_input.human_review_required:
        return "proposed_only_requires_human_review"
    return "proposed_only"


def _has_cross_project_mixing(data: Mapping[str, Any], project_ref: str | None) -> bool:
    candidates = []
    for field in ("related_project_refs", "cross_project_refs", "merge_project_refs"):
        candidates.extend(_text_tuple(data.get(field)))
    if not project_ref:
        return bool(candidates)
    return any(candidate and candidate != project_ref for candidate in candidates)


def _mixes_aegis_and_ultron(data: Mapping[str, Any], project_ref: str | None) -> bool:
    values = [project_ref or ""]
    for field in ("related_project_refs", "cross_project_refs", "merge_project_refs"):
        values.extend(_text_tuple(data.get(field)))
    lowered = [value.lower() for value in values if value]
    return any("aegis" in value for value in lowered) and any(
        "ultron" in value or "u.l.t.r.o.n" in value for value in lowered
    )


def _add_failure(
    failures: list[MemoryGovernanceFailure],
    reason: str,
    field: str,
    message: str,
) -> None:
    failures.append(MemoryGovernanceFailure(reason=reason, field=field, message=message))


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _text_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item).strip() for item in value if str(item).strip())
    return (str(value).strip(),) if str(value).strip() else ()


def _mapping_tuple(value: Any) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(deepcopy(item) for item in value if isinstance(item, Mapping))


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


def _int_or_none(value: Any) -> int | None:
    try:
        if value is None or value == "":
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _float_or_none(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
