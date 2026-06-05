from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping


LOCAL_MODEL_CONTEXT_PROFILE_VERSION = "local-model-context-profile-eval-readiness/1"
LOCAL_MODEL_CONTEXT_PROFILE_EXECUTION_PERMISSION = "not_granted_by_model_context_profile"

MODEL_ROLE_CLASSES = {
    "fast_general_chat",
    "lightweight_summary",
    "mission_control_wording",
    "general_reasoning",
    "turkish_technical_explanation",
    "coding_assistant",
    "repo_audit_candidate_notes",
    "architecture_review",
    "risk_analysis",
    "translation_terminology",
    "embedding",
    "reranking",
    "future_multimodal_reasoning",
    "future_vision",
    "future_audio",
    "future_video_frame",
    "future_screen_observation",
    "fallback_general",
    "unknown",
}

MODEL_FAMILY_CLASSES = {
    "qwen_general",
    "qwen_coder",
    "deepseek_reasoning",
    "gemma_multimodal_general",
    "gpt_oss_general",
    "bge_embedding",
    "qwen_embedding",
    "qwen_reranker",
    "qwen_vl_future",
    "unknown",
}

PROVIDER_CLASSES = {
    "lm_studio_local",
    "ollama_local_optional",
    "openai_compatible_local",
    "vllm_local",
    "mock_test_provider",
    "unknown",
}

CONTEXT_SOURCE_ALLOWANCE_CLASSES = {
    "public_docs_allowed",
    "repo_code_candidate_local_only",
    "repo_metadata_allowed",
    "user_memory_blocked_by_default",
    "project_memory_requires_governance",
    "raw_journal_blocked",
    "raw_evidence_blocked",
    "evidence_refs_allowed",
    "web_source_candidates_allowed_after_gateway",
    "document_text_future_gated",
    "image_observation_future_gated",
    "audio_observation_future_gated",
    "video_frame_future_gated",
    "unknown_blocked",
}

CONTEXT_BUDGET_CLASSES = {
    "tiny_context",
    "small_context",
    "medium_context",
    "large_context_candidate",
    "unknown_context",
    "blocked",
}

SAMPLING_PROFILE_CLASSES = {
    "strict_json",
    "safe_general",
    "architecture_review",
    "coding_low_temperature",
    "creative_ui_copy",
    "multimodal_future_gated",
    "unknown",
}

EVAL_READINESS_CLASSES = {
    "not_evaluated",
    "user_observed_metadata_only",
    "eval_plan_candidate",
    "benchmark_future_gated",
    "health_required",
    "provider_probe_required",
    "context_policy_required",
    "multimodal_privacy_required",
    "failed_eval_metadata_only",
    "unknown",
}

RISK_CLASSES = {
    "self_identity_drift",
    "self_report_untrusted",
    "hallucination_risk",
    "json_format_risk",
    "context_overrun_risk",
    "role_mismatch_risk",
    "modality_future_gated",
    "resource_unknown",
    "provider_health_unknown",
    "privacy_boundary_required",
    "unknown",
}

EMBEDDING_FAMILIES = {"bge_embedding", "qwen_embedding"}
RERANKER_FAMILIES = {"qwen_reranker"}
MULTIMODAL_ROLES = {
    "future_multimodal_reasoning",
    "future_vision",
    "future_audio",
    "future_video_frame",
    "future_screen_observation",
}
CHAT_ROLES = {
    "fast_general_chat",
    "lightweight_summary",
    "mission_control_wording",
    "general_reasoning",
    "turkish_technical_explanation",
    "coding_assistant",
    "repo_audit_candidate_notes",
    "architecture_review",
    "risk_analysis",
    "translation_terminology",
    "fallback_general",
}

