from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping


LOCAL_PROVIDER_PROBE_WIRING_VERSION = "local-provider-health-probe-wiring-readiness/1"
LOCAL_PROVIDER_PROBE_WIRING_EXECUTION_PERMISSION = (
    "not_granted_by_local_provider_probe_wiring"
)

PROBE_WIRING_CLASSES = {
    "local_provider_metadata_probe_wiring",
    "local_model_list_probe_wiring",
    "mock_transport_probe_wiring",
    "api_route_readiness_future",
    "runtime_command_readiness_future",
    "scheduler_readiness_future",
    "unknown",
}

EXECUTION_MODE_CLASSES = {
    "metadata_only",
    "mock_transport_only",
    "dry_run_only",
    "future_live_localhost_probe",
    "blocked",
    "unknown",
}

TRANSPORT_CLASSES = {
    "no_transport",
    "injected_mock_transport",
    "future_httpx_localhost_transport",
    "future_requests_localhost_transport",
    "unsupported_real_transport",
    "unknown",
}

ENDPOINT_HOST_CLASSES = {"localhost", "loopback", "lan", "remote", "cloud", "unknown"}
LOCAL_ENDPOINT_HOST_CLASSES = {"localhost", "loopback"}
BLOCKED_ENDPOINT_HOST_CLASSES = {"lan", "remote", "cloud", "unknown"}

ENDPOINT_SCOPE_CLASSES = {
    "provider_root_metadata_candidate",
    "models_list_metadata_candidate",
    "health_metadata_candidate",
    "generation_blocked",
    "chat_completion_blocked",
    "completion_blocked",
    "embeddings_blocked",
    "rerank_blocked",
    "multimodal_blocked",
    "audio_blocked",
    "file_upload_blocked",
    "tool_call_blocked",
    "unknown",
}

BLOCKED_ENDPOINT_SCOPE_CLASSES = {
    "generation_blocked": "generation_endpoint_blocked",
    "chat_completion_blocked": "chat_completion_endpoint_blocked",
    "completion_blocked": "completion_endpoint_blocked",
    "embeddings_blocked": "embedding_endpoint_blocked",
    "rerank_blocked": "reranker_endpoint_blocked",
    "multimodal_blocked": "multimodal_endpoint_blocked",
    "audio_blocked": "audio_endpoint_blocked",
    "file_upload_blocked": "file_upload_endpoint_blocked",
    "tool_call_blocked": "tool_call_endpoint_blocked",
}

PAYLOAD_CLASSES = {
    "no_payload",
    "metadata_only_empty_request",
    "prompt_payload_blocked",
    "context_payload_blocked",
    "memory_payload_blocked",
    "repo_payload_blocked",
    "raw_journal_payload_blocked",
    "raw_evidence_payload_blocked",
    "secret_payload_blocked",
    "unknown",
}

BLOCKED_PAYLOAD_CLASSES = {
    "prompt_payload_blocked",
    "context_payload_blocked",
    "memory_payload_blocked",
    "repo_payload_blocked",
    "raw_journal_payload_blocked",
    "raw_evidence_payload_blocked",
    "secret_payload_blocked",
    "unknown",
}

SECRET_POLICY_CLASSES = {
    "no_secret",
    "no_authorization_header",
    "api_key_future_gated",
    "secret_read_blocked",
    "api_key_validation_blocked",
    "unknown",
}

TIMEOUT_POLICY_CLASSES = {
    "bounded_short_timeout",
    "bounded_medium_timeout",
    "missing_timeout",
    "excessive_timeout",
    "unknown",
}

CANCELLATION_POLICY_CLASSES = {
    "cancellation_supported_candidate",
    "cancellation_not_modeled",
    "missing_cancellation_policy",
    "unknown",
}

