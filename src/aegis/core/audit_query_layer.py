from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping


AUDIT_QUERY_LAYER_VERSION = "audit-query-layer-readiness/1"
AUDIT_QUERY_LAYER_EXECUTION_PERMISSION = "not_granted_by_audit_query_layer"

AUDIT_QUERY_CATEGORIES = {
    "command_lifecycle_query",
    "approval_query",
    "clarification_query",
    "policy_decision_query",
    "evidence_query",
    "verifier_query",
    "replay_debt_query",
    "journal_integrity_query",
    "maintenance_projection_query",
    "passive_observe_query",
    "model_provider_readiness_query",
    "local_model_inventory_query",
    "capability_lease_query",
    "context_policy_query",
    "memory_governance_query",
    "identity_scope_query",
    "repo_audit_readiness_query",
    "plugin_review_query",
    "compliance_evidence_query",
    "developer_work_passport_query",
    "future_action_attribution_query",
    "future_system_drift_query",
    "future_integrity_monitor_query",
    "unknown",
}

AUDIT_QUERY_OPERATIONS = {
    "classify_query",
    "propose_projection_query",
    "propose_time_window_query",
    "propose_ref_lookup",
    "propose_risk_summary",
    "propose_debt_summary",
    "propose_state_summary",
    "propose_operator_attention_summary",
    "propose_export_future",
    "unknown",
}

PROJECTION_SOURCE_CLASSES = {
    "caller_supplied_projection",
    "maintenance_scan_projection",
    "passive_observe_projection",
    "command_lifecycle_projection",
    "approval_projection",
    "evidence_audit_projection",
    "replay_diagnostics_projection",
    "policy_projection",
    "model_readiness_projection",
    "context_policy_projection",
    "memory_governance_projection",
    "identity_scope_projection",
    "repo_audit_readiness_projection",
    "future_action_attribution_projection",
    "future_system_drift_projection",
    "unknown",
}

RESULT_COMPLETENESS_CLASSES = {
    "complete_for_supplied_projection",
    "bounded_projection_only",
    "partial_projection",
    "stale_projection",
    "unknown_completeness",
    "unavailable",
}

FRESHNESS_CLASSES = {
    "current_supplied",
    "recent_supplied",
    "stale",
    "historical",
    "unknown",
}

RESULT_TRUST_LEVELS = {
    "backend_projection",
    "caller_supplied_metadata",
    "frontend_supplied_low_trust",
    "model_output_low_trust",
    "mcp_output_low_trust",
    "tool_output_low_trust",
    "unknown",
}

RISK_LEVELS = {"info", "low", "medium", "high", "critical", "unknown"}

LOW_TRUST_RESULT_LEVELS = {
    "frontend_supplied_low_trust",
    "model_output_low_trust",
    "mcp_output_low_trust",
    "tool_output_low_trust",
}

FUTURE_GATED_CATEGORIES = {
    "future_action_attribution_query",
    "future_system_drift_query",
    "future_integrity_monitor_query",
}

FUTURE_GATED_PROJECTION_SOURCES = {
    "future_action_attribution_projection",
    "future_system_drift_projection",
}

CATEGORY_REQUIRED_PROJECTIONS = {
    "command_lifecycle_query": ("command_lifecycle_projection",),
    "approval_query": ("approval_projection", "command_lifecycle_projection"),
    "clarification_query": ("approval_projection", "command_lifecycle_projection"),
    "policy_decision_query": ("policy_projection",),
    "evidence_query": ("evidence_audit_projection",),
    "verifier_query": ("evidence_audit_projection",),
    "replay_debt_query": ("replay_diagnostics_projection",),
    "journal_integrity_query": ("replay_diagnostics_projection",),
    "maintenance_projection_query": ("maintenance_scan_projection",),
    "passive_observe_query": ("passive_observe_projection",),
    "model_provider_readiness_query": ("model_readiness_projection",),
    "local_model_inventory_query": ("model_readiness_projection",),
    "capability_lease_query": ("policy_projection",),
    "context_policy_query": ("context_policy_projection",),
    "memory_governance_query": ("memory_governance_projection",),
    "identity_scope_query": ("identity_scope_projection",),
    "repo_audit_readiness_query": ("repo_audit_readiness_projection",),
    "plugin_review_query": ("policy_projection",),
    "compliance_evidence_query": ("evidence_audit_projection",),
    "developer_work_passport_query": ("evidence_audit_projection",),
    "future_action_attribution_query": ("future_action_attribution_projection",),
    "future_system_drift_query": ("future_system_drift_projection",),
    "future_integrity_monitor_query": ("future_system_drift_projection",),
}

