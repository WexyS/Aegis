from __future__ import annotations

from aegis.core.local_model_profiles import (
    LOCAL_MODEL_PROFILE_EXECUTION_PERMISSION,
    build_resource_guardrails,
    list_local_model_profiles,
    match_configured_model_profile,
    recommended_default_profile_id,
)


def _profiles_by_id() -> dict[str, dict[str, object]]:
    return {profile["profile_id"]: profile for profile in list_local_model_profiles()}


def test_deterministic_local_model_profiles_exist() -> None:
    profiles = _profiles_by_id()

    assert set(profiles) == {
        "fast_summary",
        "default_proposal",
        "coding_review",
        "reasoning_review",
        "heavy_experiment",
        "rerank_only",
    }
    assert recommended_default_profile_id() == "default_proposal"


def test_profile_hints_and_resource_guardrails_match_operator_hardware() -> None:
    profiles = _profiles_by_id()
    guardrails = build_resource_guardrails()

    assert guardrails["hardware_target"] == "nvidia_rtx_4080_12gb_vram_32gb_ram"
    assert guardrails["vram_gb_target"] == 12
    assert guardrails["system_ram_gb_target"] == 32
    assert guardrails["expected_local_server"] == "http://127.0.0.1:1234/v1"
    assert profiles["default_proposal"]["preferred_model_id_hint"] == "google/gemma-4-12b"
    assert profiles["fast_summary"]["preferred_model_id_hint"] == "qwen/qwen3.5-9b"
    assert profiles["coding_review"]["preferred_model_id_hint"] == "qwen2.5-coder-14b-instruct"
    assert profiles["reasoning_review"]["preferred_model_id_hint"] == "deepseek-r1-distill-qwen-14b"
    assert profiles["heavy_experiment"]["preferred_model_id_hint"] == "gpt-oss-20b"
    assert profiles["rerank_only"]["preferred_model_id_hint"] == "qwen3-reranker-0.6b"


def test_profile_budget_and_selection_policy() -> None:
    profiles = _profiles_by_id()

    assert profiles["fast_summary"]["memory_pressure"] == "low"
    assert profiles["fast_summary"]["recommended_max_input_chars"] == 3000
    assert profiles["fast_summary"]["recommended_max_output_tokens"] == 256
    assert profiles["fast_summary"]["recommended_timeout_seconds"] == 20

    assert profiles["default_proposal"]["default_profile"] is True
    assert profiles["default_proposal"]["memory_pressure"] == "balanced"
    assert profiles["default_proposal"]["recommended_max_input_chars"] == 4000
    assert profiles["default_proposal"]["recommended_max_output_tokens"] == 384
    assert profiles["default_proposal"]["recommended_timeout_seconds"] == 30

    assert profiles["coding_review"]["manual_selection_required"] is True
    assert profiles["coding_review"]["memory_pressure"] == "medium_high"
    assert profiles["coding_review"]["recommended_max_input_chars"] == 6000
    assert profiles["coding_review"]["recommended_timeout_seconds"] == 45

    assert profiles["reasoning_review"]["manual_selection_required"] is True
    assert profiles["reasoning_review"]["memory_pressure"] == "medium_high"
    assert profiles["reasoning_review"]["recommended_max_input_chars"] == 5000
    assert profiles["reasoning_review"]["recommended_timeout_seconds"] == 60

    assert profiles["heavy_experiment"]["default_profile"] is False
    assert profiles["heavy_experiment"]["manual_selection_required"] is True
    assert profiles["heavy_experiment"]["memory_pressure"] == "high"
    assert "may_spill_to_ram_or_cpu_on_12gb_vram" in profiles["heavy_experiment"]["warnings"]

    assert profiles["rerank_only"]["eligible_for_completion"] is False
    assert profiles["rerank_only"]["eligible_for_rerank"] is True


def test_all_local_profiles_are_non_authority_and_local_first() -> None:
    for profile in list_local_model_profiles():
        assert profile["cloud_fallback_allowed"] is False
        assert profile["execution_permission"] == LOCAL_MODEL_PROFILE_EXECUTION_PERMISSION
        assert profile["authority"] is False
        assert profile["model_output_is_truth"] is False
        assert profile["evidence"] is False
        assert profile["verifier_success"] is False
        assert profile["approval_granted"] is False
        assert profile["capability_lease_granted"] is False


def test_known_model_profile_matching_is_metadata_only() -> None:
    assert match_configured_model_profile("google/gemma-4-12b")["matched_profile_id"] == "default_proposal"
    assert match_configured_model_profile("mradermacher/qwen2.5-coder-14b-instruct-q4_k_m")[
        "matched_profile_id"
    ] == "coding_review"
    assert match_configured_model_profile("unsloth/deepseek-r1-distill-qwen-14b-q4_k_m")[
        "matched_profile_id"
    ] == "reasoning_review"
    assert match_configured_model_profile("unsloth/gpt-oss-20b-q3_k_m")["matched_profile_id"] == "heavy_experiment"

    match = match_configured_model_profile("qwen.qwen3-reranker-0.6b")
    assert match["matched_profile_id"] == "rerank_only"
    assert match["completion_safe"] is False
    assert match["rerank_only"] is True
    assert "configured_model_appears_rerank_only_not_completion_safe" in match["warnings"]

    unknown = match_configured_model_profile("operator/custom-local-model")
    assert unknown["status"] == "unknown_configured_model"
    assert unknown["matched_profile_id"] is None
    assert unknown["automatic_model_switch_performed"] is False
    assert unknown["live_installation_claimed"] is False
