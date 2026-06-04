from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping


IDENTITY_SCOPE_CONTRACT_VERSION = "identity-tenant-scope-contract/1"
IDENTITY_SCOPE_EXECUTION_PERMISSION = "not_granted_by_identity_scope"

SUBJECT_KINDS = {
    "local_single_user",
    "local_multi_profile_future",
    "project",
    "workspace",
    "repository",
    "organization_future",
    "external_agent_future",
    "unknown",
}

PERSISTENCE_SCOPES = {
    "session_only",
    "project_scoped",
    "workspace_scoped",
    "user_profile_scoped",
    "tenant_scoped_future",
    "machine_local_only",
    "disabled",
    "unknown",
}

DATA_BOUNDARIES = {
    "local_only",
    "project_local_only",
    "private_repo_local_only",
    "cloud_disallowed",
    "cloud_allowed_later",
    "external_agent_observation_future",
    "unknown",
}

PROJECT_REQUIRED_PERSISTENCE_SCOPES = {"project_scoped"}
PROJECT_REQUIRED_SUBJECT_KINDS = {"project", "repository"}
REPOSITORY_REQUIRED_SUBJECT_KINDS = {"repository"}
CLOUD_BLOCKING_BOUNDARIES = {
    "local_only",
    "project_local_only",
    "private_repo_local_only",
    "cloud_disallowed",
    "unknown",
}

FORBIDDEN_TRUTHY_FIELDS = {
    "authority": "authority_must_be_false",
    "runtime_dispatch_allowed": "runtime_dispatch_not_allowed",
    "approval_grant": "approval_grant_not_allowed",
    "capability_grant": "capability_grant_not_allowed",
    "lease_grant": "lease_grant_not_allowed",
    "frontend_authority": "frontend_authority_not_allowed",
    "evidence_provided_by_identity_scope": "identity_scope_cannot_provide_evidence",
    "evidence_provided_by_inventory": "identity_scope_cannot_provide_evidence",
    "evidence_created": "identity_scope_cannot_provide_evidence",
    "verifier_success": "identity_scope_cannot_mark_verifier_success",
    "verified_success": "identity_scope_cannot_mark_verifier_success",
    "success": "success_claim_denied",
    "memory_write_allowed": "memory_write_not_allowed",
    "memory_retrieval_allowed": "memory_retrieval_not_allowed",
    "cloud_routing_allowed": "cloud_routing_not_allowed",
    "model_call_allowed": "model_call_not_allowed",
    "context_persistence_allowed": "context_persistence_not_allowed",
    "vector_index_allowed": "vector_index_not_allowed",
    "external_agent_tracking_allowed": "external_agent_tracking_not_allowed",
    "surveillance_allowed": "surveillance_not_allowed",
    "productivity_scoring_allowed": "productivity_scoring_not_allowed",
}

FORBIDDEN_BEHAVIOR_FIELDS = {
    "memory_write_performed": "memory_write_request_denied",
    "memory_write_requested": "memory_write_request_denied",
    "memory_retrieval_performed": "memory_retrieval_request_denied",
    "memory_read_requested": "memory_retrieval_request_denied",
    "model_call_performed": "model_call_request_denied",
    "model_call_requested": "model_call_request_denied",
    "provider_called": "provider_call_request_denied",
    "cloud_routing_performed": "cloud_routing_request_denied",
    "cloud_route_requested": "cloud_routing_request_denied",
    "vector_index_performed": "vector_index_request_denied",
    "vector_index_requested": "vector_index_request_denied",
    "context_persisted": "context_persistence_request_denied",
    "context_persistence_requested": "context_persistence_request_denied",
    "tool_call_performed": "tool_call_request_denied",
    "tool_call_requested": "tool_call_request_denied",
    "api_call_performed": "api_call_request_denied",
    "api_call_requested": "api_call_request_denied",
    "mcp_call_performed": "mcp_call_request_denied",
    "mcp_call_requested": "mcp_call_request_denied",
    "external_agent_tracking_performed": "external_agent_tracking_request_denied",
    "external_agent_tracking_requested": "external_agent_tracking_request_denied",
}

