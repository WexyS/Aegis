from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping


LOCAL_PROVIDER_HEALTH_VERSION = "local-provider-health-check-readiness/1"
LOCAL_PROVIDER_HEALTH_EXECUTION_PERMISSION = "not_granted_by_local_provider_health"

PROVIDER_CLASSES = {
    "lm_studio_local",
    "ollama_local_optional",
    "vllm_local",
    "openai_compatible_local",
    "llama_cpp_local_future",
    "mlx_local_future",
    "mock_test_provider",
    "offline_disabled_provider",
    "unknown",
}

PROVIDER_HEALTH_STATUSES = {
    "not_checked",
    "metadata_only",
    "configured_metadata_only",
    "offline_disabled",
    "not_configured",
    "endpoint_unknown",
    "endpoint_unverified",
    "endpoint_reachable_unverified_future",
    "endpoint_unreachable_metadata_only",
    "provider_process_unknown",
    "provider_process_not_observed",
    "provider_process_observed_metadata_only",
    "resource_blocked",
    "disk_pressure_blocked",
    "disabled_by_policy",
    "future_gated",
    "unknown",
}

MODEL_HEALTH_STATUSES = {
    "model_metadata_only",
    "model_listed_unverified_future",
    "model_not_listed_metadata_only",
    "model_load_not_attempted",
    "model_loaded_unverified_future",
    "model_unavailable_metadata_only",
    "model_role_mismatch",
    "model_modality_future_gated",
    "model_resource_unknown",
    "model_resource_blocked",
    "unknown",
}

HEALTH_CHECK_PHASES = {
    "classify_metadata_only",
    "validate_config_shape",
    "propose_endpoint_probe_future",
    "propose_model_list_future",
    "propose_model_load_future",
    "propose_minimal_generation_future",
    "propose_embedding_probe_future",
    "propose_reranker_probe_future",
    "propose_multimodal_probe_future",
    "unknown",
}

ENDPOINT_HOST_CLASSES = {"localhost", "loopback", "lan", "remote", "cloud", "unknown"}

MODEL_ROLES = {
    "chat_general",
    "coding",
    "reasoning",
    "summarization",
    "translation_terminology",
    "embedding",
    "reranker",
    "vision",
    "audio_stt",
    "audio_tts",
    "multimodal",
    "safety_classifier",
    "small_utility",
    "unknown",
}

MODEL_MODALITIES = {
    "text_in_text_out",
    "text_embedding",
    "text_rerank",
    "image_text",
    "audio_text",
    "text_audio",
    "multimodal",
    "unknown",
}

TASK_ROLES = {
    "mission_control_wording",
    "tool_simulation_explanation",
    "repo_audit_candidate_notes",
    "code_explanation",
    "architecture_review",
    "risk_analysis",
    "documentation_summary",
    "translation_terminology",
    "context_retrieval",
    "context_reranking",
    "visual_analysis_future_gated",
    "voice_interaction_future_gated",
    "unknown",
}

LOCAL_ENDPOINT_HOST_CLASSES = {"localhost", "loopback"}
REMOTE_ENDPOINT_HOST_CLASSES = {"lan", "remote", "cloud"}
FUTURE_PROVIDER_CLASSES = {"llama_cpp_local_future", "mlx_local_future"}
FUTURE_HEALTH_PHASES = {
    "propose_endpoint_probe_future",
    "propose_model_list_future",
    "propose_model_load_future",
    "propose_minimal_generation_future",
    "propose_embedding_probe_future",
    "propose_reranker_probe_future",
    "propose_multimodal_probe_future",
}
FUTURE_MODALITIES = {"image_text", "audio_text", "text_audio", "multimodal"}
RESOURCE_BLOCKED_STATUSES = {"resource_blocked", "disk_pressure_blocked"}
LOW_TRUST_CONFIG_SOURCES = {"frontend", "frontend_projection", "user_supplied_untrusted"}

ROLE_EXPECTED_MODALITY = {
    "chat_general": {"text_in_text_out"},
    "coding": {"text_in_text_out"},
    "reasoning": {"text_in_text_out"},
    "summarization": {"text_in_text_out"},
    "translation_terminology": {"text_in_text_out"},
    "embedding": {"text_embedding"},
    "reranker": {"text_rerank"},
    "vision": {"image_text", "multimodal"},
    "audio_stt": {"audio_text", "multimodal"},
    "audio_tts": {"text_audio", "multimodal"},
    "multimodal": {"multimodal", "image_text"},
    "safety_classifier": {"text_in_text_out"},
    "small_utility": {"text_in_text_out"},
}

