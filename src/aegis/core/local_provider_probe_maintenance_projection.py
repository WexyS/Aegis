from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping


LOCAL_PROVIDER_PROBE_MAINTENANCE_PROJECTION_VERSION = (
    "local-provider-probe-maintenance-projection/1"
)
LOCAL_PROVIDER_PROBE_MAINTENANCE_PROJECTION_EXECUTION_PERMISSION = (
    "not_granted_by_local_provider_probe_maintenance_projection"
)

PROJECTION_API_SOURCE_CLASSES = {
    "local_provider_probe_projection",
    "manual_smoke_projection",
    "mock_runner_projection",
    "future_live_runner_projection",
    "maintenance_scan_future_projection",
    "mission_control_future_projection",
    "diagnostic_api_future_projection",
    "caller_supplied_metadata",
    "unknown",
}

API_EXPOSURE_READINESS_CLASSES = {
    "api_projection_metadata_only",
    "maintenance_projection_candidate",
    "diagnostic_projection_candidate",
    "mission_control_projection_candidate",
    "requires_projection_helper",
    "requires_policy_gate",
    "requires_operator_review_for_retry",
    "blocked_by_missing_projection",
    "blocked_by_truth_label",
    "future_gated",
    "unknown",
}

MAINTENANCE_CATEGORY_CLASSES = {
    "provider_probe_status",
    "local_provider_reachability",
    "local_model_list_metadata",
    "local_provider_negative_candidate",
    "local_provider_retry_guidance",
    "local_provider_unknown",
    "unknown",
}

CONSUMER_SURFACE_CLASSES = {
    "maintenance_scan_future",
    "mission_control_future",
    "diagnostic_panel_future",
    "api_response_future",
    "cli_summary_future",
    "unknown",
}

DISPLAY_CONTRACT_CLASSES = {
    "non_authoritative_status_card",
    "negative_candidate_notice",
    "metadata_candidate_notice",
    "retry_requires_operator_approval_notice",
    "not_runtime_failure_notice",
    "not_provider_health_proof_notice",
    "not_model_availability_proof_notice",
    "unknown",
}

NEGATIVE_PROBE_RESULT_CLASSES = {
    "unreachable_negative_candidate",
    "timeout_negative_candidate",
    "connection_refused_negative_candidate",
    "invalid_response_negative_candidate",
    "unauthorized_negative_candidate",
    "unsupported_endpoint_negative_candidate",
    "cancelled_negative_candidate",
}

RETRY_REQUIRES_OPERATOR_APPROVAL_RESULTS = {
    "unreachable_negative_candidate",
    "timeout_negative_candidate",
    "connection_refused_negative_candidate",
    "invalid_response_negative_candidate",
}

METADATA_SUCCESS_RESULT_CLASSES = {
    "metadata_success_candidate",
    "model_list_success_candidate",
    "health_metadata_success_candidate",
}

EMPTY_MODEL_LIST_RESULT_CLASS = "empty_model_list_candidate"

KNOWN_PROBE_RESULT_CLASSES = (
    NEGATIVE_PROBE_RESULT_CLASSES
    | RETRY_REQUIRES_OPERATOR_APPROVAL_RESULTS
    | METADATA_SUCCESS_RESULT_CLASSES
    | {EMPTY_MODEL_LIST_RESULT_CLASS, "not_observed", "not_executed", "unknown"}
)

