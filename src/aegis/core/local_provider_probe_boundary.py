from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from ipaddress import ip_address
from typing import Any, Mapping
from urllib.parse import urlparse


LOCAL_PROVIDER_PROBE_BOUNDARY_VERSION = "local-provider-health-probe-boundary/1"
LOCAL_PROVIDER_PROBE_BOUNDARY_EXECUTION_PERMISSION = (
    "not_granted_by_local_provider_probe_boundary"
)

PROVIDER_CLASSES = {
    "lm_studio_localhost_openai_compatible_metadata",
    "openai_compatible_localhost_metadata",
    "mock_test_provider_metadata",
    "unknown",
}

ENDPOINT_HOST_CLASSES = {"localhost", "loopback", "lan", "remote", "cloud", "unknown"}
LOCAL_ENDPOINT_HOST_CLASSES = {"localhost", "loopback"}
BLOCKED_ENDPOINT_HOST_CLASSES = {"lan", "remote", "cloud", "unknown"}

PROBE_PHASES = {
    "classify_probe_boundary",
    "provider_metadata_probe_candidate",
    "models_list_probe_candidate",
    "health_metadata_probe_candidate",
    "negative_result_candidate",
    "unknown",
}

PROBE_SCOPES = {
    "provider_metadata_only",
    "models_list_metadata_only",
    "health_metadata_only",
    "mock_metadata_only",
    "unknown",
}

PAYLOAD_CLASSES = {
    "no_payload",
    "empty_get",
    "empty_head",
    "prompt_payload",
    "context_payload",
    "memory_payload",
    "repo_payload",
    "raw_journal_payload",
    "raw_evidence_payload",
    "secret_payload",
    "unknown",
}

SECRET_POLICIES = {
    "no_secret",
    "no_auth_header",
    "authorization_header_blocked",
    "api_key_validation_requested",
    "secret_read_requested",
    "unknown",
}

METADATA_ENDPOINT_CLASSES = {
    "provider_root_metadata_candidate",
    "models_list_metadata_candidate",
    "health_metadata_candidate",
    "mock_metadata_candidate",
    "unknown",
}

ALLOWED_METADATA_PATHS = {
    "/",
    "/v1",
    "/v1/",
    "/v1/models",
    "/models",
    "/health",
    "/api/tags",
}

BLOCKED_ENDPOINT_MARKERS = {
    "/chat/completions": "generation_endpoint_blocked",
    "/completions": "completion_endpoint_blocked",
    "/responses": "generation_endpoint_blocked",
    "/embeddings": "embedding_endpoint_blocked",
    "/rerank": "reranker_endpoint_blocked",
    "/audio": "audio_endpoint_blocked",
    "/images": "multimodal_endpoint_blocked",
    "/vision": "multimodal_endpoint_blocked",
    "/files": "file_upload_endpoint_blocked",
    "/tool": "tool_call_endpoint_blocked",
}

MAX_TIMEOUT_MS = 5_000
MIN_TIMEOUT_MS = 1

FORBIDDEN_TRUTHY_FIELDS = {
    "authority": "authority_must_be_false",
    "runtime_dispatch_allowed": "runtime_dispatch_not_allowed",
    "approval_grant": "approval_grant_not_allowed",
    "capability_grant": "capability_grant_not_allowed",
    "lease_grant": "lease_grant_not_allowed",
    "evidence_provided_by_probe": "probe_boundary_cannot_provide_evidence",
    "evidence_created": "probe_boundary_cannot_provide_evidence",
    "verifier_success": "probe_boundary_cannot_mark_verifier_success",
    "verified_success": "probe_boundary_cannot_mark_verifier_success",
    "mutation_performed": "mutation_performed_denied",
    "frontend_authority": "frontend_authority_not_allowed",
    "success": "success_claim_denied",
    "proof": "proof_claim_denied",
    "certification_claim": "certification_claim_denied",
    "provider_health_verified": "provider_health_verification_denied",
    "model_availability_verified": "model_availability_verification_denied",
    "model_identity_verified": "model_identity_verification_denied",
    "benchmark_claim_verified": "benchmark_verification_denied",
    "provider_selected_for_execution": "provider_execution_selection_denied",
    "model_selected_for_execution": "model_execution_selection_denied",
    "auto_mode_execution_allowed": "auto_mode_execution_denied",
    "provider_metadata_is_truth": "provider_metadata_truth_claim_denied",
    "model_list_is_truth": "model_list_truth_claim_denied",
    "self_reported_identity_is_authority": "self_reported_identity_authority_denied",
}

