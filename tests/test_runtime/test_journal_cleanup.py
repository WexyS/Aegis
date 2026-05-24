from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from aegis.core.journal_cleanup import (
    BOUNDARY_STATUS_BOUNDARY_CANDIDATE,
    BOUNDARY_STATUS_BOUNDARY_CANDIDATE_WITH_WARNINGS,
    BOUNDARY_STATUS_HASH_CHAIN_BOUNDARY_REQUIRED,
    BOUNDARY_STATUS_MALFORMED_JOURNAL_BLOCKED,
    BOUNDARY_STATUS_MISSING_JOURNAL_BLOCKED,
    BOUNDARY_STATUS_MIXED_SEQUENCE_ERAS_BLOCKED,
    BOUNDARY_STATUS_NO_COMPACTION_NEEDED,
    BOUNDARY_STATUS_SEQUENCE_GAP_BLOCKED,
    COMPACTION_READINESS_ARCHIVE_PLAN_ONLY,
    COMPACTION_READINESS_BLOCKED,
    COMPACTION_READINESS_NOT_NEEDED,
    COMPACTION_READINESS_REQUIRES_EXPLICIT_BOUNDARY,
    MANIFEST_SCHEMA_VERSION,
    build_runtime_journal_compaction_manifest,
    scan_runtime_journal_snapshot_bloat,
    validate_runtime_journal_compaction_boundary,
    write_runtime_journal_compaction_manifest_artifact,
)


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


def test_compaction_manifest_dry_run_includes_required_safety_contract(tmp_path) -> None:
    journal_path = tmp_path / "runtime_events.jsonl"
    events = [
        {
            "type": "COMMAND_RECEIVED",
            "sequence_num": 1,
            "event_hash": "hash-1",
            "previous_hash": "genesis",
            "payload": {"text": "open notepad"},
        },
        {
            "type": "SYSTEM_ONLINE",
            "sequence_num": 2,
            "event_hash": "hash-2",
            "previous_hash": "hash-1",
            "payload": {"session_id": "session-old"},
        },
        {
            "type": "SNAPSHOT_CREATED",
            "sequence_num": 3,
            "event_hash": "hash-3",
            "previous_hash": "hash-2",
            "payload": {
                "missed_events": [{"type": "SYSTEM_ONLINE", "sequence_num": 2}],
                "runtime": {"snapshot": True},
            },
        },
        {
            "type": "ACTION_FAILED",
            "sequence_num": 4,
            "event_hash": "hash-4",
            "previous_hash": "hash-3",
            "payload": {
                "action_id": "action-1",
                "success": False,
                "verified": False,
                "execution_evidence": {"verification_state": "failed"},
            },
        },
    ]
    _write_jsonl(journal_path, events)
    before = journal_path.read_bytes()

    manifest = build_runtime_journal_compaction_manifest(
        journal_path,
        operation_id="op-test",
        created_at="2026-05-24T00:00:00Z",
        archive_dir=tmp_path / "archive",
    )

    assert journal_path.read_bytes() == before
    assert manifest["manifest_schema_version"] == MANIFEST_SCHEMA_VERSION
    assert manifest["operation_id"] == "op-test"
    assert manifest["created_at"] == "2026-05-24T00:00:00Z"
    assert manifest["mode"] == "dry_run"
    assert manifest["original_journal_path"] == str(journal_path)
    assert manifest["original_file_size"] == len(before)
    assert manifest["original_sha256"] == hashlib.sha256(before).hexdigest()
    assert manifest["total_event_count"] == 4
    assert manifest["first_sequence"] == 1
    assert manifest["last_sequence"] == 4
    assert manifest["detected_control_plane_event_counts"] == {
        "SNAPSHOT_CREATED": 1,
        "SYSTEM_ONLINE": 1,
        "total": 2,
    }
    assert manifest["detected_control_plane_byte_impact"]["total"] > 0
    assert manifest["detected_control_plane_byte_impact"]["recursive_snapshot_risk_count"] == 1
    assert manifest["candidate_archive_path"] == str(tmp_path / "archive" / "runtime_events_op-test_original.jsonl")
    assert manifest["backup_path"] == str(tmp_path / "archive" / "runtime_events_op-test_backup.jsonl")
    assert manifest["candidate_compacted_journal_path"] == str(tmp_path / "runtime_events_op-test_compacted.jsonl")
    assert manifest["removed_or_excluded_event_categories"] == ["SNAPSHOT_CREATED", "SYSTEM_ONLINE"]
    assert manifest["hash_chain_handling_strategy"] == "explicit_boundary"
    assert manifest["sequence_handling_strategy"] == "compacted_with_boundary"
    assert manifest["destructive_default"] is False
    assert manifest["requires_explicit_operator_confirmation"] is True
    assert manifest["in_place_compaction_allowed"] is False
    assert "in_place_compaction" in manifest["blocked_operations"]
    assert "execution_evidence" in manifest["evidence_audit_preservation_statement"]
    assert "verify replay preserves executable, verification, and evidence events" in (
        manifest["replay_validation_requirements"]
    )
    assert manifest["boundary_validation_status"] == BOUNDARY_STATUS_BOUNDARY_CANDIDATE
    assert manifest["future_compaction_readiness"] == COMPACTION_READINESS_REQUIRES_EXPLICIT_BOUNDARY
    assert manifest["boundary_validation"]["evidence"]["failed_or_unverified_count"] == 1