FORBIDDEN_TRUTHY_FIELDS = {
    "authority": "authority_must_be_false",
    "runtime_dispatch_allowed": "runtime_dispatch_not_allowed",
    "approval_grant": "approval_grant_not_allowed",
    "capability_grant": "capability_grant_not_allowed",
    "lease_grant": "lease_grant_not_allowed",
    "evidence_provided_by_audit_query": "audit_query_cannot_provide_evidence",
    "evidence_created": "audit_query_cannot_provide_evidence",
    "verifier_success": "audit_query_cannot_mark_verifier_success",
    "verified_success": "audit_query_cannot_mark_verifier_success",
    "success": "success_claim_denied",
    "proof": "proof_claim_denied",
    "certification_claim": "certification_claim_denied",
    "query_output_is_evidence": "query_output_evidence_claim_denied",
    "query_output_is_verifier_success": "query_output_verifier_claim_denied",
    "frontend_authority": "frontend_authority_not_allowed",
    "frontend_result_is_authority": "frontend_authority_not_allowed",
    "model_output_is_authority": "model_output_authority_claim_denied",
    "mcp_output_is_authority": "mcp_output_authority_claim_denied",
    "tool_output_is_authority": "tool_output_authority_claim_denied",
    "model_output_is_truth": "model_output_truth_claim_denied",
    "mcp_output_is_truth": "mcp_output_truth_claim_denied",
    "tool_output_is_truth": "tool_output_truth_claim_denied",
}

FORBIDDEN_BEHAVIOR_FIELDS = {
    "live_query_executed": "live_query_execution_denied",
    "raw_journal_read": "raw_journal_read_denied",
    "raw_evidence_read": "raw_evidence_read_denied",
    "database_queried": "database_query_denied",
    "repo_scan_performed": "repo_scan_denied",
    "file_read_performed": "file_read_denied",
    "model_call_performed": "model_call_denied",
    "tool_call_performed": "tool_call_denied",
    "mcp_call_performed": "mcp_call_denied",
    "web_query_performed": "web_query_denied",
    "memory_retrieval_performed": "memory_retrieval_denied",
    "context_retrieval_performed": "context_retrieval_denied",
    "export_performed": "export_denied",
    "runtime_state_mutated": "runtime_state_mutation_denied",
    "journal_mutated": "journal_mutation_denied",
    "evidence_mutated": "evidence_mutation_denied",
    "replay_mutated": "replay_mutation_denied",
    "generated_artifact_created": "generated_artifact_creation_denied",
    "data_sent_external": "external_data_transfer_denied",
}


@dataclass(frozen=True)
class AuditQueryLayerFailure:
    reason: str
    field: str
    message: str


@dataclass(frozen=True)
class RelatedAuditQueryReference:
    label: str
    observed_status: str | None
    reference_only: bool = True
    authority: bool = False
    future_gated: bool = False
    implementation_claim: bool = False


@dataclass(frozen=True)
class AuditQueryLayerInput:
    request_id: str | None
    query_category: str | None
    query_operation: str | None
    namespace: str | None
    projection_source_class: str | None
    result_completeness_class: str | None
    freshness_class: str | None
    result_trust_level: str | None
    risk_level: str | None
    source_refs: tuple[Mapping[str, Any], ...]
    provenance: tuple[Mapping[str, Any], ...]
    limitations: tuple[str, ...]
    unknowns: tuple[str, ...]
    current_blocker: bool
    historical_debt: bool
    stale: bool
    future_gated: bool
    unavailable: bool
    unknown_state: bool
    full_history_requested: bool
    full_history_claimed: bool