ROLE_EXPECTED_TASKS = {
    "chat_general": {"mission_control_wording", "tool_simulation_explanation", "documentation_summary"},
    "coding": {"repo_audit_candidate_notes", "code_explanation", "architecture_review"},
    "reasoning": {"risk_analysis", "architecture_review", "repo_audit_candidate_notes"},
    "summarization": {"documentation_summary", "mission_control_wording"},
    "translation_terminology": {"translation_terminology"},
    "embedding": {"context_retrieval"},
    "reranker": {"context_reranking"},
    "vision": {"visual_analysis_future_gated"},
    "audio_stt": {"voice_interaction_future_gated"},
    "audio_tts": {"voice_interaction_future_gated"},
    "multimodal": {"visual_analysis_future_gated"},
    "safety_classifier": {"risk_analysis"},
    "small_utility": {"mission_control_wording", "documentation_summary"},
}

FORBIDDEN_TRUTHY_FIELDS = {
    "authority": "authority_must_be_false",
    "runtime_dispatch_allowed": "runtime_dispatch_not_allowed",
    "approval_grant": "approval_grant_not_allowed",
    "capability_grant": "capability_grant_not_allowed",
    "lease_grant": "lease_grant_not_allowed",
    "frontend_authority": "frontend_authority_not_allowed",
    "output_is_authority": "provider_health_output_cannot_be_authority",
    "evidence_provided_by_provider_health": "provider_health_cannot_provide_evidence",
    "evidence_provided_by_inventory": "provider_health_cannot_provide_evidence",
    "evidence_created": "provider_health_cannot_provide_evidence",
    "verifier_success": "provider_health_cannot_mark_verifier_success",
    "verified_success": "provider_health_cannot_mark_verifier_success",
    "health_verified": "provider_health_cannot_verify_health",
    "success": "success_claim_denied",
    "proof": "proof_claim_denied",
    "certification_claim": "certification_claim_denied",
    "provider_selected_for_execution": "provider_execution_selection_not_allowed",
    "model_selected_for_execution": "model_execution_selection_not_allowed",
}

FORBIDDEN_BEHAVIOR_FIELDS = {
    "endpoint_probed": "endpoint_probe_request_denied",
    "probe_endpoint": "endpoint_probe_request_denied",
    "provider_process_inspected": "provider_process_inspection_denied",
    "inspect_provider_process": "provider_process_inspection_denied",
    "provider_authenticated": "provider_authentication_denied",
    "api_key_validated": "api_key_validation_denied",
    "secret_read": "secret_read_denied",
    "model_list_requested": "model_list_request_denied",
    "model_loaded": "model_load_request_denied",
    "load_model": "model_load_request_denied",
    "model_call_performed": "model_call_request_denied",
    "minimal_generation_performed": "minimal_generation_request_denied",
    "embedding_generated": "embedding_generation_request_denied",
    "reranking_performed": "reranking_request_denied",
    "multimodal_probe_performed": "multimodal_probe_request_denied",
    "context_retrieval_performed": "context_retrieval_request_denied",
    "memory_retrieval_performed": "memory_retrieval_request_denied",
    "data_sent_external": "external_data_transfer_denied",
    "api_call_performed": "api_call_request_denied",
    "mcp_call_performed": "mcp_call_request_denied",
    "tool_call_performed": "tool_call_request_denied",
    "health_check_executed": "health_check_execution_denied",
}

PROOF_FIELDS = {
    "provider_health_is_truth": "provider_health_truth_claim_denied",
    "model_available_as_truth": "model_availability_truth_claim_denied",
    "model_output_is_truth": "model_output_truth_claim_denied",
    "model_output_as_evidence": "model_output_evidence_claim_denied",
    "model_output_as_policy": "model_output_policy_claim_denied",
    "proof_provider_available": "provider_availability_proof_denied",
    "proof_model_available": "model_availability_proof_denied",
    "proof_model_quality": "model_quality_proof_denied",
    "proof_model_health": "model_health_proof_denied",
    "security_certification": "security_certification_claim_denied",
    "compliance_certification": "compliance_certification_claim_denied",
}


