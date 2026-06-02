from __future__ import annotations

from copy import deepcopy

from aegis.core.mission_control import (
    MISSION_CONTROL_CONTRACT_VERSION,
    MISSION_CONTROL_EXECUTION_PERMISSION,
    build_mission_control_preview,
)


def _request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "request_id": "req-mission-1",
        "command_id": "cmd-mission-1",
        "raw_user_request": "read docs",
        "normalized_intent": "read_file",
        "route_kind": "filesystem",
        "proposed_action": "read docs/mission-control.md",
        "proposed_tool": "read_file",
        "affected_resources": ["docs/mission-control.md"],
        "risk_tier": "read_only",
        "capability_category": "local_file_read",
        "policy_decision_ref": "policy:read_file.path.ready",
        "policy_reason": "read-only file inspection",
        "approval_required": False,
        "approval_reason": "approval not required by policy",
        "lease_required": False,
        "evidence_expectation": ["policy_decision_ref_expected"],
        "verifier_expectation": {
            "verifier_required": False,
            "verifier_name": "",
            "verifier_postcondition": "not applicable for preview-only read proposal",
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
        "limitations": ["preview only"],
        "unknowns": [],
        "alternatives": ["ask for a narrower file path"],
        "operator_options": ["cancel", "request_dry_run_details"],
        "source_refs": ["policy:read_file.path.ready"],
    }
    request.update(overrides)
    return request


def test_valid_read_only_dry_run_preview_validates_as_non_authoritative() -> None:
    decision = build_mission_control_preview(_request())

    assert decision.contract_version == MISSION_CONTROL_CONTRACT_VERSION
    assert decision.validation_status == "review_ready"
    assert decision.failure_reasons == ()
    assert decision.preview_contract is not None
    assert decision.preview_contract.authority is False
    assert decision.preview_contract.runtime_dispatch_allowed is False
    assert decision.preview_contract.execution_permission == MISSION_CONTROL_EXECUTION_PERMISSION
    assert decision.preview_contract.approval_grant is False
    assert decision.preview_contract.capability_grant is False
    assert decision.preview_contract.lease_grant is False
    assert decision.preview_contract.evidence_provided_by_preview is False
    assert decision.preview_contract.verifier_success is False
    assert decision.preview_contract.mutation_performed is False
    assert decision.preview_contract.frontend_authority is False


def test_valid_browser_search_preview_includes_provider_evidence_and_verifier_expectations() -> None:
    decision = build_mission_control_preview(
        _request(
            raw_user_request="search Google for Aegis runtime",
            normalized_intent="search_web",
            route_kind="browser",
            proposed_action="search Google for Aegis runtime",
            proposed_tool="search_web",
            target_app="brave",
            search_provider="google",
            query="Aegis runtime",
            affected_resources=["https://www.google.com/search?q=Aegis+runtime"],
            risk_tier="browser_search",
            capability_category="browser_search",
            evidence_expectation=[
                "browser_url_verification_expected",
                "provider_interstitial_check_expected",
                "policy_decision_ref_expected",
            ],
            verifier_expectation={
                "verifier_required": True,
                "verifier_name": "browser-url-gate/1",
                "verifier_postcondition": "final URL and search query match provider expectation",
                "verifier_failure_modes": ["provider_bot_challenge", "url_mismatch"],
                "verifier_success_required_for_completion": True,
            },
            provider_interstitial_risk={
                "provider": "google",
                "known_risk": "google_sorry_bot_challenge",
                "bypass_allowed": False,
                "fallback_allowed": False,
            },
            operator_options=["approve_once", "deny", "request_safer_alternative"],
        )
    )

    assert decision.validation_status == "review_ready"
    assert decision.preview_contract is not None
    assert decision.preview_contract.search_provider == "google"
    assert "provider_interstitial_check_expected" in decision.preview_contract.evidence_expectation
    assert decision.preview_contract.verifier_expectation.verifier_name == "browser-url-gate/1"
    assert decision.preview_contract.provider_interstitial_risk["known_risk"] == "google_sorry_bot_challenge"
    assert decision.preview_contract.provider_interstitial_risk["bypass_allowed"] is False


