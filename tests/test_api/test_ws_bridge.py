from __future__ import annotations

import asyncio

import pytest

from aegis.api import ws_bridge
from aegis.core.constants import RiskLevel
from aegis.core.commands import get_approval_manager
from aegis.core.action_timeline import project_action_timeline
from aegis.core.guard_policy import GuardDecision, classify_intent_risk
from aegis.core.non_executable_runtime_adapter import (
    build_non_executable_event_batch,
    project_non_executable_events_to_snapshot,
    runtime_events_to_journal_entries,
)
from aegis.core.approval_semantics import DecisionStatus
from aegis.core.protocol import ProtocolEventType, RuntimeEvent, create_event, reset_sequence_for_testing
from aegis.core.schemas import ExecutionEvidence


@pytest.mark.asyncio
async def test_action_completed_event_carries_execution_evidence(monkeypatch) -> None:
    emitted: list[tuple[ProtocolEventType, dict]] = []

    async def fake_emit_event(event_type, payload, **kwargs):
        emitted.append((event_type, payload))

    monkeypatch.setattr(ws_bridge, "emit_event", fake_emit_event)
    evidence = ExecutionEvidence(
        action="open_app",
        target="steam",
        target_type="application",
        method="launch",
        verification_state="verified",
        started_at_ms=1,
        completed_at_ms=2,
        process_name="steam.exe",
        pids=[4242],
        process_alive=True,
    )

    await ws_bridge.emit_action_completed(
        action_id="action-1",
        success=True,
        latency_ms=12.5,
        trace_id="11111111-1111-4111-8111-111111111111",
        retries=1,
        execution_evidence=evidence,
    )

    assert emitted[0][0] == ProtocolEventType.ACTION_COMPLETED
    payload = emitted[0][1]
    assert payload["execution_evidence"]["verification_state"] == "verified"
    assert payload["execution_evidence"]["process_name"] == "steam.exe"
    assert payload["execution_evidence"]["pids"] == [4242]
    assert payload["verification"]["passed"] is True
    assert payload["verification"]["method"] == "launch"
    assert emitted[1][0] == ProtocolEventType.VERIFICATION_PASSED
    verification_payload = emitted[1][1]
    assert verification_payload["action_id"] == "action-1"
    assert verification_payload["passed"] is True
    assert verification_payload["verification_state"] == "verified"
    assert verification_payload["execution_evidence"]["process_name"] == "steam.exe"


class NonExecutableMemoryJournal:
    def __init__(self) -> None:
        self.events: list[dict] = []

    def append(self, event: RuntimeEvent) -> RuntimeEvent:
        self.events.append(event.to_dict())
        return event

    def snapshot(self) -> dict:
        last = self.events[-1] if self.events else {}
        return {
            "event_count": len(self.events),
            "last_sequence_num": last.get("sequence_num", 0),
            "last_event_hash": last.get("event_hash"),
            "integrity_status": "in-memory",
        }

    def recent_events(self, limit: int | None = None) -> list[dict]:
        if limit is None:
            return list(self.events)
        return list(self.events)[-limit:]

    def events_after(self, sequence_num: int) -> list[dict]:
        return [event for event in self.events if int(event.get("sequence_num", 0)) > sequence_num]


def _approval_batch(starting_sequence_num: int = 100):
    return build_non_executable_event_batch(
        classify_intent_risk(
            "write_file",
            {"path": "scratch/ws-bridge.txt", "content": "hello"},
            {"command_id": "cmd-approval", "trace_id": "trace-approval"},
        ),
        command_id="cmd-approval",
        trace_id="trace-approval",
        causation_id="plan-event",
        starting_sequence_num=starting_sequence_num,
        timestamp_ms=1000,
    )


def _clarification_batch(starting_sequence_num: int = 200):
    return build_non_executable_event_batch(
        classify_intent_risk(
            "click",
            {},
            {"command_id": "cmd-click", "trace_id": "trace-click", "raw_input": "click that button"},
        ),
        command_id="cmd-click",
        trace_id="trace-click",
        causation_id="plan-event",
        starting_sequence_num=starting_sequence_num,
        timestamp_ms=2000,
    )


def _blocked_batch(starting_sequence_num: int = 300):
    return build_non_executable_event_batch(
        classify_intent_risk(
            "run_command",
            {"command": "rm -rf /"},
            {"command_id": "cmd-blocked", "trace_id": "trace-blocked"},
        ),
        command_id="cmd-blocked",
        trace_id="trace-blocked",
        causation_id="plan-event",
        starting_sequence_num=starting_sequence_num,
        timestamp_ms=3000,
    )


def _approval_decision():
    return classify_intent_risk(
        "write_file",
        {"path": "scratch/ws-bridge.txt", "content": "hello"},
        {"command_id": "cmd-approval", "trace_id": "trace-approval"},
    )


def _clarification_decision():
    return classify_intent_risk(
        "click",
        {},
        {"command_id": "cmd-click", "trace_id": "trace-click", "raw_input": "click that button"},
    )


def _blocked_decision():
    return classify_intent_risk(
        "run_command",
        {"command": "rm -rf /"},
        {"command_id": "cmd-blocked", "trace_id": "trace-blocked"},
    )


def _assert_no_execution_shape(value) -> None:
    if isinstance(value, dict):
        assert "execution_evidence" not in value
        assert value.get("success") is not True
        assert value.get("verified") is not True
        assert value.get("action_started") is not True
        assert value.get("type") not in {
            ProtocolEventType.ACTION_STARTED.value,
            ProtocolEventType.ACTION_COMPLETED.value,
            ProtocolEventType.ACTION_FAILED.value,
            "ACTION_CANCELLED",
        }
        for nested in value.values():
            _assert_no_execution_shape(nested)
    elif isinstance(value, list):
        for nested in value:
            _assert_no_execution_shape(nested)


