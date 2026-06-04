from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping


MODEL_AUTO_MODE_VERSION = "model-auto-mode-provider-selection-contract/1"
MODEL_AUTO_MODE_EXECUTION_PERMISSION = "not_granted_by_model_auto_mode"

TASK_TYPES = {
    "maintenance_scan",
    "evidence_audit",
    "policy_validation",
    "repo_audit_readiness",
    "repo_audit_candidate_notes",
    "code_explanation",
    "architecture_review",
    "risk_analysis",
    "mission_control_wording",
    "tool_simulation_explanation",
    "documentation_summary",
    "translation_terminology",
    "context_retrieval",
    "context_reranking",
    "web_research_future",
    "document_analysis_future",
    "visual_analysis_future_gated",
    "audio_analysis_future_gated",
    "multimodal_analysis_future_gated",
    "voice_interaction_future_gated",
    "external_agent_oversight_future",
    "unknown",
}

USER_PREFERENCE_MODES = {
    "auto",
    "passive_only",
    "local_only",
    "cloud_allowed",
    "local_first_cloud_fallback",
    "ask_each_time",
    "disabled",
    "unknown",
}

SELECTION_MODES = {
    "passive_no_model",
    "local_model_candidate",
    "local_embedding_candidate",
    "local_reranker_candidate",
    "cloud_model_candidate_later",
    "hybrid_local_first_candidate",
    "hybrid_cloud_first_candidate_later",
    "ask_operator",
    "blocked_by_privacy",
    "blocked_by_policy",
    "blocked_by_context_policy",
    "blocked_by_memory_governance",
    "blocked_by_identity_scope",
    "blocked_by_provider_status",
    "blocked_by_region_or_terms",
    "blocked_by_secret_boundary",
    "blocked_by_resource",
    "blocked_by_unknown_metadata",
    "future_gated",
    "unsupported",
}

PROVIDER_CLASSES = {
    "passive_backend",
    "lm_studio_local",
    "ollama_local_optional",
    "vllm_local",
    "openai_compatible_local",
    "cloud_provider_future",
    "mock_test_provider",
    "offline_disabled_provider",
    "unknown",
}

PROVIDER_STATUSES = {
    "offline_disabled",
    "metadata_only",
    "configured_metadata_only",
    "not_configured",
    "unavailable",
    "endpoint_unverified",
    "endpoint_available_unverified",
    "resource_blocked",
    "disk_pressure_blocked",
    "disabled_by_policy",
    "future_gated",
    "unknown",
}

CLOUD_PROVIDER_STATUSES = {
    "not_configured",
    "api_key_missing",
    "api_key_present_unverified",
    "region_blocked",
    "unsupported_region",
    "terms_unverified",
    "quota_unknown",
    "disabled_by_policy",
    "future_gated",
    "unknown",
}

PROVIDER_SECRET_STATUSES = {
    "no_secret_required",
    "secret_missing",
    "secret_present_unverified",
    "secret_invalid_metadata_only",
    "secret_storage_unknown",
    "secret_disallowed",
    "unknown",
}

RESOURCE_STATUSES = {
    "disk_ok",
    "disk_warning",
    "disk_blocked",
    "ram_ok",
    "ram_unknown",
    "vram_ok",
    "vram_unknown",
    "gpu_required_unknown",
    "resource_unknown",
    "resource_blocked",
}

PASSIVE_TASKS = {"maintenance_scan", "evidence_audit", "policy_validation", "repo_audit_readiness"}
EMBEDDING_TASKS = {"context_retrieval"}
RERANK_TASKS = {"context_reranking"}
FUTURE_GATED_TASKS = {
    "web_research_future",
    "document_analysis_future",
    "visual_analysis_future_gated",
    "audio_analysis_future_gated",
    "multimodal_analysis_future_gated",
    "voice_interaction_future_gated",
    "external_agent_oversight_future",
}
CONTEXT_BEARING_TASKS = {
    "repo_audit_candidate_notes",
    "code_explanation",
    "architecture_review",
    "risk_analysis",
    "documentation_summary",
    "translation_terminology",
    "context_retrieval",
    "context_reranking",
    *FUTURE_GATED_TASKS,
}
PRIVATE_PRIVACY_CLASSES = {"private", "private_repo", "personal_private", "sensitive", "regulated_or_compliance_sensitive"}
SECRET_PRIVACY_CLASSES = {"secret_like", "credential_like"}
RESOURCE_BLOCKED_STATUSES = {"resource_blocked", "disk_pressure_blocked", "disk_blocked", "resource_blocked"}