@dataclass(frozen=True)
class LocalProviderHealthFailure:
    reason: str
    field: str
    message: str


@dataclass(frozen=True)
class ProviderConfigMetadata:
    provider_id: str | None
    provider_class: str | None
    provider_label: str | None
    provider_health_status: str | None
    endpoint_ref: str | None
    endpoint_scheme: str | None
    endpoint_host_class: str | None
    endpoint_port: int | None
    api_key_required: bool
    secret_status: str | None
    dependency_status: str | None
    config_source: str | None
    config_trust_level: str
    process_observation_status: str | None
    resource_status: str | None
    disk_status: str | None
    ram_status: str | None
    vram_status: str | None
    supported_model_roles: tuple[str, ...]
    supported_modalities: tuple[str, ...]
    limitations: tuple[str, ...]
    unknowns: tuple[str, ...]
    source_refs: tuple[Mapping[str, Any], ...]


@dataclass(frozen=True)
class ProviderModelHealthMetadata:
    model_id: str | None
    model_name: str | None
    model_role: str | None
    model_modality: str | None
    model_health_status: str | None
    task_roles: tuple[str, ...]
    resource_status: str | None
    listed_unverified: bool
    active_probe_requested: bool
    future_gated: bool
    limitations: tuple[str, ...]
    unknowns: tuple[str, ...]


@dataclass(frozen=True)
class LocalProviderHealthInput:
    request_id: str | None
    project_ref: str | None
    tenant_scope: str | None
    namespace: str | None
    health_check_phase: str | None
    human_review_required: bool
    provider_config: ProviderConfigMetadata
    model_metadata: tuple[ProviderModelHealthMetadata, ...]
    limitations: tuple[str, ...]
    unknowns: tuple[str, ...]
    source_refs: tuple[Mapping[str, Any], ...]
    policy_refs: tuple[str, ...]


@dataclass(frozen=True)
class LocalProviderHealthDecision:
    contract_version: str
    readiness_status: str
    request_id: str | None
    project_ref: str | None
    tenant_scope: str | None
    namespace: str | None
    provider_id: str | None
    provider_class: str | None
    provider_health_status: str
    model_health_status: str
    health_check_phase: str | None
    endpoint_host_class: str | None
    config_trust_level: str
    lower_trust_config_source: bool
    required_future_gates: tuple[str, ...]
    failure_reasons: tuple[str, ...]
    failures: tuple[LocalProviderHealthFailure, ...]
    provider_config: ProviderConfigMetadata | None
    model_metadata: tuple[ProviderModelHealthMetadata, ...]
    health_input: LocalProviderHealthInput | None
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = LOCAL_PROVIDER_HEALTH_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_provider_health: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    frontend_authority: bool = False
    endpoint_probed: bool = False
    provider_process_inspected: bool = False
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
    context_retrieval_performed: bool = False
    memory_retrieval_performed: bool = False
    data_sent_external: bool = False
    provider_selected_for_execution: bool = False
    model_selected_for_execution: bool = False
    health_verified: bool = False
    health_check_executed: bool = False
    output_is_authority: bool = False
    requires_backend_validation: bool = True
    requires_policy_check: bool = True
    requires_human_review_for_unknowns: bool = True


