from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping


ACTION_ATTRIBUTION_VERSION = "action-attribution-change-intelligence/1"
ACTION_ATTRIBUTION_EXECUTION_PERMISSION = "not_granted_by_action_attribution"

ATTRIBUTION_SUBJECTS = {
    "command_effect",
    "file_change",
    "process_change",
    "app_launch_observation",
    "provider_state_change",
    "model_inventory_change",
    "policy_decision_effect",
    "approval_effect",
    "clarification_effect",
    "evidence_state_change",
    "verifier_state_change",
    "replay_state_change",
    "maintenance_finding_change",
    "passive_observe_state_change",
    "repo_audit_readiness_change",
    "memory_governance_change",
    "context_policy_change",
    "capability_lease_candidate_change",
    "external_change_future",
    "unknown",
}

ATTRIBUTION_OPERATIONS = {
    "classify_attribution_candidate",
    "propose_causal_link",
    "propose_source_link",
    "propose_session_link",
    "propose_command_link",
    "propose_approval_link",
    "propose_evidence_ref_link",
    "propose_policy_link",
    "propose_unknown_external_change",
    "propose_operator_attention_summary",
    "propose_change_timeline_future",
    "unknown",
}

CONFIDENCE_CLASSES = {
    "direct_source_ref",
    "strong_candidate",
    "weak_candidate",
    "inferred_low_trust",
    "conflicting",
    "insufficient_evidence",
    "unknown",
}

CAUSALITY_CLASSES = {
    "causality_not_claimed",
    "direct_causality_candidate",
    "indirect_causality_candidate",
    "temporal_correlation_only",
    "external_or_unknown",
    "conflicting_causality",
    "impossible_to_determine",
    "unknown",
}

SOURCE_CLASSES = {
    "command_lifecycle_projection",
    "approval_projection",
    "policy_projection",
    "evidence_ref_projection",
    "verifier_projection",
    "audit_query_projection",
    "passive_observe_projection",
    "maintenance_projection",
    "caller_supplied_metadata",
    "frontend_supplied_low_trust",
    "model_output_low_trust",
    "mcp_output_low_trust",
    "tool_output_low_trust",
    "future_file_observation_projection",
    "future_integrity_monitor_projection",
    "unknown",
}

COMPLETENESS_CLASSES = {
    "complete_for_supplied_projection",
    "bounded_projection_only",
    "partial",
    "stale",
    "conflicting",
    "unavailable",
    "unknown",
}

LOW_TRUST_SOURCE_CLASSES = {
    "frontend_supplied_low_trust",
    "model_output_low_trust",
    "mcp_output_low_trust",
    "tool_output_low_trust",
}

FUTURE_GATED_SUBJECTS = {
    "file_change",
    "process_change",
    "external_change_future",
}

FUTURE_GATED_OPERATIONS = {"propose_change_timeline_future"}

FUTURE_GATED_SOURCE_CLASSES = {
    "future_file_observation_projection",
    "future_integrity_monitor_projection",
}