FORBIDDEN_BEHAVIOR_FIELDS = {
    "provider_probed": "provider_probe_execution_denied",
    "endpoint_probed": "endpoint_probe_execution_denied",
    "http_request_performed": "http_request_denied",
    "socket_opened": "socket_open_denied",
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
}

FORBIDDEN_BEHAVIOR_REASONS = set(FORBIDDEN_BEHAVIOR_FIELDS.values())


@dataclass(frozen=True)
class LocalProviderProbeBoundaryFailure:
    reason: str
    field: str
    message: str


@dataclass(frozen=True)
class EndpointMetadata:
    raw_url: str | None
    scheme: str | None
    host: str | None
    port: int | None
    path: str | None
    metadata_endpoint_class: str | None
    normalized_metadata_path: str | None
    is_loopback_url: bool
    is_malformed: bool


@dataclass(frozen=True)
class LocalProviderProbeBoundaryInput:
    request_id: str | None
    provider_class: str | None
    endpoint_host_class: str | None
    endpoint: EndpointMetadata
    probe_phase: str | None
    probe_scope: str | None
    timeout_ms: int | None
    payload_class: str | None
    secret_policy: str | None
    namespace: str | None
    source_refs: tuple[Mapping[str, Any], ...]
    provenance: tuple[Mapping[str, Any], ...]
    limitations: tuple[str, ...]
    unknowns: tuple[str, ...]
    authorization_header_present: bool
    operator_approval_future_required: bool


@dataclass(frozen=True)
class RelatedLocalProviderProbeBoundaryReference:
    label: str
    observed_status: str | None
    reference_only: bool = True
    authority: bool = False
    implementation_claim: bool = False


@dataclass(frozen=True)
class LocalProviderProbeBoundaryDecision:
    contract_version: str
    probe_boundary_status: str
    request_id: str | None
    provider_class: str | None
    endpoint_host_class: str | None
    endpoint_metadata: EndpointMetadata | None
    probe_phase: str | None
    probe_scope: str | None
    timeout_ms: int | None
    payload_class: str | None
    secret_policy: str | None
    namespace: str | None
    probe_classification: str
    endpoint_classification: str
    payload_classification: str
    secret_classification: str
    truthfulness_classification: str
    negative_result_classification: str
    related_references: tuple[RelatedLocalProviderProbeBoundaryReference, ...]
    failure_reasons: tuple[str, ...]
    failures: tuple[LocalProviderProbeBoundaryFailure, ...]
    probe_input: LocalProviderProbeBoundaryInput | None
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = LOCAL_PROVIDER_PROBE_BOUNDARY_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_probe: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    frontend_authority: bool = False
    provider_health_verified: bool = False
    model_availability_verified: bool = False
    model_identity_verified: bool = False
    benchmark_claim_verified: bool = False
    provider_probed: bool = False
    endpoint_probed: bool = False
    http_request_performed: bool = False
    socket_opened: bool = False
    provider_authenticated: bool = False
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