def validate_local_provider_health_request(
    request: Mapping[str, Any] | None,
    *,
    local_model_inventory_decision: Any | None = None,
    model_auto_mode_decision: Any | None = None,
    context_policy_decision: Any | None = None,
    policy_extension_decision: Any | None = None,
    identity_scope_decision: Any | None = None,
    memory_governance_decision: Any | None = None,
    foundation_config_dependency_hygiene_decision: Any | None = None,
    mission_control_decision: Any | None = None,
    tool_simulation_decision: Any | None = None,
) -> LocalProviderHealthDecision:
    """Classify local provider health metadata without probing or calling providers."""

    if not isinstance(request, Mapping):
        failure = LocalProviderHealthFailure(
            reason="missing_request",
            field="request",
            message="local provider health request must be caller-supplied metadata",
        )
        return _decision(
            readiness_status="clarification_required",
            request_id=None,
            project_ref=None,
            tenant_scope=None,
            namespace=None,
            provider_id=None,
            provider_class=None,
            provider_health_status="unknown",
            model_health_status="unknown",
            health_check_phase=None,
            endpoint_host_class=None,
            config_trust_level="unknown",
            lower_trust_config_source=False,
            required_future_gates=(),
            failures=(failure,),
            provider_config=None,
            model_metadata=(),
            health_input=None,
        )

    data = deepcopy(dict(request))
    failures: list[LocalProviderHealthFailure] = []
    _validate_forbidden_claims("request", data, failures)
    for label, decision in {
        "local_model_inventory": local_model_inventory_decision,
        "model_auto_mode": model_auto_mode_decision,
        "context_policy": context_policy_decision,
        "policy_extension": policy_extension_decision,
        "identity_scope": identity_scope_decision,
        "memory_governance": memory_governance_decision,
        "foundation_config_dependency_hygiene": foundation_config_dependency_hygiene_decision,
        "mission_control": mission_control_decision,
        "tool_simulation": tool_simulation_decision,
    }.items():
        _validate_related_decision(label, decision, failures)

    provider_config = _provider_config(data)
    model_metadata = _model_metadata(data.get("models", data.get("model_metadata")))
    health_input = LocalProviderHealthInput(
        request_id=_text(data.get("request_id")),
        project_ref=_text(data.get("project_ref")),
        tenant_scope=_text(data.get("tenant_scope")),
        namespace=_text(data.get("namespace")),
        health_check_phase=_text(data.get("health_check_phase")),
        human_review_required=_truthy(data.get("human_review_required")),
        provider_config=provider_config,
        model_metadata=model_metadata,
        limitations=_text_tuple(data.get("limitations")),
        unknowns=_text_tuple(data.get("unknowns")),
        source_refs=_mapping_tuple(data.get("source_refs")),
        policy_refs=_text_tuple(data.get("policy_refs")),
    )

    _validate_required_fields(health_input, failures)
    _validate_provider_policy(health_input, failures)
    _validate_model_policy(health_input, failures)
    _validate_related_statuses(
        context_policy_decision=context_policy_decision,
        policy_extension_decision=policy_extension_decision,
        foundation_config_dependency_hygiene_decision=foundation_config_dependency_hygiene_decision,
        failures=failures,
    )

    future_gates = _future_gates(health_input, failures)
    return _decision(
        readiness_status=_readiness_status(health_input, failures, future_gates),
        request_id=health_input.request_id,
        project_ref=health_input.project_ref,
        tenant_scope=health_input.tenant_scope,
        namespace=health_input.namespace,
        provider_id=provider_config.provider_id,
        provider_class=provider_config.provider_class,
        provider_health_status=_provider_health_status(health_input, failures, future_gates),
        model_health_status=_aggregate_model_health_status(model_metadata, failures, future_gates),
        health_check_phase=health_input.health_check_phase,
        endpoint_host_class=provider_config.endpoint_host_class,
        config_trust_level=provider_config.config_trust_level,
        lower_trust_config_source=provider_config.config_source in LOW_TRUST_CONFIG_SOURCES,
        required_future_gates=future_gates,
        failures=tuple(failures),
        provider_config=provider_config,
        model_metadata=model_metadata,
        health_input=health_input,
    )


def _decision(
    *,
    readiness_status: str,
    request_id: str | None,
    project_ref: str | None,
    tenant_scope: str | None,
    namespace: str | None,
    provider_id: str | None,
    provider_class: str | None,
    provider_health_status: str,
    model_health_status: str,
    health_check_phase: str | None,
    endpoint_host_class: str | None,
    config_trust_level: str,
    lower_trust_config_source: bool,
    required_future_gates: tuple[str, ...],
    failures: tuple[LocalProviderHealthFailure, ...],
    provider_config: ProviderConfigMetadata | None,
    model_metadata: tuple[ProviderModelHealthMetadata, ...],
    health_input: LocalProviderHealthInput | None,
) -> LocalProviderHealthDecision:
    return LocalProviderHealthDecision(
        contract_version=LOCAL_PROVIDER_HEALTH_VERSION,
        readiness_status=readiness_status,
        request_id=request_id,
        project_ref=project_ref,
        tenant_scope=tenant_scope,
        namespace=namespace,
        provider_id=provider_id,
        provider_class=provider_class,
        provider_health_status=provider_health_status,
        model_health_status=model_health_status,
        health_check_phase=health_check_phase,
        endpoint_host_class=endpoint_host_class,
        config_trust_level=config_trust_level,
        lower_trust_config_source=lower_trust_config_source,
        required_future_gates=required_future_gates,
        failure_reasons=tuple(dict.fromkeys(f.reason for f in failures)),
        failures=failures,
        provider_config=provider_config,
        model_metadata=model_metadata,
        health_input=health_input,
    )


