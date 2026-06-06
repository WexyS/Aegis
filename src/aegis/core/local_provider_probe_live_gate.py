from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping


LOCAL_PROVIDER_PROBE_LIVE_GATE_VERSION = "local-provider-health-probe-live-gate/1"
LOCAL_PROVIDER_PROBE_LIVE_GATE_EXECUTION_PERMISSION = (
    "not_granted_by_local_provider_probe_live_gate"
)

LIVE_GATE_CLASSES = {
    "localhost_metadata_probe_gate",
    "localhost_model_list_probe_gate",
    "localhost_health_metadata_probe_gate",
    "live_probe_rollout_gate",
    "operator_review_gate",
    "evidence_semantics_gate",
    "verifier_semantics_gate",
    "blocked",
    "unknown",
}

LIVE_GATE_STATUS_CLASSES = {
    "design_gate_ready_metadata_only",
    "requires_policy_gate",
    "requires_operator_review",
    "requires_capability_lease_future",
    "requires_timeout_cancellation",
    "requires_negative_evidence_semantics",
    "requires_redaction_policy",
    "requires_result_classifier",
    "requires_mock_runner",
    "blocked_by_missing_boundary",
    "blocked_by_missing_wiring",
    "blocked_by_missing_mock_runner",
    "blocked_by_host",
    "blocked_by_endpoint",
    "blocked_by_payload",
    "blocked_by_secret_policy",
    "future_gated",
    "unknown",
}

FUTURE_LIVE_TRANSPORT_CLASSES = {
    "no_transport",
    "future_injected_http_client",
    "future_httpx_localhost_only",
    "future_requests_localhost_only",
    "blocked_real_transport",
    "unknown",
}

ENDPOINT_HOST_CLASSES = {"localhost", "loopback", "lan", "remote", "cloud", "unknown"}
BLOCKED_ENDPOINT_HOST_CLASSES = {"lan", "remote", "cloud", "unknown"}