HUMAN_IDENTITY_INFERENCE_FIELDS = {
    "human_identity_verified",
    "verified_human_identity",
    "local_account_is_human_identity",
    "os_username_is_human_identity",
    "inferred_human_identity_from_local_account",
    "infer_human_identity_from_os",
}

RELATED_DECISION_LABELS = {
    "local_model_inventory_decision": "local_model_inventory",
    "model_auto_mode_decision": "model_auto_mode",
    "memory_governance_decision": "memory_governance",
    "context_compiler_decision": "context_compiler",
    "repo_audit_decision": "repo_audit",
    "developer_work_passport_decision": "developer_work_passport",
    "compliance_evidence_decision": "compliance_evidence",
    "mission_control_decision": "mission_control",
    "tool_simulation_decision": "tool_simulation",
    "plugin_review_decision": "plugin_review",
}


@dataclass(frozen=True)
class IdentityScopeFailure:
    reason: str
    field: str
    message: str


@dataclass(frozen=True)
class IdentityScopeContract:
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = IDENTITY_SCOPE_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_identity_scope: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    frontend_authority: bool = False
    memory_write_allowed: bool = False
    memory_retrieval_allowed: bool = False
    cloud_routing_allowed: bool = False
    model_call_allowed: bool = False
    context_persistence_allowed: bool = False
    vector_index_allowed: bool = False
    external_agent_tracking_allowed: bool = False
    surveillance_allowed: bool = False
    productivity_scoring_allowed: bool = False
    requires_backend_validation: bool = True
    requires_policy_check: bool = True
    requires_human_review_for_unknowns: bool = True


@dataclass(frozen=True)
class IdentityScopeInput:
    request_id: str | None
    scope_id: str | None
    subject_kind: str | None
    subject_ref: str | None
    user_ref: str | None
    profile_ref: str | None
    operator_ref: str | None
    tenant_ref: str | None
    organization_ref: str | None
    workspace_ref: str | None
    project_ref: str | None
    repository_ref: str | None
    session_ref: str | None
    machine_ref: str | None
    local_account_ref: str | None
    namespace: str | None
    data_boundary: str | None
    privacy_class: str | None
    persistence_scope: str
    retention_scope: str | None
    cloud_allowed_scope: str | None
    model_allowed_scope: str | None
    memory_allowed_scope: str | None
    source_refs: tuple[Mapping[str, Any], ...]
    limitations: tuple[str, ...]
    unknowns: tuple[str, ...]
    human_review_required: bool


@dataclass(frozen=True)
class IdentityScopeDecision:
    scope_contract_version: str
    scope_status: str
    request_id: str | None
    scope_id: str | None
    subject_kind: str | None
    namespace: str | None
    project_ref: str | None
    repository_ref: str | None
    persistence_scope: str
    data_boundary: str | None
    privacy_class: str | None
    persistence_eligibility: str
    cloud_routing_eligibility: str
    cross_project_scope_allowed: bool
    unknown_identity_fields: tuple[str, ...]
    failure_reasons: tuple[str, ...]
    failures: tuple[IdentityScopeFailure, ...]
    identity_input: IdentityScopeInput | None
    identity_contract: IdentityScopeContract
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = IDENTITY_SCOPE_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_identity_scope: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    frontend_authority: bool = False
    memory_write_allowed: bool = False
    memory_retrieval_allowed: bool = False
    cloud_routing_allowed: bool = False
    model_call_allowed: bool = False
    context_persistence_allowed: bool = False
    vector_index_allowed: bool = False
    external_agent_tracking_allowed: bool = False
    surveillance_allowed: bool = False
    productivity_scoring_allowed: bool = False
    requires_backend_validation: bool = True
    requires_policy_check: bool = True
    requires_human_review_for_unknowns: bool = True