FORBIDDEN_TRUTHY_FIELDS = {
    "authority": "authority_must_be_false",
    "runtime_dispatch_allowed": "runtime_dispatch_not_allowed",
    "approval_grant": "approval_grant_not_allowed",
    "capability_grant": "capability_grant_not_allowed",
    "lease_grant": "lease_grant_not_allowed",
    "evidence_provided_by_model_profile": "model_profile_cannot_provide_evidence",
    "evidence_created": "model_profile_cannot_provide_evidence",
    "verifier_success": "model_profile_cannot_mark_verifier_success",
    "verified_success": "model_profile_cannot_mark_verifier_success",
    "mutation_performed": "mutation_performed_denied",
    "success": "success_claim_denied",
    "proof": "proof_claim_denied",
    "certification_claim": "certification_claim_denied",
    "frontend_authority": "frontend_authority_not_allowed",
    "frontend_result_is_authority": "frontend_authority_not_allowed",
    "model_output_is_authority": "model_output_authority_claim_denied",
    "mcp_output_is_authority": "mcp_output_authority_claim_denied",
    "tool_output_is_authority": "tool_output_authority_claim_denied",
    "model_output_is_truth": "model_output_truth_claim_denied",
    "mcp_output_is_truth": "mcp_output_truth_claim_denied",
    "tool_output_is_truth": "tool_output_truth_claim_denied",
    "model_identity_verified": "model_identity_verification_denied",
    "self_report_identity_verified": "model_identity_verification_denied",
    "benchmark_claim_verified": "benchmark_verification_denied",
    "user_observation_is_benchmark_proof": "benchmark_verification_denied",
    "provider_health_verified": "provider_health_verification_denied",
}

FORBIDDEN_BEHAVIOR_FIELDS = {
    "model_loaded": "model_load_denied",
    "model_call_performed": "model_call_denied",
    "inference_performed": "inference_denied",
    "provider_probed": "provider_probe_denied",
    "endpoint_probed": "endpoint_probe_denied",
    "api_key_validated": "api_key_validation_denied",
    "secret_read": "secret_read_denied",
    "live_model_files_inspected": "live_model_file_inspection_denied",
    "embedding_generated": "embedding_generation_denied",
    "reranking_performed": "reranking_denied",
    "multimodal_inference_performed": "multimodal_inference_denied",
    "benchmark_run": "benchmark_run_denied",
    "eval_result_created": "eval_result_creation_denied",
    "context_retrieval_performed": "context_retrieval_denied",
    "memory_retrieval_performed": "memory_retrieval_denied",
    "web_query_performed": "web_query_denied",
    "repo_file_read_performed": "repo_file_read_denied",
    "tool_call_performed": "tool_call_denied",
    "mcp_call_performed": "mcp_call_denied",
    "api_call_performed": "api_call_denied",
    "profile_record_created": "profile_record_creation_denied",
    "data_sent_external": "external_data_transfer_denied",
    "runtime_state_mutated": "runtime_state_mutation_denied",
    "journal_mutated": "journal_mutation_denied",
    "evidence_mutated": "evidence_mutation_denied",
    "replay_mutated": "replay_mutation_denied",
}


@dataclass(frozen=True)
class LocalModelContextProfileFailure:
    reason: str
    field: str
    message: str


@dataclass(frozen=True)
class RelatedModelProfileReference:
    label: str
    observed_status: str | None
    reference_only: bool = True
    authority: bool = False
    future_gated: bool = False
    implementation_claim: bool = False


@dataclass(frozen=True)
class LocalModelContextProfileInput:
    request_id: str | None
    model_id: str | None
    model_name: str | None
    model_family_class: str | None
    provider_class: str | None
    intended_role: str | None
    context_source_allowance_class: str | None
    context_budget_class: str | None
    sampling_profile_class: str | None
    eval_readiness_class: str | None
    source_refs: tuple[Mapping[str, Any], ...]
    provenance: tuple[Mapping[str, Any], ...]
    limitations: tuple[str, ...]
    unknowns: tuple[str, ...]
    known_risks: tuple[str, ...]
    human_review_required: bool
    future_privacy_boundary_present: bool
    private_repo_context_candidate: bool
    cloud_context_candidate: bool