FORBIDDEN_TRUTHY_FIELDS = {
    "authority": "authority_must_be_false",
    "runtime_dispatch_allowed": "runtime_dispatch_not_allowed",
    "approval_grant": "approval_grant_not_allowed",
    "capability_grant": "capability_grant_not_allowed",
    "lease_grant": "lease_grant_not_allowed",
    "evidence_provided_by_maintenance_projection": "maintenance_projection_cannot_provide_evidence",
    "evidence_provided_by_probe_projection": "maintenance_projection_cannot_provide_evidence",
    "evidence_provided_by_probe_runner": "maintenance_projection_cannot_provide_evidence",
    "evidence_provided_by_live_gate": "maintenance_projection_cannot_provide_evidence",
    "evidence_provided_by_mock_probe": "maintenance_projection_cannot_provide_evidence",
    "evidence_created": "maintenance_projection_cannot_provide_evidence",
    "verifier_success": "maintenance_projection_cannot_mark_verifier_success",
    "verified_success": "maintenance_projection_cannot_mark_verifier_success",
    "mutation_performed": "mutation_performed_denied",
    "frontend_authority": "frontend_authority_not_allowed",
    "api_authority": "api_authority_not_allowed",
    "maintenance_health_mutated": "maintenance_health_mutation_denied",
    "runtime_health_mutated": "runtime_health_mutation_denied",
    "provider_health_verified": "provider_health_verification_denied",
    "health_verified": "provider_health_verification_denied",
    "model_availability_verified": "model_availability_verification_denied",
    "model_identity_verified": "model_identity_verification_denied",
    "benchmark_claim_verified": "benchmark_verification_denied",
    "retry_authorized": "retry_authorization_denied",
    "auto_mode_selection_performed": "auto_mode_selection_denied",
    "provider_selected_for_execution": "provider_execution_selection_denied",
    "model_selected_for_execution": "model_execution_selection_denied",
    "auto_mode_execution_allowed": "auto_mode_execution_denied",
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
    "success": "success_claim_denied",
    "proof": "proof_claim_denied",
    "certification_claim": "certification_claim_denied",
}

FORBIDDEN_BEHAVIOR_FIELDS = {
    "api_route_added": "api_route_addition_denied",
    "runtime_command_added": "runtime_command_addition_denied",
    "scheduler_added": "scheduler_addition_denied",
    "live_probe_performed": "live_probe_execution_denied",
    "real_endpoint_probed": "real_endpoint_probe_denied",
    "provider_probed": "provider_probe_execution_denied",
    "endpoint_probed": "endpoint_probe_execution_denied",
    "probe_executed": "probe_execution_denied",
    "socket_opened": "socket_open_denied",
    "http_request_performed": "http_request_denied",
    "api_call_performed": "api_call_denied",
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
    "mcp_call_performed": "mcp_call_denied",
    "tool_call_performed": "tool_call_denied",
    "memory_retrieval_performed": "memory_retrieval_denied",
    "context_retrieval_performed": "context_retrieval_denied",
    "repo_file_read_performed": "repo_file_read_denied",
    "web_query_performed": "web_query_denied",
}


@dataclass(frozen=True)
class LocalProviderProbeMaintenanceProjectionFailure:
    reason: str
    field: str
    message: str


@dataclass(frozen=True)
class LocalProviderProbeMaintenanceProjectionInput:
    request_id: str | None
    projection_api_source_class: str | None
    api_exposure_readiness_class: str | None
    maintenance_category_class: str | None
    consumer_surface_class: str | None
    display_contract_class: str | None
    namespace: str | None
    source_refs: tuple[Mapping[str, Any], ...]
    provenance: tuple[Mapping[str, Any], ...]
    local_provider_probe_projection_ref: Mapping[str, Any] | None
    probe_result_class: str | None
    projection_status: str | None
    display_severity_class: str | None
    limitations: tuple[str, ...]
    unknowns: tuple[str, ...]


@dataclass(frozen=True)
class RelatedLocalProviderProbeMaintenanceProjectionReference:
    label: str
    observed_status: str | None
    reference_only: bool = True
    authority: bool = False
    implementation_claim: bool = False


@dataclass(frozen=True)
class LocalProviderProbeMaintenanceProjectionDecision:
    contract_version: str
    projection_status: str
    request_id: str | None
    projection_api_source_class: str | None
    api_exposure_readiness_class: str | None
    maintenance_category_class: str | None
    consumer_surface_class: str | None
    display_contract_class: str | None
    namespace: str | None
    probe_result_class: str | None
    api_projection_semantics: str
    display_status_candidate: str
    retry_semantics: str
    truthfulness_classification: str
    related_references: tuple[RelatedLocalProviderProbeMaintenanceProjectionReference, ...]
    required_operator_actions: tuple[str, ...]
    failure_reasons: tuple[str, ...]
    failures: tuple[LocalProviderProbeMaintenanceProjectionFailure, ...]
    projection_input: LocalProviderProbeMaintenanceProjectionInput | None
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = LOCAL_PROVIDER_PROBE_MAINTENANCE_PROJECTION_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_maintenance_projection: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    frontend_authority: bool = False
    api_authority: bool = False
    api_route_added: bool = False
    runtime_command_added: bool = False
    scheduler_added: bool = False
    maintenance_health_mutated: bool = False
    runtime_health_mutated: bool = False
    provider_health_verified: bool = False
    model_availability_verified: bool = False
    model_identity_verified: bool = False
    benchmark_claim_verified: bool = False
    retry_authorized: bool = False
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