FORBIDDEN_TRUTHY_FIELDS = {
    "authority": "authority_must_be_false",
    "runtime_dispatch_allowed": "runtime_dispatch_not_allowed",
    "approval_grant": "approval_grant_not_allowed",
    "capability_grant": "capability_grant_not_allowed",
    "lease_grant": "lease_grant_not_allowed",
    "evidence_provided_by_attribution": "attribution_cannot_provide_evidence",
    "evidence_created": "attribution_cannot_provide_evidence",
    "verifier_success": "attribution_cannot_mark_verifier_success",
    "verified_success": "attribution_cannot_mark_verifier_success",
    "success": "success_claim_denied",
    "proof": "proof_claim_denied",
    "certification_claim": "certification_claim_denied",
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
    "live_observation_performed": "live_observation_denied",
    "file_scan_performed": "file_scan_denied",
    "file_read_performed": "file_read_denied",
    "process_scan_performed": "process_scan_denied",
    "raw_journal_read": "raw_journal_read_denied",
    "raw_evidence_read": "raw_evidence_read_denied",
    "database_queried": "database_query_denied",
    "model_call_performed": "model_call_denied",
    "tool_call_performed": "tool_call_denied",
    "mcp_call_performed": "mcp_call_denied",
    "web_query_performed": "web_query_denied",
    "memory_retrieval_performed": "memory_retrieval_denied",
    "context_retrieval_performed": "context_retrieval_denied",
    "attribution_record_created": "attribution_record_creation_denied",
    "timeline_created": "timeline_creation_denied",
    "report_generated": "report_generation_denied",
    "runtime_state_mutated": "runtime_state_mutation_denied",
    "journal_mutated": "journal_mutation_denied",
    "evidence_mutated": "evidence_mutation_denied",
    "replay_mutated": "replay_mutation_denied",
    "generated_artifact_created": "generated_artifact_creation_denied",
    "data_sent_external": "external_data_transfer_denied",
}


@dataclass(frozen=True)
class ActionAttributionFailure:
    reason: str
    field: str
    message: str


@dataclass(frozen=True)
class RelatedAttributionReference:
    label: str
    observed_status: str | None
    reference_only: bool = True
    authority: bool = False
    future_gated: bool = False
    implementation_claim: bool = False


@dataclass(frozen=True)
class ActionAttributionInput:
    request_id: str | None
    attribution_subject: str | None
    attribution_operation: str | None
    namespace: str | None
    source_class: str | None
    confidence_class: str | None
    causality_class: str | None
    completeness_class: str | None
    source_refs: tuple[Mapping[str, Any], ...]
    provenance: tuple[Mapping[str, Any], ...]
    limitations: tuple[str, ...]
    unknowns: tuple[str, ...]
    human_review_required: bool
    direct_source_refs_present: bool
    current_claim: bool
    full_attribution_claimed: bool
    causality_claim_final: bool


@dataclass(frozen=True)
class ActionAttributionDecision:
    contract_version: str
    attribution_status: str
    request_id: str | None
    attribution_subject: str | None
    attribution_operation: str | None
    namespace: str | None
    source_class: str | None
    confidence_class: str | None
    causality_class: str | None
    completeness_class: str | None
    attribution_truth_status: str
    lower_trust_source: bool
    direct_source_ref_preserved: bool
    inferred_low_trust_preserved: bool
    temporal_correlation_preserved: bool
    external_or_unknown_preserved: bool
    conflicting_attribution_preserved: bool
    insufficient_evidence_preserved: bool
    unknown_attribution_preserved: bool
    bounded_projection_preserved: bool
    stale_projection_preserved: bool
    future_gated_preserved: bool
    human_review_required: bool
    related_references: tuple[RelatedAttributionReference, ...]
    failure_reasons: tuple[str, ...]
    failures: tuple[ActionAttributionFailure, ...]
    attribution_input: ActionAttributionInput | None
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = ACTION_ATTRIBUTION_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_attribution: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    frontend_authority: bool = False
    live_observation_performed: bool = False
    file_scan_performed: bool = False
    file_read_performed: bool = False
    process_scan_performed: bool = False
    raw_journal_read: bool = False
    raw_evidence_read: bool = False
    database_queried: bool = False
    model_call_performed: bool = False
    tool_call_performed: bool = False
    mcp_call_performed: bool = False
    web_query_performed: bool = False
    memory_retrieval_performed: bool = False
    context_retrieval_performed: bool = False
    attribution_record_created: bool = False
    timeline_created: bool = False
    report_generated: bool = False
    runtime_state_mutated: bool = False
    journal_mutated: bool = False
    evidence_mutated: bool = False
    replay_mutated: bool = False
    generated_artifact_created: bool = False
    data_sent_external: bool = False
    causality_claim_final: bool = False
    requires_backend_validation: bool = True
    read_only_projection: bool = True


