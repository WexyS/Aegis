from __future__ import annotations

from types import SimpleNamespace

from aegis.core.approval_semantics import DecisionStatus
from aegis.core.guard_policy import classify_intent_risk
from aegis.core.policy_boundary import (
    POLICY_BOUNDARY_VERSION,
    POLICY_DISPATCHABLE_TOOL_NAMES,
    approval_resolution_can_resume,
    evaluate_policy_boundary,
    side_effects_missing_dispatch_contract,
)


def test_policy_boundary_allows_ready_decision_only_after_policy_classification() -> None:
    decision = classify_intent_risk("open_app", {"app": "notepad"})

    boundary = evaluate_policy_boundary(decision)

    assert decision.decision_status == DecisionStatus.READY
    assert boundary.boundary_version == POLICY_BOUNDARY_VERSION
    assert boundary.dispatch_allowed is True
    assert boundary.not_executed is False
    assert boundary.policy_rule == "open_app.known_app.ready"


def test_policy_boundary_blocks_clarification_even_if_approval_flag_is_present() -> None:
    decision = classify_intent_risk("click", {})

    boundary = evaluate_policy_boundary(decision, approval_granted=True)

    assert decision.decision_status == DecisionStatus.CLARIFICATION_REQUIRED
    assert boundary.dispatch_allowed is False
    assert boundary.requires_clarification is True
    assert boundary.not_executed is True


def test_policy_boundary_blocks_quarantined_click_approval_resume() -> None:
    decision = classify_intent_risk("click", {"x": 10, "y": 20})

    boundary = evaluate_policy_boundary(decision, approval_granted=True)

    assert decision.decision_status == DecisionStatus.APPROVAL_REQUIRED
    assert approval_resolution_can_resume(decision) is False
    assert boundary.dispatch_allowed is False
    assert boundary.resume_allowed is False
    assert boundary.not_executed is True


def test_policy_boundary_allows_resumable_approval_only_for_policy_eligible_actions() -> None:
    decision = classify_intent_risk("write_file", {"path": "scratch/a.txt", "content": "ok"})

    without_approval = evaluate_policy_boundary(decision, approval_granted=False)
    with_approval = evaluate_policy_boundary(decision, approval_granted=True)

    assert decision.decision_status == DecisionStatus.APPROVAL_REQUIRED
    assert approval_resolution_can_resume(decision) is True
    assert without_approval.dispatch_allowed is False
    assert with_approval.dispatch_allowed is True
    assert with_approval.resume_allowed is True


def test_policy_boundary_never_dispatches_blocked_decision() -> None:
    decision = classify_intent_risk("run_command", {"command": "reg delete HKCU\\Software\\Aegis /f"})

    boundary = evaluate_policy_boundary(decision, approval_granted=True)

    assert decision.decision_status == DecisionStatus.BLOCKED
    assert boundary.dispatch_allowed is False
    assert boundary.blocked is True
    assert boundary.not_executed is True


def test_side_effect_dispatch_contract_identifies_missing_dispatchable_tool() -> None:
    plan = [SimpleNamespace(intent="open_app"), SimpleNamespace(intent="read_file")]

    missing = side_effects_missing_dispatch_contract(
        plan,
        tool_spec_lookup=lambda name: SimpleNamespace(side_effecting=name == "open_app"),
        dispatchable_tool_names=POLICY_DISPATCHABLE_TOOL_NAMES - {"open_app"},
    )

    assert missing == ["open_app"]
