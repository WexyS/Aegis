from __future__ import annotations

import copy

from aegis.core.external_provider_broker_boundary import (
    EXTERNAL_PROVIDER_BROKER_CONTRACT,
    EXTERNAL_PROVIDER_BROKER_EXECUTION_PERMISSION,
    REQUIRED_OPERATOR_ACKNOWLEDGEMENTS,
    build_external_provider_broker_boundary,
    build_external_provider_prompt_preview,
    build_provider_setup_guidance,
    detect_prompt_risk_markers,
)
from aegis.core.external_provider_readiness import list_external_provider_readiness


FALSE_INVARIANTS = (
    "authority",
    "runtime_dispatch_allowed",
    "cloud_calls_enabled_now",
    "external_provider_calls_performed",
    "approval_grant",
    "approval_granted",
    "permission_granted",
    "capability_grant",
    "capability_lease_granted",
    "lease_grant",
    "evidence_created",
    "evidence",
    "verifier_success",
    "mutation_performed",
    "frontend_authority",
    "cloud_call_performed",
    "external_api_called",
    "http_request_performed",
    "model_call_performed",
    "provider_authenticated",
    "provider_key_value_exposed",
    "prompt_payload_sent",
    "data_sent_external",
    "transcript_persisted",
    "memory_write_performed",
    "tool_call_performed",
    "mcp_call_performed",
    "plugin_execution_performed",
    "agent_execution_performed",
    "workflow_execution_performed",
    "computer_control_performed",
    "shell_command_performed",
    "file_mutation_performed",
)


def _assert_false_invariants(record: dict[str, object]) -> None:
    for field in FALSE_INVARIANTS:
        assert record[field] is False, field


def test_broker_boundary_is_preview_only_and_non_authoritative() -> None:
    boundary = build_external_provider_broker_boundary(provider_readiness=list_external_provider_readiness({}))

    assert boundary["contract"] == EXTERNAL_PROVIDER_BROKER_CONTRACT
    assert boundary["status"] == "designed_disabled"
    assert boundary["execution_permission"] == EXTERNAL_PROVIDER_BROKER_EXECUTION_PERMISSION
    assert boundary["provider_key_presence_is_authorization"] is False
    assert boundary["manual_operator_opt_in_required"] is True
    assert boundary["provider_selection_required"] is True
    assert boundary["exact_model_selection_required"] is True
    assert boundary["operator_managed_env_only"] is True
    assert boundary["ui_key_input_allowed"] is False
    assert boundary["ui_env_write_allowed"] is False
    assert boundary["automatic_fallback_allowed"] is False
    assert boundary["local_failure_triggers_cloud"] is False
    assert boundary["prompt_preview_required"] is True
    assert boundary["cost_warning_required"] is True
    assert boundary["privacy_warning_required"] is True
    assert boundary["redaction_review_required"] is True
    assert boundary["secrets_allowed_in_prompt"] is False
    assert boundary["raw_logs_allowed_in_prompt"] is False
    assert boundary["raw_journals_allowed_in_prompt"] is False
    assert boundary["raw_evidence_allowed_in_prompt"] is False
    assert boundary["repo_dump_allowed_in_prompt"] is False
    assert boundary["proposal_only_output_required"] is True
    assert boundary["output_authority"] is False
    assert boundary["output_is_evidence"] is False
    assert boundary["output_is_verifier_success"] is False
    assert boundary["memory_write_allowed"] is False
    assert boundary["tool_execution_allowed"] is False
    assert boundary["provider_setup_guidance"]
    _assert_false_invariants(boundary)


