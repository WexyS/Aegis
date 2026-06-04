from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping


LOCAL_PROVIDER_PROBE_DESIGN_VERSION = "first-local-provider-health-probe-design/1"
LOCAL_PROVIDER_PROBE_DESIGN_EXECUTION_PERMISSION = "not_granted_by_provider_probe_design"

PROBE_TARGET_CLASSES = {
    "lm_studio_local_openai_compatible",
    "ollama_local_optional",
    "vllm_local",
    "generic_openai_compatible_local",
    "mock_test_provider",
    "unsupported_remote",
    "unsupported_cloud",
    "unknown",
}

ALLOWED_ENDPOINT_HOST_CLASSES = {"localhost", "loopback"}
BLOCKED_ENDPOINT_HOST_CLASSES = {"lan", "remote", "cloud", "unknown"}
ENDPOINT_HOST_CLASSES = ALLOWED_ENDPOINT_HOST_CLASSES | BLOCKED_ENDPOINT_HOST_CLASSES

PROBE_PHASES = {
    "endpoint_reachability_probe_future",
    "provider_metadata_probe_future",
    "model_list_probe_future",
    "model_role_match_probe_future",
    "minimal_generation_probe_future_blocked_for_now",
    "embedding_probe_future_blocked_for_now",
    "reranker_probe_future_blocked_for_now",
    "multimodal_probe_future_blocked_for_now",
    "unknown",
}

BLOCKED_PROBE_PHASES = {
    "minimal_generation_probe_future_blocked_for_now",
    "embedding_probe_future_blocked_for_now",
    "reranker_probe_future_blocked_for_now",
    "multimodal_probe_future_blocked_for_now",
}

FUTURE_PROBE_PHASES = {
    "endpoint_reachability_probe_future",
    "provider_metadata_probe_future",
    "model_list_probe_future",
    "model_role_match_probe_future",
}

PROBE_RESULT_STATUSES = {
    "not_executed",
    "design_only",
    "future_probe_candidate",
    "blocked_by_policy",
    "blocked_by_endpoint_host",
    "blocked_by_secret_boundary",
    "blocked_by_unknown_metadata",
    "blocked_by_missing_lease",
    "blocked_by_missing_operator_review",
    "blocked_by_missing_provider_health_readiness",
    "blocked_by_resource_pressure",
    "blocked_by_timeout_policy",
    "unsupported",
    "unknown",
}

FUTURE_EVIDENCE_TYPES = {
    "provider_probe_attempt_future",
    "endpoint_reachable_future",
    "endpoint_unreachable_future",
    "provider_metadata_response_future",
    "model_list_response_future",
    "timeout_negative_evidence_future",
    "refused_connection_negative_evidence_future",
    "invalid_response_negative_evidence_future",
    "unauthorized_negative_evidence_future",
    "unsupported_provider_negative_evidence_future",
}

SAFE_METHODS = {"GET", "HEAD"}
MAX_TIMEOUT_MS = 10_000
MAX_RETRIES = 2
MAX_REDIRECTS = 0
DISALLOWED_PATH_MARKERS = {
    "/chat/completions",
    "/completions",
    "/embeddings",
    "/rerank",
    "/audio",
    "/images",
    "/responses",
}

FORBIDDEN_TRUTHY_FIELDS = {
    "authority": "authority_must_be_false",
    "runtime_dispatch_allowed": "runtime_dispatch_not_allowed",
    "approval_grant": "approval_grant_not_allowed",
    "capability_grant": "capability_grant_not_allowed",
    "lease_grant": "lease_grant_not_allowed",
    "lease_active": "lease_active_claim_denied",
    "lease_created": "lease_creation_claim_denied",
    "lease_used": "lease_use_claim_denied",
    "evidence_provided_by_probe_design": "probe_design_cannot_provide_evidence",
    "evidence_created": "probe_design_cannot_provide_evidence",
    "verifier_success": "probe_design_cannot_mark_verifier_success",
    "verified_success": "probe_design_cannot_mark_verifier_success",
    "success": "success_claim_denied",
    "proof": "proof_claim_denied",
    "certification_claim": "certification_claim_denied",
    "frontend_authority": "frontend_authority_not_allowed",
    "health_verified": "health_verification_claim_denied",
    "provider_selected_for_execution": "provider_execution_selection_denied",
    "model_selected_for_execution": "model_execution_selection_denied",
    "model_output_is_truth": "model_output_truth_claim_denied",
    "endpoint_reachable_is_task_success": "endpoint_reachability_task_success_claim_denied",
}

