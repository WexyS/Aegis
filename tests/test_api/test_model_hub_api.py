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
    _assert_model_hub_false_invariants(data)