def validate_local_provider_probe_maintenance_projection_request(
    request: Mapping[str, Any] | None,
    *,
    local_provider_probe_projection_decision: Any | None = None,
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
) -> LocalProviderProbeMaintenanceProjectionDecision:
    """Validate maintenance projection metadata without adding API/runtime behavior."""

    if not isinstance(request, Mapping):
        failure = LocalProviderProbeMaintenanceProjectionFailure(
            reason="missing_request",
            field="request",
            message="maintenance projection requires caller-supplied metadata",
        )
        return _decision(projection_input=None, related_references=(), failures=(failure,))

    data = deepcopy(dict(request))
    failures: list[LocalProviderProbeMaintenanceProjectionFailure] = []
    related_references: list[RelatedLocalProviderProbeMaintenanceProjectionReference] = []

    _validate_forbidden_claims("request", data, failures)
    related_decisions = {
        "local_provider_probe_projection": local_provider_probe_projection_decision,
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
    }
    for label, decision in related_decisions.items():
        _validate_related_decision(label, decision, failures, related_references)

    projection_ref = _projection_reference(data, local_provider_probe_projection_decision)
    projection_input = LocalProviderProbeMaintenanceProjectionInput(
        request_id=_text(data.get("request_id")),
        projection_api_source_class=_text(data.get("projection_api_source_class")),
        api_exposure_readiness_class=_text(data.get("api_exposure_readiness_class")),
        maintenance_category_class=_text(data.get("maintenance_category_class")),
        consumer_surface_class=_text(data.get("consumer_surface_class")),
        display_contract_class=_text(data.get("display_contract_class")),
        namespace=_text(data.get("namespace")),
        source_refs=_mapping_tuple(data.get("source_refs")),
        provenance=_mapping_tuple(data.get("provenance")),
        local_provider_probe_projection_ref=projection_ref,
        probe_result_class=_probe_result_class(data, projection_ref, local_provider_probe_projection_decision),
        projection_status=_text(data.get("projection_status")) or _related_status(local_provider_probe_projection_decision),
        display_severity_class=_text(data.get("display_severity_class")),
        limitations=_text_tuple(data.get("limitations")),
        unknowns=_text_tuple(data.get("unknowns")),
    )

    _validate_required(projection_input, failures)
    _validate_projection_semantics(projection_input, failures)

    return _decision(
        projection_input=projection_input,
        related_references=tuple(related_references),
        failures=tuple(failures),
    )


def _decision(
    *,
    projection_input: LocalProviderProbeMaintenanceProjectionInput | None,
    related_references: tuple[RelatedLocalProviderProbeMaintenanceProjectionReference, ...],
    failures: tuple[LocalProviderProbeMaintenanceProjectionFailure, ...],
) -> LocalProviderProbeMaintenanceProjectionDecision:
    return LocalProviderProbeMaintenanceProjectionDecision(
        contract_version=LOCAL_PROVIDER_PROBE_MAINTENANCE_PROJECTION_VERSION,
        projection_status=_projection_status(projection_input, failures),
        request_id=projection_input.request_id if projection_input else None,
        projection_api_source_class=projection_input.projection_api_source_class if projection_input else None,
        api_exposure_readiness_class=projection_input.api_exposure_readiness_class if projection_input else None,
        maintenance_category_class=projection_input.maintenance_category_class if projection_input else None,
        consumer_surface_class=projection_input.consumer_surface_class if projection_input else None,
        display_contract_class=projection_input.display_contract_class if projection_input else None,
        namespace=projection_input.namespace if projection_input else None,
        probe_result_class=projection_input.probe_result_class if projection_input else None,
        api_projection_semantics=_api_projection_semantics(projection_input, failures),
        display_status_candidate=_display_status_candidate(projection_input, failures),
        retry_semantics=_retry_semantics(projection_input, failures),
        truthfulness_classification=_truthfulness_classification(projection_input, failures),
        related_references=related_references,
        required_operator_actions=_required_operator_actions(projection_input, failures),
        failure_reasons=tuple(dict.fromkeys(f.reason for f in failures)),
        failures=failures,
        projection_input=projection_input,
    )


