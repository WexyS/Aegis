from __future__ import annotations

import pytest
from pydantic import ValidationError

from aegis.core.approval_semantics import (
    ApprovalRequest,
    ApprovalScope,
    ApprovalStatus,
    BlockedAction,
    ClarificationRequest,
    ConfirmationMode,
    DecisionStatus,
    ExpirationPolicy,
    ProposedAction,
    ReplayPolicy,
    SourceIntent,
    approval_implies_verified,
    can_transition_decision,
    is_approval_pending,
    is_blocked,
    is_executable_decision,
    is_terminal_non_executed,
    requires_user_input,
)
from aegis.core.constants import RiskLevel


def _source_intent(intent: str = "click") -> SourceIntent:
    return SourceIntent(
        intent=intent,
        raw_input="click that button",
        source="deterministic",
        confidence=1.0,
        metadata={"decomposition": "deterministic"},
    )


def _approval_request(**overrides) -> ApprovalRequest:
    data = {
        "approval_id": "approval-1",
        "command_id": "command-1",
        "trace_id": "trace-1",
        "span_id": "span-1",
        "action_id": "action-1",
        "source_intent": _source_intent("write_file"),
        "proposed_action": ProposedAction(
            tool="write_file",
            description="Write a file in the workspace",
            action_kind="mutation",
        ),
        "normalized_params": {"path": "scratch/a.txt", "content": "hello"},
        "risk_level": RiskLevel.MEDIUM,
        "reason": "workspace mutation requires approval",
        "evidence_refs": [],
        "expected_effect": "scratch/a.txt will contain the requested content",
        "possible_side_effects": ["file content changes"],
        "rollback_note": "Restore the previous file content from before-write evidence.",
        "expiration_policy": ExpirationPolicy(mode="command_lifetime"),
        "status": ApprovalStatus.PENDING,
        "required_confirmation_mode": ConfirmationMode.UI,
        "approval_scope": ApprovalScope.SINGLE_ACTION,
        "replay_policy": ReplayPolicy(replayable_decision=True),
    }
    data.update(overrides)
    return ApprovalRequest(**data)


def _clarification_request(**overrides) -> ClarificationRequest:
    data = {
        "clarification_id": "clarification-1",
        "command_id": "command-1",
        "trace_id": "trace-1",
        "original_user_text": "click that button",
        "ambiguity_type": "target",
        "question": "Which button should Aegis click?",
        "options": [],
        "recommended_default": None,
        "blocked_until_answer": True,
    }
    data.update(overrides)
    return ClarificationRequest(**data)


def _blocked_action(**overrides) -> BlockedAction:
    data = {
        "blocked_id": "blocked-1",
        "command_id": "command-1",
        "trace_id": "trace-1",
        "source_intent": _source_intent("run_command"),
        "reason": "critical action is blocked by policy",
        "policy_rule": "critical.system_mutation.blocked",
        "risk_level": RiskLevel.CRITICAL,
        "evidence_refs": [],
        "user_message": "This action is blocked.",
        "retry_allowed": False,
        "safe_alternatives": [],
    }
    data.update(overrides)
    return BlockedAction(**data)


def test_approval_request_pending_validates_and_is_non_executable() -> None:
    request = _approval_request(status=ApprovalStatus.PENDING)

    assert request.status == ApprovalStatus.PENDING
    assert is_approval_pending(request) is True
    assert requires_user_input(request) is True
    assert is_executable_decision(request) is False
    assert is_terminal_non_executed(request) is False


def test_approval_request_approved_validates_but_does_not_mean_verified() -> None:
    request = _approval_request(status=ApprovalStatus.APPROVED)

    assert request.status == ApprovalStatus.APPROVED
    assert is_approval_pending(request) is False
    assert is_executable_decision(request) is False
    assert approval_implies_verified(request) is False


