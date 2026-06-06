from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping


LOCAL_PROVIDER_PROBE_PROJECTION_VERSION = "local-provider-probe-projection/1"
LOCAL_PROVIDER_PROBE_PROJECTION_EXECUTION_PERMISSION = (
    "not_granted_by_local_provider_probe_projection"
)

PROJECTION_SOURCE_CLASSES = {
    "manual_smoke_result",
    "mock_runner_result",
    "future_live_runner_result",
    "provider_probe_runner_result",
    "maintenance_scan_projection_future",
    "mission_control_projection_future",
    "caller_supplied_metadata",
    "unknown",
}

PROBE_RESULT_CLASSES = {
    "metadata_success_candidate",
    "model_list_success_candidate",
    "health_metadata_success_candidate",
    "unreachable_negative_candidate",
    "timeout_negative_candidate",
    "connection_refused_negative_candidate",
    "invalid_response_negative_candidate",
    "unauthorized_negative_candidate",
    "unsupported_endpoint_negative_candidate",
    "cancelled_negative_candidate",
    "empty_model_list_candidate",
    "not_observed",
    "not_executed",
    "unknown",
}

NEGATIVE_RESULT_CLASSES = {
    "unreachable_negative_candidate",
    "timeout_negative_candidate",
    "connection_refused_negative_candidate",
    "invalid_response_negative_candidate",
    "unauthorized_negative_candidate",
    "unsupported_endpoint_negative_candidate",
    "cancelled_negative_candidate",
}

SUCCESS_CANDIDATE_RESULTS = {
    "metadata_success_candidate",
    "model_list_success_candidate",
    "health_metadata_success_candidate",
}

MAINTENANCE_SURFACE_STATUS_CLASSES = {
    "provider_probe_not_configured",
    "provider_probe_candidate_ok",
    "provider_probe_negative_candidate",
    "provider_probe_unreachable_candidate",
    "provider_probe_timeout_candidate",
    "provider_probe_invalid_response_candidate",
    "provider_probe_blocked_by_policy",
    "provider_probe_future_gated",
    "provider_probe_unknown",
    "unknown",
}

TRUTH_LABEL_CLASSES = {
    "metadata_candidate_only",
    "negative_candidate_only",
    "not_runtime_failure",
    "not_provider_health_proof",
    "not_model_availability_proof",
    "not_verifier_success",
    "operator_review_recommended",
    "retry_requires_operator_approval",
    "unknown",
}

DISPLAY_SEVERITY_CLASSES = {"info", "low", "medium", "warning", "high", "critical", "unknown"}

FRESHNESS_CLASSES = {
    "current_manual_smoke",
    "recent_candidate",
    "stale_candidate",
    "historical_candidate",
    "unknown_freshness",
}

EXPECTED_STATUS_BY_RESULT = {
    "metadata_success_candidate": {"provider_probe_candidate_ok"},
    "model_list_success_candidate": {"provider_probe_candidate_ok"},
    "health_metadata_success_candidate": {"provider_probe_candidate_ok"},
    "empty_model_list_candidate": {"provider_probe_candidate_ok", "provider_probe_negative_candidate"},
    "unreachable_negative_candidate": {"provider_probe_unreachable_candidate", "provider_probe_negative_candidate"},
    "timeout_negative_candidate": {"provider_probe_timeout_candidate", "provider_probe_negative_candidate"},
    "connection_refused_negative_candidate": {
        "provider_probe_unreachable_candidate",
        "provider_probe_negative_candidate",
    },
    "invalid_response_negative_candidate": {
        "provider_probe_invalid_response_candidate",
        "provider_probe_negative_candidate",
    },
    "unauthorized_negative_candidate": {
        "provider_probe_blocked_by_policy",
        "provider_probe_negative_candidate",
    },
    "unsupported_endpoint_negative_candidate": {
        "provider_probe_blocked_by_policy",
        "provider_probe_negative_candidate",
    },
    "cancelled_negative_candidate": {"provider_probe_negative_candidate"},
    "not_observed": {"provider_probe_not_configured", "provider_probe_unknown"},
    "not_executed": {"provider_probe_not_configured", "provider_probe_future_gated"},
    "unknown": {"provider_probe_unknown", "unknown"},
}

