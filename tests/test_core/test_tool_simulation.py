from __future__ import annotations

from copy import deepcopy

from aegis.core.mission_control import build_mission_control_preview
from aegis.core.tool_simulation import (
    TOOL_SIMULATION_EXECUTION_PERMISSION,
    TOOL_SIMULATION_VERSION,
    build_tool_simulation,
    mission_control_input_from_simulation,
)


def _request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "request_id": "req-sim-1",
        "command_id": "cmd-sim-1",
        "raw_user_request": "read docs",
        "normalized_intent": "read_file",
        "route_kind": "filesystem",
        "proposed_action": "read docs/policy-tool-simulation-dry-run-v1.md",
        "proposed_tool": "read_file",
        "tool_category": "file_tool",
        "capability_category": "local_file_read",
        "risk_tier": "read_only",
        "affected_resources": ["docs/policy-tool-simulation-dry-run-v1.md"],
        "policy_rule_refs": ["policy:read_file.path.ready"],
        "policy_decision_hint": "ready",
        "approval_hint": {"required": False, "reason": "read-only proposal"},
        "lease_hint": {"required": False, "reason": "lease not required"},
        "evidence_expectation_hint": ["policy_decision_ref_expected"],
        "verifier_expectation_hint": {
            "verifier_required": False,
            "verifier_name": "",
            "verifier_postcondition": "not applicable for read-only simulation",
            "verifier_failure_modes": [],
            "verifier_success_required_for_completion": False,
        },
        "rollback_status": "not_applicable",
        "fallback_expectation": {
            "fallback_available": False,
            "fallback_type": "none",
            "fallback_is_success": False,
            "timeout_projection_possible": False,
        },
        "provider_interstitial_risk": {
            "provider": "",
            "known_risk": "not_applicable",
            "bypass_allowed": False,
            "fallback_allowed": False,
        },
        "source_refs": ["policy:read_file.path.ready"],
    }
    request.update(overrides)
    return request


def test_valid_read_only_simulation_is_non_authoritative_and_non_dispatchable() -> None:
    decision = build_tool_simulation(_request())

    assert decision.simulation_version == TOOL_SIMULATION_VERSION
    assert decision.validation_status == "simulation_ready"
    assert decision.result is not None
    assert decision.result.simulation_version == TOOL_SIMULATION_VERSION
    assert decision.result.policy_simulation_status == "simulation_ready"
    assert decision.result.can_execute is False
    assert decision.result.would_dispatch is False
    assert decision.result.dispatch_performed is False
    assert decision.result.authority is False
    assert decision.result.runtime_dispatch_allowed is False
    assert decision.result.execution_permission == TOOL_SIMULATION_EXECUTION_PERMISSION
    assert decision.result.approval_grant is False
    assert decision.result.capability_grant is False
    assert decision.result.lease_grant is False
    assert decision.result.evidence_created is False
    assert decision.result.evidence_provided_by_simulation is False
    assert decision.result.verifier_success is False
    assert decision.result.mutation_performed is False
    assert decision.result.frontend_authority is False


def test_browser_search_simulation_includes_provider_evidence_verifier_and_interstitial_expectations() -> None:
    decision = build_tool_simulation(
        _request(
            raw_user_request="search Google for Aegis runtime",
            normalized_intent="search_web",
            route_kind="browser",
            proposed_action="search Google for Aegis runtime",
            proposed_tool="search_web",
            tool_category="browser_tool",
            capability_category="browser_search",
            risk_tier="browser_search",
            target_app="brave",
            target_url="https://www.google.com/search?q=Aegis+runtime",
            search_provider="google",
            query="Aegis runtime",
            affected_resources=["https://www.google.com/search?q=Aegis+runtime"],
            evidence_expectation_hint=[
                "browser_url_verification_expected",
                "provider_interstitial_check_expected",
                "policy_decision_ref_expected",
            ],
            verifier_expectation_hint={
                "verifier_required": True,
                "verifier_name": "browser-url-gate/1",
                "verifier_postcondition": "final URL and query match provider expectation",
                "verifier_failure_modes": ["provider_bot_challenge", "url_mismatch"],
                "verifier_success_required_for_completion": True,
            },
        )
    )

    assert decision.validation_status == "simulation_ready"
    assert decision.result is not None
    assert decision.result.search_provider == "google"
    assert "browser_url_verification_expected" in decision.result.evidence_expected
    assert "provider_interstitial_check_expected" in decision.result.evidence_expected
    assert decision.result.verifier_expected.verifier_name == "browser-url-gate/1"
    assert decision.result.provider_interstitial_risk["known_risk"] == "google_sorry_bot_challenge"
    assert decision.result.provider_interstitial_risk["bypass_allowed"] is False