FORBIDDEN_BEHAVIOR_FIELDS = {
    "probe_executed": "probe_execution_denied",
    "endpoint_probed": "endpoint_probe_denied",
    "socket_opened": "socket_open_denied",
    "provider_authenticated": "provider_authentication_denied",
    "api_key_validated": "api_key_validation_denied",
    "secret_read": "secret_read_denied",
    "model_list_requested": "model_list_request_denied",
    "model_loaded": "model_load_denied",
    "model_call_performed": "model_call_denied",
    "minimal_generation_performed": "minimal_generation_denied",
    "embedding_generated": "embedding_generation_denied",
    "reranking_performed": "reranking_denied",
    "multimodal_probe_performed": "multimodal_probe_denied",
    "provider_process_inspected": "provider_process_inspection_denied",
    "live_model_files_inspected": "live_model_file_inspection_denied",
    "context_payload_sent": "context_payload_denied",
    "memory_payload_sent": "memory_payload_denied",
    "repo_payload_sent": "repo_payload_denied",
    "journal_payload_sent": "journal_payload_denied",
    "evidence_payload_sent": "evidence_payload_denied",
    "data_sent_external": "external_data_transfer_denied",
    "api_call_performed": "api_call_denied",
    "mcp_call_performed": "mcp_call_denied",
    "tool_call_performed": "tool_call_denied",
}


@dataclass(frozen=True)
class LocalProviderProbeDesignFailure:
    reason: str
    field: str
    message: str


@dataclass(frozen=True)
class ProbeConstraints:
    max_timeout_ms: int | None
    max_retries: int | None
    max_redirects: int | None
    allowed_methods: tuple[str, ...]
    allowed_paths: tuple[str, ...]
    disallowed_paths: tuple[str, ...]
    no_auth_required: bool
    no_secret_logging: bool
    no_prompt_payload: bool
    no_user_context_payload: bool
    no_repo_context_payload: bool
    no_memory_context_payload: bool
    no_raw_journal_payload: bool
    no_raw_evidence_payload: bool
    no_external_network: bool
    local_only: bool
    cancellable: bool
    rate_limited: bool
    requires_operator_review: bool
    requires_capability_lease_future: bool
    requires_policy_check: bool
    requires_negative_evidence_on_failure: bool


@dataclass(frozen=True)
class LocalProviderProbeDesignInput:
    request_id: str | None
    probe_target_class: str | None
    probe_phase: str | None
    endpoint_host_class: str | None
    namespace: str | None
    endpoint_ref: str | None
    provider_ref: str | None
    constraints: ProbeConstraints
    source_refs: tuple[Mapping[str, Any], ...]
    provenance: tuple[Mapping[str, Any], ...]
    limitations: tuple[str, ...]
    unknowns: tuple[str, ...]


@dataclass(frozen=True)
class LocalProviderProbeDesignDecision:
    contract_version: str
    probe_result_status: str
    request_id: str | None
    probe_target_class: str | None
    probe_phase: str | None
    endpoint_host_class: str | None
    namespace: str | None
    future_evidence_candidates: tuple[str, ...]
    future_negative_evidence_candidates: tuple[str, ...]
    required_future_gates: tuple[str, ...]
    failure_reasons: tuple[str, ...]
    failures: tuple[LocalProviderProbeDesignFailure, ...]
    probe_input: LocalProviderProbeDesignInput | None
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = LOCAL_PROVIDER_PROBE_DESIGN_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_probe_design: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    frontend_authority: bool = False
    probe_executed: bool = False
    endpoint_probed: bool = False
    socket_opened: bool = False
    provider_authenticated: bool = False
    api_key_validated: bool = False
    secret_read: bool = False
    model_list_requested: bool = False
    model_loaded: bool = False
    model_call_performed: bool = False
    minimal_generation_performed: bool = False
    embedding_generated: bool = False
    reranking_performed: bool = False
    multimodal_probe_performed: bool = False
    provider_process_inspected: bool = False
    live_model_files_inspected: bool = False
    context_payload_sent: bool = False
    memory_payload_sent: bool = False
    repo_payload_sent: bool = False
    journal_payload_sent: bool = False
    evidence_payload_sent: bool = False
    data_sent_external: bool = False
    health_verified: bool = False
    provider_selected_for_execution: bool = False
    model_selected_for_execution: bool = False
    requires_backend_validation: bool = True
    requires_policy_check: bool = True
    requires_human_review_for_unknowns: bool = True


