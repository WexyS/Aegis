from __future__ import annotations

from typing import Any

import pytest

from aegis.core.approval_semantics import DecisionStatus
from aegis.core.guard_policy import classify_intent_risk
from aegis.core.non_executable_projection import (
    project_guard_decision_to_journal_entries,
    project_guard_decision_to_snapshot_patch,
    project_guard_decision_to_timeline_entry,
    reconstruct_non_executable_decision_from_journal,
)


APPROVAL_EVENTS = [
    "COMMAND_CLASSIFIED",
    "APPROVAL_REQUESTED",
    "COMMAND_WAITING_FOR_APPROVAL",
]
CLARIFICATION_EVENTS = [
    "COMMAND_CLASSIFIED",
    "CLARIFICATION_REQUESTED",
    "COMMAND_WAITING_FOR_CLARIFICATION",
]
BLOCKED_EVENTS = [
    "COMMAND_CLASSIFIED",
    "ACTION_BLOCKED_BY_POLICY",
    "COMMAND_BLOCKED",
]
FORBIDDEN_NON_EXECUTABLE_EVENTS = {
    "ACTION_STARTED",
    "ACTION_COMPLETED",
    "ACTION_FAILED",
    "ACTION_CANCELLED",
}
COMMON_FIELDS = {
    "event_type",
    "command_id",
    "trace_id",
    "sequence_num",
    "causation_id",
    "decision_status",
    "risk_level",
    "policy_rule",
    "reason",
    "timestamp",
    "not_executed",
}


def _approval_decision():
    return classify_intent_risk(
        "write_file",
        {"path": "scratch/event-contract.txt", "content": "hello"},
        {"command_id": "cmd-contract", "trace_id": "trace-contract"},
    )


def _clarification_decision():
    return classify_intent_risk(
        "click",
        {},
        {
            "command_id": "cmd-click",
            "trace_id": "trace-click",
            "raw_input": "click that button",
        },
    )


def _blocked_decision():
    return classify_intent_risk(
        "run_command",
        {"command": "reg delete HKCU\\Software\\Aegis /f"},
        {
            "command_id": "cmd-block",
            "trace_id": "trace-block",
            "raw_input": "delete registry key",
        },
    )


def _entries(decision):
    return project_guard_decision_to_journal_entries(
        decision,
        causation_id="classification-1",
        sequence_num=100,
        timestamp=123456,
    )


def _assert_no_fake_execution(value: Any) -> None:
    if isinstance(value, dict):
        assert "execution_evidence" not in value
        assert value.get("verified") is not True
        assert value.get("success") is not True
        assert value.get("action_started") is not True
        for nested in value.values():
            _assert_no_fake_execution(nested)
    elif isinstance(value, list):
        for nested in value:
            _assert_no_fake_execution(nested)


def _assert_common_entry_contract(entries: list[dict[str, Any]], expected_events: list[str]) -> None:
    assert [entry["event_type"] for entry in entries] == expected_events
    assert [entry["type"] for entry in entries] == expected_events
    assert set(expected_events).isdisjoint(FORBIDDEN_NON_EXECUTABLE_EVENTS)
    assert [entry["sequence_num"] for entry in entries] == sorted(entry["sequence_num"] for entry in entries)
    assert all(entry["causation_id"] == "classification-1" for entry in entries)
    assert len({entry["trace_id"] for entry in entries}) == 1
    assert len({entry["command_id"] for entry in entries}) == 1
    for entry in entries:
        assert COMMON_FIELDS.issubset(entry)
        assert entry["timestamp"] == 123456
        assert entry["not_executed"] is True
        assert entry["event_type"] not in FORBIDDEN_NON_EXECUTABLE_EVENTS
        _assert_no_fake_execution(entry)


def test_approval_journal_event_contract_is_locked() -> None:
    decision = _approval_decision()
    entries = _entries(decision)

    _assert_common_entry_contract(entries, APPROVAL_EVENTS)
    payload = entries[1]["payload"]
    assert payload["approval_id"] == decision.approval_request.approval_id
    assert payload["proposed_action"]["tool"] == "write_file"
    assert payload["normalized_params"] == {"path": "scratch/event-contract.txt", "content": "hello"}
    assert payload["required_confirmation_mode"] == "ui"
    assert payload["approval_scope"] == "single_action"
    assert payload["expected_effect"]
    assert payload["possible_side_effects"] == ["filesystem content changes"]
    assert payload["rollback_note"]
    assert payload["evidence_refs"] == []
    assert payload["expires_at"] is None
    assert payload["approval_status"] == "pending"


def test_clarification_journal_event_contract_is_locked() -> None:
    decision = _clarification_decision()
    entries = _entries(decision)

    _assert_common_entry_contract(entries, CLARIFICATION_EVENTS)
    payload = entries[1]["payload"]
    assert payload["clarification_id"] == decision.clarification_request.clarification_id
    assert payload["original_user_text"] == "click that button"
    assert payload["ambiguity_type"] == "unresolved_click_target"
    assert payload["question"]
    assert payload["options"] == []
    assert payload["recommended_default"] is None
    assert payload["blocked_until_answer"] is True


