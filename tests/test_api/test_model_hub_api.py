from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from aegis.core.config import load_settings
from aegis.core.model_hub import MODEL_HUB_EXECUTION_PERMISSION
from aegis.main import app


API_STATUS = "/model-hub/status"


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
    assert data["runtime_dispatch_allowed"] is False
    assert data["authority"] is False
    assert data["lm_studio"]["provider"] == "lm_studio"
    assert data["lm_studio"]["probe_required_for_live_health"] is True
    assert data["lm_studio"]["local_only_boundary"] is True
    assert data["lm_studio"]["openai_compatible_local_endpoint"] is True
    assert data["provider_probe_performed"] is False
    assert data["http_request_performed"] is False
    assert data["model_call_performed"] is False
    assert data["generation_performed"] is False
    assert data["prompt_payload_sent"] is False
    assert data["memory_write_performed"] is False
    assert data["tool_call_performed"] is False
    assert data["agent_execution_performed"] is False
    assert data["workflow_execution_performed"] is False
    assert data["computer_control_performed"] is False
    assert data["external_api_called"] is False
    assert data["data_sent_external"] is False
    assert data["config_mutation_allowed"] is False


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
    assert data["provider_probe_performed"] is False
    assert data["http_request_performed"] is False
    assert data["model_call_performed"] is False
