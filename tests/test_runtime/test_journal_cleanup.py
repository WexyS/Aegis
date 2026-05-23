from __future__ import annotations

import json
from pathlib import Path

from aegis.core.journal_cleanup import scan_runtime_journal_snapshot_bloat


def _write_jsonl(path: Path, events: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n" for event in events),
        encoding="utf-8",
    )


def test_snapshot_bloat_scan_is_dry_run_and_detects_historical_control_plane_events(tmp_path) -> None:
    journal_path = tmp_path / "runtime_events.jsonl"
    events = [
        {
            "type": "COMMAND_RECEIVED",
            "sequence_num": 10,
            "event_hash": "hash-10",
            "previous_hash": "genesis",
            "payload": {"text": "open notepad"},
        },
        {
            "type": "SYSTEM_ONLINE",
            "sequence_num": 11,
            "event_hash": "hash-11",
            "previous_hash": "hash-10",
            "payload": {"session_id": "session-old"},
        },
        {
            "type": "SNAPSHOT_CREATED",
            "sequence_num": 12,
            "event_hash": "hash-12",
            "previous_hash": "hash-11",
            "payload": {
                "missed_events": [
                    {"type": "SNAPSHOT_CREATED", "sequence_num": 9, "payload": {"runtime": {"large": True}}}
                ],
                "runtime": {"snapshot": True},
            },
        },
        {
            "type": "ACTION_FAILED",
            "sequence_num": 13,
            "event_hash": "hash-13",
            "previous_hash": "hash-12",
            "payload": {"action_id": "action-1", "success": False},
        },
    ]
    _write_jsonl(journal_path, events)
    before = journal_path.read_text(encoding="utf-8")

    report = scan_runtime_journal_snapshot_bloat(journal_path)

    assert journal_path.read_text(encoding="utf-8") == before
    assert report["dry_run"] is True
    assert report["mutated"] is False
    assert report["destructive_cleanup_default"] is False
    assert report["event_count"] == 4
    assert report["first_sequence_num"] == 10
    assert report["last_sequence_num"] == 13
    assert report["control_plane"]["event_count"] == 2
    assert report["control_plane"]["snapshot_created_count"] == 1
    assert report["control_plane"]["system_online_count"] == 1
    assert report["control_plane"]["recursive_snapshot_risk_count"] == 1
    assert report["control_plane"]["recursive_snapshot_sequences"] == [12]
    assert report["recommended_strategy"] == "archive_or_compact_with_manifest"


def test_snapshot_bloat_scan_reports_hash_chain_removal_risk_without_weakening_truth(tmp_path) -> None:
    journal_path = tmp_path / "runtime_events.jsonl"
    _write_jsonl(
        journal_path,
        [
            {
                "type": "COMMAND_RECEIVED",
                "sequence_num": 1,
                "event_hash": "hash-1",
                "previous_hash": "genesis",
                "payload": {"text": "one"},
            },
            {
                "type": "SNAPSHOT_CREATED",
                "sequence_num": 2,
                "event_hash": "hash-2",
                "previous_hash": "hash-1",
                "payload": {"missed_events": []},
            },
            {
                "type": "ACTION_COMPLETED",
                "sequence_num": 3,
                "event_hash": "hash-3",
                "previous_hash": "hash-2",
                "payload": {"action_id": "action-1", "success": True},
            },
        ],
    )

    report = scan_runtime_journal_snapshot_bloat(journal_path)

    assert report["hash_chain"] == {
        "preserved": True,
        "removal_would_break_hash_chain": True,
        "removal_would_break_sequence_continuity": True,
        "compaction_boundary_required": True,
    }
    assert report["manifest_template"]["original_journal_path"] == str(journal_path)
    assert report["manifest_template"]["original_first_sequence_num"] == 1
    assert report["manifest_template"]["original_last_sequence_num"] == 3
    assert report["manifest_template"]["hash_chain_policy"] == (
        "preserve_original_archive_or_explicit_compaction_boundary"
    )
    assert any("In-place removal is unsafe" in note for note in report["safety_notes"])


def test_snapshot_bloat_scan_preserves_failed_evidence_records(tmp_path) -> None:
    journal_path = tmp_path / "runtime_events.jsonl"
    failed_evidence = {
        "verification_state": "failed",
        "checks": [{"check_name": "process_alive", "passed": False}],
    }
    _write_jsonl(
        journal_path,
        [
            {
                "type": "SNAPSHOT_CREATED",
                "sequence_num": 20,
                "event_hash": "hash-20",
                "previous_hash": "hash-19",
                "payload": {"missed_events": []},
            },
            {
                "type": "ACTION_FAILED",
                "sequence_num": 21,
                "event_hash": "hash-21",
                "previous_hash": "hash-20",
                "payload": {
                    "action_id": "action-antigravity",
                    "success": False,
                    "verified": False,
                    "execution_evidence": failed_evidence,
                },
            },
        ],
    )
    before = journal_path.read_text(encoding="utf-8")

    report = scan_runtime_journal_snapshot_bloat(journal_path)

    after = journal_path.read_text(encoding="utf-8")
    assert after == before
    assert '"ACTION_FAILED"' in after
    assert '"verification_state":"failed"' in after
    assert report["event_count"] == 2
    assert report["control_plane"]["snapshot_created_count"] == 1


def test_snapshot_bloat_scan_reports_clean_journal_without_cleanup_recommendation(tmp_path) -> None:
    journal_path = tmp_path / "runtime_events.jsonl"
    _write_jsonl(
        journal_path,
        [
            {
                "type": "COMMAND_RECEIVED",
                "sequence_num": 1,
                "event_hash": "hash-1",
                "previous_hash": "genesis",
                "payload": {"text": "read file"},
            },
            {
                "type": "ACTION_COMPLETED",
                "sequence_num": 2,
                "event_hash": "hash-2",
                "previous_hash": "hash-1",
                "payload": {"action_id": "action-1", "success": True},
            },
        ],
    )

    report = scan_runtime_journal_snapshot_bloat(journal_path)

    assert report["control_plane"]["event_count"] == 0
    assert report["hash_chain"]["removal_would_break_hash_chain"] is False
    assert report["recommended_strategy"] == "no_control_plane_bloat_detected"
    assert report["manifest_template"] is None