FORBIDDEN_TRUTHY_FIELDS = {
    "authority": "authority_must_be_false",
    "runtime_dispatch_allowed": "runtime_dispatch_not_allowed",
    "approval_grant": "approval_grant_not_allowed",
    "capability_grant": "capability_grant_not_allowed",
    "lease_grant": "lease_grant_not_allowed",
    "frontend_authority": "frontend_authority_not_allowed",
    "output_is_authority": "output_authority_not_allowed",
    "evidence_provided_by_auto_mode": "auto_mode_cannot_provide_evidence",
    "evidence_provided_by_policy": "auto_mode_cannot_provide_evidence",
    "evidence_provided_by_inventory": "auto_mode_cannot_provide_evidence",
    "evidence_created": "auto_mode_cannot_provide_evidence",
    "verifier_success": "auto_mode_cannot_mark_verifier_success",
    "verified_success": "auto_mode_cannot_mark_verifier_success",
    "success": "success_claim_denied",
    "proof": "proof_claim_denied",
    "certification_claim": "certification_claim_denied",
    "provider_selected": "provider_selection_not_allowed",
    "auto_mode_execution_allowed": "auto_mode_execution_not_allowed",
    "cloud_routing_allowed": "cloud_routing_not_allowed",
    "local_model_routing_allowed": "local_model_routing_not_allowed",
    "mcp_authority": "mcp_authority_not_allowed",
    "mcp_output_is_truth": "mcp_output_truth_claim_denied",
    "model_output_is_truth": "model_output_truth_claim_denied",
}

FORBIDDEN_BEHAVIOR_FIELDS = {
    "model_call_performed": "model_call_request_denied",
    "model_loaded": "model_load_request_denied",
    "endpoint_probed": "endpoint_probe_request_denied",
    "provider_authenticated": "provider_auth_request_denied",
    "cloud_api_called": "cloud_api_call_request_denied",
    "api_key_validated": "api_key_validation_request_denied",
    "secret_read": "secret_read_request_denied",
    "context_retrieval_performed": "context_retrieval_request_denied",
    "memory_retrieval_performed": "memory_retrieval_request_denied",
    "repo_file_read_performed": "repo_file_read_request_denied",
    "web_query_performed": "web_query_request_denied",
    "embedding_generated": "embedding_generation_request_denied",
    "reranking_performed": "reranking_request_denied",
    "inference_performed": "inference_request_denied",
    "vector_index_touched": "vector_index_request_denied",
    "data_sent_external": "external_data_transfer_denied",
    "api_call_performed": "api_call_request_denied",
    "mcp_call_performed": "mcp_call_request_denied",
    "tool_call_performed": "tool_call_request_denied",
}


@dataclass(frozen=True)
class ModelAutoModeFailure:
    reason: str
    field: str
    message: str


@dataclass(frozen=True)
class ModelAutoModeInput:
    request_id: str | None
    task_type: str | None
    user_preference_mode: str | None
    namespace: str | None
    privacy_class: str | None
    provider_class: str | None
    provider_status: str | None
    cloud_provider_status: str | None
    provider_secret_status: str | None
    resource_status: str | None
    source_refs: tuple[Mapping[str, Any], ...]
    limitations: tuple[str, ...]
    unknowns: tuple[str, ...]
    human_review_required: bool