RETRY_RECOMMENDED_RESULTS = {
    "unreachable_negative_candidate",
    "timeout_negative_candidate",
    "connection_refused_negative_candidate",
    "invalid_response_negative_candidate",
}

FORBIDDEN_TRUTHY_FIELDS = {
    "authority": "authority_must_be_false",
    "runtime_dispatch_allowed": "runtime_dispatch_not_allowed",
    "approval_grant": "approval_grant_not_allowed",
    "capability_grant": "capability_grant_not_allowed",
    "lease_grant": "lease_grant_not_allowed",
    "evidence_provided_by_probe_projection": "probe_projection_cannot_provide_evidence",
    "evidence_provided_by_probe_runner": "probe_projection_cannot_provide_evidence",
    "evidence_provided_by_live_gate": "probe_projection_cannot_provide_evidence",
    "evidence_provided_by_mock_probe": "probe_projection_cannot_provide_evidence",
    "evidence_created": "probe_projection_cannot_provide_evidence",
    "verifier_success": "probe_projection_cannot_mark_verifier_success",
    "verified_success": "probe_projection_cannot_mark_verifier_success",
    "mutation_performed": "mutation_performed_denied",
    "frontend_authority": "frontend_authority_not_allowed",
    "maintenance_health_mutated": "maintenance_health_mutation_denied",
    "runtime_health_mutated": "runtime_health_mutation_denied",
    "provider_health_verified": "provider_health_verification_denied",
    "health_verified": "provider_health_verification_denied",
    "model_availability_verified": "model_availability_verification_denied",
    "model_identity_verified": "model_identity_verification_denied",
    "benchmark_claim_verified": "benchmark_verification_denied",
    "auto_mode_selection_performed": "auto_mode_selection_denied",
    "provider_selected_for_execution": "provider_execution_selection_denied",
    "model_selected_for_execution": "model_execution_selection_denied",
    "auto_mode_execution_allowed": "auto_mode_execution_denied",
    "metadata_success_is_health_proof": "metadata_success_health_proof_denied",
    "model_list_is_availability_proof": "model_list_availability_proof_denied",
    "negative_result_is_runtime_failure": "negative_runtime_failure_claim_denied",
    "empty_model_list_is_runtime_failure": "empty_model_list_runtime_failure_claim_denied",
    "downloaded_models_are_availability_proof": "downloaded_models_availability_proof_denied",
    "provider_metadata_is_truth": "provider_metadata_truth_claim_denied",
    "model_list_is_truth": "model_list_truth_claim_denied",
    "self_reported_identity_is_authority": "self_reported_identity_authority_denied",
    "quality_or_benchmark_verified": "benchmark_verification_denied",
    "model_inventory_proves_availability": "model_inventory_availability_proof_denied",
    "success": "success_claim_denied",
    "proof": "proof_claim_denied",
    "certification_claim": "certification_claim_denied",
}