def test_valid_app_launch_preview_includes_process_window_verifier_expectation() -> None:
    decision = build_mission_control_preview(
        _request(
            raw_user_request="open notepad",
            normalized_intent="open_app",
            route_kind="desktop_app",
            proposed_action="open Notepad",
            proposed_tool="open_app",
            target_app="notepad",
            affected_resources=["process:notepad"],
            risk_tier="app_launch",
            capability_category="app_launch",
            evidence_expectation=["process_window_verification_expected", "policy_decision_ref_expected"],
            verifier_expectation={
                "verifier_required": True,
                "verifier_name": "process-window-verifier/2",
                "verifier_postcondition": "Notepad process/window is observable",
                "verifier_failure_modes": ["process_missing", "window_missing"],
                "verifier_success_required_for_completion": True,
            },
        )
    )

    assert decision.validation_status == "review_ready"
    assert decision.preview_contract is not None
    assert decision.preview_contract.verifier_expectation.verifier_name == "process-window-verifier/2"
    assert "process_window_verification_expected" in decision.preview_contract.evidence_expectation


def test_high_risk_local_file_write_requires_affected_resources_and_evidence_expectation() -> None:
    decision = build_mission_control_preview(
        _request(
            normalized_intent="write_file",
            proposed_tool="write_file",
            risk_tier="local_file_write",
            capability_category="local_file_write",
            affected_resources=[],
            evidence_expectation=[],
            approval_required=True,
            rollback_status="backup_required",
        )
    )

    assert decision.validation_status == "failed_validation"
    assert "affected_resources_required_for_high_risk_preview" in decision.failure_reasons
    assert "evidence_expectation_required_for_high_risk_preview" in decision.failure_reasons


def test_destructive_action_with_unknown_rollback_is_blocked_invalid() -> None:
    decision = build_mission_control_preview(
        _request(
            normalized_intent="run_command",
            proposed_tool="run_command",
            proposed_action="delete system files",
            risk_tier="destructive_system_change",
            capability_category="destructive_system_change",
            affected_resources=["C:/Windows"],
            approval_required=True,
            evidence_expectation=["human_review_required"],
            rollback_status="unknown",
        )
    )

    assert decision.validation_status == "blocked"
    assert "destructive_action_requires_known_rollback_or_blocked_policy" in decision.failure_reasons


def test_unknown_risk_requires_operator_attention() -> None:
    decision = build_mission_control_preview(
        _request(
            normalized_intent="future_tool",
            proposed_tool="future_tool",
            risk_tier="unknown",
            capability_category="unknown",
            evidence_expectation=["unknown_evidence_expectation"],
            operator_options=["ask_clarification"],
        )
    )

    assert decision.validation_status == "operator_attention_required"
    assert decision.requires_operator_attention is True
    assert "unknown_risk_requires_operator_attention" in decision.failure_reasons


def test_authority_grant_and_runtime_dispatch_fields_rejected() -> None:
    decision = build_mission_control_preview(
        _request(
            authority=True,
            runtime_dispatch_allowed=True,
            approval_grant=True,
            capability_grant=True,
            lease_grant=True,
        )
    )

    assert "authority_must_be_false" in decision.failure_reasons
    assert "runtime_dispatch_not_allowed" in decision.failure_reasons
    assert "approval_grant_not_allowed" in decision.failure_reasons
    assert "capability_grant_not_allowed" in decision.failure_reasons
    assert "lease_grant_not_allowed" in decision.failure_reasons


def test_preview_cannot_claim_evidence_or_verifier_success() -> None:
    decision = build_mission_control_preview(
        _request(
            evidence_provided_by_preview=True,
            verifier_success=True,
            verified_success=True,
            success=True,
        )
    )

    assert decision.evidence_provided_by_preview is False
    assert decision.verifier_success is False
    assert "preview_cannot_provide_evidence" in decision.failure_reasons
    assert "preview_cannot_mark_verifier_success" in decision.failure_reasons
    assert "success_claim_denied" in decision.failure_reasons


def test_frontend_authority_rejected() -> None:
    decision = build_mission_control_preview(_request(frontend_authority=True))

    assert decision.frontend_authority is False
    assert "frontend_authority_not_allowed" in decision.failure_reasons


def test_external_api_write_pretending_read_only_rejected() -> None:
    decision = build_mission_control_preview(
        _request(
            normalized_intent="external_api_write",
            proposed_tool="external_api_write",
            risk_tier="read_only",
            capability_category="external_api_write",
        )
    )

    assert "external_api_write_cannot_be_read_only" in decision.failure_reasons
    assert "capability_risk_tier_mismatch" in decision.failure_reasons


def test_plugin_execution_pretending_read_only_rejected() -> None:
    decision = build_mission_control_preview(
        _request(
            normalized_intent="plugin_execution",
            proposed_tool="plugin_execution",
            risk_tier="read_only",
            capability_category="plugin_execution",
        )
    )

    assert "plugin_execution_cannot_be_read_only" in decision.failure_reasons
    assert "capability_risk_tier_mismatch" in decision.failure_reasons