@dataclass(frozen=True)
class ModelAutoModeDecision:
    contract_version: str
    selection_mode: str
    request_id: str | None
    task_type: str | None
    user_preference_mode: str | None
    namespace: str | None
    selected_provider_candidate: str | None
    selected_model_candidate: str | None
    fallback_mode: str | None
    why_this_mode: tuple[str, ...]
    why_not_cloud: tuple[str, ...]
    why_not_local: tuple[str, ...]
    why_not_model: tuple[str, ...]
    limitations: tuple[str, ...]
    unknowns: tuple[str, ...]
    failure_reasons: tuple[str, ...]
    failures: tuple[ModelAutoModeFailure, ...]
    auto_mode_input: ModelAutoModeInput | None
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = MODEL_AUTO_MODE_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_auto_mode: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    frontend_authority: bool = False
    model_call_performed: bool = False
    model_loaded: bool = False
    endpoint_probed: bool = False
    provider_authenticated: bool = False
    cloud_api_called: bool = False
    api_key_validated: bool = False
    secret_read: bool = False
    context_retrieval_performed: bool = False
    memory_retrieval_performed: bool = False
    repo_file_read_performed: bool = False
    web_query_performed: bool = False
    embedding_generated: bool = False
    reranking_performed: bool = False
    inference_performed: bool = False
    vector_index_touched: bool = False
    provider_selected: bool = False
    data_sent_external: bool = False
    auto_mode_execution_allowed: bool = False
    cloud_routing_allowed: bool = False
    local_model_routing_allowed: bool = False
    output_is_authority: bool = False
    requires_backend_validation: bool = True
    requires_policy_check: bool = True
    requires_human_review_for_unknowns: bool = True


def select_model_auto_mode_candidate(
    request: Mapping[str, Any],
    *,
    identity_scope_decision: Any | None = None,
    memory_governance_decision: Any | None = None,
    context_policy_decision: Any | None = None,
    policy_extension_decision: Any | None = None,
    local_model_inventory_decision: Any | None = None,
    model_provider_readiness_decision: Any | None = None,
    mission_control_decision: Any | None = None,
    tool_simulation_decision: Any | None = None,
    repo_audit_decision: Any | None = None,
    compliance_evidence_decision: Any | None = None,
    developer_work_passport_decision: Any | None = None,
    plugin_review_decision: Any | None = None,
) -> ModelAutoModeDecision:
    """Classify a non-authoritative provider/mode candidate without executing it."""

    if not isinstance(request, Mapping):
        failure = ModelAutoModeFailure("missing_request", "request", "request must be caller-supplied metadata")
        return _decision(
            selection_mode="unsupported",
            request_id=None,
            task_type=None,
            user_preference_mode=None,
            namespace=None,
            selected_provider_candidate=None,
            selected_model_candidate=None,
            fallback_mode=None,
            why_this_mode=(),
            why_not_cloud=("missing request",),
            why_not_local=("missing request",),
            why_not_model=("missing request",),
            limitations=(),
            unknowns=(),
            failures=(failure,),
            auto_mode_input=None,
        )

    data = deepcopy(dict(request))
    failures: list[ModelAutoModeFailure] = []
    _validate_forbidden_claims("request", data, failures)
    for label, decision in {
        "identity_scope": identity_scope_decision,
        "memory_governance": memory_governance_decision,
        "context_policy": context_policy_decision,
        "policy_extension": policy_extension_decision,
        "local_model_inventory": local_model_inventory_decision,
        "model_provider_readiness": model_provider_readiness_decision,
        "mission_control": mission_control_decision,
        "tool_simulation": tool_simulation_decision,
        "repo_audit": repo_audit_decision,
        "compliance_evidence": compliance_evidence_decision,
        "developer_work_passport": developer_work_passport_decision,
        "plugin_review": plugin_review_decision,
    }.items():
        _validate_related_decision(label, decision, failures)

    auto_input = ModelAutoModeInput(
        request_id=_text(data.get("request_id")),
        task_type=_text(data.get("task_type")),
        user_preference_mode=_text(data.get("user_preference_mode")),
        namespace=_text(data.get("namespace")),
        privacy_class=_text(data.get("privacy_class")),
        provider_class=_text(data.get("provider_class")),
        provider_status=_text(data.get("provider_status")),
        cloud_provider_status=_text(data.get("cloud_provider_status")),
        provider_secret_status=_text(data.get("provider_secret_status")),
        resource_status=_text(data.get("resource_status")),
        source_refs=_mapping_tuple(data.get("source_refs")),
        limitations=_text_tuple(data.get("limitations")),
        unknowns=_text_tuple(data.get("unknowns")),
        human_review_required=_truthy(data.get("human_review_required")),
    )
    _validate_input(auto_input, failures)
    _validate_related_statuses(
        auto_input,
        identity_scope_decision,
        memory_governance_decision,
        context_policy_decision,
        policy_extension_decision,
        failures,
    )

    selection = _select_mode(auto_input, failures, context_policy_decision, local_model_inventory_decision)
    provider_candidate, model_candidate = _candidate(auto_input, selection, local_model_inventory_decision)
    why_this, why_not_cloud, why_not_local, why_not_model = _reasons(
        auto_input,
        selection,
        failures,
        context_policy_decision,
        local_model_inventory_decision,
    )
    return _decision(
        selection_mode=selection,
        request_id=auto_input.request_id,
        task_type=auto_input.task_type,
        user_preference_mode=auto_input.user_preference_mode,
        namespace=auto_input.namespace,
        selected_provider_candidate=provider_candidate,
        selected_model_candidate=model_candidate,
        fallback_mode="passive_no_model" if selection != "passive_no_model" else None,
        why_this_mode=why_this,
        why_not_cloud=why_not_cloud,
        why_not_local=why_not_local,
        why_not_model=why_not_model,
        limitations=auto_input.limitations,
        unknowns=auto_input.unknowns,
        failures=tuple(failures),
        auto_mode_input=auto_input,
    )


