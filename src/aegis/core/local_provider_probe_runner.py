from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from ipaddress import ip_address
from typing import Any, Callable, Mapping
from urllib.parse import urlparse


LOCAL_PROVIDER_PROBE_RUNNER_VERSION = "local-provider-health-probe-runner/1"
LOCAL_PROVIDER_PROBE_RUNNER_EXECUTION_PERMISSION = (
    "not_granted_by_local_provider_probe_runner"
)

ALLOWED_ENDPOINT_CLASSES = {
    "provider_root_metadata",
    "models_list_metadata",
    "health_metadata",
}

BLOCKED_ENDPOINT_CLASSES = {
    "generation": "generation_endpoint_blocked",
    "chat_completion": "chat_completion_endpoint_blocked",
    "completion": "completion_endpoint_blocked",
    "embeddings": "embedding_endpoint_blocked",
    "rerank": "rerank_endpoint_blocked",
    "multimodal": "multimodal_endpoint_blocked",
    "audio": "audio_endpoint_blocked",
    "file_upload": "file_upload_endpoint_blocked",
    "tool_call": "tool_call_endpoint_blocked",
    "unknown": "unknown_endpoint_blocked",
}

RESULT_CLASSES = {
    "metadata_success_candidate",
    "model_list_success_candidate",
    "health_metadata_success_candidate",
    "timeout_negative_candidate",
    "connection_refused_negative_candidate",
    "unreachable_negative_candidate",
    "invalid_response_negative_candidate",
    "unauthorized_negative_candidate",
    "unsupported_endpoint_negative_candidate",
    "cancelled_negative_candidate",
    "not_executed",
    "unknown",
}

NEGATIVE_RESULT_CLASSES = {
    "timeout_negative_candidate",
    "connection_refused_negative_candidate",
    "unreachable_negative_candidate",
    "invalid_response_negative_candidate",
    "unauthorized_negative_candidate",
    "unsupported_endpoint_negative_candidate",
    "cancelled_negative_candidate",
}

LOCAL_HOSTNAMES = {"localhost"}
BLOCKED_PATH_MARKERS = {
    "/chat/completions": "chat_completion_endpoint_blocked",
    "/completions": "completion_endpoint_blocked",
    "/embeddings": "embedding_endpoint_blocked",
    "/rerank": "rerank_endpoint_blocked",
    "/audio": "audio_endpoint_blocked",
    "/images": "multimodal_endpoint_blocked",
    "/responses": "generation_endpoint_blocked",
    "/generate": "generation_endpoint_blocked",
    "/files": "file_upload_endpoint_blocked",
    "/tools": "tool_call_endpoint_blocked",
}