def validate_local_provider_probe_design_request(
    request: Mapping[str, Any] | None,
    *,
    local_provider_health_decision: Any | None = None,
    capability_lease_decision: Any | None = None,
    model_auto_mode_decision: Any | None = None,
    context_policy_decision: Any | None = None,
    policy_extension_decision: Any | None = None,
    identity_scope_decision: Any | None = None,
    memory_governance_decision: Any | None = None,
    local_model_inventory_decision: Any | None = None,
    mission_control_decision: Any | None = None,
    tool_simulation_decision: Any | None = None,
) -> LocalProviderProbeDesignDecision:
    """Validate a future local provider probe design without executing a probe."""

    if not isinstance(request, Mapping):
        failure = LocalProviderProbeDesignFailure(
            reason="missing_request",
            field="request",
            message="local provider probe design request must be caller-supplied metadata",
        )
        return _decision(
            probe_result_status="unknown",
            request_id=None,
            probe_target_class=None,
            probe_phase=None,
            endpoint_host_class=None,
            namespace=None,
            future_evidence_candidates=(),
            future_negative_evidence_candidates=(),
            required_future_gates=(),
            failures=(failure,),
            probe_input=None,
        )

    data = deepcopy(dict(request))
    failures: list[LocalProviderProbeDesignFailure] = []
    _validate_forbidden_claims("request", data, failures)
    for label, decision in {
        "local_provider_health": local_provider_health_decision,
        "capability_lease": capability_lease_decision,
        "model_auto_mode": model_auto_mode_decision,
        "context_policy": context_policy_decision,
        "policy_extension": policy_extension_decision,
        "identity_scope": identity_scope_decision,
        "memory_governance": memory_governance_decision,
        "local_model_inventory": local_model_inventory_decision,
        "mission_control": mission_control_decision,
        "tool_simulation": tool_simulation_decision,
    }.items():
        _validate_related_decision(label, decision, failures)

    constraints = _constraints(data.get("probe_constraints", data))
    probe_input = LocalProviderProbeDesignInput(
        request_id=_text(data.get("request_id")),
        probe_target_class=_text(data.get("probe_target_class")),
        probe_phase=_text(data.get("probe_phase")),
        endpoint_host_class=_text(data.get("endpoint_host_class")),
        namespace=_text(data.get("namespace")),
        endpoint_ref=_text(data.get("endpoint_ref")),
        provider_ref=_text(data.get("provider_ref")),
        constraints=constraints,
        source_refs=_mapping_tuple(data.get("source_refs")),
        provenance=_mapping_tuple(data.get("provenance")),
        limitations=_text_tuple(data.get("limitations")),
        unknowns=_text_tuple(data.get("unknowns")),
    )

    _validate_required_fields(probe_input, failures)
    _validate_endpoint_boundary(probe_input, failures)
    _validate_probe_phase(probe_input, failures)
    _validate_constraints(probe_input, failures)
    _validate_related_requirements(
        probe_input,
        local_provider_health_decision=local_provider_health_decision,
        capability_lease_decision=capability_lease_decision,
        context_policy_decision=context_policy_decision,
        policy_extension_decision=policy_extension_decision,
        failures=failures,
    )

    return _decision(
        probe_result_status=_probe_result_status(probe_input, failures),
        request_id=probe_input.request_id,
        probe_target_class=probe_input.probe_target_class,
        probe_phase=probe_input.probe_phase,
        endpoint_host_class=probe_input.endpoint_host_class,
        namespace=probe_input.namespace,
        future_evidence_candidates=_future_evidence_candidates(probe_input),
        future_negative_evidence_candidates=_future_negative_evidence_candidates(probe_input),
        required_future_gates=_future_gates(probe_input, failures),
        failures=tuple(failures),
        probe_input=probe_input,
    )


