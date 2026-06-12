from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Mapping, Protocol
from urllib.parse import urlparse, urlunparse
from uuid import uuid4

import httpx

from aegis.core.config import AegisSettings, get_settings


MODEL_GATEWAY_RC1_VERSION = "model-gateway-rc1-lm-studio/1"
MODEL_GATEWAY_EXECUTION_PERMISSION = "not_granted_by_model_gateway"
MODEL_GATEWAY_PROVIDER = "lm_studio"
ALLOWED_LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}
ALLOWED_PURPOSES = {
    "explanation",
    "summarization",
    "report_polish",
    "proposal_draft",
    "society_commentary",
    "autopilot_interpretation",
    "memory_candidate_refinement",
}
MISSING_MODEL_VALUES = {"", "not_configured", "none", "null", "missing", "unknown"}

BOUNDARY_SYSTEM_MESSAGE = (
    "You are Aegis Model Gateway RC1. You generate proposals and explanations only. "
    "Do not claim authority, approval, permission, evidence, verifier success, tool "
    "execution, file changes, shell execution, MCP execution, or memory writes."
)


@dataclass(frozen=True)
class ModelGatewayConfig:
    enabled: bool
    provider: str
    base_url: str
    model: str
    timeout_seconds: float
    max_input_chars: int
    max_output_tokens: int


@dataclass(frozen=True)
class ModelGatewayUrlValidation:
    ok: bool
    normalized_base_url: str
    models_url: str
    chat_completions_url: str
    host: str
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class ModelGatewayHttpRequest:
    method: str
    url: str
    timeout_seconds: float
    json_body: Mapping[str, Any] | None = None
    headers: Mapping[str, str] | None = None


@dataclass(frozen=True)
class ModelGatewayHttpResponse:
    status_code: int
    json_data: Any


class ModelGatewayTransport(Protocol):
    async def __call__(self, request: ModelGatewayHttpRequest) -> ModelGatewayHttpResponse:
        ...


def get_model_gateway_config(settings: AegisSettings | None = None) -> ModelGatewayConfig:
    source = (settings or get_settings()).model_gateway
    return ModelGatewayConfig(
        enabled=bool(source.enabled),
        provider=str(source.provider or MODEL_GATEWAY_PROVIDER).strip(),
        base_url=str(source.lm_studio_base_url or "http://127.0.0.1:1234/v1").strip(),
        model=str(source.lm_studio_model or "not_configured").strip(),
        timeout_seconds=float(source.timeout_seconds or 20.0),
        max_input_chars=int(source.max_input_chars or 8000),
        max_output_tokens=int(source.max_output_tokens or 512),
    )


def validate_model_gateway_base_url(base_url: str) -> ModelGatewayUrlValidation:
    reasons: list[str] = []
    parsed = urlparse(str(base_url or "").strip())
    if parsed.scheme not in {"http", "https"}:
        reasons.append("unsupported_url_scheme")
    if parsed.username or parsed.password:
        reasons.append("credentials_in_url_denied")
    if parsed.query or parsed.fragment:
        reasons.append("query_or_fragment_denied")

    host = (parsed.hostname or "").lower()
    if not host:
        reasons.append("missing_host")
    elif host not in ALLOWED_LOCAL_HOSTS:
        if host.endswith(".localhost") or "localhost" in host or host.startswith("127."):
            reasons.append("spoofed_localhost_blocked")
        else:
            reasons.append("non_local_host_blocked")

    path = (parsed.path or "").rstrip("/")
    if path in {"", "/"}:
        path = "/v1"
    elif path != "/v1":
        reasons.append("unsupported_base_path")

    normalized = ""
    models_url = ""
    chat_url = ""
    if parsed.scheme and parsed.netloc and path:
        netloc = parsed.netloc
        normalized = urlunparse((parsed.scheme, netloc, path, "", "", ""))
        models_url = f"{normalized}/models"
        chat_url = f"{normalized}/chat/completions"

    return ModelGatewayUrlValidation(
        ok=not reasons,
        normalized_base_url=normalized,
        models_url=models_url,
        chat_completions_url=chat_url,
        host=host,
        reasons=tuple(reasons),
    )