@dataclass(frozen=True)
class LocalModelContextProfileDecision:
    contract_version: str
    profile_status: str
    request_id: str | None
    model_id: str | None
    model_name: str | None
    model_family_class: str | None
    provider_class: str | None
    intended_role: str | None
    context_source_allowance_class: str | None
    context_budget_class: str | None
    sampling_profile_class: str | None
    eval_readiness_class: str | None
    role_suitability_status: str
    context_allowance_status: str
    context_budget_status: str
    sampling_profile_status: str
    eval_readiness_status: str
    known_risks: tuple[str, ...]
    qwen35_retained_candidate: bool
    gemma_multimodal_candidate: bool
    self_identity_drift_preserved: bool
    unknown_resource_or_provider_health_preserved: bool
    future_gated: bool
    human_review_required: bool
    related_references: tuple[RelatedModelProfileReference, ...]
    failure_reasons: tuple[str, ...]
    failures: tuple[LocalModelContextProfileFailure, ...]
    profile_input: LocalModelContextProfileInput | None
    authority: bool = False
    runtime_dispatch_allowed: bool = False
    execution_permission: str = LOCAL_MODEL_CONTEXT_PROFILE_EXECUTION_PERMISSION
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    evidence_provided_by_model_profile: bool = False
    verifier_success: bool = False
    mutation_performed: bool = False
    frontend_authority: bool = False
    model_loaded: bool = False
    model_call_performed: bool = False
    inference_performed: bool = False
    provider_probed: bool = False
    endpoint_probed: bool = False
    api_key_validated: bool = False
    secret_read: bool = False
    live_model_files_inspected: bool = False
    embedding_generated: bool = False
    reranking_performed: bool = False
    multimodal_inference_performed: bool = False
    benchmark_run: bool = False
    eval_result_created: bool = False
    context_retrieval_performed: bool = False
    memory_retrieval_performed: bool = False
    web_query_performed: bool = False
    repo_file_read_performed: bool = False
    profile_record_created: bool = False
    data_sent_external: bool = False
    model_identity_verified: bool = False
    benchmark_claim_verified: bool = False
    provider_health_verified: bool = False
    requires_backend_validation: bool = True
    requires_policy_check: bool = True
    read_only_projection: bool = True


def validate_local_model_context_profile_request(
    request: Mapping[str, Any] | None,
    *,
    web_research_gateway_decision: Any | None = None,
    system_drift_integrity_decision: Any | None = None,
    action_attribution_decision: Any | None = None,
    audit_query_layer_decision: Any | None = None,
    passive_observe_decision: Any | None = None,
    identity_scope_decision: Any | None = None,
    memory_governance_decision: Any | None = None,
    policy_extension_decision: Any | None = None,
    context_policy_decision: Any | None = None,
    model_auto_mode_decision: Any | None = None,
    local_provider_health_decision: Any | None = None,
    local_provider_probe_design_decision: Any | None = None,
    capability_lease_decision: Any | None = None,
    local_model_inventory_decision: Any | None = None,
    mission_control_decision: Any | None = None,
    tool_simulation_decision: Any | None = None,
    repo_audit_decision: Any | None = None,
    compliance_evidence_decision: Any | None = None,
    developer_work_passport_decision: Any | None = None,
    plugin_review_decision: Any | None = None,
) -> LocalModelContextProfileDecision:
    """Validate supplied local model profile metadata without calling or probing models."""

    if not isinstance(request, Mapping):
        failure = LocalModelContextProfileFailure(
            reason="missing_request",
            field="request",
            message="local model context profile requires caller-supplied metadata",
        )
        return _decision(profile_input=None, related_references=(), failures=(failure,))

    data = deepcopy(dict(request))
    failures: list[LocalModelContextProfileFailure] = []
    related_references: list[RelatedModelProfileReference] = []

    _validate_forbidden_claims("request", data, failures)
    for label, decision in {
        "web_research_gateway": web_research_gateway_decision,
        "system_drift_integrity": system_drift_integrity_decision,
        "action_attribution": action_attribution_decision,
        "audit_query_layer": audit_query_layer_decision,
        "passive_observe": passive_observe_decision,
        "identity_scope": identity_scope_decision,
        "memory_governance": memory_governance_decision,
        "policy_extension": policy_extension_decision,
        "context_policy": context_policy_decision,
        "model_auto_mode": model_auto_mode_decision,
        "local_provider_health": local_provider_health_decision,
        "local_provider_probe_design": local_provider_probe_design_decision,
        "capability_lease": capability_lease_decision,
        "local_model_inventory": local_model_inventory_decision,
        "mission_control": mission_control_decision,
        "tool_simulation": tool_simulation_decision,
        "repo_audit": repo_audit_decision,
        "compliance_evidence": compliance_evidence_decision,
        "developer_work_passport": developer_work_passport_decision,
        "plugin_review": plugin_review_decision,
    }.items():
        _validate_related_decision(label, decision, failures, related_references)

    profile_input = LocalModelContextProfileInput(
        request_id=_text(data.get("request_id")),
        model_id=_text(data.get("model_id")),
        model_name=_text(data.get("model_name")),
        model_family_class=_text(data.get("model_family_class")),
        provider_class=_text(data.get("provider_class")),
        intended_role=_text(data.get("intended_role")),
        context_source_allowance_class=_text(data.get("context_source_allowance_class")),
        context_budget_class=_text(data.get("context_budget_class")),
        sampling_profile_class=_text(data.get("sampling_profile_class")),
        eval_readiness_class=_text(data.get("eval_readiness_class")),
        source_refs=_mapping_tuple(data.get("source_refs")),
        provenance=_mapping_tuple(data.get("provenance")),
        limitations=_text_tuple(data.get("limitations")),
        unknowns=_text_tuple(data.get("unknowns")),
        known_risks=_risk_tuple(data.get("known_risks")),
        human_review_required=_truthy(data.get("human_review_required")),
        future_privacy_boundary_present=_truthy(data.get("future_privacy_boundary_present")),
        private_repo_context_candidate=_truthy(data.get("private_repo_context_candidate")),
        cloud_context_candidate=_truthy(data.get("cloud_context_candidate")),
    )

    _validate_required(profile_input, failures)
    _validate_role_and_context(profile_input, identity_scope_decision, memory_governance_decision, context_policy_decision, failures)

    return _decision(
        profile_input=profile_input,
        related_references=tuple(related_references),
        failures=tuple(failures),
    )