def validate_action_attribution_request(
    request: Mapping[str, Any] | None,
    *,
    audit_query_layer_decision: Any | None = None,
    passive_observe_decision: Any | None = None,
    identity_scope_decision: Any | None = None,
    memory_governance_decision: Any | None = None,
    policy_extension_decision: Any | None = None,
    context_policy_decision: Any | None = None,
    model_auto_mode_decision: Any | None = None,
    local_provider_health_decision: Any | None = None,
    local_provider_probe_design_decision: Any | None = None,
    capability_lease_decision: Any | None = None,
    local_model_inventory_decision: Any | None = None,
    mission_control_decision: Any | None = None,
    tool_simulation_decision: Any | None = None,
    repo_audit_decision: Any | None = None,
    compliance_evidence_decision: Any | None = None,
    developer_work_passport_decision: Any | None = None,
    plugin_review_decision: Any | None = None,
) -> ActionAttributionDecision:
    """Validate a future action attribution candidate without observing or mutating state."""

    if not isinstance(request, Mapping):
        failure = ActionAttributionFailure(
            reason="missing_request",
            field="request",
            message="action attribution requires caller-supplied metadata",
        )
        return _decision(attribution_input=None, related_references=(), failures=(failure,))

    data = deepcopy(dict(request))
    failures: list[ActionAttributionFailure] = []
    related_references: list[RelatedAttributionReference] = []

    _validate_forbidden_claims("request", data, failures)
    if _field_bool(data, "causality_claim_final"):
        _add_failure(
            failures,
            "final_causality_claim_denied",
            "request.causality_claim_final",
            "action attribution readiness cannot make final causality claims",
        )

    for label, decision in {
        "audit_query_layer": audit_query_layer_decision,
        "passive_observe": passive_observe_decision,
        "identity_scope": identity_scope_decision,
        "memory_governance": memory_governance_decision,
        "policy_extension": policy_extension_decision,
        "context_policy": context_policy_decision,
        "model_auto_mode": model_auto_mode_decision,
        "local_provider_health": local_provider_health_decision,
        "local_provider_probe_design": local_provider_probe_design_decision,
        "capability_lease": capability_lease_decision,
        "local_model_inventory": local_model_inventory_decision,
        "mission_control": mission_control_decision,
        "tool_simulation": tool_simulation_decision,
        "repo_audit": repo_audit_decision,
        "compliance_evidence": compliance_evidence_decision,
        "developer_work_passport": developer_work_passport_decision,
        "plugin_review": plugin_review_decision,
    }.items():
        _validate_related_decision(label, decision, failures, related_references)

    attribution_input = ActionAttributionInput(
        request_id=_text(data.get("request_id")),
        attribution_subject=_text(data.get("attribution_subject")),
        attribution_operation=_text(data.get("attribution_operation")),
        namespace=_text(data.get("namespace")),
        source_class=_text(data.get("source_class")),
        confidence_class=_text(data.get("confidence_class")),
        causality_class=_text(data.get("causality_class")),
        completeness_class=_text(data.get("completeness_class")),
        source_refs=_mapping_tuple(data.get("source_refs")),
        provenance=_mapping_tuple(data.get("provenance")),
        limitations=_text_tuple(data.get("limitations")),
        unknowns=_text_tuple(data.get("unknowns")),
        human_review_required=_truthy(data.get("human_review_required")),
        direct_source_refs_present=_truthy(data.get("direct_source_refs_present")),
        current_claim=_truthy(data.get("current_claim")),
        full_attribution_claimed=_truthy(data.get("full_attribution_claimed")),
        causality_claim_final=_truthy(data.get("causality_claim_final")),
    )

    _validate_required(attribution_input, failures)
    _validate_truthfulness(attribution_input, failures)

    return _decision(
        attribution_input=attribution_input,
        related_references=tuple(related_references),
        failures=tuple(failures),
    )