FORBIDDEN_BEHAVIOR_FIELDS = {
    "live_probe_performed": "live_probe_execution_denied",
    "real_endpoint_probed": "real_endpoint_probe_denied",
    "provider_probed": "provider_probe_execution_denied",
    "endpoint_probed": "endpoint_probe_execution_denied",
    "probe_executed": "probe_execution_denied",
    "socket_opened": "socket_open_denied",
    "http_request_performed": "http_request_denied",
    "api_route_added": "api_route_addition_denied",
    "runtime_command_added": "runtime_command_addition_denied",
    "scheduler_added": "scheduler_addition_denied",
    "model_loaded": "model_load_denied",
    "model_call_performed": "model_call_denied",
    "generation_performed": "generation_denied",
    "minimal_generation_performed": "generation_denied",
    "embedding_generated": "embedding_generation_denied",
    "reranking_performed": "reranking_denied",
    "multimodal_inference_performed": "multimodal_inference_denied",
    "multimodal_probe_performed": "multimodal_inference_denied",
    "prompt_payload_sent": "prompt_payload_denied",
    "context_payload_sent": "context_payload_denied",
    "memory_payload_sent": "memory_payload_denied",
    "repo_payload_sent": "repo_payload_denied",
    "raw_journal_payload_sent": "raw_journal_payload_denied",
    "raw_evidence_payload_sent": "raw_evidence_payload_denied",
    "journal_payload_sent": "raw_journal_payload_denied",
    "evidence_payload_sent": "raw_evidence_payload_denied",
    "api_key_validated": "api_key_validation_denied",
    "secret_read": "secret_read_denied",
    "authorization_header_sent": "authorization_header_denied",
    "response_body_logged": "response_body_logging_denied",
    "secret_logged": "secret_logging_denied",
    "cloud_provider_called": "cloud_provider_call_denied",
    "lan_or_remote_endpoint_called": "lan_or_remote_endpoint_call_denied",
    "data_sent_external": "external_data_transfer_denied",
    "runtime_state_mutated": "runtime_state_mutation_denied",
    "journal_mutated": "journal_mutation_denied",
    "evidence_mutated": "evidence_mutation_denied",
    "replay_mutated": "replay_mutation_denied",
    "api_call_performed": "api_call_denied",
    "mcp_call_performed": "mcp_call_denied",
    "tool_call_performed": "tool_call_denied",
    "memory_retrieval_performed": "memory_retrieval_denied",
    "context_retrieval_performed": "context_retrieval_denied",
    "repo_file_read_performed": "repo_file_read_denied",
    "web_query_performed": "web_query_denied",
}


@dataclass(frozen=True)
class LocalProviderProbeProjectionFailure:
    reason: str
    field: str
    message: str


@dataclass(frozen=True)
class LocalProviderProbeProjectionInput:
    request_id: str | None
    projection_source_class: str | None
    probe_result_class: str | None
    maintenance_surface_status_class: str | None
    truth_label_class: str | None
    display_severity_class: str | None
    freshness_class: str | None
    namespace: str | None
    source_refs: tuple[Mapping[str, Any], ...]
    provenance: tuple[Mapping[str, Any], ...]
    limitations: tuple[str, ...]
    unknowns: tuple[str, ...]
    model_count_candidate: int | None
    response_status_code: int | None
    response_shape_classification: str | None


@dataclass(frozen=True)
class RelatedLocalProviderProbeProjectionReference:
    label: str
    observed_status: str | None
    reference_only: bool = True
    authority: bool = False
    implementation_claim: bool = False


@dataclass(frozen=True)
class LocalProviderProbeProjectionDecision:
    contract_version: str
    projection_status: str
    request_id: str | None
    projection_source_class: str | None
    probe_result_class: str | None
    maintenance_surface_status_class: str | None
    truth_label_class: str | None
    display_severity_class: str | None
    freshness_class: str | None
    namespace: str | None
    display_status_candidate: str
    result_semantics: str
    retry_semantics: str
    truthfulness_classification: str
    related_references: tuple[RelatedLocalProviderProbeProjectionReference, ...]
    required_operator_actions: tuple[str, ...]
    failure_reasons: tuple[str, ...]
    failures: tuple[LocalProviderProbeProjectionFailure, ...]
    projection_input: LocalProviderProbeProjectionInput | None
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = LOCAL_PROVIDER_PROBE_PROJECTION_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_probe_projection: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    frontend_authority: bool = False
    maintenance_health_mutated: bool = False
    runtime_health_mutated: bool = False
    provider_health_verified: bool = False
    model_availability_verified: bool = False
    model_identity_verified: bool = False
    benchmark_claim_verified: bool = False
    auto_mode_selection_performed: bool = False
    model_loaded: bool = False
    model_call_performed: bool = False
    generation_performed: bool = False
    embedding_generated: bool = False
    reranking_performed: bool = False
    multimodal_inference_performed: bool = False
    live_probe_performed: bool = False
    real_endpoint_probed: bool = False
    socket_opened: bool = False
    http_request_performed: bool = False
    api_route_added: bool = False
    runtime_command_added: bool = False
    scheduler_added: bool = False
    prompt_payload_sent: bool = False
    context_payload_sent: bool = False
    memory_payload_sent: bool = False
    repo_payload_sent: bool = False
    raw_journal_payload_sent: bool = False
    raw_evidence_payload_sent: bool = False
    api_key_validated: bool = False
    secret_read: bool = False
    authorization_header_sent: bool = False
    response_body_logged: bool = False
    secret_logged: bool = False
    cloud_provider_called: bool = False
    lan_or_remote_endpoint_called: bool = False
    data_sent_external: bool = False
    runtime_state_mutated: bool = False
    journal_mutated: bool = False
    evidence_mutated: bool = False
    replay_mutated: bool = False
    requires_backend_validation: bool = True
    requires_policy_check: bool = True
    read_only_projection: bool = True


