from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from aegis.core.external_provider_broker_boundary import REQUIRED_OPERATOR_ACKNOWLEDGEMENTS
from aegis.core.config import load_settings
from aegis.main import app


API_PREVIEW = "/model-hub/external-provider-preview"


@pytest.fixture(autouse=True)
def clear_external_provider_env(monkeypatch: pytest.MonkeyPatch):
    for name in (
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
async def test_external_provider_preview_endpoint_is_dry_run_only() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            API_PREVIEW,
            json={
                "provider_id": "openrouter",
                "model_id": "future/model",
                "purpose": "explanation",
                "prompt": "Explain Model Hub status without calling any provider.",
                "operator_acknowledgements": list(REQUIRED_OPERATOR_ACKNOWLEDGEMENTS),
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "blocked_until_external_provider_broker_enabled"
    assert data["would_call_provider"] is False
    assert data["cloud_call_performed"] is False
    assert data["external_api_called"] is False


@pytest.mark.asyncio
async def test_external_provider_preview_endpoint_supports_kimi_as_blocked_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = "moonshot-secret-should-not-return"
    monkeypatch.setenv("AEGIS_MOONSHOT_API_KEY", secret)
    load_settings(force_reload=True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            API_PREVIEW,
            json={
                "provider_id": "moonshot_kimi",
                "model_id": "kimi-k2.7-code",
                "purpose": "coding_review",
                "prompt": "Summarize this small code-review plan as proposal-only metadata.",
                "operator_acknowledgements": list(REQUIRED_OPERATOR_ACKNOWLEDGEMENTS),
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "blocked_until_external_provider_broker_enabled"
    assert data["provider_id"] == "moonshot_kimi"
    assert data["provider_label"] == "Moonshot / Kimi"
    assert data["provider_status"] == "key_present_calls_disabled"
    assert data["model_id"] == "kimi-k2.7-code"
    assert secret not in repr(data)
    assert data["would_call_provider"] is False
    assert data["cloud_call_performed"] is False
    assert data["external_api_called"] is False
    assert data["http_request_performed"] is False
    assert data["model_call_performed"] is False
    assert data["prompt_payload_sent"] is False
    assert data["data_sent_external"] is False
    assert data["provider_key_value_exposed"] is False
    assert data["authority"] is False
    assert data["verifier_success"] is False
    assert data["approval_granted"] is False
    assert data["capability_lease_granted"] is False


@pytest.mark.asyncio
async def test_external_provider_preview_endpoint_never_returns_env_key_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = "sk-env-secret-should-not-return"
    monkeypatch.setenv("AEGIS_OPENAI_API_KEY", secret)
    load_settings(force_reload=True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            API_PREVIEW,
            json={
                "provider_id": "openai",
                "purpose": "explanation",
                "prompt": "Safe prompt preview only.",
                "operator_acknowledgements": list(REQUIRED_OPERATOR_ACKNOWLEDGEMENTS),
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["provider_status"] == "key_present_calls_disabled"
    assert data["provider_key_value_exposed"] is False
    assert secret not in repr(data)
    assert data["would_call_provider"] is False
    assert data["cloud_call_performed"] is False


@pytest.mark.asyncio
async def test_external_provider_preview_endpoint_redacts_prompt_secret_markers() -> None:
    secret = "sk-prompt-secret-should-not-return"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            API_PREVIEW,
            json={
                "provider_id": "anthropic",
                "purpose": "reasoning_review",
                "prompt": f"Authorization: Bearer private-token\napi_key={secret}",
                "operator_acknowledgements": list(REQUIRED_OPERATOR_ACKNOWLEDGEMENTS),
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "blocked_by_prompt_safety_preview"
    assert secret not in data["prompt_preview"]
    assert "private-token" not in data["prompt_preview"]
    assert "prompt_contains_sensitive_or_raw_diagnostic_markers" in data["blocked_reasons"]
    assert data["external_api_called"] is False