@pytest.mark.asyncio
async def test_append_non_executable_decision_approval_allocates_live_sequence_and_fanout_after_append() -> None:
    reset_sequence_for_testing()
    journal = NonExecutableMemoryJournal()
    emitted: list[dict] = []

    async def fanout(event: RuntimeEvent) -> None:
        assert len(journal.events) == 3
        assert any(stored["event_id"] == event.event_id for stored in journal.events)
        emitted.append(event.to_dict())

    result = await ws_bridge.append_non_executable_decision(
        _approval_decision(),
        command_id="cmd-approval",
        trace_id="trace-approval",
        causation_id="plan-event",
        span_id="span-approval",
        action_id="action-approval",
        journal=journal,
        session_id="session-live-non-executable",
        fanout=fanout,
    )

    assert [event.type for event in result.events] == [
        ProtocolEventType.COMMAND_CLASSIFIED.value,
        ProtocolEventType.APPROVAL_REQUESTED.value,
        ProtocolEventType.COMMAND_WAITING_FOR_APPROVAL.value,
    ]
    assert [event["type"] for event in journal.events] == [event.type for event in result.events]
    assert emitted == journal.events
    assert [event.sequence_num for event in result.events] == [1, 2, 3]
    assert len({event.sequence_num for event in result.events}) == 3
    assert all(event.causation_id == "plan-event" for event in result.events)
    assert all(event.session_id == "session-live-non-executable" for event in result.events)
    assert all(event.payload["command_id"] == "cmd-approval" for event in result.events)
    assert all(event.payload["trace_id"] == "trace-approval" for event in result.events)
    assert all(event.payload["not_executed"] is True for event in result.events)
    assert all(event.type != ProtocolEventType.APPROVAL_REQUIRED.value for event in result.events)
    assert result.events[1].payload["approval_id"] == "approval-policy"
    assert result.events[1].payload["approval_status"] == "pending"
    assert result.events[1].payload["approval_scope"] == "single_action"
    assert result.events[1].payload["required_confirmation_mode"] == "ui"
    assert result.snapshot_patch["pending_approval"]["approval_id"] == "approval-policy"
    assert result.action_timeline_entries[0]["kind"] == "approval_requested"
    assert result.replay_state["command_status"] == "waiting_for_approval"
    _assert_no_execution_shape([event.to_dict() for event in result.events])


@pytest.mark.asyncio
async def test_append_non_executable_decision_clarification_payload_and_order() -> None:
    reset_sequence_for_testing()
    journal = NonExecutableMemoryJournal()

    result = await ws_bridge.append_non_executable_decision(
        _clarification_decision(),
        command_id="cmd-click",
        trace_id="trace-click",
        causation_id="plan-event",
        span_id="span-click",
        action_id="action-click",
        journal=journal,
    )

    assert [event.type for event in result.events] == [
        ProtocolEventType.COMMAND_CLASSIFIED.value,
        ProtocolEventType.CLARIFICATION_REQUESTED.value,
        ProtocolEventType.COMMAND_WAITING_FOR_CLARIFICATION.value,
    ]
    assert [event.sequence_num for event in result.events] == [1, 2, 3]
    clarification = result.events[1].payload
    waiting = result.events[2].payload
    assert clarification["clarification_id"] == "clarification-policy"
    assert clarification["ambiguity_type"] == "unresolved_click_target"
    assert "generic click quarantine" in clarification["reason"]
    assert "target resolution" in clarification["reason"]
    assert waiting["command_status"] == "waiting_for_clarification"
    assert result.snapshot_patch["pending_clarification"]["clarification_id"] == "clarification-policy"
    assert result.action_timeline_entries[0]["kind"] == "clarification_requested"
    _assert_no_execution_shape(journal.events)


@pytest.mark.asyncio
async def test_append_non_executable_decision_blocked_payload_and_terminal_projection() -> None:
    reset_sequence_for_testing()
    journal = NonExecutableMemoryJournal()

    result = await ws_bridge.append_non_executable_decision(
        _blocked_decision(),
        command_id="cmd-blocked",
        trace_id="trace-blocked",
        causation_id="plan-event",
        span_id="span-blocked",
        action_id="action-blocked",
        journal=journal,
    )

    assert [event.type for event in result.events] == [
        ProtocolEventType.COMMAND_CLASSIFIED.value,
        ProtocolEventType.ACTION_BLOCKED_BY_POLICY.value,
        ProtocolEventType.COMMAND_BLOCKED.value,
    ]
    assert [event.sequence_num for event in result.events] == [1, 2, 3]
    assert result.events[1].payload["blocked_id"] == "blocked-policy"
    assert result.events[1].payload["terminal_non_executed"] is True
    assert result.events[2].payload["command_status"] == "blocked"
    assert result.events[2].payload["terminal_non_executed"] is True
    assert result.snapshot_patch["last_blocked_action"]["blocked_id"] == "blocked-policy"
    assert result.snapshot_patch["terminal_non_executed"] is True
    assert result.action_timeline_entries[0]["kind"] == "blocked_by_policy"
    assert result.replay_state["command_status"] == "blocked"
    _assert_no_execution_shape(journal.events)


@pytest.mark.asyncio
async def test_append_non_executable_decision_repeated_calls_remain_unique_and_monotonic() -> None:
    reset_sequence_for_testing()
    journal = NonExecutableMemoryJournal()

    first = await ws_bridge.append_non_executable_decision(
        _approval_decision(),
        command_id="cmd-approval",
        trace_id="trace-approval",
        causation_id="approval-cause",
        journal=journal,
    )
    second = await ws_bridge.append_non_executable_decision(
        _clarification_decision(),
        command_id="cmd-click",
        trace_id="trace-click",
        causation_id="click-cause",
        journal=journal,
    )

    sequences = [event["sequence_num"] for event in journal.events]
    assert sequences == [1, 2, 3, 4, 5, 6]
    assert len(sequences) == len(set(sequences))
    assert [event.sequence_num for event in first.events] == [1, 2, 3]
    assert [event.sequence_num for event in second.events] == [4, 5, 6]
    assert journal.events_after(3) == journal.events[3:]