def _decision(
    *,
    probe_result_status: str,
    request_id: str | None,
    probe_target_class: str | None,
    probe_phase: str | None,
    endpoint_host_class: str | None,
    namespace: str | None,
    future_evidence_candidates: tuple[str, ...],
    future_negative_evidence_candidates: tuple[str, ...],
    required_future_gates: tuple[str, ...],
    failures: tuple[LocalProviderProbeDesignFailure, ...],
    probe_input: LocalProviderProbeDesignInput | None,
) -> LocalProviderProbeDesignDecision:
    return LocalProviderProbeDesignDecision(
        contract_version=LOCAL_PROVIDER_PROBE_DESIGN_VERSION,
        probe_result_status=probe_result_status,
        request_id=request_id,
        probe_target_class=probe_target_class,
        probe_phase=probe_phase,
        endpoint_host_class=endpoint_host_class,
        namespace=namespace,
        future_evidence_candidates=future_evidence_candidates,
        future_negative_evidence_candidates=future_negative_evidence_candidates,
        required_future_gates=required_future_gates,
        failure_reasons=tuple(dict.fromkeys(f.reason for f in failures)),
        failures=failures,
        probe_input=probe_input,
    )


def _constraints(value: Any) -> ProbeConstraints:
    data = value if isinstance(value, Mapping) else {}
    return ProbeConstraints(
        max_timeout_ms=_int(data.get("max_timeout_ms")),
        max_retries=_int(data.get("max_retries")),
        max_redirects=_int(data.get("max_redirects")),
        allowed_methods=_upper_tuple(data.get("allowed_methods")),
        allowed_paths=_text_tuple(data.get("allowed_paths")),
        disallowed_paths=_text_tuple(data.get("disallowed_paths")),
        no_auth_required=_truthy(data.get("no_auth_required")),
        no_secret_logging=_truthy(data.get("no_secret_logging")),
        no_prompt_payload=_truthy(data.get("no_prompt_payload")),
        no_user_context_payload=_truthy(data.get("no_user_context_payload")),
        no_repo_context_payload=_truthy(data.get("no_repo_context_payload")),
        no_memory_context_payload=_truthy(data.get("no_memory_context_payload")),
        no_raw_journal_payload=_truthy(data.get("no_raw_journal_payload")),
        no_raw_evidence_payload=_truthy(data.get("no_raw_evidence_payload")),
        no_external_network=_truthy(data.get("no_external_network")),
        local_only=_truthy(data.get("local_only")),
        cancellable=_truthy(data.get("cancellable")),
        rate_limited=_truthy(data.get("rate_limited")),
        requires_operator_review=_truthy(data.get("requires_operator_review")),
        requires_capability_lease_future=_truthy(data.get("requires_capability_lease_future")),
        requires_policy_check=_truthy(data.get("requires_policy_check")),
        requires_negative_evidence_on_failure=_truthy(data.get("requires_negative_evidence_on_failure")),
    )