async def httpx_model_gateway_transport(request: ModelGatewayHttpRequest) -> ModelGatewayHttpResponse:
    async with httpx.AsyncClient(timeout=request.timeout_seconds, trust_env=False) as client:
        response = await client.request(
            request.method,
            request.url,
            json=request.json_body,
            headers=dict(request.headers or {}),
        )
    return ModelGatewayHttpResponse(status_code=response.status_code, json_data=response.json())


def build_model_gateway_status(config: ModelGatewayConfig | None = None) -> dict[str, Any]:
    gateway_config = config or get_model_gateway_config()
    url_validation = validate_model_gateway_base_url(gateway_config.base_url)
    failures = list(_config_failures(gateway_config, url_validation, require_model=False))
    status = "disabled"
    if gateway_config.enabled and failures:
        status = "misconfigured"
    elif gateway_config.enabled:
        status = "configured"
    return _base_payload(
        status=status,
        config=gateway_config,
        url_validation=url_validation,
        failure_reasons=tuple(failures),
        limitations=_common_limitations(),
        unknowns=("provider_health_not_probed_by_status_endpoint",),
    )


async def probe_model_gateway(
    config: ModelGatewayConfig | None = None,
    *,
    transport: ModelGatewayTransport | None = None,
) -> dict[str, Any]:
    gateway_config = config or get_model_gateway_config()
    url_validation = validate_model_gateway_base_url(gateway_config.base_url)
    failures = list(_config_failures(gateway_config, url_validation, require_model=False))
    if not gateway_config.enabled:
        return _base_payload(
            status="disabled",
            config=gateway_config,
            url_validation=url_validation,
            failure_reasons=tuple(failures),
            limitations=_common_limitations(),
            unknowns=("gateway_disabled_no_probe_performed",),
        )
    if failures:
        return _base_payload(
            status="misconfigured",
            config=gateway_config,
            url_validation=url_validation,
            failure_reasons=tuple(failures),
            limitations=_common_limitations(),
            unknowns=(),
        )

    started = time.time()
    try:
        response = await (transport or httpx_model_gateway_transport)(
            ModelGatewayHttpRequest(
                method="GET",
                url=url_validation.models_url,
                timeout_seconds=gateway_config.timeout_seconds,
                headers={},
            )
        )
    except TimeoutError:
        return _probe_error_payload("timeout", gateway_config, url_validation, "provider_probe_timeout", started)
    except (httpx.TimeoutException, httpx.ConnectTimeout, httpx.ReadTimeout):
        return _probe_error_payload("timeout", gateway_config, url_validation, "provider_probe_timeout", started)
    except (httpx.ConnectError, ConnectionRefusedError, OSError):
        return _probe_error_payload("unavailable", gateway_config, url_validation, "provider_unavailable", started)
    except Exception as exc:
        return _probe_error_payload("error", gateway_config, url_validation, _sanitize_error(exc), started)

    payload = _base_payload(
        status="ready",
        config=gateway_config,
        url_validation=url_validation,
        failure_reasons=(),
        limitations=_common_limitations(),
        unknowns=(),
    )
    payload["http_request_performed"] = True
    payload["provider_probe_performed"] = True
    payload["duration_ms"] = _duration_ms(started)
    payload["health_result"] = _probe_result(response)
    if response.status_code >= 400:
        payload["status"] = "error"
        payload["failure_reasons"] = (f"http_status_{response.status_code}",)
    elif not isinstance(response.json_data, Mapping):
        payload["status"] = "error"
        payload["failure_reasons"] = ("invalid_json_shape",)
    return payload