@pytest.mark.asyncio
async def test_append_non_executable_decision_generic_click_preserves_quarantine_reason() -> None:
    reset_sequence_for_testing()
    journal = NonExecutableMemoryJournal()

    result = await ws_bridge.append_non_executable_decision(
        _clarification_decision(),
        command_id="cmd-click",
        trace_id="trace-click",
        causation_id="click-cause",
        action_id="action-click",
        journal=journal,
    )

    assert ProtocolEventType.ACTION_STARTED.value not in [event.type for event in result.events]
    assert all("tool" not in event.payload for event in result.events)
    assert all("tool_run" not in event.payload for event in result.events)
    reasons = " ".join(str(event.payload.get("reason", "")) for event in result.events)
    policies = " ".join(str(event.payload.get("policy_rule", "")) for event in result.events)
    assert "generic click quarantine" in reasons
    assert "target resolution" in reasons
    assert "generic_click.quarantined" in policies
    assert [entry["kind"] for entry in result.action_timeline_entries] == ["clarification_requested"]
    _assert_no_execution_shape(journal.events)


@pytest.mark.asyncio
async def test_append_non_executable_decision_rejects_unsupported_decisions() -> None:
    journal = NonExecutableMemoryJournal()
    unsupported = [
        classify_intent_risk("open_app", {"app": "notepad"}),
        GuardDecision(
            decision_status=DecisionStatus.UNVERIFIED,
            risk_level=RiskLevel.MEDIUM,
            reason="unverified belongs to execution",
            policy_rule="unverified.executed",
        ),
        GuardDecision(
            decision_status=DecisionStatus.FAILED,
            risk_level=RiskLevel.MEDIUM,
            reason="failed belongs to execution",
            policy_rule="failed.executed",
        ),
        GuardDecision(
            decision_status=DecisionStatus.CANCELLED,
            risk_level=RiskLevel.LOW,
            reason="cancelled has separate lifecycle semantics",
            policy_rule="cancelled.out_of_scope",
        ),
    ]

    for decision in unsupported:
        with pytest.raises(ValueError, match=decision.decision_status.value):
            await ws_bridge.append_non_executable_decision(
                decision,
                command_id="cmd-negative",
                trace_id="trace-negative",
                journal=journal,
            )

    assert journal.events == []


@pytest.mark.asyncio
async def test_append_non_executable_decision_rejects_forbidden_projected_payload(monkeypatch) -> None:
    reset_sequence_for_testing()
    journal = NonExecutableMemoryJournal()
    emitted: list[RuntimeEvent] = []

    def fake_project(*args, **kwargs):
        return [
            {
                "event_type": ProtocolEventType.COMMAND_CLASSIFIED.value,
                "type": ProtocolEventType.COMMAND_CLASSIFIED.value,
                "timestamp": 0,
                "command_id": "cmd-bad",
                "trace_id": "trace-bad",
                "span_id": None,
                "sequence_num": None,
                "causation_id": "bad-cause",
                "decision_status": DecisionStatus.CLARIFICATION_REQUIRED.value,
                "risk_level": RiskLevel.HIGH.value,
                "policy_rule": "bad.execution_evidence",
                "reason": "bad",
                "payload": {
                    "command_id": "cmd-bad",
                    "trace_id": "trace-bad",
                    "decision_status": DecisionStatus.CLARIFICATION_REQUIRED.value,
                    "risk_level": RiskLevel.HIGH.value,
                    "policy_rule": "bad.execution_evidence",
                    "reason": "bad",
                    "not_executed": True,
                    "execution_evidence": {"fake": True},
                },
            }
        ]

    async def fanout(event: RuntimeEvent) -> None:
        emitted.append(event)

    monkeypatch.setattr(ws_bridge, "project_guard_decision_to_journal_entries", fake_project)

    with pytest.raises(ValueError, match="execution_evidence"):
        await ws_bridge.append_non_executable_decision(
            _clarification_decision(),
            command_id="cmd-bad",
            trace_id="trace-bad",
            causation_id="bad-cause",
            journal=journal,
            fanout=fanout,
        )

    assert journal.events == []
    assert emitted == []


def _patch_snapshot_dependencies(monkeypatch, *, commands_snapshot: dict | None = None) -> None:
    class FakeAuthority:
        def snapshot(self, journal_snapshot):
            return {"fsm_state": "IDLE", "last_event_sequence": journal_snapshot["last_sequence_num"]}

    class FakeApprovalManager:
        def snapshot(self):
            return commands_snapshot or {
                "records": [],
                "pending_approvals": [],
                "pending_clarifications": [],
                "active_command": None,
            }

    monkeypatch.setattr(ws_bridge, "_session_id", "session-non-executable")
    monkeypatch.setattr(ws_bridge, "get_runtime_authority", lambda *args, **kwargs: FakeAuthority())
    monkeypatch.setattr(ws_bridge, "get_approval_manager", lambda: FakeApprovalManager())
    monkeypatch.setattr(ws_bridge, "get_last_maintenance_scan", lambda: None)
    monkeypatch.setattr(ws_bridge, "get_app_registry_snapshot", lambda: {"entries": []})
    monkeypatch.setattr(ws_bridge, "get_tool_registry_snapshot", lambda: {"tools": []})


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("decision_factory", "command_id", "trace_id", "projection_key", "timeline_kind", "command_status"),
    [
        (
            _approval_decision,
            "cmd-approval",
            "trace-approval",
            "pending_approval",
            "approval_requested",
            "waiting_for_approval",
        ),
        (
            _clarification_decision,
            "cmd-click",
            "trace-click",
            "pending_clarification",
            "clarification_requested",
            "waiting_for_clarification",
        ),
        (
            _blocked_decision,
            "cmd-blocked",
            "trace-blocked",
            "last_blocked_action",
            "blocked_by_policy",
            "blocked",
        ),
    ],
)
async def test_runtime_snapshot_projects_non_executable_state_from_journal(
    monkeypatch,
    decision_factory,
    command_id: str,
    trace_id: str,
    projection_key: str,
    timeline_kind: str,
    command_status: str,
) -> None:
    reset_sequence_for_testing()
    journal = NonExecutableMemoryJournal()
    _patch_snapshot_dependencies(monkeypatch)

    await ws_bridge.append_non_executable_decision(
        decision_factory(),
        command_id=command_id,
        trace_id=trace_id,
        causation_id="guard-cause",
        span_id="guard-span",
        action_id="guard-action",
        journal=journal,
        session_id="session-non-executable",
    )

    journal_snapshot, runtime_snapshot = ws_bridge._build_runtime_snapshot(journal)
    projection = runtime_snapshot["non_executable_decisions"]
    timeline = runtime_snapshot["action_timeline"]

    assert journal_snapshot["last_sequence_num"] == 3
    assert projection[projection_key] is not None
    assert projection["command_status"] == command_status
    assert projection["not_executed"] is True
    assert projection["executed"] is False
    assert "execution_evidence" not in projection
    assert timeline
    assert timeline[0]["kind"] == timeline_kind
    assert timeline[0]["not_executed"] is True
    assert timeline[0].get("success") is not True
    assert timeline[0].get("verified") is not True
    assert "execution_evidence" not in timeline[0]
    assert ProtocolEventType.APPROVAL_REQUIRED.value not in [event["type"] for event in journal.events]
    if command_status == "blocked":
        assert projection["terminal_non_executed"] is True
        assert timeline[0]["terminal"] is True