def test_provider_setup_guidance_never_exposes_key_values() -> None:
    secret = "sk-this-key-must-not-leak"
    readiness = list_external_provider_readiness({"AEGIS_OPENROUTER_API_KEY": secret})

    guidance = build_provider_setup_guidance(provider_readiness=readiness)
    openrouter = next(item for item in guidance if item["provider_id"] == "openrouter")

    assert openrouter["status"] == "key_present_calls_disabled"
    assert openrouter["api_key_present"] is True
    assert openrouter["api_key_value_exposed"] is False
    assert openrouter["cloud_call_enabled"] is False
    assert openrouter["automatic_fallback_allowed"] is False
    assert "<paste-key-in-your-own-shell>" in openrouter["api_key_placeholder"]
    assert secret not in repr(guidance)


def test_moonshot_kimi_provider_setup_guidance_is_disabled_preview_only() -> None:
    secret = "moonshot-secret-must-not-leak"
    readiness = list_external_provider_readiness({"AEGIS_MOONSHOT_API_KEY": secret})

    guidance = build_provider_setup_guidance(provider_readiness=readiness)
    kimi = next(item for item in guidance if item["provider_id"] == "moonshot_kimi")

    assert kimi["label"] == "Moonshot / Kimi"
    assert kimi["status"] == "key_present_calls_disabled"
    assert kimi["api_key_env_var"] == "AEGIS_MOONSHOT_API_KEY"
    assert kimi["model_env_var"] == "AEGIS_MOONSHOT_MODEL"
    assert kimi["base_url_env_var"] == "AEGIS_MOONSHOT_BASE_URL"
    assert kimi["default_base_url_guidance"] == "https://api.moonshot.ai/v1"
    assert "kimi-k2.7-code" in kimi["suggested_models"]
    assert "kimi-k2.7-code" in kimi["model_placeholder"]
    assert "<paste-key-in-your-own-shell>" in kimi["api_key_placeholder"]
    assert secret not in repr(kimi)
    assert kimi["api_key_present"] is True
    assert kimi["api_key_value_exposed"] is False
    assert kimi["operator_managed_env_only"] is True
    assert kimi["ui_key_input_allowed"] is False
    assert kimi["ui_env_write_allowed"] is False
    assert kimi["cloud_call_enabled"] is False
    assert kimi["automatic_fallback_allowed"] is False


def test_valid_preview_request_still_blocks_provider_call() -> None:
    request = {
        "provider_id": "openrouter",
        "model_id": "future/model",
        "purpose": "explanation",
        "prompt": "Explain this status using only safe metadata.",
        "operator_acknowledgements": list(REQUIRED_OPERATOR_ACKNOWLEDGEMENTS),
    }
    original = copy.deepcopy(request)

    preview = build_external_provider_prompt_preview(
        request,
        provider_readiness=list_external_provider_readiness({"AEGIS_OPENROUTER_API_KEY": "present"}),
    )

    assert request == original
    assert preview["status"] == "blocked_until_external_provider_broker_enabled"
    assert preview["provider_id"] == "openrouter"
    assert preview["provider_status"] == "key_present_calls_disabled"
    assert preview["would_call_provider"] is False
    assert preview["prompt_preview_only"] is True
    assert preview["manual_operator_opt_in_required"] is True
    assert preview["provider_selection_required"] is True
    assert preview["exact_model_selection_required"] is True
    assert preview["provider_key_presence_is_authorization"] is False
    assert preview["automatic_fallback_allowed"] is False
    assert preview["local_failure_triggers_cloud"] is False
    assert preview["missing_acknowledgements"] == ()
    assert preview["blocked_reasons"] == (
        "external_provider_broker_not_enabled",
        "external_provider_calls_disabled",
    )
    _assert_false_invariants(preview)


