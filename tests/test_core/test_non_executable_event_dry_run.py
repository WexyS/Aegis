from __future__ import annotations

from typing import Any

import pytest

from aegis.core.approval_semantics import DecisionStatus
from aegis.core.constants import RiskLevel
from aegis.core.guard_policy import GuardDecision, classify_intent_risk
from aegis.core.non_executable_event_dry_run import build_non_executable_runtime_events
from aegis.core.non_executable_projection import reconstruct_non_executable_decision_from_journal
from aegis.core.protocol import ProtocolEventType, create_event, reset_sequence_for_testing


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
        {"path": "scratch/dry-run.txt", "content": "hello"},
        {
            "command_id": "cmd-approval",
            "trace_id": "trace-approval",
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


def _events(decision: GuardDecision, *, starting_sequence_num: int = 25):
    return build_non_executable_runtime_events(
        decision,
        command_id="cmd-dry-run",
        trace_id="trace-dry-run",
        causation_id="classification-event",
        starting_sequence_num=starting_sequence_num,
        timestamp_ms=123456,
    )


def _journal_entries_from_runtime_events(events) -> list[dict[str, Any]]:
    return [
        {
            "event_type": event.type,
            "sequence_num": event.sequence_num,
            "payload": event.payload,
        }
        for event in events
    ]


def _assert_common_runtime_event_contract(events, expected_types: list[str]) -> None:
    assert [event.type for event in events] == expected_types
    assert [event.type for event in events] == [ProtocolEventType(event.type).value for event in events]
    assert set(expected_types).isdisjoint(EXECUTION_EVENT_TYPES)
    assert [event.sequence_num for event in events] == sorted(event.sequence_num for event in events)
    assert [event.sequence_num for event in events] == list(range(events[0].sequence_num, events[0].sequence_num + len(events)))
    assert all(event.trace_id == "trace-dry-run" for event in events)
    assert all(event.causation_id == "classification-event" for event in events)
    assert all(event.timestamp == 123456 for event in events)
    assert all(event.source == "guard" for event in events)

    for event in events:
        payload = event.payload
        assert payload["command_id"] == "cmd-dry-run"
        assert payload["trace_id"] == "trace-dry-run"
        assert payload["not_executed"] is True
        assert payload["decision_status"] in {
            DecisionStatus.APPROVAL_REQUIRED.value,
            DecisionStatus.CLARIFICATION_REQUIRED.value,
            DecisionStatus.BLOCKED.value,
        }
        assert payload["risk_level"]
        assert payload["policy_rule"]
        assert payload["reason"]
        _assert_no_fake_execution(event.to_dict())


def _assert_no_fake_execution(value: Any) -> None:
    if isinstance(value, dict):
        assert "execution_evidence" not in value
        assert value.get("verified") is not True
        assert value.get("success") is not True
        assert value.get("action_started") is not True
        assert value.get("type") not in EXECUTION_EVENT_TYPES
        for nested in value.values():
            _assert_no_fake_execution(nested)
    elif isinstance(value, list):
        for nested in value:
            _assert_no_fake_execution(nested)


def test_approval_required_dry_run_builds_canonical_runtime_events_and_replays_pending() -> None:
    events = _events(_approval_decision())

    _assert_common_runtime_event_contract(events, APPROVAL_EVENTS)
    requested_payload = events[1].payload
    assert requested_payload["approval_id"] == "approval-policy"
    assert requested_payload["proposed_action"]["tool"] == "write_file"
    assert requested_payload["approval_status"] == "pending"
    assert requested_payload["required_confirmation_mode"] == "ui"
    assert requested_payload["approval_scope"] == "single_action"

    replay = reconstruct_non_executable_decision_from_journal(_journal_entries_from_runtime_events(events))
    assert replay["pending_approval"]["approval_id"] == "approval-policy"
    assert replay["pending_approval"]["approval_status"] == "pending"
    assert replay["command_status"] == "waiting_for_approval"
    assert replay["auto_approved"] is False
    assert replay["executed"] is False


def test_clarification_required_dry_run_builds_canonical_runtime_events_and_replays_pending() -> None:
    events = _events(_clarification_decision())

    _assert_common_runtime_event_contract(events, CLARIFICATION_EVENTS)
    requested_payload = events[1].payload
    assert requested_payload["clarification_id"] == "clarification-policy"
    assert requested_payload["ambiguity_type"] == "unresolved_click_target"
    assert requested_payload["question"]
    assert requested_payload["options"] == []
    assert requested_payload["blocked_until_answer"] is True

    replay = reconstruct_non_executable_decision_from_journal(_journal_entries_from_runtime_events(events))
    assert replay["pending_clarification"]["clarification_id"] == "clarification-policy"
    assert replay["pending_clarification"]["original_user_text"] == "click that button"
    assert replay["command_status"] == "waiting_for_clarification"
    assert replay["executed"] is False


def test_blocked_dry_run_builds_canonical_runtime_events_and_replays_terminal_blocked() -> None:
    events = _events(_blocked_decision())

    _assert_common_runtime_event_contract(events, BLOCKED_EVENTS)
    blocked_payload = events[1].payload
    assert blocked_payload["blocked_id"] == "blocked-policy"
    assert blocked_payload["source_intent"]["intent"] == "run_command"
    assert blocked_payload["risk_level"] == RiskLevel.CRITICAL.value
    assert blocked_payload["terminal_non_executed"] is True
    assert events[2].payload["command_status"] == "blocked"
    assert events[2].payload["terminal_non_executed"] is True

    replay = reconstruct_non_executable_decision_from_journal(_journal_entries_from_runtime_events(events))
    assert replay["last_blocked_action"]["blocked_id"] == "blocked-policy"
    assert replay["command_status"] == "blocked"
    assert replay["terminal_non_executed"] is True
    assert replay["executed"] is False


def test_generic_click_dry_run_stays_non_executable_and_preserves_quarantine_reason() -> None:
    events = _events(_clarification_decision())

    assert [event.type for event in events] == CLARIFICATION_EVENTS
    assert EXECUTION_EVENT_TYPES.isdisjoint({event.type for event in events})
    assert all("execution_evidence" not in event.payload for event in events)
    assert all(event.payload["not_executed"] is True for event in events)
    assert "generic click quarantine" in events[0].payload["reason"]
    assert "target resolution" in events[0].payload["reason"]
    assert "quarantined" in events[0].payload["policy_rule"]


@pytest.mark.parametrize(
    "decision",
    [
        classify_intent_risk("open_app", {"app": "notepad"}),
        GuardDecision(
            decision_status=DecisionStatus.UNVERIFIED,
            risk_level=RiskLevel.MEDIUM,
            reason="unverified represents an action that already ran",
            policy_rule="unverified.executed",
        ),
        GuardDecision(
            decision_status=DecisionStatus.FAILED,
            risk_level=RiskLevel.MEDIUM,
            reason="failed represents a hard execution failure",
            policy_rule="failed.executed",
        ),
        GuardDecision(
            decision_status=DecisionStatus.CANCELLED,
            risk_level=RiskLevel.LOW,
            reason="cancelled needs a separate future projection contract",
            policy_rule="cancelled.out_of_scope",
        ),
    ],
)
def test_dry_run_rejects_non_supported_decision_statuses(decision: GuardDecision) -> None:
    with pytest.raises(ValueError, match=decision.decision_status.value):
        _events(decision)


def test_dry_run_does_not_consume_global_runtime_sequence_counter() -> None:
    reset_sequence_for_testing()

    events = _events(_approval_decision(), starting_sequence_num=200)
    next_real_event = create_event(ProtocolEventType.SYSTEM_ONLINE, {})

    assert [event.sequence_num for event in events] == [200, 201, 202]
    assert next_real_event.sequence_num == 1


def test_dry_run_module_does_not_import_runtime_side_effect_boundaries() -> None:
    import aegis.core.non_executable_event_dry_run as dry_run

    forbidden_fragments = ("executor", "orchestrator", "event_bus", "journal", "tools", "ws_bridge")
    source_names = set(dry_run.build_non_executable_runtime_events.__code__.co_names)

    assert source_names.isdisjoint(forbidden_fragments)