def test_app_launch_simulation_includes_process_window_verifier_expectation() -> None:
    decision = build_tool_simulation(
        _request(
            raw_user_request="open notepad",
            normalized_intent="open_app",
            route_kind="desktop_app",
            proposed_action="open Notepad",
            proposed_tool="open_app",
            tool_category="app_tool",
            capability_category="app_launch",
            risk_tier="app_launch",
            target_app="notepad",
            affected_resources=["process:notepad"],
            approval_hint={"required": False, "reason": "known app open"},
            evidence_expectation_hint=["process_window_verification_expected", "policy_decision_ref_expected"],
            verifier_expectation_hint={
                "verifier_required": True,
                "verifier_name": "process-window-verifier/2",
                "verifier_postcondition": "Notepad process/window is observable",
                "verifier_failure_modes": ["process_missing", "window_missing"],
                "verifier_success_required_for_completion": True,
            },
        )
    )

    assert decision.validation_status == "simulation_ready"
    assert decision.result is not None
    assert "process_window_verification_expected" in decision.result.evidence_expected
    assert decision.result.verifier_expected.verifier_name == "process-window-verifier/2"


def test_local_file_write_simulation_requires_affected_resources_and_evidence_expectation() -> None:
    decision = build_tool_simulation(
        _request(
            normalized_intent="write_file",
            proposed_tool="write_file",
            tool_category="file_tool",
            capability_category="local_file_write",
            risk_tier="local_file_write",
            affected_resources=[],
            approval_hint={"required": True, "reason": "workspace write requires approval"},
            evidence_expectation_hint=[],
            rollback_status="backup_required",
        )
    )

    assert decision.validation_status == "blocked_by_missing_resource_scope"
    assert decision.result is not None
    assert "affected_resources_required_for_side_effecting_simulation" in decision.result.blocked_reasons
    assert "evidence_expectation_required_for_side_effecting_simulation" in decision.result.blocked_reasons


def test_destructive_action_with_unavailable_or_unknown_rollback_is_blocked() -> None:
    for rollback_status in ("unavailable", "unknown"):
        decision = build_tool_simulation(
            _request(
                normalized_intent="run_command",
                proposed_tool="run_command",
                proposed_action="delete system files",
                tool_category="shell_tool",
                capability_category="destructive_system_change",
                risk_tier="destructive_system_change",
                affected_resources=["C:/Windows"],
                approval_hint={"required": True, "reason": "destructive action"},
                evidence_expectation_hint=["human_review_required"],
                verifier_expectation_hint={
                    "verifier_required": True,
                    "verifier_name": "human-review",
                    "verifier_postcondition": "operator confirms blocked high-risk proposal",
                    "verifier_failure_modes": ["rollback_unavailable"],
                    "verifier_success_required_for_completion": True,
                },
                rollback_status=rollback_status,
            )
        )

        assert decision.validation_status == "blocked_by_unavailable_rollback"
        assert decision.result is not None
        assert "destructive_action_requires_known_rollback_or_blocked_policy" in decision.result.blocked_reasons


def test_unknown_risk_blocks_or_requires_clarification() -> None:
    decision = build_tool_simulation(
        _request(
            normalized_intent="future_action",
            proposed_tool="read_file",
            risk_tier="unknown",
            capability_category="unknown",
            evidence_expectation_hint=["unknown_evidence_expectation"],
        )
    )

    assert decision.validation_status == "blocked_by_unknown_risk"
    assert decision.result is not None
    assert decision.result.operator_attention_required is True
    assert "unknown_risk_tier" in decision.result.blocked_reasons


