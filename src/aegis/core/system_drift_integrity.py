from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping


SYSTEM_DRIFT_INTEGRITY_VERSION = "system-drift-integrity-monitoring-readiness/1"
SYSTEM_DRIFT_INTEGRITY_EXECUTION_PERMISSION = "not_granted_by_system_drift_integrity"

DRIFT_SUBJECTS = {
    "file_metadata_drift",
    "file_hash_drift_future",
    "config_drift",
    "dependency_drift",
    "environment_drift",
    "process_presence_drift",
    "service_port_drift",
    "app_registry_drift",
    "tool_registry_drift",
    "provider_config_drift",
    "model_inventory_drift",
    "policy_boundary_drift",
    "dispatch_surface_drift",
    "memory_governance_drift",
    "context_policy_drift",
    "capability_lease_drift",
    "passive_observe_state_drift",
    "maintenance_projection_drift",
    "evidence_debt_drift",
    "replay_diagnostics_drift",
    "resource_pressure_drift",
    "frontend_generated_drift",
    "external_unknown_drift",
    "unknown",
}

INTEGRITY_SUBJECTS = {
    "critical_config_integrity",
    "dispatch_policy_integrity",
    "provider_config_integrity",
    "model_metadata_integrity",
    "dependency_integrity",
    "frontend_generated_artifact_integrity",
    "journal_boundary_integrity_future",
    "evidence_ref_integrity_future",
    "repo_source_integrity_future",
    "plugin_manifest_integrity",
    "vertical_pack_integrity",
    "unknown",
}

DRIFT_OPERATIONS = {
    "classify_drift_candidate",
    "compare_supplied_baseline_metadata",
    "compare_supplied_current_metadata",
    "propose_integrity_finding",
    "propose_operator_attention",
    "propose_expected_change",
    "propose_external_or_unknown_change",
    "propose_future_monitoring_scope",
    "unknown",
}

DRIFT_STATUSES = {
    "no_drift_claimed",
    "drift_candidate",
    "expected_change_candidate",
    "unexpected_change_candidate",
    "external_or_unknown_change",
    "conflicting_change",
    "stale_baseline",
    "missing_baseline",
    "missing_current_state",
    "insufficient_metadata",
    "future_gated",
    "unknown",
}

INTEGRITY_STATUSES = {
    "integrity_not_claimed",
    "integrity_candidate",
    "integrity_warning_candidate",
    "integrity_blocker_candidate",
    "integrity_unknown",
    "integrity_unavailable",
    "future_gated",
    "unknown",
}

BASELINE_SOURCE_CLASSES = {
    "caller_supplied_baseline",
    "maintenance_projection_baseline",
    "passive_observe_baseline",
    "audit_query_projection_baseline",
    "action_attribution_projection_baseline",
    "config_metadata_baseline",
    "repo_audit_readiness_baseline",
    "future_file_hash_baseline",
    "future_process_snapshot_baseline",
    "unknown",
}

CURRENT_SOURCE_CLASSES = {
    "caller_supplied_current_metadata",
    "maintenance_projection_current",
    "passive_observe_current",
    "audit_query_projection_current",
    "action_attribution_projection_current",
    "config_metadata_current",
    "repo_audit_readiness_current",
    "future_file_hash_current",
    "future_process_snapshot_current",
    "unknown",
}

ATTRIBUTION_RELATIONSHIPS = {
    "not_attributed",
    "aegis_attributed_candidate",
    "external_candidate",
    "unknown_external",
    "temporal_correlation_only",
    "conflicting_attribution",
    "attribution_unavailable",
    "unknown",
}

SEVERITY_CLASSES = {"info", "low", "medium", "high", "critical", "unknown"}

COMPLETENESS_CLASSES = {
    "complete_for_supplied_metadata",
    "bounded_metadata_only",
    "partial",
    "stale",
    "conflicting",
    "unavailable",
    "unknown",
}