def _provider_config(data: Mapping[str, Any]) -> ProviderConfigMetadata:
    provider_data = data.get("provider_config")
    provider_map = provider_data if isinstance(provider_data, Mapping) else data
    config_source = _text(provider_map.get("config_source"))
    return ProviderConfigMetadata(
        provider_id=_text(provider_map.get("provider_id")),
        provider_class=_text(provider_map.get("provider_class")),
        provider_label=_text(provider_map.get("provider_label")),
        provider_health_status=_text(provider_map.get("provider_health_status", provider_map.get("provider_status"))),
        endpoint_ref=_text(provider_map.get("endpoint_ref")),
        endpoint_scheme=_text(provider_map.get("endpoint_scheme")),
        endpoint_host_class=_text(provider_map.get("endpoint_host_class")),
        endpoint_port=_int(provider_map.get("endpoint_port")),
        api_key_required=_truthy(provider_map.get("api_key_required")),
        secret_status=_text(provider_map.get("secret_status")),
        dependency_status=_text(provider_map.get("dependency_status")),
        config_source=config_source,
        config_trust_level=_config_trust_level(config_source),
        process_observation_status=_text(provider_map.get("process_observation_status")),
        resource_status=_text(provider_map.get("resource_status")),
        disk_status=_text(provider_map.get("disk_status")),
        ram_status=_text(provider_map.get("ram_status")),
        vram_status=_text(provider_map.get("vram_status")),
        supported_model_roles=_text_tuple(provider_map.get("supported_model_roles")),
        supported_modalities=_text_tuple(provider_map.get("supported_modalities")),
        limitations=_text_tuple(provider_map.get("limitations")),
        unknowns=_text_tuple(provider_map.get("unknowns")),
        source_refs=_mapping_tuple(provider_map.get("source_refs")),
    )