async def complete_model_gateway(
    request: Mapping[str, Any] | None,
    config: ModelGatewayConfig | None = None,
    *,
    transport: ModelGatewayTransport | None = None,
) -> dict[str, Any]:
    gateway_config = config or get_model_gateway_config()
    url_validation = validate_model_gateway_base_url(gateway_config.base_url)
    request_data = dict(request or {})
    started = time.time()
    request_id = str(request_data.get("request_id") or f"model_gateway_{uuid4().hex}")
    purpose = str(request_data.get("purpose") or "explanation").strip()
    requested_model = str(request_data.get("model") or "").strip()
    model = requested_model or gateway_config.model
    failures = list(_config_failures(gateway_config, url_validation, require_model=True))
    warnings: list[str] = []

    if purpose not in ALLOWED_PURPOSES:
        failures.append("unsupported_purpose")
    if _missing_model(model):
        failures.append("missing_model")
    prompt_text = _prompt_text(request_data)
    if not prompt_text:
        failures.append("missing_prompt")
    if len(prompt_text) > gateway_config.max_input_chars:
        failures.append("input_too_large")
    max_tokens = int(request_data.get("max_output_tokens") or gateway_config.max_output_tokens)
    if max_tokens < 1:
        failures.append("invalid_max_output_tokens")
    if max_tokens > gateway_config.max_output_tokens:
        failures.append("max_output_tokens_exceeds_configured_cap")
    temperature = float(request_data.get("temperature", 0.1))
    if temperature < 0.0 or temperature > 1.0:
        failures.append("temperature_out_of_range")

    if not gateway_config.enabled:
        status = "disabled"
    elif failures:
        status = "misconfigured" if any(reason in failures for reason in {"unsupported_provider", "missing_model", "unsupported_url_scheme", "non_local_host_blocked"}) else "blocked"
    else:
        status = "running"

    if status != "running":
        return _completion_payload(
            status=status,
            request_id=request_id,
            config=gateway_config,
            url_validation=url_validation,
            purpose=purpose,
            model=model,
            started=started,
            failure_reasons=tuple(dict.fromkeys(failures)),
            warnings=tuple(warnings),
            output_text="",
            usage={},
            raw_error=None,
        )

    messages = _chat_messages(request_data, purpose)
    body = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    try:
        response = await (transport or httpx_model_gateway_transport)(
            ModelGatewayHttpRequest(
                method="POST",
                url=url_validation.chat_completions_url,
                timeout_seconds=gateway_config.timeout_seconds,
                json_body=body,
                headers={"Content-Type": "application/json"},
            )
        )
    except TimeoutError:
        return _completion_payload(
            status="timeout",
            request_id=request_id,
            config=gateway_config,
            url_validation=url_validation,
            purpose=purpose,
            model=model,
            started=started,
            failure_reasons=("provider_timeout",),
            warnings=tuple(warnings),
            output_text="",
            usage={},
            raw_error="provider_timeout",
        )
    except (httpx.TimeoutException, httpx.ConnectTimeout, httpx.ReadTimeout):
        return _completion_payload(
            status="timeout",
            request_id=request_id,
            config=gateway_config,
            url_validation=url_validation,
            purpose=purpose,
            model=model,
            started=started,
            failure_reasons=("provider_timeout",),
            warnings=tuple(warnings),
            output_text="",
            usage={},
            raw_error="provider_timeout",
        )
    except (httpx.ConnectError, ConnectionRefusedError, OSError):
        return _completion_payload(
            status="unavailable",
            request_id=request_id,
            config=gateway_config,
            url_validation=url_validation,
            purpose=purpose,
            model=model,
            started=started,
            failure_reasons=("provider_unavailable",),
            warnings=tuple(warnings),
            output_text="",
            usage={},
            raw_error="provider_unavailable",
        )
    except Exception as exc:
        return _completion_payload(
            status="error",
            request_id=request_id,
            config=gateway_config,
            url_validation=url_validation,
            purpose=purpose,
            model=model,
            started=started,
            failure_reasons=("provider_error",),
            warnings=tuple(warnings),
            output_text="",
            usage={},
            raw_error=_sanitize_error(exc),
        )

    if response.status_code >= 400:
        return _completion_payload(
            status="error",
            request_id=request_id,
            config=gateway_config,
            url_validation=url_validation,
            purpose=purpose,
            model=model,
            started=started,
            failure_reasons=(f"http_status_{response.status_code}",),
            warnings=tuple(warnings),
            output_text="",
            usage={},
            raw_error=f"http_status_{response.status_code}",
        )
    output_text = _extract_chat_output(response.json_data)
    if not output_text:
        return _completion_payload(
            status="error",
            request_id=request_id,
            config=gateway_config,
            url_validation=url_validation,
            purpose=purpose,
            model=model,
            started=started,
            failure_reasons=("empty_model_output",),
            warnings=tuple(warnings),
            output_text="",
            usage=_usage(response.json_data),
            raw_error="empty_model_output",
        )
    payload = _completion_payload(
        status="completed",
        request_id=request_id,
        config=gateway_config,
        url_validation=url_validation,
        purpose=purpose,
        model=model,
        started=started,
        failure_reasons=(),
        warnings=tuple(warnings),
        output_text=output_text,
        usage=_usage(response.json_data),
        raw_error=None,
    )
    payload["http_request_performed"] = True
    payload["model_call_performed"] = True
    payload["generation_performed"] = True
    payload["prompt_payload_sent"] = True
    return payload