def test_compaction_manifest_clean_journal_is_no_op_plan(tmp_path) -> None:
    journal_path = tmp_path / "runtime_events.jsonl"
    _write_jsonl(
        journal_path,
        [
            {
                "type": "COMMAND_RECEIVED",
                "sequence_num": 10,
                "event_hash": "hash-10",
                "previous_hash": "genesis",
                "payload": {"text": "read README.md"},
            },
            {
                "type": "ACTION_COMPLETED",
                "sequence_num": 11,
                "event_hash": "hash-11",
                "previous_hash": "hash-10",
                "payload": {"action_id": "action-1", "success": True},
            },
        ],
    )

    manifest = build_runtime_journal_compaction_manifest(
        journal_path,
        operation_id="op-clean",
        created_at="2026-05-24T00:00:00Z",
    )

    assert manifest["recommended_operation"] == "no_op"
    assert manifest["candidate_archive_path"] is None
    assert manifest["candidate_compacted_journal_path"] is None
    assert manifest["backup_path"] is None
    assert manifest["removed_or_excluded_event_categories"] == []
    assert manifest["hash_chain_handling_strategy"] == "preserved"
    assert manifest["sequence_handling_strategy"] == "preserved"
    assert manifest["destructive_default"] is False
    assert manifest["requires_explicit_operator_confirmation"] is True
    assert manifest["blockers"] == []
    assert manifest["boundary_validation_status"] == BOUNDARY_STATUS_NO_COMPACTION_NEEDED
    assert manifest["future_compaction_readiness"] == COMPACTION_READINESS_NOT_NEEDED


def test_compaction_manifest_missing_journal_fails_safely(tmp_path) -> None:
    journal_path = tmp_path / "missing_runtime_events.jsonl"

    manifest = build_runtime_journal_compaction_manifest(
        journal_path,
        mode="compact_plan",
        operation_id="op-missing",
        created_at="2026-05-24T00:00:00Z",
    )

    assert manifest["original_file_size"] is None
    assert manifest["original_sha256"] is None
    assert manifest["recommended_operation"] == "no_op"
    assert manifest["hash_chain_handling_strategy"] == "not_applicable"
    assert manifest["sequence_handling_strategy"] == "not_applicable"
    assert "journal_missing" in manifest["blockers"]
    assert "cannot_plan_missing_journal" in manifest["blockers"]
    assert manifest["destructive_default"] is False
    assert manifest["in_place_compaction_allowed"] is False
    assert manifest["boundary_validation_status"] == BOUNDARY_STATUS_MISSING_JOURNAL_BLOCKED
    assert manifest["future_compaction_readiness"] == COMPACTION_READINESS_BLOCKED


def test_compaction_manifest_malformed_journal_blocks_future_execution(tmp_path) -> None:
    journal_path = tmp_path / "runtime_events.jsonl"
    journal_path.write_text(
        json.dumps({"type": "COMMAND_RECEIVED", "sequence_num": 1, "payload": {}}) + "\n{not-json}\n",
        encoding="utf-8",
    )

    manifest = build_runtime_journal_compaction_manifest(
        journal_path,
        operation_id="op-malformed",
        created_at="2026-05-24T00:00:00Z",
    )

    assert manifest["scan"]["parse_error_count"] == 1
    assert "journal_parse_errors" in manifest["blockers"]
    assert any("parse errors" in warning for warning in manifest["warnings"])
    assert manifest["destructive_default"] is False
    assert manifest["boundary_validation_status"] == BOUNDARY_STATUS_MALFORMED_JOURNAL_BLOCKED


