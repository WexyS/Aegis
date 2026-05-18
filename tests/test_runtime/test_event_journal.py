from __future__ import annotations

import json
import logging
from pathlib import Path
from types import SimpleNamespace

from aegis.core.event_journal import RuntimeEventJournal
from aegis.core.protocol import ProtocolEventType, create_event


def test_runtime_event_journal_events_after_and_duplicate_suppression(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        "aegis.core.event_journal.get_settings",
        lambda: SimpleNamespace(logging=SimpleNamespace(directory=str(tmp_path))),
    )
    journal = RuntimeEventJournal(max_memory_events=10)

    first = journal.append(create_event(ProtocolEventType.COMMAND_RECEIVED, {"text": "one"}))
    second = journal.append(create_event(ProtocolEventType.APPROVAL_REQUIRED, {"command": {"command_id": "cmd-1"}}))
    journal.append(first)

    snapshot = journal.snapshot()
    after_first = journal.events_after(first.sequence_num)

    assert snapshot["event_count"] == 2
    assert after_first == [second.to_dict()]
    assert snapshot["last_sequence_num"] == second.sequence_num
    assert snapshot["last_event_hash"] == second.event_hash
    assert snapshot["integrity_status"] == "hash-chain"
    assert snapshot["integrity_checked_events"] == 2


def test_runtime_event_journal_append_fsyncs_before_commit(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        "aegis.core.event_journal.get_settings",
        lambda: SimpleNamespace(logging=SimpleNamespace(directory=str(tmp_path))),
    )
    fsync_calls: list[int] = []
    monkeypatch.setattr("aegis.core.event_journal.os.fsync", lambda fileno: fsync_calls.append(fileno))
    journal = RuntimeEventJournal(max_memory_events=10)

    journal.append(create_event(ProtocolEventType.COMMAND_RECEIVED, {"text": "durable"}))

    assert len(fsync_calls) == 1


def test_runtime_event_journal_events_after_reads_disk_when_memory_tail_is_bounded(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        "aegis.core.event_journal.get_settings",
        lambda: SimpleNamespace(logging=SimpleNamespace(directory=str(tmp_path))),
    )
    journal = RuntimeEventJournal(max_memory_events=2)
    events = [
        journal.append(create_event(ProtocolEventType.COMMAND_RECEIVED, {"text": f"event-{index}"}))
        for index in range(5)
    ]

    after_first = journal.events_after(events[0].sequence_num)

    assert [event["event_id"] for event in after_first] == [event.event_id for event in events[1:]]


def test_runtime_event_journal_reload_failure_is_logged(tmp_path, monkeypatch, caplog) -> None:
    monkeypatch.setattr(
        "aegis.core.event_journal.get_settings",
        lambda: SimpleNamespace(logging=SimpleNamespace(directory=str(tmp_path))),
    )
    (tmp_path / "runtime_events.jsonl").write_text("{not-json}\n", encoding="utf-8")

    with caplog.at_level(logging.ERROR, logger="aegis.core.event_journal"):
        journal = RuntimeEventJournal(max_memory_events=10)

    assert journal.snapshot()["event_count"] == 0
    assert "Failed to reload runtime event journal from disk" in caplog.text


def test_runtime_event_journal_integrity_allows_session_genesis_reset(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        "aegis.core.event_journal.get_settings",
        lambda: SimpleNamespace(logging=SimpleNamespace(directory=str(tmp_path))),
    )
    journal = RuntimeEventJournal(max_memory_events=10)

    first = create_event(ProtocolEventType.SYSTEM_ONLINE, {}, session_id="session-one")
    second = create_event(ProtocolEventType.SYSTEM_ONLINE, {}, session_id="session-two")
    journal.append(first)
    journal.append(second)
    event = second.to_dict()
    event["previous_hash"] = "genesis"
    journal._events[-1] = event

    snapshot = journal.snapshot()

    assert snapshot["integrity_status"] == "hash-chain"
    assert snapshot["integrity_chain_resets"] == 1