@dataclass(frozen=True)
class AuditQueryLayerDecision:
    contract_version: str
    query_status: str
    request_id: str | None
    query_category: str | None
    query_operation: str | None
    namespace: str | None
    projection_source_class: str | None
    result_completeness_class: str | None
    freshness_class: str | None
    result_trust_level: str | None
    risk_level: str
    required_projection_kinds: tuple[str, ...]
    projection_truth_status: str
    lower_trust_result: bool
    current_blocker_preserved: bool
    historical_debt_preserved: bool
    stale_projection_preserved: bool
    future_gated_preserved: bool
    unknown_projection_preserved: bool
    unavailable_projection_preserved: bool
    bounded_projection_preserved: bool
    full_history_valid_for_supplied_projection: bool
    related_references: tuple[RelatedAuditQueryReference, ...]
    failure_reasons: tuple[str, ...]
    failures: tuple[AuditQueryLayerFailure, ...]
    query_input: AuditQueryLayerInput | None
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = AUDIT_QUERY_LAYER_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_audit_query: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    frontend_authority: bool = False
    live_query_executed: bool = False
    raw_journal_read: bool = False
    raw_evidence_read: bool = False
    database_queried: bool = False
    repo_scan_performed: bool = False
    file_read_performed: bool = False
    model_call_performed: bool = False
    tool_call_performed: bool = False
    mcp_call_performed: bool = False
    web_query_performed: bool = False
    memory_retrieval_performed: bool = False
    context_retrieval_performed: bool = False
    export_performed: bool = False
    runtime_state_mutated: bool = False
    journal_mutated: bool = False
    evidence_mutated: bool = False
    replay_mutated: bool = False
    generated_artifact_created: bool = False
    data_sent_external: bool = False
    full_history_claimed: bool = False
    requires_backend_validation: bool = True
    read_only_projection: bool = True


def validate_audit_query_layer_request(
    request: Mapping[str, Any] | None,
    *,
    passive_observe_decision: Any | None = None,
    maintenance_decision: Any | None = None,
    command_lifecycle_decision: Any | None = None,
    evidence_audit_decision: Any | None = None,
    policy_extension_decision: Any | None = None,
    context_policy_decision: Any | None = None,
    memory_governance_decision: Any | None = None,
    identity_scope_decision: Any | None = None,
    local_model_inventory_decision: Any | None = None,
    model_provider_readiness_decision: Any | None = None,
    model_auto_mode_decision: Any | None = None,
    capability_lease_decision: Any | None = None,
    repo_audit_decision: Any | None = None,
    compliance_evidence_decision: Any | None = None,
    developer_work_passport_decision: Any | None = None,
    mission_control_decision: Any | None = None,
    tool_simulation_decision: Any | None = None,
    plugin_review_decision: Any | None = None,
) -> AuditQueryLayerDecision:
    """Validate a future audit query plan without executing any query."""

    if not isinstance(request, Mapping):
        failure = AuditQueryLayerFailure(
            reason="missing_request",
            field="request",
            message="audit query layer requires caller-supplied metadata",
        )
        return _decision(
            query_input=None,
            related_references=(),
            failures=(failure,),
        )

    data = deepcopy(dict(request))
    failures: list[AuditQueryLayerFailure] = []
    related_references: list[RelatedAuditQueryReference] = []

    _validate_forbidden_claims("request", data, failures)
    for label, decision in {
        "passive_observe": passive_observe_decision,
        "maintenance": maintenance_decision,
        "command_lifecycle": command_lifecycle_decision,
        "evidence_audit": evidence_audit_decision,
        "policy_extension": policy_extension_decision,
        "context_policy": context_policy_decision,
        "memory_governance": memory_governance_decision,
        "identity_scope": identity_scope_decision,
        "local_model_inventory": local_model_inventory_decision,
        "model_provider_readiness": model_provider_readiness_decision,
        "model_auto_mode": model_auto_mode_decision,
        "capability_lease": capability_lease_decision,
        "repo_audit": repo_audit_decision,
        "compliance_evidence": compliance_evidence_decision,
        "developer_work_passport": developer_work_passport_decision,
        "mission_control": mission_control_decision,
        "tool_simulation": tool_simulation_decision,
        "plugin_review": plugin_review_decision,
    }.items():
        _validate_related_decision(label, decision, failures, related_references)

    query_input = AuditQueryLayerInput(
        request_id=_text(data.get("request_id")),
        query_category=_text(data.get("query_category")),
        query_operation=_text(data.get("query_operation")),
        namespace=_text(data.get("namespace")),
        projection_source_class=_text(data.get("projection_source_class")),
        result_completeness_class=_text(data.get("result_completeness_class")),
        freshness_class=_text(data.get("freshness_class")),
        result_trust_level=_text(data.get("result_trust_level")),
        risk_level=_text(data.get("risk_level")),
        source_refs=_mapping_tuple(data.get("source_refs")),
        provenance=_mapping_tuple(data.get("provenance")),
        limitations=_text_tuple(data.get("limitations")),
        unknowns=_text_tuple(data.get("unknowns")),
        current_blocker=_truthy(data.get("current_blocker")),
        historical_debt=_truthy(data.get("historical_debt")),
        stale=_truthy(data.get("stale")),
        future_gated=_truthy(data.get("future_gated")),
        unavailable=_truthy(data.get("unavailable")),
        unknown_state=_truthy(data.get("unknown_state")),
        full_history_requested=_truthy(data.get("full_history_requested")),
        full_history_claimed=_truthy(data.get("full_history_claimed")),
    )

    _validate_required(query_input, failures)
    _validate_truthfulness(query_input, failures)

    future_gated = _is_future_gated(query_input)
    return _decision(
        query_input=query_input,
        related_references=tuple(related_references),
        failures=tuple(failures),
        future_gated=future_gated,
    )


