from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

from aegis.core.config import PROJECT_ROOT, load_settings
from aegis.core.event_journal import RuntimeEventJournal, get_runtime_journal, reset_runtime_journal_for_tests
from aegis.core.protocol import ProtocolEventType, create_event


def test_pytest_runtime_journal_defaults_to_isolated_temp_log_dir() -> None:
    live_fingerprint = _journal_fingerprint(_live_journal_path())
    journal = get_runtime_journal()

    journal.append(create_event(ProtocolEventType.SYSTEM_ONLINE, {"test": "isolated"}))

    test_root = Path(os.environ["AEGIS_TEST_RUNTIME_ROOT"]).resolve()
    assert test_root in journal.path.resolve().parents
    assert journal.path.resolve() != _live_journal_path().resolve()
    assert journal.path.exists()
    assert _journal_fingerprint(_live_journal_path()) == live_fingerprint


def test_pytest_live_journal_write_guard_blocks_accidental_live_append(monkeypatch) -> None:
    monkeypatch.setenv("AEGIS_LOG_DIR", str(PROJECT_ROOT / "logs"))
    load_settings(force_reload=True)
    reset_runtime_journal_for_tests()
    journal = RuntimeEventJournal(max_memory_events=1)

    with pytest.raises(RuntimeError, match="Refusing to write the live Aegis runtime journal"):
        journal.append(create_event(ProtocolEventType.SYSTEM_ONLINE, {"test": "live-blocked"}))


def test_representative_runtime_journal_access_does_not_change_live_journal() -> None:
    before = _journal_fingerprint(_live_journal_path())
    journal = get_runtime_journal()

    for index in range(3):
        journal.append(
            create_event(
                ProtocolEventType.COMMAND_BLOCKED,
                {"command_id": f"test-{index}", "reason": "isolated test"},
            )
        )

    assert _journal_fingerprint(_live_journal_path()) == before


def _live_journal_path() -> Path:
    return PROJECT_ROOT / "logs" / "runtime_events.jsonl"


def _journal_fingerprint(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"exists": False, "size": 0, "sha256": None, "event_count": 0}
    digest = hashlib.sha256()
    event_count = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
            event_count += chunk.count(b"\n")
    return {
        "exists": True,
        "size": path.stat().st_size,
        "sha256": digest.hexdigest(),
        "event_count": event_count,
    }