def test_compaction_manifest_rejects_executed_modes_in_dry_run_planner(tmp_path) -> None:
    journal_path = tmp_path / "runtime_events.jsonl"
    _write_jsonl(journal_path, [])

    with pytest.raises(ValueError, match="require an executed operation"):
        build_runtime_journal_compaction_manifest(journal_path, mode="executed_compaction")


def test_boundary_validation_clean_journal_returns_no_compaction_needed(tmp_path) -> None:
    journal_path = tmp_path / "runtime_events.jsonl"
    _write_jsonl(
        journal_path,
        [
            {
                "type": "COMMAND_RECEIVED",
                "sequence_num": 1,
                "event_hash": "hash-1",
                "previous_hash": "genesis",
                "payload": {"text": "read README.md"},
            },
            {
                "type": "ACTION_COMPLETED",
                "sequence_num": 2,
                "event_hash": "hash-2",
                "previous_hash": "hash-1",
                "payload": {"success": True, "verified": True},
            },
        ],
    )
    before = journal_path.read_text(encoding="utf-8")

    validation = validate_runtime_journal_compaction_boundary(journal_path)

    assert journal_path.read_text(encoding="utf-8") == before
    assert validation["status"] == BOUNDARY_STATUS_NO_COMPACTION_NEEDED
    assert validation["compaction_readiness"] == COMPACTION_READINESS_NOT_NEEDED
    assert validation["blockers"] == []
    assert validation["control_plane"]["event_count"] == 0
    assert validation["sequence"]["monotonic"] is True


def test_boundary_validation_missing_and_malformed_journals_fail_closed(tmp_path) -> None:
    missing = validate_runtime_journal_compaction_boundary(tmp_path / "missing.jsonl")
    assert missing["status"] == BOUNDARY_STATUS_MISSING_JOURNAL_BLOCKED
    assert missing["compaction_readiness"] == COMPACTION_READINESS_BLOCKED
    assert "journal_missing" in missing["blockers"]

    malformed_path = tmp_path / "runtime_events.jsonl"
    malformed_path.write_text("{not-json}\n", encoding="utf-8")
    before = malformed_path.read_text(encoding="utf-8")

    malformed = validate_runtime_journal_compaction_boundary(malformed_path)

    assert malformed_path.read_text(encoding="utf-8") == before
    assert malformed["status"] == BOUNDARY_STATUS_MALFORMED_JOURNAL_BLOCKED
    assert malformed["compaction_readiness"] == COMPACTION_READINESS_BLOCKED
    assert "journal_parse_errors" in malformed["blockers"]


def test_boundary_validation_contiguous_control_plane_bloat_is_boundary_candidate(tmp_path) -> None:
    journal_path = tmp_path / "runtime_events.jsonl"
    _write_jsonl(
        journal_path,
        [
            {"type": "COMMAND_RECEIVED", "sequence_num": 1, "event_hash": "hash-1", "payload": {}},
            {
                "type": "SYSTEM_ONLINE",
                "sequence_num": 2,
                "event_hash": "hash-2",
                "previous_hash": "hash-1",
                "payload": {},
            },
            {
                "type": "SNAPSHOT_CREATED",
                "sequence_num": 3,
                "event_hash": "hash-3",
                "previous_hash": "hash-2",
                "payload": {"missed_events": []},
            },
            {
                "type": "ACTION_COMPLETED",
                "sequence_num": 4,
                "event_hash": "hash-4",
                "previous_hash": "hash-3",
                "payload": {"success": True},
            },
        ],
    )

    validation = validate_runtime_journal_compaction_boundary(journal_path)

    assert validation["status"] == BOUNDARY_STATUS_BOUNDARY_CANDIDATE
    assert validation["compaction_readiness"] == COMPACTION_READINESS_REQUIRES_EXPLICIT_BOUNDARY
    assert validation["control_plane"]["block_count"] == 1
    assert validation["control_plane"]["interleaved_with_runtime_events"] is False
    assert validation["hash_chain"]["explicit_boundary_required"] is True