@pytest.mark.asyncio
async def test_runtime_snapshot_projects_generic_click_as_pending_clarification(monkeypatch) -> None:
    reset_sequence_for_testing()
    journal = NonExecutableMemoryJournal()
    _patch_snapshot_dependencies(monkeypatch)

    await ws_bridge.append_non_executable_decision(
        _clarification_decision(),
        command_id="cmd-click",
        trace_id="trace-click",
        causation_id="click-cause",
        action_id="click-action",
        journal=journal,
        session_id="session-non-executable",
    )

    _, runtime_snapshot = ws_bridge._build_runtime_snapshot(journal)
    projection = runtime_snapshot["non_executable_decisions"]
    timeline = runtime_snapshot["action_timeline"]

    assert projection["pending_clarification"]["clarification_id"] == "clarification-policy"
    assert projection["command_status"] == "waiting_for_clarification"
    assert "generic click quarantine" in projection["pending_clarification"]["reason"]
    assert "target resolution" in projection["pending_clarification"]["reason"]
    assert timeline[0]["kind"] == "clarification_requested"
    assert ProtocolEventType.ACTION_STARTED.value not in [event["type"] for event in journal.events]
    _assert_no_execution_shape(journal.events)


@pytest.mark.asyncio
async def test_non_executable_batch_append_preserves_order_and_projection(monkeypatch) -> None:
    journal = NonExecutableMemoryJournal()
    batch = _approval_batch()

    monkeypatch.setattr(ws_bridge, "get_runtime_journal", lambda: (_ for _ in ()).throw(AssertionError("global journal used")))
    monkeypatch.setattr(ws_bridge, "get_runtime_authority", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("runtime authority mutated")))
    appended = await ws_bridge.append_non_executable_event_batch(
        batch.events,
        journal=journal,
        session_id="session-non-executable",
    )

    assert appended == batch.events
    assert [event["type"] for event in journal.events] == [
        ProtocolEventType.COMMAND_CLASSIFIED.value,
        ProtocolEventType.APPROVAL_REQUESTED.value,
        ProtocolEventType.COMMAND_WAITING_FOR_APPROVAL.value,
    ]
    assert [event["sequence_num"] for event in journal.events] == [100, 101, 102]
    assert len({event["sequence_num"] for event in journal.events}) == 3
    assert {event["causation_id"] for event in journal.events} == {"plan-event"}
    assert all(event["session_id"] == "session-non-executable" for event in journal.events)
    assert all(event["payload"]["command_id"] == "cmd-approval" for event in journal.events)
    assert all(event["payload"]["trace_id"] == "trace-approval" for event in journal.events)
    assert all(event["payload"]["not_executed"] is True for event in journal.events)
    _assert_no_execution_shape(journal.events)

    snapshot_patch = project_non_executable_events_to_snapshot(journal.recent_events())
    timeline = project_action_timeline(journal.recent_events(), session_id="session-non-executable")

    assert snapshot_patch["pending_approval"]["approval_id"] == "approval-policy"
    assert snapshot_patch["command_status"] == "waiting_for_approval"
    assert timeline[0]["kind"] == "approval_requested"
    assert timeline[0]["status"] == "approval_required"
    assert "execution_evidence" not in timeline[0]


@pytest.mark.asyncio
async def test_non_executable_batch_fanout_uses_canonical_order_and_payloads() -> None:
    journal = NonExecutableMemoryJournal()
    batch = _clarification_batch()
    emitted: list[dict] = []

    async def fanout(event: RuntimeEvent) -> None:
        emitted.append(event.to_dict())

    await ws_bridge.append_non_executable_event_batch(
        batch.events,
        journal=journal,
        session_id="session-non-executable",
        fanout=fanout,
    )

    assert [event["type"] for event in emitted] == [
        ProtocolEventType.COMMAND_CLASSIFIED.value,
        ProtocolEventType.CLARIFICATION_REQUESTED.value,
        ProtocolEventType.COMMAND_WAITING_FOR_CLARIFICATION.value,
    ]
    assert emitted == journal.events
    assert all(ProtocolEventType(event["type"]).value == event["type"] for event in emitted)
    assert all(event["payload"]["not_executed"] is True for event in emitted)
    assert "generic click quarantine" in emitted[0]["payload"]["reason"]
    assert "target resolution" in emitted[0]["payload"]["reason"]
    _assert_no_execution_shape(emitted)