def _model_metadata(value: Any) -> tuple[ProviderModelHealthMetadata, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    models: list[ProviderModelHealthMetadata] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        role = _text(item.get("model_role"))
        modality = _text(item.get("model_modality"))
        models.append(
            ProviderModelHealthMetadata(
                model_id=_text(item.get("model_id")),
                model_name=_text(item.get("model_name")),
                model_role=role,
                model_modality=modality,
                model_health_status=_text(item.get("model_health_status")),
                task_roles=_text_tuple(item.get("task_roles")),
                resource_status=_text(item.get("resource_status")),
                listed_unverified=_truthy(item.get("listed_unverified")),
                active_probe_requested=_truthy(item.get("active_probe_requested")),
                future_gated=bool(role in {"vision", "audio_stt", "audio_tts", "multimodal"} or modality in FUTURE_MODALITIES),
                limitations=_text_tuple(item.get("limitations")),
                unknowns=_text_tuple(item.get("unknowns")),
            )
        )
    return tuple(models)


def _validate_required_fields(
    health_input: LocalProviderHealthInput,
    failures: list[LocalProviderHealthFailure],
) -> None:
    required = {
        "request_id": health_input.request_id,
        "project_ref": health_input.project_ref,
        "tenant_scope": health_input.tenant_scope,
        "namespace": health_input.namespace,
        "health_check_phase": health_input.health_check_phase,
        "provider_id": health_input.provider_config.provider_id,
        "provider_class": health_input.provider_config.provider_class,
    }
    for field, value in required.items():
        if not value:
            _add_failure(failures, f"missing_{field}", field, f"{field} is required")
    phase = health_input.health_check_phase
    if phase and phase not in HEALTH_CHECK_PHASES:
        _add_failure(failures, "unsupported_health_check_phase", "health_check_phase", "health check phase is not recognized")


def _validate_provider_policy(
    health_input: LocalProviderHealthInput,
    failures: list[LocalProviderHealthFailure],
) -> None:
    config = health_input.provider_config
    if config.provider_class and config.provider_class not in PROVIDER_CLASSES:
        _add_failure(failures, "unsupported_provider_class", "provider_class", "provider class is not recognized")
    if config.provider_health_status and config.provider_health_status not in PROVIDER_HEALTH_STATUSES:
        _add_failure(failures, "unsupported_provider_health_status", "provider_health_status", "provider health status is not recognized")
    if config.endpoint_host_class and config.endpoint_host_class not in ENDPOINT_HOST_CLASSES:
        _add_failure(failures, "unsupported_endpoint_host_class", "endpoint_host_class", "endpoint host class is not recognized")
    if config.provider_class == "offline_disabled_provider":
        return
    if not config.endpoint_host_class:
        _add_failure(failures, "missing_endpoint_host_class", "endpoint_host_class", "endpoint host class is required for local provider metadata")
    if config.endpoint_host_class in REMOTE_ENDPOINT_HOST_CLASSES:
        _add_failure(failures, "non_local_endpoint_host_blocked", "endpoint_host_class", "LAN, remote, and cloud hosts are blocked in local provider health readiness")
    if config.endpoint_host_class == "unknown" and not health_input.human_review_required:
        _add_failure(failures, "unknown_endpoint_requires_human_review", "endpoint_host_class", "unknown endpoint host requires human review")
    if config.api_key_required:
        _add_failure(failures, "api_key_requirement_out_of_scope", "api_key_required", "API key validation is out of scope for local provider health readiness")
    if config.secret_status not in {None, "", "no_secret_required", "unknown", "not_applicable"}:
        _add_failure(failures, "secret_status_out_of_scope", "secret_status", "secret presence or validation is out of scope")
    if config.provider_health_status in RESOURCE_BLOCKED_STATUSES or config.resource_status in RESOURCE_BLOCKED_STATUSES:
        _add_failure(failures, "provider_resource_blocked", "resource_status", "provider resources are blocked by metadata")
    if config.disk_status == "disk_pressure_blocked":
        _add_failure(failures, "provider_disk_pressure_blocked", "disk_status", "disk pressure blocks careless provider expansion")


def _validate_model_policy(
    health_input: LocalProviderHealthInput,
    failures: list[LocalProviderHealthFailure],
) -> None:
    phase = health_input.health_check_phase
    if phase != "classify_metadata_only" and not health_input.model_metadata:
        _add_failure(failures, "missing_model_metadata", "models", "non-passive provider readiness requires model metadata")
    for index, model in enumerate(health_input.model_metadata):
        prefix = f"models[{index}]"
        if not model.model_id:
            _add_failure(failures, "missing_model_id", f"{prefix}.model_id", "model_id is required")
        if not model.model_name:
            _add_failure(failures, "missing_model_name", f"{prefix}.model_name", "model_name is required")
        if not model.model_role:
            _add_failure(failures, "missing_model_role", f"{prefix}.model_role", "model_role is required")
        elif model.model_role not in MODEL_ROLES:
            _add_failure(failures, "unsupported_model_role", f"{prefix}.model_role", "model role is not recognized")
        elif model.model_role == "unknown" and not health_input.human_review_required:
            _add_failure(failures, "unknown_model_role_requires_human_review", f"{prefix}.model_role", "unknown model role requires human review")
        if not model.model_modality:
            _add_failure(failures, "missing_model_modality", f"{prefix}.model_modality", "model_modality is required")
        elif model.model_modality not in MODEL_MODALITIES:
            _add_failure(failures, "unsupported_model_modality", f"{prefix}.model_modality", "model modality is not recognized")
        elif model.model_modality == "unknown" and not health_input.human_review_required:
            _add_failure(failures, "unknown_model_modality_requires_human_review", f"{prefix}.model_modality", "unknown model modality requires human review")
        expected_modalities = ROLE_EXPECTED_MODALITY.get(model.model_role or "", set())
        if expected_modalities and model.model_modality and model.model_modality not in expected_modalities:
            _add_failure(failures, "model_role_modality_mismatch", f"{prefix}.model_modality", "model role and modality are incompatible")
        expected_tasks = ROLE_EXPECTED_TASKS.get(model.model_role or "", set())
        incompatible_tasks = tuple(task for task in model.task_roles if task not in expected_tasks and task != "unknown")
        if incompatible_tasks:
            reason = "retrieval_model_mapped_to_chat" if model.model_role in {"embedding", "reranker"} else "model_task_role_mismatch"
            _add_failure(failures, reason, f"{prefix}.task_roles", "model task role mapping is incompatible")
        if any(task == "unknown" for task in model.task_roles) and not health_input.human_review_required:
            _add_failure(failures, "unknown_task_role_requires_human_review", f"{prefix}.task_roles", "unknown task role requires human review")
        if model.model_health_status and model.model_health_status not in MODEL_HEALTH_STATUSES:
            _add_failure(failures, "unsupported_model_health_status", f"{prefix}.model_health_status", "model health status is not recognized")
        if model.model_health_status == "model_loaded_unverified_future":
            _add_failure(failures, "model_loaded_status_out_of_scope", f"{prefix}.model_health_status", "model load status is out of scope until a future probe sprint")
        if model.active_probe_requested:
            _add_failure(failures, "active_model_probe_request_denied", f"{prefix}.active_probe_requested", "active model probes are denied")
        if model.resource_status in RESOURCE_BLOCKED_STATUSES:
            _add_failure(failures, "model_resource_blocked", f"{prefix}.resource_status", "model resources are blocked by metadata")
        if model.future_gated and phase != "propose_multimodal_probe_future":
            _add_failure(failures, "model_modality_future_gated", f"{prefix}.model_modality", "vision, audio, and multimodal health require a future privacy boundary")


def _validate_related_statuses(
    *,
    context_policy_decision: Any | None,
    policy_extension_decision: Any | None,
    foundation_config_dependency_hygiene_decision: Any | None,
    failures: list[LocalProviderHealthFailure],
) -> None:
    if context_policy_decision is not None:
        status = str(_field_value(context_policy_decision, "policy_status") or "")
        if status.startswith("blocked"):
            _add_failure(failures, "context_policy_not_ready", "context_policy_decision.policy_status", "blocked context policy cannot authorize provider health")
    if policy_extension_decision is not None:
        outcome = str(_field_value(policy_extension_decision, "policy_outcome") or "")
        if outcome.startswith("blocked") or outcome in {"unsupported", "unknown"}:
            _add_failure(failures, "policy_extension_not_ready", "policy_extension_decision.policy_outcome", "blocked policy extension cannot be contradicted")
    if foundation_config_dependency_hygiene_decision is not None:
        status = str(_field_value(foundation_config_dependency_hygiene_decision, "hygiene_status") or "")
        if status.startswith("blocked"):
            _add_failure(failures, "foundation_config_dependency_hygiene_not_ready", "foundation_config_dependency_hygiene_decision.hygiene_status", "blocked config/dependency hygiene blocks provider health readiness")


def _validate_related_decision(
    label: str,
    decision: Any | None,
    failures: list[LocalProviderHealthFailure],
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
            f"{label} cannot grant provider health authority, evidence, verifier success, routing, execution, or active provider behavior",
        )


def _validate_forbidden_claims(
    label: str,
    source: Any,
    failures: list[LocalProviderHealthFailure],
) -> None:
    for field, reason in FORBIDDEN_TRUTHY_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(failures, reason, f"{label}.{field}", "authority, grants, proof, evidence, verifier success, health verification, or execution selection claims are denied")
    for field, reason in FORBIDDEN_BEHAVIOR_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(failures, reason, f"{label}.{field}", "provider probing, process inspection, auth, model listing/loading/calls, API, MCP, tools, memory, or external transfer are denied")
    for field, reason in PROOF_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(failures, reason, f"{label}.{field}", "provider/model truth, proof, certification, evidence, and quality claims are denied")
    execution_permission = _field_value(source, "execution_permission")
    if execution_permission not in (None, "", LOCAL_PROVIDER_HEALTH_EXECUTION_PERMISSION):
        permission_text = str(execution_permission)
        if not permission_text.startswith("not_granted"):
            _add_failure(failures, "execution_permission_claim_denied", f"{label}.execution_permission", "local provider health cannot grant execution permission")


def _future_gates(
    health_input: LocalProviderHealthInput,
    failures: list[LocalProviderHealthFailure],
) -> tuple[str, ...]:
    gates: list[str] = []
    phase = health_input.health_check_phase
    provider_class = health_input.provider_config.provider_class
    endpoint_host_class = health_input.provider_config.endpoint_host_class
    if phase in FUTURE_HEALTH_PHASES:
        gates.append(f"{phase}_requires_future_probe_boundary")
    if provider_class in FUTURE_PROVIDER_CLASSES:
        gates.append(f"{provider_class}_requires_future_provider_boundary")
    if endpoint_host_class in REMOTE_ENDPOINT_HOST_CLASSES:
        gates.append("non_local_endpoint_requires_future_boundary")
    for model in health_input.model_metadata:
        if model.future_gated:
            gates.append("multimodal_or_voice_model_requires_future_privacy_boundary")
        if model.listed_unverified:
            gates.append("model_list_status_requires_future_probe_evidence")
    if any("unknown" in failure.reason for failure in failures):
        gates.append("unknown_metadata_requires_human_review")
    return tuple(dict.fromkeys(gates))


def _readiness_status(
    health_input: LocalProviderHealthInput,
    failures: list[LocalProviderHealthFailure],
    future_gates: tuple[str, ...],
) -> str:
    reasons = {failure.reason for failure in failures}
    if reasons:
        if "unsafe_related_decision" in reasons:
            return "blocked_by_unsafe_related_decision"
        if any("authority" in reason or "grant" in reason for reason in reasons):
            return "blocked_by_authority_claim"
        if any("evidence" in reason or "verifier" in reason or "proof" in reason or "certification" in reason or "truth" in reason for reason in reasons):
            return "blocked_by_evidence_claim"
        if any("request_denied" in reason or "execution" in reason or "probe" in reason or "call" in reason or "load" in reason or "external" in reason for reason in reasons):
            return "blocked_by_execution_claim"
        if any("secret" in reason or "api_key" in reason for reason in reasons):
            return "blocked_by_secret_policy"
        if any("endpoint" in reason for reason in reasons):
            return "blocked_by_endpoint_policy"
        if any("resource" in reason or "disk_pressure" in reason for reason in reasons):
            return "blocked_by_resource"
        if any(reason.startswith("missing_") or reason.startswith("unsupported_") for reason in reasons):
            return "blocked_by_missing_required_field"
        if any("context_policy" in reason for reason in reasons):
            return "blocked_by_context_policy"
        if any("policy_extension" in reason for reason in reasons):
            return "blocked_by_policy_extension"
        if any("model_" in reason or "retrieval_model" in reason for reason in reasons):
            return "blocked_by_model_policy"
        return "blocked_by_policy"
    if health_input.provider_config.provider_class == "offline_disabled_provider":
        return "offline_disabled_ready"
    if future_gates:
        return "future_gated"
    if health_input.human_review_required or health_input.unknowns or health_input.provider_config.unknowns:
        return "metadata_ready_requires_human_review"
    return "metadata_ready"


def _provider_health_status(
    health_input: LocalProviderHealthInput,
    failures: list[LocalProviderHealthFailure],
    future_gates: tuple[str, ...],
) -> str:
    if failures:
        return "unknown"
    config = health_input.provider_config
    if config.provider_class == "offline_disabled_provider":
        return "offline_disabled"
    if future_gates:
        return "future_gated"
    return config.provider_health_status or "metadata_only"


def _aggregate_model_health_status(
    models: tuple[ProviderModelHealthMetadata, ...],
    failures: list[LocalProviderHealthFailure],
    future_gates: tuple[str, ...],
) -> str:
    if failures:
        reasons = {failure.reason for failure in failures}
        if any("modality_future_gated" in reason for reason in reasons):
            return "model_modality_future_gated"
        if any("resource" in reason for reason in reasons):
            return "model_resource_blocked"
        if any("role" in reason or "mismatch" in reason for reason in reasons):
            return "model_role_mismatch"
        return "unknown"
    if any(model.future_gated for model in models) or any("multimodal" in gate for gate in future_gates):
        return "model_modality_future_gated"
    if any(model.listed_unverified for model in models):
        return "model_listed_unverified_future"
    return "model_metadata_only" if models else "model_load_not_attempted"


def _config_trust_level(config_source: str | None) -> str:
    if config_source in LOW_TRUST_CONFIG_SOURCES:
        return "lower_trust_metadata_only"
    if config_source in {"backend_config", "operator_supplied", "test_fixture", "synthetic_fixture"}:
        return "metadata_only"
    if config_source:
        return "unknown"
    return "unknown"


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
    failures: list[LocalProviderHealthFailure],
    reason: str,
    field: str,
    message: str,
) -> None:
    failures.append(LocalProviderHealthFailure(reason=reason, field=field, message=message))