def validate_identity_scope_request(
    request: Mapping[str, Any],
    *,
    local_model_inventory_decision: Any | None = None,
    model_auto_mode_decision: Any | None = None,
    memory_governance_decision: Any | None = None,
    context_compiler_decision: Any | None = None,
    repo_audit_decision: Any | None = None,
    developer_work_passport_decision: Any | None = None,
    compliance_evidence_decision: Any | None = None,
    mission_control_decision: Any | None = None,
    tool_simulation_decision: Any | None = None,
    plugin_review_decision: Any | None = None,
) -> IdentityScopeDecision:
    """Validate caller-supplied identity scope metadata.

    This helper is pure. It does not inspect the OS, infer real people, persist
    identity, write memory, route models, create evidence, or dispatch runtime
    behavior.
    """

    data = deepcopy(dict(request))
    failures: list[IdentityScopeFailure] = []
    _validate_forbidden_claims("request", data, failures)

    request_id = _text(data.get("request_id"))
    scope_id = _text(data.get("scope_id"))
    subject_kind = _text(data.get("subject_kind"))
    namespace = _text(data.get("namespace"))
    privacy_class = _text(data.get("privacy_class"))
    data_boundary = _text(data.get("data_boundary"))
    persistence_scope = _text(data.get("persistence_scope")) or "session_only"
    project_ref = _text(data.get("project_ref"))
    repository_ref = _text(data.get("repository_ref"))
    session_ref = _text(data.get("session_ref"))

    if not request_id and not scope_id:
        _add_failure(failures, "missing_scope_identity", "request_id", "request_id or scope_id is required")
    if not subject_kind:
        _add_failure(failures, "missing_subject_kind", "subject_kind", "subject_kind is required")
    elif subject_kind not in SUBJECT_KINDS:
        _add_failure(failures, "unsupported_subject_kind", "subject_kind", "subject_kind is not recognized")
    if not namespace:
        _add_failure(failures, "missing_namespace", "namespace", "namespace is required")
    if not privacy_class and not data_boundary:
        _add_failure(
            failures,
            "missing_privacy_or_data_boundary",
            "privacy_class",
            "privacy_class or data_boundary is required",
        )
    if persistence_scope not in PERSISTENCE_SCOPES:
        _add_failure(
            failures,
            "unsupported_persistence_scope",
            "persistence_scope",
            "persistence_scope is not recognized",
        )
    if data_boundary and data_boundary not in DATA_BOUNDARIES:
        _add_failure(
            failures,
            "unsupported_data_boundary",
            "data_boundary",
            "data_boundary is not recognized",
        )

    if persistence_scope == "session_only" and not session_ref:
        _add_failure(failures, "missing_session_ref", "session_ref", "session_only scope requires session_ref")
    if (
        persistence_scope in PROJECT_REQUIRED_PERSISTENCE_SCOPES
        or subject_kind in PROJECT_REQUIRED_SUBJECT_KINDS
        or _truthy(data.get("project_memory_requested"))
        or _truthy(data.get("repo_context_requested"))
        or _truthy(data.get("persistent_context_requested"))
    ) and not project_ref:
        _add_failure(
            failures,
            "missing_project_ref",
            "project_ref",
            "project/repository scoped memory, context, and product records require project_ref",
        )
    if subject_kind in REPOSITORY_REQUIRED_SUBJECT_KINDS and not repository_ref:
        _add_failure(
            failures,
            "missing_repository_ref",
            "repository_ref",
            "repository scoped objects require repository_ref",
        )

    unknown_identity_fields = _unknown_identity_fields(data, subject_kind)
    if subject_kind == "unknown":
        unknown_identity_fields = _append_unique(unknown_identity_fields, "subject_kind")
        _add_failure(
            failures,
            "identity_unknown_requires_human_review",
            "subject_kind",
            "unknown identity requires human review and cannot enable persistence or cloud routing",
        )

    if _has_cross_project_mixing(data, project_ref):
        _add_failure(
            failures,
            "cross_project_scope_mixing_denied",
            "project_ref",
            "cross-project scope mixing is denied by default",
        )
    if _mixes_aegis_and_ultron(data, project_ref):
        _add_failure(
            failures,
            "aegis_ultron_scope_merge_denied",
            "project_ref",
            "Aegis and Ultron project scopes must remain distinct",
        )
    for field in HUMAN_IDENTITY_INFERENCE_FIELDS:
        if _truthy(data.get(field)):
            _add_failure(
                failures,
                "local_account_not_human_identity",
                field,
                "local machine or OS account metadata cannot prove a human identity",
            )

    if subject_kind == "external_agent_future" or data_boundary == "external_agent_observation_future":
        if _truthy(data.get("active_external_agent_tracking")) or _truthy(
            data.get("external_agent_tracking_requested")
        ):
            _add_failure(
                failures,
                "external_agent_tracking_not_allowed",
                "external_agent_tracking_requested",
                "external agent tracking requires a future explicit scope sprint",
            )
        unknown_identity_fields = _append_unique(unknown_identity_fields, "external_agent_future_scope")

    for label, decision in {
        "local_model_inventory_decision": local_model_inventory_decision,
        "model_auto_mode_decision": model_auto_mode_decision,
        "memory_governance_decision": memory_governance_decision,
        "context_compiler_decision": context_compiler_decision,
        "repo_audit_decision": repo_audit_decision,
        "developer_work_passport_decision": developer_work_passport_decision,
        "compliance_evidence_decision": compliance_evidence_decision,
        "mission_control_decision": mission_control_decision,
        "tool_simulation_decision": tool_simulation_decision,
        "plugin_review_decision": plugin_review_decision,
    }.items():
        _validate_related_decision(RELATED_DECISION_LABELS[label], decision, failures)

    identity_input = IdentityScopeInput(
        request_id=request_id,
        scope_id=scope_id,
        subject_kind=subject_kind,
        subject_ref=_text(data.get("subject_ref")),
        user_ref=_text(data.get("user_ref")),
        profile_ref=_text(data.get("profile_ref")),
        operator_ref=_text(data.get("operator_ref")),
        tenant_ref=_text(data.get("tenant_ref")),
        organization_ref=_text(data.get("organization_ref")),
        workspace_ref=_text(data.get("workspace_ref")),
        project_ref=project_ref,
        repository_ref=repository_ref,
        session_ref=session_ref,
        machine_ref=_text(data.get("machine_ref")),
        local_account_ref=_text(data.get("local_account_ref")),
        namespace=namespace,
        data_boundary=data_boundary,
        privacy_class=privacy_class,
        persistence_scope=persistence_scope,
        retention_scope=_text(data.get("retention_scope")),
        cloud_allowed_scope=_text(data.get("cloud_allowed_scope")),
        model_allowed_scope=_text(data.get("model_allowed_scope")),
        memory_allowed_scope=_text(data.get("memory_allowed_scope")),
        source_refs=_mapping_tuple(data.get("source_refs")),
        limitations=_text_tuple(data.get("limitations")),
        unknowns=tuple(unknown_identity_fields),
        human_review_required=bool(data.get("human_review_required") or unknown_identity_fields),
    )

    failure_reasons = tuple(dict.fromkeys(f.reason for f in failures))
    return IdentityScopeDecision(
        scope_contract_version=IDENTITY_SCOPE_CONTRACT_VERSION,
        scope_status=_scope_status(identity_input, failure_reasons),
        request_id=request_id,
        scope_id=scope_id,
        subject_kind=subject_kind,
        namespace=namespace,
        project_ref=project_ref,
        repository_ref=repository_ref,
        persistence_scope=persistence_scope,
        data_boundary=data_boundary,
        privacy_class=privacy_class,
        persistence_eligibility=_persistence_eligibility(identity_input, failure_reasons),
        cloud_routing_eligibility=_cloud_routing_eligibility(identity_input, failure_reasons),
        cross_project_scope_allowed=False,
        unknown_identity_fields=tuple(unknown_identity_fields),
        failure_reasons=failure_reasons,
        failures=tuple(failures),
        identity_input=identity_input,
        identity_contract=IdentityScopeContract(),
    )