def _validate_required(
    projection_input: LocalProviderProbeMaintenanceProjectionInput,
    failures: list[LocalProviderProbeMaintenanceProjectionFailure],
) -> None:
    required = {
        "request_id": projection_input.request_id,
        "projection_api_source_class": projection_input.projection_api_source_class,
        "api_exposure_readiness_class": projection_input.api_exposure_readiness_class,
        "maintenance_category_class": projection_input.maintenance_category_class,
        "consumer_surface_class": projection_input.consumer_surface_class,
        "display_contract_class": projection_input.display_contract_class,
        "namespace": projection_input.namespace,
    }
    for field, value in required.items():
        if not value:
            _add_failure(failures, f"missing_{field}", field, f"{field} is required")
    if not (projection_input.source_refs or projection_input.provenance):
        _add_failure(
            failures,
            "missing_source_refs_or_provenance",
            "source_refs",
            "source refs or provenance are required",
        )
    if projection_input.local_provider_probe_projection_ref is None:
        _add_failure(
            failures,
            "missing_probe_projection_reference",
            "local_provider_probe_projection_ref",
            "maintenance projection requires a safe probe projection reference or equivalent metadata",
        )
    if projection_input.projection_api_source_class and projection_input.projection_api_source_class not in PROJECTION_API_SOURCE_CLASSES:
        _add_failure(failures, "unsupported_projection_api_source_class", "projection_api_source_class", "projection API source class is not recognized")
    if projection_input.api_exposure_readiness_class and projection_input.api_exposure_readiness_class not in API_EXPOSURE_READINESS_CLASSES:
        _add_failure(failures, "unsupported_api_exposure_readiness_class", "api_exposure_readiness_class", "API exposure readiness class is not recognized")
    if projection_input.maintenance_category_class and projection_input.maintenance_category_class not in MAINTENANCE_CATEGORY_CLASSES:
        _add_failure(failures, "unsupported_maintenance_category_class", "maintenance_category_class", "maintenance category class is not recognized")
    if projection_input.consumer_surface_class and projection_input.consumer_surface_class not in CONSUMER_SURFACE_CLASSES:
        _add_failure(failures, "unsupported_consumer_surface_class", "consumer_surface_class", "consumer surface class is not recognized")
    if projection_input.display_contract_class and projection_input.display_contract_class not in DISPLAY_CONTRACT_CLASSES:
        _add_failure(failures, "unsupported_display_contract_class", "display_contract_class", "display contract class is not recognized")
    if projection_input.probe_result_class and projection_input.probe_result_class not in KNOWN_PROBE_RESULT_CLASSES:
        _add_failure(failures, "unsupported_probe_result_class", "probe_result_class", "probe result class is not recognized")