def _validate_required_fields(
    probe_input: LocalProviderProbeDesignInput,
    failures: list[LocalProviderProbeDesignFailure],
) -> None:
    required = {
        "request_id": probe_input.request_id,
        "probe_target_class": probe_input.probe_target_class,
        "probe_phase": probe_input.probe_phase,
        "endpoint_host_class": probe_input.endpoint_host_class,
        "namespace": probe_input.namespace,
        "max_timeout_ms": probe_input.constraints.max_timeout_ms,
        "max_retries": probe_input.constraints.max_retries,
    }
    for field, value in required.items():
        if value is None or value == "":
            _add_failure(failures, f"missing_{field}", field, f"{field} is required")
    if probe_input.probe_target_class and probe_input.probe_target_class not in PROBE_TARGET_CLASSES:
        _add_failure(failures, "unsupported_probe_target_class", "probe_target_class", "probe target class is not recognized")
    if probe_input.probe_phase and probe_input.probe_phase not in PROBE_PHASES:
        _add_failure(failures, "unsupported_probe_phase", "probe_phase", "probe phase is not recognized")
    if probe_input.endpoint_host_class and probe_input.endpoint_host_class not in ENDPOINT_HOST_CLASSES:
        _add_failure(failures, "unsupported_endpoint_host_class", "endpoint_host_class", "endpoint host class is not recognized")


def _validate_endpoint_boundary(
    probe_input: LocalProviderProbeDesignInput,
    failures: list[LocalProviderProbeDesignFailure],
) -> None:
    if probe_input.probe_target_class in {"unsupported_remote", "unsupported_cloud"}:
        _add_failure(failures, "unsupported_provider_target_blocked", "probe_target_class", "remote/cloud providers are blocked")
    if probe_input.probe_target_class == "unknown":
        _add_failure(failures, "unknown_probe_target_blocked", "probe_target_class", "unknown provider target is blocked")
    if probe_input.endpoint_host_class in {"lan", "remote", "cloud"}:
        _add_failure(failures, "endpoint_host_blocked", "endpoint_host_class", "LAN, remote, and cloud endpoints are blocked")
    if probe_input.endpoint_host_class == "unknown":
        _add_failure(failures, "unknown_endpoint_host_blocked", "endpoint_host_class", "unknown endpoint host is blocked")


def _validate_probe_phase(
    probe_input: LocalProviderProbeDesignInput,
    failures: list[LocalProviderProbeDesignFailure],
) -> None:
    phase = probe_input.probe_phase
    if phase in BLOCKED_PROBE_PHASES:
        _add_failure(failures, "probe_phase_blocked_for_now", "probe_phase", "generation, embedding, reranker, and multimodal probes are blocked for now")
    if phase == "unknown":
        _add_failure(failures, "unknown_probe_phase_blocked", "probe_phase", "unknown probe phase is blocked")
    if phase == "model_list_probe_future":
        paths = set(probe_input.constraints.allowed_paths)
        if paths and not paths.issubset({"/v1/models", "/api/tags"}):
            _add_failure(failures, "model_list_path_not_metadata_only", "allowed_paths", "model list probe design must stay on metadata-only paths")


def _validate_constraints(
    probe_input: LocalProviderProbeDesignInput,
    failures: list[LocalProviderProbeDesignFailure],
) -> None:
    constraints = probe_input.constraints
    required_true = {
        "local_only": constraints.local_only,
        "no_secret_logging": constraints.no_secret_logging,
        "no_prompt_payload": constraints.no_prompt_payload,
        "no_user_context_payload": constraints.no_user_context_payload,
        "no_repo_context_payload": constraints.no_repo_context_payload,
        "no_memory_context_payload": constraints.no_memory_context_payload,
        "no_raw_journal_payload": constraints.no_raw_journal_payload,
        "no_raw_evidence_payload": constraints.no_raw_evidence_payload,
        "no_external_network": constraints.no_external_network,
        "cancellable": constraints.cancellable,
        "rate_limited": constraints.rate_limited,
        "requires_policy_check": constraints.requires_policy_check,
        "requires_negative_evidence_on_failure": constraints.requires_negative_evidence_on_failure,
    }
    for field, value in required_true.items():
        if not value:
            _add_failure(failures, f"{field}_required", field, f"{field} must be true")
    if constraints.max_timeout_ms is not None:
        if constraints.max_timeout_ms <= 0:
            _add_failure(failures, "invalid_timeout_policy", "max_timeout_ms", "timeout must be positive")
        elif constraints.max_timeout_ms > MAX_TIMEOUT_MS:
            _add_failure(failures, "timeout_policy_too_broad", "max_timeout_ms", "timeout exceeds design limit")
    if constraints.max_retries is not None:
        if constraints.max_retries < 0:
            _add_failure(failures, "invalid_retry_policy", "max_retries", "retries cannot be negative")
        elif constraints.max_retries > MAX_RETRIES:
            _add_failure(failures, "retry_policy_too_broad", "max_retries", "retries exceed design limit")
    if constraints.max_redirects is not None and constraints.max_redirects > MAX_REDIRECTS:
        _add_failure(failures, "redirects_not_allowed", "max_redirects", "redirects are not allowed for local provider probe design")
    if not constraints.allowed_methods:
        _add_failure(failures, "missing_allowed_methods", "allowed_methods", "allowed methods are required")
    if any(method not in SAFE_METHODS for method in constraints.allowed_methods):
        _add_failure(failures, "unsafe_method_blocked", "allowed_methods", "only GET/HEAD metadata methods are allowed")
    if any(_path_is_disallowed(path) for path in constraints.allowed_paths):
        _add_failure(failures, "unsafe_probe_path_blocked", "allowed_paths", "generation, embedding, rerank, multimodal, and response paths are blocked")
    if not any(path in constraints.disallowed_paths for path in {"/v1/chat/completions", "/v1/embeddings"}):
        _add_failure(failures, "missing_disallowed_generation_paths", "disallowed_paths", "generation and embedding paths must be explicitly disallowed")
    if not constraints.no_auth_required:
        _add_failure(failures, "auth_requirement_blocked", "no_auth_required", "first local provider probe design must not require auth or secrets")