def _decision(
    *,
    attribution_input: ActionAttributionInput | None,
    related_references: tuple[RelatedAttributionReference, ...],
    failures: tuple[ActionAttributionFailure, ...],
) -> ActionAttributionDecision:
    future_gated = bool(attribution_input and _is_future_gated(attribution_input))
    return ActionAttributionDecision(
        contract_version=ACTION_ATTRIBUTION_VERSION,
        attribution_status=_attribution_status(attribution_input, list(failures), future_gated),
        request_id=attribution_input.request_id if attribution_input else None,
        attribution_subject=attribution_input.attribution_subject if attribution_input else None,
        attribution_operation=attribution_input.attribution_operation if attribution_input else None,
        namespace=attribution_input.namespace if attribution_input else None,
        source_class=attribution_input.source_class if attribution_input else None,
        confidence_class=attribution_input.confidence_class if attribution_input else None,
        causality_class=attribution_input.causality_class if attribution_input else None,
        completeness_class=attribution_input.completeness_class if attribution_input else None,
        attribution_truth_status=_truth_status(attribution_input, list(failures)),
        lower_trust_source=bool(attribution_input and attribution_input.source_class in LOW_TRUST_SOURCE_CLASSES),
        direct_source_ref_preserved=bool(attribution_input and attribution_input.confidence_class == "direct_source_ref"),
        inferred_low_trust_preserved=bool(
            attribution_input
            and (attribution_input.confidence_class == "inferred_low_trust" or attribution_input.source_class in LOW_TRUST_SOURCE_CLASSES)
        ),
        temporal_correlation_preserved=bool(attribution_input and attribution_input.causality_class == "temporal_correlation_only"),
        external_or_unknown_preserved=bool(attribution_input and attribution_input.causality_class == "external_or_unknown"),
        conflicting_attribution_preserved=bool(
            attribution_input
            and (attribution_input.confidence_class == "conflicting" or attribution_input.causality_class == "conflicting_causality")
        ),
        insufficient_evidence_preserved=bool(attribution_input and attribution_input.confidence_class == "insufficient_evidence"),
        unknown_attribution_preserved=bool(
            attribution_input
            and (
                attribution_input.attribution_subject == "unknown"
                or attribution_input.confidence_class == "unknown"
                or attribution_input.causality_class == "unknown"
                or attribution_input.completeness_class == "unknown"
            )
        ),
        bounded_projection_preserved=bool(
            attribution_input and attribution_input.completeness_class != "complete_for_supplied_projection"
        ),
        stale_projection_preserved=bool(attribution_input and attribution_input.completeness_class == "stale"),
        future_gated_preserved=future_gated,
        human_review_required=_human_review_required(attribution_input, list(failures), future_gated),
        related_references=related_references,
        failure_reasons=tuple(failure.reason for failure in failures),
        failures=failures,
        attribution_input=attribution_input,
    )


def _validate_required(
    attribution_input: ActionAttributionInput,
    failures: list[ActionAttributionFailure],
) -> None:
    for field in (
        "request_id",
        "attribution_subject",
        "attribution_operation",
        "namespace",
        "source_class",
        "confidence_class",
        "causality_class",
        "completeness_class",
    ):
        if not getattr(attribution_input, field):
            _add_failure(failures, f"missing_{field}", field, f"attribution request is missing {field}")
    if attribution_input.attribution_subject and attribution_input.attribution_subject not in ATTRIBUTION_SUBJECTS:
        _add_failure(failures, "unsupported_attribution_subject", "attribution_subject", "attribution subject is not recognized")
    if attribution_input.attribution_operation and attribution_input.attribution_operation not in ATTRIBUTION_OPERATIONS:
        _add_failure(failures, "unsupported_attribution_operation", "attribution_operation", "attribution operation is not recognized")
    if attribution_input.source_class and attribution_input.source_class not in SOURCE_CLASSES:
        _add_failure(failures, "unsupported_source_class", "source_class", "source class is not recognized")
    if attribution_input.confidence_class and attribution_input.confidence_class not in CONFIDENCE_CLASSES:
        _add_failure(failures, "unsupported_confidence_class", "confidence_class", "confidence class is not recognized")
    if attribution_input.causality_class and attribution_input.causality_class not in CAUSALITY_CLASSES:
        _add_failure(failures, "unsupported_causality_class", "causality_class", "causality class is not recognized")
    if attribution_input.completeness_class and attribution_input.completeness_class not in COMPLETENESS_CLASSES:
        _add_failure(failures, "unsupported_completeness_class", "completeness_class", "completeness class is not recognized")
    if not (attribution_input.source_refs or attribution_input.provenance):
        _add_failure(
            failures,
            "missing_source_refs_or_provenance",
            "source_refs",
            "attribution candidates require source refs or provenance",
        )