def test_unknown_tool_blocks_or_requires_clarification() -> None:
    decision = build_tool_simulation(
        _request(
            normalized_intent="future_tool",
            proposed_tool="future_tool",
            tool_category="unknown_tool",
        )
    )

    assert decision.validation_status == "unsupported_tool"
    assert decision.result is not None
    assert "unsupported_tool" in decision.result.blocked_reasons


def test_quarantined_click_and_generic_click_block() -> None:
    for tool in ("click", "browser_click", "desktop_click"):
        decision = build_tool_simulation(
            _request(
                normalized_intent=tool,
                proposed_tool=tool,
                tool_category="browser_tool" if tool == "browser_click" else "app_tool",
                risk_tier="unknown",
                capability_category="unknown",
            )
        )

        assert decision.validation_status == "blocked_by_quarantined_tool"
        assert decision.result is not None
        assert "quarantined_tool_not_simulatable_as_executable" in decision.result.blocked_reasons


def test_raw_control_command_simulation_blocks() -> None:
    decision = build_tool_simulation(
        _request(
            raw_user_request="/reset_memory",
            normalized_intent="/reset_memory",
            proposed_action="reset memory",
            proposed_tool="/reset_memory",
            tool_category="unknown_tool",
        )
    )

    assert decision.validation_status == "unsupported_action"
    assert decision.result is not None
    assert "raw_control_command_not_simulatable_as_direct_execution" in decision.result.blocked_reasons


def test_vision_live_feed_simulation_blocks_without_future_explicit_gate() -> None:
    decision = build_tool_simulation(
        _request(
            normalized_intent="vision_live_feed",
            proposed_tool="vision_live_feed",
            tool_category="model_tool",
            capability_category="unknown",
            risk_tier="unknown",
        )
    )

    assert decision.validation_status == "unsupported_tool"
    assert decision.result is not None
    assert "vision_live_feed_not_simulatable_without_future_privacy_gate" in decision.result.blocked_reasons


def test_external_api_write_requires_approval_lease_evidence_and_does_not_dispatch() -> None:
    decision = build_tool_simulation(
        _request(
            normalized_intent="external_api_write",
            proposed_tool="external_api_write",
            tool_category="api_tool",
            capability_category="external_api_write",
            risk_tier="external_api_write",
            affected_resources=["api:crm.example/write"],
            approval_hint={"required": True, "reason": "external write requires approval"},
            lease_hint={
                "required": True,
                "reason": "external API write requires scoped lease candidate",
                "scope": "external_api_write:crm.example",
                "duration": "10m",
            },
            evidence_expectation_hint=["policy_decision_ref_expected", "human_review_required"],
            verifier_expectation_hint={
                "verifier_required": True,
                "verifier_name": "external-write-preflight-review",
                "verifier_postcondition": "operator reviews external write scope before execution",
                "verifier_failure_modes": ["missing_api_scope"],
                "verifier_success_required_for_completion": True,
            },
        )
    )

    assert decision.validation_status == "approval_required"
    assert decision.result is not None
    assert decision.result.approval_required is True
    assert decision.result.lease_required is True
    assert decision.result.can_execute is False
    assert decision.result.would_dispatch is False
    assert decision.result.dispatch_performed is False


def test_plugin_execution_cannot_be_simulated_as_read_only() -> None:
    decision = build_tool_simulation(
        _request(
            normalized_intent="plugin_execution",
            proposed_tool="plugin_execution",
            tool_category="plugin_tool",
            capability_category="plugin_execution",
            risk_tier="read_only",
        )
    )

    assert decision.validation_status == "blocked_by_policy"
    assert decision.result is not None
    assert "plugin_execution_cannot_be_read_only" in decision.result.blocked_reasons


