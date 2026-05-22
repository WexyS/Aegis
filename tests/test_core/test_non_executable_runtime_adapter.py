from __future__ import annotations

from typing import Any

import pytest

from aegis.core.approval_semantics import DecisionStatus
from aegis.core.constants import RiskLevel
from aegis.core.guard_policy import GuardDecision, classify_intent_risk
from aegis.core.non_executable_runtime_adapter import (
    COMMAND_STATUS_REPRESENTATION_NOTE,
    append_non_executable_decision_events_dry,
    build_non_executable_event_batch,
    project_non_executable_events_to_action_timeline,
    project_non_executable_events_to_snapshot,
    runtime_events_to_journal_entries,
)
from aegis.core.protocol import ProtocolEventType, RuntimeEvent, create_event, reset_sequence_for_testing


APPROVAL_EVENTS = [
    ProtocolEventType.COMMAND_CLASSIFIED.value,
    ProtocolEventType.APPROVAL_REQUESTED.value,
    ProtocolEventType.COMMAND_WAITING_FOR_APPROVAL.value,
]
CLARIFICATION_EVENTS = [
    ProtocolEventType.COMMAND_CLASSIFIED.value,
    ProtocolEventType.CLARIFICATION_REQUESTED.value,
    ProtocolEventType.COMMAND_WAITING_FOR_CLARIFICATION.value,
]
BLOCKED_EVENTS = [
    ProtocolEventType.COMMAND_CLASSIFIED.value,
    ProtocolEventType.ACTION_BLOCKED_BY_POLICY.value,
    ProtocolEventType.COMMAND_BLOCKED.value,
]
EXECUTION_EVENT_TYPES = {
    ProtocolEventType.ACTION_STARTED.value,
    ProtocolEventType.ACTION_COMPLETED.value,
    ProtocolEventType.ACTION_FAILED.value,
    "ACTION_CANCELLED",
}


def _approval_decision() -> GuardDecision:
    return classify_intent_risk(
        "write_file",
        {"path": "scratch/runtime-adapter.txt", "content": "hello"},
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
            "command_id": "cmd-click",
            "trace_id": "trace-click",
            "raw_input": "click that button",
        },
    )


def _blocked_decision() -> GuardDecision:
    return classify_intent_risk(
        "run_command",
        {"command": "reg delete HKCU\\Software\\Aegis /f"},
        {
            "command_id": "cmd-blocked",
            "trace_id": "trace-blocked",
            "raw_input": "delete registry key",
        },
    )


def _batch(decision: GuardDecision, *, starting_sequence_num: int = 300):
    return build_non_executable_event_batch(
        decision,
        command_id="cmd-runtime",
        trace_id="trace-runtime",
        causation_id="caused-by-parser",
        starting_sequence_num=starting_sequence_num,
        timestamp_ms=987654,
        span_id="span-runtime",
        action_id="action-runtime",
    )


def _assert_common_batch_contract(batch, expected_types: list[str]) -> None:
    assert all(isinstance(event, RuntimeEvent) for event in batch.events)
    assert [event.type for event in batch.events] == expected_types
    assert ProtocolEventType.APPROVAL_REQUIRED.value not in expected_types
    assert EXECUTION_EVENT_TYPES.isdisjoint({event.type for event in batch.events})
    assert [event.sequence_num for event in batch.events] == list(
        range(batch.events[0].sequence_num, batch.events[0].sequence_num + len(batch.events))
    )
    assert all(event.trace_id == "trace-runtime" for event in batch.events)
    assert all(event.causation_id == "caused-by-parser" for event in batch.events)
    assert all(event.span_id == "span-runtime" for event in batch.events)
    assert all(event.timestamp == 987654 for event in batch.events)
    assert all(event.source == "guard" for event in batch.events)

    for event in batch.events:
        payload = event.payload
        assert payload["command_id"] == "cmd-runtime"
        assert payload["trace_id"] == "trace-runtime"
        assert payload["action_id"] == "action-runtime"
        assert payload["not_executed"] is True
        assert payload["decision_status"] in {
            DecisionStatus.APPROVAL_REQUIRED.value,
            DecisionStatus.CLARIFICATION_REQUIRED.value,
            DecisionStatus.BLOCKED.value,
        }
        assert payload["risk_level"]
        assert payload["policy_rule"]
        assert payload["reason"]
        _assert_no_execution_shape(event.to_dict())

    _assert_no_execution_shape(batch.snapshot_patch)
    _assert_no_execution_shape(batch.action_timeline_entries)
    assert batch.command_status_representation_note == COMMAND_STATUS_REPRESENTATION_NOTE


