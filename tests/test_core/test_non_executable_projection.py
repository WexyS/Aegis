from __future__ import annotations

from typing import Any

import pytest

from aegis.core.approval_semantics import DecisionStatus
from aegis.core.constants import RiskLevel
from aegis.core.guard_policy import GuardDecision, classify_intent_risk
from aegis.core.non_executable_projection import (
    project_guard_decision_to_journal_entries,
    project_guard_decision_to_snapshot_patch,
    project_guard_decision_to_timeline_entry,
    reconstruct_non_executable_decision_from_journal,
)


def _assert_no_execution_projection(value: Any) -> None:
    if isinstance(value, dict):
        assert "execution_evidence" not in value
        assert "ACTION_STARTED" not in value.values()
        for nested in value.values():
            _assert_no_execution_projection(nested)
    elif isinstance(value, list):
        for nested in value:
            _assert_no_execution_projection(nested)


def _approval_decision() -> GuardDecision:
    return classify_intent_risk(
        "write_file",
        {"path": "scratch/a.txt", "content": "hello"},
        {
            "command_id": "cmd-approval",
            "trace_id": "trace-approval",
            "span_id": "span-approval",
            "action_id": "action-approval",
        },
    )


def _clarification_decision() -> GuardDecision:
    return classify_intent_risk(
        "click",
        {},
        {
            "command_id": "cmd-clarification",
            "trace_id": "trace-clarification",
            "raw_input": "click that button",
        },
    )


def _blocked_decision() -> GuardDecision:
    return classify_intent_risk(
        "run_command",
        {"command": "rm -rf /"},
        {
            "command_id": "cmd-blocked",
            "trace_id": "trace-blocked",
            "raw_input": "delete everything",
        },
    )


def test_approval_required_projects_journal_snapshot_timeline_and_replay() -> None:
    decision = _approval_decision()

    entries = project_guard_decision_to_journal_entries(
        decision,
        causation_id="parser-event-1",
        sequence_num=50,
    )
    snapshot = project_guard_decision_to_snapshot_patch(decision)
    timeline = project_guard_decision_to_timeline_entry(decision)
    replay = reconstruct_non_executable_decision_from_journal(entries)

    assert [entry["event_type"] for entry in entries] == [
        "COMMAND_CLASSIFIED",
        "APPROVAL_REQUESTED",
        "COMMAND_WAITING_FOR_APPROVAL",
    ]
    assert [entry["sequence_num"] for entry in entries] == [50, 51, 52]
    assert {entry["causation_id"] for entry in entries} == {"parser-event-1"}
    assert all(entry["command_id"] == "cmd-approval" for entry in entries)
    assert all(entry["trace_id"] == "trace-approval" for entry in entries)
    assert snapshot["pending_approval"]["approval_id"] == "approval-policy"
    assert snapshot["command_status"] == "waiting_for_approval"
    assert snapshot["last_guard_decision"]["decision_status"] == DecisionStatus.APPROVAL_REQUIRED.value
    assert timeline["kind"] == "approval_requested"
    assert timeline["status"] == DecisionStatus.APPROVAL_REQUIRED.value
    assert timeline["not_executed"] is True
    assert timeline["terminal"] is False
    assert replay["pending_approval"]["approval_id"] == "approval-policy"
    assert replay["command_status"] == "waiting_for_approval"
    assert replay["auto_approved"] is False
    assert replay["executed"] is False
    assert "ACTION_STARTED" not in [entry["event_type"] for entry in entries]
    _assert_no_execution_projection(entries)
    _assert_no_execution_projection(snapshot)
    _assert_no_execution_projection(timeline)


def test_clarification_required_projects_journal_snapshot_timeline_and_replay() -> None:
    decision = _clarification_decision()

    entries = project_guard_decision_to_journal_entries(
        decision,
        causation_id="parser-event-2",
        sequence_num=70,
    )
    snapshot = project_guard_decision_to_snapshot_patch(decision)
    timeline = project_guard_decision_to_timeline_entry(decision)
    replay = reconstruct_non_executable_decision_from_journal(entries)

    assert [entry["event_type"] for entry in entries] == [
        "COMMAND_CLASSIFIED",
        "CLARIFICATION_REQUESTED",
        "COMMAND_WAITING_FOR_CLARIFICATION",
    ]
    assert [entry["sequence_num"] for entry in entries] == [70, 71, 72]
    assert {entry["causation_id"] for entry in entries} == {"parser-event-2"}
    assert snapshot["pending_clarification"]["clarification_id"] == "clarification-policy"
    assert snapshot["command_status"] == "waiting_for_clarification"
    assert snapshot["last_guard_decision"]["decision_status"] == DecisionStatus.CLARIFICATION_REQUIRED.value
    assert timeline["kind"] == "clarification_requested"
    assert timeline["status"] == DecisionStatus.CLARIFICATION_REQUIRED.value
    assert timeline["not_executed"] is True
    assert timeline["question"]
    assert replay["pending_clarification"]["clarification_id"] == "clarification-policy"
    assert replay["command_status"] == "waiting_for_clarification"
    assert replay["executed"] is False
    assert "ACTION_STARTED" not in [entry["event_type"] for entry in entries]
    _assert_no_execution_projection(entries)
    _assert_no_execution_projection(snapshot)
    _assert_no_execution_projection(timeline)


