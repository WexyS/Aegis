from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from aegis.core.config import load_settings
from aegis.core.model_hub import MODEL_HUB_EXECUTION_PERMISSION
from aegis.main import app


API_STATUS = "/model-hub/status"
MODEL_HUB_FALSE_INVARIANTS = (
    "runtime_dispatch_allowed",
    "authority",
    "provider_probe_performed",
    "http_request_performed",
    "model_call_performed",
    "generation_performed",
    "prompt_payload_sent",
    "context_payload_sent",
    "memory_write_performed",
    "tool_call_performed",
    "mcp_call_performed",
    "plugin_execution_performed",
    "agent_execution_performed",
    "workflow_execution_performed",
    "computer_control_performed",
    "shell_command_performed",
    "file_mutation_performed",
    "external_api_called",
    "cloud_routing_allowed",
    "data_sent_external",
    "config_mutation_allowed",
    "env_file_written",
    "evidence_created",
    "evidence_provided_by_model_hub",
    "verifier_success",
    "approval_grant",
    "approval_granted",
    "capability_grant",
    "capability_lease_granted",
    "lease_grant",
    "mutation_performed",
    "frontend_authority",
)


def _assert_model_hub_false_invariants(data: dict[str, object]) -> None:
    for field in MODEL_HUB_FALSE_INVARIANTS:
        assert data[field] is False, field


@pytest.fixture(autouse=True)
def clear_model_hub_env(monkeypatch: pytest.MonkeyPatch):
    for name in (
        "AEGIS_MODEL_GATEWAY_ENABLED",
        "AEGIS_MODEL_PROVIDER",
        "AEGIS_LM_STUDIO_BASE_URL",
        "AEGIS_LM_STUDIO_MODEL",
        "AEGIS_MODEL_TIMEOUT_SECONDS",
        "AEGIS_MODEL_MAX_INPUT_CHARS",
        "AEGIS_MODEL_MAX_OUTPUT_TOKENS",
        "AEGIS_OPENROUTER_API_KEY",
        "AEGIS_DEEPSEEK_API_KEY",
        "AEGIS_OPENAI_API_KEY",
        "AEGIS_ANTHROPIC_API_KEY",
        "AEGIS_GEMINI_API_KEY",
        "AEGIS_MOONSHOT_API_KEY",
        "AEGIS_MOONSHOT_MODEL",
        "AEGIS_MOONSHOT_BASE_URL",
    ):
        monkeypatch.delenv(name, raising=False)
    load_settings(force_reload=True)
    yield
    load_settings(force_reload=True)


