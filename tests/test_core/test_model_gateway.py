from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from aegis.core.config import load_settings
from aegis.core.model_gateway import (
    MODEL_GATEWAY_EXECUTION_PERMISSION,
    MODEL_GATEWAY_RC1_VERSION,
    ModelGatewayConfig,
    ModelGatewayHttpRequest,
    ModelGatewayHttpResponse,
    build_model_gateway_status,
    complete_model_gateway,
    probe_model_gateway,
    validate_model_gateway_base_url,
)


class FakeTransport:
    def __init__(self, response: ModelGatewayHttpResponse | None = None, exc: Exception | None = None) -> None:
        self.response = response or ModelGatewayHttpResponse(
            status_code=200,
            json_data={"object": "list", "data": [{"id": "qwen-local"}]},
        )
        self.exc = exc
        self.calls: list[ModelGatewayHttpRequest] = []

    async def __call__(self, request: ModelGatewayHttpRequest) -> ModelGatewayHttpResponse:
        self.calls.append(request)
        if self.exc is not None:
            raise self.exc
        return self.response


def _config(**overrides: object) -> ModelGatewayConfig:
    values: dict[str, object] = {
        "enabled": True,
        "provider": "lm_studio",
        "base_url": "http://127.0.0.1:1234/v1",
        "model": "qwen-local",
        "timeout_seconds": 2.0,
        "max_input_chars": 4000,
        "max_output_tokens": 256,
    }
    values.update(overrides)
    return ModelGatewayConfig(**values)  # type: ignore[arg-type]


def _completion_response(text: str = "Proposal text") -> ModelGatewayHttpResponse:
    return ModelGatewayHttpResponse(
        status_code=200,
        json_data={
            "choices": [{"message": {"content": text}}],
            "usage": {"prompt_tokens": 7, "completion_tokens": 3, "total_tokens": 10},
        },
    )


def _assert_non_authority(data: dict[str, object]) -> None:
    assert data["authority"] is False
    assert data["runtime_dispatch_allowed"] is False
    assert data["execution_permission"] == MODEL_GATEWAY_EXECUTION_PERMISSION
    assert data["evidence"] is False
    assert data["evidence_provided_by_model"] is False
    assert data["verifier_success"] is False
    assert data["approval_granted"] is False
    assert data["approval_grant"] is False
    assert data["permission_granted"] is False
    assert data["capability_lease_granted"] is False
    assert data["capability_grant"] is False
    assert data["lease_grant"] is False
    assert data["memory_output_is_authority"] is False
    assert data["model_output_is_truth"] is False
    assert data["model_output_is_evidence"] is False
    assert data["model_output_is_verifier_success"] is False
    assert data["requires_backend_validation"] is True
    assert data["requires_policy_check"] is True


def _assert_no_side_effects(data: dict[str, object]) -> None:
    assert data["memory_write_performed"] is False
    assert data["tool_call_performed"] is False
    assert data["mcp_call_performed"] is False
    assert data["shell_command_performed"] is False
    assert data["file_mutation_performed"] is False
    assert data["data_sent_external"] is False
    assert data.get("transcript_persisted", False) is False
    assert data.get("journal_mutated", False) is False
    assert data.get("evidence_mutated", False) is False
    assert data.get("runtime_state_mutated", False) is False


def test_default_gateway_disabled_status(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "AEGIS_MODEL_GATEWAY_ENABLED",
        "AEGIS_MODEL_PROVIDER",
        "AEGIS_LM_STUDIO_BASE_URL",
        "AEGIS_LM_STUDIO_MODEL",
    ):
        monkeypatch.delenv(name, raising=False)
    load_settings(force_reload=True)

    status = build_model_gateway_status()

    assert status["model_gateway_version"] == MODEL_GATEWAY_RC1_VERSION
    assert status["status"] == "disabled"
    assert status["enabled"] is False
    assert "gateway_disabled" in status["failure_reasons"]
    assert status["http_request_performed"] is False
    _assert_non_authority(status)
    _assert_no_side_effects(status)


@pytest.mark.parametrize(
    "base_url",
    [
        "http://127.0.0.1:1234/v1",
        "http://localhost:1234/v1",
        "http://[::1]:1234/v1",
        "http://127.0.0.1:1234",
    ],
)
def test_valid_local_lm_studio_urls_are_accepted(base_url: str) -> None:
    result = validate_model_gateway_base_url(base_url)

    assert result.ok is True
    assert result.reasons == ()
    assert result.models_url.endswith("/v1/models")
    assert result.chat_completions_url.endswith("/v1/chat/completions")


@pytest.mark.parametrize(
    ("base_url", "reason"),
    [
        ("http://example.com:1234/v1", "non_local_host_blocked"),
        ("http://192.168.1.10:1234/v1", "non_local_host_blocked"),
        ("file:///tmp/model", "unsupported_url_scheme"),
        ("ws://127.0.0.1:1234/v1", "unsupported_url_scheme"),
        ("http://localhost.evil.test:1234/v1", "spoofed_localhost_blocked"),
        ("http://127.0.0.1.evil.test:1234/v1", "spoofed_localhost_blocked"),
        ("http://127.0.0.1:1234/other", "unsupported_base_path"),
        ("http://user:pass@127.0.0.1:1234/v1", "credentials_in_url_denied"),
        ("http://127.0.0.1:1234/v1?token=secret", "query_or_fragment_denied"),
        ("http://127.0.0.1:1234/v1#fragment", "query_or_fragment_denied"),
    ],
)
def test_remote_and_malformed_urls_are_rejected(base_url: str, reason: str) -> None:
    result = validate_model_gateway_base_url(base_url)

    assert result.ok is False
    assert reason in result.reasons