def _decision(
    *,
    profile_input: LocalModelContextProfileInput | None,
    related_references: tuple[RelatedModelProfileReference, ...],
    failures: tuple[LocalModelContextProfileFailure, ...],
) -> LocalModelContextProfileDecision:
    future_gated = bool(profile_input and _is_future_gated(profile_input))
    return LocalModelContextProfileDecision(
        contract_version=LOCAL_MODEL_CONTEXT_PROFILE_VERSION,
        profile_status=_profile_status(profile_input, list(failures), future_gated),
        request_id=profile_input.request_id if profile_input else None,
        model_id=profile_input.model_id if profile_input else None,
        model_name=profile_input.model_name if profile_input else None,
        model_family_class=profile_input.model_family_class if profile_input else None,
        provider_class=profile_input.provider_class if profile_input else None,
        intended_role=profile_input.intended_role if profile_input else None,
        context_source_allowance_class=profile_input.context_source_allowance_class if profile_input else None,
        context_budget_class=profile_input.context_budget_class if profile_input else None,
        sampling_profile_class=profile_input.sampling_profile_class if profile_input else None,
        eval_readiness_class=profile_input.eval_readiness_class if profile_input else None,
        role_suitability_status=_role_suitability_status(profile_input, list(failures), future_gated),
        context_allowance_status=_context_allowance_status(profile_input, list(failures)),
        context_budget_status=_context_budget_status(profile_input, list(failures)),
        sampling_profile_status=_sampling_profile_status(profile_input, list(failures)),
        eval_readiness_status=_eval_readiness_status(profile_input, list(failures), future_gated),
        known_risks=profile_input.known_risks if profile_input else (),
        qwen35_retained_candidate=bool(profile_input and profile_input.model_family_class == "qwen_general" and profile_input.intended_role == "fast_general_chat"),
        gemma_multimodal_candidate=bool(profile_input and profile_input.model_family_class == "gemma_multimodal_general"),
        self_identity_drift_preserved=bool(profile_input and "self_identity_drift" in profile_input.known_risks),
        unknown_resource_or_provider_health_preserved=bool(
            profile_input
            and ("resource_unknown" in profile_input.known_risks or "provider_health_unknown" in profile_input.known_risks)
        ),
        future_gated=future_gated,
        human_review_required=_human_review_required(profile_input, list(failures), future_gated),
        related_references=related_references,
        failure_reasons=tuple(failure.reason for failure in failures),
        failures=failures,
        profile_input=profile_input,
    )


