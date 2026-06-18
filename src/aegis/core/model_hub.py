from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from aegis.core.external_provider_readiness import (
    build_cloud_fallback_policy,
    list_external_provider_readiness,
)
from aegis.core.external_provider_broker_boundary import build_external_provider_broker_boundary
from aegis.core.integration_registry import list_integrations_by_family
from aegis.core.local_model_profiles import (
    build_resource_guardrails,
    list_local_model_profiles,
    match_configured_model_profile,
    recommended_default_profile_id,
)
from aegis.core.mode_policy import list_mode_policies, mode_allows_execution_now
from aegis.core.model_gateway import build_model_gateway_status
from aegis.core.orchestrator_readiness import build_orchestrator_readiness


MODEL_HUB_CONTRACT = "aegis-model-hub"
MODEL_HUB_EXECUTION_PERMISSION = "not_granted_by_model_hub"


def build_model_hub_status(
    *,
    model_gateway_status: Mapping[str, Any] | None = None,
    external_provider_env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    gateway_status = dict(model_gateway_status or build_model_gateway_status())
    readiness = build_orchestrator_readiness(model_gateway_status=gateway_status)
    model_hub_integrations = _model_hub_integrations()
    mode_policy_summary = _mode_policy_summary()
    lm_studio = _lm_studio_summary(gateway_status)
    local_model_profiles = list_local_model_profiles()
    active_profile_match = match_configured_model_profile(gateway_status.get("model"))
    external_provider_readiness = list_external_provider_readiness(external_provider_env)

    return {
        "contract": MODEL_HUB_CONTRACT,
        "status": _hub_status(gateway_status),
        "model_gateway": gateway_status,
        "orchestrator_readiness": readiness,
        "model_hub_integrations": model_hub_integrations,
        "mode_policy_summary": mode_policy_summary,
        "lm_studio": lm_studio,
        "local_model_profiles": local_model_profiles,
        "resource_guardrails": build_resource_guardrails(),
        "recommended_default_profile_id": recommended_default_profile_id(),
        "active_model_profile_match": active_profile_match,
        "external_provider_readiness": external_provider_readiness,
        "external_provider_broker_boundary": build_external_provider_broker_boundary(
            provider_readiness=external_provider_readiness,
        ),
        "cloud_fallback_policy": build_cloud_fallback_policy(),
        "non_authority_flags": _non_authority_flags(),
        "authority": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": MODEL_HUB_EXECUTION_PERMISSION,
        "approval_grant": False,
        "approval_granted": False,
        "capability_grant": False,
        "capability_lease_granted": False,
        "lease_grant": False,
        "evidence_created": False,
        "evidence_provided_by_model_hub": False,
        "verifier_success": False,
        "mutation_performed": False,
        "frontend_authority": False,
        "provider_probe_performed": False,
        "http_request_performed": False,
        "model_call_performed": False,
        "generation_performed": False,
        "prompt_payload_sent": False,
        "context_payload_sent": False,
        "memory_write_performed": False,
        "tool_call_performed": False,
        "mcp_call_performed": False,
        "plugin_execution_performed": False,
        "agent_execution_performed": False,
        "workflow_execution_performed": False,
        "computer_control_performed": False,
        "shell_command_performed": False,
        "file_mutation_performed": False,
        "external_api_called": False,
        "cloud_routing_allowed": False,
        "data_sent_external": False,
        "config_mutation_allowed": False,
        "env_file_written": False,
        "requires_backend_validation": True,
        "requires_policy_check": True,
        "limitations": [
            "model_hub_status_is_config_and_registry_projection_only",
            "status_endpoint_does_not_probe_lm_studio",
            "status_endpoint_does_not_call_models",
            "frontend_state_is_not_authority",
            "local_model_output_is_proposal_only",
            "no_cloud_fallback",
            "provider_key_presence_is_readiness_metadata_only",
            "local_model_profile_match_is_config_metadata_only",
            "external_provider_broker_boundary_is_preview_only",
        ],
    }


def _hub_status(gateway_status: Mapping[str, Any]) -> str:
    status = str(gateway_status.get("status") or "unknown")
    if status == "configured":
        return "configured_metadata_only"
    if status in {"disabled", "misconfigured", "blocked", "unavailable", "timeout", "error", "ready"}:
        return status
    return "unknown"


def _lm_studio_summary(gateway_status: Mapping[str, Any]) -> dict[str, Any]:
    model = gateway_status.get("model")
    return {
        "provider": "lm_studio",
        "base_url": gateway_status.get("base_url"),
        "host": gateway_status.get("host"),
        "enabled": bool(gateway_status.get("enabled")),
        "model": model,
        "model_configured": bool(gateway_status.get("model_configured")),
        "status": gateway_status.get("status") or "unknown",
        "failure_reasons": list(gateway_status.get("failure_reasons") or []),
        "warnings": list(gateway_status.get("warnings") or []),
        "probe_required_for_live_health": True,
        "local_only_boundary": True,
        "openai_compatible_local_endpoint": True,
        "config_mutation_allowed": False,
        "env_file_written": False,
        "cloud_fallback_available": False,
        "status_source": "config_only_model_gateway_status",
    }


def _model_hub_integrations() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for record in list_integrations_by_family("model_hub"):
        records.append(
            {
                "integration_id": record.get("integration_id"),
                "aegis_name": record.get("aegis_name"),
                "family": record.get("family"),
                "aegis_surface": record.get("aegis_surface"),
                "source_strategy": record.get("source_strategy"),
                "default_execution_status": record.get("default_execution_status"),
                "current_status": record.get("current_status"),
                "risk_level": record.get("risk_level"),
                "requires_network": bool(record.get("requires_network")),
                "requires_secret": bool(record.get("requires_secret")),
                "requires_process_spawn": bool(record.get("requires_process_spawn")),
                "requires_model_gateway": bool(record.get("requires_model_gateway")),
                "requires_external_api": bool(record.get("requires_external_api")),
                "allowed_modes": list(record.get("allowed_modes") or []),
                "notes": list(record.get("notes") or []),
                "authority": False,
                "runtime_dispatch_allowed": False,
                "execution_permission": record.get("execution_permission"),
                "execution_enabled_now": False,
                "model_call_performed": False,
                "external_api_called": False,
            }
        )
    return records


def _mode_policy_summary() -> dict[str, Any]:
    modes = []
    for policy in list_mode_policies():
        mode = str(policy.get("mode") or "unknown")
        modes.append(
            {
                "mode": mode,
                "display_name": policy.get("display_name"),
                "model_gateway_allowed": bool(policy.get("model_gateway_allowed")),
                "external_api_allowed": bool(policy.get("external_api_allowed")),
                "tool_execution_allowed": bool(policy.get("tool_execution_allowed")),
                "agent_execution_allowed": bool(policy.get("agent_execution_allowed")),
                "workflow_execution_allowed": bool(policy.get("workflow_execution_allowed")),
                "computer_control_allowed": bool(policy.get("computer_control_allowed")),
                "mode_allows_execution_now": mode_allows_execution_now(mode),
                "current_execution_grant": False,
            }
        )
    return {
        "modes": modes,
        "mode_count": len(modes),
        "execution_allowed_now": False,
        "external_api_allowed_now": False,
        "cloud_routing_allowed": False,
    }


def _non_authority_flags() -> dict[str, bool]:
    return {
        "model_output_is_not_truth": True,
        "model_output_is_not_evidence": True,
        "model_output_is_not_verifier_success": True,
        "model_output_is_not_approval": True,
        "model_output_is_not_permission": True,
        "model_output_is_not_capability_lease": True,
        "model_hub_status_is_not_live_provider_health": True,
        "model_gateway_status_is_config_only_until_probe": True,
        "frontend_is_not_authority": True,
        "integration_registry_metadata_is_not_execution_permission": True,
        "mode_policy_metadata_is_not_execution_permission": True,
    }