def _validate_truthfulness(
    attribution_input: ActionAttributionInput,
    failures: list[ActionAttributionFailure],
) -> None:
    if (
        attribution_input.causality_class == "direct_causality_candidate"
        and attribution_input.confidence_class != "direct_source_ref"
    ):
        _add_failure(
            failures,
            "direct_causality_requires_direct_source_ref",
            "confidence_class",
            "direct causality candidates require direct source refs",
        )
    if (
        attribution_input.causality_class == "direct_causality_candidate"
        and not (attribution_input.direct_source_refs_present or attribution_input.source_refs)
    ):
        _add_failure(
            failures,
            "direct_causality_requires_source_refs",
            "source_refs",
            "direct causality candidates require source refs",
        )
    if attribution_input.full_attribution_claimed and attribution_input.completeness_class != "complete_for_supplied_projection":
        _add_failure(
            failures,
            "full_attribution_requires_complete_supplied_projection",
            "full_attribution_claimed",
            "full attribution cannot be claimed for bounded, partial, stale, conflicting, unavailable, or unknown projections",
        )
    if attribution_input.current_claim and attribution_input.completeness_class == "stale":
        _add_failure(
            failures,
            "stale_projection_cannot_claim_current_causality",
            "current_claim",
            "stale projections cannot claim current causality",
        )
    if attribution_input.source_class in LOW_TRUST_SOURCE_CLASSES and attribution_input.confidence_class == "direct_source_ref":
        _add_failure(
            failures,
            "low_trust_source_cannot_claim_direct_source_ref",
            "source_class",
            "frontend, model, MCP, and tool output cannot become authoritative direct source refs",
        )
    if attribution_input.source_class in LOW_TRUST_SOURCE_CLASSES and attribution_input.completeness_class == "complete_for_supplied_projection":
        _add_failure(
            failures,
            "low_trust_source_cannot_claim_complete_attribution",
            "source_class",
            "frontend, model, MCP, and tool output cannot become complete attribution",
        )