def _decision(
    *,
    query_input: AuditQueryLayerInput | None,
    related_references: tuple[RelatedAuditQueryReference, ...],
    failures: tuple[AuditQueryLayerFailure, ...],
    future_gated: bool = False,
) -> AuditQueryLayerDecision:
    required = _required_projection_kinds(query_input)
    full_history_valid = _full_history_valid(query_input, failures)
    return AuditQueryLayerDecision(
        contract_version=AUDIT_QUERY_LAYER_VERSION,
        query_status=_query_status(query_input, list(failures), future_gated),
        request_id=query_input.request_id if query_input else None,
        query_category=query_input.query_category if query_input else None,
        query_operation=query_input.query_operation if query_input else None,
        namespace=query_input.namespace if query_input else None,
        projection_source_class=query_input.projection_source_class if query_input else None,
        result_completeness_class=query_input.result_completeness_class if query_input else None,
        freshness_class=query_input.freshness_class if query_input else None,
        result_trust_level=query_input.result_trust_level if query_input else None,
        risk_level=_risk_level(query_input, list(failures)),
        required_projection_kinds=required,
        projection_truth_status=_projection_truth_status(query_input, list(failures)),
        lower_trust_result=bool(query_input and query_input.result_trust_level in LOW_TRUST_RESULT_LEVELS),
        current_blocker_preserved=bool(query_input and query_input.current_blocker),
        historical_debt_preserved=bool(query_input and query_input.historical_debt),
        stale_projection_preserved=bool(
            query_input
            and (query_input.stale or query_input.freshness_class == "stale" or query_input.result_completeness_class == "stale_projection")
        ),
        future_gated_preserved=bool(query_input and (query_input.future_gated or future_gated)),
        unknown_projection_preserved=bool(
            query_input
            and (query_input.unknown_state or query_input.freshness_class == "unknown" or query_input.result_completeness_class == "unknown_completeness")
        ),
        unavailable_projection_preserved=bool(
            query_input and (query_input.unavailable or query_input.result_completeness_class == "unavailable")
        ),
        bounded_projection_preserved=bool(
            query_input and query_input.result_completeness_class != "complete_for_supplied_projection"
        ),
        full_history_valid_for_supplied_projection=full_history_valid,
        related_references=related_references,
        failure_reasons=tuple(failure.reason for failure in failures),
        failures=failures,
        query_input=query_input,
        full_history_claimed=full_history_valid,
    )