def validate_local_provider_probe_boundary_request(
    request: Mapping[str, Any] | None,
    *,
    local_provider_health_decision: Any | None = None,
    local_provider_probe_design_decision: Any | None = None,
    model_auto_mode_decision: Any | None = None,
    local_model_inventory_decision: Any | None = None,
    local_model_context_profile_decision: Any | None = None,
    policy_extension_decision: Any | None = None,
    context_policy_decision: Any | None = None,
    memory_governance_decision: Any | None = None,
    identity_scope_decision: Any | None = None,
    capability_lease_decision: Any | None = None,
) -> LocalProviderProbeBoundaryDecision:
    """Validate a local-only metadata probe boundary without performing a probe."""

    if not isinstance(request, Mapping):
        failure = LocalProviderProbeBoundaryFailure(
            reason="missing_request",
            field="request",
            message="local provider probe boundary requires caller-supplied metadata",
        )
        return _decision(probe_input=None, related_references=(), failures=(failure,))

    data = deepcopy(dict(request))
    failures: list[LocalProviderProbeBoundaryFailure] = []
    related_references: list[RelatedLocalProviderProbeBoundaryReference] = []

    _validate_forbidden_claims("request", data, failures)
    for label, decision in {
        "local_provider_health": local_provider_health_decision,
        "local_provider_probe_design": local_provider_probe_design_decision,
        "model_auto_mode": model_auto_mode_decision,
        "local_model_inventory": local_model_inventory_decision,
        "local_model_context_profile": local_model_context_profile_decision,
        "policy_extension": policy_extension_decision,
        "context_policy": context_policy_decision,
        "memory_governance": memory_governance_decision,
        "identity_scope": identity_scope_decision,
        "capability_lease": capability_lease_decision,
    }.items():
        _validate_related_decision(label, decision, failures, related_references)

    endpoint = _endpoint_metadata(data.get("endpoint_url_metadata", data.get("endpoint_descriptor")))
    probe_input = LocalProviderProbeBoundaryInput(
        request_id=_text(data.get("request_id")),
        provider_class=_text(data.get("provider_class")),
        endpoint_host_class=_text(data.get("endpoint_host_class")),
        endpoint=endpoint,
        probe_phase=_text(data.get("probe_phase")),
        probe_scope=_text(data.get("probe_scope")),
        timeout_ms=_int(data.get("timeout_ms")),
        payload_class=_text(data.get("payload_class")),
        secret_policy=_text(data.get("secret_policy")),
        namespace=_text(data.get("namespace")),
        source_refs=_mapping_tuple(data.get("source_refs")),
        provenance=_mapping_tuple(data.get("provenance")),
        limitations=_text_tuple(data.get("limitations")),
        unknowns=_text_tuple(data.get("unknowns")),
        authorization_header_present=_truthy(data.get("authorization_header_present")),
        operator_approval_future_required=_truthy(data.get("operator_approval_future_required")),
    )

    _validate_required(probe_input, failures)
    _validate_provider_and_host(probe_input, failures)
    _validate_endpoint(probe_input, failures)
    _validate_payload_and_secret(probe_input, failures)
    _validate_timeout(probe_input, failures)
    _validate_truthfulness(data, failures)

    return _decision(
        probe_input=probe_input,
        related_references=tuple(related_references),
        failures=tuple(failures),
    )


def _decision(
    *,
    probe_input: LocalProviderProbeBoundaryInput | None,
    related_references: tuple[RelatedLocalProviderProbeBoundaryReference, ...],
    failures: tuple[LocalProviderProbeBoundaryFailure, ...],
) -> LocalProviderProbeBoundaryDecision:
    return LocalProviderProbeBoundaryDecision(
        contract_version=LOCAL_PROVIDER_PROBE_BOUNDARY_VERSION,
        probe_boundary_status=_probe_boundary_status(probe_input, failures),
        request_id=probe_input.request_id if probe_input else None,
        provider_class=probe_input.provider_class if probe_input else None,
        endpoint_host_class=probe_input.endpoint_host_class if probe_input else None,
        endpoint_metadata=probe_input.endpoint if probe_input else None,
        probe_phase=probe_input.probe_phase if probe_input else None,
        probe_scope=probe_input.probe_scope if probe_input else None,
        timeout_ms=probe_input.timeout_ms if probe_input else None,
        payload_class=probe_input.payload_class if probe_input else None,
        secret_policy=probe_input.secret_policy if probe_input else None,
        namespace=probe_input.namespace if probe_input else None,
        probe_classification=_probe_classification(probe_input, failures),
        endpoint_classification=_endpoint_classification(probe_input, failures),
        payload_classification=_payload_classification(probe_input, failures),
        secret_classification=_secret_classification(probe_input, failures),
        truthfulness_classification=_truthfulness_classification(probe_input, failures),
        negative_result_classification=_negative_result_classification(probe_input, failures),
        related_references=related_references,
        failure_reasons=tuple(dict.fromkeys(f.reason for f in failures)),
        failures=failures,
        probe_input=probe_input,
    )