def test_runtime_event_journal_reports_historical_break_without_poisoning_active_chain(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        "aegis.core.event_journal.get_settings",
        lambda: SimpleNamespace(logging=SimpleNamespace(directory=str(tmp_path))),
    )
    journal = RuntimeEventJournal(max_memory_events=10)

    journal.append(create_event(ProtocolEventType.SYSTEM_ONLINE, {}, session_id="session-one"))
    second = journal.append(create_event(ProtocolEventType.COMMAND_RECEIVED, {"text": "click"}, session_id="session-one"))
    third = journal.append(create_event(ProtocolEventType.APPROVAL_REQUIRED, {"command": {"command_id": "cmd-1"}}, session_id="session-one"))
    broken_second = second.to_dict()
    broken_second["previous_hash"] = "legacy-corrupt-link"
    journal._events[1] = broken_second

    snapshot = journal.snapshot()

    assert snapshot["integrity_status"] == "hash-chain"
    assert snapshot["historical_integrity_status"] == "broken"
    assert snapshot["historical_integrity_breaks"] == 1
    assert snapshot["active_chain_start_sequence"] == second.sequence_num
    assert snapshot["last_event_hash"] == third.event_hash


def test_runtime_event_journal_syncs_disk_before_append_from_multiple_instances(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        "aegis.core.event_journal.get_settings",
        lambda: SimpleNamespace(logging=SimpleNamespace(directory=str(tmp_path))),
    )
    journal_a = RuntimeEventJournal(max_memory_events=10)
    journal_b = RuntimeEventJournal(max_memory_events=10)

    first = journal_a.append(create_event(ProtocolEventType.SYSTEM_ONLINE, {}, session_id="session-one"))
    second = journal_b.append(create_event(ProtocolEventType.COMMAND_RECEIVED, {"text": "click"}, session_id="session-one"))
    third = journal_a.append(create_event(ProtocolEventType.APPROVAL_REQUIRED, {"command": {"command_id": "cmd-1"}}, session_id="session-one"))
    verifier = RuntimeEventJournal(max_memory_events=10)
    snapshot = verifier.snapshot()

    assert second.previous_hash == first.event_hash
    assert third.previous_hash == second.event_hash
    assert snapshot["integrity_status"] == "hash-chain"
    assert snapshot["historical_integrity_status"] == "hash-chain"
    assert snapshot["historical_integrity_breaks"] == 0


def test_runtime_event_journal_repairs_historical_breaks_by_archiving_original(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        "aegis.core.event_journal.get_settings",
        lambda: SimpleNamespace(logging=SimpleNamespace(directory=str(tmp_path))),
    )
    journal = RuntimeEventJournal(max_memory_events=10)
    first = journal.append(create_event(ProtocolEventType.SYSTEM_ONLINE, {}, session_id="session-one"))
    second = journal.append(create_event(ProtocolEventType.COMMAND_RECEIVED, {"text": "click"}, session_id="session-one"))
    third = journal.append(create_event(ProtocolEventType.APPROVAL_REQUIRED, {"command": {"command_id": "cmd-1"}}, session_id="session-one"))

    lines = journal.path.read_text(encoding="utf-8").splitlines()
    broken_second = second.to_dict()
    broken_second["previous_hash"] = "legacy-corrupt-link"
    lines[1] = json.dumps(broken_second, ensure_ascii=False, separators=(",", ":"))
    journal.path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    broken = RuntimeEventJournal(max_memory_events=10)
    before = broken.snapshot()
    repair = broken.repair_historical_breaks()
    after = broken.snapshot()

    assert before["historical_integrity_status"] == "broken"
    assert repair["repaired"] is True
    assert repair["archived_event_count"] == 3
    assert repair["active_event_count"] == 2
    assert after["integrity_status"] == "hash-chain"
    assert after["historical_integrity_status"] == "hash-chain"
    assert after["historical_integrity_breaks"] == 0
    assert broken.path.exists()
    assert Path(repair["archived_path"]).exists()
    assert first.to_dict()["event_id"] in Path(repair["archived_path"]).read_text(encoding="utf-8")
    assert third.to_dict()["event_id"] in broken.path.read_text(encoding="utf-8")