def validate_local_provider_probe_projection_request(
    request: Mapping[str, Any] | None,
    *,
    local_provider_probe_runner_decision: Any | None = None,
    local_provider_probe_live_gate_decision: Any | None = None,
    local_provider_probe_mock_runner_decision: Any | None = None,
    local_provider_probe_wiring_decision: Any | None = None,
    local_provider_probe_boundary_decision: Any | None = None,
    local_provider_probe_design_decision: Any | None = None,
    local_provider_health_decision: Any | None = None,
    local_model_context_profile_decision: Any | None = None,
    model_auto_mode_decision: Any | None = None,
    local_model_inventory_decision: Any | None = None,
    context_policy_decision: Any | None = None,
    identity_scope_decision: Any | None = None,
    memory_governance_decision: Any | None = None,
    policy_extension_decision: Any | None = None,
    capability_lease_decision: Any | None = None,
    audit_query_layer_decision: Any | None = None,
    action_attribution_decision: Any | None = None,
    system_drift_integrity_decision: Any | None = None,
    passive_observe_decision: Any | None = None,
    mission_control_decision: Any | None = None,
    tool_simulation_decision: Any | None = None,
) -> LocalProviderProbeProjectionDecision:
    """Project local provider probe result metadata without probing or mutating health."""

    if not isinstance(request, Mapping):
        failure = LocalProviderProbeProjectionFailure(
            reason="missing_request",
            field="request",
            message="local provider probe projection requires caller-supplied metadata",
        )
        return _decision(projection_input=None, related_references=(), failures=(failure,))

    data = deepcopy(dict(request))
    failures: list[LocalProviderProbeProjectionFailure] = []
    related_references: list[RelatedLocalProviderProbeProjectionReference] = []

    _validate_forbidden_claims("request", data, failures)
    for label, decision in {
        "local_provider_probe_runner": local_provider_probe_runner_decision,
        "local_provider_probe_live_gate": local_provider_probe_live_gate_decision,
        "local_provider_probe_mock_runner": local_provider_probe_mock_runner_decision,
        "local_provider_probe_wiring": local_provider_probe_wiring_decision,
        "local_provider_probe_boundary": local_provider_probe_boundary_decision,
        "local_provider_probe_design": local_provider_probe_design_decision,
        "local_provider_health": local_provider_health_decision,
        "local_model_context_profile": local_model_context_profile_decision,
        "model_auto_mode": model_auto_mode_decision,
        "local_model_inventory": local_model_inventory_decision,
        "context_policy": context_policy_decision,
        "identity_scope": identity_scope_decision,
        "memory_governance": memory_governance_decision,
        "policy_extension": policy_extension_decision,
        "capability_lease": capability_lease_decision,
        "audit_query_layer": audit_query_layer_decision,
        "action_attribution": action_attribution_decision,
        "system_drift_integrity": system_drift_integrity_decision,
        "passive_observe": passive_observe_decision,
        "mission_control": mission_control_decision,
        "tool_simulation": tool_simulation_decision,
    }.items():
        _validate_related_decision(label, decision, failures, related_references)

    projection_input = LocalProviderProbeProjectionInput(
        request_id=_text(data.get("request_id")),
        projection_source_class=_text(data.get("projection_source_class")),
        probe_result_class=_text(data.get("probe_result_class")),
        maintenance_surface_status_class=_text(data.get("maintenance_surface_status_class")),
        truth_label_class=_text(data.get("truth_label_class")),
        display_severity_class=_text(data.get("display_severity_class")),
        freshness_class=_text(data.get("freshness_class")),
        namespace=_text(data.get("namespace")),
        source_refs=_mapping_tuple(data.get("source_refs")),
        provenance=_mapping_tuple(data.get("provenance")),
        limitations=_text_tuple(data.get("limitations")),
        unknowns=_text_tuple(data.get("unknowns")),
        model_count_candidate=_int(data.get("model_count_candidate")),
        response_status_code=_int(data.get("response_status_code")),
        response_shape_classification=_text(data.get("response_shape_classification")),
    )

    _validate_required(projection_input, failures)
    _validate_projection_semantics(projection_input, failures)
    _validate_truthfulness(data, failures)

    return _decision(
        projection_input=projection_input,
        related_references=tuple(related_references),
        failures=tuple(failures),
    )


