from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping


LOCAL_PROVIDER_PROBE_MOCK_RUNNER_VERSION = "local-provider-health-probe-mock-runner/1"
LOCAL_PROVIDER_PROBE_MOCK_RUNNER_EXECUTION_PERMISSION = (
    "not_granted_by_local_provider_probe_mock_runner"
)

RUNNER_REQUEST_CLASSES = {
    "mock_provider_root_probe",
    "mock_models_list_probe",
    "mock_health_metadata_probe",
    "mock_invalid_response_probe",
    "mock_timeout_probe",
    "mock_connection_refused_probe",
    "mock_unauthorized_probe",
    "mock_unsupported_endpoint_probe",
    "unknown",
}

MOCK_RESULT_CLASSES = {
    "mock_success_metadata_candidate",
    "mock_timeout_negative_candidate",
    "mock_connection_refused_negative_candidate",
    "mock_invalid_response_negative_candidate",
    "mock_unauthorized_negative_candidate",
    "mock_unsupported_endpoint_negative_candidate",
    "mock_malformed_metadata_negative_candidate",
    "not_executed",
    "unknown",
}

NEGATIVE_MOCK_RESULTS = {
    "mock_timeout_negative_candidate",
    "mock_connection_refused_negative_candidate",
    "mock_invalid_response_negative_candidate",
    "mock_unauthorized_negative_candidate",
    "mock_unsupported_endpoint_negative_candidate",
    "mock_malformed_metadata_negative_candidate",
}

RUNNER_READINESS_CLASSES = {
    "mock_runner_ready",
    "requires_probe_wiring",
    "requires_probe_boundary",
    "blocked_by_transport",
    "blocked_by_endpoint_scope",
    "blocked_by_payload",
    "blocked_by_secret_policy",
    "blocked_by_timeout_policy",
    "blocked_by_unknown_host",
    "blocked_by_real_transport",
    "future_gated",
    "unknown",
}

METADATA_RESPONSE_SHAPE_CLASSES = {
    "provider_metadata_shape_candidate",
    "models_list_shape_candidate",
    "health_metadata_shape_candidate",
    "empty_response_negative_candidate",
    "malformed_response_negative_candidate",
    "unknown_shape",
}

NEGATIVE_RESPONSE_SHAPES = {
    "empty_response_negative_candidate",
    "malformed_response_negative_candidate",
}

BLOCKED_RUNNER_READINESS_CLASSES = {
    "requires_probe_wiring": "missing_probe_wiring_reference",
    "requires_probe_boundary": "missing_probe_boundary_reference",
    "blocked_by_transport": "blocked_by_transport",
    "blocked_by_endpoint_scope": "blocked_by_endpoint_scope",
    "blocked_by_payload": "blocked_by_payload",
    "blocked_by_secret_policy": "blocked_by_secret_policy",
    "blocked_by_timeout_policy": "blocked_by_timeout_policy",
    "blocked_by_unknown_host": "blocked_by_unknown_host",
    "blocked_by_real_transport": "blocked_by_real_transport",
}

FORBIDDEN_TRUTHY_FIELDS = {
    "authority": "authority_must_be_false",
    "runtime_dispatch_allowed": "runtime_dispatch_not_allowed",
    "approval_grant": "approval_grant_not_allowed",
    "capability_grant": "capability_grant_not_allowed",
    "lease_grant": "lease_grant_not_allowed",
    "evidence_provided_by_mock_probe": "mock_runner_cannot_provide_evidence",
    "evidence_provided_by_probe_wiring": "mock_runner_cannot_provide_evidence",
    "evidence_provided_by_probe": "mock_runner_cannot_provide_evidence",
    "evidence_created": "mock_runner_cannot_provide_evidence",
    "verifier_success": "mock_runner_cannot_mark_verifier_success",
    "verified_success": "mock_runner_cannot_mark_verifier_success",
    "mutation_performed": "mutation_performed_denied",
    "frontend_authority": "frontend_authority_not_allowed",
    "success": "success_claim_denied",
    "proof": "proof_claim_denied",
    "certification_claim": "certification_claim_denied",
    "provider_health_verified": "provider_health_verification_denied",
    "health_verified": "provider_health_verification_denied",
    "model_availability_verified": "model_availability_verification_denied",
    "model_identity_verified": "model_identity_verification_denied",
    "benchmark_claim_verified": "benchmark_verification_denied",
    "provider_metadata_is_truth": "provider_metadata_truth_claim_denied",
    "model_list_is_truth": "model_list_truth_claim_denied",
    "mock_success_is_health_proof": "mock_success_health_proof_denied",
    "mock_model_list_is_availability_proof": "mock_model_list_availability_proof_denied",
    "mock_health_metadata_is_verifier_success": "mock_health_verifier_success_claim_denied",
    "negative_mock_result_is_runtime_failure": "negative_mock_runtime_failure_claim_denied",
    "self_reported_identity_is_authority": "self_reported_identity_authority_denied",
    "quality_or_benchmark_verified": "benchmark_verification_denied",
    "provider_selected_for_execution": "provider_execution_selection_denied",
    "model_selected_for_execution": "model_execution_selection_denied",
    "auto_mode_execution_allowed": "auto_mode_execution_denied",
    "probe_candidate_selects_auto_mode": "auto_mode_selection_claim_denied",
    "model_inventory_proves_availability": "model_inventory_availability_proof_denied",
}