def _config_failures(
    config: ModelGatewayConfig,
    url_validation: ModelGatewayUrlValidation,
    *,
    require_model: bool,
) -> tuple[str, ...]:
    failures: list[str] = []
    if not config.enabled:
        failures.append("gateway_disabled")
    if config.provider != MODEL_GATEWAY_PROVIDER:
        failures.append("unsupported_provider")
    failures.extend(url_validation.reasons)
    if config.timeout_seconds <= 0:
        failures.append("invalid_timeout")
    if config.max_input_chars < 1:
        failures.append("invalid_max_input_chars")
    if config.max_output_tokens < 1:
        failures.append("invalid_max_output_tokens")
    if require_model and _missing_model(config.model):
        failures.append("missing_model")
    return tuple(dict.fromkeys(failures))


def _missing_model(model: str) -> bool:
    return str(model or "").strip().lower() in MISSING_MODEL_VALUES


def _base_payload(
    *,
    status: str,
    config: ModelGatewayConfig,
    url_validation: ModelGatewayUrlValidation,
    failure_reasons: tuple[str, ...],
    limitations: tuple[str, ...],
    unknowns: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "model_gateway_version": MODEL_GATEWAY_RC1_VERSION,
        "status": status,
        "provider": config.provider,
        "base_url": url_validation.normalized_base_url or config.base_url,
        "host": url_validation.host,
        "model": None if _missing_model(config.model) else config.model,
        "model_configured": not _missing_model(config.model),
        "enabled": config.enabled,
        "timeout_seconds": config.timeout_seconds,
        "max_input_chars": config.max_input_chars,
        "max_output_tokens": config.max_output_tokens,
        "health_result": "not_probed",
        "failure_reasons": failure_reasons,
        "warnings": (),
        "limitations": limitations,
        "unknowns": unknowns,
        "duration_ms": 0,
        "provider_probe_performed": False,
        "http_request_performed": False,
        "model_call_performed": False,
        "generation_performed": False,
        "prompt_payload_sent": False,
        "context_payload_sent": False,
        "memory_write_performed": False,
        "tool_call_performed": False,
        "mcp_call_performed": False,
        "shell_command_performed": False,
        "file_mutation_performed": False,
        "data_sent_external": False,
        **_non_authority_flags(),
    }


def _completion_payload(
    *,
    status: str,
    request_id: str,
    config: ModelGatewayConfig,
    url_validation: ModelGatewayUrlValidation,
    purpose: str,
    model: str,
    started: float,
    failure_reasons: tuple[str, ...],
    warnings: tuple[str, ...],
    output_text: str,
    usage: Mapping[str, Any],
    raw_error: str | None,
) -> dict[str, Any]:
    return {
        "model_gateway_version": MODEL_GATEWAY_RC1_VERSION,
        "request_id": request_id,
        "status": status,
        "provider": config.provider,
        "base_url": url_validation.normalized_base_url or config.base_url,
        "model": None if _missing_model(model) else model,
        "purpose": purpose,
        "output_text": output_text,
        "usage": dict(usage),
        "started_at": started,
        "completed_at": time.time(),
        "duration_ms": _duration_ms(started),
        "warnings": warnings,
        "limitations": _common_limitations(),
        "failure_reasons": failure_reasons,
        "raw_error": raw_error,
        "schema_validation": "openai_chat_completion_candidate" if status == "completed" else "not_validated",
        "safety_validation": "non_authority_envelope_applied",
        "http_request_performed": False,
        "model_call_performed": False,
        "generation_performed": False,
        "prompt_payload_sent": False,
        "context_payload_sent": False,
        "memory_write_performed": False,
        "tool_call_performed": False,
        "mcp_call_performed": False,
        "shell_command_performed": False,
        "file_mutation_performed": False,
        "data_sent_external": False,
        "transcript_persisted": False,
        "journal_mutated": False,
        "evidence_mutated": False,
        "runtime_state_mutated": False,
        **_non_authority_flags(),
    }