FORBIDDEN_TRUTHY_FIELDS = {
    "authority": "authority_must_be_false",
    "runtime_dispatch_allowed": "runtime_dispatch_not_allowed",
    "approval_grant": "approval_grant_not_allowed",
    "capability_grant": "capability_grant_not_allowed",
    "lease_grant": "lease_grant_not_allowed",
    "evidence_provided_by_probe_runner": "probe_runner_cannot_provide_evidence",
    "evidence_provided_by_live_gate": "probe_runner_cannot_provide_evidence",
    "evidence_provided_by_mock_probe": "probe_runner_cannot_provide_evidence",
    "evidence_created": "probe_runner_cannot_provide_evidence",
    "verifier_success": "probe_runner_cannot_mark_verifier_success",
    "verified_success": "probe_runner_cannot_mark_verifier_success",
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
    "metadata_success_is_health_proof": "metadata_success_health_proof_denied",
    "model_list_is_availability_proof": "model_list_availability_proof_denied",
    "negative_result_is_runtime_failure": "negative_runtime_failure_claim_denied",
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

PAYLOAD_FIELDS = {
    "body",
    "request_body",
    "json",
    "payload",
    "prompt",
    "messages",
    "context",
    "memory",
    "repo_content",
    "raw_journal",
    "raw_evidence",
    "secrets",
}

SECRET_HEADER_NAMES = {
    "authorization",
    "api-key",
    "apikey",
    "x-api-key",
    "x-goog-api-key",
    "bearer",
}


@dataclass(frozen=True)
class LocalProviderProbeRunnerFailure:
    reason: str
    field: str
    message: str


@dataclass(frozen=True)
class LocalProviderProbeHttpResponse:
    status_code: int
    json_data: Any | None = None
    content_type: str | None = None


@dataclass(frozen=True)
class LocalProviderProbeRunnerInput:
    request_id: str | None
    endpoint_url: str | None
    endpoint_class: str | None
    timeout_seconds: float | None
    namespace: str | None
    source_refs: tuple[Mapping[str, Any], ...]
    provenance: tuple[Mapping[str, Any], ...]
    paired_live_gate_ref: str | None
    limitations: tuple[str, ...]
    unknowns: tuple[str, ...]


@dataclass(frozen=True)
class LocalProviderProbeTransportRequest:
    method: str
    url: str
    timeout_seconds: float
    headers: Mapping[str, str]
    body: None = None


@dataclass(frozen=True)
class RelatedLocalProviderProbeRunnerReference:
    label: str
    observed_status: str | None
    reference_only: bool = True
    authority: bool = False
    implementation_claim: bool = False


@dataclass(frozen=True)
class LocalProviderProbeRunnerDecision:
    contract_version: str
    runner_status: str
    request_id: str | None
    endpoint_url: str | None
    endpoint_class: str | None
    result_class: str
    response_shape_classification: str
    host_classification: str
    endpoint_classification: str
    payload_classification: str
    secret_classification: str
    timeout_classification: str
    truthfulness_classification: str
    namespace: str | None
    response_status_code: int | None
    response_shape_keys: tuple[str, ...]
    model_count_candidate: int | None
    related_references: tuple[RelatedLocalProviderProbeRunnerReference, ...]
    failure_reasons: tuple[str, ...]
    failures: tuple[LocalProviderProbeRunnerFailure, ...]
    probe_input: LocalProviderProbeRunnerInput | None
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = LOCAL_PROVIDER_PROBE_RUNNER_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_probe_runner: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    frontend_authority: bool = False
    api_route_added: bool = False
    runtime_command_added: bool = False
    scheduler_added: bool = False
    provider_health_verified: bool = False
    model_availability_verified: bool = False
    model_identity_verified: bool = False
    benchmark_claim_verified: bool = False
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
    runtime_state_mutated: bool = False
    journal_mutated: bool = False
    evidence_mutated: bool = False
    replay_mutated: bool = False
    requires_backend_validation: bool = True
    requires_policy_check: bool = True
    read_only_projection: bool = True


class LocalProviderProbeCancelled(Exception):
    """Raised by injected transports to classify cancellation without retrying."""


TransportCallable = Callable[[LocalProviderProbeTransportRequest], Any]


def run_local_provider_probe(
    request: Mapping[str, Any] | None,
    *,
    transport: TransportCallable | None = None,
    local_provider_probe_live_gate_decision: Any | None = None,
    local_provider_probe_wiring_decision: Any | None = None,
    local_provider_probe_boundary_decision: Any | None = None,
    local_provider_probe_mock_runner_decision: Any | None = None,
    local_provider_health_decision: Any | None = None,
    model_auto_mode_decision: Any | None = None,
    local_model_inventory_decision: Any | None = None,
    local_model_context_profile_decision: Any | None = None,
    context_policy_decision: Any | None = None,
    identity_scope_decision: Any | None = None,
    memory_governance_decision: Any | None = None,
    policy_extension_decision: Any | None = None,
    capability_lease_decision: Any | None = None,
    mission_control_decision: Any | None = None,
    tool_simulation_decision: Any | None = None,
) -> LocalProviderProbeRunnerDecision:
    """Run a GET-only localhost provider metadata probe through an injected transport."""

    if not isinstance(request, Mapping):
        failure = LocalProviderProbeRunnerFailure(
            reason="missing_request",
            field="request",
            message="local provider probe runner requires caller-supplied metadata",
        )
        return _decision(
            probe_input=None,
            related_references=(),
            failures=(failure,),
            result_class="not_executed",
        )

    data = deepcopy(dict(request))
    failures: list[LocalProviderProbeRunnerFailure] = []
    related_references: list[RelatedLocalProviderProbeRunnerReference] = []

    _validate_forbidden_claims("request", data, failures)
    for label, decision in {
        "local_provider_probe_live_gate": local_provider_probe_live_gate_decision,
        "local_provider_probe_wiring": local_provider_probe_wiring_decision,
        "local_provider_probe_boundary": local_provider_probe_boundary_decision,
        "local_provider_probe_mock_runner": local_provider_probe_mock_runner_decision,
        "local_provider_health": local_provider_health_decision,
        "model_auto_mode": model_auto_mode_decision,
        "local_model_inventory": local_model_inventory_decision,
        "local_model_context_profile": local_model_context_profile_decision,
        "context_policy": context_policy_decision,
        "identity_scope": identity_scope_decision,
        "memory_governance": memory_governance_decision,
        "policy_extension": policy_extension_decision,
        "capability_lease": capability_lease_decision,
        "mission_control": mission_control_decision,
        "tool_simulation": tool_simulation_decision,
    }.items():
        _validate_related_decision(label, decision, failures, related_references)

    probe_input = LocalProviderProbeRunnerInput(
        request_id=_text(data.get("request_id")),
        endpoint_url=_text(data.get("endpoint_url") or data.get("url")),
        endpoint_class=_text(data.get("endpoint_class")),
        timeout_seconds=_timeout(data.get("timeout_seconds")),
        namespace=_text(data.get("namespace")),
        source_refs=_mapping_tuple(data.get("source_refs")),
        provenance=_mapping_tuple(data.get("provenance")),
        paired_live_gate_ref=_text(data.get("paired_live_gate_ref")),
        limitations=_text_tuple(data.get("limitations")),
        unknowns=_text_tuple(data.get("unknowns")),
    )

    _validate_required(
        probe_input,
        failures,
        has_live_gate_decision=local_provider_probe_live_gate_decision is not None,
    )
    _validate_endpoint_url(probe_input, failures)
    _validate_endpoint_class_and_path(probe_input, failures)
    _validate_payload_secret_logging(data, failures)
    _validate_truthfulness(data, failures)

    if failures:
        return _decision(
            probe_input=probe_input,
            related_references=tuple(related_references),
            failures=tuple(failures),
            result_class=_blocked_result_class(failures),
        )
    if transport is None:
        failure = LocalProviderProbeRunnerFailure(
            reason="missing_transport",
            field="transport",
            message="an injected transport is required for the localhost metadata probe",
        )
        return _decision(
            probe_input=probe_input,
            related_references=tuple(related_references),
            failures=(failure,),
            result_class="not_executed",
        )

    transport_request = LocalProviderProbeTransportRequest(
        method="GET",
        url=probe_input.endpoint_url or "",
        timeout_seconds=probe_input.timeout_seconds or 0.0,
        headers={},
        body=None,
    )
    try:
        response = transport(transport_request)
    except LocalProviderProbeCancelled:
        return _decision(
            probe_input=probe_input,
            related_references=tuple(related_references),
            failures=(),
            result_class="cancelled_negative_candidate",
        )
    except TimeoutError:
        return _decision(
            probe_input=probe_input,
            related_references=tuple(related_references),
            failures=(),
            result_class="timeout_negative_candidate",
        )
    except ConnectionRefusedError:
        return _decision(
            probe_input=probe_input,
            related_references=tuple(related_references),
            failures=(),
            result_class="connection_refused_negative_candidate",
        )
    except OSError:
        return _decision(
            probe_input=probe_input,
            related_references=tuple(related_references),
            failures=(),
            result_class="unreachable_negative_candidate",
        )

    normalized = _normalize_response(response)
    result_class = _result_class_from_response(probe_input.endpoint_class, normalized)
    return _decision(
        probe_input=probe_input,
        related_references=tuple(related_references),
        failures=(),
        result_class=result_class,
        response=normalized,
    )


def _decision(
    *,
    probe_input: LocalProviderProbeRunnerInput | None,
    related_references: tuple[RelatedLocalProviderProbeRunnerReference, ...],
    failures: tuple[LocalProviderProbeRunnerFailure, ...],
    result_class: str,
    response: LocalProviderProbeHttpResponse | None = None,
) -> LocalProviderProbeRunnerDecision:
    response_shape = _response_shape(response)
    return LocalProviderProbeRunnerDecision(
        contract_version=LOCAL_PROVIDER_PROBE_RUNNER_VERSION,
        runner_status=_runner_status(probe_input, failures, result_class),
        request_id=probe_input.request_id if probe_input else None,
        endpoint_url=probe_input.endpoint_url if probe_input else None,
        endpoint_class=probe_input.endpoint_class if probe_input else None,
        result_class=result_class if result_class in RESULT_CLASSES else "unknown",
        response_shape_classification=response_shape,
        host_classification=_host_classification(probe_input, failures),
        endpoint_classification=_endpoint_classification(probe_input, failures, result_class),
        payload_classification=_payload_classification(failures),
        secret_classification=_secret_classification(failures),
        timeout_classification=_timeout_classification(probe_input, failures),
        truthfulness_classification=_truthfulness_classification(probe_input, failures),
        namespace=probe_input.namespace if probe_input else None,
        response_status_code=response.status_code if response else None,
        response_shape_keys=_response_shape_keys(response),
        model_count_candidate=_model_count_candidate(response),
        related_references=related_references,
        failure_reasons=tuple(dict.fromkeys(f.reason for f in failures)),
        failures=failures,
        probe_input=probe_input,
    )


def _validate_required(
    probe_input: LocalProviderProbeRunnerInput,
    failures: list[LocalProviderProbeRunnerFailure],
    *,
    has_live_gate_decision: bool,
) -> None:
    required = {
        "request_id": probe_input.request_id,
        "endpoint_url": probe_input.endpoint_url,
        "endpoint_class": probe_input.endpoint_class,
        "timeout_seconds": probe_input.timeout_seconds,
        "namespace": probe_input.namespace,
    }
    for field, value in required.items():
        if value is None or value == "":
            _add_failure(failures, f"missing_{field}", field, f"{field} is required")
    if not (probe_input.source_refs or probe_input.provenance):
        _add_failure(failures, "missing_source_refs_or_provenance", "source_refs", "source refs or provenance are required")
    if not (probe_input.paired_live_gate_ref or has_live_gate_decision):
        _add_failure(failures, "missing_live_gate_reference", "paired_live_gate_ref", "safe live gate metadata or related decision is required")
    if probe_input.endpoint_class:
        if probe_input.endpoint_class not in ALLOWED_ENDPOINT_CLASSES | set(BLOCKED_ENDPOINT_CLASSES):
            _add_failure(failures, "unsupported_endpoint_class", "endpoint_class", "endpoint class is not recognized")


def _validate_endpoint_url(
    probe_input: LocalProviderProbeRunnerInput,
    failures: list[LocalProviderProbeRunnerFailure],
) -> None:
    if not probe_input.endpoint_url:
        return
    try:
        parsed = urlparse(probe_input.endpoint_url)
    except ValueError:
        _add_failure(failures, "malformed_url", "endpoint_url", "endpoint URL is malformed")
        return
    if parsed.scheme not in {"http", "https"}:
        _add_failure(failures, "unsupported_url_scheme", "endpoint_url", "only http/https loopback metadata endpoints are allowed")
    if parsed.username or parsed.password:
        _add_failure(failures, "url_credentials_blocked", "endpoint_url", "URL credentials are blocked")
    if parsed.fragment:
        _add_failure(failures, "url_fragment_blocked", "endpoint_url", "URL fragments are not used for metadata probes")
    host = parsed.hostname
    if not host:
        _add_failure(failures, "missing_url_host", "endpoint_url", "endpoint URL must include a host")
        return
    if not _is_loopback_host(host):
        reason = _non_loopback_reason(host)
        _add_failure(failures, reason, "endpoint_url", "only localhost or loopback endpoints are allowed")


def _validate_endpoint_class_and_path(
    probe_input: LocalProviderProbeRunnerInput,
    failures: list[LocalProviderProbeRunnerFailure],
) -> None:
    endpoint_class = probe_input.endpoint_class
    if endpoint_class in BLOCKED_ENDPOINT_CLASSES:
        _add_failure(
            failures,
            BLOCKED_ENDPOINT_CLASSES[endpoint_class],
            "endpoint_class",
            "generation, chat, completion, embedding, rerank, multimodal, audio, upload, tool, and unknown endpoints are blocked",
        )
    if not probe_input.endpoint_url:
        return
    parsed = urlparse(probe_input.endpoint_url)
    path = parsed.path.lower().rstrip("/")
    for marker, reason in BLOCKED_PATH_MARKERS.items():
        if path.endswith(marker) or marker in path:
            _add_failure(failures, reason, "endpoint_url", "endpoint path resolves to a blocked model/action endpoint")
            return
    if endpoint_class == "models_list_metadata" and not path.endswith("/models"):
        _add_failure(failures, "models_list_path_mismatch", "endpoint_url", "models-list metadata probes must target a models metadata path")
    if endpoint_class == "health_metadata" and not (path.endswith("/health") or path.endswith("/healthz")):
        _add_failure(failures, "health_path_mismatch", "endpoint_url", "health metadata probes must target a health metadata path")


def _validate_payload_secret_logging(
    data: Mapping[str, Any],
    failures: list[LocalProviderProbeRunnerFailure],
) -> None:
    for field in PAYLOAD_FIELDS:
        if _field_value(data, field) not in (None, "", (), [], {}):
            _add_failure(failures, f"{field}_payload_blocked", field, "provider probe runner is GET-only and cannot send payloads")
    headers = _field_value(data, "headers")
    if headers not in (None, "", (), [], {}):
        if isinstance(headers, Mapping):
            for name, value in headers.items():
                lowered = str(name).strip().lower()
                if lowered in SECRET_HEADER_NAMES or "authorization" in lowered or "api" in lowered:
                    _add_failure(failures, "authorization_header_denied", "headers", "Authorization and API key headers are blocked")
                if isinstance(value, str) and ("bearer " in value.lower() or "sk-" in value.lower()):
                    _add_failure(failures, "secret_header_value_denied", "headers", "secret-like header values are blocked")
        else:
            _add_failure(failures, "headers_blocked", "headers", "custom headers are not accepted for this no-auth metadata probe")
    if _truthy(data.get("validate_api_key")):
        _add_failure(failures, "api_key_validation_denied", "validate_api_key", "API key validation is blocked")
    if _truthy(data.get("read_secret")):
        _add_failure(failures, "secret_read_denied", "read_secret", "secret reads are blocked")
    if _truthy(data.get("log_response_body")):
        _add_failure(failures, "response_body_logging_denied", "log_response_body", "response body logging is blocked")
    if _truthy(data.get("log_secret")):
        _add_failure(failures, "secret_logging_denied", "log_secret", "secret logging is blocked")


def _validate_truthfulness(data: Mapping[str, Any], failures: list[LocalProviderProbeRunnerFailure]) -> None:
    proof_fields = {
        "metadata_success_is_health_proof": "metadata_success_health_proof_denied",
        "model_list_is_availability_proof": "model_list_availability_proof_denied",
        "negative_result_is_runtime_failure": "negative_runtime_failure_claim_denied",
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
            _add_failure(failures, reason, field, "probe runner metadata cannot become proof, runtime failure, model availability, benchmark, identity, or Auto Mode selection")


def _validate_related_decision(
    label: str,
    decision: Any | None,
    failures: list[LocalProviderProbeRunnerFailure],
    related_references: list[RelatedLocalProviderProbeRunnerReference],
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
            f"{label} cannot authorize unsafe provider calls, model calls, payload transfer, evidence, verifier success, or grants",
        )
    related_references.append(
        RelatedLocalProviderProbeRunnerReference(
            label=label,
            observed_status=_related_status(decision),
            implementation_claim=len(failures) > before,
        )
    )


def _validate_forbidden_claims(
    label: str,
    source: Any,
    failures: list[LocalProviderProbeRunnerFailure],
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
                f"{label} cannot add runtime/API surfaces, perform model behavior, transfer payloads, authenticate, read secrets, call external systems, or mutate runtime state",
            )
    execution_permission = _field_value(source, "execution_permission")
    if execution_permission not in (None, "", LOCAL_PROVIDER_PROBE_RUNNER_EXECUTION_PERMISSION):
        permission_text = str(execution_permission)
        if not permission_text.startswith("not_granted"):
            _add_failure(failures, "execution_permission_claim_denied", f"{label}.execution_permission", "local provider probe runner cannot grant execution permission")


def _normalize_response(response: Any) -> LocalProviderProbeHttpResponse:
    if isinstance(response, LocalProviderProbeHttpResponse):
        return response
    if isinstance(response, Mapping):
        return LocalProviderProbeHttpResponse(
            status_code=int(response.get("status_code", 0) or 0),
            json_data=deepcopy(response.get("json_data", response.get("json"))),
            content_type=_text(response.get("content_type")),
        )
    return LocalProviderProbeHttpResponse(status_code=0, json_data=None)


def _result_class_from_response(
    endpoint_class: str | None,
    response: LocalProviderProbeHttpResponse,
) -> str:
    if response.status_code in {401, 403}:
        return "unauthorized_negative_candidate"
    if response.status_code == 404:
        return "unsupported_endpoint_negative_candidate"
    if response.status_code < 200 or response.status_code >= 300:
        return "invalid_response_negative_candidate"
    shape = _response_shape(response)
    if shape in {"invalid_response_shape", "empty_response_shape"}:
        return "invalid_response_negative_candidate"
    if endpoint_class == "models_list_metadata":
        if shape == "models_list_shape_candidate":
            return "model_list_success_candidate"
        return "invalid_response_negative_candidate"
    if endpoint_class == "health_metadata":
        return "health_metadata_success_candidate"
    return "metadata_success_candidate"


def _blocked_result_class(failures: list[LocalProviderProbeRunnerFailure]) -> str:
    reasons = {failure.reason for failure in failures}
    if any("endpoint" in reason for reason in reasons):
        return "unsupported_endpoint_negative_candidate"
    if any("timeout" in reason for reason in reasons):
        return "timeout_negative_candidate"
    return "not_executed"


def _runner_status(
    probe_input: LocalProviderProbeRunnerInput | None,
    failures: tuple[LocalProviderProbeRunnerFailure, ...],
    result_class: str,
) -> str:
    if probe_input is None:
        return "not_executed"
    reasons = {failure.reason for failure in failures}
    if reasons:
        if "unsafe_related_decision" in reasons:
            return "blocked_by_related_decision"
        if any(reason.startswith("missing_") or reason.startswith("unsupported_") for reason in reasons):
            return "blocked_by_missing_or_unsupported_metadata"
        if any("host" in reason or "lan" in reason or "remote" in reason or "cloud" in reason or "loopback" in reason or "url" in reason for reason in reasons):
            return "blocked_by_host"
        if any("endpoint" in reason or "generation" in reason or "completion" in reason or "embedding" in reason or "rerank" in reason or "multimodal" in reason or "audio" in reason or "upload" in reason or "tool" in reason for reason in reasons):
            return "blocked_by_endpoint"
        if any("payload" in reason for reason in reasons):
            return "blocked_by_payload"
        if any("secret" in reason or "auth" in reason or "api_key" in reason or "header" in reason for reason in reasons):
            return "blocked_by_secret_policy"
        if any("proof" in reason or "truth" in reason or "availability" in reason or "identity" in reason or "benchmark" in reason for reason in reasons):
            return "blocked_by_truthfulness_claim"
        return "not_executed"
    if result_class in NEGATIVE_RESULT_CLASSES:
        return result_class
    return result_class


def _host_classification(
    probe_input: LocalProviderProbeRunnerInput | None,
    failures: tuple[LocalProviderProbeRunnerFailure, ...],
) -> str:
    if probe_input is None or failures:
        return "blocked_or_not_executed"
    if not probe_input.endpoint_url:
        return "blocked_or_not_executed"
    host = urlparse(probe_input.endpoint_url).hostname or ""
    if host.lower() == "localhost":
        return "localhost_only"
    return "loopback_only"


def _endpoint_classification(
    probe_input: LocalProviderProbeRunnerInput | None,
    failures: tuple[LocalProviderProbeRunnerFailure, ...],
    result_class: str,
) -> str:
    if probe_input is None or failures:
        return "blocked_or_not_executed"
    if probe_input.endpoint_class == "models_list_metadata":
        return "models_list_metadata_candidate_not_availability_proof"
    if probe_input.endpoint_class == "health_metadata":
        return "health_metadata_candidate_not_health_proof"
    if result_class in NEGATIVE_RESULT_CLASSES:
        return "negative_metadata_candidate_not_runtime_failure"
    return "provider_root_metadata_candidate_not_health_proof"


def _payload_classification(failures: tuple[LocalProviderProbeRunnerFailure, ...]) -> str:
    if any("payload" in failure.reason for failure in failures):
        return "blocked_payload"
    return "get_only_no_payload"


def _secret_classification(failures: tuple[LocalProviderProbeRunnerFailure, ...]) -> str:
    if any("secret" in failure.reason or "auth" in failure.reason or "api_key" in failure.reason or "header" in failure.reason for failure in failures):
        return "blocked_secret_or_authorization"
    return "no_secret_no_authorization_no_api_key_validation"


def _timeout_classification(
    probe_input: LocalProviderProbeRunnerInput | None,
    failures: tuple[LocalProviderProbeRunnerFailure, ...],
) -> str:
    if probe_input is None or any("timeout" in failure.reason for failure in failures):
        return "blocked_timeout"
    return "bounded_short_timeout"


def _truthfulness_classification(
    probe_input: LocalProviderProbeRunnerInput | None,
    failures: tuple[LocalProviderProbeRunnerFailure, ...],
) -> str:
    if probe_input is None or failures:
        return "blocked_or_not_executed"
    return "metadata_result_not_health_model_identity_benchmark_evidence_or_verifier_proof"


def _response_shape(response: LocalProviderProbeHttpResponse | None) -> str:
    if response is None:
        return "not_observed"
    if response.json_data is None:
        return "empty_response_shape"
    if isinstance(response.json_data, Mapping):
        if isinstance(response.json_data.get("data"), list):
            return "models_list_shape_candidate"
        if any(key in response.json_data for key in ("status", "ok", "health")):
            return "health_metadata_shape_candidate"
        return "provider_metadata_shape_candidate"
    return "invalid_response_shape"


def _response_shape_keys(response: LocalProviderProbeHttpResponse | None) -> tuple[str, ...]:
    if response is None or not isinstance(response.json_data, Mapping):
        return ()
    return tuple(sorted(str(key) for key in response.json_data.keys()))


def _model_count_candidate(response: LocalProviderProbeHttpResponse | None) -> int | None:
    if response is None or not isinstance(response.json_data, Mapping):
        return None
    data = response.json_data.get("data")
    if isinstance(data, list):
        return len(data)
    return None


def _is_loopback_host(host: str) -> bool:
    lowered = host.strip().lower().rstrip(".")
    if lowered in LOCAL_HOSTNAMES:
        return True
    try:
        return ip_address(lowered).is_loopback
    except ValueError:
        return False


def _non_loopback_reason(host: str) -> str:
    lowered = host.strip().lower().rstrip(".")
    try:
        parsed = ip_address(lowered)
    except ValueError:
        if "localhost" in lowered or "127.0.0.1" in lowered or "::1" in lowered:
            return "spoofed_localhost_blocked"
        return "remote_or_unknown_host_blocked"
    if parsed.is_private:
        return "lan_endpoint_blocked"
    if parsed.is_global:
        return "cloud_or_remote_endpoint_blocked"
    return "remote_or_unknown_host_blocked"


def _related_status(decision: Any) -> str | None:
    for field in (
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


def _timeout(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        timeout = float(value)
    except (TypeError, ValueError):
        return None
    if timeout <= 0 or timeout > 5:
        return None
    return timeout


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
    failures: list[LocalProviderProbeRunnerFailure],
    reason: str,
    field: str,
    message: str,
) -> None:
    failures.append(LocalProviderProbeRunnerFailure(reason=reason, field=field, message=message))