FORBIDDEN_BEHAVIOR_FIELDS = {
    "api_route_added": "api_route_addition_denied",
    "runtime_command_added": "runtime_command_addition_denied",
    "scheduler_added": "scheduler_addition_denied",
    "real_endpoint_probed": "real_endpoint_probe_denied",
    "provider_probed": "provider_probe_execution_denied",
    "endpoint_probed": "endpoint_probe_execution_denied",
    "probe_executed": "probe_execution_denied",
    "socket_opened": "socket_open_denied",
    "http_request_performed": "http_request_denied",
    "real_transport_used": "real_transport_use_denied",
    "provider_authenticated": "provider_authentication_denied",
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
class LocalProviderProbeMockRunnerFailure:
    reason: str
    field: str
    message: str


@dataclass(frozen=True)
class LocalProviderProbeMockRunnerInput:
    request_id: str | None
    runner_request_class: str | None
    mock_result_class: str | None
    runner_readiness_class: str | None
    metadata_response_shape_class: str | None
    namespace: str | None
    source_refs: tuple[Mapping[str, Any], ...]
    provenance: tuple[Mapping[str, Any], ...]
    paired_probe_wiring_ref: str | None
    paired_probe_boundary_ref: str | None
    limitations: tuple[str, ...]
    unknowns: tuple[str, ...]
    mock_transport_only_requested: bool | None


@dataclass(frozen=True)
class RelatedLocalProviderProbeMockRunnerReference:
    label: str
    observed_status: str | None
    reference_only: bool = True
    authority: bool = False
    implementation_claim: bool = False


@dataclass(frozen=True)
class LocalProviderProbeMockRunnerDecision:
    contract_version: str
    mock_runner_status: str
    request_id: str | None
    runner_request_class: str | None
    mock_result_class: str | None
    runner_readiness_class: str | None
    metadata_response_shape_class: str | None
    namespace: str | None
    runner_classification: str
    mock_result_classification: str
    response_shape_classification: str
    truthfulness_classification: str
    related_references: tuple[RelatedLocalProviderProbeMockRunnerReference, ...]
    required_future_gates: tuple[str, ...]
    failure_reasons: tuple[str, ...]
    failures: tuple[LocalProviderProbeMockRunnerFailure, ...]
    probe_input: LocalProviderProbeMockRunnerInput | None
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = LOCAL_PROVIDER_PROBE_MOCK_RUNNER_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_mock_probe: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    frontend_authority: bool = False
    api_route_added: bool = False
    runtime_command_added: bool = False
    scheduler_added: bool = False
    real_endpoint_probed: bool = False
    socket_opened: bool = False
    http_request_performed: bool = False
    provider_probed: bool = False
    mock_transport_only: bool = True
    real_transport_used: bool = False
    model_loaded: bool = False
    model_call_performed: bool = False
    generation_performed: bool = False
    embedding_generated: bool = False
    reranking_performed: bool = False
    multimodal_inference_performed: bool = False
    prompt_payload_sent: bool = False
    context_payload_sent: bool = False
    memory_payload_sent: bool = False
    repo_payload_sent: bool = False
    raw_journal_payload_sent: bool = False
    raw_evidence_payload_sent: bool = False
    api_key_validated: bool = False
    secret_read: bool = False
    authorization_header_sent: bool = False
    cloud_provider_called: bool = False
    lan_or_remote_endpoint_called: bool = False
    data_sent_external: bool = False
    provider_health_verified: bool = False
    model_availability_verified: bool = False
    model_identity_verified: bool = False
    benchmark_claim_verified: bool = False
    runtime_state_mutated: bool = False
    journal_mutated: bool = False
    evidence_mutated: bool = False
    replay_mutated: bool = False
    requires_backend_validation: bool = True
    requires_policy_check: bool = True
    read_only_projection: bool = True


def validate_local_provider_probe_mock_runner_request(
    request: Mapping[str, Any] | None,
    *,
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
) -> LocalProviderProbeMockRunnerDecision:
    """Classify injected mock probe result metadata without real provider access."""

    if not isinstance(request, Mapping):
        failure = LocalProviderProbeMockRunnerFailure(
            reason="missing_request",
            field="request",
            message="local provider probe mock runner requires caller-supplied metadata",
        )
        return _decision(probe_input=None, related_references=(), failures=(failure,))

    data = deepcopy(dict(request))
    failures: list[LocalProviderProbeMockRunnerFailure] = []
    related_references: list[RelatedLocalProviderProbeMockRunnerReference] = []

    _validate_forbidden_claims("request", data, failures)
    for label, decision in {
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

    probe_input = LocalProviderProbeMockRunnerInput(
        request_id=_text(data.get("request_id")),
        runner_request_class=_text(data.get("runner_request_class")),
        mock_result_class=_text(data.get("mock_result_class")),
        runner_readiness_class=_text(data.get("runner_readiness_class")),
        metadata_response_shape_class=_text(data.get("metadata_response_shape_class")),
        namespace=_text(data.get("namespace")),
        source_refs=_mapping_tuple(data.get("source_refs")),
        provenance=_mapping_tuple(data.get("provenance")),
        paired_probe_wiring_ref=_text(data.get("paired_probe_wiring_ref")),
        paired_probe_boundary_ref=_text(data.get("paired_probe_boundary_ref")),
        limitations=_text_tuple(data.get("limitations")),
        unknowns=_text_tuple(data.get("unknowns")),
        mock_transport_only_requested=_optional_bool(data.get("mock_transport_only")),
    )

    _validate_required(
        probe_input,
        failures,
        has_wiring_decision=local_provider_probe_wiring_decision is not None,
        has_boundary_decision=local_provider_probe_boundary_decision is not None,
    )
    _validate_runner_metadata(probe_input, failures)
    _validate_mock_result_and_shape(probe_input, failures)
    _validate_truthfulness(data, failures)

    return _decision(
        probe_input=probe_input,
        related_references=tuple(related_references),
        failures=tuple(failures),
    )


def _decision(
    *,
    probe_input: LocalProviderProbeMockRunnerInput | None,
    related_references: tuple[RelatedLocalProviderProbeMockRunnerReference, ...],
    failures: tuple[LocalProviderProbeMockRunnerFailure, ...],
) -> LocalProviderProbeMockRunnerDecision:
    future_gates = _future_gates(probe_input, failures)
    return LocalProviderProbeMockRunnerDecision(
        contract_version=LOCAL_PROVIDER_PROBE_MOCK_RUNNER_VERSION,
        mock_runner_status=_mock_runner_status(probe_input, failures, future_gates),
        request_id=probe_input.request_id if probe_input else None,
        runner_request_class=probe_input.runner_request_class if probe_input else None,
        mock_result_class=probe_input.mock_result_class if probe_input else None,
        runner_readiness_class=probe_input.runner_readiness_class if probe_input else None,
        metadata_response_shape_class=probe_input.metadata_response_shape_class if probe_input else None,
        namespace=probe_input.namespace if probe_input else None,
        runner_classification=_runner_classification(probe_input, failures, future_gates),
        mock_result_classification=_mock_result_classification(probe_input, failures),
        response_shape_classification=_response_shape_classification(probe_input, failures),
        truthfulness_classification=_truthfulness_classification(probe_input, failures),
        related_references=related_references,
        required_future_gates=future_gates,
        failure_reasons=tuple(dict.fromkeys(f.reason for f in failures)),
        failures=failures,
        probe_input=probe_input,
    )


def _validate_required(
    probe_input: LocalProviderProbeMockRunnerInput,
    failures: list[LocalProviderProbeMockRunnerFailure],
    *,
    has_wiring_decision: bool,
    has_boundary_decision: bool,
) -> None:
    required = {
        "request_id": probe_input.request_id,
        "runner_request_class": probe_input.runner_request_class,
        "mock_result_class": probe_input.mock_result_class,
        "runner_readiness_class": probe_input.runner_readiness_class,
        "metadata_response_shape_class": probe_input.metadata_response_shape_class,
        "namespace": probe_input.namespace,
    }
    for field, value in required.items():
        if value is None or value == "":
            _add_failure(failures, f"missing_{field}", field, f"{field} is required")
    if not (probe_input.source_refs or probe_input.provenance):
        _add_failure(failures, "missing_source_refs_or_provenance", "source_refs", "source refs or provenance are required")
    if not (probe_input.paired_probe_wiring_ref or has_wiring_decision):
        _add_failure(failures, "missing_probe_wiring_reference", "paired_probe_wiring_ref", "paired probe wiring metadata or related decision is required")
    if not (probe_input.paired_probe_boundary_ref or has_boundary_decision):
        _add_failure(failures, "missing_probe_boundary_reference", "paired_probe_boundary_ref", "paired probe boundary metadata or related decision is required")
    if probe_input.runner_request_class and probe_input.runner_request_class not in RUNNER_REQUEST_CLASSES:
        _add_failure(failures, "unsupported_runner_request_class", "runner_request_class", "runner request class is not recognized")
    if probe_input.mock_result_class and probe_input.mock_result_class not in MOCK_RESULT_CLASSES:
        _add_failure(failures, "unsupported_mock_result_class", "mock_result_class", "mock result class is not recognized")
    if probe_input.runner_readiness_class and probe_input.runner_readiness_class not in RUNNER_READINESS_CLASSES:
        _add_failure(failures, "unsupported_runner_readiness_class", "runner_readiness_class", "runner readiness class is not recognized")
    if probe_input.metadata_response_shape_class and probe_input.metadata_response_shape_class not in METADATA_RESPONSE_SHAPE_CLASSES:
        _add_failure(failures, "unsupported_metadata_response_shape_class", "metadata_response_shape_class", "metadata response shape class is not recognized")


def _validate_runner_metadata(
    probe_input: LocalProviderProbeMockRunnerInput,
    failures: list[LocalProviderProbeMockRunnerFailure],
) -> None:
    if probe_input.runner_request_class == "unknown":
        _add_failure(failures, "unknown_runner_request_blocked", "runner_request_class", "unknown mock runner request is blocked")
    if probe_input.runner_readiness_class in BLOCKED_RUNNER_READINESS_CLASSES:
        _add_failure(
            failures,
            BLOCKED_RUNNER_READINESS_CLASSES[probe_input.runner_readiness_class],
            "runner_readiness_class",
            "blocked runner readiness metadata cannot become a mock runner result",
        )
    if probe_input.runner_readiness_class == "unknown":
        _add_failure(failures, "unknown_runner_readiness_blocked", "runner_readiness_class", "unknown mock runner readiness is blocked")
    if probe_input.mock_transport_only_requested is False and probe_input.mock_result_class != "not_executed":
        _add_failure(failures, "mock_transport_only_required", "mock_transport_only", "mock runner requires mock_transport_only=true for candidate results")


def _validate_mock_result_and_shape(
    probe_input: LocalProviderProbeMockRunnerInput,
    failures: list[LocalProviderProbeMockRunnerFailure],
) -> None:
    result = probe_input.mock_result_class
    shape = probe_input.metadata_response_shape_class
    if result == "unknown":
        _add_failure(failures, "unknown_mock_result_blocked", "mock_result_class", "unknown mock result is blocked")
    if shape == "unknown_shape":
        _add_failure(failures, "unknown_response_shape", "metadata_response_shape_class", "unknown response shape remains unknown and requires review")
    if shape in NEGATIVE_RESPONSE_SHAPES and result == "mock_success_metadata_candidate":
        _add_failure(failures, "mock_success_response_shape_mismatch", "metadata_response_shape_class", "mock success cannot use negative response shape")
    if result in NEGATIVE_MOCK_RESULTS and shape not in NEGATIVE_RESPONSE_SHAPES | {
        "provider_metadata_shape_candidate",
        "models_list_shape_candidate",
        "health_metadata_shape_candidate",
    }:
        _add_failure(failures, "negative_mock_response_shape_unknown", "metadata_response_shape_class", "negative mock result requires explicit response shape metadata")
    if result == "mock_timeout_negative_candidate" and probe_input.runner_request_class != "mock_timeout_probe":
        _add_failure(failures, "mock_timeout_runner_mismatch", "runner_request_class", "timeout result requires timeout runner request class")
    if result == "mock_connection_refused_negative_candidate" and probe_input.runner_request_class != "mock_connection_refused_probe":
        _add_failure(failures, "mock_connection_refused_runner_mismatch", "runner_request_class", "connection refused result requires matching runner request class")
    if result == "mock_invalid_response_negative_candidate" and probe_input.runner_request_class not in {"mock_invalid_response_probe", "mock_unsupported_endpoint_probe"}:
        _add_failure(failures, "mock_invalid_response_runner_mismatch", "runner_request_class", "invalid response result requires matching runner request class")
    if result == "mock_unauthorized_negative_candidate" and probe_input.runner_request_class != "mock_unauthorized_probe":
        _add_failure(failures, "mock_unauthorized_runner_mismatch", "runner_request_class", "unauthorized result requires matching runner request class")
    if result == "mock_unsupported_endpoint_negative_candidate" and probe_input.runner_request_class != "mock_unsupported_endpoint_probe":
        _add_failure(failures, "mock_unsupported_endpoint_runner_mismatch", "runner_request_class", "unsupported endpoint result requires matching runner request class")


def _validate_truthfulness(data: Mapping[str, Any], failures: list[LocalProviderProbeMockRunnerFailure]) -> None:
    proof_fields = {
        "mock_success_is_health_proof": "mock_success_health_proof_denied",
        "mock_model_list_is_availability_proof": "mock_model_list_availability_proof_denied",
        "mock_health_metadata_is_verifier_success": "mock_health_verifier_success_claim_denied",
        "negative_mock_result_is_runtime_failure": "negative_mock_runtime_failure_claim_denied",
        "provider_metadata_is_truth": "provider_metadata_truth_claim_denied",
        "model_list_is_truth": "model_list_truth_claim_denied",
        "provider_health_is_proof": "provider_health_proof_denied",
        "model_availability_is_execution_ready": "model_availability_execution_ready_claim_denied",
        "quality_or_benchmark_verified": "benchmark_verification_denied",
        "self_reported_identity_is_authority": "self_reported_identity_authority_denied",
        "probe_candidate_selects_auto_mode": "auto_mode_selection_claim_denied",
        "model_inventory_proves_availability": "model_inventory_availability_proof_denied",
    }
    for field, reason in proof_fields.items():
        if _truthy(data.get(field)):
            _add_failure(failures, reason, field, "mock runner metadata cannot become proof, runtime failure, model availability, benchmark, identity, or Auto Mode selection")


def _validate_related_decision(
    label: str,
    decision: Any | None,
    failures: list[LocalProviderProbeMockRunnerFailure],
    related_references: list[RelatedLocalProviderProbeMockRunnerReference],
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
            f"{label} cannot authorize real probes, runtime/API wiring, model calls, payload transfer, evidence, verifier success, or grants",
        )
    related_references.append(
        RelatedLocalProviderProbeMockRunnerReference(
            label=label,
            observed_status=_related_status(decision),
            implementation_claim=len(failures) > before,
        )
    )


def _validate_forbidden_claims(
    label: str,
    source: Any,
    failures: list[LocalProviderProbeMockRunnerFailure],
) -> None:
    for field, reason in FORBIDDEN_TRUTHY_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(
                failures,
                reason,
                f"{label}.{field}",
                f"{label} cannot claim authority, grants, evidence, verifier success, provider health proof, model availability proof, identity proof, benchmark proof, or execution selection",
            )
    for field, reason in FORBIDDEN_BEHAVIOR_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(
                failures,
                reason,
                f"{label}.{field}",
                f"{label} cannot add runtime/API surfaces, perform probes, HTTP/socket behavior, use real transport, perform model behavior, transfer payloads, authenticate, read secrets, call external systems, or mutate runtime state",
            )
    execution_permission = _field_value(source, "execution_permission")
    if execution_permission not in (None, "", LOCAL_PROVIDER_PROBE_MOCK_RUNNER_EXECUTION_PERMISSION):
        permission_text = str(execution_permission)
        if not permission_text.startswith("not_granted"):
            _add_failure(failures, "execution_permission_claim_denied", f"{label}.execution_permission", "mock runner cannot grant execution permission")


def _mock_runner_status(
    probe_input: LocalProviderProbeMockRunnerInput | None,
    failures: tuple[LocalProviderProbeMockRunnerFailure, ...],
    future_gates: tuple[str, ...],
) -> str:
    if probe_input is None:
        return "requires_probe_wiring"
    reasons = {failure.reason for failure in failures}
    if not reasons:
        if future_gates:
            return "future_gated"
        return "mock_runner_ready"
    if "unsafe_related_decision" in reasons:
        return "blocked_by_transport"
    if "missing_probe_wiring_reference" in reasons:
        return "requires_probe_wiring"
    if "missing_probe_boundary_reference" in reasons:
        return "requires_probe_boundary"
    if any(reason.startswith("missing_") or reason.startswith("unsupported_") for reason in reasons):
        return "unknown"
    if any("transport" in reason or "socket" in reason or "http" in reason or "endpoint_probe" in reason or "real_endpoint" in reason for reason in reasons):
        return "blocked_by_transport"
    if any("endpoint" in reason for reason in reasons):
        return "blocked_by_endpoint_scope"
    if any("payload" in reason for reason in reasons):
        return "blocked_by_payload"
    if any("secret" in reason or "auth" in reason or "api_key" in reason for reason in reasons):
        return "blocked_by_secret_policy"
    if any("timeout" in reason for reason in reasons):
        return "blocked_by_timeout_policy"
    if any("unknown" in reason for reason in reasons):
        return "unknown"
    return "blocked_by_transport"


def _future_gates(
    probe_input: LocalProviderProbeMockRunnerInput | None,
    failures: tuple[LocalProviderProbeMockRunnerFailure, ...],
) -> tuple[str, ...]:
    if probe_input is None or failures:
        return ()
    gates: list[str] = []
    if probe_input.runner_readiness_class == "future_gated":
        gates.append("mock_runner_requires_future_gate")
    if probe_input.mock_result_class == "not_executed":
        gates.append("not_executed_requires_future_mock_result")
    return tuple(dict.fromkeys(gates))


def _runner_classification(
    probe_input: LocalProviderProbeMockRunnerInput | None,
    failures: tuple[LocalProviderProbeMockRunnerFailure, ...],
    future_gates: tuple[str, ...],
) -> str:
    if probe_input is None or failures:
        return "blocked"
    if future_gates:
        return "future_gated_not_executed"
    return "mock_transport_runner_metadata_only"


def _mock_result_classification(
    probe_input: LocalProviderProbeMockRunnerInput | None,
    failures: tuple[LocalProviderProbeMockRunnerFailure, ...],
) -> str:
    if probe_input is None or failures:
        return "blocked"
    if probe_input.mock_result_class in NEGATIVE_MOCK_RESULTS:
        return "negative_mock_candidate_metadata_only_not_runtime_failure"
    if probe_input.mock_result_class == "mock_success_metadata_candidate":
        return "mock_success_metadata_only_not_health_proof"
    return "not_executed"


def _response_shape_classification(
    probe_input: LocalProviderProbeMockRunnerInput | None,
    failures: tuple[LocalProviderProbeMockRunnerFailure, ...],
) -> str:
    if probe_input is None or failures:
        return "blocked"
    shape = probe_input.metadata_response_shape_class
    if shape == "models_list_shape_candidate":
        return "models_list_shape_candidate_not_availability_proof"
    if shape in NEGATIVE_RESPONSE_SHAPES:
        return "negative_response_shape_candidate_only"
    if shape == "unknown_shape":
        return "unknown_shape_requires_review"
    return "metadata_shape_candidate_only"


def _truthfulness_classification(
    probe_input: LocalProviderProbeMockRunnerInput | None,
    failures: tuple[LocalProviderProbeMockRunnerFailure, ...],
) -> str:
    if probe_input is None or failures:
        return "blocked"
    return "mock_metadata_not_health_model_identity_benchmark_evidence_or_verifier_proof"


def _related_status(decision: Any) -> str | None:
    for field in (
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
        "display_readiness_status",
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


def _optional_bool(value: Any) -> bool | None:
    if value is None:
        return None
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
    failures: list[LocalProviderProbeMockRunnerFailure],
    reason: str,
    field: str,
    message: str,
) -> None:
    failures.append(LocalProviderProbeMockRunnerFailure(reason=reason, field=field, message=message))