def test_blocked_projects_terminal_non_executed_journal_snapshot_timeline_and_replay() -> None:
    decision = _blocked_decision()

    entries = project_guard_decision_to_journal_entries(
        decision,
        causation_id="parser-event-3",
        sequence_num=90,
    )
    snapshot = project_guard_decision_to_snapshot_patch(decision)
    timeline = project_guard_decision_to_timeline_entry(decision)
    replay = reconstruct_non_executable_decision_from_journal(entries)

    assert [entry["event_type"] for entry in entries] == [
        "COMMAND_CLASSIFIED",
        "ACTION_BLOCKED_BY_POLICY",
        "COMMAND_BLOCKED",
    ]
    assert [entry["sequence_num"] for entry in entries] == [90, 91, 92]
    assert snapshot["last_blocked_action"]["blocked_id"] == "blocked-policy"
    assert snapshot["command_status"] == "blocked"
    assert snapshot["terminal_non_executed"] is True
    assert snapshot["last_guard_decision"]["decision_status"] == DecisionStatus.BLOCKED.value
    assert timeline["kind"] == "blocked_by_policy"
    assert timeline["status"] == DecisionStatus.BLOCKED.value
    assert timeline["not_executed"] is True
    assert timeline["terminal"] is True
    assert timeline["terminal_non_executed"] is True
    assert replay["last_blocked_action"]["blocked_id"] == "blocked-policy"
    assert replay["terminal_non_executed"] is True
    assert replay["command_status"] == "blocked"
    assert replay["executed"] is False
    assert "ACTION_STARTED" not in [entry["event_type"] for entry in entries]
    _assert_no_execution_projection(entries)
    _assert_no_execution_projection(snapshot)
    _assert_no_execution_projection(timeline)


def test_generic_click_projection_is_non_executable_and_preserves_quarantine_reason() -> None:
    decision = _clarification_decision()

    entries = project_guard_decision_to_journal_entries(decision)
    snapshot = project_guard_decision_to_snapshot_patch(decision)
    timeline = project_guard_decision_to_timeline_entry(decision)

    assert decision.decision_status in {
        DecisionStatus.CLARIFICATION_REQUIRED,
        DecisionStatus.BLOCKED,
    }
    assert "generic click quarantine" in timeline["reason"]
    assert "target resolution" in timeline["reason"]
    assert snapshot["not_executed"] is True
    assert timeline["not_executed"] is True
    assert "ACTION_STARTED" not in [entry["event_type"] for entry in entries]
    _assert_no_execution_projection(entries)
    _assert_no_execution_projection(snapshot)
    _assert_no_execution_projection(timeline)


def test_replay_uses_sequence_order_not_timestamps() -> None:
    entries = project_guard_decision_to_journal_entries(_blocked_decision(), sequence_num=10)
    shuffled = [dict(entries[2], timestamp="2026-05-21T00:00:01Z"), dict(entries[0], timestamp="2026-05-21T00:00:03Z"), dict(entries[1], timestamp="2026-05-21T00:00:02Z")]

    replay = reconstruct_non_executable_decision_from_journal(shuffled)

    assert replay["journal_order"] == [
        "COMMAND_CLASSIFIED",
        "ACTION_BLOCKED_BY_POLICY",
        "COMMAND_BLOCKED",
    ]
    assert replay["command_status"] == "blocked"


def test_replay_preserves_input_journal_order_when_sequence_is_absent() -> None:
    entries = project_guard_decision_to_journal_entries(_clarification_decision())
    entries[0]["timestamp"] = "2026-05-21T00:00:03Z"
    entries[1]["timestamp"] = "2026-05-21T00:00:01Z"
    entries[2]["timestamp"] = "2026-05-21T00:00:02Z"

    replay = reconstruct_non_executable_decision_from_journal(entries)

    assert replay["journal_order"] == [
        "COMMAND_CLASSIFIED",
        "CLARIFICATION_REQUESTED",
        "COMMAND_WAITING_FOR_CLARIFICATION",
    ]
    assert replay["command_status"] == "waiting_for_clarification"


def test_ready_decision_is_rejected_by_non_executable_projection() -> None:
    ready = classify_intent_risk("open_app", {"app": "notepad"})

    with pytest.raises(ValueError, match="ready"):
        project_guard_decision_to_journal_entries(ready)
    with pytest.raises(ValueError, match="ready"):
        project_guard_decision_to_snapshot_patch(ready)
    with pytest.raises(ValueError, match="ready"):
        project_guard_decision_to_timeline_entry(ready)


@pytest.mark.parametrize("status", [DecisionStatus.UNVERIFIED, DecisionStatus.FAILED])
def test_executed_terminal_statuses_are_rejected_by_non_executable_projection(status: DecisionStatus) -> None:
    decision = GuardDecision(
        decision_status=status,
        risk_level=RiskLevel.MEDIUM,
        reason=f"{status.value} represents an executed or failed action path",
        policy_rule=f"{status.value}.not_non_executable",
    )

    with pytest.raises(ValueError, match=status.value):
        project_guard_decision_to_journal_entries(decision)
    with pytest.raises(ValueError, match=status.value):
        project_guard_decision_to_snapshot_patch(decision)
    with pytest.raises(ValueError, match=status.value):
        project_guard_decision_to_timeline_entry(decision)
