from __future__ import annotations

from aegis.core.operator_auto_router import (
    CONTRACT_NAME,
    EMPTY_STATUS,
    NO_ACTION_FLAGS,
    PREVIEW_STATUS,
    build_operator_route_preview,
)


def _assert_no_action_flags(preview: dict[str, object]) -> None:
    for field, expected in NO_ACTION_FLAGS.items():
        assert preview[field] is expected, field
    assert preview["proposal_only"] is True
    assert preview["requires_backend_owned_policy_before_execution"] is True
    assert preview["process_trace_is_summary_not_hidden_reasoning"] is True
    assessment = preview["capability_assessment"]
    assert isinstance(assessment, dict)
    assert assessment["preview_only"] is True
    assert assessment["execution_authorized"] is False


def test_empty_request_returns_blocked_preview_without_execution() -> None:
    preview = build_operator_route_preview("   ")

    assert preview["contract"] == CONTRACT_NAME
    assert preview["status"] == EMPTY_STATUS
    assert preview["primary_intent"] == "unknown"
    assert preview["route_id"] == "status_explainer"
    _assert_no_action_flags(preview)


def test_status_request_routes_to_status_explainer() -> None:
    preview = build_operator_route_preview("Aegis su an ne durumda? Explain health.")

    assert preview["status"] == PREVIEW_STATUS
    assert preview["primary_intent"] == "ask_status"
    assert preview["route_id"] == "status_explainer"
    assert preview["capability_assessment"]["classification"] == "observe_only"
    _assert_no_action_flags(preview)


def test_ui_screenshot_plus_codex_prompt_routes_to_vision_to_code_prompt() -> None:
    preview = build_operator_route_preview("Bu UI sorununu analiz et ve Codex promptu hazırla")

    assert preview["route_id"] == "vision_to_code_prompt"
    assert "vision_review" in preview["intents"]
    assert "code_prompt" in preview["intents"]
    assert preview["vision_boundary_required"] is True
    assert preview["artifact"]["type"] == "codex_prompt_draft"
    _assert_no_action_flags(preview)


def test_memory_request_routes_to_memory_policy_preview() -> None:
    preview = build_operator_route_preview("Bunu hafızaya al ama önce açıkla")

    assert preview["route_id"] == "memory_policy_preview"
    assert preview["memory_action_proposed"] is True
    assert preview["artifact"]["type"] == "memory_action_preview"
    _assert_no_action_flags(preview)


def test_web_research_request_routes_to_research_plan() -> None:
    preview = build_operator_route_preview("Gerekirse web araştırması yap")

    assert preview["route_id"] == "research_plan"
    assert preview["research_boundary_required"] is True
    assert preview["artifact"]["type"] == "research_plan"
    _assert_no_action_flags(preview)


def test_model_provider_keywords_route_to_model_hub_review() -> None:
    for prompt in (
        "LM Studio modelimi değerlendir",
        "Qwen ve Gemma profilini incele",
        "DeepSeek OpenRouter sınırını açıkla",
        "Moonshot Kimi provider readiness nedir?",
    ):
        preview = build_operator_route_preview(prompt)
        assert preview["route_id"] == "model_hub_review"
        assert preview["primary_intent"] == "model_hub"
        _assert_no_action_flags(preview)


def test_kimi_moonshot_mentions_are_disabled_metadata_only() -> None:
    preview = build_operator_route_preview("Kimi K2.7 Code modelini Aegis için değerlendir")

    assert preview["route_id"] == "model_hub_review"
    assert preview["external_cloud_candidate_disabled"] is True
    assert preview["cloud_fallback_allowed"] is False
    assert preview["cloud_call_performed"] is False
    assert preview["external_provider_call_performed"] is False
    assert preview["kimi_moonshot_call_performed"] is False
    assert any(
        item["profile_id"] == "external_cloud_candidate"
        and item["selected_for_call"] is False
        for item in preview["model_candidates"]
    )
    _assert_no_action_flags(preview)


def test_command_execute_request_routes_to_command_approval_preview() -> None:
    preview = build_operator_route_preview("Bu komutu çalıştırmadan önce güvenli plan hazırla")

    assert preview["route_id"] == "command_approval_preview"
    assert preview["approval_needed"] is True
    assert preview["permission_mode"] == "safe_preview"
    assert preview["artifact"]["type"] == "command_approval_preview"
    assert preview["capability_assessment"]["classification"] == "execution_unavailable"
    _assert_no_action_flags(preview)


def test_approval_permission_request_routes_to_approval_review() -> None:
    preview = build_operator_route_preview("Bu işlem için onay ve permission durumunu incele")

    assert preview["route_id"] == "approval_review"
    assert preview["approval_needed"] is True
    _assert_no_action_flags(preview)


def test_safe_sprint_plan_routes_to_safe_plan_builder() -> None:
    preview = build_operator_route_preview("Sıradaki güvenli sprint planını hazırla")

    assert preview["route_id"] == "safe_plan_builder"
    assert preview["primary_intent"] == "safe_plan"
    assert preview["artifact"]["type"] == "safe_plan_draft"
    _assert_no_action_flags(preview)


def test_stable_preview_id_is_deterministic_for_same_input() -> None:
    first = build_operator_route_preview("LM Studio modelimi değerlendir")
    second = build_operator_route_preview("LM Studio modelimi değerlendir")

    assert first["preview_id"] == second["preview_id"]
    assert first["artifact"]["id"] == second["artifact"]["id"]


def test_trace_items_are_summary_metadata_not_hidden_reasoning() -> None:
    preview = build_operator_route_preview("Bu UI sorununu analiz et ve Codex promptu hazırla")

    trace_items = preview["trace_items"]
    assert [item["step"] for item in trace_items] == [
        "request_received",
        "intent_preview_generated",
        "route_selected",
        "model_candidate_selected",
        "permission_boundary_evaluated",
        "cloud_boundary_evaluated",
        "memory_policy_evaluated",
        "artifact_draft_created",
        "blocked_actions_not_performed",
    ]
    assert all(item["status"] in {"done", "info", "blocked", "waiting"} for item in trace_items)
    assert all("hidden reasoning" not in item["detail"].casefold() for item in trace_items)
    assert all(len(item["detail"]) <= 160 for item in trace_items)


def test_artifact_is_preview_only_with_no_action_safety_flags() -> None:
    preview = build_operator_route_preview("Draft a safe sprint plan")
    artifact = preview["artifact"]

    assert artifact["status"] == "preview_only"
    assert artifact["safety_flags"] == (
        "no_command_execution",
        "no_model_call",
        "no_cloud_call",
        "no_external_provider_call",
        "no_kimi_moonshot_call",
        "no_image_upload",
        "no_video_upload",
        "no_memory_write",
        "no_tool_call",
        "no_evidence",
        "no_verifier_success",
        "no_approval_or_permission_grant",
    )
    _assert_no_action_flags(preview)