def _validate_required(
    query_input: AuditQueryLayerInput,
    failures: list[AuditQueryLayerFailure],
) -> None:
    for field in (
        "request_id",
        "query_category",
        "query_operation",
        "namespace",
        "projection_source_class",
        "result_completeness_class",
        "freshness_class",
        "result_trust_level",
    ):
        if not getattr(query_input, field):
            _add_failure(failures, f"missing_{field}", field, f"audit query request is missing {field}")
    if query_input.query_category and query_input.query_category not in AUDIT_QUERY_CATEGORIES:
        _add_failure(failures, "unsupported_query_category", "query_category", "query category is not recognized")
    if query_input.query_operation and query_input.query_operation not in AUDIT_QUERY_OPERATIONS:
        _add_failure(failures, "unsupported_query_operation", "query_operation", "query operation is not recognized")
    if query_input.projection_source_class and query_input.projection_source_class not in PROJECTION_SOURCE_CLASSES:
        _add_failure(
            failures,
            "unsupported_projection_source_class",
            "projection_source_class",
            "projection source class is not recognized",
        )
    if query_input.result_completeness_class and query_input.result_completeness_class not in RESULT_COMPLETENESS_CLASSES:
        _add_failure(
            failures,
            "unsupported_result_completeness_class",
            "result_completeness_class",
            "result completeness class is not recognized",
        )
    if query_input.freshness_class and query_input.freshness_class not in FRESHNESS_CLASSES:
        _add_failure(failures, "unsupported_freshness_class", "freshness_class", "freshness class is not recognized")
    if query_input.result_trust_level and query_input.result_trust_level not in RESULT_TRUST_LEVELS:
        _add_failure(
            failures,
            "unsupported_result_trust_level",
            "result_trust_level",
            "result trust level is not recognized",
        )
    if query_input.risk_level and query_input.risk_level not in RISK_LEVELS:
        _add_failure(failures, "unsupported_risk_level", "risk_level", "risk level is not recognized")
    if not (query_input.source_refs or query_input.provenance):
        _add_failure(
            failures,
            "missing_source_refs_or_provenance",
            "source_refs",
            "audit query projections require source refs or provenance",
        )


def _validate_truthfulness(
    query_input: AuditQueryLayerInput,
    failures: list[AuditQueryLayerFailure],
) -> None:
    if query_input.full_history_claimed and query_input.result_completeness_class != "complete_for_supplied_projection":
        _add_failure(
            failures,
            "full_history_claim_requires_complete_supplied_projection",
            "full_history_claimed",
            "full history can only be claimed for explicitly complete caller-supplied projections",
        )
    if query_input.result_trust_level in LOW_TRUST_RESULT_LEVELS and query_input.result_completeness_class == "complete_for_supplied_projection":
        _add_failure(
            failures,
            "lower_trust_result_cannot_claim_complete_history",
            "result_trust_level",
            "frontend, model, MCP, and tool outputs cannot become complete audit history",
        )
    if query_input.current_blocker and query_input.historical_debt:
        _add_failure(
            failures,
            "current_blocker_and_historical_debt_must_remain_distinct",
            "current_blocker",
            "current blockers and historical debt must not be collapsed into one success state",
        )
    if query_input.unknown_state and query_input.result_completeness_class == "complete_for_supplied_projection":
        _add_failure(
            failures,
            "unknown_state_cannot_claim_complete_projection",
            "unknown_state",
            "unknown state cannot be marked complete",
        )
    if query_input.unavailable and query_input.result_completeness_class == "complete_for_supplied_projection":
        _add_failure(
            failures,
            "unavailable_projection_cannot_claim_complete_projection",
            "unavailable",
            "unavailable projection cannot be marked complete",
        )
    if query_input.stale and query_input.freshness_class == "current_supplied":
        _add_failure(
            failures,
            "stale_projection_cannot_claim_current_freshness",
            "freshness_class",
            "stale projection cannot claim current freshness",
        )


def _validate_related_decision(
    label: str,
    decision: Any | None,
    failures: list[AuditQueryLayerFailure],
    related_references: list[RelatedAuditQueryReference],
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
            f"{label} cannot grant audit query authority, dispatch, evidence, verifier success, execution, mutation, or exports",
        )
    related_references.append(
        RelatedAuditQueryReference(
            label=label,
            observed_status=_related_status(decision),
            reference_only=True,
            authority=False,
            future_gated=_related_future_gated(decision),
            implementation_claim=False,
        )
    )


def _validate_forbidden_claims(
    label: str,
    source: Any,
    failures: list[AuditQueryLayerFailure],
) -> None:
    for field, reason in FORBIDDEN_TRUTHY_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(
                failures,
                reason,
                f"{label}.{field}",
                f"{label} cannot claim authority, grants, evidence, verifier success, proof, certification, or truth",
            )
    for field, reason in FORBIDDEN_BEHAVIOR_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(
                failures,
                reason,
                f"{label}.{field}",
                f"{label} cannot execute live queries, reads, scans, calls, exports, mutations, or external transfer",
            )
    execution_permission = _field_value(source, "execution_permission")
    if execution_permission not in (None, "", AUDIT_QUERY_LAYER_EXECUTION_PERMISSION):
        permission_text = str(execution_permission)
        if not permission_text.startswith("not_granted"):
            _add_failure(
                failures,
                "execution_permission_claim_denied",
                f"{label}.execution_permission",
                "audit query metadata cannot grant execution permission",
            )