FUTURE_GATED_DRIFT_SUBJECTS = {
    "file_hash_drift_future",
    "process_presence_drift",
    "external_unknown_drift",
}

FUTURE_GATED_INTEGRITY_SUBJECTS = {
    "journal_boundary_integrity_future",
    "evidence_ref_integrity_future",
    "repo_source_integrity_future",
}

FUTURE_GATED_SOURCE_CLASSES = {
    "future_file_hash_baseline",
    "future_process_snapshot_baseline",
    "future_file_hash_current",
    "future_process_snapshot_current",
}

FORBIDDEN_TRUTHY_FIELDS = {
    "authority": "authority_must_be_false",
    "runtime_dispatch_allowed": "runtime_dispatch_not_allowed",
    "approval_grant": "approval_grant_not_allowed",
    "capability_grant": "capability_grant_not_allowed",
    "lease_grant": "lease_grant_not_allowed",
    "evidence_provided_by_drift_monitor": "drift_monitor_cannot_provide_evidence",
    "evidence_created": "drift_monitor_cannot_provide_evidence",
    "verifier_success": "drift_monitor_cannot_mark_verifier_success",
    "verified_success": "drift_monitor_cannot_mark_verifier_success",
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
    "live_monitoring_started": "live_monitoring_denied",
    "file_watch_started": "file_watch_denied",
    "process_watch_started": "process_watch_denied",
    "file_scan_performed": "file_scan_denied",
    "process_scan_performed": "process_scan_denied",
    "file_read_performed": "file_read_denied",
    "hash_computation_performed": "hash_computation_denied",
    "raw_journal_read": "raw_journal_read_denied",
    "raw_evidence_read": "raw_evidence_read_denied",
    "database_queried": "database_query_denied",
    "model_call_performed": "model_call_denied",
    "tool_call_performed": "tool_call_denied",
    "mcp_call_performed": "mcp_call_denied",
    "web_query_performed": "web_query_denied",
    "memory_retrieval_performed": "memory_retrieval_denied",
    "context_retrieval_performed": "context_retrieval_denied",
    "drift_record_created": "drift_record_creation_denied",
    "integrity_record_created": "integrity_record_creation_denied",
    "report_generated": "report_generation_denied",
    "runtime_state_mutated": "runtime_state_mutation_denied",
    "journal_mutated": "journal_mutation_denied",
    "evidence_mutated": "evidence_mutation_denied",
    "replay_mutated": "replay_mutation_denied",
    "generated_artifact_created": "generated_artifact_creation_denied",
    "data_sent_external": "external_data_transfer_denied",
}


@dataclass(frozen=True)
class SystemDriftIntegrityFailure:
    reason: str
    field: str
    message: str


@dataclass(frozen=True)
class RelatedDriftIntegrityReference:
    label: str
    observed_status: str | None
    reference_only: bool = True
    authority: bool = False
    future_gated: bool = False
    implementation_claim: bool = False


@dataclass(frozen=True)
class SystemDriftIntegrityInput:
    request_id: str | None
    drift_subject: str | None
    integrity_subject: str | None
    drift_operation: str | None
    namespace: str | None
    baseline_source_class: str | None
    current_source_class: str | None
    drift_status: str | None
    integrity_status: str | None
    attribution_relationship: str | None
    severity_class: str | None
    completeness_class: str | None
    source_refs: tuple[Mapping[str, Any], ...]
    provenance: tuple[Mapping[str, Any], ...]
    limitations: tuple[str, ...]
    unknowns: tuple[str, ...]
    human_review_required: bool
    current_blocker: bool
    historical_debt: bool
    resource_debt: bool
    full_drift_analysis_claimed: bool
    drift_proof_claimed: bool
    integrity_proof_claimed: bool
    causality_claim_final: bool