def test_blocked_journal_event_contract_is_locked() -> None:
    decision = _blocked_decision()
    entries = _entries(decision)

    _assert_common_entry_contract(entries, BLOCKED_EVENTS)
    payload = entries[1]["payload"]
    assert payload["blocked_id"] == decision.blocked_action.blocked_id
    assert payload["source_intent"]["intent"] == "run_command"
    assert payload["policy_rule"] == "run_command.critical_pattern.blocked"
    assert payload["risk_level"] == "critical"
    assert payload["user_message"]
    assert payload["retry_allowed"] is False
    assert payload["safe_alternatives"] == [
        {
            "label": "Use a known test command",
            "command_hint": None,
            "reason": "Known test/build commands are lower risk than arbitrary shell commands.",
        }
    ]
    assert payload["terminal_non_executed"] is True


@pytest.mark.parametrize(
    ("decision_factory", "expected_status", "expected_status_value"),
    [
        (_approval_decision, "waiting_for_approval", DecisionStatus.APPROVAL_REQUIRED.value),
        (_clarification_decision, "waiting_for_clarification", DecisionStatus.CLARIFICATION_REQUIRED.value),
        (_blocked_decision, "blocked", DecisionStatus.BLOCKED.value),
    ],
)
def test_snapshot_contract_for_non_executable_decisions(
    decision_factory,
    expected_status: str,
    expected_status_value: str,
) -> None:
    patch = project_guard_decision_to_snapshot_patch(decision_factory())

    assert patch["command_status"] == expected_status
    assert patch["last_guard_decision"]["decision_status"] == expected_status_value
    assert patch["last_risk_level"] in {"medium", "high", "critical"}
    if expected_status == "waiting_for_approval":
        assert patch["pending_approval"] is not None
    elif expected_status == "waiting_for_clarification":
        assert patch["pending_clarification"] is not None
    else:
        assert patch["last_blocked_action"] is not None
        assert patch["terminal_non_executed"] is True
    _assert_no_fake_execution(patch)


@pytest.mark.parametrize(
    ("decision_factory", "expected_kind", "expected_status", "terminal"),
    [
        (_approval_decision, "approval_requested", DecisionStatus.APPROVAL_REQUIRED.value, False),
        (_clarification_decision, "clarification_requested", DecisionStatus.CLARIFICATION_REQUIRED.value, False),
        (_blocked_decision, "blocked_by_policy", DecisionStatus.BLOCKED.value, True),
    ],
)
def test_timeline_contract_for_non_executable_decisions(
    decision_factory,
    expected_kind: str,
    expected_status: str,
    terminal: bool,
) -> None:
    entry = project_guard_decision_to_timeline_entry(decision_factory())

    assert entry["kind"] == expected_kind
    assert entry["status"] == expected_status
    assert entry["not_executed"] is True
    assert entry["executed"] is False
    assert entry["terminal"] is terminal
    _assert_no_fake_execution(entry)


def test_replay_contract_reconstructs_non_executable_decisions_without_execution() -> None:
    approval_replay = reconstruct_non_executable_decision_from_journal(_entries(_approval_decision()))
    clarification_replay = reconstruct_non_executable_decision_from_journal(_entries(_clarification_decision()))
    blocked_replay = reconstruct_non_executable_decision_from_journal(_entries(_blocked_decision()))

    assert approval_replay["pending_approval"]["approval_status"] == "pending"
    assert approval_replay["auto_approved"] is False
    assert approval_replay["executed"] is False
    assert clarification_replay["pending_clarification"]["original_user_text"] == "click that button"
    assert clarification_replay["executed"] is False
    assert blocked_replay["last_blocked_action"]["risk_level"] == "critical"
    assert blocked_replay["terminal_non_executed"] is True
    assert blocked_replay["command_status"] == "blocked"
    assert blocked_replay["last_guard_decision"]["decision_status"] == DecisionStatus.BLOCKED.value
    assert "pending_approval" in blocked_replay and blocked_replay["pending_approval"] is None
    _assert_no_fake_execution(approval_replay)
    _assert_no_fake_execution(clarification_replay)
    _assert_no_fake_execution(blocked_replay)


def test_replay_uses_sequence_order_not_timestamp_order() -> None:
    entries = _entries(_blocked_decision())
    out_of_timestamp_order = [
        dict(entries[2], timestamp=1),
        dict(entries[0], timestamp=3),
        dict(entries[1], timestamp=2),
    ]

    replay = reconstruct_non_executable_decision_from_journal(out_of_timestamp_order)

    assert replay["journal_order"] == BLOCKED_EVENTS
    assert replay["command_status"] == "blocked"


def test_generic_click_contract_stays_non_executable() -> None:
    decision = _clarification_decision()
    entries = _entries(decision)
    snapshot = project_guard_decision_to_snapshot_patch(decision)
    timeline = project_guard_decision_to_timeline_entry(decision)

    assert decision.decision_status in {DecisionStatus.CLARIFICATION_REQUIRED, DecisionStatus.BLOCKED}
    assert "generic click quarantine" in decision.reason
    assert "target resolution" in decision.reason
    assert "quarantined" in decision.policy_rule
    assert [entry["event_type"] for entry in entries] == CLARIFICATION_EVENTS
    assert "ACTION_STARTED" not in [entry["event_type"] for entry in entries]
    assert snapshot["not_executed"] is True
    assert timeline["not_executed"] is True
    _assert_no_fake_execution(entries)
    _assert_no_fake_execution(snapshot)
    _assert_no_fake_execution(timeline)