def _validate_projection_semantics(
    projection_input: LocalProviderProbeMaintenanceProjectionInput,
    failures: list[LocalProviderProbeMaintenanceProjectionFailure],
) -> None:
    source = projection_input.projection_api_source_class
    readiness = projection_input.api_exposure_readiness_class
    category = projection_input.maintenance_category_class
    surface = projection_input.consumer_surface_class
    display = projection_input.display_contract_class
    result = projection_input.probe_result_class

    if source == "unknown":
        _add_failure(failures, "unknown_projection_api_source_blocked", "projection_api_source_class", "unknown projection API source requires clarification")
    if readiness == "unknown":
        _add_failure(failures, "unknown_api_exposure_readiness_blocked", "api_exposure_readiness_class", "unknown API readiness requires clarification")
    if category == "unknown":
        _add_failure(failures, "unknown_maintenance_category_blocked", "maintenance_category_class", "unknown maintenance category requires clarification")
    if surface == "unknown":
        _add_failure(failures, "unknown_consumer_surface_blocked", "consumer_surface_class", "unknown consumer surface requires clarification")
    if display == "unknown":
        _add_failure(failures, "unknown_display_contract_blocked", "display_contract_class", "unknown display contract requires clarification")
    if result == "unknown":
        _add_failure(failures, "unknown_probe_result_blocked", "probe_result_class", "unknown probe result requires clarification")

    if readiness == "blocked_by_missing_projection":
        _add_failure(failures, "blocked_by_missing_projection", "api_exposure_readiness_class", "missing projection readiness remains blocked")
    if readiness == "blocked_by_truth_label":
        _add_failure(failures, "blocked_by_truth_label", "api_exposure_readiness_class", "truth label blocker remains blocked")
    if readiness == "future_gated" and display != "non_authoritative_status_card":
        _add_failure(failures, "future_gated_requires_non_authoritative_display", "display_contract_class", "future-gated projection requires non-authoritative display")

    if result in NEGATIVE_PROBE_RESULT_CLASSES:
        allowed_displays = {
            "negative_candidate_notice",
            "not_runtime_failure_notice",
            "retry_requires_operator_approval_notice",
            "non_authoritative_status_card",
        }
        if display not in allowed_displays:
            _add_failure(failures, "negative_candidate_display_contract_required", "display_contract_class", "negative candidates must use a negative, retry, not-runtime-failure, or non-authoritative display contract")
        if category not in {
            "local_provider_negative_candidate",
            "local_provider_reachability",
            "local_provider_retry_guidance",
            "provider_probe_status",
        }:
            _add_failure(failures, "negative_candidate_category_required", "maintenance_category_class", "negative candidates must stay in reachability, retry guidance, provider status, or negative candidate categories")
    if result in RETRY_REQUIRES_OPERATOR_APPROVAL_RESULTS:
        if readiness != "requires_operator_review_for_retry" or display != "retry_requires_operator_approval_notice":
            _add_failure(failures, "retry_requires_operator_approval", "api_exposure_readiness_class", "retryable negative candidates must preserve operator approval requirement")
    if result in METADATA_SUCCESS_RESULT_CLASSES:
        if display not in {
            "metadata_candidate_notice",
            "not_provider_health_proof_notice",
            "not_model_availability_proof_notice",
            "non_authoritative_status_card",
        }:
            _add_failure(failures, "metadata_candidate_display_contract_required", "display_contract_class", "metadata candidates must use metadata-only or non-proof display contracts")
    if result == "model_list_success_candidate":
        if category != "local_model_list_metadata":
            _add_failure(failures, "model_list_category_required", "maintenance_category_class", "model list candidates must stay in local model list metadata category")
        if display != "not_model_availability_proof_notice":
            _add_failure(failures, "model_list_availability_notice_required", "display_contract_class", "model list candidates must be labeled as not model availability proof")
    if result == EMPTY_MODEL_LIST_RESULT_CLASS:
        if display not in {
            "metadata_candidate_notice",
            "not_runtime_failure_notice",
            "not_model_availability_proof_notice",
            "non_authoritative_status_card",
        }:
            _add_failure(failures, "empty_model_list_display_contract_required", "display_contract_class", "empty model list is metadata only, not runtime failure")
    if readiness in {
        "api_projection_metadata_only",
        "maintenance_projection_candidate",
        "diagnostic_projection_candidate",
        "mission_control_projection_candidate",
    } and display == "retry_requires_operator_approval_notice" and result not in RETRY_REQUIRES_OPERATOR_APPROVAL_RESULTS:
        _add_failure(failures, "retry_notice_without_retryable_result", "display_contract_class", "retry notice requires a retryable negative candidate")


def _validate_related_decision(
    label: str,
    decision: Any | None,
    failures: list[LocalProviderProbeMaintenanceProjectionFailure],
    related_references: list[RelatedLocalProviderProbeMaintenanceProjectionReference],
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
            f"{label} cannot authorize API/runtime surfaces, retries, live probes, health mutation, provider proof, model proof, evidence, verifier success, or grants",
        )
    related_references.append(
        RelatedLocalProviderProbeMaintenanceProjectionReference(
            label=label,
            observed_status=_related_status(decision),
            implementation_claim=len(failures) > before,
        )
    )