def _assert_no_execution_shape(value: Any) -> None:
    if isinstance(value, dict):
        assert "execution_evidence" not in value
        assert value.get("verified") is not True
        assert value.get("success") is not True
        assert value.get("action_started") is not True
        assert value.get("type") not in EXECUTION_EVENT_TYPES
        for nested in value.values():
            _assert_no_execution_shape(nested)
    elif isinstance(value, list):
        for nested in value:
            _assert_no_execution_shape(nested)


def test_approval_required_adapter_batch_projects_runtime_contract() -> None:
    batch = _batch(_approval_decision())

    _assert_common_batch_contract(batch, APPROVAL_EVENTS)
    assert batch.snapshot_patch["pending_approval"]["approval_id"] == "approval-policy"
    assert batch.snapshot_patch["command_status"] == "waiting_for_approval"
    assert batch.action_timeline_entries == project_non_executable_events_to_action_timeline(batch.events)
    assert batch.action_timeline_entries[0]["kind"] == "approval_requested"
    assert batch.action_timeline_entries[0]["status"] == DecisionStatus.APPROVAL_REQUIRED.value
    assert batch.action_timeline_entries[0]["not_executed"] is True
    assert batch.action_timeline_entries[0]["terminal"] is False
    assert batch.replay_state["pending_approval"]["approval_id"] == "approval-policy"
    assert batch.replay_state["auto_approved"] is False
    assert batch.replay_state["executed"] is False


def test_clarification_required_adapter_batch_projects_runtime_contract() -> None:
    batch = _batch(_clarification_decision())

    _assert_common_batch_contract(batch, CLARIFICATION_EVENTS)
    assert batch.snapshot_patch["pending_clarification"]["clarification_id"] == "clarification-policy"
    assert batch.snapshot_patch["command_status"] == "waiting_for_clarification"
    assert "waiting_for_clarification" in batch.command_status_representation_note
    assert batch.action_timeline_entries[0]["kind"] == "clarification_requested"
    assert batch.action_timeline_entries[0]["status"] == DecisionStatus.CLARIFICATION_REQUIRED.value
    assert batch.action_timeline_entries[0]["question"]
    assert batch.replay_state["pending_clarification"]["clarification_id"] == "clarification-policy"
    assert batch.replay_state["command_status"] == "waiting_for_clarification"
    assert batch.replay_state["executed"] is False


def test_blocked_adapter_batch_projects_terminal_non_executed_contract() -> None:
    batch = _batch(_blocked_decision())

    _assert_common_batch_contract(batch, BLOCKED_EVENTS)
    assert batch.snapshot_patch["last_blocked_action"]["blocked_id"] == "blocked-policy"
    assert batch.snapshot_patch["command_status"] == "blocked"
    assert batch.snapshot_patch["terminal_non_executed"] is True
    assert batch.action_timeline_entries[0]["kind"] == "blocked_by_policy"
    assert batch.action_timeline_entries[0]["status"] == DecisionStatus.BLOCKED.value
    assert batch.action_timeline_entries[0]["terminal"] is True
    assert batch.action_timeline_entries[0]["terminal_non_executed"] is True
    assert batch.replay_state["last_blocked_action"]["blocked_id"] == "blocked-policy"
    assert batch.replay_state["terminal_non_executed"] is True
    assert batch.replay_state["executed"] is False


def test_projection_from_runtime_events_reconstructs_snapshot_without_execution() -> None:
    batch = _batch(_approval_decision())

    snapshot = project_non_executable_events_to_snapshot(batch.events)

    assert snapshot["pending_approval"]["approval_id"] == "approval-policy"
    assert snapshot["pending_clarification"] is None
    assert snapshot["last_blocked_action"] is None
    assert snapshot["command_status"] == "waiting_for_approval"
    assert snapshot["not_executed"] is True
    assert snapshot["executed"] is False
    _assert_no_execution_shape(snapshot)


