from __future__ import annotations

from aegis.core.approval_semantics import DecisionStatus
from aegis.core.constants import CommandStatus
from aegis.core.guard_policy import classify_intent_risk
from aegis.core.non_executable_runtime_adapter import build_non_executable_event_batch
from aegis.core.protocol import ProtocolEventType, RuntimeEvent, RuntimeState, create_event


def test_runtime_event_creation_is_canonical_sequence_source_for_live_events() -> None:
    first = create_event(ProtocolEventType.COMMAND_RECEIVED, {"text": "read README.md"})
    hydrated = RuntimeEvent.from_dict(first.to_dict())
    second = create_event(ProtocolEventType.INTENT_PARSED, {"intents": []})
    third = create_event(ProtocolEventType.PLAN_CREATED, {"steps": []})

    assert hydrated.sequence_num == first.sequence_num
    assert second.sequence_num == first.sequence_num + 1
    assert third.sequence_num == second.sequence_num + 1


def test_prebuilt_non_executable_batch_does_not_advance_live_sequence_counter() -> None:
    before = create_event(ProtocolEventType.COMMAND_RECEIVED, {"text": "click"})
    decision = classify_intent_risk(
        "click",
        {},
        {"command_id": "cmd-click", "trace_id": "trace-click", "original_user_text": "click"},
    )

    batch = build_non_executable_event_batch(
        decision,
        command_id="cmd-click",
        trace_id="trace-click",
        causation_id="span-click",
        starting_sequence_num=5000,
        span_id="span-click",
        action_id="action-click",
    )
    after = create_event(ProtocolEventType.PLAN_CREATED, {"steps": []})

    assert [event.sequence_num for event in batch.events] == [5000, 5001, 5002]
    assert after.sequence_num == before.sequence_num + 1


def test_command_lifecycle_has_clarification_waiting_without_runtime_fsm_state() -> None:
    assert CommandStatus.WAITING_FOR_CLARIFICATION.value == "waiting_for_clarification"
    assert CommandStatus.WAITING_FOR_CLARIFICATION not in {
        CommandStatus.EXECUTED,
        CommandStatus.FAILED,
        CommandStatus.BLOCKED,
    }
    assert "WAITING_FOR_CLARIFICATION" not in RuntimeState.__members__


def test_legacy_approval_required_and_new_approval_requested_remain_distinct() -> None:
    decision = classify_intent_risk(
        "write_file",
        {"path": "scratch/out.txt", "content": "x"},
        {"command_id": "cmd-approval", "trace_id": "trace-approval"},
    )
    batch = build_non_executable_event_batch(
        decision,
        command_id="cmd-approval",
        trace_id="trace-approval",
        causation_id="span-approval",
        starting_sequence_num=6000,
    )
    legacy = create_event(
        ProtocolEventType.APPROVAL_REQUIRED,
        {"command": {"command_id": "legacy-cmd", "status": CommandStatus.PENDING_APPROVAL.value}},
    )

    event_types = [event.type for event in batch.events]
    assert ProtocolEventType.APPROVAL_REQUIRED.value not in event_types
    assert ProtocolEventType.APPROVAL_REQUESTED.value in event_types
    assert legacy.type == ProtocolEventType.APPROVAL_REQUIRED.value
    assert "command" in legacy.payload
    assert all("approval_request" not in event.payload for event in [legacy])


def test_generic_click_policy_is_non_ready_before_default_wiring() -> None:
    decision = classify_intent_risk(
        "click",
        {},
        {"command_id": "cmd-click", "trace_id": "trace-click", "original_user_text": "click"},
    )

    assert decision.decision_status == DecisionStatus.CLARIFICATION_REQUIRED
    assert decision.requires_clarification is True
    assert "generic click quarantine" in decision.reason
    assert "target resolution" in decision.reason