def _decision(
    *,
    projection_input: LocalProviderProbeProjectionInput | None,
    related_references: tuple[RelatedLocalProviderProbeProjectionReference, ...],
    failures: tuple[LocalProviderProbeProjectionFailure, ...],
) -> LocalProviderProbeProjectionDecision:
    return LocalProviderProbeProjectionDecision(
        contract_version=LOCAL_PROVIDER_PROBE_PROJECTION_VERSION,
        projection_status=_projection_status(projection_input, failures),
        request_id=projection_input.request_id if projection_input else None,
        projection_source_class=projection_input.projection_source_class if projection_input else None,
        probe_result_class=projection_input.probe_result_class if projection_input else None,
        maintenance_surface_status_class=projection_input.maintenance_surface_status_class if projection_input else None,
        truth_label_class=projection_input.truth_label_class if projection_input else None,
        display_severity_class=projection_input.display_severity_class if projection_input else None,
        freshness_class=projection_input.freshness_class if projection_input else None,
        namespace=projection_input.namespace if projection_input else None,
        display_status_candidate=_display_status_candidate(projection_input, failures),
        result_semantics=_result_semantics(projection_input, failures),
        retry_semantics=_retry_semantics(projection_input, failures),
        truthfulness_classification=_truthfulness_classification(projection_input, failures),
        related_references=related_references,
        required_operator_actions=_required_operator_actions(projection_input, failures),
        failure_reasons=tuple(dict.fromkeys(f.reason for f in failures)),
        failures=failures,
        projection_input=projection_input,
    )


def _validate_required(
    projection_input: LocalProviderProbeProjectionInput,
    failures: list[LocalProviderProbeProjectionFailure],
) -> None:
    required = {
        "request_id": projection_input.request_id,
        "projection_source_class": projection_input.projection_source_class,
        "probe_result_class": projection_input.probe_result_class,
        "maintenance_surface_status_class": projection_input.maintenance_surface_status_class,
        "truth_label_class": projection_input.truth_label_class,
        "display_severity_class": projection_input.display_severity_class,
        "freshness_class": projection_input.freshness_class,
        "namespace": projection_input.namespace,
    }
    for field, value in required.items():
        if not value:
            _add_failure(failures, f"missing_{field}", field, f"{field} is required")
    if not (projection_input.source_refs or projection_input.provenance):
        _add_failure(failures, "missing_source_refs_or_provenance", "source_refs", "source refs or provenance are required")
    if projection_input.projection_source_class and projection_input.projection_source_class not in PROJECTION_SOURCE_CLASSES:
        _add_failure(failures, "unsupported_projection_source_class", "projection_source_class", "projection source class is not recognized")
    if projection_input.probe_result_class and projection_input.probe_result_class not in PROBE_RESULT_CLASSES:
        _add_failure(failures, "unsupported_probe_result_class", "probe_result_class", "probe result class is not recognized")
    if projection_input.maintenance_surface_status_class and projection_input.maintenance_surface_status_class not in MAINTENANCE_SURFACE_STATUS_CLASSES:
        _add_failure(failures, "unsupported_maintenance_surface_status_class", "maintenance_surface_status_class", "maintenance surface status class is not recognized")
    if projection_input.truth_label_class and projection_input.truth_label_class not in TRUTH_LABEL_CLASSES:
        _add_failure(failures, "unsupported_truth_label_class", "truth_label_class", "truth label class is not recognized")
    if projection_input.display_severity_class and projection_input.display_severity_class not in DISPLAY_SEVERITY_CLASSES:
        _add_failure(failures, "unsupported_display_severity_class", "display_severity_class", "display severity class is not recognized")
    if projection_input.freshness_class and projection_input.freshness_class not in FRESHNESS_CLASSES:
        _add_failure(failures, "unsupported_freshness_class", "freshness_class", "freshness class is not recognized")


