from __future__ import annotations

from aegis.core.mode_policy import get_mode_policy, list_mode_policies, mode_allows_execution_now


REQUIRED_MODES = {"safe", "balanced", "power", "yolo_lab"}


def test_all_four_modes_exist() -> None:
    policies = list_mode_policies()

    assert {policy["mode"] for policy in policies} == REQUIRED_MODES


def test_no_mode_allows_execution_now() -> None:
    for mode in REQUIRED_MODES:
        policy = get_mode_policy(mode)

        assert policy is not None
        assert mode_allows_execution_now(mode) is False
        assert policy["mode_allows_execution_now"] is False
        assert policy["current_execution_grant"] is False
        assert policy["runtime_dispatch_allowed"] is False


def test_safe_mode_blocks_external_and_execution_surfaces() -> None:
    policy = get_mode_policy("safe")

    assert policy is not None
    assert policy["memory_silent_write"] is False
    assert policy["external_api_allowed"] is False
    assert policy["tool_execution_allowed"] is False
    assert policy["agent_execution_allowed"] is False
    assert policy["workflow_execution_allowed"] is False
    assert policy["computer_control_allowed"] is False
    assert policy["filesystem_write_allowed"] is False
    assert policy["model_gateway_allowed"] is True
    assert "model_gateway_status_or_proposal_readiness_only" in policy["notes"]


def test_balanced_mode_requires_external_api_preview() -> None:
    policy = get_mode_policy("balanced")

    assert policy is not None
    assert policy["external_api_allowed"] is False
    assert policy["external_api_preview_required"] is True
    assert policy["approval_required_for_medium_risk"] is True
    assert policy["computer_control_allowed"] is False
    assert policy["filesystem_write_allowed"] is False


def test_power_mode_requires_approval_and_ledger_posture() -> None:
    policy = get_mode_policy("power")

    assert policy is not None
    assert policy["approval_required_for_medium_risk"] is True
    assert policy["approval_required_for_high_risk"] is True
    assert policy["activity_ledger_required"] is True
    assert policy["memory_ledger_required"] is True
    assert policy["post_run_report_required"] is True
    assert policy["current_execution_grant"] is False


def test_yolo_lab_requires_hard_safety_controls() -> None:
    policy = get_mode_policy("yolo_lab")

    assert policy is not None
    assert policy["display_name"] == "YOLO Lab"
    assert policy["kill_switch_required"] is True
    assert policy["session_timebox_required"] is True
    assert policy["activity_ledger_required"] is True
    assert policy["memory_ledger_required"] is True
    assert policy["post_run_report_required"] is True
    assert policy["tool_execution_allowed"] is False
    assert policy["agent_execution_allowed"] is False
    assert policy["workflow_execution_allowed"] is False
    assert policy["computer_control_allowed"] is False


def test_no_mode_policy_grants_authority_or_proof() -> None:
    for policy in list_mode_policies():
        assert policy["authority"] is False
        assert policy["evidence_created"] is False
        assert policy["verifier_success"] is False
        assert policy["approval_granted"] is False
        assert policy["approval_grant"] is False
        assert policy["capability_lease_granted"] is False
        assert policy["capability_grant"] is False
        assert policy["lease_grant"] is False
        assert policy["frontend_authority"] is False
