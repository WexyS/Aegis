from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from aegis.core.integration_registry import build_integration_landscape
from aegis.core.mode_policy import list_mode_policies, mode_allows_execution_now
from aegis.core.model_gateway import build_model_gateway_status


ORCHESTRATOR_READINESS_CONTRACT = "aegis-orchestrator-readiness"
ORCHESTRATOR_EXECUTION_PERMISSION = "not_granted_by_orchestrator_readiness"


def build_orchestrator_readiness(
    *,
    model_gateway_status: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    landscape = build_integration_landscape()
    mode_policies = list_mode_policies()
    gateway_status = dict(model_gateway_status or build_model_gateway_status())
    gateway_state = str(gateway_status.get("status") or "unknown")
    lm_studio_readiness = _lm_studio_readiness(gateway_state)
    local_model_usable = gateway_state == "configured"
    return {
        "contract": ORCHESTRATOR_READINESS_CONTRACT,
        "status": "ready_for_architecture_review",
        "integration_landscape_count": landscape["integration_count"],
        "families_represented": landscape["families"],
        "family_counts": landscape["family_counts"],
        "modes_represented": [policy["mode"] for policy in mode_policies],
        "mode_policies": mode_policies,
        "mode_execution_allowed_now": {
            policy["mode"]: mode_allows_execution_now(str(policy["mode"])) for policy in mode_policies
        },
        "model_gateway_status": gateway_status,
        "model_gateway_status_source": "config_only_build_model_gateway_status",
        "lm_studio_readiness_state": lm_studio_readiness,
        "provider_probe_performed": False,
        "http_request_performed": False,
        "model_call_performed": False,
        "lm_studio_called": False,
        "local_model_usability": local_model_usable,
        "local_model_output_status": "proposal-only",
        "execution_allowed": False,
        "memory_write_allowed": False,
        "tool_execution_allowed": False,
        "agent_execution_allowed": False,
        "workflow_execution_allowed": False,
        "computer_execution_allowed": False,
        "external_api_allowed": False,
        "external_process_launch_allowed": False,
        "non_authority_flags": _non_authority_flags(),
        "authority": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": ORCHESTRATOR_EXECUTION_PERMISSION,
        "evidence_created": False,
        "verifier_success": False,
        "approval_granted": False,
        "capability_lease_granted": False,
        "frontend_authority": False,
        "limitations": [
            "orchestrator_readiness_only",
            "integration_registry_does_not_execute_integrations",
            "mode_policy_does_not_grant_execution",
            "model_gateway_status_is_config_only",
            "lm_studio_not_probed_or_called",
        ],
    }


def _lm_studio_readiness(status: str) -> str:
    if status == "disabled":
        return "disabled"
    if status == "misconfigured":
        return "misconfigured"
    if status == "configured":
        return "configured"
    return "not_probed"


def _non_authority_flags() -> dict[str, bool]:
    return {
        "model_output_is_not_truth": True,
        "model_output_is_not_evidence": True,
        "model_output_is_not_verifier_success": True,
        "model_output_is_not_approval": True,
        "model_output_is_not_permission": True,
        "model_output_is_not_capability_lease": True,
        "frontend_is_not_authority": True,
    }