def _validate_projection_semantics(
    projection_input: LocalProviderProbeProjectionInput,
    failures: list[LocalProviderProbeProjectionFailure],
) -> None:
    source = projection_input.projection_source_class
    result = projection_input.probe_result_class
    status = projection_input.maintenance_surface_status_class
    truth = projection_input.truth_label_class
    severity = projection_input.display_severity_class
    freshness = projection_input.freshness_class
    if source == "unknown":
        _add_failure(failures, "unknown_projection_source_blocked", "projection_source_class", "unknown projection source requires clarification")
    if result == "unknown":
        _add_failure(failures, "unknown_probe_result_blocked", "probe_result_class", "unknown probe result requires clarification")
    if status == "unknown":
        _add_failure(failures, "unknown_maintenance_status_blocked", "maintenance_surface_status_class", "unknown maintenance status requires clarification")
    if truth == "unknown":
        _add_failure(failures, "unknown_truth_label_blocked", "truth_label_class", "unknown truth label is blocked")
    expected_statuses = EXPECTED_STATUS_BY_RESULT.get(result or "", set())
    if expected_statuses and status not in expected_statuses:
        _add_failure(failures, "probe_result_status_mismatch", "maintenance_surface_status_class", "maintenance surface status does not preserve probe result distinction")
    if result in NEGATIVE_RESULT_CLASSES and truth not in {"negative_candidate_only", "not_runtime_failure", "operator_review_recommended", "retry_requires_operator_approval"}:
        _add_failure(failures, "negative_result_truth_label_required", "truth_label_class", "negative results must stay negative candidate or not-runtime-failure labels")
    if result in SUCCESS_CANDIDATE_RESULTS and truth not in {"metadata_candidate_only", "not_provider_health_proof", "not_model_availability_proof", "not_verifier_success"}:
        _add_failure(failures, "success_result_truth_label_required", "truth_label_class", "success candidates must stay metadata-only or non-proof labels")
    if result == "model_list_success_candidate" and truth == "not_provider_health_proof":
        _add_failure(failures, "model_list_must_not_imply_health", "truth_label_class", "model-list success should not be framed as provider health proof")
    if result == "empty_model_list_candidate" and severity in {"high", "critical"}:
        _add_failure(failures, "empty_model_list_overstated", "display_severity_class", "empty model list is metadata only and not a runtime failure")
    if result in RETRY_RECOMMENDED_RESULTS and truth != "retry_requires_operator_approval":
        _add_failure(failures, "retry_requires_operator_approval", "truth_label_class", "retryable negative result must preserve operator approval requirement")
    if freshness == "unknown_freshness" and severity not in {"info", "low", "medium", "warning", "unknown"}:
        _add_failure(failures, "unknown_freshness_severity_overstated", "display_severity_class", "unknown freshness cannot become critical projection")
    if result in {"not_observed", "not_executed"} and status not in {"provider_probe_not_configured", "provider_probe_future_gated"}:
        _add_failure(failures, "not_executed_status_mismatch", "maintenance_surface_status_class", "not observed or not executed must not be displayed as provider status")