def _endpoint_metadata(value: Any) -> EndpointMetadata:
    data = value if isinstance(value, Mapping) else {}
    raw_url = _text(data.get("url") or data.get("endpoint_url") or data.get("endpoint_ref"))
    metadata_endpoint_class = _text(data.get("metadata_endpoint_class"))
    descriptor_path = _text(data.get("path"))
    descriptor_host = _text(data.get("host"))
    descriptor_scheme = _text(data.get("scheme"))
    descriptor_port = _int(data.get("port"))

    if not raw_url and any(v is not None for v in (descriptor_path, descriptor_host, descriptor_scheme, descriptor_port)):
        scheme = descriptor_scheme or "http"
        host = descriptor_host or ""
        port = f":{descriptor_port}" if descriptor_port is not None else ""
        path = descriptor_path or "/"
        raw_url = f"{scheme}://{host}{port}{path}"

    if not raw_url:
        return EndpointMetadata(
            raw_url=None,
            scheme=None,
            host=None,
            port=None,
            path=None,
            metadata_endpoint_class=metadata_endpoint_class,
            normalized_metadata_path=None,
            is_loopback_url=False,
            is_malformed=False,
        )

    try:
        parsed = urlparse(raw_url)
        host = parsed.hostname
        port = parsed.port
        scheme = parsed.scheme
        path = parsed.path or "/"
    except ValueError:
        return EndpointMetadata(
            raw_url=raw_url,
            scheme=None,
            host=None,
            port=None,
            path=None,
            metadata_endpoint_class=metadata_endpoint_class,
            normalized_metadata_path=None,
            is_loopback_url=False,
            is_malformed=True,
        )

    malformed = not bool(scheme and host)
    return EndpointMetadata(
        raw_url=raw_url,
        scheme=scheme or None,
        host=host,
        port=port,
        path=path,
        metadata_endpoint_class=metadata_endpoint_class,
        normalized_metadata_path=_normalize_metadata_path(path),
        is_loopback_url=_is_loopback_host(host),
        is_malformed=malformed,
    )


def _validate_required(
    probe_input: LocalProviderProbeBoundaryInput,
    failures: list[LocalProviderProbeBoundaryFailure],
) -> None:
    required = {
        "request_id": probe_input.request_id,
        "provider_class": probe_input.provider_class,
        "endpoint_host_class": probe_input.endpoint_host_class,
        "probe_phase": probe_input.probe_phase,
        "probe_scope": probe_input.probe_scope,
        "timeout_ms": probe_input.timeout_ms,
        "payload_class": probe_input.payload_class,
        "secret_policy": probe_input.secret_policy,
        "namespace": probe_input.namespace,
    }
    for field, value in required.items():
        if value is None or value == "":
            _add_failure(failures, f"missing_{field}", field, f"{field} is required")
    if not probe_input.endpoint.raw_url:
        _add_failure(failures, "missing_endpoint_descriptor", "endpoint_url_metadata", "endpoint descriptor or URL metadata is required")
    if not (probe_input.source_refs or probe_input.provenance):
        _add_failure(failures, "missing_source_refs_or_provenance", "source_refs", "source refs or provenance are required")
    if probe_input.provider_class and probe_input.provider_class not in PROVIDER_CLASSES:
        _add_failure(failures, "unsupported_provider_class", "provider_class", "provider class is not supported by the probe boundary")
    if probe_input.endpoint_host_class and probe_input.endpoint_host_class not in ENDPOINT_HOST_CLASSES:
        _add_failure(failures, "unsupported_endpoint_host_class", "endpoint_host_class", "endpoint host class is not recognized")
    if probe_input.probe_phase and probe_input.probe_phase not in PROBE_PHASES:
        _add_failure(failures, "unsupported_probe_phase", "probe_phase", "probe phase is not recognized")
    if probe_input.probe_scope and probe_input.probe_scope not in PROBE_SCOPES:
        _add_failure(failures, "unsupported_probe_scope", "probe_scope", "probe scope is not recognized")
    if probe_input.payload_class and probe_input.payload_class not in PAYLOAD_CLASSES:
        _add_failure(failures, "unsupported_payload_class", "payload_class", "payload class is not recognized")
    if probe_input.secret_policy and probe_input.secret_policy not in SECRET_POLICIES:
        _add_failure(failures, "unsupported_secret_policy", "secret_policy", "secret policy is not recognized")
    endpoint_class = probe_input.endpoint.metadata_endpoint_class
    if endpoint_class and endpoint_class not in METADATA_ENDPOINT_CLASSES:
        _add_failure(failures, "unsupported_metadata_endpoint_class", "metadata_endpoint_class", "metadata endpoint class is not recognized")