@pytest.mark.asyncio
async def test_model_hub_status_is_config_only_when_gateway_disabled() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(API_STATUS)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "disabled"
    assert data["execution_permission"] == MODEL_HUB_EXECUTION_PERMISSION
    _assert_model_hub_false_invariants(data)
    assert data["lm_studio"]["provider"] == "lm_studio"
    assert data["lm_studio"]["probe_required_for_live_health"] is True
    assert data["lm_studio"]["local_only_boundary"] is True
    assert data["lm_studio"]["openai_compatible_local_endpoint"] is True
    assert data["recommended_default_profile_id"] == "default_proposal"
    assert data["resource_guardrails"]["vram_gb_target"] == 12
    assert data["resource_guardrails"]["system_ram_gb_target"] == 32
    assert data["active_model_profile_match"]["status"] == "no_configured_model"
    assert data["cloud_fallback_policy"]["automatic_cloud_fallback_allowed"] is False
    assert data["cloud_fallback_policy"]["cloud_calls_enabled_now"] is False
    assert data["cloud_fallback_policy"]["external_provider_broker_required"] is True
    assert data["external_provider_broker_boundary"]["status"] == "designed_disabled"
    assert data["external_provider_broker_boundary"]["external_api_called"] is False
    assert data["external_provider_broker_boundary"]["provider_key_value_exposed"] is False
    assert data["external_provider_broker_boundary"]["ui_key_input_allowed"] is False
    assert data["external_provider_broker_boundary"]["ui_env_write_allowed"] is False
    assert data["external_provider_broker_boundary"]["provider_setup_guidance"]
    assert data["local_model_profiles"]
    vision_profile = next(
        record for record in data["local_model_profiles"]
        if record["profile_id"] == "vision_review"
    )
    assert vision_profile["preferred_model_id_hint"] == "qwen/qwen3-vl-8b"
    assert "Qwen 3 VL 8B" in vision_profile["purpose"]
    assert "automatic_image_upload_disabled" in vision_profile["warnings"]
    assert "automatic_model_call_disabled" in vision_profile["warnings"]
    assert vision_profile["default_profile"] is False
    assert vision_profile["cloud_fallback_allowed"] is False
    assert vision_profile["authority"] is False
    assert vision_profile["evidence"] is False
    assert vision_profile["verifier_success"] is False
    assert vision_profile["approval_granted"] is False
    assert vision_profile["capability_lease_granted"] is False
    assert data["external_provider_readiness"]
    assert all(record["cloud_completion_enabled"] is False for record in data["external_provider_readiness"])
    assert all(record["api_key_value_exposed"] is False for record in data["external_provider_readiness"])
    kimi = next(
        record for record in data["external_provider_readiness"]
        if record["provider_id"] == "moonshot_kimi"
    )
    assert kimi["label"] == "Moonshot / Kimi"
    assert "AEGIS_MOONSHOT_API_KEY" in kimi["expected_env_vars"]
    assert "AEGIS_MOONSHOT_MODEL" in kimi["expected_env_vars"]
    assert "kimi-k2.7-code" in kimi["suggested_models"]
    assert kimi["cloud_completion_enabled"] is False
    assert kimi["automatic_fallback_allowed"] is False