def test_boundary_validation_interleaved_control_plane_bloat_warns_archive_only(tmp_path) -> None:
    journal_path = tmp_path / "runtime_events.jsonl"
    _write_jsonl(
        journal_path,
        [
            {"type": "COMMAND_RECEIVED", "sequence_num": 1, "event_hash": "hash-1", "payload": {}},
            {
                "type": "SNAPSHOT_CREATED",
                "sequence_num": 2,
                "event_hash": "hash-2",
                "previous_hash": "hash-1",
                "payload": {"missed_events": []},
            },
            {
                "type": "ACTION_FAILED",
                "sequence_num": 3,
                "event_hash": "hash-3",
                "previous_hash": "hash-2",
                "payload": {"success": False, "execution_evidence": {"verification_state": "failed"}},
            },
            {
                "type": "SYSTEM_ONLINE",
                "sequence_num": 4,
                "event_hash": "hash-4",
                "previous_hash": "hash-3",
                "payload": {},
            },
        ],
    )

    validation = validate_runtime_journal_compaction_boundary(journal_path)

    assert validation["status"] == BOUNDARY_STATUS_BOUNDARY_CANDIDATE_WITH_WARNINGS
    assert validation["compaction_readiness"] == COMPACTION_READINESS_ARCHIVE_PLAN_ONLY
    assert validation["control_plane"]["block_count"] == 2
    assert validation["control_plane"]["interleaved_with_runtime_events"] is True
    assert validation["evidence"]["failed_or_unverified_count"] == 1
    assert validation["evidence"]["preservation_required"] is True
    assert any("interleaved" in warning for warning in validation["warnings"])


def test_boundary_validation_sequence_gap_and_mixed_sequence_eras_block_compaction(tmp_path) -> None:
    gap_path = tmp_path / "gap_runtime_events.jsonl"
    _write_jsonl(
        gap_path,
        [
            {"type": "COMMAND_RECEIVED", "sequence_num": 1, "payload": {}},
            {"type": "SNAPSHOT_CREATED", "sequence_num": 3, "payload": {"missed_events": []}},
        ],
    )

    gap = validate_runtime_journal_compaction_boundary(gap_path)

    assert gap["status"] == BOUNDARY_STATUS_SEQUENCE_GAP_BLOCKED
    assert gap["compaction_readiness"] == COMPACTION_READINESS_BLOCKED
    assert "sequence_gaps" in gap["blockers"]
    assert gap["sequence"]["gap_count"] == 1

    mixed_path = tmp_path / "mixed_runtime_events.jsonl"
    _write_jsonl(
        mixed_path,
        [
            {"type": "COMMAND_RECEIVED", "sequence_num": 20, "payload": {}},
            {"type": "SNAPSHOT_CREATED", "sequence_num": 2, "payload": {"missed_events": []}},
        ],
    )

    mixed = validate_runtime_journal_compaction_boundary(mixed_path)

    assert mixed["status"] == BOUNDARY_STATUS_MIXED_SEQUENCE_ERAS_BLOCKED
    assert mixed["compaction_readiness"] == COMPACTION_READINESS_BLOCKED
    assert "mixed_sequence_eras" in mixed["blockers"]
    assert mixed["sequence"]["mixed_sequence_eras_suspected"] is True


def test_boundary_validation_hash_chain_mismatch_requires_explicit_boundary(tmp_path) -> None:
    journal_path = tmp_path / "runtime_events.jsonl"
    _write_jsonl(
        journal_path,
        [
            {"type": "COMMAND_RECEIVED", "sequence_num": 1, "event_hash": "hash-1", "payload": {}},
            {
                "type": "SNAPSHOT_CREATED",
                "sequence_num": 2,
                "event_hash": "hash-2",
                "previous_hash": "not-hash-1",
                "payload": {"missed_events": []},
            },
        ],
    )

    validation = validate_runtime_journal_compaction_boundary(journal_path)

    assert validation["status"] == BOUNDARY_STATUS_HASH_CHAIN_BOUNDARY_REQUIRED
    assert validation["compaction_readiness"] == COMPACTION_READINESS_REQUIRES_EXPLICIT_BOUNDARY
    assert validation["hash_chain"]["mismatch_count"] == 1
    assert validation["hash_chain"]["explicit_boundary_required"] is True


