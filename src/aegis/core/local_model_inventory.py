from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping


LOCAL_MODEL_INVENTORY_VERSION = "local-model-inventory-role-mapping-readiness/1"
LOCAL_MODEL_INVENTORY_EXECUTION_PERMISSION = (
    "not_granted_by_local_model_inventory"
)

PROVIDER_CLASSES = {
    "lm_studio_local",
    "ollama_local",
    "vllm_local",
    "openai_compatible_local",
    "mock_test_provider",
    "offline_disabled_provider",
    "unknown_local_provider",
}

LOCAL_PROVIDER_CLASSES = {
    "lm_studio_local",
    "ollama_local",
    "vllm_local",
    "openai_compatible_local",
    "mock_test_provider",
    "unknown_local_provider",
}

OFFLINE_PROVIDER_CLASSES = {"offline_disabled_provider"}

PROVIDER_STATUSES = {
    "available_metadata_only",
    "configured_metadata_only",
    "not_configured",
    "unavailable",
    "endpoint_unverified",
    "endpoint_available_unverified",
    "resource_blocked",
    "disk_pressure_blocked",
    "disabled_by_policy",
    "unknown",
}

OFFLINE_PROVIDER_STATUSES = {
    "not_configured",
    "unavailable",
    "disabled_by_policy",
}

RESOURCE_BLOCKED_PROVIDER_STATUSES = {
    "resource_blocked",
    "disk_pressure_blocked",
}

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

AUTO_MODE_ELIGIBILITY = {
    "passive_preferred",
    "local_preferred",
    "local_only",
    "cloud_allowed_later",
    "blocked_by_privacy",
    "blocked_by_resource",
    "blocked_by_unknown_metadata",
    "blocked_by_policy",
    "future_gated",
}