@pytest.mark.asyncio
async def test_model_hub_status_reports_configured_metadata_without_probe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AEGIS_MODEL_GATEWAY_ENABLED", "true")
    monkeypatch.setenv("AEGIS_MODEL_PROVIDER", "lm_studio")
    monkeypatch.setenv("AEGIS_LM_STUDIO_BASE_URL", "http://127.0.0.1:1234/v1")
    monkeypatch.setenv("AEGIS_LM_STUDIO_MODEL", "qwen-local")
    load_settings(force_reload=True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(API_STATUS)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "configured_metadata_only"
    assert data["model_gateway"]["status"] == "configured"
    assert data["lm_studio"]["model"] == "qwen-local"
    assert data["lm_studio"]["model_configured"] is True
    assert data["active_model_profile_match"]["status"] == "unknown_configured_model"
    assert data["active_model_profile_match"]["automatic_model_switch_performed"] is False
    assert data["active_model_profile_match"]["live_installation_claimed"] is False
    assert data["model_hub_integrations"]
    assert any(record["integration_id"] == "lm_studio" for record in data["model_hub_integrations"])
    assert all("upstream_url" not in record for record in data["model_hub_integrations"])
    assert any(
        record["integration_id"] == "openrouter" and record["default_execution_status"] == "blocked"
        for record in data["model_hub_integrations"]
    )
    assert any(
        record["integration_id"] == "deepseek" and record["default_execution_status"] == "blocked"
        for record in data["model_hub_integrations"]
    )
    assert data["mode_policy_summary"]["execution_allowed_now"] is False
    assert all(
        mode["mode_allows_execution_now"] is False
        for mode in data["mode_policy_summary"]["modes"]
    )
    assert data["orchestrator_readiness"]["provider_probe_performed"] is False
    _assert_model_hub_false_invariants(data)


@pytest.mark.asyncio
async def test_model_hub_status_matches_known_configured_profile_without_probe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AEGIS_MODEL_GATEWAY_ENABLED", "true")
    monkeypatch.setenv("AEGIS_LM_STUDIO_MODEL", "google/gemma-4-12b")
    load_settings(force_reload=True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(API_STATUS)

    assert response.status_code == 200
    data = response.json()
    assert data["active_model_profile_match"]["matched_profile_id"] == "default_proposal"
    assert data["active_model_profile_match"]["completion_safe"] is True
    assert data["provider_probe_performed"] is False
    assert data["http_request_performed"] is False
    assert data["model_call_performed"] is False
    _assert_model_hub_false_invariants(data)


@pytest.mark.asyncio
async def test_model_hub_status_warns_when_configured_model_is_reranker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AEGIS_MODEL_GATEWAY_ENABLED", "true")
    monkeypatch.setenv("AEGIS_LM_STUDIO_MODEL", "qwen.qwen3-reranker-0.6b")
    load_settings(force_reload=True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(API_STATUS)

    assert response.status_code == 200
    data = response.json()
    match = data["active_model_profile_match"]
    assert match["matched_profile_id"] == "rerank_only"
    assert match["completion_safe"] is False
    assert "configured_model_appears_rerank_only_not_completion_safe" in match["warnings"]
    _assert_model_hub_false_invariants(data)


@pytest.mark.asyncio
async def test_model_hub_status_reports_provider_key_presence_without_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = "sk-do-not-return-this"
    monkeypatch.setenv("AEGIS_OPENROUTER_API_KEY", secret)
    load_settings(force_reload=True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(API_STATUS)

    assert response.status_code == 200
    data = response.json()
    openrouter = next(
        record for record in data["external_provider_readiness"]
        if record["provider_id"] == "openrouter"
    )
    assert openrouter["status"] == "key_present_calls_disabled"
    assert openrouter["api_key_present"] is True
    assert openrouter["api_key_value_exposed"] is False
    assert openrouter["cloud_completion_enabled"] is False
    assert openrouter["automatic_fallback_allowed"] is False
    assert secret not in repr(data)
    broker_guidance = next(
        record for record in data["external_provider_broker_boundary"]["provider_setup_guidance"]
        if record["provider_id"] == "openrouter"
    )
    assert broker_guidance["api_key_present"] is True
    assert broker_guidance["api_key_value_exposed"] is False
    assert broker_guidance["cloud_call_enabled"] is False
    assert secret not in repr(data["external_provider_broker_boundary"])
    assert data["external_api_called"] is False
    assert data["data_sent_external"] is False
    _assert_model_hub_false_invariants(data)


@pytest.mark.asyncio
async def test_model_hub_status_includes_kimi_readiness_without_cloud_enablement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = "moonshot-secret-must-not-return"
    monkeypatch.setenv("AEGIS_MOONSHOT_API_KEY", secret)
    monkeypatch.setenv("AEGIS_MOONSHOT_MODEL", "kimi-k2.7-code")
    load_settings(force_reload=True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(API_STATUS)

    assert response.status_code == 200
    data = response.json()
    kimi = next(
        record for record in data["external_provider_readiness"]
        if record["provider_id"] == "moonshot_kimi"
    )
    assert kimi["label"] == "Moonshot / Kimi"
    assert kimi["status"] == "key_present_calls_disabled"
    assert kimi["api_key_present"] is True
    assert kimi["api_key_value_exposed"] is False
    assert kimi["cloud_completion_enabled"] is False
    assert kimi["automatic_fallback_allowed"] is False
    assert kimi["manual_operator_opt_in_required"] is True
    assert "kimi-k2.7-code" in kimi["suggested_models"]
    assert secret not in repr(data)
    broker_guidance = next(
        record for record in data["external_provider_broker_boundary"]["provider_setup_guidance"]
        if record["provider_id"] == "moonshot_kimi"
    )
    assert broker_guidance["api_key_present"] is True
    assert broker_guidance["api_key_value_exposed"] is False
    assert broker_guidance["cloud_call_enabled"] is False
    assert broker_guidance["automatic_fallback_allowed"] is False
    assert "kimi-k2.7-code" in broker_guidance["model_placeholder"]
    assert data["cloud_fallback_policy"]["automatic_cloud_fallback_allowed"] is False
    assert data["external_api_called"] is False
    assert data["cloud_routing_allowed"] is False
    assert data["data_sent_external"] is False
    _assert_model_hub_false_invariants(data)