ENDPOINT_SCOPE_CLASSES = {
    "provider_root_metadata_future",
    "models_list_metadata_future",
    "health_metadata_future",
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

BLOCKED_ENDPOINT_SCOPE_REASONS = {
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

PAYLOAD_POLICY_CLASSES = {
    "no_payload",
    "empty_metadata_request_only",
    "prompt_payload_blocked",
    "context_payload_blocked",
    "memory_payload_blocked",
    "repo_payload_blocked",
    "raw_journal_payload_blocked",
    "raw_evidence_payload_blocked",
    "secret_payload_blocked",
    "unknown",
}

BLOCKED_PAYLOAD_POLICY_CLASSES = {
    "prompt_payload_blocked",
    "context_payload_blocked",
    "memory_payload_blocked",
    "repo_payload_blocked",
    "raw_journal_payload_blocked",
    "raw_evidence_payload_blocked",
    "secret_payload_blocked",
    "unknown",
}

LOGGING_REDACTION_CLASSES = {
    "no_payload_logging",
    "endpoint_only_redacted",
    "status_code_only_future",
    "response_shape_only_future",
    "response_body_logging_blocked",
    "secret_logging_blocked",
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

FUTURE_RESULT_CLASSES = {
    "future_metadata_success_candidate",
    "future_model_list_candidate",
    "future_timeout_negative_candidate",
    "future_connection_refused_negative_candidate",
    "future_invalid_response_negative_candidate",
    "future_unauthorized_negative_candidate",
    "future_unsupported_endpoint_negative_candidate",
    "future_cancelled_negative_candidate",
    "not_executed",
    "unknown",
}

NEGATIVE_FUTURE_RESULTS = {
    "future_timeout_negative_candidate",
    "future_connection_refused_negative_candidate",
    "future_invalid_response_negative_candidate",
    "future_unauthorized_negative_candidate",
    "future_unsupported_endpoint_negative_candidate",
    "future_cancelled_negative_candidate",
}

BLOCKED_STATUS_REASONS = {
    "blocked_by_missing_boundary": "missing_probe_boundary_reference",
    "blocked_by_missing_wiring": "missing_probe_wiring_reference",
    "blocked_by_missing_mock_runner": "missing_mock_runner_reference",
    "blocked_by_host": "blocked_by_host",
    "blocked_by_endpoint": "blocked_by_endpoint_scope",
    "blocked_by_payload": "blocked_by_payload",
    "blocked_by_secret_policy": "blocked_by_secret_policy",
}

FUTURE_GATE_STATUS_CLASSES = {
    "requires_policy_gate",
    "requires_operator_review",
    "requires_capability_lease_future",
    "requires_timeout_cancellation",
    "requires_negative_evidence_semantics",
    "requires_redaction_policy",
    "requires_result_classifier",
    "requires_mock_runner",
    "future_gated",
}

FORBIDDEN_TRUTHY_FIELDS = {
    "authority": "authority_must_be_false",
    "runtime_dispatch_allowed": "runtime_dispatch_not_allowed",
    "approval_grant": "approval_grant_not_allowed",
    "capability_grant": "capability_grant_not_allowed",
    "lease_grant": "lease_grant_not_allowed",
    "evidence_provided_by_live_gate": "live_gate_cannot_provide_evidence",
    "evidence_provided_by_mock_probe": "live_gate_cannot_provide_evidence",
    "evidence_created": "live_gate_cannot_provide_evidence",
    "verifier_success": "live_gate_cannot_mark_verifier_success",
    "verified_success": "live_gate_cannot_mark_verifier_success",
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
    "future_result_is_provider_health_proof": "future_result_health_proof_denied",
    "future_model_list_is_availability_proof": "future_model_list_availability_proof_denied",
    "future_negative_result_is_runtime_failure": "future_negative_runtime_failure_claim_denied",
    "provider_metadata_is_truth": "provider_metadata_truth_claim_denied",
    "model_list_is_truth": "model_list_truth_claim_denied",
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
    "live_probe_performed": "live_probe_execution_denied",
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
    "response_body_logged": "response_body_logging_denied",
    "secret_logged": "secret_logging_denied",
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
class LocalProviderProbeLiveGateFailure:
    reason: str
    field: str
    message: str


@dataclass(frozen=True)
class LocalProviderProbeLiveGateInput:
    request_id: str | None
    live_gate_class: str | None
    live_gate_status_class: str | None
    future_live_transport_class: str | None
    endpoint_host_class: str | None
    endpoint_scope_class: str | None
    payload_policy_class: str | None
    logging_redaction_class: str | None
    timeout_policy_class: str | None
    cancellation_policy_class: str | None
    future_result_class: str | None
    namespace: str | None
    source_refs: tuple[Mapping[str, Any], ...]
    provenance: tuple[Mapping[str, Any], ...]
    paired_probe_boundary_ref: str | None
    paired_probe_wiring_ref: str | None
    paired_mock_runner_ref: str | None
    limitations: tuple[str, ...]
    unknowns: tuple[str, ...]


@dataclass(frozen=True)
class RelatedLocalProviderProbeLiveGateReference:
    label: str
    observed_status: str | None
    reference_only: bool = True
    authority: bool = False
    implementation_claim: bool = False


@dataclass(frozen=True)
class LocalProviderProbeLiveGateDecision:
    contract_version: str
    live_gate_status: str
    request_id: str | None
    live_gate_class: str | None
    live_gate_status_class: str | None
    future_live_transport_class: str | None
    endpoint_host_class: str | None
    endpoint_scope_class: str | None
    payload_policy_class: str | None
    logging_redaction_class: str | None
    timeout_policy_class: str | None
    cancellation_policy_class: str | None
    future_result_class: str | None
    namespace: str | None
    live_gate_classification: str
    transport_classification: str
    endpoint_classification: str
    payload_classification: str
    logging_classification: str
    timeout_classification: str
    cancellation_classification: str
    future_result_classification: str
    truthfulness_classification: str
    related_references: tuple[RelatedLocalProviderProbeLiveGateReference, ...]
    required_future_gates: tuple[str, ...]
    failure_reasons: tuple[str, ...]
    failures: tuple[LocalProviderProbeLiveGateFailure, ...]
    probe_input: LocalProviderProbeLiveGateInput | None
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = LOCAL_PROVIDER_PROBE_LIVE_GATE_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_live_gate: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    frontend_authority: bool = False
    api_route_added: bool = False
    runtime_command_added: bool = False
    scheduler_added: bool = False
    live_probe_performed: bool = False
    real_endpoint_probed: bool = False
    socket_opened: bool = False
    http_request_performed: bool = False
    provider_probed: bool = False
    real_transport_used: bool = False
    mock_transport_only: bool = False
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
    response_body_logged: bool = False
    secret_logged: bool = False
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


def validate_local_provider_probe_live_gate_request(
    request: Mapping[str, Any] | None,
    *,
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
) -> LocalProviderProbeLiveGateDecision:
    """Validate live localhost probe design gate metadata without probing."""

    if not isinstance(request, Mapping):
        failure = LocalProviderProbeLiveGateFailure(
            reason="missing_request",
            field="request",
            message="local provider live gate requires caller-supplied metadata",
        )
        return _decision(probe_input=None, related_references=(), failures=(failure,))

    data = deepcopy(dict(request))
    failures: list[LocalProviderProbeLiveGateFailure] = []
    related_references: list[RelatedLocalProviderProbeLiveGateReference] = []

    _validate_forbidden_claims("request", data, failures)
    for label, decision in {
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

    probe_input = LocalProviderProbeLiveGateInput(
        request_id=_text(data.get("request_id")),
        live_gate_class=_text(data.get("live_gate_class")),
        live_gate_status_class=_text(data.get("live_gate_status_class")),
        future_live_transport_class=_text(data.get("future_live_transport_class")),
        endpoint_host_class=_text(data.get("endpoint_host_class")),
        endpoint_scope_class=_text(data.get("endpoint_scope_class")),
        payload_policy_class=_text(data.get("payload_policy_class")),
        logging_redaction_class=_text(data.get("logging_redaction_class")),
        timeout_policy_class=_text(data.get("timeout_policy_class")),
        cancellation_policy_class=_text(data.get("cancellation_policy_class")),
        future_result_class=_text(data.get("future_result_class")),
        namespace=_text(data.get("namespace")),
        source_refs=_mapping_tuple(data.get("source_refs")),
        provenance=_mapping_tuple(data.get("provenance")),
        paired_probe_boundary_ref=_text(data.get("paired_probe_boundary_ref")),
        paired_probe_wiring_ref=_text(data.get("paired_probe_wiring_ref")),
        paired_mock_runner_ref=_text(data.get("paired_mock_runner_ref")),
        limitations=_text_tuple(data.get("limitations")),
        unknowns=_text_tuple(data.get("unknowns")),
    )

    _validate_required(
        probe_input,
        failures,
        has_boundary_decision=local_provider_probe_boundary_decision is not None,
        has_wiring_decision=local_provider_probe_wiring_decision is not None,
        has_mock_runner_decision=local_provider_probe_mock_runner_decision is not None,
    )
    _validate_gate_metadata(probe_input, failures)
    _validate_transport_host_endpoint(probe_input, failures)
    _validate_payload_logging_timeout_cancellation(probe_input, failures)
    _validate_future_result(probe_input, failures)
    _validate_truthfulness(data, failures)

    return _decision(
        probe_input=probe_input,
        related_references=tuple(related_references),
        failures=tuple(failures),
    )


def _decision(
    *,
    probe_input: LocalProviderProbeLiveGateInput | None,
    related_references: tuple[RelatedLocalProviderProbeLiveGateReference, ...],
    failures: tuple[LocalProviderProbeLiveGateFailure, ...],
) -> LocalProviderProbeLiveGateDecision:
    future_gates = _future_gates(probe_input, failures)
    return LocalProviderProbeLiveGateDecision(
        contract_version=LOCAL_PROVIDER_PROBE_LIVE_GATE_VERSION,
        live_gate_status=_live_gate_status(probe_input, failures, future_gates),
        request_id=probe_input.request_id if probe_input else None,
        live_gate_class=probe_input.live_gate_class if probe_input else None,
        live_gate_status_class=probe_input.live_gate_status_class if probe_input else None,
        future_live_transport_class=probe_input.future_live_transport_class if probe_input else None,
        endpoint_host_class=probe_input.endpoint_host_class if probe_input else None,
        endpoint_scope_class=probe_input.endpoint_scope_class if probe_input else None,
        payload_policy_class=probe_input.payload_policy_class if probe_input else None,
        logging_redaction_class=probe_input.logging_redaction_class if probe_input else None,
        timeout_policy_class=probe_input.timeout_policy_class if probe_input else None,
        cancellation_policy_class=probe_input.cancellation_policy_class if probe_input else None,
        future_result_class=probe_input.future_result_class if probe_input else None,
        namespace=probe_input.namespace if probe_input else None,
        live_gate_classification=_live_gate_classification(probe_input, failures, future_gates),
        transport_classification=_transport_classification(probe_input, failures),
        endpoint_classification=_endpoint_classification(probe_input, failures),
        payload_classification=_payload_classification(probe_input, failures),
        logging_classification=_logging_classification(probe_input, failures),
        timeout_classification=_timeout_classification(probe_input, failures),
        cancellation_classification=_cancellation_classification(probe_input, failures),
        future_result_classification=_future_result_classification(probe_input, failures),
        truthfulness_classification=_truthfulness_classification(probe_input, failures),
        related_references=related_references,
        required_future_gates=future_gates,
        failure_reasons=tuple(dict.fromkeys(f.reason for f in failures)),
        failures=failures,
        probe_input=probe_input,
    )


def _validate_required(
    probe_input: LocalProviderProbeLiveGateInput,
    failures: list[LocalProviderProbeLiveGateFailure],
    *,
    has_boundary_decision: bool,
    has_wiring_decision: bool,
    has_mock_runner_decision: bool,
) -> None:
    required = {
        "request_id": probe_input.request_id,
        "live_gate_class": probe_input.live_gate_class,
        "live_gate_status_class": probe_input.live_gate_status_class,
        "future_live_transport_class": probe_input.future_live_transport_class,
        "endpoint_host_class": probe_input.endpoint_host_class,
        "endpoint_scope_class": probe_input.endpoint_scope_class,
        "payload_policy_class": probe_input.payload_policy_class,
        "logging_redaction_class": probe_input.logging_redaction_class,
        "timeout_policy_class": probe_input.timeout_policy_class,
        "cancellation_policy_class": probe_input.cancellation_policy_class,
        "future_result_class": probe_input.future_result_class,
        "namespace": probe_input.namespace,
    }
    for field, value in required.items():
        if value is None or value == "":
            _add_failure(failures, f"missing_{field}", field, f"{field} is required")
    if not (probe_input.source_refs or probe_input.provenance):
        _add_failure(failures, "missing_source_refs_or_provenance", "source_refs", "source refs or provenance are required")
    if not (probe_input.paired_probe_boundary_ref or has_boundary_decision):
        _add_failure(failures, "missing_probe_boundary_reference", "paired_probe_boundary_ref", "paired probe boundary metadata or related decision is required")
    if not (probe_input.paired_probe_wiring_ref or has_wiring_decision):
        _add_failure(failures, "missing_probe_wiring_reference", "paired_probe_wiring_ref", "paired probe wiring metadata or related decision is required")
    if not (probe_input.paired_mock_runner_ref or has_mock_runner_decision):
        _add_failure(failures, "missing_mock_runner_reference", "paired_mock_runner_ref", "paired mock runner metadata or related decision is required")
    if probe_input.live_gate_class and probe_input.live_gate_class not in LIVE_GATE_CLASSES:
        _add_failure(failures, "unsupported_live_gate_class", "live_gate_class", "live gate class is not recognized")
    if probe_input.live_gate_status_class and probe_input.live_gate_status_class not in LIVE_GATE_STATUS_CLASSES:
        _add_failure(failures, "unsupported_live_gate_status_class", "live_gate_status_class", "live gate status class is not recognized")
    if probe_input.future_live_transport_class and probe_input.future_live_transport_class not in FUTURE_LIVE_TRANSPORT_CLASSES:
        _add_failure(failures, "unsupported_future_live_transport_class", "future_live_transport_class", "future live transport class is not recognized")
    if probe_input.endpoint_host_class and probe_input.endpoint_host_class not in ENDPOINT_HOST_CLASSES:
        _add_failure(failures, "unsupported_endpoint_host_class", "endpoint_host_class", "endpoint host class is not recognized")
    if probe_input.endpoint_scope_class and probe_input.endpoint_scope_class not in ENDPOINT_SCOPE_CLASSES:
        _add_failure(failures, "unsupported_endpoint_scope_class", "endpoint_scope_class", "endpoint scope class is not recognized")
    if probe_input.payload_policy_class and probe_input.payload_policy_class not in PAYLOAD_POLICY_CLASSES:
        _add_failure(failures, "unsupported_payload_policy_class", "payload_policy_class", "payload policy class is not recognized")
    if probe_input.logging_redaction_class and probe_input.logging_redaction_class not in LOGGING_REDACTION_CLASSES:
        _add_failure(failures, "unsupported_logging_redaction_class", "logging_redaction_class", "logging/redaction class is not recognized")
    if probe_input.timeout_policy_class and probe_input.timeout_policy_class not in TIMEOUT_POLICY_CLASSES:
        _add_failure(failures, "unsupported_timeout_policy_class", "timeout_policy_class", "timeout policy class is not recognized")
    if probe_input.cancellation_policy_class and probe_input.cancellation_policy_class not in CANCELLATION_POLICY_CLASSES:
        _add_failure(failures, "unsupported_cancellation_policy_class", "cancellation_policy_class", "cancellation policy class is not recognized")
    if probe_input.future_result_class and probe_input.future_result_class not in FUTURE_RESULT_CLASSES:
        _add_failure(failures, "unsupported_future_result_class", "future_result_class", "future result class is not recognized")


def _validate_gate_metadata(
    probe_input: LocalProviderProbeLiveGateInput,
    failures: list[LocalProviderProbeLiveGateFailure],
) -> None:
    if probe_input.live_gate_class in {"blocked", "unknown"}:
        _add_failure(failures, "live_gate_class_blocked", "live_gate_class", "blocked or unknown live gate class cannot be ready")
    status = probe_input.live_gate_status_class
    if status in BLOCKED_STATUS_REASONS:
        _add_failure(failures, BLOCKED_STATUS_REASONS[status], "live_gate_status_class", "blocked live gate status cannot be ready")
    if status == "unknown":
        _add_failure(failures, "unknown_live_gate_status_blocked", "live_gate_status_class", "unknown live gate status is blocked")


def _validate_transport_host_endpoint(
    probe_input: LocalProviderProbeLiveGateInput,
    failures: list[LocalProviderProbeLiveGateFailure],
) -> None:
    transport = probe_input.future_live_transport_class
    if transport in {"blocked_real_transport", "unknown"}:
        _add_failure(failures, "blocked_real_transport", "future_live_transport_class", "real or unknown live transport is blocked")
    if probe_input.endpoint_host_class in BLOCKED_ENDPOINT_HOST_CLASSES:
        _add_failure(failures, "blocked_by_host", "endpoint_host_class", "only localhost or loopback may be future live candidates")
    scope = probe_input.endpoint_scope_class
    if scope in BLOCKED_ENDPOINT_SCOPE_REASONS:
        _add_failure(failures, BLOCKED_ENDPOINT_SCOPE_REASONS[scope], "endpoint_scope_class", "generation, embedding, reranker, multimodal, audio, upload, and tool endpoint scopes are blocked")
    if scope == "unknown":
        _add_failure(failures, "unknown_endpoint_scope_blocked", "endpoint_scope_class", "unknown endpoint scope is blocked or future-gated")


def _validate_payload_logging_timeout_cancellation(
    probe_input: LocalProviderProbeLiveGateInput,
    failures: list[LocalProviderProbeLiveGateFailure],
) -> None:
    if probe_input.payload_policy_class in BLOCKED_PAYLOAD_POLICY_CLASSES:
        _add_failure(failures, "blocked_by_payload", "payload_policy_class", "only no-payload or empty metadata request policy is allowed")
    if probe_input.logging_redaction_class in {"response_body_logging_blocked", "secret_logging_blocked", "unknown"}:
        reason = "response_body_logging_denied" if probe_input.logging_redaction_class == "response_body_logging_blocked" else "secret_logging_denied"
        if probe_input.logging_redaction_class == "unknown":
            reason = "unknown_logging_redaction_blocked"
        _add_failure(failures, reason, "logging_redaction_class", "response body, secret, or unknown logging policy is blocked")
    if probe_input.timeout_policy_class in {"missing_timeout", "unknown"}:
        _add_failure(failures, "missing_timeout_policy", "timeout_policy_class", "bounded timeout policy is required")
    if probe_input.timeout_policy_class == "excessive_timeout":
        _add_failure(failures, "excessive_timeout_policy", "timeout_policy_class", "excessive timeout policy is blocked")
    if probe_input.cancellation_policy_class in {"missing_cancellation_policy", "unknown"}:
        _add_failure(failures, "missing_cancellation_policy", "cancellation_policy_class", "explicit cancellation policy metadata is required")


def _validate_future_result(
    probe_input: LocalProviderProbeLiveGateInput,
    failures: list[LocalProviderProbeLiveGateFailure],
) -> None:
    result = probe_input.future_result_class
    if result == "unknown":
        _add_failure(failures, "unknown_future_result_blocked", "future_result_class", "unknown future result metadata is blocked")
    if result == "future_model_list_candidate" and probe_input.endpoint_scope_class != "models_list_metadata_future":
        _add_failure(failures, "future_model_list_result_endpoint_mismatch", "endpoint_scope_class", "future model list result requires model-list endpoint metadata")
    if result == "future_metadata_success_candidate" and probe_input.endpoint_scope_class not in {"provider_root_metadata_future", "health_metadata_future"}:
        _add_failure(failures, "future_metadata_success_endpoint_mismatch", "endpoint_scope_class", "future metadata success requires provider root or health metadata endpoint")
    if result in NEGATIVE_FUTURE_RESULTS and probe_input.live_gate_status_class == "design_gate_ready_metadata_only":
        _add_failure(failures, "negative_result_requires_evidence_semantics_gate", "live_gate_status_class", "future negative results require negative evidence semantics gate")


def _validate_truthfulness(data: Mapping[str, Any], failures: list[LocalProviderProbeLiveGateFailure]) -> None:
    proof_fields = {
        "future_result_is_provider_health_proof": "future_result_health_proof_denied",
        "future_model_list_is_availability_proof": "future_model_list_availability_proof_denied",
        "future_negative_result_is_runtime_failure": "future_negative_runtime_failure_claim_denied",
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
            _add_failure(failures, reason, field, "live gate metadata cannot become proof, runtime failure, model availability, benchmark, identity, or Auto Mode selection")


def _validate_related_decision(
    label: str,
    decision: Any | None,
    failures: list[LocalProviderProbeLiveGateFailure],
    related_references: list[RelatedLocalProviderProbeLiveGateReference],
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
            f"{label} cannot authorize live probes, runtime/API wiring, model calls, payload transfer, evidence, verifier success, or grants",
        )
    related_references.append(
        RelatedLocalProviderProbeLiveGateReference(
            label=label,
            observed_status=_related_status(decision),
            implementation_claim=len(failures) > before,
        )
    )


def _validate_forbidden_claims(
    label: str,
    source: Any,
    failures: list[LocalProviderProbeLiveGateFailure],
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
                f"{label} cannot add runtime/API surfaces, perform live probes, HTTP/socket behavior, use real transport, perform model behavior, transfer payloads, authenticate, read secrets, log sensitive data, call external systems, or mutate runtime state",
            )
    execution_permission = _field_value(source, "execution_permission")
    if execution_permission not in (None, "", LOCAL_PROVIDER_PROBE_LIVE_GATE_EXECUTION_PERMISSION):
        permission_text = str(execution_permission)
        if not permission_text.startswith("not_granted"):
            _add_failure(failures, "execution_permission_claim_denied", f"{label}.execution_permission", "live gate cannot grant execution permission")


def _live_gate_status(
    probe_input: LocalProviderProbeLiveGateInput | None,
    failures: tuple[LocalProviderProbeLiveGateFailure, ...],
    future_gates: tuple[str, ...],
) -> str:
    if probe_input is None:
        return "unknown"
    reasons = {failure.reason for failure in failures}
    if not reasons:
        if future_gates:
            return "future_gated"
        return "design_gate_ready_metadata_only"
    if "unsafe_related_decision" in reasons:
        return "blocked_by_secret_policy"
    if "missing_probe_boundary_reference" in reasons:
        return "blocked_by_missing_boundary"
    if "missing_probe_wiring_reference" in reasons:
        return "blocked_by_missing_wiring"
    if "missing_mock_runner_reference" in reasons:
        return "blocked_by_missing_mock_runner"
    if any(reason.startswith("missing_") or reason.startswith("unsupported_") for reason in reasons):
        return "unknown"
    if any("live_probe" in reason or "probe_execution" in reason or "http" in reason or "socket" in reason or "transport" in reason or "model_" in reason or "generation" in reason or "reranking" in reason or "multimodal" in reason for reason in reasons):
        return "blocked_by_endpoint"
    if "blocked_by_host" in reasons:
        return "blocked_by_host"
    if any("endpoint" in reason or "generation" in reason or "completion" in reason or "embedding" in reason or "reranker" in reason or "multimodal" in reason or "audio" in reason or "file_upload" in reason or "tool_call" in reason for reason in reasons):
        return "blocked_by_endpoint"
    if any("payload" in reason for reason in reasons):
        return "blocked_by_payload"
    if any("secret" in reason or "auth" in reason or "api_key" in reason for reason in reasons):
        return "blocked_by_secret_policy"
    if any("timeout" in reason for reason in reasons):
        return "requires_timeout_cancellation"
    if any("cancellation" in reason for reason in reasons):
        return "requires_timeout_cancellation"
    if any("logging" in reason for reason in reasons):
        return "requires_redaction_policy"
    return "unknown"


def _future_gates(
    probe_input: LocalProviderProbeLiveGateInput | None,
    failures: tuple[LocalProviderProbeLiveGateFailure, ...],
) -> tuple[str, ...]:
    if probe_input is None or failures:
        return ()
    gates: list[str] = []
    if probe_input.live_gate_status_class in FUTURE_GATE_STATUS_CLASSES:
        gates.append(f"{probe_input.live_gate_status_class}_requires_future_gate")
    if probe_input.live_gate_class in {"live_probe_rollout_gate", "operator_review_gate", "evidence_semantics_gate", "verifier_semantics_gate"}:
        gates.append(f"{probe_input.live_gate_class}_requires_future_review")
    if probe_input.future_live_transport_class in {"future_injected_http_client", "future_httpx_localhost_only", "future_requests_localhost_only"}:
        gates.append(f"{probe_input.future_live_transport_class}_requires_future_injected_transport")
    if probe_input.future_result_class in NEGATIVE_FUTURE_RESULTS:
        gates.append("future_negative_result_requires_evidence_semantics")
    return tuple(dict.fromkeys(gates))


def _live_gate_classification(
    probe_input: LocalProviderProbeLiveGateInput | None,
    failures: tuple[LocalProviderProbeLiveGateFailure, ...],
    future_gates: tuple[str, ...],
) -> str:
    if probe_input is None or failures:
        return "blocked"
    if future_gates:
        return "future_gated_not_executed"
    return "live_gate_metadata_only"


def _transport_classification(
    probe_input: LocalProviderProbeLiveGateInput | None,
    failures: tuple[LocalProviderProbeLiveGateFailure, ...],
) -> str:
    if probe_input is None or failures:
        return "blocked"
    if probe_input.future_live_transport_class == "no_transport":
        return "no_transport_no_execution"
    return "future_localhost_transport_not_executed"


def _endpoint_classification(
    probe_input: LocalProviderProbeLiveGateInput | None,
    failures: tuple[LocalProviderProbeLiveGateFailure, ...],
) -> str:
    if probe_input is None or failures:
        return "blocked"
    if probe_input.endpoint_scope_class == "models_list_metadata_future":
        return "future_model_list_candidate_not_availability_proof"
    return "future_metadata_endpoint_candidate_only"


def _payload_classification(
    probe_input: LocalProviderProbeLiveGateInput | None,
    failures: tuple[LocalProviderProbeLiveGateFailure, ...],
) -> str:
    if probe_input is None or failures:
        return "blocked"
    return "no_payload_or_empty_metadata_request_only"


def _logging_classification(
    probe_input: LocalProviderProbeLiveGateInput | None,
    failures: tuple[LocalProviderProbeLiveGateFailure, ...],
) -> str:
    if probe_input is None or failures:
        return "blocked"
    return "redacted_metadata_logging_only"


def _timeout_classification(
    probe_input: LocalProviderProbeLiveGateInput | None,
    failures: tuple[LocalProviderProbeLiveGateFailure, ...],
) -> str:
    if probe_input is None or failures:
        return "blocked"
    return "bounded_timeout_required_for_future_live_probe"


def _cancellation_classification(
    probe_input: LocalProviderProbeLiveGateInput | None,
    failures: tuple[LocalProviderProbeLiveGateFailure, ...],
) -> str:
    if probe_input is None or failures:
        return "blocked"
    if probe_input.cancellation_policy_class == "cancellation_not_modeled":
        return "cancellation_not_modeled_requires_future_review"
    return "cancellation_supported_candidate"


def _future_result_classification(
    probe_input: LocalProviderProbeLiveGateInput | None,
    failures: tuple[LocalProviderProbeLiveGateFailure, ...],
) -> str:
    if probe_input is None or failures:
        return "blocked"
    if probe_input.future_result_class in NEGATIVE_FUTURE_RESULTS:
        return "future_negative_candidate_not_runtime_failure"
    if probe_input.future_result_class == "future_model_list_candidate":
        return "future_model_list_candidate_not_availability_proof"
    if probe_input.future_result_class == "not_executed":
        return "not_executed"
    return "future_metadata_success_candidate_not_health_proof"


def _truthfulness_classification(
    probe_input: LocalProviderProbeLiveGateInput | None,
    failures: tuple[LocalProviderProbeLiveGateFailure, ...],
) -> str:
    if probe_input is None or failures:
        return "blocked"
    return "future_results_not_health_model_identity_benchmark_evidence_or_verifier_proof"


def _related_status(decision: Any) -> str | None:
    for field in (
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
    failures: list[LocalProviderProbeLiveGateFailure],
    reason: str,
    field: str,
    message: str,
) -> None:
    failures.append(LocalProviderProbeLiveGateFailure(reason=reason, field=field, message=message))