def _validate_provider_and_host(
    probe_input: LocalProviderProbeBoundaryInput,
    failures: list[LocalProviderProbeBoundaryFailure],
) -> None:
    if probe_input.provider_class == "unknown":
        _add_failure(failures, "unknown_provider_blocked", "provider_class", "unknown provider class is blocked")
    if probe_input.endpoint_host_class in BLOCKED_ENDPOINT_HOST_CLASSES:
        _add_failure(failures, "blocked_by_host", "endpoint_host_class", "only localhost or loopback endpoint host classes are allowed")
    if probe_input.endpoint_host_class in LOCAL_ENDPOINT_HOST_CLASSES and probe_input.endpoint.host:
        if not probe_input.endpoint.is_loopback_url:
            _add_failure(failures, "endpoint_host_class_url_mismatch", "endpoint_url_metadata", "declared local host class does not match endpoint URL host")


def _validate_endpoint(
    probe_input: LocalProviderProbeBoundaryInput,
    failures: list[LocalProviderProbeBoundaryFailure],
) -> None:
    endpoint = probe_input.endpoint
    if endpoint.is_malformed:
        _add_failure(failures, "malformed_endpoint", "endpoint_url_metadata", "endpoint URL metadata is malformed")
        return
    if not endpoint.raw_url:
        return
    if endpoint.scheme not in {"http", "https"}:
        _add_failure(failures, "unsupported_endpoint_scheme", "endpoint_url_metadata", "only explicit HTTP metadata endpoints are allowed")
    if endpoint.scheme == "https" and endpoint.host in {"localhost", "127.0.0.1", "::1"}:
        pass
    if not endpoint.is_loopback_url:
        _add_failure(failures, "non_loopback_endpoint_blocked", "endpoint_url_metadata", "endpoint URL host must be localhost or loopback")
    if endpoint.host and _looks_like_localhost_spoof(endpoint.host):
        _add_failure(failures, "localhost_spoof_rejected", "endpoint_url_metadata", "localhost spoof host is rejected")
    if endpoint.normalized_metadata_path is None:
        _add_failure(failures, "unknown_endpoint_blocked", "endpoint_url_metadata", "unknown endpoint path is blocked or future-gated")
    if endpoint.path:
        lowered_path = endpoint.path.lower()
        for marker, reason in BLOCKED_ENDPOINT_MARKERS.items():
            if marker in lowered_path:
                _add_failure(failures, reason, "endpoint_url_metadata", "generation, embedding, reranker, multimodal, upload, and tool endpoints are blocked")
    endpoint_class = endpoint.metadata_endpoint_class
    if endpoint_class in {None, "", "unknown"}:
        _add_failure(failures, "unknown_metadata_endpoint_class_blocked", "metadata_endpoint_class", "metadata endpoint class must be explicit")


def _validate_payload_and_secret(
    probe_input: LocalProviderProbeBoundaryInput,
    failures: list[LocalProviderProbeBoundaryFailure],
) -> None:
    if probe_input.payload_class in {
        "prompt_payload",
        "context_payload",
        "memory_payload",
        "repo_payload",
        "raw_journal_payload",
        "raw_evidence_payload",
        "secret_payload",
        "unknown",
    }:
        _add_failure(failures, "blocked_by_payload", "payload_class", "only no-payload or empty metadata requests are allowed")
    if probe_input.secret_policy in {
        "authorization_header_blocked",
        "api_key_validation_requested",
        "secret_read_requested",
        "unknown",
    }:
        _add_failure(failures, "blocked_by_secret_policy", "secret_policy", "secrets, API key validation, and Authorization headers are blocked")
    if probe_input.authorization_header_present:
        _add_failure(failures, "authorization_header_denied", "authorization_header_present", "Authorization headers are blocked by default")