@pytest.mark.asyncio
async def test_provider_unavailable_is_structured_without_crash() -> None:
    transport = FakeTransport(exc=ConnectionRefusedError())

    status = await probe_model_gateway(_config(), transport=transport)

    assert status["status"] == "unavailable"
    assert "provider_unavailable" in status["failure_reasons"]
    assert status["provider_probe_performed"] is True
    assert status["http_request_performed"] is True
    _assert_non_authority(status)
    _assert_no_side_effects(status)


@pytest.mark.asyncio
async def test_probe_ready_with_fake_models_response() -> None:
    transport = FakeTransport()

    status = await probe_model_gateway(_config(), transport=transport)

    assert status["status"] == "ready"
    assert status["health_result"]["model_count_candidate"] == 1
    assert status["health_result"]["response_shape"] == "openai_models_list_candidate"
    assert transport.calls == [
        ModelGatewayHttpRequest(
            method="GET",
            url="http://127.0.0.1:1234/v1/models",
            timeout_seconds=2.0,
            headers={},
        )
    ]
    _assert_non_authority(status)


@pytest.mark.asyncio
async def test_probe_malformed_models_response_fails_closed() -> None:
    transport = FakeTransport(response=ModelGatewayHttpResponse(status_code=200, json_data=[]))

    status = await probe_model_gateway(_config(), transport=transport)

    assert status["status"] == "error"
    assert status["failure_reasons"] == ("invalid_json_shape",)
    assert status["provider_probe_performed"] is True
    assert status["http_request_performed"] is True
    _assert_non_authority(status)
    _assert_no_side_effects(status)


@pytest.mark.asyncio
async def test_completion_success_with_mocked_response() -> None:
    transport = FakeTransport(response=_completion_response("A bounded proposal."))

    result = await complete_model_gateway(
        {
            "request_id": "model-gateway:test:1",
            "purpose": "explanation",
            "prompt": "Explain the RC boundary.",
            "max_output_tokens": 64,
            "temperature": 0.2,
        },
        _config(),
        transport=transport,
    )

    assert result["status"] == "completed"
    assert result["output_text"] == "A bounded proposal."
    assert result["usage"]["total_tokens"] == 10
    assert result["model_call_performed"] is True
    assert result["generation_performed"] is True
    assert result["prompt_payload_sent"] is True
    assert transport.calls[0].method == "POST"
    assert transport.calls[0].url == "http://127.0.0.1:1234/v1/chat/completions"
    body = transport.calls[0].json_body
    assert body is not None
    assert body["model"] == "qwen-local"
    assert body["stream"] is False
    assert body["messages"][0]["role"] == "system"
    assert "proposal" in body["messages"][0]["content"].lower()
    _assert_non_authority(result)
    _assert_no_side_effects(result)


@pytest.mark.asyncio
async def test_completion_malformed_response_fails_closed() -> None:
    transport = FakeTransport(response=ModelGatewayHttpResponse(status_code=200, json_data={"choices": []}))

    result = await complete_model_gateway(
        {"purpose": "explanation", "prompt": "Explain Aegis."},
        _config(),
        transport=transport,
    )

    assert result["status"] == "error"
    assert result["failure_reasons"] == ("empty_model_output",)
    assert result["raw_error"] == "empty_model_output"
    assert result["model_call_performed"] is False
    _assert_non_authority(result)
    _assert_no_side_effects(result)


@pytest.mark.asyncio
async def test_completion_blocked_when_gateway_disabled() -> None:
    transport = FakeTransport(response=_completion_response())

    result = await complete_model_gateway(
        {"purpose": "explanation", "prompt": "Hello"},
        _config(enabled=False),
        transport=transport,
    )

    assert result["status"] == "disabled"
    assert "gateway_disabled" in result["failure_reasons"]
    assert result["model_call_performed"] is False
    assert transport.calls == []
    _assert_non_authority(result)
    _assert_no_side_effects(result)


@pytest.mark.asyncio
async def test_completion_blocked_when_model_missing() -> None:
    transport = FakeTransport(response=_completion_response())

    result = await complete_model_gateway(
        {"purpose": "explanation", "prompt": "Hello"},
        _config(model="not_configured"),
        transport=transport,
    )

    assert result["status"] == "misconfigured"
    assert "missing_model" in result["failure_reasons"]
    assert transport.calls == []
    _assert_non_authority(result)


@pytest.mark.asyncio
async def test_timeout_error_produces_structured_response() -> None:
    transport = FakeTransport(exc=TimeoutError())

    result = await complete_model_gateway(
        {"purpose": "summarization", "prompt": "Summarize this."},
        _config(),
        transport=transport,
    )

    assert result["status"] == "timeout"
    assert result["raw_error"] == "provider_timeout"
    assert result["model_call_performed"] is False
    _assert_non_authority(result)
    _assert_no_side_effects(result)


@pytest.mark.asyncio
async def test_completion_rejects_oversized_input_before_transport() -> None:
    transport = FakeTransport(response=_completion_response())

    result = await complete_model_gateway(
        {"purpose": "explanation", "prompt": "x" * 6},
        _config(max_input_chars=5),
        transport=transport,
    )

    assert result["status"] == "blocked"
    assert "input_too_large" in result["failure_reasons"]
    assert transport.calls == []
    _assert_no_side_effects(result)


def test_config_dataclass_is_immutable() -> None:
    config = _config()

    with pytest.raises(FrozenInstanceError):
        config.model = "mutated"  # type: ignore[misc]