@dataclass(frozen=True)
class SystemDriftIntegrityDecision:
    contract_version: str
    readiness_status: str
    request_id: str | None
    drift_subject: str | None
    integrity_subject: str | None
    drift_operation: str | None
    namespace: str | None
    baseline_source_class: str | None
    current_source_class: str | None
    drift_status: str | None
    integrity_status: str | None
    attribution_relationship: str | None
    severity_class: str | None
    completeness_class: str | None
    drift_truth_status: str
    integrity_truth_status: str
    expected_change_preserved: bool
    unexpected_change_preserved: bool
    external_unknown_preserved: bool
    conflicting_change_preserved: bool
    stale_baseline_preserved: bool
    missing_baseline_preserved: bool
    missing_current_state_preserved: bool
    insufficient_metadata_preserved: bool
    current_blocker_preserved: bool
    historical_debt_preserved: bool
    resource_debt_preserved: bool
    bounded_metadata_preserved: bool
    future_gated_preserved: bool
    human_review_required: bool
    related_references: tuple[RelatedDriftIntegrityReference, ...]
    failure_reasons: tuple[str, ...]
    failures: tuple[SystemDriftIntegrityFailure, ...]
    drift_input: SystemDriftIntegrityInput | None
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = SYSTEM_DRIFT_INTEGRITY_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_drift_monitor: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    frontend_authority: bool = False
    live_monitoring_started: bool = False
    file_watch_started: bool = False
    process_watch_started: bool = False
    file_scan_performed: bool = False
    process_scan_performed: bool = False
    file_read_performed: bool = False
    hash_computation_performed: bool = False
    raw_journal_read: bool = False
    raw_evidence_read: bool = False
    database_queried: bool = False
    model_call_performed: bool = False
    tool_call_performed: bool = False
    mcp_call_performed: bool = False
    web_query_performed: bool = False
    memory_retrieval_performed: bool = False
    context_retrieval_performed: bool = False
    drift_record_created: bool = False
    integrity_record_created: bool = False
    report_generated: bool = False
    runtime_state_mutated: bool = False
    journal_mutated: bool = False
    evidence_mutated: bool = False
    replay_mutated: bool = False
    generated_artifact_created: bool = False
    data_sent_external: bool = False
    drift_proof_claimed: bool = False
    integrity_proof_claimed: bool = False
    causality_claim_final: bool = False
    requires_backend_validation: bool = True
    read_only_projection: bool = True