def _validate_truthfulness(data: Mapping[str, Any], failures: list[LocalProviderProbeProjectionFailure]) -> None:
    for field, reason in {
        "unreachable_result_is_runtime_failure": "negative_runtime_failure_claim_denied",
        "timeout_result_is_runtime_failure": "negative_runtime_failure_claim_denied",
        "connection_refused_result_is_runtime_failure": "negative_runtime_failure_claim_denied",
        "empty_model_list_is_runtime_failure": "empty_model_list_runtime_failure_claim_denied",
        "metadata_success_is_health_proof": "metadata_success_health_proof_denied",
        "model_list_is_availability_proof": "model_list_availability_proof_denied",
        "downloaded_models_are_availability_proof": "downloaded_models_availability_proof_denied",
        "self_reported_identity_is_authority": "self_reported_identity_authority_denied",
        "quality_or_benchmark_verified": "benchmark_verification_denied",
        "probe_candidate_selects_auto_mode": "auto_mode_selection_claim_denied",
        "model_inventory_proves_availability": "model_inventory_availability_proof_denied",
    }.items():
        if _truthy(data.get(field)):
            _add_failure(failures, reason, field, "probe projection cannot become runtime failure, proof, authority, benchmark, availability, or Auto Mode selection")


def _validate_related_decision(
    label: str,
    decision: Any | None,
    failures: list[LocalProviderProbeProjectionFailure],
    related_references: list[RelatedLocalProviderProbeProjectionReference],
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
            f"{label} cannot authorize provider health, model availability, runtime mutation, live probing, evidence, verifier success, or grants",
        )
    related_references.append(
        RelatedLocalProviderProbeProjectionReference(
            label=label,
            observed_status=_related_status(decision),
            implementation_claim=len(failures) > before,
        )
    )


def _validate_forbidden_claims(
    label: str,
    source: Any,
    failures: list[LocalProviderProbeProjectionFailure],
) -> None:
    for field, reason in FORBIDDEN_TRUTHY_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(
                failures,
                reason,
                f"{label}.{field}",
                f"{label} cannot claim authority, grants, evidence, verifier success, health mutation, provider health proof, model availability proof, identity proof, benchmark proof, or execution selection",
            )
    for field, reason in FORBIDDEN_BEHAVIOR_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(
                failures,
                reason,
                f"{label}.{field}",
                f"{label} cannot perform live probes, sockets, HTTP, runtime/API wiring, model behavior, payload transfer, auth, secret reads, external calls, or runtime mutations",
            )
    execution_permission = _field_value(source, "execution_permission")
    if execution_permission not in (None, "", LOCAL_PROVIDER_PROBE_PROJECTION_EXECUTION_PERMISSION):
        permission_text = str(execution_permission)
        if not permission_text.startswith("not_granted"):
            _add_failure(failures, "execution_permission_claim_denied", f"{label}.execution_permission", "local provider probe projection cannot grant execution permission")


def _projection_status(
    projection_input: LocalProviderProbeProjectionInput | None,
    failures: tuple[LocalProviderProbeProjectionFailure, ...],
) -> str:
    if projection_input is None:
        return "blocked_by_missing_required_field"
    reasons = {failure.reason for failure in failures}
    if not reasons:
        if projection_input.probe_result_class in NEGATIVE_RESULT_CLASSES:
            return "negative_candidate_projected"
        if projection_input.probe_result_class in SUCCESS_CANDIDATE_RESULTS:
            return "metadata_candidate_projected"
        if projection_input.probe_result_class == "empty_model_list_candidate":
            return "empty_model_list_candidate_projected"
        if projection_input.probe_result_class in {"not_observed", "not_executed"}:
            return "not_executed_projected"
        return "projection_ready"
    if "unsafe_related_decision" in reasons:
        return "blocked_by_unsafe_related_decision"
    if any(reason.startswith("missing_") or reason.startswith("unsupported_") for reason in reasons):
        return "blocked_by_missing_required_field"
    if any("mutation" in reason or "health_" in reason for reason in reasons):
        return "blocked_by_health_mutation_or_proof_claim"
    if any("runtime_failure" in reason or "truth" in reason or "proof" in reason or "availability" in reason or "identity" in reason or "benchmark" in reason for reason in reasons):
        return "blocked_by_truthfulness_claim"
    if any("probe" in reason or "socket" in reason or "http" in reason or "call" in reason or "payload" in reason or "external" in reason for reason in reasons):
        return "blocked_by_execution_claim"
    if any("grant" in reason or "authority" in reason or "dispatch" in reason for reason in reasons):
        return "blocked_by_authority_claim"
    return "blocked_by_projection_policy"