def test_memory_write_pretending_read_only_rejected() -> None:
    decision = build_mission_control_preview(
        _request(
            normalized_intent="memory_write",
            proposed_tool="memory_write",
            risk_tier="read_only",
            capability_category="memory_write",
        )
    )

    assert "memory_write_cannot_be_read_only" in decision.failure_reasons
    assert "capability_risk_tier_mismatch" in decision.failure_reasons


def test_compliance_certification_wording_rejected() -> None:
    decision = build_mission_control_preview(
        _request(
            claims=[
                "This preview is proof of compliance",
                "Official audit result",
                "Court-admissible evidence",
                "Compliance certification",
            ]
        )
    )

    assert "proof_of_compliance_claim_denied" in decision.failure_reasons
    assert "official_audit_result_claim_denied" in decision.failure_reasons
    assert "court_admissible_claim_denied" in decision.failure_reasons
    assert "compliance_certification_claim_denied" in decision.failure_reasons


def test_policy_denied_cannot_be_overridden_by_preview() -> None:
    decision = build_mission_control_preview(
        _request(
            policy_decision_ref="policy:run_command.critical_pattern.blocked",
            policy_decision_status="blocked",
            policy_reason="critical command blocked by backend policy",
            approval_required=False,
            operator_options=["approve_once"],
        )
    )

    assert decision.validation_status == "blocked"
    assert "policy_denied_cannot_be_overridden_by_preview" in decision.failure_reasons
    assert decision.approval_grant is False


def test_approval_required_is_explanatory_only_not_approval_grant() -> None:
    decision = build_mission_control_preview(
        _request(
            approval_required=True,
            approval_reason="workspace write requires explicit approval",
            approval_grant=False,
            operator_options=["approve_once", "deny"],
        )
    )

    assert decision.validation_status == "review_ready"
    assert decision.preview_contract is not None
    assert decision.preview_contract.approval_required is True
    assert decision.preview_contract.approval_grant is False


def test_lease_candidate_is_proposal_only_not_lease_grant() -> None:
    decision = build_mission_control_preview(
        _request(
            lease_required=True,
            lease_scope="browser_search:google",
            lease_duration="10m",
            operator_options=["create_scoped_lease_candidate"],
        )
    )

    assert decision.validation_status == "review_ready"
    assert decision.preview_contract is not None
    assert decision.preview_contract.lease_required is True
    assert decision.preview_contract.lease_scope == "browser_search:google"
    assert decision.preview_contract.lease_grant is False


def test_timeout_fallback_expectation_cannot_claim_success() -> None:
    decision = build_mission_control_preview(
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

    assert "fallback_cannot_be_success" in decision.failure_reasons
    assert decision.preview_contract is not None
    assert decision.preview_contract.fallback_expectation["fallback_is_success"] is False


def test_provider_interstitial_warning_cannot_bypass_provider_challenge() -> None:
    decision = build_mission_control_preview(
        _request(
            normalized_intent="search_web",
            proposed_tool="search_web",
            route_kind="browser",
            risk_tier="browser_search",
            capability_category="browser_search",
            search_provider="google",
            evidence_expectation=["provider_interstitial_check_expected", "browser_url_verification_expected"],
            provider_interstitial_risk={
                "provider": "google",
                "known_risk": "google_sorry_bot_challenge",
                "bypass_allowed": True,
                "fallback_allowed": False,
            },
        )
    )

    assert "provider_interstitial_bypass_not_allowed" in decision.failure_reasons
    assert decision.preview_contract is not None
    assert decision.preview_contract.provider_interstitial_risk["bypass_allowed"] is False


def test_validation_does_not_mutate_input() -> None:
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

    decision = build_mission_control_preview(request)

    assert request == before
    assert decision.preview_contract is not None
    assert decision.preview_contract.fallback_expectation["fallback_is_success"] is False
    assert decision.preview_contract.provider_interstitial_risk["bypass_allowed"] is False


def test_no_image_model_or_tool_generation_is_used_or_required() -> None:
    decision = build_mission_control_preview(
        _request(
            requested_tools=[],
            model_calls_requested=[],
            image_generation_requested=False,
            screenshot_requested=False,
            visual_asset_requested=False,
        )
    )

    assert decision.validation_status == "review_ready"
    assert decision.preview_contract is not None
    assert decision.preview_contract.actions_performed == ()
    assert decision.preview_contract.image_generation_used is False
    assert decision.preview_contract.model_call_used is False
    assert decision.preview_contract.tool_call_used is False
    assert decision.preview_contract.screenshot_created is False
    assert decision.preview_contract.visual_asset_created is False