def _validate_related_decision(
    label: str,
    decision: Any | None,
    failures: list[ActionAttributionFailure],
    related_references: list[RelatedAttributionReference],
) -> None:
    if decision is None:
        return
    before = len(failures)
    _validate_forbidden_claims(label, decision, failures)
    if _field_bool(decision, "causality_claim_final"):
        _add_failure(
            failures,
            "unsafe_related_decision",
            label,
            f"{label} cannot provide final causality for action attribution",
        )
    if len(failures) > before:
        _add_failure(
            failures,
            "unsafe_related_decision",
            label,
            f"{label} cannot grant attribution authority, dispatch, grants, evidence, verifier success, execution, mutation, or reports",
        )
    related_references.append(
        RelatedAttributionReference(
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
    failures: list[ActionAttributionFailure],
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
                f"{label} cannot perform live observation, scans, reads, calls, retrieval, records, timelines, reports, mutations, or external transfer",
            )
    execution_permission = _field_value(source, "execution_permission")
    if execution_permission not in (None, "", ACTION_ATTRIBUTION_EXECUTION_PERMISSION):
        permission_text = str(execution_permission)
        if not permission_text.startswith("not_granted"):
            _add_failure(
                failures,
                "execution_permission_claim_denied",
                f"{label}.execution_permission",
                "action attribution metadata cannot grant execution permission",
            )


def _attribution_status(
    attribution_input: ActionAttributionInput | None,
    failures: list[ActionAttributionFailure],
    future_gated: bool,
) -> str:
    if attribution_input is None:
        return "blocked_by_missing_required_field"
    reasons = {failure.reason for failure in failures}
    if reasons:
        if "unsafe_related_decision" in reasons:
            return "blocked_by_unsafe_related_decision"
        if any(reason.startswith("missing_") or reason.startswith("unsupported_") for reason in reasons):
            return "blocked_by_missing_required_field"
        if any("authority" in reason or "grant" in reason or "permission" in reason for reason in reasons):
            return "blocked_by_authority_claim"
        if "final_causality_claim_denied" in reasons:
            return "blocked_by_truthfulness_claim"
        if any(
            "denied" in reason
            or "mutation" in reason
            or "external" in reason
            or "artifact" in reason
            or "generation" in reason
            for reason in reasons
        ):
            return "blocked_by_execution_claim"
        if any("evidence" in reason or "verifier" in reason or "proof" in reason or "certification" in reason for reason in reasons):
            return "blocked_by_evidence_claim"
        if any("causality" in reason or "attribution" in reason for reason in reasons):
            return "blocked_by_truthfulness_claim"
        return "blocked_by_policy"
    if future_gated:
        return "future_gated"
    if attribution_input.confidence_class in {"conflicting", "insufficient_evidence"} or attribution_input.causality_class == "conflicting_causality":
        return "requires_human_review"
    if attribution_input.causality_class in {"external_or_unknown", "impossible_to_determine", "unknown"}:
        return "unknown_or_external_preserved"
    return "attribution_candidate_ready"


def _truth_status(attribution_input: ActionAttributionInput | None, failures: list[ActionAttributionFailure]) -> str:
    if attribution_input is None or failures:
        return "blocked"
    if attribution_input.source_class in LOW_TRUST_SOURCE_CLASSES:
        return "lower_trust_reference_only"
    if attribution_input.confidence_class == "direct_source_ref":
        return "direct_source_ref_candidate"
    if attribution_input.causality_class == "temporal_correlation_only":
        return "temporal_correlation_only"
    if attribution_input.causality_class == "external_or_unknown":
        return "external_or_unknown"
    if attribution_input.confidence_class == "conflicting" or attribution_input.causality_class == "conflicting_causality":
        return "conflicting"
    if attribution_input.confidence_class == "insufficient_evidence":
        return "insufficient_evidence"
    return "candidate_only"


def _human_review_required(
    attribution_input: ActionAttributionInput | None,
    failures: list[ActionAttributionFailure],
    future_gated: bool,
) -> bool:
    if attribution_input is None:
        return True
    if failures or future_gated or attribution_input.human_review_required:
        return True
    return (
        attribution_input.confidence_class in {"conflicting", "insufficient_evidence", "unknown", "inferred_low_trust"}
        or attribution_input.causality_class
        in {"temporal_correlation_only", "external_or_unknown", "conflicting_causality", "impossible_to_determine", "unknown"}
        or attribution_input.completeness_class in {"partial", "stale", "conflicting", "unavailable", "unknown"}
    )


def _is_future_gated(attribution_input: ActionAttributionInput) -> bool:
    return (
        attribution_input.attribution_subject in FUTURE_GATED_SUBJECTS
        or attribution_input.attribution_operation in FUTURE_GATED_OPERATIONS
        or attribution_input.source_class in FUTURE_GATED_SOURCE_CLASSES
    )


def _related_status(decision: Any) -> str | None:
    for field in (
        "attribution_status",
        "query_status",
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
        "probe_result_status",
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
    failures: list[ActionAttributionFailure],
    reason: str,
    field: str,
    message: str,
) -> None:
    failures.append(ActionAttributionFailure(reason=reason, field=field, message=message))