def test_memory_write_cannot_be_simulated_as_read_only() -> None:
    decision = build_tool_simulation(
        _request(
            normalized_intent="memory_write",
            proposed_tool="memory_write",
            tool_category="memory_tool",
            capability_category="memory_write",
            risk_tier="read_only",
        )
    )

    assert decision.validation_status == "blocked_by_policy"
    assert decision.result is not None
    assert "memory_write_cannot_be_read_only" in decision.result.blocked_reasons


def test_authority_grant_and_runtime_dispatch_fields_rejected() -> None:
    decision = build_tool_simulation(
        _request(
            authority=True,
            runtime_dispatch_allowed=True,
            can_execute=True,
            would_dispatch=True,
            dispatch_performed=True,
            approval_grant=True,
            capability_grant=True,
            lease_grant=True,
        )
    )

    assert "authority_must_be_false" in decision.failure_reasons
    assert "runtime_dispatch_not_allowed" in decision.failure_reasons
    assert "can_execute_not_allowed" in decision.failure_reasons
    assert "would_dispatch_not_allowed" in decision.failure_reasons
    assert "dispatch_performed_not_allowed" in decision.failure_reasons
    assert "approval_grant_not_allowed" in decision.failure_reasons
    assert "capability_grant_not_allowed" in decision.failure_reasons
    assert "lease_grant_not_allowed" in decision.failure_reasons


def test_simulation_cannot_claim_evidence_or_verifier_success() -> None:
    decision = build_tool_simulation(
        _request(
            evidence_created=True,
            evidence_provided_by_simulation=True,
            verifier_success=True,
            verified_success=True,
            success=True,
        )
    )

    assert decision.evidence_created is False
    assert decision.evidence_provided_by_simulation is False
    assert decision.verifier_success is False
    assert "simulation_cannot_create_evidence" in decision.failure_reasons
    assert "simulation_cannot_mark_verifier_success" in decision.failure_reasons
    assert "success_claim_denied" in decision.failure_reasons


def test_frontend_authority_rejected() -> None:
    decision = build_tool_simulation(_request(frontend_authority=True))

    assert decision.frontend_authority is False
    assert "frontend_authority_not_allowed" in decision.failure_reasons


def test_policy_denied_cannot_be_overridden_by_simulation() -> None:
    decision = build_tool_simulation(
        _request(
            policy_decision_hint="blocked",
            policy_rule_refs=["policy:run_command.critical_pattern.blocked"],
            approval_hint={"required": False, "reason": "caller tried to bypass policy"},
        )
    )

    assert decision.validation_status == "blocked_by_policy"
    assert decision.result is not None
    assert "policy_denied_cannot_be_overridden_by_simulation" in decision.result.blocked_reasons
    assert decision.result.approval_grant is False


def test_approval_required_is_explanatory_only_not_approval_grant() -> None:
    decision = build_tool_simulation(
        _request(
            approval_hint={"required": True, "reason": "workspace write requires approval"},
        )
    )

    assert decision.validation_status == "approval_required"
    assert decision.result is not None
    assert decision.result.approval_required is True
    assert decision.result.approval_reason == "workspace write requires approval"
    assert decision.result.approval_grant is False


def test_lease_required_is_explanatory_only_not_lease_grant() -> None:
    decision = build_tool_simulation(
        _request(
            lease_hint={
                "required": True,
                "reason": "repeated browser searches need scoped lease candidate",
                "scope": "browser_search:google",
                "duration": "10m",
            }
        )
    )

    assert decision.validation_status == "lease_required"
    assert decision.result is not None
    assert decision.result.lease_required is True
    assert decision.result.lease_reason == "repeated browser searches need scoped lease candidate"
    assert decision.result.proposed_lease_scope == "browser_search:google"
    assert decision.result.lease_grant is False


def test_timeout_fallback_expectation_cannot_claim_success() -> None:
    decision = build_tool_simulation(
        _request(
            timeout_budget_ref="timeout:browser_dispatching",
            fallback_expectation={
                "fallback_available": True,
                "fallback_type": "retry",
                "fallback_is_success": True,
                "timeout_projection_possible": True,
            },
        )
    )

    assert decision.result is not None
    assert "fallback_cannot_be_success" in decision.result.blocked_reasons
    assert decision.result.fallback_expectation["fallback_is_success"] is False