def _validate_forbidden_claims(
    label: str,
    source: Any,
    failures: list[LocalProviderProbeMaintenanceProjectionFailure],
) -> None:
    for field, reason in FORBIDDEN_TRUTHY_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(
                failures,
                reason,
                f"{label}.{field}",
                f"{label} cannot claim authority, grants, evidence, verifier success, health mutation, provider health proof, model availability proof, identity proof, benchmark proof, retry authorization, or execution selection",
            )
    for field, reason in FORBIDDEN_BEHAVIOR_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(
                failures,
                reason,
                f"{label}.{field}",
                f"{label} cannot add API/runtime surfaces, run live probes, open sockets, perform HTTP, call models, send payloads, validate secrets, log bodies, call external endpoints, or mutate runtime state",
            )
    execution_permission = _field_value(source, "execution_permission")
    if execution_permission not in (
        None,
        "",
        LOCAL_PROVIDER_PROBE_MAINTENANCE_PROJECTION_EXECUTION_PERMISSION,
    ):
        permission_text = str(execution_permission)
        if not permission_text.startswith("not_granted"):
            _add_failure(
                failures,
                "execution_permission_claim_denied",
                f"{label}.execution_permission",
                "local provider probe maintenance projection cannot grant execution permission",
            )


def _projection_status(
    projection_input: LocalProviderProbeMaintenanceProjectionInput | None,
    failures: tuple[LocalProviderProbeMaintenanceProjectionFailure, ...],
) -> str:
    if projection_input is None:
        return "blocked_by_missing_required_field"
    reasons = {failure.reason for failure in failures}
    if not reasons:
        result = projection_input.probe_result_class
        if result in NEGATIVE_PROBE_RESULT_CLASSES:
            if result in RETRY_REQUIRES_OPERATOR_APPROVAL_RESULTS:
                return "negative_candidate_requires_operator_retry_review"
            return "negative_candidate_projection_ready"
        if result == "model_list_success_candidate":
            return "model_list_metadata_projection_ready"
        if result in METADATA_SUCCESS_RESULT_CLASSES:
            return "metadata_candidate_projection_ready"
        if result == EMPTY_MODEL_LIST_RESULT_CLASS:
            return "empty_model_list_projection_ready"
        if projection_input.api_exposure_readiness_class == "future_gated":
            return "future_gated_projection_ready"
        return "maintenance_projection_ready"
    if "unsafe_related_decision" in reasons:
        return "blocked_by_unsafe_related_decision"
    if "blocked_by_missing_projection" in reasons:
        return "blocked_by_missing_projection"
    if "blocked_by_truth_label" in reasons:
        return "blocked_by_truth_label"
    if any(reason.startswith("missing_") or reason.startswith("unsupported_") for reason in reasons):
        return "blocked_by_missing_required_field"
    if any("health_" in reason or "runtime_failure" in reason or "proof" in reason or "availability" in reason or "identity" in reason or "benchmark" in reason for reason in reasons):
        return "blocked_by_truthfulness_claim"
    if any("retry" in reason for reason in reasons):
        return "blocked_by_retry_authorization_or_label"
    if any("route" in reason or "command" in reason or "scheduler" in reason or "probe" in reason or "socket" in reason or "http" in reason or "call" in reason or "payload" in reason or "secret" in reason or "external" in reason for reason in reasons):
        return "blocked_by_execution_claim"
    if any("grant" in reason or "authority" in reason or "dispatch" in reason for reason in reasons):
        return "blocked_by_authority_claim"
    return "blocked_by_projection_policy"


def _api_projection_semantics(
    projection_input: LocalProviderProbeMaintenanceProjectionInput | None,
    failures: tuple[LocalProviderProbeMaintenanceProjectionFailure, ...],
) -> str:
    if projection_input is None or failures:
        return "blocked"
    result = projection_input.probe_result_class
    if result in NEGATIVE_PROBE_RESULT_CLASSES:
        return f"{result}_display_only_not_runtime_failure_or_health_mutation"
    if result == "model_list_success_candidate":
        return "model_list_metadata_display_only_not_model_availability_proof"
    if result in METADATA_SUCCESS_RESULT_CLASSES:
        return f"{result}_display_only_not_provider_health_proof"
    if result == EMPTY_MODEL_LIST_RESULT_CLASS:
        return "empty_model_list_display_only_not_runtime_failure_or_availability_proof"
    return "projection_metadata_only_no_api_runtime_or_frontend_authority"