def _decision(
    *,
    selection_mode: str,
    request_id: str | None,
    task_type: str | None,
    user_preference_mode: str | None,
    namespace: str | None,
    selected_provider_candidate: str | None,
    selected_model_candidate: str | None,
    fallback_mode: str | None,
    why_this_mode: tuple[str, ...],
    why_not_cloud: tuple[str, ...],
    why_not_local: tuple[str, ...],
    why_not_model: tuple[str, ...],
    limitations: tuple[str, ...],
    unknowns: tuple[str, ...],
    failures: tuple[ModelAutoModeFailure, ...],
    auto_mode_input: ModelAutoModeInput | None,
) -> ModelAutoModeDecision:
    return ModelAutoModeDecision(
        contract_version=MODEL_AUTO_MODE_VERSION,
        selection_mode=selection_mode,
        request_id=request_id,
        task_type=task_type,
        user_preference_mode=user_preference_mode,
        namespace=namespace,
        selected_provider_candidate=selected_provider_candidate,
        selected_model_candidate=selected_model_candidate,
        fallback_mode=fallback_mode,
        why_this_mode=why_this_mode,
        why_not_cloud=why_not_cloud,
        why_not_local=why_not_local,
        why_not_model=why_not_model,
        limitations=limitations,
        unknowns=unknowns,
        failure_reasons=tuple(dict.fromkeys(f.reason for f in failures)),
        failures=failures,
        auto_mode_input=auto_mode_input,
    )


def _validate_input(auto_input: ModelAutoModeInput, failures: list[ModelAutoModeFailure]) -> None:
    for field in ("request_id", "task_type", "user_preference_mode", "namespace"):
        if not getattr(auto_input, field):
            _add_failure(failures, f"missing_{field}", field, f"{field} is required")
    if auto_input.task_type and auto_input.task_type not in TASK_TYPES:
        _add_failure(failures, "unsupported_task_type", "task_type", "task type is not recognized")
    if auto_input.user_preference_mode and auto_input.user_preference_mode not in USER_PREFERENCE_MODES:
        _add_failure(failures, "unsupported_user_preference_mode", "user_preference_mode", "preference is not recognized")
    if auto_input.provider_class and auto_input.provider_class not in PROVIDER_CLASSES:
        _add_failure(failures, "unsupported_provider_class", "provider_class", "provider class is not recognized")
    if auto_input.provider_status and auto_input.provider_status not in PROVIDER_STATUSES:
        _add_failure(failures, "unsupported_provider_status", "provider_status", "provider status is not recognized")
    if auto_input.cloud_provider_status and auto_input.cloud_provider_status not in CLOUD_PROVIDER_STATUSES:
        _add_failure(failures, "unsupported_cloud_provider_status", "cloud_provider_status", "cloud status is not recognized")
    if auto_input.provider_secret_status and auto_input.provider_secret_status not in PROVIDER_SECRET_STATUSES:
        _add_failure(failures, "unsupported_provider_secret_status", "provider_secret_status", "secret status is not recognized")
    if auto_input.resource_status and auto_input.resource_status not in RESOURCE_STATUSES:
        _add_failure(failures, "unsupported_resource_status", "resource_status", "resource status is not recognized")
    if auto_input.privacy_class is None and auto_input.task_type in CONTEXT_BEARING_TASKS:
        _add_failure(failures, "missing_privacy_class", "privacy_class", "context-bearing tasks require privacy metadata")


