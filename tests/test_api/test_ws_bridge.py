from __future__ import annotations

import pytest

from aegis.api import ws_bridge
from aegis.core.protocol import ProtocolEventType
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

    assert len(appended) == 1
    assert emitted[0][0] == ProtocolEventType.SNAPSHOT_CREATED.value
    assert emitted[0][2] == "sid-1"
    payload = emitted[0][1]["payload"]
    assert payload["missed_event_count"] == 1
    assert payload["truth_sync"] == {
        "source_of_truth": "backend_snapshot_protocol_event_journal",
        "snapshot_sequence_num": appended[0].sequence_num,
        "journal_tail_sequence_num": 7,
        "client_last_sequence_num": 4,
        "missed_event_count": 1,
        "replay_required": True,
    }