def validate_system_drift_integrity_request(
    request: Mapping[str, Any] | None,
    *,
    action_attribution_decision: Any | None = None,
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
) -> SystemDriftIntegrityDecision:
    """Validate supplied drift/integrity metadata without monitoring or reading live state."""

    if not isinstance(request, Mapping):
        failure = SystemDriftIntegrityFailure(
            reason="missing_request",
            field="request",
            message="system drift integrity readiness requires caller-supplied metadata",
        )
        return _decision(drift_input=None, related_references=(), failures=(failure,))

    data = deepcopy(dict(request))
    failures: list[SystemDriftIntegrityFailure] = []
    related_references: list[RelatedDriftIntegrityReference] = []

    _validate_forbidden_claims("request", data, failures)
    _validate_final_claims("request", data, failures)

    for label, decision in {
        "action_attribution": action_attribution_decision,
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

    drift_input = SystemDriftIntegrityInput(
        request_id=_text(data.get("request_id")),
        drift_subject=_text(data.get("drift_subject")),
        integrity_subject=_text(data.get("integrity_subject")),
        drift_operation=_text(data.get("drift_operation")),
        namespace=_text(data.get("namespace")),
        baseline_source_class=_text(data.get("baseline_source_class")),
        current_source_class=_text(data.get("current_source_class")),
        drift_status=_text(data.get("drift_status")),
        integrity_status=_text(data.get("integrity_status")),
        attribution_relationship=_text(data.get("attribution_relationship")),
        severity_class=_text(data.get("severity_class")),
        completeness_class=_text(data.get("completeness_class")),
        source_refs=_mapping_tuple(data.get("source_refs")),
        provenance=_mapping_tuple(data.get("provenance")),
        limitations=_text_tuple(data.get("limitations")),
        unknowns=_text_tuple(data.get("unknowns")),
        human_review_required=_truthy(data.get("human_review_required")),
        current_blocker=_truthy(data.get("current_blocker")),
        historical_debt=_truthy(data.get("historical_debt")),
        resource_debt=_truthy(data.get("resource_debt")),
        full_drift_analysis_claimed=_truthy(data.get("full_drift_analysis_claimed")),
        drift_proof_claimed=_truthy(data.get("drift_proof_claimed")),
        integrity_proof_claimed=_truthy(data.get("integrity_proof_claimed")),
        causality_claim_final=_truthy(data.get("causality_claim_final")),
    )

    _validate_required(drift_input, failures)
    _validate_truthfulness(drift_input, failures)

    return _decision(
        drift_input=drift_input,
        related_references=tuple(related_references),
        failures=tuple(failures),
    )


def _decision(
    *,
    drift_input: SystemDriftIntegrityInput | None,
    related_references: tuple[RelatedDriftIntegrityReference, ...],
    failures: tuple[SystemDriftIntegrityFailure, ...],
) -> SystemDriftIntegrityDecision:
    future_gated = bool(drift_input and _is_future_gated(drift_input))
    return SystemDriftIntegrityDecision(
        contract_version=SYSTEM_DRIFT_INTEGRITY_VERSION,
        readiness_status=_readiness_status(drift_input, list(failures), future_gated),
        request_id=drift_input.request_id if drift_input else None,
        drift_subject=drift_input.drift_subject if drift_input else None,
        integrity_subject=drift_input.integrity_subject if drift_input else None,
        drift_operation=drift_input.drift_operation if drift_input else None,
        namespace=drift_input.namespace if drift_input else None,
        baseline_source_class=drift_input.baseline_source_class if drift_input else None,
        current_source_class=drift_input.current_source_class if drift_input else None,
        drift_status=drift_input.drift_status if drift_input else None,
        integrity_status=drift_input.integrity_status if drift_input else None,
        attribution_relationship=drift_input.attribution_relationship if drift_input else None,
        severity_class=drift_input.severity_class if drift_input else None,
        completeness_class=drift_input.completeness_class if drift_input else None,
        drift_truth_status=_drift_truth_status(drift_input, list(failures)),
        integrity_truth_status=_integrity_truth_status(drift_input, list(failures)),
        expected_change_preserved=bool(drift_input and drift_input.drift_status == "expected_change_candidate"),
        unexpected_change_preserved=bool(drift_input and drift_input.drift_status == "unexpected_change_candidate"),
        external_unknown_preserved=bool(
            drift_input
            and (
                drift_input.drift_status == "external_or_unknown_change"
                or drift_input.attribution_relationship in {"external_candidate", "unknown_external"}
            )
        ),
        conflicting_change_preserved=bool(
            drift_input
            and (
                drift_input.drift_status == "conflicting_change"
                or drift_input.attribution_relationship == "conflicting_attribution"
                or drift_input.completeness_class == "conflicting"
            )
        ),
        stale_baseline_preserved=bool(
            drift_input and (drift_input.drift_status == "stale_baseline" or drift_input.completeness_class == "stale")
        ),
        missing_baseline_preserved=bool(drift_input and drift_input.drift_status == "missing_baseline"),
        missing_current_state_preserved=bool(drift_input and drift_input.drift_status == "missing_current_state"),
        insufficient_metadata_preserved=bool(drift_input and drift_input.drift_status == "insufficient_metadata"),
        current_blocker_preserved=bool(drift_input and drift_input.current_blocker),
        historical_debt_preserved=bool(drift_input and drift_input.historical_debt),
        resource_debt_preserved=bool(drift_input and drift_input.resource_debt),
        bounded_metadata_preserved=bool(
            drift_input and drift_input.completeness_class != "complete_for_supplied_metadata"
        ),
        future_gated_preserved=future_gated,
        human_review_required=_human_review_required(drift_input, list(failures), future_gated),
        related_references=related_references,
        failure_reasons=tuple(failure.reason for failure in failures),
        failures=failures,
        drift_input=drift_input,
    )


def _validate_required(
    drift_input: SystemDriftIntegrityInput,
    failures: list[SystemDriftIntegrityFailure],
) -> None:
    for field in (
        "request_id",
        "drift_operation",
        "namespace",
        "baseline_source_class",
        "current_source_class",
        "drift_status",
        "integrity_status",
        "attribution_relationship",
        "severity_class",
        "completeness_class",
    ):
        if not getattr(drift_input, field):
            _add_failure(failures, f"missing_{field}", field, f"drift integrity request is missing {field}")
    if not (drift_input.drift_subject or drift_input.integrity_subject):
        _add_failure(failures, "missing_subject", "drift_subject", "drift or integrity subject is required")
    if drift_input.drift_subject and drift_input.drift_subject not in DRIFT_SUBJECTS:
        _add_failure(failures, "unsupported_drift_subject", "drift_subject", "drift subject is not recognized")
    if drift_input.integrity_subject and drift_input.integrity_subject not in INTEGRITY_SUBJECTS:
        _add_failure(failures, "unsupported_integrity_subject", "integrity_subject", "integrity subject is not recognized")
    if drift_input.drift_operation and drift_input.drift_operation not in DRIFT_OPERATIONS:
        _add_failure(failures, "unsupported_drift_operation", "drift_operation", "drift operation is not recognized")
    if drift_input.baseline_source_class and drift_input.baseline_source_class not in BASELINE_SOURCE_CLASSES:
        _add_failure(failures, "unsupported_baseline_source_class", "baseline_source_class", "baseline source class is not recognized")
    if drift_input.current_source_class and drift_input.current_source_class not in CURRENT_SOURCE_CLASSES:
        _add_failure(failures, "unsupported_current_source_class", "current_source_class", "current source class is not recognized")
    if drift_input.drift_status and drift_input.drift_status not in DRIFT_STATUSES:
        _add_failure(failures, "unsupported_drift_status", "drift_status", "drift status is not recognized")
    if drift_input.integrity_status and drift_input.integrity_status not in INTEGRITY_STATUSES:
        _add_failure(failures, "unsupported_integrity_status", "integrity_status", "integrity status is not recognized")
    if drift_input.attribution_relationship and drift_input.attribution_relationship not in ATTRIBUTION_RELATIONSHIPS:
        _add_failure(failures, "unsupported_attribution_relationship", "attribution_relationship", "attribution relationship is not recognized")
    if drift_input.severity_class and drift_input.severity_class not in SEVERITY_CLASSES:
        _add_failure(failures, "unsupported_severity_class", "severity_class", "severity class is not recognized")
    if drift_input.completeness_class and drift_input.completeness_class not in COMPLETENESS_CLASSES:
        _add_failure(failures, "unsupported_completeness_class", "completeness_class", "completeness class is not recognized")
    if not (drift_input.source_refs or drift_input.provenance):
        _add_failure(
            failures,
            "missing_source_refs_or_provenance",
            "source_refs",
            "drift and integrity candidates require source refs or provenance",
        )


def _validate_truthfulness(
    drift_input: SystemDriftIntegrityInput,
    failures: list[SystemDriftIntegrityFailure],
) -> None:
    if drift_input.full_drift_analysis_claimed and drift_input.completeness_class != "complete_for_supplied_metadata":
        _add_failure(
            failures,
            "full_drift_analysis_requires_complete_supplied_metadata",
            "full_drift_analysis_claimed",
            "full drift analysis cannot be claimed for bounded, partial, stale, conflicting, unavailable, or unknown metadata",
        )
    if drift_input.drift_proof_claimed:
        _add_failure(failures, "drift_proof_claim_denied", "drift_proof_claimed", "drift readiness cannot claim proof")
    if drift_input.integrity_proof_claimed:
        _add_failure(
            failures,
            "integrity_proof_claim_denied",
            "integrity_proof_claimed",
            "integrity readiness cannot claim proof",
        )
    if drift_input.causality_claim_final:
        _add_failure(
            failures,
            "final_causality_claim_denied",
            "causality_claim_final",
            "drift readiness cannot claim final causality",
        )
    if drift_input.drift_status == "expected_change_candidate" and drift_input.integrity_status in {
        "integrity_candidate",
        "integrity_warning_candidate",
        "integrity_blocker_candidate",
    }:
        _add_failure(
            failures,
            "expected_change_cannot_claim_integrity_success",
            "integrity_status",
            "expected change candidates cannot become integrity success",
        )
    if drift_input.drift_status == "unexpected_change_candidate" and drift_input.integrity_status == "integrity_candidate":
        _add_failure(
            failures,
            "unexpected_change_cannot_claim_integrity_success",
            "integrity_status",
            "unexpected change candidates cannot become integrity proof",
        )
    if drift_input.attribution_relationship == "temporal_correlation_only" and drift_input.drift_status == "expected_change_candidate":
        _add_failure(
            failures,
            "temporal_correlation_cannot_be_expected_change",
            "attribution_relationship",
            "temporal correlation cannot become expected attributed drift",
        )


def _validate_related_decision(
    label: str,
    decision: Any | None,
    failures: list[SystemDriftIntegrityFailure],
    related_references: list[RelatedDriftIntegrityReference],
) -> None:
    if decision is None:
        return
    before = len(failures)
    _validate_forbidden_claims(label, decision, failures)
    _validate_final_claims(label, decision, failures)
    if len(failures) > before:
        _add_failure(
            failures,
            "unsafe_related_decision",
            label,
            f"{label} cannot grant drift/integrity authority, dispatch, grants, evidence, verifier success, execution, mutation, proof, or reports",
        )
    related_references.append(
        RelatedDriftIntegrityReference(
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
    failures: list[SystemDriftIntegrityFailure],
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
                f"{label} cannot perform monitoring, watchers, scans, reads, hashes, calls, retrieval, records, reports, mutations, or external transfer",
            )
    execution_permission = _field_value(source, "execution_permission")
    if execution_permission not in (None, "", SYSTEM_DRIFT_INTEGRITY_EXECUTION_PERMISSION):
        permission_text = str(execution_permission)
        if not permission_text.startswith("not_granted"):
            _add_failure(
                failures,
                "execution_permission_claim_denied",
                f"{label}.execution_permission",
                "system drift integrity metadata cannot grant execution permission",
            )


def _validate_final_claims(
    label: str,
    source: Any,
    failures: list[SystemDriftIntegrityFailure],
) -> None:
    for field, reason in {
        "drift_proof_claimed": "drift_proof_claim_denied",
        "integrity_proof_claimed": "integrity_proof_claim_denied",
        "causality_claim_final": "final_causality_claim_denied",
    }.items():
        if _field_bool(source, field):
            _add_failure(
                failures,
                reason,
                f"{label}.{field}",
                "drift/integrity readiness cannot claim proof or final causality",
            )


def _readiness_status(
    drift_input: SystemDriftIntegrityInput | None,
    failures: list[SystemDriftIntegrityFailure],
    future_gated: bool,
) -> str:
    if drift_input is None:
        return "blocked_by_missing_required_field"
    reasons = {failure.reason for failure in failures}
    if reasons:
        if "unsafe_related_decision" in reasons:
            return "blocked_by_unsafe_related_decision"
        if any(reason.startswith("missing_") or reason.startswith("unsupported_") for reason in reasons):
            return "blocked_by_missing_required_field"
        if any("authority" in reason or "grant" in reason or "permission" in reason for reason in reasons):
            return "blocked_by_authority_claim"
        if any(
            "proof" in reason
            or "causality" in reason
            or "expected_change" in reason
            or "unexpected_change" in reason
            or "full_drift_analysis" in reason
            for reason in reasons
        ):
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
        if any("evidence" in reason or "verifier" in reason or "certification" in reason for reason in reasons):
            return "blocked_by_evidence_claim"
        return "blocked_by_policy"
    if future_gated or drift_input.drift_status == "future_gated" or drift_input.integrity_status == "future_gated":
        return "future_gated"
    if drift_input.drift_status in {"missing_baseline", "missing_current_state", "insufficient_metadata", "unknown"}:
        return "drift_metadata_incomplete"
    if drift_input.drift_status in {"conflicting_change", "stale_baseline"} or drift_input.completeness_class in {"stale", "conflicting"}:
        return "requires_human_review"
    return "drift_integrity_candidate_ready"


def _drift_truth_status(
    drift_input: SystemDriftIntegrityInput | None,
    failures: list[SystemDriftIntegrityFailure],
) -> str:
    if drift_input is None or failures:
        return "blocked"
    if drift_input.drift_status in {"missing_baseline", "missing_current_state", "insufficient_metadata"}:
        return drift_input.drift_status
    if drift_input.drift_status == "external_or_unknown_change":
        return "external_or_unknown"
    if drift_input.drift_status == "conflicting_change":
        return "conflicting"
    if drift_input.drift_status == "stale_baseline":
        return "stale_baseline"
    if drift_input.drift_status == "no_drift_claimed":
        return "no_drift_claimed"
    return "candidate_only"


def _integrity_truth_status(
    drift_input: SystemDriftIntegrityInput | None,
    failures: list[SystemDriftIntegrityFailure],
) -> str:
    if drift_input is None or failures:
        return "blocked"
    if drift_input.integrity_status in {"integrity_unknown", "integrity_unavailable", "unknown"}:
        return drift_input.integrity_status
    if drift_input.integrity_status == "integrity_not_claimed":
        return "integrity_not_claimed"
    return "candidate_only"


def _human_review_required(
    drift_input: SystemDriftIntegrityInput | None,
    failures: list[SystemDriftIntegrityFailure],
    future_gated: bool,
) -> bool:
    if drift_input is None:
        return True
    if failures or future_gated or drift_input.human_review_required:
        return True
    return (
        drift_input.drift_status
        in {"unexpected_change_candidate", "external_or_unknown_change", "conflicting_change", "stale_baseline", "missing_baseline", "missing_current_state", "insufficient_metadata", "unknown"}
        or drift_input.integrity_status in {"integrity_warning_candidate", "integrity_blocker_candidate", "integrity_unknown", "integrity_unavailable", "unknown"}
        or drift_input.attribution_relationship
        in {"external_candidate", "unknown_external", "temporal_correlation_only", "conflicting_attribution", "attribution_unavailable", "unknown"}
        or drift_input.severity_class in {"high", "critical", "unknown"}
        or drift_input.completeness_class in {"partial", "stale", "conflicting", "unavailable", "unknown"}
    )


def _is_future_gated(drift_input: SystemDriftIntegrityInput) -> bool:
    return (
        drift_input.drift_subject in FUTURE_GATED_DRIFT_SUBJECTS
        or drift_input.integrity_subject in FUTURE_GATED_INTEGRITY_SUBJECTS
        or drift_input.drift_operation == "propose_future_monitoring_scope"
        or drift_input.baseline_source_class in FUTURE_GATED_SOURCE_CLASSES
        or drift_input.current_source_class in FUTURE_GATED_SOURCE_CLASSES
    )


def _related_status(decision: Any) -> str | None:
    for field in (
        "readiness_status",
        "attribution_status",
        "query_status",
        "display_state",
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
    failures: list[SystemDriftIntegrityFailure],
    reason: str,
    field: str,
    message: str,
) -> None:
    failures.append(SystemDriftIntegrityFailure(reason=reason, field=field, message=message))