def _validate_related_statuses(
    auto_input: ModelAutoModeInput,
    identity_scope_decision: Any | None,
    memory_governance_decision: Any | None,
    context_policy_decision: Any | None,
    policy_extension_decision: Any | None,
    failures: list[ModelAutoModeFailure],
) -> None:
    if auto_input.privacy_class in PRIVATE_PRIVACY_CLASSES and identity_scope_decision is None:
        _add_failure(failures, "missing_identity_scope", "identity_scope_decision", "private context requires identity scope")
    if identity_scope_decision is not None and _status_blocked(identity_scope_decision, "scope_status"):
        _add_failure(failures, "identity_scope_not_ready", "identity_scope_decision.scope_status", "identity scope is blocked")
    if auto_input.task_type in {"context_retrieval", "context_reranking"} and memory_governance_decision is None:
        _add_failure(failures, "missing_memory_governance", "memory_governance_decision", "retrieval/reranking requires memory governance")
    if memory_governance_decision is not None and _status_blocked(memory_governance_decision, "governance_status"):
        _add_failure(failures, "memory_governance_not_ready", "memory_governance_decision.governance_status", "memory governance is blocked")
    if auto_input.task_type in CONTEXT_BEARING_TASKS and context_policy_decision is None:
        _add_failure(failures, "missing_context_policy", "context_policy_decision", "context-bearing model mode requires context policy")
    if context_policy_decision is not None and _status_blocked(context_policy_decision, "policy_status"):
        _add_failure(failures, "context_policy_not_ready", "context_policy_decision.policy_status", "context policy is blocked")
    if policy_extension_decision is None and auto_input.task_type in FUTURE_GATED_TASKS:
        _add_failure(failures, "missing_policy_extension", "policy_extension_decision", "future task requires policy extension metadata")
    if policy_extension_decision is not None and _status_blocked(policy_extension_decision, "policy_outcome"):
        _add_failure(failures, "policy_extension_not_ready", "policy_extension_decision.policy_outcome", "policy extension is blocked")