def _validate_related_decision(
    label: str,
    decision: Any | None,
    failures: list[IdentityScopeFailure],
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
            f"{label} cannot override identity scope with authority, dispatch, grant, evidence, verifier, memory, model, cloud, tool, API, MCP, or tracking claims",
        )


def _validate_forbidden_claims(
    label: str,
    source: Any,
    failures: list[IdentityScopeFailure],
) -> None:
    for field, reason in FORBIDDEN_TRUTHY_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(
                failures,
                reason,
                f"{label}.{field}",
                f"{label} cannot claim identity authority, grants, permissions, evidence, verifier success, or tracking",
            )
    for field, reason in FORBIDDEN_BEHAVIOR_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(
                failures,
                reason,
                f"{label}.{field}",
                f"{label} cannot perform or request memory, model, cloud, vector, tool, API, MCP, or tracking behavior",
            )
    execution_permission = _field_value(source, "execution_permission")
    if execution_permission not in (None, "", IDENTITY_SCOPE_EXECUTION_PERMISSION):
        permission_text = str(execution_permission)
        if not permission_text.startswith("not_granted"):
            _add_failure(
                failures,
                "execution_permission_claim_denied",
                f"{label}.execution_permission",
                "identity scope metadata cannot grant execution permission",
            )


def _scope_status(
    identity_input: IdentityScopeInput,
    failure_reasons: tuple[str, ...],
) -> str:
    reasons = set(failure_reasons)
    if reasons:
        if "unsafe_related_decision" in reasons:
            return "blocked_by_unsafe_related_decision"
        if "cross_project_scope_mixing_denied" in reasons or "aegis_ultron_scope_merge_denied" in reasons:
            return "blocked_by_cross_project_scope"
        if "missing_project_ref" in reasons:
            return "blocked_by_missing_project_ref"
        if "missing_repository_ref" in reasons:
            return "blocked_by_missing_repository_ref"
        if "missing_session_ref" in reasons:
            return "blocked_by_missing_session_ref"
        if "identity_unknown_requires_human_review" in reasons:
            return "clarification_required"
        return "blocked_by_policy"
    if identity_input.human_review_required:
        return "scope_ready_requires_human_review"
    return "scope_ready"