def _validate_related_requirements(
    probe_input: LocalProviderProbeDesignInput,
    *,
    local_provider_health_decision: Any | None,
    capability_lease_decision: Any | None,
    context_policy_decision: Any | None,
    policy_extension_decision: Any | None,
    failures: list[LocalProviderProbeDesignFailure],
) -> None:
    if local_provider_health_decision is None:
        _add_failure(failures, "missing_local_provider_health_readiness", "local_provider_health_decision", "local provider health readiness is required")
    elif _status_blocked(local_provider_health_decision, "readiness_status"):
        _add_failure(failures, "local_provider_health_readiness_not_ready", "local_provider_health_decision.readiness_status", "local provider health readiness is blocked")
    if probe_input.constraints.requires_capability_lease_future:
        if capability_lease_decision is None:
            _add_failure(failures, "missing_capability_lease_candidate", "capability_lease_decision", "future repeated probes require lease candidate metadata")
        elif _field_bool(capability_lease_decision, "lease_active") or _field_bool(capability_lease_decision, "lease_used"):
            _add_failure(failures, "active_lease_claim_denied", "capability_lease_decision", "current lease candidates cannot activate probes")
    if context_policy_decision is not None and _status_blocked(context_policy_decision, "policy_status"):
        _add_failure(failures, "context_policy_not_ready", "context_policy_decision.policy_status", "blocked context policy cannot be contradicted")
    if policy_extension_decision is not None and _status_blocked(policy_extension_decision, "policy_outcome"):
        _add_failure(failures, "policy_extension_not_ready", "policy_extension_decision.policy_outcome", "blocked policy extension cannot be contradicted")


def _validate_related_decision(
    label: str,
    decision: Any | None,
    failures: list[LocalProviderProbeDesignFailure],
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
            f"{label} cannot grant probe authority, execution, evidence, verifier success, provider/model selection, payload transfer, or active behavior",
        )


def _validate_forbidden_claims(
    label: str,
    source: Any,
    failures: list[LocalProviderProbeDesignFailure],
) -> None:
    for field, reason in FORBIDDEN_TRUTHY_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(failures, reason, f"{label}.{field}", "authority, grants, evidence, verifier, proof, health verification, or selection claims are denied")
    for field, reason in FORBIDDEN_BEHAVIOR_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(failures, reason, f"{label}.{field}", "probe execution, sockets, auth, model behavior, payload transfer, API, MCP, or tool behavior is denied")
    execution_permission = _field_value(source, "execution_permission")
    if execution_permission not in (None, "", LOCAL_PROVIDER_PROBE_DESIGN_EXECUTION_PERMISSION):
        permission_text = str(execution_permission)
        if not permission_text.startswith("not_granted"):
            _add_failure(failures, "execution_permission_claim_denied", f"{label}.execution_permission", "provider probe design cannot grant execution permission")