def _validate_required(
    profile_input: LocalModelContextProfileInput,
    failures: list[LocalModelContextProfileFailure],
) -> None:
    for field in (
        "request_id",
        "model_id",
        "model_family_class",
        "provider_class",
        "intended_role",
        "context_budget_class",
        "sampling_profile_class",
        "eval_readiness_class",
    ):
        if not getattr(profile_input, field):
            _add_failure(failures, f"missing_{field}", field, f"model profile request is missing {field}")
    if profile_input.model_family_class and profile_input.model_family_class not in MODEL_FAMILY_CLASSES:
        _add_failure(failures, "unsupported_model_family_class", "model_family_class", "model family class is not recognized")
    if profile_input.provider_class and profile_input.provider_class not in PROVIDER_CLASSES:
        _add_failure(failures, "unsupported_provider_class", "provider_class", "provider class is not recognized")
    if profile_input.intended_role and profile_input.intended_role not in MODEL_ROLE_CLASSES:
        _add_failure(failures, "unsupported_intended_role", "intended_role", "intended role is not recognized")
    if profile_input.context_source_allowance_class and profile_input.context_source_allowance_class not in CONTEXT_SOURCE_ALLOWANCE_CLASSES:
        _add_failure(failures, "unsupported_context_source_allowance_class", "context_source_allowance_class", "context source allowance class is not recognized")
    if profile_input.context_budget_class and profile_input.context_budget_class not in CONTEXT_BUDGET_CLASSES:
        _add_failure(failures, "unsupported_context_budget_class", "context_budget_class", "context budget class is not recognized")
    if profile_input.sampling_profile_class and profile_input.sampling_profile_class not in SAMPLING_PROFILE_CLASSES:
        _add_failure(failures, "unsupported_sampling_profile_class", "sampling_profile_class", "sampling profile class is not recognized")
    if profile_input.eval_readiness_class and profile_input.eval_readiness_class not in EVAL_READINESS_CLASSES:
        _add_failure(failures, "unsupported_eval_readiness_class", "eval_readiness_class", "eval readiness class is not recognized")
    if not (profile_input.source_refs or profile_input.provenance):
        _add_failure(failures, "missing_source_refs_or_provenance", "source_refs", "model profile metadata requires source refs or provenance")


def _validate_role_and_context(
    profile_input: LocalModelContextProfileInput,
    identity_scope_decision: Any | None,
    memory_governance_decision: Any | None,
    context_policy_decision: Any | None,
    failures: list[LocalModelContextProfileFailure],
) -> None:
    if profile_input.model_family_class in EMBEDDING_FAMILIES and profile_input.intended_role != "embedding":
        _add_failure(failures, "embedding_model_cannot_be_chat_role", "intended_role", "embedding models cannot be chat/general models")
    if profile_input.model_family_class in RERANKER_FAMILIES and profile_input.intended_role != "reranking":
        _add_failure(failures, "reranker_model_cannot_be_chat_role", "intended_role", "rerankers cannot be chat/general models")
    if profile_input.model_family_class == "qwen_coder" and profile_input.intended_role in MULTIMODAL_ROLES:
        _add_failure(failures, "coding_model_cannot_default_multimodal", "intended_role", "coding model profile cannot default to multimodal roles")
    if profile_input.intended_role in MULTIMODAL_ROLES and not profile_input.future_privacy_boundary_present:
        _add_failure(failures, "multimodal_role_requires_future_privacy_boundary", "future_privacy_boundary_present", "multimodal roles require a future privacy boundary")
    if profile_input.context_source_allowance_class in {"raw_journal_blocked", "raw_evidence_blocked", "unknown_blocked"}:
        _add_failure(failures, "blocked_context_source_not_allowed", "context_source_allowance_class", "blocked context sources cannot be allowed to model profiles")
    if profile_input.context_source_allowance_class == "user_memory_blocked_by_default":
        _add_failure(failures, "user_memory_blocked_by_default", "context_source_allowance_class", "user memory remains blocked by default")
    if profile_input.context_source_allowance_class == "project_memory_requires_governance" and memory_governance_decision is None:
        _add_failure(failures, "missing_memory_governance", "memory_governance_decision", "project memory profile metadata requires Memory Governance")
    if profile_input.private_repo_context_candidate and identity_scope_decision is None:
        _add_failure(failures, "missing_identity_scope", "identity_scope_decision", "private repo profile metadata requires Identity Scope")
    if profile_input.context_budget_class == "large_context_candidate" and context_policy_decision is None:
        _add_failure(failures, "missing_context_policy", "context_policy_decision", "large context candidates require Context Policy")
    if profile_input.private_repo_context_candidate and profile_input.cloud_context_candidate:
        _add_failure(failures, "private_repo_cloud_context_contradiction", "cloud_context_candidate", "private repo context remains local-only candidate")