def _query_status(
    query_input: AuditQueryLayerInput | None,
    failures: list[AuditQueryLayerFailure],
    future_gated: bool,
) -> str:
    if query_input is None:
        return "blocked_by_missing_required_field"
    reasons = {failure.reason for failure in failures}
    if reasons:
        if "unsafe_related_decision" in reasons:
            return "blocked_by_unsafe_related_decision"
        if "full_history_claim_requires_complete_supplied_projection" in reasons:
            return "blocked_by_full_history_claim"
        if any("authority" in reason or "grant" in reason or "permission" in reason for reason in reasons):
            return "blocked_by_authority_claim"
        if any(
            "denied" in reason
            or "mutation" in reason
            or "external" in reason
            or "artifact" in reason
            for reason in reasons
        ):
            return "blocked_by_execution_claim"
        if any("evidence" in reason or "verifier" in reason or "proof" in reason or "certification" in reason for reason in reasons):
            return "blocked_by_evidence_claim"
        if any(reason.startswith("missing_") or reason.startswith("unsupported_") for reason in reasons):
            return "blocked_by_missing_required_field"
        return "blocked_by_policy"
    if future_gated:
        return "future_gated"
    if query_input.unavailable:
        return "projection_unavailable"
    if query_input.unknown_state or query_input.result_completeness_class == "unknown_completeness":
        return "clarification_required"
    if query_input.result_completeness_class == "complete_for_supplied_projection":
        return "query_plan_ready"
    return "query_plan_ready_bounded_projection"


def _projection_truth_status(
    query_input: AuditQueryLayerInput | None,
    failures: list[AuditQueryLayerFailure],
) -> str:
    if query_input is None or failures:
        return "blocked"
    if query_input.result_trust_level in LOW_TRUST_RESULT_LEVELS:
        return "lower_trust_reference_only"
    if query_input.result_completeness_class == "complete_for_supplied_projection":
        return "complete_for_supplied_projection_only"
    return "bounded_projection_only"


def _risk_level(query_input: AuditQueryLayerInput | None, failures: list[AuditQueryLayerFailure]) -> str:
    if failures:
        return "high"
    if query_input is None:
        return "unknown"
    if query_input.risk_level:
        return query_input.risk_level
    if query_input.current_blocker:
        return "high"
    if query_input.historical_debt or query_input.stale:
        return "medium"
    if query_input.unknown_state or query_input.unavailable:
        return "unknown"
    if query_input.future_gated or _is_future_gated(query_input):
        return "low"
    return "info"


def _required_projection_kinds(query_input: AuditQueryLayerInput | None) -> tuple[str, ...]:
    if query_input is None or query_input.query_category is None:
        return ()
    return CATEGORY_REQUIRED_PROJECTIONS.get(query_input.query_category, ())


def _is_future_gated(query_input: AuditQueryLayerInput) -> bool:
    return (
        query_input.future_gated
        or query_input.query_operation == "propose_export_future"
        or query_input.query_category in FUTURE_GATED_CATEGORIES
        or query_input.projection_source_class in FUTURE_GATED_PROJECTION_SOURCES
    )


def _full_history_valid(query_input: AuditQueryLayerInput | None, failures: tuple[AuditQueryLayerFailure, ...]) -> bool:
    if query_input is None or failures:
        return False
    return (
        query_input.full_history_claimed
        and query_input.result_completeness_class == "complete_for_supplied_projection"
        and query_input.result_trust_level not in LOW_TRUST_RESULT_LEVELS
        and bool(query_input.source_refs or query_input.provenance)
    )


def _related_status(decision: Any) -> str | None:
    for field in (
        "query_status",
        "observe_scope",
        "display_state",
        "readiness_status",
        "policy_status",
        "policy_outcome",
        "inventory_status",
        "governance_status",
        "scope_status",
        "lifecycle_state",
        "selection_mode",
        "decision_status",
        "runner_status",
    ):
        value = _field_value(decision, field)
        if value:
            return str(value)
    return None


def _related_future_gated(decision: Any) -> bool:
    status = str(_related_status(decision) or "")
    return _field_bool(decision, "future_gated") or "future" in status


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
    failures: list[AuditQueryLayerFailure],
    reason: str,
    field: str,
    message: str,
) -> None:
    failures.append(AuditQueryLayerFailure(reason=reason, field=field, message=message))