def _select_mode(
    auto_input: ModelAutoModeInput,
    failures: list[ModelAutoModeFailure],
    context_policy_decision: Any | None,
    local_model_inventory_decision: Any | None,
) -> str:
    reasons = {failure.reason for failure in failures}
    task = auto_input.task_type or "unknown"
    preference = auto_input.user_preference_mode or "unknown"
    if any(reason.endswith("_request_denied") or "not_allowed" in reason for reason in reasons):
        return "blocked_by_policy"
    if "authority_must_be_false" in reasons or "runtime_dispatch_not_allowed" in reasons:
        return "blocked_by_policy"
    if task not in TASK_TYPES or task == "unknown" or preference == "unknown":
        return "unsupported" if "unsupported_task_type" in reasons else "ask_operator"
    if preference == "disabled":
        return "blocked_by_policy"
    if task in PASSIVE_TASKS:
        return "passive_no_model"
    if preference == "passive_only":
        return "passive_no_model"
    if preference == "ask_each_time":
        return "ask_operator"
    if auto_input.privacy_class in SECRET_PRIVACY_CLASSES or _context_field(context_policy_decision, "secret_context_allowed"):
        return "blocked_by_secret_boundary"
    if "raw_journal_blocked_by_default" in reasons or "raw_journal_not_allowed" in reasons:
        return "blocked_by_context_policy"
    if auto_input.privacy_class == "unknown":
        return "ask_operator"
    if auto_input.resource_status in RESOURCE_BLOCKED_STATUSES or auto_input.provider_status in RESOURCE_BLOCKED_STATUSES:
        return "blocked_by_resource"
    if "missing_identity_scope" in reasons or "identity_scope_not_ready" in reasons:
        return "blocked_by_identity_scope"
    if "missing_memory_governance" in reasons or "memory_governance_not_ready" in reasons:
        return "blocked_by_memory_governance"
    if "missing_context_policy" in reasons or "context_policy_not_ready" in reasons:
        return "blocked_by_context_policy"
    if "policy_extension_not_ready" in reasons:
        return "blocked_by_policy"
    if any(reason.startswith("missing_") or reason.startswith("unsupported_") for reason in reasons):
        return "blocked_by_unknown_metadata"
    if task in FUTURE_GATED_TASKS:
        return "future_gated"
    if _cloud_blocked(auto_input, context_policy_decision):
        if preference == "cloud_allowed":
            return "blocked_by_privacy"
    if auto_input.cloud_provider_status in {"region_blocked", "unsupported_region", "terms_unverified"}:
        return "blocked_by_region_or_terms"
    if auto_input.cloud_provider_status == "api_key_present_unverified" or auto_input.provider_secret_status == "secret_present_unverified":
        return "blocked_by_provider_status"
    if task in EMBEDDING_TASKS:
        return "local_embedding_candidate" if _has_model_role(local_model_inventory_decision, "embedding", task) else "blocked_by_provider_status"
    if task in RERANK_TASKS:
        return "local_reranker_candidate" if _has_model_role(local_model_inventory_decision, "reranker", task) else "blocked_by_provider_status"
    if preference == "local_first_cloud_fallback":
        return "hybrid_local_first_candidate" if _has_chat_candidate(local_model_inventory_decision, task) else "blocked_by_provider_status"
    if preference == "cloud_allowed":
        return "cloud_model_candidate_later"
    return "local_model_candidate" if _has_chat_candidate(local_model_inventory_decision, task) else "blocked_by_provider_status"


def _candidate(
    auto_input: ModelAutoModeInput,
    selection: str,
    local_model_inventory_decision: Any | None,
) -> tuple[str | None, str | None]:
    if selection == "passive_no_model":
        return "passive_backend", None
    if selection in {"local_model_candidate", "hybrid_local_first_candidate"}:
        return _local_provider(local_model_inventory_decision), _model_id_for_task(local_model_inventory_decision, auto_input.task_type or "")
    if selection == "local_embedding_candidate":
        return _local_provider(local_model_inventory_decision), _model_id_by_role(local_model_inventory_decision, "embedding", auto_input.task_type or "")
    if selection == "local_reranker_candidate":
        return _local_provider(local_model_inventory_decision), _model_id_by_role(local_model_inventory_decision, "reranker", auto_input.task_type or "")
    if selection == "cloud_model_candidate_later":
        return "cloud_provider_future", None
    return None, None