def _persistence_eligibility(
    identity_input: IdentityScopeInput,
    failure_reasons: tuple[str, ...],
) -> str:
    if failure_reasons:
        return "blocked_by_identity_scope"
    if identity_input.persistence_scope == "session_only":
        return "session_only_no_persistent_memory"
    if identity_input.persistence_scope in {"project_scoped", "workspace_scoped", "user_profile_scoped"}:
        return "metadata_ready_policy_required"
    if identity_input.persistence_scope in {"disabled", "unknown"}:
        return "blocked_by_unknown_or_disabled_scope"
    return "future_gated_policy_required"


def _cloud_routing_eligibility(
    identity_input: IdentityScopeInput,
    failure_reasons: tuple[str, ...],
) -> str:
    if failure_reasons:
        return "blocked_by_identity_scope"
    boundary = identity_input.data_boundary or "unknown"
    if boundary in CLOUD_BLOCKING_BOUNDARIES:
        return "blocked_by_data_boundary"
    if boundary == "cloud_allowed_later":
        return "future_gated_policy_required"
    return "blocked_by_unknown_or_future_scope"


def _unknown_identity_fields(data: Mapping[str, Any], subject_kind: str | None) -> tuple[str, ...]:
    unknowns = list(_text_tuple(data.get("unknowns")))
    for field in ("tenant_ref", "workspace_ref", "user_ref", "profile_ref"):
        if not _text(data.get(field)):
            unknowns.append(field)
    if subject_kind in (None, "", "unknown"):
        unknowns.append("subject_kind")
    return tuple(dict.fromkeys(unknowns))


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
    has_aegis = any("aegis" in value for value in lowered)
    has_ultron = any("ultron" in value or "u.l.t.r.o.n" in value for value in lowered)
    return has_aegis and has_ultron


def _add_failure(
    failures: list[IdentityScopeFailure],
    reason: str,
    field: str,
    message: str,
) -> None:
    failures.append(IdentityScopeFailure(reason=reason, field=field, message=message))


def _append_unique(values: tuple[str, ...], value: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys((*values, value)))


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