def test_provider_interstitial_risk_cannot_bypass_provider_challenge() -> None:
    decision = build_tool_simulation(
        _request(
            normalized_intent="search_web",
            proposed_tool="search_web",
            tool_category="browser_tool",
            capability_category="browser_search",
            risk_tier="browser_search",
            search_provider="google",
            evidence_expectation_hint=[
                "browser_url_verification_expected",
                "provider_interstitial_check_expected",
            ],
            verifier_expectation_hint={
                "verifier_required": True,
                "verifier_name": "browser-url-gate/1",
                "verifier_postcondition": "URL matches expected provider",
                "verifier_failure_modes": ["provider_bot_challenge"],
                "verifier_success_required_for_completion": True,
            },
            provider_interstitial_risk={
                "provider": "google",
                "known_risk": "google_sorry_bot_challenge",
                "bypass_allowed": True,
                "fallback_allowed": False,
            },
        )
    )

    assert decision.result is not None
    assert "provider_interstitial_bypass_not_allowed" in decision.result.blocked_reasons
    assert decision.result.provider_interstitial_risk["bypass_allowed"] is False


def test_compliance_certification_wording_rejected() -> None:
    decision = build_tool_simulation(
        _request(
            claims=[
                "Compliance certification",
                "official audit result",
                "court-admissible evidence",
                "proof of compliance",
                "controls are effective",
                "organization is safe",
            ]
        )
    )

    assert "compliance_certification_claim_denied" in decision.failure_reasons
    assert "official_audit_result_claim_denied" in decision.failure_reasons
    assert "court_admissible_claim_denied" in decision.failure_reasons
    assert "proof_of_compliance_claim_denied" in decision.failure_reasons
    assert "proof_control_effective_claim_denied" in decision.failure_reasons
    assert "proof_organization_safe_claim_denied" in decision.failure_reasons


def test_simulation_does_not_mutate_input() -> None:
    request = _request(
        fallback_expectation={
            "fallback_available": True,
            "fallback_type": "retry",
            "fallback_is_success": True,
            "timeout_projection_possible": True,
        },
        provider_interstitial_risk={
            "provider": "google",
            "known_risk": "google_sorry_bot_challenge",
            "bypass_allowed": True,
            "fallback_allowed": False,
        },
    )
    before = deepcopy(request)

    decision = build_tool_simulation(request)

    assert request == before
    assert decision.result is not None
    assert decision.result.fallback_expectation["fallback_is_success"] is False
    assert decision.result.provider_interstitial_risk["bypass_allowed"] is False


def test_mission_control_can_consume_simulation_metadata() -> None:
    simulation = build_tool_simulation(
        _request(
            normalized_intent="search_web",
            proposed_tool="search_web",
            tool_category="browser_tool",
            capability_category="browser_search",
            risk_tier="browser_search",
            search_provider="google",
            query="Aegis runtime",
            evidence_expectation_hint=[
                "browser_url_verification_expected",
                "provider_interstitial_check_expected",
            ],
            verifier_expectation_hint={
                "verifier_required": True,
                "verifier_name": "browser-url-gate/1",
                "verifier_postcondition": "URL matches expected provider",
                "verifier_failure_modes": ["provider_bot_challenge"],
                "verifier_success_required_for_completion": True,
            },
        )
    )

    mission_request = mission_control_input_from_simulation(simulation.result)
    mission_decision = build_mission_control_preview(mission_request)

    assert mission_decision.validation_status == "review_ready"
    assert mission_decision.preview_contract is not None
    assert mission_decision.preview_contract.execution_permission == "not_granted_by_mission_control"
    assert mission_decision.preview_contract.runtime_dispatch_allowed is False
    assert mission_decision.preview_contract.verifier_success is False
    assert mission_decision.preview_contract.search_provider == "google"
