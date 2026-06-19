from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


LOCAL_MODEL_PROFILE_EXECUTION_PERMISSION = "not_granted_by_model_profile"
LOCAL_MODEL_HARDWARE_TARGET = "nvidia_rtx_4080_12gb_vram_32gb_ram"
TARGET_VRAM_GB = 12
TARGET_SYSTEM_RAM_GB = 32


@dataclass(frozen=True)
class LocalModelProfile:
    profile_id: str
    label: str
    purpose: str
    preferred_model_id_hint: str
    model_id_matchers: tuple[str, ...]
    eligible_for_completion: bool
    eligible_for_probe: bool
    eligible_for_rerank: bool
    default_profile: bool
    manual_selection_required: bool
    hardware_target: str
    vram_gb_target: int
    system_ram_gb_target: int
    memory_pressure: str
    recommended_max_input_chars: int
    recommended_max_output_tokens: int
    recommended_timeout_seconds: int
    warnings: tuple[str, ...]
    limitations: tuple[str, ...]
    operator_steps: tuple[str, ...]
    cloud_fallback_allowed: bool = False
    execution_permission: str = LOCAL_MODEL_PROFILE_EXECUTION_PERMISSION
    authority: bool = False
    model_output_is_truth: bool = False
    evidence: bool = False
    verifier_success: bool = False
    approval_granted: bool = False
    capability_lease_granted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


