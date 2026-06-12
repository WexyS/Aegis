from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from aegis.api.routes_model_gateway import set_model_gateway_transport_for_tests
from aegis.core.config import load_settings
from aegis.core.model_gateway import (
    MODEL_GATEWAY_EXECUTION_PERMISSION,
    ModelGatewayHttpRequest,
    ModelGatewayHttpResponse,
)
from aegis.main import app


API_STATUS = "/model-gateway/status"
API_PROBE = "/model-gateway/probe"
API_COMPLETE = "/model-gateway/complete"


class FakeTransport:
    def __init__(self, response: ModelGatewayHttpResponse | None = None, exc: Exception | None = None) -> None:
        self.response = response or ModelGatewayHttpResponse(
            status_code=200,
            json_data={"object": "list", "data": [{"id": "api-model"}]},
        )
        self.exc = exc
        self.calls: list[ModelGatewayHttpRequest] = []

    async def __call__(self, request: ModelGatewayHttpRequest) -> ModelGatewayHttpResponse:
        self.calls.append(request)
        if self.exc is not None:
            raise self.exc
        return self.response


@pytest.fixture(autouse=True)
def clear_model_gateway_env(monkeypatch: pytest.MonkeyPatch):
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
    set_model_gateway_transport_for_tests(None)
    load_settings(force_reload=True)
    yield
    set_model_gateway_transport_for_tests(None)
    load_settings(force_reload=True)


def _enable_gateway(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AEGIS_MODEL_GATEWAY_ENABLED", "true")
    monkeypatch.setenv("AEGIS_MODEL_PROVIDER", "lm_studio")
    monkeypatch.setenv("AEGIS_LM_STUDIO_BASE_URL", "http://127.0.0.1:1234/v1")
    monkeypatch.setenv("AEGIS_LM_STUDIO_MODEL", "api-model")
    monkeypatch.setenv("AEGIS_MODEL_TIMEOUT_SECONDS", "2")
    monkeypatch.setenv("AEGIS_MODEL_MAX_INPUT_CHARS", "4000")
    monkeypatch.setenv("AEGIS_MODEL_MAX_OUTPUT_TOKENS", "256")
    load_settings(force_reload=True)


def _assert_non_authority(data: dict[str, object]) -> None:
    assert data["authority"] is False
    assert data["runtime_dispatch_allowed"] is False
    assert data["execution_permission"] == MODEL_GATEWAY_EXECUTION_PERMISSION
    assert data["evidence"] is False
    assert data["evidence_provided_by_model"] is False
    assert data["verifier_success"] is False
    assert data["approval_granted"] is False
    assert data["permission_granted"] is False
    assert data["capability_lease_granted"] is False
    assert data["memory_write_performed"] is False
    assert data["tool_call_performed"] is False
    assert data["mcp_call_performed"] is False
    assert data["shell_command_performed"] is False
    assert data["file_mutation_performed"] is False
    assert data["data_sent_external"] is False


@pytest.mark.asyncio
async def test_status_endpoint_works_when_gateway_disabled() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(API_STATUS)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "disabled"
    assert data["enabled"] is False
    assert data["http_request_performed"] is False
    assert data["model_call_performed"] is False
    _assert_non_authority(data)


@pytest.mark.asyncio
async def test_probe_endpoint_uses_mocked_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_gateway(monkeypatch)
    fake = FakeTransport()
    set_model_gateway_transport_for_tests(fake)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(API_PROBE)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["health_result"]["model_count_candidate"] == 1
    assert len(fake.calls) == 1
    assert fake.calls[0].method == "GET"
    assert fake.calls[0].url == "http://127.0.0.1:1234/v1/models"
    _assert_non_authority(data)


@pytest.mark.asyncio
async def test_complete_endpoint_returns_structured_mocked_response(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_gateway(monkeypatch)
    fake = FakeTransport(
        ModelGatewayHttpResponse(
            status_code=200,
            json_data={
                "choices": [{"message": {"content": "API proposal"}}],
                "usage": {"total_tokens": 4},
            },
        )
    )
    set_model_gateway_transport_for_tests(fake)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            API_COMPLETE,
            json={"purpose": "explanation", "prompt": "Explain Aegis.", "max_output_tokens": 64},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["output_text"] == "API proposal"
    assert data["usage"]["total_tokens"] == 4
    assert data["model_call_performed"] is True
    assert data["generation_performed"] is True
    assert len(fake.calls) == 1
    assert fake.calls[0].method == "POST"
    assert fake.calls[0].json_body is not None
    assert fake.calls[0].json_body["model"] == "api-model"
    _assert_non_authority(data)


@pytest.mark.asyncio
async def test_complete_endpoint_blocks_when_disabled_without_transport_call() -> None:
    fake = FakeTransport()
    set_model_gateway_transport_for_tests(fake)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(API_COMPLETE, json={"purpose": "explanation", "prompt": "Hello"})

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "disabled"
    assert "gateway_disabled" in data["failure_reasons"]
    assert data["model_call_performed"] is False
    assert fake.calls == []
    _assert_non_authority(data)


@pytest.mark.asyncio
async def test_complete_endpoint_rejects_remote_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AEGIS_MODEL_GATEWAY_ENABLED", "true")
    monkeypatch.setenv("AEGIS_LM_STUDIO_BASE_URL", "http://example.com:1234/v1")
    monkeypatch.setenv("AEGIS_LM_STUDIO_MODEL", "api-model")
    load_settings(force_reload=True)
    fake = FakeTransport()
    set_model_gateway_transport_for_tests(fake)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(API_COMPLETE, json={"purpose": "explanation", "prompt": "Hello"})

    assert response.status_code == 200
    data = response.json()
    assert data["status"] in {"misconfigured", "blocked"}
    assert "non_local_host_blocked" in data["failure_reasons"]
    assert fake.calls == []
    _assert_non_authority(data)