def test_moonshot_kimi_preview_request_remains_blocked_and_no_send() -> None:
    preview = build_external_provider_prompt_preview(
        {
            "provider_id": "moonshot_kimi",
            "model_id": "kimi-k2.7-code",
            "purpose": "coding_review",
            "prompt": "Review this small code summary as proposal-only metadata.",
            "operator_acknowledgements": list(REQUIRED_OPERATOR_ACKNOWLEDGEMENTS),
        },
        provider_readiness=list_external_provider_readiness({"AEGIS_MOONSHOT_API_KEY": "present"}),
    )

    assert preview["status"] == "blocked_until_external_provider_broker_enabled"
    assert preview["provider_id"] == "moonshot_kimi"
    assert preview["provider_label"] == "Moonshot / Kimi"
    assert preview["model_id"] == "kimi-k2.7-code"
    assert preview["would_call_provider"] is False
    assert preview["cloud_call_performed"] is False
    assert preview["external_api_called"] is False
    assert preview["http_request_performed"] is False
    assert preview["model_call_performed"] is False
    assert preview["prompt_payload_sent"] is False
    assert preview["data_sent_external"] is False
    assert preview["transcript_persisted"] is False
    _assert_false_invariants(preview)


def test_preview_redacts_secret_like_prompt_material_and_keeps_calls_disabled() -> None:
    secret = "sk-supersecretvalue12345"
    preview = build_external_provider_prompt_preview(
        {
            "provider_id": "openai",
            "purpose": "explanation",
            "prompt": f"Use api_key={secret} with Authorization: Bearer very-secret-token",
            "operator_acknowledgements": list(REQUIRED_OPERATOR_ACKNOWLEDGEMENTS),
        },
        provider_readiness=list_external_provider_readiness({"AEGIS_OPENAI_API_KEY": "configured"}),
    )

    assert "possible_api_key_marker" in preview["heuristic_prompt_risk_markers"]
    assert "api_key_marker" in preview["heuristic_prompt_risk_markers"]
    assert "token_marker" in preview["heuristic_prompt_risk_markers"]
    assert secret not in preview["prompt_preview"]
    assert "very-secret-token" not in preview["prompt_preview"]
    assert "prompt_contains_sensitive_or_raw_diagnostic_markers" in preview["blocked_reasons"]
    assert preview["status"] == "blocked_by_prompt_safety_preview"
    assert preview["cloud_call_performed"] is False
    assert preview["data_sent_external"] is False
    assert preview["provider_key_value_exposed"] is False


def test_missing_acknowledgements_and_unknown_provider_block_preview() -> None:
    preview = build_external_provider_prompt_preview(
        {
            "provider_id": "unknown-provider",
            "purpose": "explanation",
            "prompt": "Short safe prompt.",
            "operator_acknowledgements": [],
        },
        provider_readiness=list_external_provider_readiness({}),
    )

    assert preview["status"] == "blocked_by_unknown_provider"
    assert "unsupported_or_missing_provider" in preview["blocked_reasons"]
    assert "required_operator_acknowledgements_missing" in preview["blocked_reasons"]
    assert set(preview["missing_acknowledgements"]) == set(REQUIRED_OPERATOR_ACKNOWLEDGEMENTS)
    _assert_false_invariants(preview)


def test_empty_or_oversized_prompt_blocks_without_external_behavior() -> None:
    empty_preview = build_external_provider_prompt_preview(
        {"provider_id": "gemini", "purpose": "explanation", "prompt": ""},
        provider_readiness=list_external_provider_readiness({}),
    )
    large_preview = build_external_provider_prompt_preview(
        {"provider_id": "gemini", "purpose": "explanation", "prompt": "x" * 4001},
        provider_readiness=list_external_provider_readiness({}),
    )

    assert empty_preview["status"] == "blocked_by_empty_prompt"
    assert large_preview["status"] == "blocked_by_prompt_too_large"
    assert empty_preview["external_api_called"] is False
    assert large_preview["external_api_called"] is False
    assert empty_preview["model_call_performed"] is False
    assert large_preview["model_call_performed"] is False


def test_risk_marker_detection_is_heuristic_only() -> None:
    markers = detect_prompt_risk_markers(
        "Traceback (most recent call last):\nlogs/runtime_events.jsonl\n.env\nnode_modules/pkg"
    )

    assert "traceback_marker" in markers
    assert "runtime_events_marker" in markers
    assert "env_file_marker" in markers
    assert "dependency_or_cache_path_marker" in markers
