from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "model_hub_live_smoke.py"
SPEC = importlib.util.spec_from_file_location("model_hub_live_smoke", SCRIPT_PATH)
assert SPEC is not None
model_hub_live_smoke = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = model_hub_live_smoke
SPEC.loader.exec_module(model_hub_live_smoke)


def test_local_api_urls_are_allowed() -> None:
    assert (
        model_hub_live_smoke.normalize_aegis_api_url("http://127.0.0.1:8400/")
        == "http://127.0.0.1:8400"
    )
    assert (
        model_hub_live_smoke.normalize_aegis_api_url("http://localhost:8400")
        == "http://localhost:8400"
    )


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com",
        "http://127.0.0.1:8400?token=x",
        "http://user:pass@127.0.0.1:8400",
        "file:///tmp/aegis",
    ],
)
def test_unsafe_api_urls_are_rejected(url: str) -> None:
    with pytest.raises(ValueError):
        model_hub_live_smoke.normalize_aegis_api_url(url)


def test_default_smoke_plan_is_status_only_and_non_mutating() -> None:
    plan = model_hub_live_smoke.build_smoke_plan(model_hub_live_smoke.SmokeOptions())

    assert plan["status_requests"] == ("/model-hub/status", "/model-gateway/status")
    assert plan["probe_requested"] is False
    assert plan["completion_requested"] is False
    assert plan["completion_allowed_by_operator_flags"] is False
    assert plan["will_write_files"] is False
    assert plan["will_edit_env"] is False
    assert plan["will_execute_tools"] is False
    assert plan["will_create_evidence"] is False
    assert plan["will_grant_approval_or_lease"] is False
    assert plan["will_use_cloud_fallback"] is False


def test_completion_requires_live_operator_confirmation() -> None:
    blocked = model_hub_live_smoke.build_smoke_plan(
        model_hub_live_smoke.SmokeOptions(complete=True)
    )
    assert blocked["completion_allowed_by_operator_flags"] is False
    assert blocked["completion_blocked_reasons"] == (
        "missing_live_operator_flag",
        "missing_confirm_local_lm_studio_flag",
    )

    allowed = model_hub_live_smoke.build_smoke_plan(
        model_hub_live_smoke.SmokeOptions(
            live=True,
            complete=True,
            confirm_local_lm_studio=True,
        )
    )
    assert allowed["completion_allowed_by_operator_flags"] is True
    assert allowed["completion_blocked_reasons"] == ()


def test_safe_prompt_preserves_non_authority_boundary() -> None:
    prompt = model_hub_live_smoke.smoke_completion_prompt()

    assert "Do not claim execution" in prompt
    assert "approval" in prompt
    assert "evidence" in prompt
    assert "verifier success" in prompt
    assert "tool access" in prompt
    assert "file mutation" in prompt
    assert "external/cloud access" in prompt


def test_custom_prompt_is_length_limited() -> None:
    with pytest.raises(ValueError, match="operator_prompt_too_large"):
        model_hub_live_smoke.smoke_completion_prompt(
            "x" * (model_hub_live_smoke.MAX_OPERATOR_PROMPT_CHARS + 1)
        )


def test_completion_request_is_small_and_proposal_oriented() -> None:
    request = model_hub_live_smoke.build_completion_request()

    assert request["purpose"] == "explanation"
    assert request["temperature"] == 0.1
    assert request["max_output_tokens"] == 256
    assert len(request["prompt"]) <= model_hub_live_smoke.MAX_OPERATOR_PROMPT_CHARS
    assert "file mutation" in request["prompt"]


def test_summary_keeps_disabled_gateway_fail_closed() -> None:
    plan = model_hub_live_smoke.build_smoke_plan(model_hub_live_smoke.SmokeOptions())
    summary = model_hub_live_smoke.summarize_smoke_payloads(
        plan=plan,
        model_hub_status={
            "status": "configured",
            "failure_reasons": (),
            "recommended_default_profile_id": "default_proposal",
            "local_model_profiles": [{"profile_id": "default_proposal"}],
            "active_model_profile_match": {"matched_profile_id": "default_proposal"},
            "external_provider_readiness": [
                {
                    "provider_id": "openrouter",
                    "status": "missing_key_disabled",
                    "api_key_present": False,
                    "api_key_value_exposed": False,
                    "cloud_completion_enabled": False,
                    "automatic_fallback_allowed": False,
                }
            ],
            "cloud_fallback_policy": {"automatic_cloud_fallback_allowed": False},
        },
        model_gateway_status={
            "status": "disabled",
            "enabled": False,
            "model_configured": False,
            "provider": "lm_studio",
            "base_url": "http://127.0.0.1:1234/v1",
            "model": None,
            "failure_reasons": ("gateway_disabled",),
            "authority": False,
            "runtime_dispatch_allowed": False,
            "verifier_success": False,
        },
    )

    assert summary["model_gateway_status"] == "disabled"
    assert summary["gateway_enabled"] is False
    assert summary["model_configured"] is False
    assert summary["failure_reasons"] == ("gateway_disabled",)
    assert summary["recommended_default_profile_id"] == "default_proposal"
    assert summary["local_model_profile_count"] == 1
    assert summary["active_model_profile_match"] == {"matched_profile_id": "default_proposal"}
    assert summary["provider_readiness_statuses"]["openrouter"]["api_key_value_exposed"] is False
    assert summary["provider_readiness_statuses"]["openrouter"]["cloud_completion_enabled"] is False
    assert summary["cloud_fallback_policy"] == {"automatic_cloud_fallback_allowed": False}
    assert summary["model_output_proposal_only"] is True
    assert summary["non_authority_flags_preserved"] is True
    assert summary["execution_performed"] is False
    assert summary["memory_write_performed"] is False
    assert summary["tool_call_performed"] is False
    assert summary["evidence_created"] is False
    assert summary["verifier_success"] is False
    assert summary["approval_granted"] is False
    assert summary["capability_lease_granted"] is False
    assert summary["env_edited"] is False
    assert summary["files_written"] is False
    assert summary["cloud_fallback_used"] is False


def test_summary_detects_authority_claim_regression() -> None:
    plan = model_hub_live_smoke.build_smoke_plan(model_hub_live_smoke.SmokeOptions())
    summary = model_hub_live_smoke.summarize_smoke_payloads(
        plan=plan,
        model_hub_status={"status": "configured"},
        model_gateway_status={
            "status": "configured",
            "enabled": True,
            "model_configured": True,
            "authority": False,
            "runtime_dispatch_allowed": False,
            "verifier_success": False,
        },
        completion_result={
            "status": "completed",
            "authority": True,
            "runtime_dispatch_allowed": False,
            "verifier_success": False,
        },
    )

    assert summary["model_output_proposal_only"] is False
    assert summary["non_authority_flags_preserved"] is False