def test_manifest_artifact_writer_writes_json_to_explicit_safe_output_path(tmp_path) -> None:
    journal_dir = tmp_path / "logs"
    journal_dir.mkdir()
    journal_path = journal_dir / "runtime_events.jsonl"
    archive_dir = journal_dir / "archive"
    archive_dir.mkdir()
    output_path = archive_dir / "cleanup-manifest.json"
    _write_jsonl(
        journal_path,
        [
            {
                "type": "COMMAND_RECEIVED",
                "sequence_num": 1,
                "event_hash": "hash-1",
                "previous_hash": "genesis",
                "payload": {"text": "open notepad"},
            },
            {
                "type": "SNAPSHOT_CREATED",
                "sequence_num": 2,
                "event_hash": "hash-2",
                "previous_hash": "hash-1",
                "payload": {"missed_events": [{"type": "SYSTEM_ONLINE", "sequence_num": 1}]},
            },
            {
                "type": "ACTION_FAILED",
                "sequence_num": 3,
                "event_hash": "hash-3",
                "previous_hash": "hash-2",
                "payload": {
                    "success": False,
                    "verified": False,
                    "execution_evidence": {"verification_state": "failed"},
                },
            },
        ],
    )
    before = journal_path.read_bytes()

    result = write_runtime_journal_compaction_manifest_artifact(
        journal_path,
        output_path,
        operation_id="op-artifact",
        created_at="2026-05-24T00:00:00Z",
    )

    assert journal_path.read_bytes() == before
    assert output_path.exists()
    written = output_path.read_text(encoding="utf-8")
    assert written.endswith("\n")
    manifest = json.loads(written)
    assert manifest["manifest_schema_version"] == MANIFEST_SCHEMA_VERSION
    assert manifest["operation_id"] == "op-artifact"
    assert manifest["original_sha256"] == hashlib.sha256(before).hexdigest()
    assert manifest["total_event_count"] == 3
    assert manifest["detected_control_plane_event_counts"]["SNAPSHOT_CREATED"] == 1
    assert manifest["detected_control_plane_byte_impact"]["total"] > 0
    assert manifest["destructive_default"] is False
    assert manifest["requires_explicit_operator_confirmation"] is True
    assert manifest["hash_chain_handling_strategy"] == "explicit_boundary"
    assert manifest["sequence_handling_strategy"] == "compacted_with_boundary"
    assert manifest["boundary_validation_status"] == BOUNDARY_STATUS_BOUNDARY_CANDIDATE
    assert manifest["future_compaction_readiness"] == COMPACTION_READINESS_REQUIRES_EXPLICIT_BOUNDARY
    assert manifest["boundary_validation"]["mutated"] is False
    assert manifest["boundary_validation"]["control_plane"]["event_count"] == 1
    assert "verify replay preserves executable, verification, and evidence events" in (
        manifest["replay_validation_requirements"]
    )
    assert "execution_evidence" in manifest["evidence_audit_preservation_statement"]
    assert result == {
        "output_path": str(output_path),
        "bytes_written": len(written.encode("utf-8")),
        "manifest_operation_id": "op-artifact",
        "original_journal_sha256": manifest["original_sha256"],
        "dry_run": True,
        "destructive_default": False,
        "journal_mutated": False,
        "archive_created": False,
        "compacted_journal_created": False,
    }


def test_manifest_artifact_writer_can_create_safe_parent_directory_only_when_requested(tmp_path) -> None:
    journal_dir = tmp_path / "logs"
    journal_dir.mkdir()
    journal_path = journal_dir / "runtime_events.jsonl"
    output_path = journal_dir / "manifests" / "cleanup-manifest.json"
    _write_jsonl(journal_path, [{"type": "COMMAND_RECEIVED", "sequence_num": 1, "payload": {}}])

    with pytest.raises(FileNotFoundError):
        write_runtime_journal_compaction_manifest_artifact(journal_path, output_path)

    result = write_runtime_journal_compaction_manifest_artifact(
        journal_path,
        output_path,
        operation_id="op-create-parent",
        created_at="2026-05-24T00:00:00Z",
        create_parent_dirs=True,
    )

    assert output_path.exists()
    assert result["manifest_operation_id"] == "op-create-parent"