ROLE_COMPATIBLE_MODALITIES = {
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

ROLE_COMPATIBLE_TASKS = {
    "chat_general": {
        "mission_control_wording",
        "tool_simulation_explanation",
        "documentation_summary",
        "translation_terminology",
    },
    "coding": {
        "repo_audit_candidate_notes",
        "code_explanation",
        "architecture_review",
        "documentation_summary",
    },
    "reasoning": {
        "architecture_review",
        "risk_analysis",
        "repo_audit_candidate_notes",
        "code_explanation",
    },
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

CHAT_GENERATION_ROLES = {
    "chat_general",
    "coding",
    "reasoning",
    "summarization",
    "translation_terminology",
    "safety_classifier",
    "small_utility",
}

FUTURE_GATED_ROLES = {"vision", "audio_stt", "audio_tts", "multimodal"}

FORBIDDEN_TRUTHY_FIELDS = {
    "authority": "authority_must_be_false",
    "runtime_dispatch_allowed": "runtime_dispatch_not_allowed",
    "approval_grant": "approval_grant_not_allowed",
    "capability_grant": "capability_grant_not_allowed",
    "lease_grant": "lease_grant_not_allowed",
    "frontend_authority": "frontend_authority_not_allowed",
    "output_is_authority": "model_inventory_output_cannot_be_authority",
    "model_output_treated_as_authority": "model_output_authority_claim_denied",
    "evidence_provided_by_inventory": "inventory_cannot_provide_evidence",
    "evidence_provided_by_model": "model_cannot_provide_evidence",
    "evidence_provided_by_output": "model_output_cannot_provide_evidence",
    "verifier_success": "inventory_cannot_mark_verifier_success",
    "verified_success": "inventory_cannot_mark_verifier_success",
    "success": "success_claim_denied",
    "router_decision_final": "router_decision_not_final",
    "auto_mode_execution_allowed": "auto_mode_execution_not_allowed",
}

FORBIDDEN_BEHAVIOR_FIELDS = {
    "model_call_performed": "model_call_request_denied",
    "model_call_requested": "model_call_request_denied",
    "call_model": "model_call_request_denied",
    "model_loaded": "model_load_request_denied",
    "load_model": "model_load_request_denied",
    "endpoint_probed": "endpoint_probe_request_denied",
    "probe_endpoint": "endpoint_probe_request_denied",
    "provider_authenticated": "provider_auth_request_denied",
    "model_downloaded": "model_download_request_denied",
    "download_model": "model_download_request_denied",
    "model_file_read": "model_file_read_request_denied",
    "model_file_moved": "model_file_move_request_denied",
    "model_file_deleted": "model_file_delete_request_denied",
    "embedding_generated": "embedding_generation_request_denied",
    "generate_embedding": "embedding_generation_request_denied",
    "reranking_performed": "reranking_request_denied",
    "rerank_performed": "reranking_request_denied",
    "inference_performed": "inference_request_denied",
    "run_inference": "inference_request_denied",
    "memory_access_performed": "memory_access_request_denied",
    "memory_read_requested": "memory_access_request_denied",
    "memory_write_requested": "memory_access_request_denied",
    "api_call_performed": "api_call_request_denied",
    "api_call_requested": "api_call_request_denied",
    "mcp_call_performed": "mcp_call_request_denied",
    "mcp_call_requested": "mcp_call_request_denied",
    "tool_call_performed": "tool_call_request_denied",
    "tool_call_requested": "tool_call_request_denied",
}

PROOF_FIELDS = {
    "model_output_is_truth": "model_output_truth_claim_denied",
    "model_output_as_evidence": "model_output_evidence_claim_denied",
    "model_output_as_policy": "model_output_policy_claim_denied",
    "model_output_as_compliance_proof": "model_output_compliance_claim_denied",
    "proof_model_available": "model_availability_proof_claim_denied",
    "proof_model_quality": "model_quality_proof_claim_denied",
    "proof_model_health": "model_health_proof_claim_denied",
    "proof_secure": "security_proof_claim_denied",
    "proof_compliant": "compliance_proof_claim_denied",
    "security_certification": "security_certification_claim_denied",
    "compliance_certification": "compliance_certification_claim_denied",
    "certification_claim": "certification_claim_denied",
}

LOCAL_ONLY_TERMS_VALUES = {"unknown", "out_of_scope", "not_applicable", "local_only"}


@dataclass(frozen=True)
class LocalModelInventoryFailure:
    reason: str
    field: str
    message: str


@dataclass(frozen=True)
class LocalModelSourceRef:
    ref_id: str
    ref_type: str
    description: str | None = None


@dataclass(frozen=True)
class LocalModelContextPolicy:
    max_context_tokens: int | None
    recommended_context_budget: int | None
    can_receive_private_repo_context: bool
    can_receive_user_memory_context: bool
    can_receive_runtime_logs: bool
    can_receive_evidence_refs: bool
    can_receive_raw_evidence: bool
    can_receive_secret_like_content: bool
    can_receive_raw_journal: bool
    can_receive_compliance_context: bool
    can_receive_web_context: bool
    requires_redaction: bool
    requires_source_refs: bool
    output_requires_validation: bool


@dataclass(frozen=True)
class LocalModelResourceProfile:
    estimated_vram_gb: float | None = None
    estimated_ram_gb: float | None = None
    gpu_required: bool = False
    cpu_usable: bool = False
    latency_class: str | None = None
    quality_class: str | None = None
    cost_class: str | None = None
    resource_status: str | None = None


@dataclass(frozen=True)
class LocalModelMetadata:
    model_id: str | None
    model_name: str | None
    model_family: str | None
    model_role: str | None
    model_modality: str | None
    quantization: str | None = None
    parameter_count: str | int | float | None = None
    disk_size_bytes: int | None = None
    context_window_tokens: int | None = None
    max_output_tokens: int | None = None
    local_path_ref: str | None = None
    endpoint_ref: str | None = None
    endpoint_status: str | None = None
    privacy_class: str | None = None
    data_sensitivity_allowed: tuple[str, ...] = ()
    task_roles: tuple[str, ...] = ()
    resource_requirements: LocalModelResourceProfile = LocalModelResourceProfile()
    license_ref: str | None = None
    terms_status: str | None = None
    region_status: str | None = None
    source_refs: tuple[LocalModelSourceRef, ...] = ()
    limitations: tuple[str, ...] = ()
    unknowns: tuple[str, ...] = ()
    human_review_required: bool = False
    active_use_requested: bool = False


@dataclass(frozen=True)
class LocalModelRoleMapping:
    model_id: str | None
    model_name: str | None
    model_role: str | None
    model_modality: str | None
    task_roles: tuple[str, ...]
    suitability_status: str
    auto_mode_eligibility: str
    proposal_only: bool = True
    chat_generation_candidate: bool = False
    active_use_allowed: bool = False
    future_gated: bool = False
    local_only_for_private_context: bool = False
    can_receive_private_repo_context: bool = False
    can_receive_secret_like_content: bool = False
    can_receive_raw_journal: bool = False
    output_requires_validation: bool = True
    limitations: tuple[str, ...] = ()
    unknowns: tuple[str, ...] = ()
    failure_reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class LocalModelInventoryContract:
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = LOCAL_MODEL_INVENTORY_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_inventory: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    frontend_authority: bool = False
    model_call_performed: bool = False
    model_loaded: bool = False
    endpoint_probed: bool = False
    provider_authenticated: bool = False
    model_downloaded: bool = False
    model_file_read: bool = False
    model_file_moved: bool = False
    model_file_deleted: bool = False
    embedding_generated: bool = False
    reranking_performed: bool = False
    inference_performed: bool = False
    memory_access_performed: bool = False
    api_call_performed: bool = False
    mcp_call_performed: bool = False
    tool_call_performed: bool = False
    router_decision_final: bool = False
    auto_mode_execution_allowed: bool = False
    output_is_authority: bool = False
    requires_backend_validation: bool = True
    requires_policy_check: bool = True
    requires_human_review_for_unknowns: bool = True


@dataclass(frozen=True)
class LocalModelInventoryInput:
    request_id: str | None
    project_ref: str | None
    tenant_scope: str | None
    namespace: str | None
    provider_id: str | None
    provider_class: str | None
    provider_status: str | None
    privacy_class: str | None
    data_sensitivity_allowed: tuple[str, ...]
    context_policy: LocalModelContextPolicy | None
    source_refs: tuple[LocalModelSourceRef, ...]
    policy_refs: tuple[str, ...]
    limitations: tuple[str, ...]
    unknowns: tuple[str, ...]
    models: tuple[LocalModelMetadata, ...]
    human_review_required: bool


@dataclass(frozen=True)
class LocalModelInventoryDecision:
    contract_version: str
    inventory_status: str
    request_id: str | None
    project_ref: str | None
    tenant_scope: str | None
    namespace: str | None
    provider_id: str | None
    provider_class: str | None
    provider_status: str | None
    failure_reasons: tuple[str, ...]
    failures: tuple[LocalModelInventoryFailure, ...]
    inventory_input: LocalModelInventoryInput | None
    inventory_contract: LocalModelInventoryContract
    role_mappings: tuple[LocalModelRoleMapping, ...]
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = LOCAL_MODEL_INVENTORY_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_inventory: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    frontend_authority: bool = False
    model_call_performed: bool = False
    model_loaded: bool = False
    endpoint_probed: bool = False
    provider_authenticated: bool = False
    model_downloaded: bool = False
    model_file_read: bool = False
    model_file_moved: bool = False
    model_file_deleted: bool = False
    embedding_generated: bool = False
    reranking_performed: bool = False
    inference_performed: bool = False
    memory_access_performed: bool = False
    api_call_performed: bool = False
    mcp_call_performed: bool = False
    tool_call_performed: bool = False
    router_decision_final: bool = False
    auto_mode_execution_allowed: bool = False
    output_is_authority: bool = False
    requires_backend_validation: bool = True
    requires_policy_check: bool = True
    requires_human_review_for_unknowns: bool = True


def validate_local_model_inventory_request(
    request: Mapping[str, Any] | None,
    *,
    provider_decision: Any | None = None,
    model_provider_readiness: Any | None = None,
    mission_control_decision: Any | None = None,
    tool_simulation_decision: Any | None = None,
    repo_audit_decision: Any | None = None,
    context_compiler_decision: Any | None = None,
    compliance_evidence_decision: Any | None = None,
    developer_work_passport_decision: Any | None = None,
) -> LocalModelInventoryDecision:
    """Validate synthetic model metadata without touching providers or files."""

    failures: list[LocalModelInventoryFailure] = []
    contract = LocalModelInventoryContract()

    if not isinstance(request, Mapping):
        failure = LocalModelInventoryFailure(
            reason="missing_request",
            field="request",
            message="local model inventory request must be a mapping",
        )
        return _decision(
            inventory_status="clarification_required",
            request_id=None,
            project_ref=None,
            tenant_scope=None,
            namespace=None,
            provider_id=None,
            provider_class=None,
            provider_status=None,
            failures=(failure,),
            inventory_input=None,
            inventory_contract=contract,
            role_mappings=(),
        )

    data = deepcopy(dict(request))
    _validate_related_decision("provider", provider_decision, failures)
    _validate_related_decision(
        "model_provider_readiness",
        model_provider_readiness,
        failures,
    )
    _validate_related_decision("mission_control", mission_control_decision, failures)
    _validate_related_decision("tool_simulation", tool_simulation_decision, failures)
    _validate_related_decision("repo_audit", repo_audit_decision, failures)
    _validate_related_decision("context_compiler", context_compiler_decision, failures)
    _validate_related_decision(
        "compliance_evidence",
        compliance_evidence_decision,
        failures,
    )
    _validate_related_decision(
        "developer_work_passport",
        developer_work_passport_decision,
        failures,
    )

    request_id = _text(data.get("request_id")) or None
    project_ref = _text(data.get("project_ref")) or _text(data.get("project_scope")) or None
    tenant_scope = _text(data.get("tenant_scope")) or None
    namespace = _text(data.get("namespace")) or None
    provider_id = _text(data.get("provider_id")) or None
    provider_class = _text(data.get("provider_class")) or None
    provider_status = _text(data.get("provider_status")) or None
    privacy_class = _text(data.get("privacy_class")) or None
    context_policy = _context_policy(data.get("context_policy"))
    models = _models(data.get("models", data.get("model_metadata")))
    inventory_input = LocalModelInventoryInput(
        request_id=request_id,
        project_ref=project_ref,
        tenant_scope=tenant_scope,
        namespace=namespace,
        provider_id=provider_id,
        provider_class=provider_class,
        provider_status=provider_status,
        privacy_class=privacy_class,
        data_sensitivity_allowed=_strings(data.get("data_sensitivity_allowed")),
        context_policy=context_policy,
        source_refs=_source_refs(data.get("source_refs")),
        policy_refs=_strings(data.get("policy_refs")),
        limitations=_strings(data.get("limitations")),
        unknowns=_strings(data.get("unknowns")),
        models=models,
        human_review_required=_bool(data.get("human_review_required")),
    )

    _validate_identity(inventory_input, failures)
    _validate_request_claims(data, failures)
    _validate_model_claims(data.get("models", data.get("model_metadata")), failures)
    _validate_provider(inventory_input, failures)
    _validate_local_only_terms(data, failures)
    _validate_model_local_only_terms(data.get("models", data.get("model_metadata")), failures)
    _validate_context_policy(inventory_input, failures)

    role_mappings = tuple(
        _role_mapping(model, inventory_input, failures)
        for model in inventory_input.models
    )

    return _decision(
        inventory_status=_inventory_status(
            inventory_input,
            failures,
            role_mappings,
        ),
        request_id=request_id,
        project_ref=project_ref,
        tenant_scope=tenant_scope,
        namespace=namespace,
        provider_id=provider_id,
        provider_class=provider_class,
        provider_status=provider_status,
        failures=tuple(failures),
        inventory_input=inventory_input,
        inventory_contract=contract,
        role_mappings=role_mappings,
    )


def _decision(
    *,
    inventory_status: str,
    request_id: str | None,
    project_ref: str | None,
    tenant_scope: str | None,
    namespace: str | None,
    provider_id: str | None,
    provider_class: str | None,
    provider_status: str | None,
    failures: tuple[LocalModelInventoryFailure, ...],
    inventory_input: LocalModelInventoryInput | None,
    inventory_contract: LocalModelInventoryContract,
    role_mappings: tuple[LocalModelRoleMapping, ...],
) -> LocalModelInventoryDecision:
    return LocalModelInventoryDecision(
        contract_version=LOCAL_MODEL_INVENTORY_VERSION,
        inventory_status=inventory_status,
        request_id=request_id,
        project_ref=project_ref,
        tenant_scope=tenant_scope,
        namespace=namespace,
        provider_id=provider_id,
        provider_class=provider_class,
        provider_status=provider_status,
        failure_reasons=tuple(f.reason for f in failures),
        failures=failures,
        inventory_input=inventory_input,
        inventory_contract=inventory_contract,
        role_mappings=role_mappings,
    )


def _validate_identity(
    inventory_input: LocalModelInventoryInput,
    failures: list[LocalModelInventoryFailure],
) -> None:
    required = {
        "request_id": inventory_input.request_id,
        "project_ref": inventory_input.project_ref,
        "tenant_scope": inventory_input.tenant_scope,
        "namespace": inventory_input.namespace,
    }
    for field, value in required.items():
        if not value:
            _add_failure(
                failures,
                "missing_identity",
                field,
                f"{field} is required for local model inventory readiness",
            )


def _validate_provider(
    inventory_input: LocalModelInventoryInput,
    failures: list[LocalModelInventoryFailure],
) -> None:
    if not inventory_input.provider_id:
        _add_failure(
            failures,
            "missing_provider_identity",
            "provider_id",
            "provider_id is required",
        )
    if not inventory_input.provider_class:
        _add_failure(
            failures,
            "missing_provider_class",
            "provider_class",
            "provider_class is required",
        )
    elif inventory_input.provider_class not in PROVIDER_CLASSES:
        _add_failure(
            failures,
            "unsupported_provider_class",
            "provider_class",
            f"{inventory_input.provider_class!r} is not a supported local inventory provider class",
        )
    if not inventory_input.provider_status:
        _add_failure(
            failures,
            "missing_provider_status",
            "provider_status",
            "provider_status is required",
        )
    elif inventory_input.provider_status not in PROVIDER_STATUSES:
        _add_failure(
            failures,
            "unsupported_provider_status",
            "provider_status",
            f"{inventory_input.provider_status!r} is not supported",
        )
    if (
        not inventory_input.models
        and inventory_input.provider_class not in OFFLINE_PROVIDER_CLASSES
        and inventory_input.provider_status not in OFFLINE_PROVIDER_STATUSES
    ):
        _add_failure(
            failures,
            "missing_model_metadata",
            "models",
            "at least one model metadata entry is required unless the provider is explicitly offline or disabled",
        )
    if inventory_input.provider_status in RESOURCE_BLOCKED_PROVIDER_STATUSES:
        _add_failure(
            failures,
            "provider_resource_blocked",
            "provider_status",
            "resource-blocked provider metadata cannot become model readiness",
        )


def _validate_context_policy(
    inventory_input: LocalModelInventoryInput,
    failures: list[LocalModelInventoryFailure],
) -> None:
    if inventory_input.models and not inventory_input.privacy_class:
        _add_failure(
            failures,
            "missing_privacy_class",
            "privacy_class",
            "privacy_class is required for non-passive local model role mapping",
        )
    if inventory_input.models and not inventory_input.data_sensitivity_allowed:
        _add_failure(
            failures,
            "missing_data_sensitivity_allowed",
            "data_sensitivity_allowed",
            "data_sensitivity_allowed is required for non-passive local model role mapping",
        )
    if inventory_input.models and inventory_input.context_policy is None:
        _add_failure(
            failures,
            "missing_context_policy",
            "context_policy",
            "context policy metadata is required for non-passive local model role mapping",
        )
        return
    policy = inventory_input.context_policy
    if policy is None:
        return
    if policy.can_receive_secret_like_content:
        _add_failure(
            failures,
            "raw_secret_context_denied",
            "context_policy.can_receive_secret_like_content",
            "raw secrets, tokens, env values, and API keys are denied",
        )
    if policy.can_receive_raw_journal:
        _add_failure(
            failures,
            "raw_journal_context_denied",
            "context_policy.can_receive_raw_journal",
            "raw runtime journal context is denied by default",
        )
    if policy.can_receive_raw_evidence:
        _add_failure(
            failures,
            "raw_evidence_context_denied",
            "context_policy.can_receive_raw_evidence",
            "raw evidence is denied in this local inventory contract; use refs only",
        )


def _validate_request_claims(
    data: Mapping[str, Any],
    failures: list[LocalModelInventoryFailure],
) -> None:
    _validate_claim_fields("request", data, failures)


def _validate_model_claims(
    value: Any,
    failures: list[LocalModelInventoryFailure],
) -> None:
    if not isinstance(value, (list, tuple)):
        return
    for index, item in enumerate(value):
        if isinstance(item, Mapping):
            _validate_claim_fields(f"models[{index}]", item, failures)


def _validate_related_decision(
    label: str,
    decision: Any | None,
    failures: list[LocalModelInventoryFailure],
) -> None:
    if decision is None:
        return
    before = len(failures)
    _validate_claim_fields(label, decision, failures)
    if len(failures) > before:
        _add_failure(
            failures,
            "unsafe_related_decision",
            label,
            f"{label} decision contains authority, execution, model, API, tool, memory, evidence, verifier, or proof claims",
        )


def _validate_claim_fields(
    label: str,
    source: Any,
    failures: list[LocalModelInventoryFailure],
) -> None:
    for field, reason in FORBIDDEN_TRUTHY_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(
                failures,
                reason,
                f"{label}.{field}",
                f"{label} cannot claim authority, grants, success, evidence, or final routing",
            )
    for field, reason in FORBIDDEN_BEHAVIOR_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(
                failures,
                reason,
                f"{label}.{field}",
                f"{label} cannot perform or request model/provider/tool/API/MCP/memory behavior",
            )
    for field, reason in PROOF_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(
                failures,
                reason,
                f"{label}.{field}",
                f"{label} cannot claim model truth, proof, certification, evidence, or verifier success",
            )
    execution_permission = _field_value(source, "execution_permission")
    if execution_permission not in (None, "", LOCAL_MODEL_INVENTORY_EXECUTION_PERMISSION):
        permission_text = str(execution_permission)
        if not permission_text.startswith("not_granted"):
            _add_failure(
                failures,
                "execution_permission_claim_denied",
                f"{label}.execution_permission",
                "execution permission cannot be granted by local model inventory metadata",
            )


def _validate_local_only_terms(
    data: Mapping[str, Any],
    failures: list[LocalModelInventoryFailure],
) -> None:
    for field in ("region_status", "terms_status", "cloud_region_status"):
        value = _text(data.get(field))
        if value and value not in LOCAL_ONLY_TERMS_VALUES:
            _add_failure(
                failures,
                "cloud_terms_or_region_claim_denied",
                field,
                "cloud region and terms claims are out of scope unless marked unknown or out_of_scope",
            )


def _validate_model_local_only_terms(
    value: Any,
    failures: list[LocalModelInventoryFailure],
) -> None:
    if not isinstance(value, (list, tuple)):
        return
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            continue
        for field in ("region_status", "terms_status", "cloud_region_status"):
            raw = item.get(field)
            value_text = _text(raw)
            if value_text and value_text not in LOCAL_ONLY_TERMS_VALUES:
                _add_failure(
                    failures,
                    "cloud_terms_or_region_claim_denied",
                    f"models[{index}].{field}",
                    "cloud region and terms claims are out of scope unless marked unknown or out_of_scope",
                )


def _role_mapping(
    model: LocalModelMetadata,
    inventory_input: LocalModelInventoryInput,
    failures: list[LocalModelInventoryFailure],
) -> LocalModelRoleMapping:
    model_failures: list[str] = []
    role = model.model_role
    modality = model.model_modality
    task_roles = model.task_roles
    context_policy = inventory_input.context_policy

    if not model.model_id:
        model_failures.append("missing_model_id")
        _add_failure(failures, "missing_model_id", "models.model_id", "model_id is required")
    if not model.model_name:
        model_failures.append("missing_model_name")
        _add_failure(
            failures,
            "missing_model_name",
            "models.model_name",
            "model_name is required",
        )
    if not role:
        model_failures.append("missing_model_role")
        _add_failure(
            failures,
            "missing_model_role",
            "models.model_role",
            "model_role is required",
        )
    elif role not in MODEL_ROLES:
        model_failures.append("unsupported_model_role")
        _add_failure(
            failures,
            "unsupported_model_role",
            "models.model_role",
            f"{role!r} is not a supported model role",
        )
    elif role == "unknown":
        model_failures.append("unknown_model_role_requires_human_review")
        if not model.human_review_required and not inventory_input.human_review_required:
            _add_failure(
                failures,
                "unknown_model_role_requires_human_review",
                "models.model_role",
                "unknown model role requires human review or clarification",
            )

    if not modality:
        model_failures.append("missing_model_modality")
        _add_failure(
            failures,
            "missing_model_modality",
            "models.model_modality",
            "model_modality is required",
        )
    elif modality not in MODEL_MODALITIES:
        model_failures.append("unsupported_model_modality")
        _add_failure(
            failures,
            "unsupported_model_modality",
            "models.model_modality",
            f"{modality!r} is not a supported model modality",
        )
    elif modality == "unknown":
        model_failures.append("unknown_model_modality_requires_human_review")
        if not model.human_review_required and not inventory_input.human_review_required:
            _add_failure(
                failures,
                "unknown_model_modality_requires_human_review",
                "models.model_modality",
                "unknown model modality requires human review or clarification",
            )

    if role in ROLE_COMPATIBLE_MODALITIES and modality:
        allowed_modalities = ROLE_COMPATIBLE_MODALITIES[role]
        if modality not in allowed_modalities:
            model_failures.append("model_role_modality_mismatch")
            _add_failure(
                failures,
                "model_role_modality_mismatch",
                "models.model_modality",
                f"{role!r} cannot be mapped to modality {modality!r}",
            )

    unknown_task = any(task == "unknown" for task in task_roles)
    if unknown_task and not (model.human_review_required or inventory_input.human_review_required):
        model_failures.append("unknown_task_role_requires_human_review")
        _add_failure(
            failures,
            "unknown_task_role_requires_human_review",
            "models.task_roles",
            "unknown task role requires human review or clarification",
        )
    for task in task_roles:
        if task and task not in TASK_ROLES:
            model_failures.append("unsupported_task_role")
            _add_failure(
                failures,
                "unsupported_task_role",
                "models.task_roles",
                f"{task!r} is not a supported task role",
            )

    if role in ROLE_COMPATIBLE_TASKS:
        allowed_tasks = ROLE_COMPATIBLE_TASKS[role]
        incompatible = tuple(
            task for task in task_roles if task not in allowed_tasks and task != "unknown"
        )
        if incompatible:
            reason = (
                "retrieval_model_mapped_to_chat"
                if role in {"embedding", "reranker"}
                else "model_task_role_mismatch"
            )
            model_failures.append(reason)
            _add_failure(
                failures,
                reason,
                "models.task_roles",
                f"{role!r} cannot be mapped to task roles {incompatible!r}",
            )

    future_gated = bool(role in FUTURE_GATED_ROLES)
    active_use_requested = model.active_use_requested
    if future_gated:
        gate_tasks = ROLE_COMPATIBLE_TASKS.get(role or "", set())
        has_future_gate_task = all(task in gate_tasks for task in task_roles) if task_roles else False
        if active_use_requested or not has_future_gate_task:
            model_failures.append("future_gated_model_active_use_denied")
            _add_failure(
                failures,
                "future_gated_model_active_use_denied",
                "models.task_roles",
                "vision, audio, and multimodal models require future-gated task roles and cannot be active by default",
            )

    resource_blocked = (
        inventory_input.provider_status in RESOURCE_BLOCKED_PROVIDER_STATUSES
        or model.resource_requirements.resource_status in RESOURCE_BLOCKED_PROVIDER_STATUSES
    )
    can_receive_private = bool(
        context_policy.can_receive_private_repo_context if context_policy else False
    )
    local_only_for_private = (
        can_receive_private
        and inventory_input.provider_class in LOCAL_PROVIDER_CLASSES
    )
    auto_eligibility = _auto_mode_eligibility(
        inventory_input,
        model,
        model_failures,
        future_gated=future_gated,
        local_only_for_private=local_only_for_private,
        resource_blocked=resource_blocked,
    )
    suitability_status = (
        "future_gated"
        if future_gated and not any(
            reason == "future_gated_model_active_use_denied"
            for reason in model_failures
        )
        else "blocked"
        if model_failures or resource_blocked
        else "metadata_ready"
    )
    return LocalModelRoleMapping(
        model_id=model.model_id,
        model_name=model.model_name,
        model_role=role,
        model_modality=modality,
        task_roles=task_roles,
        suitability_status=suitability_status,
        auto_mode_eligibility=auto_eligibility,
        proposal_only=True,
        chat_generation_candidate=bool(role in CHAT_GENERATION_ROLES),
        active_use_allowed=False,
        future_gated=future_gated,
        local_only_for_private_context=local_only_for_private,
        can_receive_private_repo_context=can_receive_private,
        can_receive_secret_like_content=bool(
            context_policy.can_receive_secret_like_content if context_policy else False
        ),
        can_receive_raw_journal=bool(
            context_policy.can_receive_raw_journal if context_policy else False
        ),
        output_requires_validation=bool(
            context_policy.output_requires_validation if context_policy else True
        ),
        limitations=model.limitations,
        unknowns=model.unknowns,
        failure_reasons=tuple(model_failures),
    )


def _auto_mode_eligibility(
    inventory_input: LocalModelInventoryInput,
    model: LocalModelMetadata,
    model_failures: list[str],
    *,
    future_gated: bool,
    local_only_for_private: bool,
    resource_blocked: bool,
) -> str:
    if inventory_input.provider_status in {"disabled_by_policy", "not_configured", "unavailable"}:
        return "passive_preferred"
    if resource_blocked:
        return "blocked_by_resource"
    if any("privacy" in reason or "secret" in reason or "journal" in reason for reason in model_failures):
        return "blocked_by_privacy"
    if any("unknown" in reason for reason in model_failures):
        return "blocked_by_unknown_metadata"
    if future_gated:
        return "future_gated"
    if local_only_for_private:
        return "local_only"
    if inventory_input.provider_class in LOCAL_PROVIDER_CLASSES:
        return "local_preferred"
    return "blocked_by_policy"


def _inventory_status(
    inventory_input: LocalModelInventoryInput,
    failures: list[LocalModelInventoryFailure],
    role_mappings: tuple[LocalModelRoleMapping, ...],
) -> str:
    if failures:
        reasons = {failure.reason for failure in failures}
        if "missing_request" in reasons:
            return "clarification_required"
        if any(
            reason
            in {
                "missing_model_metadata",
                "missing_model_id",
                "missing_model_name",
                "missing_model_role",
                "missing_model_modality",
            }
            for reason in reasons
        ):
            return "blocked_by_missing_model_metadata"
        if any(reason in {"missing_identity", "missing_provider_identity"} for reason in reasons):
            return "blocked_by_missing_identity"
        if any(reason.startswith("missing_provider") for reason in reasons):
            return "blocked_by_provider_policy"
        if any("authority" in reason or "grant" in reason for reason in reasons):
            return "blocked_by_authority_claim"
        if any("evidence" in reason or "verifier" in reason for reason in reasons):
            return "blocked_by_evidence_claim"
        if any("request_denied" in reason or "execution" in reason for reason in reasons):
            return "blocked_by_execution_claim"
        if any("provider" in reason or "cloud_terms" in reason for reason in reasons):
            return "blocked_by_provider_policy"
        if any("context" in reason or "journal" in reason for reason in reasons):
            return "blocked_by_context_policy"
        if any("privacy" in reason or "secret" in reason for reason in reasons):
            return "blocked_by_privacy_policy"
        if any("resource" in reason or "disk" in reason for reason in reasons):
            return "blocked_by_resource"
        if any("related" in reason for reason in reasons):
            return "blocked_by_unsafe_related_decision"
        if any("role" in reason for reason in reasons):
            return "blocked_by_model_role"
        if any("modality" in reason for reason in reasons):
            return "blocked_by_model_modality"
        return "blocked_by_policy"
    if (
        inventory_input.provider_class in OFFLINE_PROVIDER_CLASSES
        or inventory_input.provider_status in OFFLINE_PROVIDER_STATUSES
    ):
        return "offline_disabled_ready"
    if (
        inventory_input.human_review_required
        or any(mapping.future_gated for mapping in role_mappings)
        or any(mapping.unknowns for mapping in role_mappings)
    ):
        return "inventory_ready_requires_human_review"
    return "inventory_ready"


def _models(value: Any) -> tuple[LocalModelMetadata, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    models: list[LocalModelMetadata] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        resource_data = item.get("resource_requirements")
        resource_map = resource_data if isinstance(resource_data, Mapping) else item
        models.append(
            LocalModelMetadata(
                model_id=_text(item.get("model_id")) or None,
                model_name=_text(item.get("model_name")) or None,
                model_family=_text(item.get("model_family")) or None,
                model_role=_text(item.get("model_role")) or None,
                model_modality=_text(item.get("model_modality")) or None,
                quantization=_text(item.get("quantization")) or None,
                parameter_count=item.get("parameter_count"),
                disk_size_bytes=_int(item.get("disk_size_bytes")),
                context_window_tokens=_int(item.get("context_window_tokens")),
                max_output_tokens=_int(item.get("max_output_tokens")),
                local_path_ref=_text(item.get("local_path_ref")) or None,
                endpoint_ref=_text(item.get("endpoint_ref")) or None,
                endpoint_status=_text(item.get("endpoint_status")) or None,
                privacy_class=_text(item.get("privacy_class")) or None,
                data_sensitivity_allowed=_strings(item.get("data_sensitivity_allowed")),
                task_roles=_strings(item.get("task_roles")),
                resource_requirements=LocalModelResourceProfile(
                    estimated_vram_gb=_float(resource_map.get("estimated_vram_gb")),
                    estimated_ram_gb=_float(resource_map.get("estimated_ram_gb")),
                    gpu_required=_bool(resource_map.get("gpu_required")),
                    cpu_usable=_bool(resource_map.get("cpu_usable")),
                    latency_class=_text(resource_map.get("latency_class")) or None,
                    quality_class=_text(resource_map.get("quality_class")) or None,
                    cost_class=_text(resource_map.get("cost_class")) or None,
                    resource_status=_text(resource_map.get("resource_status")) or None,
                ),
                license_ref=_text(item.get("license_ref")) or None,
                terms_status=_text(item.get("terms_status")) or None,
                region_status=_text(item.get("region_status")) or None,
                source_refs=_source_refs(item.get("source_refs")),
                limitations=_strings(item.get("limitations")),
                unknowns=_strings(item.get("unknowns")),
                human_review_required=_bool(item.get("human_review_required")),
                active_use_requested=_bool(item.get("active_use_requested")),
            )
        )
    return tuple(models)


def _context_policy(value: Any) -> LocalModelContextPolicy | None:
    if not isinstance(value, Mapping):
        return None
    return LocalModelContextPolicy(
        max_context_tokens=_int(value.get("max_context_tokens")),
        recommended_context_budget=_int(value.get("recommended_context_budget")),
        can_receive_private_repo_context=_bool(value.get("can_receive_private_repo_context")),
        can_receive_user_memory_context=_bool(value.get("can_receive_user_memory_context")),
        can_receive_runtime_logs=_bool(value.get("can_receive_runtime_logs")),
        can_receive_evidence_refs=_bool(value.get("can_receive_evidence_refs")),
        can_receive_raw_evidence=_bool(value.get("can_receive_raw_evidence")),
        can_receive_secret_like_content=_bool(value.get("can_receive_secret_like_content")),
        can_receive_raw_journal=_bool(value.get("can_receive_raw_journal")),
        can_receive_compliance_context=_bool(value.get("can_receive_compliance_context")),
        can_receive_web_context=_bool(value.get("can_receive_web_context")),
        requires_redaction=_bool(value.get("requires_redaction")),
        requires_source_refs=_bool(value.get("requires_source_refs")),
        output_requires_validation=_bool(value.get("output_requires_validation"), default=True),
    )


def _source_refs(value: Any) -> tuple[LocalModelSourceRef, ...]:
    refs: list[LocalModelSourceRef] = []
    if not isinstance(value, (list, tuple)):
        return ()
    for item in value:
        if not isinstance(item, Mapping):
            continue
        ref_id = _text(item.get("ref_id"))
        ref_type = _text(item.get("ref_type"))
        if ref_id and ref_type:
            refs.append(
                LocalModelSourceRef(
                    ref_id=ref_id,
                    ref_type=ref_type,
                    description=_text(item.get("description")) or None,
                )
            )
    return tuple(refs)


def _strings(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, (list, tuple, set)):
        strings = tuple(str(item) for item in value if str(item))
        return strings
    return ()


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _bool(value: Any, *, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def _field_value(source: Any, field: str) -> Any:
    if isinstance(source, Mapping):
        return source.get(field)
    return getattr(source, field, None)


def _field_bool(source: Any, field: str) -> bool:
    return _bool(_field_value(source, field))


def _add_failure(
    failures: list[LocalModelInventoryFailure],
    reason: str,
    field: str,
    message: str,
) -> None:
    failures.append(LocalModelInventoryFailure(reason=reason, field=field, message=message))