def _validate_timeout(
    probe_input: LocalProviderProbeBoundaryInput,
    failures: list[LocalProviderProbeBoundaryFailure],
) -> None:
    timeout = probe_input.timeout_ms
    if timeout is None:
        return
    if timeout < MIN_TIMEOUT_MS:
        _add_failure(failures, "invalid_timeout_policy", "timeout_ms", "timeout must be positive")
    if timeout > MAX_TIMEOUT_MS:
        _add_failure(failures, "blocked_by_timeout_policy", "timeout_ms", "timeout exceeds local provider probe boundary limit")


def _validate_truthfulness(data: Mapping[str, Any], failures: list[LocalProviderProbeBoundaryFailure]) -> None:
    proof_fields = {
        "provider_metadata_is_truth": "provider_metadata_truth_claim_denied",
        "model_list_is_truth": "model_list_truth_claim_denied",
        "provider_health_is_proof": "provider_health_proof_denied",
        "model_availability_is_execution_ready": "model_availability_execution_ready_claim_denied",
        "probe_candidate_selects_auto_mode": "auto_mode_selection_claim_denied",
        "probe_candidate_is_model_profile_proof": "model_profile_proof_claim_denied",
        "quality_or_benchmark_verified": "benchmark_verification_denied",
        "self_reported_identity_is_authority": "self_reported_identity_authority_denied",
    }
    for field, reason in proof_fields.items():
        if _truthy(data.get(field)):
            _add_failure(failures, reason, field, "probe boundary metadata cannot become truth, proof, model availability, benchmark, identity, or Auto Mode selection")


def _validate_related_decision(
    label: str,
    decision: Any | None,
    failures: list[LocalProviderProbeBoundaryFailure],
    related_references: list[RelatedLocalProviderProbeBoundaryReference],
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
            f"{label} cannot authorize provider probes, runtime dispatch, model calls, payload transfer, evidence, verifier success, or grants",
        )
    related_references.append(
        RelatedLocalProviderProbeBoundaryReference(
            label=label,
            observed_status=_related_status(decision),
            implementation_claim=len(failures) > before,
        )
    )


def _validate_forbidden_claims(
    label: str,
    source: Any,
    failures: list[LocalProviderProbeBoundaryFailure],
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
                f"{label} cannot perform probes, HTTP/socket behavior, model behavior, payload transfer, auth, secret reads, external calls, or runtime mutations",
            )
    execution_permission = _field_value(source, "execution_permission")
    if execution_permission not in (None, "", LOCAL_PROVIDER_PROBE_BOUNDARY_EXECUTION_PERMISSION):
        permission_text = str(execution_permission)
        if not permission_text.startswith("not_granted"):
            _add_failure(failures, "execution_permission_claim_denied", f"{label}.execution_permission", "local provider probe boundary cannot grant execution permission")


def _probe_boundary_status(
    probe_input: LocalProviderProbeBoundaryInput | None,
    failures: tuple[LocalProviderProbeBoundaryFailure, ...],
) -> str:
    if probe_input is None:
        return "blocked_by_unknown_provider"
    reasons = {failure.reason for failure in failures}
    if not reasons:
        return "probe_allowed_candidate"
    if "unsafe_related_decision" in reasons:
        return "blocked_by_policy"
    if any(reason.startswith("missing_") or reason.startswith("unsupported_") for reason in reasons):
        return "blocked_by_unknown_provider"
    if "blocked_by_host" in reasons or "non_loopback_endpoint_blocked" in reasons or "endpoint_host_class_url_mismatch" in reasons or "localhost_spoof_rejected" in reasons:
        return "blocked_by_host"
    if any("endpoint" in reason or "generation" in reason or "completion" in reason or "embedding" in reason or "reranker" in reason or "multimodal" in reason or "audio" in reason or "file_upload" in reason or "tool_call" in reason for reason in reasons):
        return "blocked_by_endpoint_scope"
    if "blocked_by_payload" in reasons or any("payload" in reason for reason in reasons):
        return "blocked_by_payload"
    if "blocked_by_secret_policy" in reasons or any("secret" in reason or "auth" in reason or "api_key" in reason for reason in reasons):
        return "blocked_by_secret_policy"
    if "blocked_by_timeout_policy" in reasons or "invalid_timeout_policy" in reasons:
        return "blocked_by_timeout_policy"
    if any("unknown" in reason for reason in reasons):
        return "unknown"
    return "blocked_by_endpoint_scope"


