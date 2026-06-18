from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, urlunparse
from urllib.request import Request, urlopen


DEFAULT_AEGIS_API_URL = "http://127.0.0.1:8400"
LOCAL_API_HOSTS = {"127.0.0.1", "localhost", "::1"}
MAX_OPERATOR_PROMPT_CHARS = 1200

SAFE_MODEL_HUB_SMOKE_PROMPT = (
    "You are connected to Aegis through the local Model Gateway. Summarize the "
    "current Aegis Model Hub state and the safest next step. Do not claim "
    "execution, approval, evidence, verifier success, memory writes, tool access, "
    "shell access, file mutation, computer control, or external/cloud access."
)


@dataclass(frozen=True)
class SmokeOptions:
    api_url: str = DEFAULT_AEGIS_API_URL
    probe: bool = False
    live: bool = False
    complete: bool = False
    confirm_local_lm_studio: bool = False
    prompt: str | None = None
    timeout_seconds: float = 10.0
    allow_nonlocal_api: bool = False


def normalize_aegis_api_url(api_url: str, *, allow_nonlocal_api: bool = False) -> str:
    parsed = urlparse(str(api_url or "").strip())
    reasons: list[str] = []
    if parsed.scheme not in {"http", "https"}:
        reasons.append("unsupported_api_url_scheme")
    if parsed.username or parsed.password:
        reasons.append("credentials_in_api_url_denied")
    if parsed.query or parsed.fragment:
        reasons.append("query_or_fragment_in_api_url_denied")
    host = (parsed.hostname or "").lower()
    if not host:
        reasons.append("missing_api_host")
    elif not allow_nonlocal_api and host not in LOCAL_API_HOSTS:
        reasons.append("non_local_aegis_api_denied")
    if reasons:
        raise ValueError(",".join(reasons))

    path = (parsed.path or "").rstrip("/")
    return urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))


def smoke_completion_prompt(prompt: str | None = None) -> str:
    if prompt is None:
        return SAFE_MODEL_HUB_SMOKE_PROMPT
    candidate = str(prompt).strip()
    if not candidate:
        return SAFE_MODEL_HUB_SMOKE_PROMPT
    if len(candidate) > MAX_OPERATOR_PROMPT_CHARS:
        raise ValueError("operator_prompt_too_large")
    return candidate


def build_smoke_plan(options: SmokeOptions) -> dict[str, Any]:
    api_url = normalize_aegis_api_url(
        options.api_url,
        allow_nonlocal_api=options.allow_nonlocal_api,
    )
    completion_blocked_reasons = _completion_blockers(options)
    return {
        "api_url": api_url,
        "status_requests": ("/model-hub/status", "/model-gateway/status"),
        "probe_requested": bool(options.probe),
        "probe_endpoint": "/model-gateway/probe" if options.probe else None,
        "completion_requested": bool(options.complete),
        "completion_endpoint": "/model-gateway/complete" if options.complete else None,
        "completion_allowed_by_operator_flags": bool(options.complete and not completion_blocked_reasons),
        "completion_blocked_reasons": tuple(completion_blocked_reasons),
        "will_write_files": False,
        "will_edit_env": False,
        "will_execute_tools": False,
        "will_create_evidence": False,
        "will_grant_approval_or_lease": False,
        "will_use_cloud_fallback": False,
    }


def build_completion_request(prompt: str | None = None) -> dict[str, Any]:
    return {
        "request_id": "model_hub_operator_live_smoke",
        "purpose": "explanation",
        "prompt": smoke_completion_prompt(prompt),
        "temperature": 0.1,
        "max_output_tokens": 256,
    }


def summarize_smoke_payloads(
    *,
    plan: Mapping[str, Any],
    model_hub_status: Mapping[str, Any] | None,
    model_gateway_status: Mapping[str, Any] | None,
    probe_result: Mapping[str, Any] | None = None,
    completion_result: Mapping[str, Any] | None = None,
    request_error: str | None = None,
) -> dict[str, Any]:
    gateway = dict(model_gateway_status or {})
    hub = dict(model_hub_status or {})
    completion = dict(completion_result or {})
    probe = dict(probe_result or {})
    failures = list(gateway.get("failure_reasons") or ())
    failures.extend(hub.get("failure_reasons") or ())
    failures.extend(probe.get("failure_reasons") or ())
    failures.extend(completion.get("failure_reasons") or ())
    if request_error:
        failures.append(request_error)

    return {
        "decision": "AEGIS_MODEL_HUB_LM_STUDIO_SMOKE_OPERATOR_RESULT",
        "api_url": plan.get("api_url"),
        "model_hub_status": hub.get("status", "unknown"),
        "model_gateway_status": gateway.get("status", "unknown"),
        "gateway_enabled": bool(gateway.get("enabled", False)),
        "model_configured": bool(gateway.get("model_configured", False)),
        "provider": gateway.get("provider"),
        "base_url": gateway.get("base_url"),
        "model": gateway.get("model"),
        "probe_requested": bool(plan.get("probe_requested")),
        "probe_status": probe.get("status") if probe else "not_requested",
        "completion_requested": bool(plan.get("completion_requested")),
        "completion_allowed_by_operator_flags": bool(plan.get("completion_allowed_by_operator_flags")),
        "completion_status": completion.get("status") if completion else "not_requested",
        "completion_blocked_reasons": tuple(plan.get("completion_blocked_reasons") or ()),
        "failure_reasons": tuple(dict.fromkeys(str(reason) for reason in failures if reason)),
        "model_output_proposal_only": _proposal_only(completion),
        "non_authority_flags_preserved": _non_authority_flags_preserved(gateway, probe, completion),
        "execution_performed": False,
        "memory_write_performed": False,
        "tool_call_performed": False,
        "plugin_execution_performed": False,
        "agent_execution_performed": False,
        "evidence_created": False,
        "verifier_success": False,
        "approval_granted": False,
        "capability_lease_granted": False,
        "env_edited": False,
        "files_written": False,
        "cloud_fallback_used": False,
    }