@pytest.mark.asyncio
async def test_non_executable_blocked_batch_preserves_policy_vs_command_lifecycle_events() -> None:
    journal = NonExecutableMemoryJournal()
    batch = _blocked_batch()

    await ws_bridge.append_non_executable_event_batch(batch.events, journal=journal)

    policy_block = journal.events[1]
    command_block = journal.events[2]
    assert policy_block["type"] == ProtocolEventType.ACTION_BLOCKED_BY_POLICY.value
    assert policy_block["payload"]["blocked_id"] == "blocked-policy"
    assert policy_block["payload"]["terminal_non_executed"] is True
    assert command_block["type"] == ProtocolEventType.COMMAND_BLOCKED.value
    assert command_block["payload"]["command_status"] == "blocked"
    assert command_block["payload"]["terminal_non_executed"] is True


def test_non_executable_replay_uses_sequence_order_not_timestamp_order() -> None:
    batch = _blocked_batch(starting_sequence_num=500)
    events = [event.to_dict() for event in batch.events]
    events[0]["timestamp"] = 3000
    events[1]["timestamp"] = 1000
    events[2]["timestamp"] = 2000
    shuffled = [events[2], events[0], events[1]]

    entries = runtime_events_to_journal_entries(shuffled)
    timeline = project_action_timeline(shuffled)
    snapshot_patch = project_non_executable_events_to_snapshot(shuffled)

    assert [entry["event_type"] for entry in sorted(entries, key=lambda item: item["sequence_num"])] == [
        ProtocolEventType.COMMAND_CLASSIFIED.value,
        ProtocolEventType.ACTION_BLOCKED_BY_POLICY.value,
        ProtocolEventType.COMMAND_BLOCKED.value,
    ]
    assert timeline[0]["kind"] == "blocked_by_policy"
    assert timeline[0]["sequence_num"] == 501
    assert snapshot_patch["command_status"] == "blocked"
    assert snapshot_patch["terminal_non_executed"] is True


@pytest.mark.asyncio
async def test_non_executable_batch_rejects_execution_and_legacy_approval_events() -> None:
    journal = NonExecutableMemoryJournal()
    batch = _approval_batch()

    action_started = create_event(
        ProtocolEventType.ACTION_STARTED,
        {
            "command_id": "cmd-approval",
            "trace_id": "trace-approval",
            "decision_status": "approval_required",
            "risk_level": "medium",
            "policy_rule": "bad.action_started",
            "reason": "bad",
            "not_executed": True,
        },
        trace_id="trace-approval",
        causation_id="plan-event",
    )
    legacy_approval = create_event(
        ProtocolEventType.APPROVAL_REQUIRED,
        {
            "command_id": "cmd-approval",
            "trace_id": "trace-approval",
            "decision_status": "approval_required",
            "risk_level": "medium",
            "policy_rule": "legacy.approval_required",
            "reason": "bad",
            "not_executed": True,
        },
        trace_id="trace-approval",
        causation_id="plan-event",
    )
    with_evidence = RuntimeEvent.from_dict(batch.events[0].to_dict())
    with_evidence.payload = dict(with_evidence.payload)
    with_evidence.payload["execution_evidence"] = {"fake": True}

    with pytest.raises(ValueError, match="ACTION_STARTED"):
        await ws_bridge.append_non_executable_event_batch([action_started], journal=journal)
    with pytest.raises(ValueError, match="APPROVAL_REQUIRED"):
        await ws_bridge.append_non_executable_event_batch([legacy_approval], journal=journal)
    with pytest.raises(ValueError, match="execution_evidence"):
        await ws_bridge.append_non_executable_event_batch([with_evidence], journal=journal)

    assert journal.events == []


@pytest.mark.parametrize(
    "decision",
    [
        classify_intent_risk("open_app", {"app": "notepad"}),
        GuardDecision(
            decision_status=DecisionStatus.UNVERIFIED,
            risk_level=RiskLevel.MEDIUM,
            reason="unverified belongs to execution",
            policy_rule="unverified.executed",
        ),
        GuardDecision(
            decision_status=DecisionStatus.FAILED,
            risk_level=RiskLevel.MEDIUM,
            reason="failed belongs to execution",
            policy_rule="failed.executed",
        ),
        GuardDecision(
            decision_status=DecisionStatus.CANCELLED,
            risk_level=RiskLevel.LOW,
            reason="cancelled has separate lifecycle semantics",
            policy_rule="cancelled.out_of_scope",
        ),
    ],
)
def test_non_executable_adapter_rejects_unsupported_decisions_before_ws_bridge(decision) -> None:
    with pytest.raises(ValueError, match=decision.decision_status.value):
        build_non_executable_event_batch(
            decision,
            command_id="cmd-negative",
            trace_id="trace-negative",
            causation_id="plan-event",
        )


@pytest.mark.asyncio
async def test_emit_event_serializes_sequence_creation_with_journal_append(monkeypatch) -> None:
    reset_sequence_for_testing()
    appended = []

    class FakeJournal:
        def append(self, event):
            appended.append(event.to_dict())
            return event

    async def fake_to_thread(fn, *args, **kwargs):
        await asyncio.sleep(0)
        return fn(*args, **kwargs)

    monkeypatch.setattr(ws_bridge, "get_runtime_journal", lambda: FakeJournal())
    monkeypatch.setattr(ws_bridge.asyncio, "to_thread", fake_to_thread)
    monkeypatch.setattr(ws_bridge, "_connected_clients", set())

    await asyncio.gather(*[
        ws_bridge.emit_event(
            ProtocolEventType.TELEMETRY_UPDATE,
            {"index": index},
            source=ws_bridge.Component.SYSTEM,
        )
        for index in range(20)
    ])

    sequences = [event["sequence_num"] for event in appended]
    assert sequences == sorted(sequences)
    assert len(sequences) == len(set(sequences)) == 20


