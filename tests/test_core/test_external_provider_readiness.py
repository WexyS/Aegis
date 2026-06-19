from __future__ import annotations

from aegis.core.external_provider_readiness import (
    EXTERNAL_PROVIDER_EXECUTION_PERMISSION,
    build_cloud_fallback_policy,
    expected_provider_env_placeholders,
    list_external_provider_readiness,
)


def _records_by_id(env: dict[str, str] | None = None) -> dict[str, dict[str, object]]:
    return {record["provider_id"]: record for record in list_external_provider_readiness(env or {})}


def test_provider_readiness_records_exist() -> None:
    records = _records_by_id()

    assert set(records) == {
        "openrouter",
        "deepseek",
        "openai",
        "anthropic",
        "gemini",
        "moonshot_kimi",
    }
    assert records["openrouter"]["expected_env_vars"] == (
        "AEGIS_OPENROUTER_API_KEY",
        "AEGIS_OPENROUTER_MODEL",
    )
    assert records["deepseek"]["expected_env_vars"] == (
        "AEGIS_DEEPSEEK_API_KEY",
        "AEGIS_DEEPSEEK_MODEL",
    )
    assert records["openai"]["expected_env_vars"] == ("AEGIS_OPENAI_API_KEY", "AEGIS_OPENAI_MODEL")
    assert records["anthropic"]["expected_env_vars"] == (
        "AEGIS_ANTHROPIC_API_KEY",
        "AEGIS_ANTHROPIC_MODEL",
    )
    assert records["gemini"]["expected_env_vars"] == ("AEGIS_GEMINI_API_KEY", "AEGIS_GEMINI_MODEL")
    assert records["moonshot_kimi"]["expected_env_vars"] == (
        "AEGIS_MOONSHOT_API_KEY",
        "AEGIS_MOONSHOT_MODEL",
        "AEGIS_MOONSHOT_BASE_URL",
    )


def test_absent_key_is_missing_key_disabled() -> None:
    for record in list_external_provider_readiness({}):
        assert record["status"] == "missing_key_disabled"
        assert record["api_key_present"] is False
        assert record["api_key_value_exposed"] is False


def test_present_key_is_boolean_only_and_calls_remain_disabled() -> None:
    secret = "sk-this-must-not-appear"
    records = _records_by_id({"AEGIS_OPENROUTER_API_KEY": secret})
    openrouter = records["openrouter"]

    assert openrouter["status"] == "key_present_calls_disabled"
    assert openrouter["api_key_present"] is True
    assert openrouter["api_key_value_exposed"] is False
    assert secret not in repr(openrouter)
    assert openrouter["cloud_completion_enabled"] is False
    assert openrouter["automatic_fallback_allowed"] is False
    assert openrouter["manual_operator_opt_in_required"] is True
    assert openrouter["prompt_preview_required"] is True
    assert openrouter["cost_warning_required"] is True
    assert openrouter["privacy_warning_required"] is True


def test_provider_records_never_allow_sensitive_prompt_material_or_authority() -> None:
    for record in list_external_provider_readiness({"AEGIS_OPENAI_API_KEY": "present"}):
        assert record["secrets_allowed_in_prompt"] is False
        assert record["raw_logs_allowed_in_prompt"] is False
        assert record["raw_journals_allowed_in_prompt"] is False
        assert record["raw_evidence_allowed_in_prompt"] is False
        assert record["repo_dump_allowed_in_prompt"] is False
        assert record["output_authority"] is False
        assert record["output_is_evidence"] is False
        assert record["output_is_verifier_success"] is False
        assert record["authority"] is False
        assert record["evidence_created"] is False
        assert record["verifier_success"] is False
        assert record["approval_granted"] is False
        assert record["permission_granted"] is False
        assert record["lease_grant"] is False
        assert record["capability_lease_granted"] is False
        assert record["memory_write_allowed"] is False
        assert record["tool_execution_allowed"] is False
        assert record["model_call_allowed"] is False
        assert record["external_api_call_allowed"] is False
        assert record["data_sent_external"] is False
        assert record["execution_permission"] == EXTERNAL_PROVIDER_EXECUTION_PERMISSION


def test_cloud_fallback_policy_blocks_current_routing() -> None:
    policy = build_cloud_fallback_policy()

    assert policy["automatic_cloud_fallback_allowed"] is False
    assert policy["cloud_calls_enabled_now"] is False
    assert policy["external_provider_broker_required"] is True
    assert policy["operator_opt_in_required"] is True
    assert policy["prompt_preview_required"] is True
    assert policy["cost_warning_required"] is True
    assert policy["privacy_warning_required"] is True
    assert policy["secrets_redaction_required"] is True
    assert policy["proposal_only_output_required"] is True
    assert policy["provider_key_presence_is_authorization"] is False
    assert policy["local_failure_triggers_cloud"] is False
    assert policy["provider_routing_added"] is False


def test_env_placeholders_are_placeholders_only() -> None:
    placeholders = expected_provider_env_placeholders()

    assert {item["provider_id"] for item in placeholders} == {
        "openrouter",
        "deepseek",
        "openai",
        "anthropic",
        "gemini",
        "moonshot_kimi",
    }
    for item in placeholders:
        assert "<paste-key-in-your-own-shell>" in item["api_key_placeholder"]
        assert "<future-model-id>" in item["model_placeholder"] or "kimi-k2.7-code" in item["model_placeholder"]
        assert "sk-" not in item["api_key_placeholder"]


def test_moonshot_kimi_is_metadata_only_and_proposal_only() -> None:
    secret = "moonshot-secret-must-not-leak"
    records = _records_by_id(
        {
            "AEGIS_MOONSHOT_API_KEY": secret,
            "AEGIS_MOONSHOT_MODEL": "kimi-k2.7-code",
            "AEGIS_MOONSHOT_BASE_URL": "https://api.moonshot.ai/v1",
        }
    )
    kimi = records["moonshot_kimi"]

    assert "Moonshot" in str(kimi["label"]) or "Kimi" in str(kimi["label"])
    assert kimi["provider_family"] == "external_cloud_provider"
    assert kimi["status"] == "key_present_calls_disabled"
    assert "AEGIS_MOONSHOT_API_KEY" in kimi["expected_env_vars"]
    assert "AEGIS_MOONSHOT_MODEL" in kimi["expected_env_vars"]
    assert kimi["default_base_url_guidance"] == "https://api.moonshot.ai/v1"
    assert "kimi-k2.7-code" in kimi["suggested_models"]
    assert "kimi-k2.7-code-highspeed" in kimi["suggested_models"]
    assert kimi["api_key_present"] is True
    assert kimi["api_key_value_exposed"] is False
    assert secret not in repr(kimi)
    assert kimi["cloud_completion_enabled"] is False
    assert kimi["automatic_fallback_allowed"] is False
    assert kimi["manual_operator_opt_in_required"] is True
    assert kimi["cost_warning_required"] is True
    assert kimi["privacy_warning_required"] is True
    assert kimi["prompt_preview_required"] is True
    assert kimi["output_authority"] is False
    assert kimi["output_is_evidence"] is False
    assert kimi["output_is_verifier_success"] is False
    assert kimi["authority"] is False
    assert kimi["approval_granted"] is False
    assert kimi["permission_granted"] is False
    assert kimi["lease_grant"] is False
    assert kimi["capability_lease_granted"] is False
    assert kimi["memory_write_allowed"] is False
    assert kimi["tool_execution_allowed"] is False
    assert kimi["model_call_allowed"] is False
    assert kimi["external_api_call_allowed"] is False
    assert kimi["data_sent_external"] is False