def _validate_related_decision(
    label: str,
    decision: Any | None,
    failures: list[LocalModelContextProfileFailure],
    related_references: list[RelatedModelProfileReference],
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
            f"{label} cannot grant model profile authority, dispatch, grants, evidence, verifier success, execution, health proof, benchmark proof, or records",
        )
    related_references.append(
        RelatedModelProfileReference(
            label=label,
            observed_status=_related_status(decision),
            reference_only=True,
            authority=False,
            future_gated=_related_future_gated(decision),
            implementation_claim=False,
        )
    )


def _validate_forbidden_claims(
    label: str,
    source: Any,
    failures: list[LocalModelContextProfileFailure],
) -> None:
    for field, reason in FORBIDDEN_TRUTHY_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(
                failures,
                reason,
                f"{label}.{field}",
                f"{label} cannot claim authority, grants, evidence, verifier success, identity, benchmark, health, proof, or truth",
            )
    for field, reason in FORBIDDEN_BEHAVIOR_FIELDS.items():
        if _field_bool(source, field):
            _add_failure(
                failures,
                reason,
                f"{label}.{field}",
                f"{label} cannot load/call/probe models, inspect files, run evals, retrieve context, read repos, mutate, or transfer data",
            )
    execution_permission = _field_value(source, "execution_permission")
    if execution_permission not in (None, "", LOCAL_MODEL_CONTEXT_PROFILE_EXECUTION_PERMISSION):
        permission_text = str(execution_permission)
        if not permission_text.startswith("not_granted"):
            _add_failure(
                failures,
                "execution_permission_claim_denied",
                f"{label}.execution_permission",
                "model profile metadata cannot grant execution permission",
            )


def _profile_status(
    profile_input: LocalModelContextProfileInput | None,
    failures: list[LocalModelContextProfileFailure],
    future_gated: bool,
) -> str:
    if profile_input is None:
        return "blocked_by_missing_required_field"
    reasons = {failure.reason for failure in failures}
    if reasons:
        if "unsafe_related_decision" in reasons:
            return "blocked_by_unsafe_related_decision"
        if any(reason.startswith("missing_") or reason.startswith("unsupported_") for reason in reasons):
            return "blocked_by_missing_required_field"
        if "execution_permission_claim_denied" in reasons:
            return "blocked_by_authority_claim"
        if any("denied" in reason or "mutation" in reason or "external" in reason for reason in reasons):
            return "blocked_by_execution_claim"
        if any("identity" in reason or "benchmark" in reason or "health" in reason or "truth" in reason for reason in reasons):
            return "blocked_by_truth_claim"
        if any("context" in reason or "memory" in reason or "privacy" in reason or "cloud" in reason for reason in reasons):
            return "blocked_by_context_policy"
        if any("role" in reason or "multimodal" in reason for reason in reasons):
            return "blocked_by_role_mismatch"
        if any("authority" in reason or "grant" in reason or "permission" in reason for reason in reasons):
            return "blocked_by_authority_claim"
        if any("evidence" in reason or "verifier" in reason or "proof" in reason for reason in reasons):
            return "blocked_by_evidence_claim"
        return "blocked_by_policy"
    if future_gated:
        return "future_gated"
    if profile_input.human_review_required or _human_review_required(profile_input, failures, future_gated):
        return "profile_requires_human_review"
    return "profile_candidate_ready"