def _display_status_candidate(
    projection_input: LocalProviderProbeProjectionInput | None,
    failures: tuple[LocalProviderProbeProjectionFailure, ...],
) -> str:
    if projection_input is None or failures:
        return "blocked_or_not_displayable"
    return projection_input.maintenance_surface_status_class or "provider_probe_unknown"


def _result_semantics(
    projection_input: LocalProviderProbeProjectionInput | None,
    failures: tuple[LocalProviderProbeProjectionFailure, ...],
) -> str:
    if projection_input is None or failures:
        return "blocked"
    result = projection_input.probe_result_class
    if result in NEGATIVE_RESULT_CLASSES:
        return f"{result}_not_runtime_failure"
    if result == "empty_model_list_candidate":
        return "empty_model_list_candidate_not_runtime_failure_or_availability_proof"
    if result == "model_list_success_candidate":
        return "model_list_candidate_not_model_availability_proof"
    if result in {"metadata_success_candidate", "health_metadata_success_candidate"}:
        return f"{result}_not_provider_health_proof"
    return "not_executed_or_unknown_projection"


def _retry_semantics(
    projection_input: LocalProviderProbeProjectionInput | None,
    failures: tuple[LocalProviderProbeProjectionFailure, ...],
) -> str:
    if projection_input is None or failures:
        return "blocked"
    if projection_input.probe_result_class in RETRY_RECOMMENDED_RESULTS:
        return "retry_requires_operator_approval"
    if projection_input.probe_result_class in NEGATIVE_RESULT_CLASSES:
        return "operator_review_recommended"
    return "no_retry_authorized_by_projection"


def _truthfulness_classification(
    projection_input: LocalProviderProbeProjectionInput | None,
    failures: tuple[LocalProviderProbeProjectionFailure, ...],
) -> str:
    if projection_input is None or failures:
        return "blocked"
    return "projection_not_health_availability_identity_benchmark_evidence_verifier_or_permission"


def _required_operator_actions(
    projection_input: LocalProviderProbeProjectionInput | None,
    failures: tuple[LocalProviderProbeProjectionFailure, ...],
) -> tuple[str, ...]:
    if projection_input is None or failures:
        return ()
    actions: list[str] = []
    result = projection_input.probe_result_class
    if result in RETRY_RECOMMENDED_RESULTS:
        actions.append("operator_approval_required_before_retry")
    if result in NEGATIVE_RESULT_CLASSES:
        actions.append("operator_review_recommended")
    if projection_input.freshness_class in {"stale_candidate", "historical_candidate", "unknown_freshness"}:
        actions.append("freshness_review_recommended")
    return tuple(dict.fromkeys(actions))


def _related_status(decision: Any) -> str | None:
    for field in (
        "projection_status",
        "runner_status",
        "live_gate_status",
        "mock_runner_status",
        "wiring_readiness_status",
        "probe_boundary_status",
        "probe_result_status",
        "readiness_status",
        "selection_status",
        "inventory_status",
        "profile_status",
        "policy_status",
        "governance_status",
        "scope_status",
        "lifecycle_state",
        "policy_outcome",
    ):
        value = _field_value(decision, field)
        if value is not None:
            return str(value)
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


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _text_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        text = value.strip()
        return (text,) if text else ()
    if isinstance(value, (list, tuple, set)):
        return tuple(text for item in value if (text := _text(item)))
    text = _text(value)
    return (text,) if text else ()


def _mapping_tuple(value: Any) -> tuple[Mapping[str, Any], ...]:
    if value is None:
        return ()
    if isinstance(value, Mapping):
        return (deepcopy(dict(value)),)
    if isinstance(value, (list, tuple)):
        return tuple(deepcopy(dict(item)) for item in value if isinstance(item, Mapping))
    return ()


def _int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _add_failure(
    failures: list[LocalProviderProbeProjectionFailure],
    reason: str,
    field: str,
    message: str,
) -> None:
    failures.append(LocalProviderProbeProjectionFailure(reason=reason, field=field, message=message))