@pytest.mark.asyncio
async def test_approve_command_reports_queue_full_instead_of_silently_dropping(monkeypatch) -> None:
    manager = get_approval_manager()
    manager.reset_for_tests()
    record = manager.create_received("open notepad", command_id="cmd-queue-full")
    manager.register_pending(
        command_id=record.command_id,
        text=record.text,
        trace_id="11111111-1111-4111-8111-111111111111",
        risk_level=RiskLevel.MEDIUM,
        reason="approval required",
    )
    queue: asyncio.Queue = asyncio.Queue(maxsize=1)
    queue.put_nowait(ws_bridge.QueuedCommand("sid-existing", "busy", "auto", 0.0))
    emitted = []

    async def fake_emit_event(event_type, payload, **kwargs):
        emitted.append((event_type, payload, kwargs))

    monkeypatch.setattr(ws_bridge, "_command_queue", queue)
    monkeypatch.setattr(ws_bridge, "_command_queue_capacity", 1)
    monkeypatch.setattr(ws_bridge, "emit_event", fake_emit_event)

    await ws_bridge.approve_command("sid-1", {"command_id": "cmd-queue-full"})

    updated = manager.get("cmd-queue-full")
    assert updated is not None
    assert updated.status.value == "blocked"
    assert any(event[0] == ProtocolEventType.COMMAND_BLOCKED for event in emitted)
    assert any(event[0] == ProtocolEventType.DETERMINISM_BREACH for event in emitted)
    assert queue.qsize() == 1


@pytest.mark.asyncio
async def test_approved_command_resume_helper_queues_policy_gated_command_without_execution_event(monkeypatch) -> None:
    manager = get_approval_manager()
    manager.reset_for_tests()
    manager.register_pending(
        command_id="cmd-resume-helper",
        text="open notepad",
        trace_id="11111111-1111-4111-8111-111111111112",
        risk_level=RiskLevel.MEDIUM,
        reason="approval required",
    )
    record = manager.resolve_approval("cmd-resume-helper", approved=True)
    queue: asyncio.Queue = asyncio.Queue(maxsize=4)
    emitted: list[tuple[ProtocolEventType, dict]] = []

    async def fake_emit_event(event_type, payload, **kwargs):
        emitted.append((event_type, payload))

    monkeypatch.setattr(ws_bridge, "_command_queue", queue)
    monkeypatch.setattr(ws_bridge, "_command_queue_capacity", 4)
    monkeypatch.setattr(ws_bridge, "emit_event", fake_emit_event)

    assert await ws_bridge.enqueue_approved_command_for_resume(record) is True

    queued = queue.get_nowait()
    assert queued.command_id == "cmd-resume-helper"
    assert queued.approval_granted is True
    updated = manager.get("cmd-resume-helper")
    assert updated is not None
    assert updated.metadata["approval_resume_status"] == "queued_for_execution"
    assert updated.metadata["approval_resume_queue_depth"] == 1
    assert any(event[0] == ProtocolEventType.COMMAND_STATUS_CHANGED for event in emitted)
    assert all(event[0] != ProtocolEventType.ACTION_STARTED for event in emitted)
    assert all(event[0] != ProtocolEventType.ACTION_COMPLETED for event in emitted)


@pytest.mark.asyncio
async def test_ws_approval_decision_deny_emits_rejected_truth_and_snapshot_without_execution(monkeypatch) -> None:
    manager = get_approval_manager()
    manager.reset_for_tests()
    manager.register_pending(
        command_id="cmd-ws-deny",
        text="open notepad",
        trace_id="11111111-1111-4111-8111-111111111113",
        risk_level=RiskLevel.MEDIUM,
        reason="approval required",
        metadata={"approval_id": "approval-ws-deny"},
    )
    emitted: list[tuple[ProtocolEventType, dict]] = []
    snapshots: list[str] = []
    queue: asyncio.Queue = asyncio.Queue(maxsize=4)

    async def fake_emit_event(event_type, payload, **kwargs):
        emitted.append((event_type, payload))

    async def fake_emit_snapshot(*, to, last_sequence_num=0):
        snapshots.append(to)

    monkeypatch.setattr(ws_bridge, "_command_queue", queue)
    monkeypatch.setattr(ws_bridge, "_command_queue_capacity", 4)
    monkeypatch.setattr(ws_bridge, "emit_event", fake_emit_event)
    monkeypatch.setattr(ws_bridge, "_emit_snapshot", fake_emit_snapshot)

    await ws_bridge.resolve_approval(
        "sid-deny",
        {"approval_id": "approval-ws-deny", "decision": "deny"},
    )

    updated = manager.get("cmd-ws-deny")
    assert updated is not None
    assert updated.status.value == "rejected"
    assert updated.metadata["approval_resolution_status"] == "approval_denied"
    assert updated.metadata["mutation_performed"] is False
    assert updated.metadata["not_executed"] is True
    assert queue.qsize() == 0
    emitted_types = [event[0] for event in emitted]
    assert ProtocolEventType.APPROVAL_RESOLVED in emitted_types
    assert ProtocolEventType.COMMAND_REJECTED in emitted_types
    assert ProtocolEventType.COMMAND_STATUS_CHANGED in emitted_types
    assert ProtocolEventType.ACTION_STARTED not in emitted_types
    assert ProtocolEventType.ACTION_COMPLETED not in emitted_types
    assert snapshots == ["sid-deny"]