def _role_suitability_status(
    profile_input: LocalModelContextProfileInput | None,
    failures: list[LocalModelContextProfileFailure],
    future_gated: bool,
) -> str:
    if profile_input is None or failures:
        return "blocked"
    if profile_input.intended_role == "embedding":
        return "embedding_candidate_not_chat"
    if profile_input.intended_role == "reranking":
        return "reranker_candidate_not_chat"
    if future_gated:
        return "future_gated"
    return "role_candidate_only"


def _context_allowance_status(
    profile_input: LocalModelContextProfileInput | None,
    failures: list[LocalModelContextProfileFailure],
) -> str:
    if profile_input is None or failures:
        return "blocked"
    if profile_input.context_source_allowance_class in {"repo_code_candidate_local_only", "repo_metadata_allowed"}:
        return "local_or_metadata_candidate"
    if profile_input.context_source_allowance_class == "evidence_refs_allowed":
        return "refs_only_candidate"
    if profile_input.context_source_allowance_class and "future_gated" in profile_input.context_source_allowance_class:
        return "future_gated"
    return "context_candidate_only"


def _context_budget_status(
    profile_input: LocalModelContextProfileInput | None,
    failures: list[LocalModelContextProfileFailure],
) -> str:
    if profile_input is None or failures:
        return "blocked"
    if profile_input.context_budget_class == "large_context_candidate":
        return "large_context_candidate_only"
    if profile_input.context_budget_class == "blocked":
        return "blocked"
    return "budget_metadata_only"


def _sampling_profile_status(
    profile_input: LocalModelContextProfileInput | None,
    failures: list[LocalModelContextProfileFailure],
) -> str:
    if profile_input is None or failures:
        return "blocked"
    return "sampling_metadata_only"


def _eval_readiness_status(
    profile_input: LocalModelContextProfileInput | None,
    failures: list[LocalModelContextProfileFailure],
    future_gated: bool,
) -> str:
    if profile_input is None or failures:
        return "blocked"
    if future_gated or profile_input.eval_readiness_class in {"benchmark_future_gated", "multimodal_privacy_required"}:
        return "future_gated"
    return "eval_metadata_only"


def _human_review_required(
    profile_input: LocalModelContextProfileInput | None,
    failures: list[LocalModelContextProfileFailure],
    future_gated: bool,
) -> bool:
    if profile_input is None:
        return True
    if failures or future_gated or profile_input.human_review_required:
        return True
    return (
        "self_identity_drift" in profile_input.known_risks
        or "resource_unknown" in profile_input.known_risks
        or "provider_health_unknown" in profile_input.known_risks
        or profile_input.context_budget_class in {"large_context_candidate", "unknown_context"}
        or profile_input.eval_readiness_class
        in {"not_evaluated", "user_observed_metadata_only", "health_required", "provider_probe_required", "unknown"}
    )


def _is_future_gated(profile_input: LocalModelContextProfileInput) -> bool:
    return (
        profile_input.intended_role in MULTIMODAL_ROLES
        or profile_input.context_source_allowance_class
        in {"document_text_future_gated", "image_observation_future_gated", "audio_observation_future_gated", "video_frame_future_gated"}
        or profile_input.sampling_profile_class == "multimodal_future_gated"
        or profile_input.eval_readiness_class in {"benchmark_future_gated", "multimodal_privacy_required"}
        or profile_input.model_family_class == "qwen_vl_future"
    )


def _risk_tuple(value: Any) -> tuple[str, ...]:
    risks = _text_tuple(value)
    return tuple(risk for risk in risks if risk in RISK_CLASSES)


def _related_status(decision: Any) -> str | None:
    for field in (
        "profile_status",
        "readiness_status",
        "inventory_status",
        "selection_mode",
        "policy_status",
        "policy_outcome",
        "governance_status",
        "scope_status",
        "probe_result_status",
        "health_status",
        "query_status",
        "display_state",
        "decision_status",
    ):
        value = _field_value(decision, field)
        if value:
            return str(value)
    return None


def _related_future_gated(decision: Any) -> bool:
    status = str(_related_status(decision) or "")
    return _field_bool(decision, "future_gated") or "future" in status


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
    failures: list[LocalModelContextProfileFailure],
    reason: str,
    field: str,
    message: str,
) -> None:
    failures.append(LocalModelContextProfileFailure(reason=reason, field=field, message=message))
