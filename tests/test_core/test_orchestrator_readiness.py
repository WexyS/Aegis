from __future__ import annotations

from aegis.core.integration_registry import VALID_INTEGRATION_FAMILIES
from aegis.core.orchestrator_readiness import build_orchestrator_readiness


def _gateway_status(status: str) -> dict[str, object]:
    return {
        "status": status,
        "provider": "lm_studio",
        "enabled": status != "disabled",
        "model_configured": status == "configured",
        "provider_probe_performed": False,
        "http_request_performed": False,
        "model_call_performed": False,
    }


def test_readiness_does_not_perform_live_provider_calls() -> None:
    readiness = build_orchestrator_readiness(model_gateway_status=_gateway_status("configured"))

    assert readiness["model_gateway_status_source"] == "config_only_build_model_gateway_status"
    assert readiness["provider_probe_performed"] is False
    assert readiness["http_request_performed"] is False
    assert readiness["model_call_performed"] is False
    assert readiness["lm_studio_called"] is False


def test_readiness_reports_execution_and_mutation_as_false() -> None:
    readiness = build_orchestrator_readiness(model_gateway_status=_gateway_status("disabled"))

    assert readiness["execution_allowed"] is False
    assert readiness["memory_write_allowed"] is False
    assert readiness["tool_execution_allowed"] is False
    assert readiness["agent_execution_allowed"] is False
    assert readiness["workflow_execution_allowed"] is False
    assert readiness["computer_execution_allowed"] is False
    assert readiness["external_api_allowed"] is False
    assert readiness["external_process_launch_allowed"] is False
    assert readiness["runtime_dispatch_allowed"] is False
    assert readiness["evidence_created"] is False
    assert readiness["verifier_success"] is False
    assert readiness["approval_granted"] is False
    assert readiness["capability_lease_granted"] is False


def test_readiness_preserves_model_output_non_authority_flags() -> None:
    readiness = build_orchestrator_readiness(model_gateway_status=_gateway_status("configured"))
    flags = readiness["non_authority_flags"]

    assert flags["model_output_is_not_truth"] is True
    assert flags["model_output_is_not_evidence"] is True
    assert flags["model_output_is_not_verifier_success"] is True
    assert flags["model_output_is_not_approval"] is True
    assert flags["model_output_is_not_permission"] is True
    assert flags["model_output_is_not_capability_lease"] is True
    assert flags["frontend_is_not_authority"] is True


def test_readiness_includes_integration_family_counts() -> None:
    readiness = build_orchestrator_readiness(model_gateway_status=_gateway_status("disabled"))

    assert readiness["integration_landscape_count"] > 0
    assert set(readiness["families_represented"]) == VALID_INTEGRATION_FAMILIES
    assert set(readiness["family_counts"]) == VALID_INTEGRATION_FAMILIES
    assert all(count > 0 for count in readiness["family_counts"].values())
    assert set(readiness["modes_represented"]) == {"safe", "balanced", "power", "yolo_lab"}
    assert all(value is False for value in readiness["mode_execution_allowed_now"].values())


def test_lm_studio_readiness_tracks_config_only_gateway_status() -> None:
    disabled = build_orchestrator_readiness(model_gateway_status=_gateway_status("disabled"))
    misconfigured = build_orchestrator_readiness(model_gateway_status=_gateway_status("misconfigured"))
    configured = build_orchestrator_readiness(model_gateway_status=_gateway_status("configured"))
    ready = build_orchestrator_readiness(model_gateway_status=_gateway_status("ready"))

    assert disabled["lm_studio_readiness_state"] == "disabled"
    assert disabled["local_model_usability"] is False
    assert misconfigured["lm_studio_readiness_state"] == "misconfigured"
    assert misconfigured["local_model_usability"] is False
    assert configured["lm_studio_readiness_state"] == "configured"
    assert configured["local_model_usability"] is True
    assert ready["lm_studio_readiness_state"] == "not_probed"
    assert ready["local_model_usability"] is False


def test_readiness_limitations_state_architecture_only() -> None:
    readiness = build_orchestrator_readiness(model_gateway_status=_gateway_status("disabled"))

    assert "orchestrator_readiness_only" in readiness["limitations"]
    assert "integration_registry_does_not_execute_integrations" in readiness["limitations"]
    assert "mode_policy_does_not_grant_execution" in readiness["limitations"]
    assert "lm_studio_not_probed_or_called" in readiness["limitations"]