LOCAL_MODEL_PROFILES: tuple[LocalModelProfile, ...] = (
    LocalModelProfile(
        profile_id="fast_summary",
        label="Fast summary",
        purpose="Fast, low-resource summaries and short explanations.",
        preferred_model_id_hint="qwen/qwen3.5-9b",
        model_id_matchers=("qwen3.5-9b", "qwen3_5-9b", "qwen3.5 9b", "qwen3.5"),
        eligible_for_completion=True,
        eligible_for_probe=True,
        eligible_for_rerank=False,
        default_profile=False,
        manual_selection_required=False,
        hardware_target=LOCAL_MODEL_HARDWARE_TARGET,
        vram_gb_target=TARGET_VRAM_GB,
        system_ram_gb_target=TARGET_SYSTEM_RAM_GB,
        memory_pressure="low",
        recommended_max_input_chars=3000,
        recommended_max_output_tokens=256,
        recommended_timeout_seconds=20,
        warnings=("verify_exact_lm_studio_model_id_from_v1_models",),
        limitations=("not_live_installation_proof", "not_quality_or_latency_proof"),
        operator_steps=(
            "Load the intended Qwen 9B-class model in LM Studio.",
            "Set AEGIS_LM_STUDIO_MODEL to the exact id reported by /v1/models.",
            "Use this profile for short summaries before trying larger models.",
        ),
    ),
    LocalModelProfile(
        profile_id="default_proposal",
        label="Default proposal",
        purpose="Balanced local proposals and general Aegis explanations.",
        preferred_model_id_hint="google/gemma-4-12b",
        model_id_matchers=("google/gemma-4-12b", "gemma-4-12b", "gemma 4 12b", "gemma-12b"),
        eligible_for_completion=True,
        eligible_for_probe=True,
        eligible_for_rerank=False,
        default_profile=True,
        manual_selection_required=False,
        hardware_target=LOCAL_MODEL_HARDWARE_TARGET,
        vram_gb_target=TARGET_VRAM_GB,
        system_ram_gb_target=TARGET_SYSTEM_RAM_GB,
        memory_pressure="balanced",
        recommended_max_input_chars=4000,
        recommended_max_output_tokens=384,
        recommended_timeout_seconds=30,
        warnings=("verify_exact_lm_studio_model_id_from_v1_models",),
        limitations=("not_live_installation_proof", "not_quality_or_latency_proof"),
        operator_steps=(
            "Use as the default local proposal profile when resource pressure is acceptable.",
            "Keep prompts small and safe; do not include secrets, raw logs, journals, evidence, or repo dumps.",
        ),
    ),
    LocalModelProfile(
        profile_id="vision_review",
        label="Vision review",
        purpose="Qwen 3 VL 8B candidate for screenshot, UI review, visual inspection, and image-grounded reasoning proposals.",
        preferred_model_id_hint="qwen/qwen3-vl-8b",
        model_id_matchers=(
            "qwen3-vl-8b",
            "qwen3 vl 8b",
            "qwen 3 vl 8b",
            "qwen3-vl-8b-instruct",
            "qwen 3 vl",
        ),
        eligible_for_completion=True,
        eligible_for_probe=True,
        eligible_for_rerank=False,
        default_profile=False,
        manual_selection_required=True,
        hardware_target=LOCAL_MODEL_HARDWARE_TARGET,
        vram_gb_target=TARGET_VRAM_GB,
        system_ram_gb_target=TARGET_SYSTEM_RAM_GB,
        memory_pressure="medium_high",
        recommended_max_input_chars=3000,
        recommended_max_output_tokens=384,
        recommended_timeout_seconds=45,
        warnings=(
            "vision_input_requires_explicit_future_boundary",
            "automatic_image_upload_disabled",
            "automatic_model_call_disabled",
            "verify_exact_lm_studio_model_id_from_v1_models",
        ),
        limitations=(
            "not_live_installation_proof",
            "not_quality_or_latency_proof",
            "profile_does_not_enable_vision_input_routing",
            "output_is_proposal_only",
            "no_authority_evidence_verifier_approval_permission_or_execution_granted",
        ),
        operator_steps=(
            "Use only as a local vision profile candidate after a future Vision Input Boundary exists.",
            "Do not upload screenshots or images automatically from this profile metadata.",
            "Verify the exact Qwen 3 VL 8B LM Studio model id from /v1/models before any manual smoke.",
        ),
    ),
    LocalModelProfile(
        profile_id="coding_review",
        label="Coding review",
        purpose="Code explanation and review-oriented local proposals.",
        preferred_model_id_hint="qwen2.5-coder-14b-instruct",
        model_id_matchers=("qwen2.5-coder", "qwen2_5-coder", "qwen 2.5 coder", "coder-14b-instruct"),
        eligible_for_completion=True,
        eligible_for_probe=True,
        eligible_for_rerank=False,
        default_profile=False,
        manual_selection_required=True,
        hardware_target=LOCAL_MODEL_HARDWARE_TARGET,
        vram_gb_target=TARGET_VRAM_GB,
        system_ram_gb_target=TARGET_SYSTEM_RAM_GB,
        memory_pressure="medium_high",
        recommended_max_input_chars=6000,
        recommended_max_output_tokens=512,
        recommended_timeout_seconds=45,
        warnings=("higher_memory_pressure_on_12gb_vram", "verify_exact_lm_studio_model_id_from_v1_models"),
        limitations=("not_live_installation_proof", "not_quality_or_latency_proof"),
        operator_steps=(
            "Select manually for coding review or code explanation.",
            "Reduce input size if LM Studio spills to RAM/CPU or times out.",
        ),
    ),
    LocalModelProfile(
        profile_id="reasoning_review",
        label="Reasoning review",
        purpose="Heavier local reasoning, risk analysis, and architecture review proposals.",
        preferred_model_id_hint="deepseek-r1-distill-qwen-14b",
        model_id_matchers=("deepseek-r1-distill-qwen-14b", "deepseek-r1", "distill-qwen-14b"),
        eligible_for_completion=True,
        eligible_for_probe=True,
        eligible_for_rerank=False,
        default_profile=False,
        manual_selection_required=True,
        hardware_target=LOCAL_MODEL_HARDWARE_TARGET,
        vram_gb_target=TARGET_VRAM_GB,
        system_ram_gb_target=TARGET_SYSTEM_RAM_GB,
        memory_pressure="medium_high",
        recommended_max_input_chars=5000,
        recommended_max_output_tokens=512,
        recommended_timeout_seconds=60,
        warnings=("higher_latency_expected", "higher_memory_pressure_on_12gb_vram"),
        limitations=("not_live_installation_proof", "not_quality_or_latency_proof"),
        operator_steps=(
            "Select manually for architecture or risk review.",
            "Prefer smaller prompts and verify proposal output against backend truth.",
        ),
    ),
    LocalModelProfile(
        profile_id="heavy_experiment",
        label="Heavy experiment",
        purpose="Manual heavy local experiment only.",
        preferred_model_id_hint="gpt-oss-20b",
        model_id_matchers=("gpt-oss-20b", "gpt oss 20b", "gpt_oss_20b"),
        eligible_for_completion=True,
        eligible_for_probe=True,
        eligible_for_rerank=False,
        default_profile=False,
        manual_selection_required=True,
        hardware_target=LOCAL_MODEL_HARDWARE_TARGET,
        vram_gb_target=TARGET_VRAM_GB,
        system_ram_gb_target=TARGET_SYSTEM_RAM_GB,
        memory_pressure="high",
        recommended_max_input_chars=3000,
        recommended_max_output_tokens=384,
        recommended_timeout_seconds=75,
        warnings=(
            "manual_experiment_only",
            "may_spill_to_ram_or_cpu_on_12gb_vram",
            "expect_latency_or_timeout_risk",
        ),
        limitations=("not_live_installation_proof", "not_quality_or_latency_proof", "not_default_profile"),
        operator_steps=(
            "Use only after smaller local profiles are insufficient.",
            "Expect high memory pressure and keep prompts short.",
        ),
    ),
    LocalModelProfile(
        profile_id="rerank_only",
        label="Rerank only",
        purpose="Search/rerank support only; not safe as a proposal/completion model.",
        preferred_model_id_hint="qwen3-reranker-0.6b",
        model_id_matchers=("qwen3-reranker", "reranker-0.6b", "reranker"),
        eligible_for_completion=False,
        eligible_for_probe=True,
        eligible_for_rerank=True,
        default_profile=False,
        manual_selection_required=True,
        hardware_target=LOCAL_MODEL_HARDWARE_TARGET,
        vram_gb_target=TARGET_VRAM_GB,
        system_ram_gb_target=TARGET_SYSTEM_RAM_GB,
        memory_pressure="low",
        recommended_max_input_chars=0,
        recommended_max_output_tokens=0,
        recommended_timeout_seconds=20,
        warnings=("configured_model_appears_rerank_only_not_completion_safe",),
        limitations=("not_a_chat_or_proposal_model", "not_live_installation_proof"),
        operator_steps=(
            "Use only for future reranking/search support.",
            "Do not configure this as the proposal completion model.",
        ),
    ),
)