def test_dry_append_helper_only_appends_to_in_memory_event_log() -> None:
    batch = _batch(_approval_decision())
    event_log: list[RuntimeEvent] = []

    returned = append_non_executable_decision_events_dry(batch, event_log=event_log)

    assert returned is event_log
    assert event_log == batch.events
    assert [event.type for event in event_log] == APPROVAL_EVENTS
    assert all(event.payload["not_executed"] is True for event in event_log)
    assert all("execution_evidence" not in event.payload for event in event_log)


def test_replay_and_projection_use_sequence_order_before_timestamp_order() -> None:
    batch = _batch(_blocked_decision(), starting_sequence_num=500)
    events = [event.to_dict() for event in batch.events]
    events[0]["timestamp"] = 30
    events[1]["timestamp"] = 10
    events[2]["timestamp"] = 20
    shuffled = [events[2], events[0], events[1]]

    snapshot = project_non_executable_events_to_snapshot(shuffled)
    timeline = project_non_executable_events_to_action_timeline(shuffled)
    replay_entries = runtime_events_to_journal_entries(shuffled)

    assert [entry["event_type"] for entry in sorted(replay_entries, key=lambda item: item["sequence_num"])] == BLOCKED_EVENTS
    assert snapshot["command_status"] == "blocked"
    assert snapshot["terminal_non_executed"] is True
    assert timeline[0]["kind"] == "blocked_by_policy"
    assert timeline[0]["sequence_num"] == 501


def test_generic_click_adapter_stays_non_executable_and_preserves_quarantine_text() -> None:
    batch = _batch(_clarification_decision())

    assert [event.type for event in batch.events] == CLARIFICATION_EVENTS
    assert all("execution_evidence" not in event.payload for event in batch.events)
    assert all(event.payload["not_executed"] is True for event in batch.events)
    assert "generic click quarantine" in batch.events[0].payload["reason"]
    assert "target resolution" in batch.events[0].payload["reason"]
    assert "quarantined" in batch.events[0].payload["policy_rule"]
    assert batch.action_timeline_entries[0]["kind"] == "clarification_requested"


@pytest.mark.parametrize(
    "decision",
    [
        classify_intent_risk("open_app", {"app": "notepad"}),
        GuardDecision(
            decision_status=DecisionStatus.UNVERIFIED,
            risk_level=RiskLevel.MEDIUM,
            reason="unverified means execution already happened",
            policy_rule="unverified.executed",
        ),
        GuardDecision(
            decision_status=DecisionStatus.FAILED,
            risk_level=RiskLevel.MEDIUM,
            reason="failed belongs to execution failure handling",
            policy_rule="failed.executed",
        ),
        GuardDecision(
            decision_status=DecisionStatus.CANCELLED,
            risk_level=RiskLevel.LOW,
            reason="cancelled needs a separate future lifecycle contract",
            policy_rule="cancelled.out_of_scope",
        ),
    ],
)
def test_adapter_rejects_non_supported_decision_statuses(decision: GuardDecision) -> None:
    with pytest.raises(ValueError, match=decision.decision_status.value):
        _batch(decision)


def test_adapter_does_not_emit_legacy_approval_required_or_execution_events() -> None:
    for decision in (_approval_decision(), _clarification_decision(), _blocked_decision()):
        batch = _batch(decision)
        emitted = {event.type for event in batch.events}

        assert ProtocolEventType.APPROVAL_REQUIRED.value not in emitted
        assert EXECUTION_EVENT_TYPES.isdisjoint(emitted)


def test_adapter_does_not_consume_global_runtime_sequence_counter() -> None:
    reset_sequence_for_testing()

    batch = _batch(_approval_decision(), starting_sequence_num=900)
    next_real_event = create_event(ProtocolEventType.SYSTEM_ONLINE, {})

    assert [event.sequence_num for event in batch.events] == [900, 901, 902]
    assert next_real_event.sequence_num == 1


def test_adapter_module_does_not_reference_runtime_execution_boundaries() -> None:
    import aegis.core.non_executable_runtime_adapter as adapter

    forbidden_fragments = {"executor", "orchestrator", "tools", "ws_bridge", "sio"}
    names = set(adapter.build_non_executable_event_batch.__code__.co_names)

    assert names.isdisjoint(forbidden_fragments)