def _display_status_candidate(
    projection_input: LocalProviderProbeMaintenanceProjectionInput | None,
    failures: tuple[LocalProviderProbeMaintenanceProjectionFailure, ...],
) -> str:
    if projection_input is None or failures:
        return "blocked_or_not_displayable"
    return projection_input.display_contract_class or "non_authoritative_status_card"


def _retry_semantics(
    projection_input: LocalProviderProbeMaintenanceProjectionInput | None,
    failures: tuple[LocalProviderProbeMaintenanceProjectionFailure, ...],
) -> str:
    if projection_input is None or failures:
        return "blocked"
    if projection_input.probe_result_class in RETRY_REQUIRES_OPERATOR_APPROVAL_RESULTS:
        return "retry_requires_operator_approval"
    if projection_input.probe_result_class in NEGATIVE_PROBE_RESULT_CLASSES:
        return "operator_review_recommended_no_retry_authorized"
    return "no_retry_authorized_by_maintenance_projection"


def _truthfulness_classification(
    projection_input: LocalProviderProbeMaintenanceProjectionInput | None,
    failures: tuple[LocalProviderProbeMaintenanceProjectionFailure, ...],
) -> str:
    if projection_input is None or failures:
        return "blocked"
    return "not_runtime_health_not_provider_health_not_model_availability_not_evidence_not_verifier_success"


def _required_operator_actions(
    projection_input: LocalProviderProbeMaintenanceProjectionInput | None,
    failures: tuple[LocalProviderProbeMaintenanceProjectionFailure, ...],
) -> tuple[str, ...]:
    if projection_input is None or failures:
        return ()
    actions: list[str] = []
    if projection_input.probe_result_class in RETRY_REQUIRES_OPERATOR_APPROVAL_RESULTS:
        actions.append("operator_approval_required_before_retry")
    if projection_input.probe_result_class in NEGATIVE_PROBE_RESULT_CLASSES:
        actions.append("operator_review_recommended")
    if projection_input.api_exposure_readiness_class in {"requires_policy_gate", "future_gated"}:
        actions.append("policy_gate_required_before_future_surface")
    return tuple(dict.fromkeys(actions))


def _projection_reference(
    data: Mapping[str, Any],
    projection_decision: Any | None,
) -> Mapping[str, Any] | None:
    for field in (
        "local_provider_probe_projection_ref",
        "probe_projection_ref",
        "projection_ref",
        "probe_projection_metadata",
    ):
        value = data.get(field)
        if isinstance(value, Mapping):
            return deepcopy(dict(value))
    if _text(data.get("probe_result_class")) or _text(data.get("projection_status")):
        return {
            "probe_result_class": _text(data.get("probe_result_class")),
            "projection_status": _text(data.get("projection_status")),
            "ref_type": "caller_supplied_probe_projection_metadata",
        }
    if projection_decision is not None:
        return {
            "probe_result_class": _field_value(projection_decision, "probe_result_class"),
            "projection_status": _related_status(projection_decision),
            "ref_type": "related_probe_projection_decision",
        }
    return None


def _probe_result_class(
    data: Mapping[str, Any],
    projection_ref: Mapping[str, Any] | None,
    projection_decision: Any | None,
) -> str | None:
    from_request = _text(data.get("probe_result_class"))
    from_ref = _text(projection_ref.get("probe_result_class")) if projection_ref else None
    from_decision = _text(_field_value(projection_decision, "probe_result_class"))
    return from_request or from_ref or from_decision


def _related_status(decision: Any | None) -> str | None:
    if decision is None:
        return None
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
    if source is None:
        return None
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


def _add_failure(
    failures: list[LocalProviderProbeMaintenanceProjectionFailure],
    reason: str,
    field: str,
    message: str,
) -> None:
    failures.append(LocalProviderProbeMaintenanceProjectionFailure(reason=reason, field=field, message=message))