def list_local_model_profiles() -> list[dict[str, Any]]:
    return [profile.to_dict() for profile in LOCAL_MODEL_PROFILES]


def build_resource_guardrails() -> dict[str, Any]:
    return {
        "hardware_target": LOCAL_MODEL_HARDWARE_TARGET,
        "gpu": "NVIDIA RTX 4080",
        "vram_gb_target": TARGET_VRAM_GB,
        "system_ram_gb_target": TARGET_SYSTEM_RAM_GB,
        "local_model_manager": "LM Studio",
        "expected_local_server": "http://127.0.0.1:1234/v1",
        "default_profile_id": "default_proposal",
        "recommended_order": (
            "fast_summary",
            "default_proposal",
            "vision_review",
            "coding_review",
            "reasoning_review",
            "heavy_experiment",
            "rerank_only",
        ),
        "automatic_model_switching_allowed": False,
        "ui_env_write_allowed": False,
        "live_probe_required_for_installation_claim": True,
        "configured_model_is_not_live_proof": True,
        "warnings": (
            "hardware_safety_is_not_guaranteed",
            "larger_models_may_spill_to_ram_or_cpu",
            "exact_lm_studio_model_ids_must_be_verified_from_v1_models",
        ),
        "limitations": (
            "resource_guardrails_are_static_recommendations",
            "no_model_loaded_or_called_by_profile_projection",
        ),
    }


def recommended_default_profile_id() -> str:
    return "default_proposal"


def match_configured_model_profile(configured_model: str | None) -> dict[str, Any]:
    candidate = str(configured_model or "").strip()
    if not candidate:
        return _match_payload(
            status="no_configured_model",
            configured_model=None,
            matched_profile=None,
            match_type="none",
            warnings=("no_lm_studio_model_configured",),
        )

    normalized = _normalize_model_id(candidate)
    for profile in LOCAL_MODEL_PROFILES:
        if normalized == _normalize_model_id(profile.preferred_model_id_hint):
            return _match_payload(
                status="matched",
                configured_model=candidate,
                matched_profile=profile,
                match_type="exact_hint",
                warnings=_profile_match_warnings(profile),
            )

    for profile in LOCAL_MODEL_PROFILES:
        for matcher in profile.model_id_matchers:
            if _normalize_model_id(matcher) in normalized:
                return _match_payload(
                    status="matched",
                    configured_model=candidate,
                    matched_profile=profile,
                    match_type="family_substring",
                    warnings=_profile_match_warnings(profile),
                )

    return _match_payload(
        status="unknown_configured_model",
        configured_model=candidate,
        matched_profile=None,
        match_type="unknown",
        warnings=("configured_model_profile_unknown_no_auto_switch",),
    )


def _match_payload(
    *,
    status: str,
    configured_model: str | None,
    matched_profile: LocalModelProfile | None,
    match_type: str,
    warnings: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "status": status,
        "configured_model": configured_model,
        "matched_profile_id": matched_profile.profile_id if matched_profile else None,
        "matched_profile_label": matched_profile.label if matched_profile else None,
        "match_type": match_type,
        "completion_safe": bool(matched_profile.eligible_for_completion) if matched_profile else False,
        "rerank_only": matched_profile.profile_id == "rerank_only" if matched_profile else False,
        "automatic_model_switch_performed": False,
        "live_installation_claimed": False,
        "warnings": warnings,
        "limitations": (
            "profile_match_uses_configured_model_metadata_only",
            "lm_studio_probe_required_for_live_model_proof",
        ),
        "authority": False,
        "evidence": False,
        "verifier_success": False,
    }


def _profile_match_warnings(profile: LocalModelProfile) -> tuple[str, ...]:
    warnings = list(profile.warnings)
    if profile.profile_id == "rerank_only":
        warnings.append("configured_model_appears_rerank_only_not_completion_safe")
    if profile.memory_pressure == "high":
        warnings.append("high_memory_pressure_on_target_hardware")
    return tuple(dict.fromkeys(warnings))


def _normalize_model_id(value: str) -> str:
    return str(value or "").strip().lower().replace("\\", "/").replace("_", "-")