def run_operator_smoke(options: SmokeOptions) -> dict[str, Any]:
    plan = build_smoke_plan(options)
    api_url = str(plan["api_url"])
    request_error = None
    hub_status: Mapping[str, Any] | None = None
    gateway_status: Mapping[str, Any] | None = None
    probe_result: Mapping[str, Any] | None = None
    completion_result: Mapping[str, Any] | None = None

    try:
        hub_status = _request_json("GET", f"{api_url}/model-hub/status", timeout=options.timeout_seconds)
        gateway_status = _request_json("GET", f"{api_url}/model-gateway/status", timeout=options.timeout_seconds)
        if options.probe:
            probe_result = _request_json("POST", f"{api_url}/model-gateway/probe", timeout=options.timeout_seconds)
        if plan["completion_allowed_by_operator_flags"]:
            completion_result = _request_json(
                "POST",
                f"{api_url}/model-gateway/complete",
                payload=build_completion_request(options.prompt),
                timeout=options.timeout_seconds,
            )
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        request_error = f"{exc.__class__.__name__}: {str(exc)[:160]}"

    return summarize_smoke_payloads(
        plan=plan,
        model_hub_status=hub_status,
        model_gateway_status=gateway_status,
        probe_result=probe_result,
        completion_result=completion_result,
        request_error=request_error,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run an explicit operator-only Aegis Model Hub / LM Studio smoke check."
    )
    parser.add_argument("--api-url", default=DEFAULT_AEGIS_API_URL)
    parser.add_argument("--probe", action="store_true", help="Also call POST /model-gateway/probe.")
    parser.add_argument("--complete", action="store_true", help="Request a proposal-only completion if live flags are present.")
    parser.add_argument("--live", action="store_true", help="Operator confirms this is a live local smoke attempt.")
    parser.add_argument(
        "--confirm-local-lm-studio",
        action="store_true",
        help="Required with --live --complete before POST /model-gateway/complete is called.",
    )
    parser.add_argument("--prompt", help="Optional harmless smoke prompt. Do not include secrets or private data.")
    parser.add_argument("--timeout-seconds", type=float, default=10.0)
    parser.add_argument(
        "--allow-nonlocal-api",
        action="store_true",
        help="Diagnostic escape hatch for non-default deployments. Not needed for local operator smoke.",
    )
    args = parser.parse_args(argv)
    try:
        result = run_operator_smoke(
            SmokeOptions(
                api_url=args.api_url,
                probe=args.probe,
                complete=args.complete,
                live=args.live,
                confirm_local_lm_studio=args.confirm_local_lm_studio,
                prompt=args.prompt,
                timeout_seconds=args.timeout_seconds,
                allow_nonlocal_api=args.allow_nonlocal_api,
            )
        )
    except ValueError as exc:
        result = {
            "decision": "AEGIS_MODEL_HUB_LM_STUDIO_SMOKE_OPERATOR_RESULT",
            "status": "blocked",
            "failure_reasons": (str(exc),),
            "files_written": False,
            "env_edited": False,
            "cloud_fallback_used": False,
        }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def _completion_blockers(options: SmokeOptions) -> tuple[str, ...]:
    if not options.complete:
        return ()
    blockers: list[str] = []
    if not options.live:
        blockers.append("missing_live_operator_flag")
    if not options.confirm_local_lm_studio:
        blockers.append("missing_confirm_local_lm_studio_flag")
    return tuple(blockers)


def _request_json(
    method: str,
    url: str,
    *,
    payload: Mapping[str, Any] | None = None,
    timeout: float,
) -> Mapping[str, Any]:
    body = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(url, data=body, method=method, headers=headers)
    with urlopen(request, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))
    if not isinstance(data, Mapping):
        raise ValueError("response_json_shape_not_object")
    return data


def _proposal_only(completion: Mapping[str, Any]) -> bool:
    if not completion:
        return True
    return not any(
        bool(completion.get(field))
        for field in (
            "authority",
            "evidence",
            "evidence_provided_by_model",
            "verifier_success",
            "approval_granted",
            "permission_granted",
            "capability_lease_granted",
            "model_output_is_truth",
            "model_output_is_evidence",
            "model_output_is_verifier_success",
        )
    )


def _non_authority_flags_preserved(*payloads: Mapping[str, Any]) -> bool:
    checked = [dict(payload) for payload in payloads if payload]
    if not checked:
        return False
    for payload in checked:
        if payload.get("authority") is not False:
            return False
        if payload.get("runtime_dispatch_allowed") is not False:
            return False
        if payload.get("verifier_success") is not False:
            return False
    return True


if __name__ == "__main__":
    sys.exit(main())