@pytest.mark.asyncio
async def test_action_failed_event_carries_execution_evidence(monkeypatch) -> None:
    emitted: list[tuple[ProtocolEventType, dict]] = []

    async def fake_emit_event(event_type, payload, **kwargs):
        emitted.append((event_type, payload))

    monkeypatch.setattr(ws_bridge, "emit_event", fake_emit_event)
    evidence = ExecutionEvidence(
        action="open_app",
        target="steam",
        target_type="application",
        method="launch",
        verification_state="failed",
        started_at_ms=1,
        completed_at_ms=2,
        process_name="steam.exe",
        pids=[],
        process_alive=False,
        warnings=["process crashed after launch"],
    )

    await ws_bridge.emit_action_failed(
        action_id="action-1",
        error="Error: process crashed after launch",
        trace_id="11111111-1111-4111-8111-111111111111",
        is_recoverable=True,
        execution_evidence=evidence,
    )

    assert emitted[0][0] == ProtocolEventType.ACTION_FAILED
    payload = emitted[0][1]
    assert payload["execution_evidence"]["verification_state"] == "failed"
    assert payload["execution_evidence"]["process_alive"] is False
    assert payload["verification"]["passed"] is False
    assert payload["verification"]["method"] == "launch"
    assert emitted[1][0] == ProtocolEventType.VERIFICATION_FAILED
    verification_payload = emitted[1][1]
    assert verification_payload["action_id"] == "action-1"
    assert verification_payload["passed"] is False
    assert verification_payload["verification_state"] == "failed"
    assert verification_payload["execution_evidence"]["process_alive"] is False


def test_runtime_snapshot_includes_journal_backed_action_timeline(monkeypatch) -> None:
    class FakeJournal:
        def snapshot(self):
            return {"last_sequence_num": 7, "last_event_hash": "hash"}

        def recent_events(self):
            return [
                {
                    "type": "ACTION_STARTED",
                    "timestamp": 100,
                    "sequence_num": 6,
                    "session_id": "session-test",
                    "trace_id": "11111111-1111-4111-8111-111111111111",
                    "payload": {"action_id": "action-1", "tool": "open_app", "target": "steam"},
                },
                {
                    "type": "ACTION_COMPLETED",
                    "timestamp": 150,
                    "sequence_num": 7,
                    "session_id": "session-test",
                    "trace_id": "11111111-1111-4111-8111-111111111111",
                    "payload": {
                        "action_id": "action-1",
                        "success": True,
                        "latency_ms": 50,
                        "execution_evidence": {
                            "action": "open_app",
                            "target": "steam",
                            "target_type": "application",
                            "method": "launch",
                            "verification_state": "verified",
                            "pids": [4242],
                            "retry_count": 0,
                            "recovery_triggered": False,
                            "attempts": [],
                            "fallback_chain": [],
                            "warnings": [],
                        },
                    },
                },
            ]

    class FakeAuthority:
        def snapshot(self, journal_snapshot):
            return {"fsm_state": "IDLE", "last_event_sequence": journal_snapshot["last_sequence_num"]}

    class FakeApprovalManager:
        def snapshot(self):
            return {"records": []}

    monkeypatch.setattr(ws_bridge, "_session_id", "session-test")
    monkeypatch.setattr(ws_bridge, "get_runtime_authority", lambda *args, **kwargs: FakeAuthority())
    monkeypatch.setattr(ws_bridge, "get_approval_manager", lambda: FakeApprovalManager())
    monkeypatch.setattr(ws_bridge, "get_last_maintenance_scan", lambda: None)
    monkeypatch.setattr(ws_bridge, "get_app_registry_snapshot", lambda: {"entries": []})

    journal_snapshot, runtime_snapshot = ws_bridge._build_runtime_snapshot(FakeJournal())

    assert journal_snapshot["last_sequence_num"] == 7
    assert runtime_snapshot["action_timeline"][0]["action_id"] == "action-1"
    assert runtime_snapshot["action_timeline"][0]["execution_evidence"]["verification_state"] == "verified"


@pytest.mark.asyncio
async def test_snapshot_event_carries_truth_sync_contract(monkeypatch) -> None:
    appended = []
    emitted = []

    class FakeJournal:
        def snapshot(self):
            return {"event_count": 2, "last_sequence_num": 7, "last_event_hash": "hash", "integrity_status": "hash-chain"}

        def recent_events(self):
            return []

        def events_after(self, sequence_num: int):
            assert sequence_num == 4
            return [
                {
                    "event_id": "snapshot-old",
                    "type": "SNAPSHOT_CREATED",
                    "sequence_num": 5,
                    "timestamp": 90,
                    "payload": {
                        "missed_events": [
                            {"type": "SNAPSHOT_CREATED", "sequence_num": 4, "payload": {"recursive": True}}
                        ]
                    },
                },
                {
                    "event_id": "system-old",
                    "type": "SYSTEM_ONLINE",
                    "sequence_num": 6,
                    "timestamp": 95,
                    "payload": {"journal": {"last_sequence_num": 5}},
                },
                {
                    "event_id": "11111111-1111-4111-8111-111111111111",
                    "type": "ACTION_COMPLETED",
                    "sequence_num": 7,
                    "timestamp": 100,
                    "payload": {"action_id": "action-1"},
                }
            ]

        def append(self, event):
            appended.append(event)
            return event

    class FakeAuthority:
        def snapshot(self, journal_snapshot):
            return {"fsm_state": "IDLE", "last_event_sequence": journal_snapshot["last_sequence_num"]}

    class FakeApprovalManager:
        def snapshot(self):
            return {"records": []}

    class FakeSio:
        async def emit(self, event_name, data, to=None):
            emitted.append((event_name, data, to))

    fake_journal = FakeJournal()
    monkeypatch.setattr(ws_bridge, "_session_id", "session-test")
    monkeypatch.setattr(ws_bridge, "get_runtime_journal", lambda: fake_journal)
    monkeypatch.setattr(ws_bridge, "get_runtime_authority", lambda *args, **kwargs: FakeAuthority())
    monkeypatch.setattr(ws_bridge, "get_approval_manager", lambda: FakeApprovalManager())
    monkeypatch.setattr(ws_bridge, "get_last_maintenance_scan", lambda: None)
    monkeypatch.setattr(ws_bridge, "get_app_registry_snapshot", lambda: {"entries": []})
    monkeypatch.setattr(ws_bridge, "get_tool_registry_snapshot", lambda: {"tools": []})
    monkeypatch.setattr(ws_bridge, "sio", FakeSio())

    await ws_bridge._emit_snapshot(to="sid-1", last_sequence_num=4)

    assert appended == []
    assert emitted[0][0] == ProtocolEventType.SNAPSHOT_CREATED.value
    assert emitted[0][2] == "sid-1"
    event = emitted[0][1]
    assert "sequence_num" not in event
    assert "event_hash" not in event
    payload = event["payload"]
    assert payload["missed_event_count"] == 1
    assert [event["type"] for event in payload["missed_events"]] == ["ACTION_COMPLETED"]
    assert payload["truth_sync"] == {
        "source_of_truth": "backend_snapshot_protocol_event_journal",
        "snapshot_sequence_num": 7,
        "journal_tail_sequence_num": 7,
        "client_last_sequence_num": 4,
        "missed_event_count": 1,
        "replay_required": True,
    }