PROBE_RESULT_CLASSES = {
    "not_executed",
    "mock_success_metadata_candidate",
    "mock_timeout_negative_candidate",
    "mock_connection_refused_negative_candidate",
    "mock_invalid_response_negative_candidate",
    "mock_unauthorized_negative_candidate",
    "future_live_success_metadata_candidate",
    "future_live_negative_candidate",
    "unknown",
}

RUNTIME_API_READINESS_CLASSES = {
    "no_runtime_wiring",
    "api_contract_candidate",
    "runtime_command_contract_candidate",
    "requires_policy_gate",
    "requires_capability_lease_future",
    "requires_operator_approval_future",
    "blocked",
    "unknown",
}

FUTURE_WIRING_CLASSES = {
    "api_route_readiness_future",
    "runtime_command_readiness_future",
    "scheduler_readiness_future",
}

FUTURE_TRANSPORT_CLASSES = {
    "future_httpx_localhost_transport",
    "future_requests_localhost_transport",
}

NEGATIVE_MOCK_RESULTS = {
    "mock_timeout_negative_candidate",
    "mock_connection_refused_negative_candidate",
    "mock_invalid_response_negative_candidate",
    "mock_unauthorized_negative_candidate",
}

FORBIDDEN_TRUTHY_FIELDS = {
    "authority": "authority_must_be_false",
    "runtime_dispatch_allowed": "runtime_dispatch_not_allowed",
    "approval_grant": "approval_grant_not_allowed",
    "capability_grant": "capability_grant_not_allowed",
    "lease_grant": "lease_grant_not_allowed",
    "evidence_provided_by_probe_wiring": "probe_wiring_cannot_provide_evidence",
    "evidence_provided_by_probe": "probe_wiring_cannot_provide_evidence",
    "evidence_provided_by_probe_design": "probe_wiring_cannot_provide_evidence",
    "evidence_provided_by_provider_health": "probe_wiring_cannot_provide_evidence",
    "evidence_created": "probe_wiring_cannot_provide_evidence",
    "verifier_success": "probe_wiring_cannot_mark_verifier_success",
    "verified_success": "probe_wiring_cannot_mark_verifier_success",
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
    "negative_mock_result_is_runtime_failure": "negative_mock_runtime_failure_claim_denied",
    "self_reported_identity_is_authority": "self_reported_identity_authority_denied",
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
class LocalProviderProbeWiringFailure:
    reason: str
    field: str
    message: str


@dataclass(frozen=True)
class LocalProviderProbeWiringInput:
    request_id: str | None
    probe_wiring_class: str | None
    execution_mode_class: str | None
    transport_class: str | None
    endpoint_host_class: str | None
    endpoint_scope_class: str | None
    payload_class: str | None
    secret_policy_class: str | None
    timeout_policy_class: str | None
    cancellation_policy_class: str | None
    probe_result_class: str | None
    runtime_api_readiness_class: str | None
    namespace: str | None
    source_refs: tuple[Mapping[str, Any], ...]
    provenance: tuple[Mapping[str, Any], ...]
    limitations: tuple[str, ...]
    unknowns: tuple[str, ...]


@dataclass(frozen=True)
class RelatedLocalProviderProbeWiringReference:
    label: str
    observed_status: str | None
    reference_only: bool = True
    authority: bool = False
    implementation_claim: bool = False


@dataclass(frozen=True)
class LocalProviderProbeWiringDecision:
    contract_version: str
    wiring_readiness_status: str
    request_id: str | None
    probe_wiring_class: str | None
    execution_mode_class: str | None
    transport_class: str | None
    endpoint_host_class: str | None
    endpoint_scope_class: str | None
    payload_class: str | None
    secret_policy_class: str | None
    timeout_policy_class: str | None
    cancellation_policy_class: str | None
    probe_result_class: str | None
    runtime_api_readiness_class: str | None
    namespace: str | None
    wiring_classification: str
    transport_classification: str
    endpoint_classification: str
    payload_classification: str
    secret_classification: str
    timeout_classification: str
    cancellation_classification: str
    probe_result_classification: str
    truthfulness_classification: str
    runtime_api_classification: str
    required_future_gates: tuple[str, ...]
    related_references: tuple[RelatedLocalProviderProbeWiringReference, ...]
    failure_reasons: tuple[str, ...]
    failures: tuple[LocalProviderProbeWiringFailure, ...]
    probe_input: LocalProviderProbeWiringInput | None
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = LOCAL_PROVIDER_PROBE_WIRING_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_probe_wiring: bool = False
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


def validate_local_provider_probe_wiring_request(
    request: Mapping[str, Any] | None,
    *,
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
) -> LocalProviderProbeWiringDecision:
    """Validate local provider probe wiring readiness without runtime wiring."""

    if not isinstance(request, Mapping):
        failure = LocalProviderProbeWiringFailure(
            reason="missing_request",
            field="request",
            message="local provider probe wiring requires caller-supplied metadata",
        )
        return _decision(probe_input=None, related_references=(), failures=(failure,))

    data = deepcopy(dict(request))
    failures: list[LocalProviderProbeWiringFailure] = []
    related_references: list[RelatedLocalProviderProbeWiringReference] = []

    _validate_forbidden_claims("request", data, failures)
    for label, decision in {
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

    probe_input = LocalProviderProbeWiringInput(
        request_id=_text(data.get("request_id")),
        probe_wiring_class=_text(data.get("probe_wiring_class")),
        execution_mode_class=_text(data.get("execution_mode_class")),
        transport_class=_text(data.get("transport_class")),
        endpoint_host_class=_text(data.get("endpoint_host_class")),
        endpoint_scope_class=_text(data.get("endpoint_scope_class")),
        payload_class=_text(data.get("payload_class")),
        secret_policy_class=_text(data.get("secret_policy_class")),
        timeout_policy_class=_text(data.get("timeout_policy_class")),
        cancellation_policy_class=_text(data.get("cancellation_policy_class")),
        probe_result_class=_text(data.get("probe_result_class", "not_executed")),
        runtime_api_readiness_class=_text(data.get("runtime_api_readiness_class", "no_runtime_wiring")),
        namespace=_text(data.get("namespace")),
        source_refs=_mapping_tuple(data.get("source_refs")),
        provenance=_mapping_tuple(data.get("provenance")),
        limitations=_text_tuple(data.get("limitations")),
        unknowns=_text_tuple(data.get("unknowns")),
    )

    _validate_required(probe_input, failures)
    _validate_wiring_and_transport(probe_input, failures)
    _validate_host_and_endpoint(probe_input, failures)
    _validate_payload_secret_timeout_cancellation(probe_input, failures)
    _validate_probe_result(probe_input, failures)
    _validate_truthfulness(data, failures)

    return _decision(
        probe_input=probe_input,
        related_references=tuple(related_references),
        failures=tuple(failures),
    )


def _decision(
    *,
    probe_input: LocalProviderProbeWiringInput | None,
    related_references: tuple[RelatedLocalProviderProbeWiringReference, ...],
    failures: tuple[LocalProviderProbeWiringFailure, ...],
) -> LocalProviderProbeWiringDecision:
    future_gates = _future_gates(probe_input, failures)
    return LocalProviderProbeWiringDecision(
        contract_version=LOCAL_PROVIDER_PROBE_WIRING_VERSION,
        wiring_readiness_status=_wiring_readiness_status(probe_input, failures, future_gates),
        request_id=probe_input.request_id if probe_input else None,
        probe_wiring_class=probe_input.probe_wiring_class if probe_input else None,
        execution_mode_class=probe_input.execution_mode_class if probe_input else None,
        transport_class=probe_input.transport_class if probe_input else None,
        endpoint_host_class=probe_input.endpoint_host_class if probe_input else None,
        endpoint_scope_class=probe_input.endpoint_scope_class if probe_input else None,
        payload_class=probe_input.payload_class if probe_input else None,
        secret_policy_class=probe_input.secret_policy_class if probe_input else None,
        timeout_policy_class=probe_input.timeout_policy_class if probe_input else None,
        cancellation_policy_class=probe_input.cancellation_policy_class if probe_input else None,
        probe_result_class=probe_input.probe_result_class if probe_input else None,
        runtime_api_readiness_class=probe_input.runtime_api_readiness_class if probe_input else None,
        namespace=probe_input.namespace if probe_input else None,
        wiring_classification=_wiring_classification(probe_input, failures, future_gates),
        transport_classification=_transport_classification(probe_input, failures, future_gates),
        endpoint_classification=_endpoint_classification(probe_input, failures),
        payload_classification=_payload_classification(probe_input, failures),
        secret_classification=_secret_classification(probe_input, failures),
        timeout_classification=_timeout_classification(probe_input, failures),
        cancellation_classification=_cancellation_classification(probe_input, failures),
        probe_result_classification=_probe_result_classification(probe_input, failures, future_gates),
        truthfulness_classification=_truthfulness_classification(probe_input, failures),
        runtime_api_classification=_runtime_api_classification(probe_input, failures, future_gates),
        required_future_gates=future_gates,
        related_references=related_references,
        failure_reasons=tuple(dict.fromkeys(f.reason for f in failures)),
        failures=failures,
        probe_input=probe_input,
    )


def _validate_required(
    probe_input: LocalProviderProbeWiringInput,
    failures: list[LocalProviderProbeWiringFailure],
) -> None:
    required = {
        "request_id": probe_input.request_id,
        "probe_wiring_class": probe_input.probe_wiring_class,
        "execution_mode_class": probe_input.execution_mode_class,
        "transport_class": probe_input.transport_class,
        "endpoint_host_class": probe_input.endpoint_host_class,
        "endpoint_scope_class": probe_input.endpoint_scope_class,
        "payload_class": probe_input.payload_class,
        "secret_policy_class": probe_input.secret_policy_class,
        "timeout_policy_class": probe_input.timeout_policy_class,
        "cancellation_policy_class": probe_input.cancellation_policy_class,
        "namespace": probe_input.namespace,
    }
    for field, value in required.items():
        if value is None or value == "":
            _add_failure(failures, f"missing_{field}", field, f"{field} is required")
    if not (probe_input.source_refs or probe_input.provenance):
        _add_failure(
            failures,
            "missing_source_refs_or_provenance",
            "source_refs",
            "source refs or provenance are required",
        )
    if probe_input.probe_wiring_class and probe_input.probe_wiring_class not in PROBE_WIRING_CLASSES:
        _add_failure(failures, "unsupported_probe_wiring_class", "probe_wiring_class", "probe wiring class is not recognized")
    if probe_input.execution_mode_class and probe_input.execution_mode_class not in EXECUTION_MODE_CLASSES:
        _add_failure(failures, "unsupported_execution_mode_class", "execution_mode_class", "execution mode class is not recognized")
    if probe_input.transport_class and probe_input.transport_class not in TRANSPORT_CLASSES:
        _add_failure(failures, "unsupported_transport_class", "transport_class", "transport class is not recognized")
    if probe_input.endpoint_host_class and probe_input.endpoint_host_class not in ENDPOINT_HOST_CLASSES:
        _add_failure(failures, "unsupported_endpoint_host_class", "endpoint_host_class", "endpoint host class is not recognized")
    if probe_input.endpoint_scope_class and probe_input.endpoint_scope_class not in ENDPOINT_SCOPE_CLASSES:
        _add_failure(failures, "unsupported_endpoint_scope_class", "endpoint_scope_class", "endpoint scope class is not recognized")
    if probe_input.payload_class and probe_input.payload_class not in PAYLOAD_CLASSES:
        _add_failure(failures, "unsupported_payload_class", "payload_class", "payload class is not recognized")
    if probe_input.secret_policy_class and probe_input.secret_policy_class not in SECRET_POLICY_CLASSES:
        _add_failure(failures, "unsupported_secret_policy_class", "secret_policy_class", "secret policy class is not recognized")
    if probe_input.timeout_policy_class and probe_input.timeout_policy_class not in TIMEOUT_POLICY_CLASSES:
        _add_failure(failures, "unsupported_timeout_policy_class", "timeout_policy_class", "timeout policy class is not recognized")
    if probe_input.cancellation_policy_class and probe_input.cancellation_policy_class not in CANCELLATION_POLICY_CLASSES:
        _add_failure(failures, "unsupported_cancellation_policy_class", "cancellation_policy_class", "cancellation policy class is not recognized")
    if probe_input.probe_result_class and probe_input.probe_result_class not in PROBE_RESULT_CLASSES:
        _add_failure(failures, "unsupported_probe_result_class", "probe_result_class", "probe result class is not recognized")
    if probe_input.runtime_api_readiness_class and probe_input.runtime_api_readiness_class not in RUNTIME_API_READINESS_CLASSES:
        _add_failure(failures, "unsupported_runtime_api_readiness_class", "runtime_api_readiness_class", "runtime/API readiness class is not recognized")


def _validate_wiring_and_transport(
    probe_input: LocalProviderProbeWiringInput,
    failures: list[LocalProviderProbeWiringFailure],
) -> None:
    if probe_input.probe_wiring_class == "unknown":
        _add_failure(failures, "unknown_probe_wiring_blocked", "probe_wiring_class", "unknown probe wiring is blocked")
    if probe_input.execution_mode_class in {"blocked", "unknown"}:
        _add_failure(failures, "execution_mode_blocked", "execution_mode_class", "blocked or unknown execution mode is not a candidate")
    if probe_input.transport_class in {"unsupported_real_transport", "unknown"}:
        _add_failure(failures, "unsupported_real_transport_blocked", "transport_class", "real or unknown transport is blocked")
    if probe_input.transport_class == "injected_mock_transport" and probe_input.execution_mode_class != "mock_transport_only":
        _add_failure(failures, "mock_transport_requires_mock_mode", "execution_mode_class", "injected mock transport is allowed only in mock transport mode")
    if probe_input.transport_class == "no_transport" and probe_input.execution_mode_class not in {"metadata_only", "dry_run_only"}:
        _add_failure(failures, "no_transport_cannot_execute", "transport_class", "no transport means no execution")
    if probe_input.runtime_api_readiness_class == "blocked":
        _add_failure(failures, "runtime_api_readiness_blocked", "runtime_api_readiness_class", "runtime/API readiness metadata is blocked")
    if probe_input.runtime_api_readiness_class == "unknown":
        _add_failure(failures, "runtime_api_readiness_unknown", "runtime_api_readiness_class", "runtime/API readiness metadata is unknown")


def _validate_host_and_endpoint(
    probe_input: LocalProviderProbeWiringInput,
    failures: list[LocalProviderProbeWiringFailure],
) -> None:
    if probe_input.endpoint_host_class in BLOCKED_ENDPOINT_HOST_CLASSES:
        _add_failure(failures, "blocked_by_host", "endpoint_host_class", "only localhost or loopback endpoint host classes are allowed")
    scope = probe_input.endpoint_scope_class
    if scope in BLOCKED_ENDPOINT_SCOPE_CLASSES:
        _add_failure(failures, BLOCKED_ENDPOINT_SCOPE_CLASSES[scope], "endpoint_scope_class", "generation, embedding, reranker, multimodal, audio, upload, and tool endpoint scopes are blocked")
    if scope == "unknown":
        _add_failure(failures, "unknown_endpoint_scope_blocked", "endpoint_scope_class", "unknown endpoint scope is blocked or future-gated")


def _validate_payload_secret_timeout_cancellation(
    probe_input: LocalProviderProbeWiringInput,
    failures: list[LocalProviderProbeWiringFailure],
) -> None:
    if probe_input.payload_class in BLOCKED_PAYLOAD_CLASSES:
        _add_failure(failures, "blocked_by_payload", "payload_class", "only no-payload or metadata-only empty request classes are allowed")
    if probe_input.secret_policy_class in {"secret_read_blocked", "api_key_validation_blocked", "unknown"}:
        _add_failure(failures, "blocked_by_secret_policy", "secret_policy_class", "secret reads, API key validation, and unknown secret policy are blocked")
    if probe_input.secret_policy_class == "api_key_future_gated":
        _add_failure(failures, "api_key_future_gated_not_allowed_now", "secret_policy_class", "API key handling is future-gated and not allowed now")
    if probe_input.timeout_policy_class in {"missing_timeout", "unknown"}:
        _add_failure(failures, "missing_timeout_policy", "timeout_policy_class", "bounded timeout policy is required")
    if probe_input.timeout_policy_class == "excessive_timeout":
        _add_failure(failures, "excessive_timeout_policy", "timeout_policy_class", "excessive timeout policy is blocked")
    if probe_input.cancellation_policy_class in {"missing_cancellation_policy", "unknown"}:
        _add_failure(failures, "missing_cancellation_policy", "cancellation_policy_class", "explicit cancellation policy metadata is required")


def _validate_probe_result(
    probe_input: LocalProviderProbeWiringInput,
    failures: list[LocalProviderProbeWiringFailure],
) -> None:
    result = probe_input.probe_result_class
    if result == "unknown":
        _add_failure(failures, "unknown_probe_result_blocked", "probe_result_class", "unknown probe result metadata is blocked")
    if result in {"future_live_success_metadata_candidate", "future_live_negative_candidate"}:
        _add_failure(failures, "future_live_result_not_allowed_now", "probe_result_class", "future live result metadata cannot be claimed in this sprint")
    if result == "mock_success_metadata_candidate" and probe_input.transport_class != "injected_mock_transport":
        _add_failure(failures, "mock_success_requires_mock_transport", "transport_class", "mock success metadata requires injected mock transport")
    if result in NEGATIVE_MOCK_RESULTS and probe_input.transport_class != "injected_mock_transport":
        _add_failure(failures, "negative_mock_requires_mock_transport", "transport_class", "negative mock result metadata requires injected mock transport")


def _validate_truthfulness(data: Mapping[str, Any], failures: list[LocalProviderProbeWiringFailure]) -> None:
    proof_fields = {
        "provider_metadata_is_truth": "provider_metadata_truth_claim_denied",
        "model_list_is_truth": "model_list_truth_claim_denied",
        "mock_success_is_health_proof": "mock_success_health_proof_denied",
        "negative_mock_result_is_runtime_failure": "negative_mock_runtime_failure_claim_denied",
        "provider_health_is_proof": "provider_health_proof_denied",
        "model_availability_is_execution_ready": "model_availability_execution_ready_claim_denied",
        "probe_candidate_selects_auto_mode": "auto_mode_selection_claim_denied",
        "quality_or_benchmark_verified": "benchmark_verification_denied",
        "self_reported_identity_is_authority": "self_reported_identity_authority_denied",
        "model_inventory_proves_availability": "model_inventory_availability_proof_denied",
    }
    for field, reason in proof_fields.items():
        if _truthy(data.get(field)):
            _add_failure(failures, reason, field, "probe wiring metadata cannot become truth, proof, runtime failure, model availability, benchmark, identity, or Auto Mode selection")


def _validate_related_decision(
    label: str,
    decision: Any | None,
    failures: list[LocalProviderProbeWiringFailure],
    related_references: list[RelatedLocalProviderProbeWiringReference],
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
            f"{label} cannot authorize probe execution, runtime/API wiring, model calls, payload transfer, evidence, verifier success, or grants",
        )
    related_references.append(
        RelatedLocalProviderProbeWiringReference(
            label=label,
            observed_status=_related_status(decision),
            implementation_claim=len(failures) > before,
        )
    )


def _validate_forbidden_claims(
    label: str,
    source: Any,
    failures: list[LocalProviderProbeWiringFailure],
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
                f"{label} cannot add runtime/API surfaces, perform probes, HTTP/socket behavior, model behavior, payload transfer, auth, secret reads, external calls, or runtime mutations",
            )
    execution_permission = _field_value(source, "execution_permission")
    if execution_permission not in (None, "", LOCAL_PROVIDER_PROBE_WIRING_EXECUTION_PERMISSION):
        permission_text = str(execution_permission)
        if not permission_text.startswith("not_granted"):
            _add_failure(failures, "execution_permission_claim_denied", f"{label}.execution_permission", "local provider probe wiring cannot grant execution permission")


def _wiring_readiness_status(
    probe_input: LocalProviderProbeWiringInput | None,
    failures: tuple[LocalProviderProbeWiringFailure, ...],
    future_gates: tuple[str, ...],
) -> str:
    if probe_input is None:
        return "blocked_by_missing_required_field"
    reasons = {failure.reason for failure in failures}
    if not reasons:
        if future_gates:
            return "future_gated"
        if probe_input.execution_mode_class == "mock_transport_only":
            return "mock_transport_candidate"
        return "wiring_readiness_candidate"
    if "unsafe_related_decision" in reasons:
        return "blocked_by_policy"
    if any(reason.startswith("missing_") or reason.startswith("unsupported_") for reason in reasons):
        return "blocked_by_missing_required_field"
    if "blocked_by_host" in reasons:
        return "blocked_by_host"
    if any("endpoint" in reason or "generation" in reason or "completion" in reason or "embedding" in reason or "reranker" in reason or "multimodal" in reason or "audio" in reason or "file_upload" in reason or "tool_call" in reason for reason in reasons):
        return "blocked_by_endpoint_scope"
    if any("payload" in reason for reason in reasons):
        return "blocked_by_payload"
    if any("secret" in reason or "auth" in reason or "api_key" in reason for reason in reasons):
        return "blocked_by_secret_policy"
    if any("timeout" in reason for reason in reasons):
        return "blocked_by_timeout_policy"
    if any("cancellation" in reason for reason in reasons):
        return "blocked_by_cancellation_policy"
    if any("transport" in reason for reason in reasons):
        return "blocked_by_transport"
    if any("proof" in reason or "truth" in reason or "verification" in reason or "availability" in reason or "identity" in reason or "benchmark" in reason for reason in reasons):
        return "blocked_by_truthfulness_claim"
    return "blocked_by_policy"


def _future_gates(
    probe_input: LocalProviderProbeWiringInput | None,
    failures: tuple[LocalProviderProbeWiringFailure, ...],
) -> tuple[str, ...]:
    if probe_input is None or failures:
        return ()
    gates: list[str] = []
    if probe_input.probe_wiring_class in FUTURE_WIRING_CLASSES:
        gates.append(f"{probe_input.probe_wiring_class}_requires_future_runtime_boundary")
    if probe_input.execution_mode_class == "future_live_localhost_probe":
        gates.append("future_live_localhost_probe_requires_explicit_runtime_gate")
    if probe_input.transport_class in FUTURE_TRANSPORT_CLASSES:
        gates.append(f"{probe_input.transport_class}_requires_future_injected_client")
    if probe_input.runtime_api_readiness_class in {
        "api_contract_candidate",
        "runtime_command_contract_candidate",
        "requires_policy_gate",
        "requires_capability_lease_future",
        "requires_operator_approval_future",
    }:
        gates.append(f"{probe_input.runtime_api_readiness_class}_requires_future_boundary")
    return tuple(dict.fromkeys(gates))


def _wiring_classification(
    probe_input: LocalProviderProbeWiringInput | None,
    failures: tuple[LocalProviderProbeWiringFailure, ...],
    future_gates: tuple[str, ...],
) -> str:
    if probe_input is None or failures:
        return "blocked"
    if future_gates:
        return "future_gated_not_executed"
    return "readiness_metadata_only"


def _transport_classification(
    probe_input: LocalProviderProbeWiringInput | None,
    failures: tuple[LocalProviderProbeWiringFailure, ...],
    future_gates: tuple[str, ...],
) -> str:
    if probe_input is None or failures:
        return "blocked"
    if probe_input.transport_class == "injected_mock_transport":
        return "mock_transport_metadata_only"
    if probe_input.transport_class == "no_transport":
        return "no_transport_no_execution"
    if future_gates:
        return "future_localhost_transport_not_executed"
    return "transport_metadata_only"


def _endpoint_classification(
    probe_input: LocalProviderProbeWiringInput | None,
    failures: tuple[LocalProviderProbeWiringFailure, ...],
) -> str:
    if probe_input is None or failures:
        return "blocked"
    if probe_input.endpoint_scope_class == "models_list_metadata_candidate":
        return "models_list_candidate_not_availability_proof"
    return "metadata_endpoint_candidate_only"


def _payload_classification(
    probe_input: LocalProviderProbeWiringInput | None,
    failures: tuple[LocalProviderProbeWiringFailure, ...],
) -> str:
    if probe_input is None or failures:
        return "blocked"
    return "no_payload_or_metadata_empty_request_only"


def _secret_classification(
    probe_input: LocalProviderProbeWiringInput | None,
    failures: tuple[LocalProviderProbeWiringFailure, ...],
) -> str:
    if probe_input is None or failures:
        return "blocked"
    return "no_secret_no_authorization_no_api_key_validation"


def _timeout_classification(
    probe_input: LocalProviderProbeWiringInput | None,
    failures: tuple[LocalProviderProbeWiringFailure, ...],
) -> str:
    if probe_input is None or failures:
        return "blocked"
    return "bounded_timeout_metadata_only"


def _cancellation_classification(
    probe_input: LocalProviderProbeWiringInput | None,
    failures: tuple[LocalProviderProbeWiringFailure, ...],
) -> str:
    if probe_input is None or failures:
        return "blocked"
    if probe_input.cancellation_policy_class == "cancellation_not_modeled":
        return "cancellation_not_modeled_requires_future_review"
    return "cancellation_supported_candidate"


def _probe_result_classification(
    probe_input: LocalProviderProbeWiringInput | None,
    failures: tuple[LocalProviderProbeWiringFailure, ...],
    future_gates: tuple[str, ...],
) -> str:
    if probe_input is None or failures:
        return "blocked"
    result = probe_input.probe_result_class
    if result in NEGATIVE_MOCK_RESULTS:
        return "negative_mock_candidate_metadata_only_not_runtime_failure"
    if result == "mock_success_metadata_candidate":
        return "mock_success_metadata_only_not_health_proof"
    if future_gates:
        return "future_result_not_executed"
    return "not_executed"


def _truthfulness_classification(
    probe_input: LocalProviderProbeWiringInput | None,
    failures: tuple[LocalProviderProbeWiringFailure, ...],
) -> str:
    if probe_input is None or failures:
        return "blocked"
    return "metadata_and_mock_results_not_health_model_or_benchmark_proof"


def _runtime_api_classification(
    probe_input: LocalProviderProbeWiringInput | None,
    failures: tuple[LocalProviderProbeWiringFailure, ...],
    future_gates: tuple[str, ...],
) -> str:
    if probe_input is None or failures:
        return "blocked"
    if future_gates:
        return "future_runtime_api_contract_not_added"
    return "no_runtime_api_wiring_added"


def _related_status(decision: Any) -> str | None:
    for field in (
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
    failures: list[LocalProviderProbeWiringFailure],
    reason: str,
    field: str,
    message: str,
) -> None:
    failures.append(LocalProviderProbeWiringFailure(reason=reason, field=field, message=message))