def test_manifest_artifact_writer_refuses_source_journal_and_runtime_journal_filename(tmp_path) -> None:
    journal_dir = tmp_path / "logs"
    archive_dir = journal_dir / "archive"
    archive_dir.mkdir(parents=True)
    journal_path = journal_dir / "runtime_events.jsonl"
    _write_jsonl(journal_path, [{"type": "COMMAND_RECEIVED", "sequence_num": 1, "payload": {}}])

    with pytest.raises(ValueError, match="source journal path"):
        write_runtime_journal_compaction_manifest_artifact(journal_path, journal_path)
    with pytest.raises(ValueError, match="runtime journal filename"):
        write_runtime_journal_compaction_manifest_artifact(journal_path, archive_dir / "runtime_events.jsonl")


def test_manifest_artifact_writer_refuses_unsafe_output_paths(tmp_path) -> None:
    journal_dir = tmp_path / "logs"
    archive_dir = journal_dir / "archive"
    archive_dir.mkdir(parents=True)
    journal_path = journal_dir / "runtime_events.jsonl"
    _write_jsonl(journal_path, [{"type": "COMMAND_RECEIVED", "sequence_num": 1, "payload": {}}])

    unsafe_outside = tmp_path / "outside.json"
    unsafe_traversal = archive_dir / ".." / "escape.json"
    unsafe_frontend = journal_dir / "archive" / ".next" / "manifest.json"
    bad_suffix = archive_dir / "manifest.txt"
    with pytest.raises(ValueError, match="archive or manifests directory"):
        write_runtime_journal_compaction_manifest_artifact(journal_path, unsafe_outside)
    with pytest.raises(ValueError, match="archive or manifests directory"):
        write_runtime_journal_compaction_manifest_artifact(journal_path, unsafe_traversal)
    with pytest.raises(ValueError, match="frontend build"):
        write_runtime_journal_compaction_manifest_artifact(journal_path, unsafe_frontend)
    with pytest.raises(ValueError, match="must end with .json"):
        write_runtime_journal_compaction_manifest_artifact(journal_path, bad_suffix)


def test_manifest_artifact_writer_refuses_overwrite_by_default_and_allows_explicit_overwrite(tmp_path) -> None:
    journal_dir = tmp_path / "logs"
    archive_dir = journal_dir / "archive"
    archive_dir.mkdir(parents=True)
    journal_path = journal_dir / "runtime_events.jsonl"
    output_path = archive_dir / "manifest.json"
    _write_jsonl(journal_path, [{"type": "COMMAND_RECEIVED", "sequence_num": 1, "payload": {}}])
    output_path.write_text('{"old":true}\n', encoding="utf-8")

    with pytest.raises(FileExistsError):
        write_runtime_journal_compaction_manifest_artifact(journal_path, output_path)

    result = write_runtime_journal_compaction_manifest_artifact(
        journal_path,
        output_path,
        operation_id="op-overwrite",
        created_at="2026-05-24T00:00:00Z",
        overwrite=True,
    )

    manifest = json.loads(output_path.read_text(encoding="utf-8"))
    assert manifest["operation_id"] == "op-overwrite"
    assert result["manifest_operation_id"] == "op-overwrite"


def test_manifest_artifact_writer_missing_or_malformed_journal_does_not_write(tmp_path) -> None:
    journal_dir = tmp_path / "logs"
    archive_dir = journal_dir / "archive"
    archive_dir.mkdir(parents=True)
    missing_journal = journal_dir / "missing_runtime_events.jsonl"
    missing_output = archive_dir / "missing-manifest.json"

    with pytest.raises(ValueError, match="blockers"):
        write_runtime_journal_compaction_manifest_artifact(missing_journal, missing_output)
    assert not missing_output.exists()

    malformed_journal = journal_dir / "runtime_events.jsonl"
    malformed_output = archive_dir / "malformed-manifest.json"
    malformed_journal.write_text("{not-json}\n", encoding="utf-8")
    before = malformed_journal.read_text(encoding="utf-8")

    with pytest.raises(ValueError, match="blockers"):
        write_runtime_journal_compaction_manifest_artifact(malformed_journal, malformed_output)
    assert malformed_journal.read_text(encoding="utf-8") == before
    assert not malformed_output.exists()