def _non_authority_flags() -> dict[str, Any]:
    return {
        "authority": False,
        "execution_permission": MODEL_GATEWAY_EXECUTION_PERMISSION,
        "evidence": False,
        "evidence_provided_by_model": False,
        "verifier_success": False,
        "approval_granted": False,
        "approval_grant": False,
        "permission_granted": False,
        "capability_lease_granted": False,
        "capability_grant": False,
        "lease_grant": False,
        "runtime_dispatch_allowed": False,
        "memory_output_is_authority": False,
        "model_output_is_truth": False,
        "model_output_is_evidence": False,
        "model_output_is_verifier_success": False,
        "requires_backend_validation": True,
        "requires_policy_check": True,
    }


def _common_limitations() -> tuple[str, ...]:
    return (
        "local_lm_studio_only",
        "model_output_is_proposal_only",
        "no_hidden_fallback",
        "no_memory_write",
        "no_tool_mcp_shell_or_file_mutation",
        "no_evidence_or_verifier_success",
    )


def _probe_error_payload(
    status: str,
    config: ModelGatewayConfig,
    url_validation: ModelGatewayUrlValidation,
    reason: str,
    started: float,
) -> dict[str, Any]:
    payload = _base_payload(
        status=status,
        config=config,
        url_validation=url_validation,
        failure_reasons=(reason,),
        limitations=_common_limitations(),
        unknowns=(),
    )
    payload["duration_ms"] = _duration_ms(started)
    payload["provider_probe_performed"] = True
    payload["http_request_performed"] = True
    return payload


def _probe_result(response: ModelGatewayHttpResponse) -> dict[str, Any]:
    result = {
        "status_code": response.status_code,
        "model_count_candidate": 0,
        "response_shape": "unknown",
    }
    if isinstance(response.json_data, Mapping):
        data = response.json_data.get("data")
        if isinstance(data, list):
            result["model_count_candidate"] = len(data)
            result["response_shape"] = "openai_models_list_candidate"
        else:
            result["response_shape"] = "metadata_candidate"
    return result


def _prompt_text(request: Mapping[str, Any]) -> str:
    if request.get("prompt") is not None:
        return str(request.get("prompt") or "")
    messages = request.get("messages")
    if isinstance(messages, list):
        parts = []
        for item in messages:
            if isinstance(item, Mapping):
                parts.append(str(item.get("content") or ""))
        return "\n".join(parts)
    return ""


def _chat_messages(request: Mapping[str, Any], purpose: str) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = [
        {"role": "system", "content": f"{BOUNDARY_SYSTEM_MESSAGE} Purpose: {purpose}."}
    ]
    provided = request.get("messages")
    if isinstance(provided, list):
        for item in provided:
            if isinstance(item, Mapping):
                role = str(item.get("role") or "user")
                content = str(item.get("content") or "")
                if role not in {"system", "user", "assistant"}:
                    role = "user"
                if content:
                    messages.append({"role": role, "content": content})
        return messages
    prompt = str(request.get("prompt") or "")
    if prompt:
        messages.append({"role": "user", "content": prompt})
    return messages


def _extract_chat_output(data: Any) -> str:
    if not isinstance(data, Mapping):
        return ""
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    first = choices[0]
    if not isinstance(first, Mapping):
        return ""
    message = first.get("message")
    if isinstance(message, Mapping):
        return str(message.get("content") or "").strip()
    return str(first.get("text") or "").strip()


def _usage(data: Any) -> dict[str, Any]:
    if isinstance(data, Mapping) and isinstance(data.get("usage"), Mapping):
        return dict(data["usage"])
    return {}


def _sanitize_error(exc: Exception) -> str:
    name = exc.__class__.__name__
    text = str(exc).strip()
    if not text:
        return name
    return f"{name}: {text[:160]}"


def _duration_ms(started: float) -> int:
    return max(0, int((time.time() - started) * 1000))