def _probe_classification(
    probe_input: LocalProviderProbeBoundaryInput | None,
    failures: tuple[LocalProviderProbeBoundaryFailure, ...],
) -> str:
    if probe_input is None or failures:
        return "blocked"
    if probe_input.probe_phase == "negative_result_candidate":
        return "negative_candidate_metadata_only"
    return "metadata_probe_candidate_only"


def _endpoint_classification(
    probe_input: LocalProviderProbeBoundaryInput | None,
    failures: tuple[LocalProviderProbeBoundaryFailure, ...],
) -> str:
    if probe_input is None or failures:
        return "blocked"
    if probe_input.endpoint.normalized_metadata_path == "/v1/models":
        return "models_list_metadata_candidate_not_availability_proof"
    return "local_metadata_endpoint_candidate"


def _payload_classification(
    probe_input: LocalProviderProbeBoundaryInput | None,
    failures: tuple[LocalProviderProbeBoundaryFailure, ...],
) -> str:
    if probe_input is None or failures:
        return "blocked"
    return "no_payload_or_empty_metadata_only"


def _secret_classification(
    probe_input: LocalProviderProbeBoundaryInput | None,
    failures: tuple[LocalProviderProbeBoundaryFailure, ...],
) -> str:
    if probe_input is None or failures:
        return "blocked"
    return "no_secret_no_authorization_header"


def _truthfulness_classification(
    probe_input: LocalProviderProbeBoundaryInput | None,
    failures: tuple[LocalProviderProbeBoundaryFailure, ...],
) -> str:
    if probe_input is None or failures:
        return "blocked"
    return "metadata_candidate_not_health_or_model_proof"


def _negative_result_classification(
    probe_input: LocalProviderProbeBoundaryInput | None,
    failures: tuple[LocalProviderProbeBoundaryFailure, ...],
) -> str:
    if probe_input is None:
        return "unknown"
    if probe_input.probe_phase == "negative_result_candidate":
        return "negative_candidate_metadata_only_not_runtime_failure"
    return "negative_evidence_expected_future_not_created"


def _related_status(decision: Any) -> str | None:
    for field in (
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


def _normalize_metadata_path(path: str | None) -> str | None:
    if not path:
        return None
    normalized = path.rstrip("/") or "/"
    if normalized == "/v1":
        return "/v1"
    if normalized in ALLOWED_METADATA_PATHS:
        return normalized
    return None


def _is_loopback_host(host: str | None) -> bool:
    if not host:
        return False
    lowered = host.strip().lower().strip("[]")
    if lowered == "localhost":
        return True
    try:
        return ip_address(lowered).is_loopback
    except ValueError:
        return False


def _looks_like_localhost_spoof(host: str) -> bool:
    lowered = host.strip().lower()
    return "localhost" in lowered and lowered != "localhost"


def _field_bool(source: Any, field: str) -> bool:
    return _truthy(_field_value(source, field))


def _field_value(source: Any, field: str) -> Any:
    if isinstance(source, Mapping):
        return source.get(field)
    return getattr(source, field, None)


def _truthy(value: Any, *, default: bool = False) -> bool:
    if value is None:
        return default
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
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _add_failure(
    failures: list[LocalProviderProbeBoundaryFailure],
    reason: str,
    field: str,
    message: str,
) -> None:
    failures.append(LocalProviderProbeBoundaryFailure(reason=reason, field=field, message=message))