def _probe_result_status(
    probe_input: LocalProviderProbeDesignInput,
    failures: list[LocalProviderProbeDesignFailure],
) -> str:
    reasons = {failure.reason for failure in failures}
    if reasons:
        if "missing_local_provider_health_readiness" in reasons:
            return "blocked_by_missing_provider_health_readiness"
        if "missing_capability_lease_candidate" in reasons:
            return "blocked_by_missing_lease"
        if any("missing_" in reason for reason in reasons):
            return "unsupported"
        if "policy_extension_not_ready" in reasons:
            return "blocked_by_policy"
        if any("endpoint" in reason or "provider_target" in reason for reason in reasons):
            return "blocked_by_endpoint_host"
        if any("secret" in reason or "auth" in reason or "api_key" in reason for reason in reasons):
            return "blocked_by_secret_boundary"
        if any("timeout" in reason or "retry" in reason or "redirect" in reason for reason in reasons):
            return "blocked_by_timeout_policy"
        if any("unknown" in reason for reason in reasons):
            return "blocked_by_unknown_metadata"
        return "blocked_by_policy"
    if probe_input.probe_phase in FUTURE_PROBE_PHASES:
        return "future_probe_candidate"
    return "design_only"


def _future_evidence_candidates(probe_input: LocalProviderProbeDesignInput) -> tuple[str, ...]:
    candidates = ["provider_probe_attempt_future"]
    if probe_input.probe_phase == "endpoint_reachability_probe_future":
        candidates.extend(("endpoint_reachable_future", "endpoint_unreachable_future"))
    if probe_input.probe_phase == "provider_metadata_probe_future":
        candidates.append("provider_metadata_response_future")
    if probe_input.probe_phase == "model_list_probe_future":
        candidates.append("model_list_response_future")
    return tuple(candidate for candidate in candidates if candidate in FUTURE_EVIDENCE_TYPES)


def _future_negative_evidence_candidates(probe_input: LocalProviderProbeDesignInput) -> tuple[str, ...]:
    del probe_input
    return (
        "timeout_negative_evidence_future",
        "refused_connection_negative_evidence_future",
        "invalid_response_negative_evidence_future",
        "unauthorized_negative_evidence_future",
        "unsupported_provider_negative_evidence_future",
    )


def _future_gates(
    probe_input: LocalProviderProbeDesignInput,
    failures: list[LocalProviderProbeDesignFailure],
) -> tuple[str, ...]:
    gates = ["requires_future_probe_implementation_boundary"]
    if probe_input.probe_phase == "model_list_probe_future":
        gates.append("requires_future_model_list_gate")
    if probe_input.probe_phase == "model_role_match_probe_future":
        gates.append("requires_future_model_inventory_role_match_gate")
    if probe_input.constraints.requires_capability_lease_future:
        gates.append("requires_future_capability_lease_use_boundary")
    if any("unknown" in failure.reason for failure in failures):
        gates.append("unknown_metadata_requires_human_review")
    return tuple(dict.fromkeys(gates))


def _path_is_disallowed(path: str) -> bool:
    lowered = path.lower().strip()
    return any(marker in lowered for marker in DISALLOWED_PATH_MARKERS)


def _status_blocked(decision: Any, field: str) -> bool:
    status = str(_field_value(decision, field) or "")
    return status.startswith("blocked") or status in {"unsupported", "unknown", "clarification_required"}


def _mapping_tuple(value: Any) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(deepcopy(item) for item in value if isinstance(item, Mapping))


def _upper_tuple(value: Any) -> tuple[str, ...]:
    return tuple(item.upper() for item in _text_tuple(value))


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


def _int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
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


def _add_failure(
    failures: list[LocalProviderProbeDesignFailure],
    reason: str,
    field: str,
    message: str,
) -> None:
    failures.append(LocalProviderProbeDesignFailure(reason=reason, field=field, message=message))