def _reasons(
    auto_input: ModelAutoModeInput,
    selection: str,
    failures: list[ModelAutoModeFailure],
    context_policy_decision: Any | None,
    local_model_inventory_decision: Any | None,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    why_this = [f"selection_mode={selection}"]
    if selection == "passive_no_model":
        why_this.append("deterministic backend validation or passive preference")
    if selection.startswith("local") or selection.startswith("hybrid_local"):
        why_this.append("local candidate metadata only; no provider selected")
    if selection == "future_gated":
        why_this.append("future privacy/provider boundary required")
    why_not_cloud: list[str] = []
    if auto_input.user_preference_mode == "local_only":
        why_not_cloud.append("local_only preference blocks cloud")
    if _cloud_blocked(auto_input, context_policy_decision):
        why_not_cloud.append("privacy/context policy blocks cloud")
    if auto_input.cloud_provider_status:
        why_not_cloud.append(f"cloud_provider_status={auto_input.cloud_provider_status}")
    why_not_local: list[str] = []
    if not local_model_inventory_decision:
        why_not_local.append("missing local model inventory")
    if auto_input.provider_status:
        why_not_local.append(f"provider_status={auto_input.provider_status}")
    why_not_model = [failure.reason for failure in failures]
    if selection == "passive_no_model":
        why_not_model.append("model not needed")
    return (
        tuple(dict.fromkeys(why_this)),
        tuple(dict.fromkeys(why_not_cloud)),
        tuple(dict.fromkeys(why_not_local)),
        tuple(dict.fromkeys(why_not_model)),
    )


def _validate_related_decision(label: str, decision: Any | None, failures: list[ModelAutoModeFailure]) -> None:
    if decision is None:
        return
    before = len(failures)
    _validate_forbidden_claims(label, decision, failures)
    if len(failures) > before:
        _add_failure(failures, "unsafe_related_decision", label, f"{label} cannot provide model routing authority")


def _validate_forbidden_claims(label: str, source: Any, failures: list[ModelAutoModeFailure]) -> None:
    for field, reason in FORBIDDEN_TRUTHY_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(failures, reason, f"{label}.{field}", "authority, grants, evidence, verifier success, routing, or execution claims are denied")
    for field, reason in FORBIDDEN_BEHAVIOR_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(failures, reason, f"{label}.{field}", "model/provider/context/memory/web/vector behavior is denied")
    execution_permission = _field_value(source, "execution_permission")
    if execution_permission not in (None, "", MODEL_AUTO_MODE_EXECUTION_PERMISSION):
        permission_text = str(execution_permission)
        if not permission_text.startswith("not_granted"):
            _add_failure(failures, "execution_permission_claim_denied", f"{label}.execution_permission", "Auto Mode cannot grant execution permission")


def _status_blocked(decision: Any, field: str) -> bool:
    status = str(_field_value(decision, field) or "")
    return status.startswith("blocked") or status in {"unsupported", "unknown", "clarification_required"}


def _cloud_blocked(auto_input: ModelAutoModeInput, context_policy_decision: Any | None) -> bool:
    if auto_input.user_preference_mode == "local_only":
        return True
    if auto_input.privacy_class in PRIVATE_PRIVACY_CLASSES or auto_input.privacy_class in SECRET_PRIVACY_CLASSES:
        return True
    if _context_field(context_policy_decision, "cloud_routing_allowed"):
        return True
    status = str(_field_value(context_policy_decision, "policy_status") or "")
    return status.startswith("blocked")


def _context_field(context_policy_decision: Any | None, field: str) -> bool:
    return _field_bool(context_policy_decision, field) if context_policy_decision is not None else False


def _has_chat_candidate(decision: Any | None, task: str) -> bool:
    return _model_id_for_task(decision, task) is not None


def _has_model_role(decision: Any | None, role: str, task: str) -> bool:
    return _model_id_by_role(decision, role, task) is not None


def _model_id_for_task(decision: Any | None, task: str) -> str | None:
    for mapping in _role_mappings(decision):
        role = str(_field_value(mapping, "model_role") or "")
        if role in {"embedding", "reranker", "vision", "audio_stt", "audio_tts", "multimodal"}:
            continue
        tasks = tuple(_field_value(mapping, "task_roles") or ())
        if task in tasks and not _field_bool(mapping, "future_gated"):
            return _text(_field_value(mapping, "model_id"))
    return None


def _model_id_by_role(decision: Any | None, role: str, task: str) -> str | None:
    for mapping in _role_mappings(decision):
        tasks = tuple(_field_value(mapping, "task_roles") or ())
        if str(_field_value(mapping, "model_role") or "") == role and task in tasks:
            return _text(_field_value(mapping, "model_id"))
    return None


def _role_mappings(decision: Any | None) -> tuple[Any, ...]:
    if decision is None:
        return ()
    mappings = _field_value(decision, "role_mappings")
    return tuple(mappings or ())


def _local_provider(decision: Any | None) -> str | None:
    provider_class = _text(_field_value(decision, "provider_class"))
    if provider_class:
        return provider_class
    return None


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


def _field_bool(source: Any, field: str) -> bool:
    return _truthy(_field_value(source, field))


def _field_value(source: Any, field: str) -> Any:
    if source is None:
        return None
    if isinstance(source, Mapping):
        return source.get(field)
    return getattr(source, field, None)


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _truthy(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on", "allowed", "grant"}
    return bool(value)


def _add_failure(
    failures: list[ModelAutoModeFailure],
    reason: str,
    field: str,
    message: str,
) -> None:
    failures.append(ModelAutoModeFailure(reason=reason, field=field, message=message))