@pytest.mark.asyncio
async def test_repeated_snapshot_handshakes_do_not_append_or_grow_recursively(monkeypatch) -> None:
    appended = []
    emitted = []

    class FakeJournal:
        def snapshot(self):
            return {
                "event_count": 3,
                "last_sequence_num": 9,
                "last_event_hash": "hash",
                "integrity_status": "hash-chain",
            }

        def recent_events(self):
            return []

        def events_after(self, sequence_num: int):
            return [
                {
                    "event_id": "snapshot-prior",
                    "type": "SNAPSHOT_CREATED",
                    "sequence_num": 8,
                    "timestamp": 100,
                    "payload": {
                        "runtime": {"large": "snapshot"},
                        "missed_events": [{"type": "SNAPSHOT_CREATED", "sequence_num": 7}],
                    },
                },
                {
                    "event_id": "real-event",
                    "type": "ACTION_FAILED",
                    "sequence_num": 9,
                    "timestamp": 101,
                    "payload": {"action_id": "action-1", "error": "failed"},
                },
            ]

        def append(self, event):
            appended.append(event)
            return event

    class FakeAuthority:
        def snapshot(self, journal_snapshot):
            return {"fsm_state": "IDLE", "last_event_sequence": journal_snapshot["last_sequence_num"]}

    class FakeApprovalManager:
        def snapshot(self):
            return {"records": []}

    class FakeSio:
        async def emit(self, event_name, data, to=None):
            emitted.append((event_name, data, to))

    monkeypatch.setattr(ws_bridge, "_session_id", "session-test")
    monkeypatch.setattr(ws_bridge, "get_runtime_journal", lambda: FakeJournal())
    monkeypatch.setattr(ws_bridge, "get_runtime_authority", lambda *args, **kwargs: FakeAuthority())
    monkeypatch.setattr(ws_bridge, "get_approval_manager", lambda: FakeApprovalManager())
    monkeypatch.setattr(ws_bridge, "get_last_maintenance_scan", lambda: None)
    monkeypatch.setattr(ws_bridge, "get_app_registry_snapshot", lambda: {"entries": []})
    monkeypatch.setattr(ws_bridge, "get_tool_registry_snapshot", lambda: {"tools": []})
    monkeypatch.setattr(ws_bridge, "sio", FakeSio())

    await ws_bridge._emit_snapshot(to="sid-1", last_sequence_num=7)
    await ws_bridge._emit_snapshot(to="sid-1", last_sequence_num=7)

    assert appended == []
    assert len(emitted) == 2
    for _, data, _ in emitted:
        assert "sequence_num" not in data
        missed = data["payload"]["missed_events"]
        assert [event["type"] for event in missed] == ["ACTION_FAILED"]
        assert all("SNAPSHOT_CREATED" != event["type"] for event in missed)


@pytest.mark.asyncio
async def test_connect_handshake_and_snapshot_do_not_consume_global_journal_sequence(monkeypatch) -> None:
    appended = []
    emitted = []

    class FakeJournal:
        def snapshot(self):
            return {
                "event_count": 1,
                "last_sequence_num": 12,
                "last_event_hash": "hash",
                "integrity_status": "hash-chain",
            }

        def recent_events(self):
            return []

        def events_after(self, sequence_num: int):
            return []

        def append(self, event):
            appended.append(event)
            return event

    class FakeAuthority:
        def snapshot(self, journal_snapshot):
            return {"fsm_state": "IDLE", "last_event_sequence": journal_snapshot["last_sequence_num"]}

    class FakeApprovalManager:
        def snapshot(self):
            return {"records": []}

    class FakeSio:
        async def emit(self, event_name, data, to=None):
            emitted.append((event_name, data, to))

    monkeypatch.setattr(ws_bridge, "_session_id", "session-test")
    monkeypatch.setattr(ws_bridge, "get_runtime_journal", lambda: FakeJournal())
    monkeypatch.setattr(ws_bridge, "get_runtime_authority", lambda *args, **kwargs: FakeAuthority())
    monkeypatch.setattr(ws_bridge, "get_approval_manager", lambda: FakeApprovalManager())
    monkeypatch.setattr(ws_bridge, "get_last_maintenance_scan", lambda: None)
    monkeypatch.setattr(ws_bridge, "get_app_registry_snapshot", lambda: {"entries": []})
    monkeypatch.setattr(ws_bridge, "get_tool_registry_snapshot", lambda: {"tools": []})
    monkeypatch.setattr(ws_bridge, "sio", FakeSio())
    ws_bridge._connected_clients.clear()

    await ws_bridge.connect("sid-1", {})

    assert appended == []
    assert [item[0] for item in emitted] == [
        ProtocolEventType.SYSTEM_ONLINE.value,
        ProtocolEventType.SNAPSHOT_CREATED.value,
    ]
    assert all("sequence_num" not in data for _, data, _ in emitted)
    assert emitted[1][1]["payload"]["truth_sync"]["snapshot_sequence_num"] == 12
