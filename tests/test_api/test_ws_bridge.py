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