@pytest.mark.parametrize("status", [ApprovalStatus.DENIED, ApprovalStatus.EXPIRED, ApprovalStatus.CANCELLED])
def test_approval_request_denied_expired_or_cancelled_is_terminal_non_executed(
    status: ApprovalStatus,
) -> None:
    request = _approval_request(status=status)

    assert is_terminal_non_executed(request) is True
    assert is_executable_decision(request) is False
    assert requires_user_input(request) is False


def test_clarification_request_validates_and_is_non_executable() -> None:
    request = _clarification_request()

    assert request.blocked_until_answer is True
    assert is_executable_decision(request) is False
    assert requires_user_input(request) is True
    assert is_terminal_non_executed(request) is False


def test_blocked_action_validates_and_is_terminal_non_executed() -> None:
    blocked = _blocked_action()

    assert is_blocked(blocked) is True
    assert is_executable_decision(blocked) is False
    assert is_terminal_non_executed(blocked) is True
    assert requires_user_input(blocked) is False


def test_blocked_cannot_be_treated_as_approval_required() -> None:
    assert can_transition_decision(DecisionStatus.BLOCKED, DecisionStatus.APPROVAL_REQUIRED) is False
    assert is_blocked(DecisionStatus.BLOCKED) is True
    assert requires_user_input(DecisionStatus.BLOCKED) is False


def test_invalid_risk_level_fails_validation() -> None:
    with pytest.raises(ValidationError):
        _approval_request(risk_level="spicy")


def test_invalid_approval_status_fails_validation() -> None:
    with pytest.raises(ValidationError):
        _approval_request(status="waiting")


def test_invalid_confirmation_mode_fails_validation() -> None:
    with pytest.raises(ValidationError):
        _approval_request(required_confirmation_mode="telepathy")


def test_helper_predicates_for_decision_statuses() -> None:
    assert is_executable_decision(DecisionStatus.READY) is True
    assert is_executable_decision(DecisionStatus.APPROVAL_REQUIRED) is False
    assert is_executable_decision(DecisionStatus.CLARIFICATION_REQUIRED) is False
    assert is_executable_decision(DecisionStatus.BLOCKED) is False
    assert requires_user_input(DecisionStatus.APPROVAL_REQUIRED) is True
    assert requires_user_input(DecisionStatus.CLARIFICATION_REQUIRED) is True
    assert is_terminal_non_executed(DecisionStatus.BLOCKED) is True
    assert is_terminal_non_executed(DecisionStatus.UNVERIFIED) is False
    assert is_terminal_non_executed(DecisionStatus.FAILED) is False
    assert is_terminal_non_executed(DecisionStatus.CANCELLED) is True


def test_generic_click_high_risk_can_be_represented_as_clarification_or_blocked_but_not_executable() -> None:
    clarification = _clarification_request(
        original_user_text="click that button",
        ambiguity_type="target",
        question="The click target is ambiguous. Which target should be resolved?",
    )
    blocked = _blocked_action(
        source_intent=_source_intent("click"),
        reason="generic click is quarantined until browser_click/desktop_click split exists",
        policy_rule="generic_click.quarantined",
        risk_level=RiskLevel.HIGH,
        user_message="Generic click is not executable.",
        retry_allowed=True,
    )

    assert is_executable_decision(clarification) is False
    assert is_executable_decision(blocked) is False
    assert requires_user_input(clarification) is True
    assert is_blocked(blocked) is True


def test_critical_risk_example_is_blocked_by_policy_representation() -> None:
    blocked = _blocked_action(
        source_intent=_source_intent("run_command"),
        reason="registry mutation is critical and blocked",
        policy_rule="critical.registry_mutation.blocked",
        risk_level=RiskLevel.CRITICAL,
        user_message="Registry mutation is blocked by policy.",
        retry_allowed=False,
    )

    assert blocked.risk_level == RiskLevel.CRITICAL
    assert is_blocked(blocked) is True
    assert is_terminal_non_executed(blocked) is True
    assert can_transition_decision(DecisionStatus.BLOCKED, DecisionStatus.APPROVAL_REQUIRED) is False
