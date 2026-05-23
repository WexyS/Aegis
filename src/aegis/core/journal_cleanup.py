from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from typing import Any


CONTROL_PLANE_EVENT_TYPES = {"SNAPSHOT_CREATED", "SYSTEM_ONLINE"}
MANIFEST_SCHEMA_VERSION = "runtime-journal-archive-compaction-manifest/1"
SUPPORTED_MANIFEST_PLAN_MODES = {"dry_run", "archive_plan", "compact_plan"}
EXECUTED_MANIFEST_MODES = {"executed_archive", "executed_compaction"}


def scan_runtime_journal_snapshot_bloat(journal_path: str | Path) -> dict[str, Any]:
    """Dry-run scan for historically persisted websocket control-plane events.

    This helper is intentionally read-only. Persisted SNAPSHOT_CREATED and
    SYSTEM_ONLINE records may be part of the hash chain and sequence history, so
    cleanup must be planned as an archive/compaction operation instead of silent
    deletion or in-place line removal.
    """

    path = Path(journal_path)
    report: dict[str, Any] = {
        "scan_version": "runtime-journal-cleanup-readiness/1",
        "journal_path": str(path),
        "exists": path.exists(),
        "dry_run": True,
        "mutated": False,
        "destructive_cleanup_default": False,
        "event_count": 0,
        "total_bytes": 0,
        "parse_error_count": 0,
        "first_sequence_num": None,
        "last_sequence_num": None,
        "control_plane": {
            "event_count": 0,
            "total_bytes": 0,
            "snapshot_created_count": 0,
            "snapshot_created_bytes": 0,
            "system_online_count": 0,
            "system_online_bytes": 0,
            "first_sequence_num": None,
            "last_sequence_num": None,
            "largest_snapshot_bytes": 0,
            "largest_snapshot_sequence_num": None,
            "recursive_snapshot_risk_count": 0,
            "recursive_snapshot_sequences": [],
        },
        "hash_chain": {
            "preserved": True,
            "removal_would_break_hash_chain": False,
            "removal_would_break_sequence_continuity": False,
            "compaction_boundary_required": False,
        },
        "recommended_strategy": "no_control_plane_bloat_detected",
        "safety_notes": [],
        "manifest_template": None,
    }

    if not path.exists():
        report["safety_notes"].append("Journal file does not exist; no cleanup action is available.")
        return report

    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            line_bytes = len(line.encode("utf-8"))
            report["total_bytes"] += line_bytes
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                report["parse_error_count"] += 1
                continue

            report["event_count"] += 1
            sequence_num = _coerce_sequence(event.get("sequence_num"))
            _record_sequence(report, sequence_num)

            event_type = str(event.get("type") or event.get("event_type") or "")
            if event_type not in CONTROL_PLANE_EVENT_TYPES:
                continue

            control = report["control_plane"]
            control["event_count"] += 1
            control["total_bytes"] += line_bytes
            _record_control_sequence(control, sequence_num)

            if event_type == "SNAPSHOT_CREATED":
                control["snapshot_created_count"] += 1
                control["snapshot_created_bytes"] += line_bytes
                if line_bytes > control["largest_snapshot_bytes"]:
                    control["largest_snapshot_bytes"] = line_bytes
                    control["largest_snapshot_sequence_num"] = sequence_num
                if _has_recursive_snapshot_risk(event):
                    control["recursive_snapshot_risk_count"] += 1
                    control["recursive_snapshot_sequences"].append(sequence_num or line_number)
            elif event_type == "SYSTEM_ONLINE":
                control["system_online_count"] += 1
                control["system_online_bytes"] += line_bytes

    if report["control_plane"]["event_count"]:
        report["hash_chain"].update(
            {
                "removal_would_break_hash_chain": True,
                "removal_would_break_sequence_continuity": True,
                "compaction_boundary_required": True,
            }
        )
        report["recommended_strategy"] = "archive_or_compact_with_manifest"
        report["safety_notes"].extend(
            [
                "In-place removal is unsafe because persisted control-plane records can be hash-chain members.",
                "Use replay filtering immediately; use archive/compaction only with an explicit manifest and backup.",
            ]
        )
        report["manifest_template"] = {
            "original_journal_path": str(path),
            "archive_path": None,
            "total_event_count": report["event_count"],
            "control_plane_event_count": report["control_plane"]["event_count"],
            "snapshot_created_count": report["control_plane"]["snapshot_created_count"],
            "system_online_count": report["control_plane"]["system_online_count"],
            "original_first_sequence_num": report["first_sequence_num"],
            "original_last_sequence_num": report["last_sequence_num"],
            "compacted_first_sequence_num": None,
            "compacted_last_sequence_num": None,
            "hash_chain_policy": "preserve_original_archive_or_explicit_compaction_boundary",
            "dry_run": True,
        }

    if report["parse_error_count"]:
        report["safety_notes"].append("Journal contains parse errors; compaction requires a separate integrity plan.")

    return report


def build_runtime_journal_compaction_manifest(
    journal_path: str | Path,
    *,
    mode: str = "dry_run",
    operation_id: str | None = None,
    created_at: str | None = None,
    archive_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Build a dry-run archive/compaction manifest without mutating the journal.

    The manifest is a planning contract only. It records the current journal
    fingerprint, detected control-plane bloat, and the safety requirements a
    future explicit archive/compaction operation must satisfy.
    """

    if mode in EXECUTED_MANIFEST_MODES:
        raise ValueError(f"{mode} manifests require an executed operation and are not supported by dry-run planning")
    if mode not in SUPPORTED_MANIFEST_PLAN_MODES:
        raise ValueError(f"unsupported journal cleanup manifest mode: {mode}")

    path = Path(journal_path)
    scan = scan_runtime_journal_snapshot_bloat(path)
    op_id = operation_id or f"journal-cleanup-{uuid4().hex}"
    timestamp = created_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    archive_root = Path(archive_dir) if archive_dir is not None else path.parent / "archive"

    exists = bool(scan["exists"])
    has_control_plane_bloat = bool(scan["control_plane"]["event_count"])
    has_parse_errors = bool(scan["parse_error_count"])
    original_file_size = path.stat().st_size if exists else None
    original_sha256 = _sha256_file(path) if exists else None

    candidate_archive_path = None
    candidate_compacted_journal_path = None
    backup_path = None
    excluded_categories: list[str] = []
    retained_categories = ["runtime_event_journal_events"]
    warnings: list[str] = []
    blockers: list[str] = []

    if not exists:
        blockers.append("journal_missing")
        recommended_operation = "no_op"
        hash_chain_strategy = "not_applicable"
        sequence_strategy = "not_applicable"
    elif not has_control_plane_bloat:
        recommended_operation = "no_op"
        hash_chain_strategy = "preserved"
        sequence_strategy = "preserved"
        warnings.append("No historical control-plane bloat detected; compaction is not needed.")
    else:
        recommended_operation = "archive_or_compact_with_manifest"
        hash_chain_strategy = "explicit_boundary"
        sequence_strategy = "compacted_with_boundary"
        excluded_categories = sorted(CONTROL_PLANE_EVENT_TYPES)
        candidate_archive_path = str(archive_root / f"{path.stem}_{op_id}_original{path.suffix}")
        backup_path = str(archive_root / f"{path.stem}_{op_id}_backup{path.suffix}")
        candidate_compacted_journal_path = str(path.with_name(f"{path.stem}_{op_id}_compacted{path.suffix}"))
        warnings.extend(scan["safety_notes"])
        warnings.append("In-place compaction is forbidden; future execution must write a separate compacted file.")

    if has_parse_errors:
        blockers.append("journal_parse_errors")
        warnings.append("Journal parse errors must be resolved before archive or compaction execution.")

    if mode == "compact_plan" and not has_control_plane_bloat:
        blockers.append("nothing_to_compact")
    if mode in {"archive_plan", "compact_plan"} and not exists:
        blockers.append("cannot_plan_missing_journal")

    return {
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "operation_id": op_id,
        "created_at": timestamp,
        "mode": mode,
        "original_journal_path": str(path),
        "original_file_size": original_file_size,
        "original_sha256": original_sha256,
        "total_event_count": scan["event_count"],
        "first_sequence": scan["first_sequence_num"],
        "last_sequence": scan["last_sequence_num"],
        "detected_control_plane_event_counts": {
            "SNAPSHOT_CREATED": scan["control_plane"]["snapshot_created_count"],
            "SYSTEM_ONLINE": scan["control_plane"]["system_online_count"],
            "total": scan["control_plane"]["event_count"],
        },
        "detected_control_plane_byte_impact": {
            "SNAPSHOT_CREATED": scan["control_plane"]["snapshot_created_bytes"],
            "SYSTEM_ONLINE": scan["control_plane"]["system_online_bytes"],
            "total": scan["control_plane"]["total_bytes"],
            "largest_snapshot_bytes": scan["control_plane"]["largest_snapshot_bytes"],
            "recursive_snapshot_risk_count": scan["control_plane"]["recursive_snapshot_risk_count"],
        },
        "candidate_archive_path": candidate_archive_path,
        "candidate_compacted_journal_path": candidate_compacted_journal_path,
        "backup_path": backup_path,
        "removed_or_excluded_event_categories": excluded_categories,
        "retained_event_categories": retained_categories,
        "hash_chain_handling_strategy": hash_chain_strategy,
        "sequence_handling_strategy": sequence_strategy,
        "replay_validation_requirements": [
            "verify original journal hash before execution",
            "verify compacted journal hash after execution if compaction is implemented",
            "verify replay preserves executable, verification, and evidence events",
            "verify sequence ordering is explicit across any compaction boundary",
            "verify historical control-plane events remain excluded from live missed_events replay",
        ],
        "evidence_audit_preservation_statement": (
            "Cleanup planning must not remove, rewrite, downgrade, or hide ACTION_FAILED, "
            "VERIFICATION_FAILED, execution_evidence, success, or verified fields."
        ),
        "destructive_default": False,
        "requires_explicit_operator_confirmation": True,
        "in_place_compaction_allowed": False,
        "blocked_operations": ["in_place_removal", "in_place_compaction"],
        "recommended_operation": recommended_operation,
        "warnings": warnings,
        "blockers": blockers,
        "scan": scan,
    }


def _coerce_sequence(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _record_sequence(report: dict[str, Any], sequence_num: int | None) -> None:
    if sequence_num is None:
        return
    if report["first_sequence_num"] is None:
        report["first_sequence_num"] = sequence_num
    report["last_sequence_num"] = sequence_num


def _record_control_sequence(control: dict[str, Any], sequence_num: int | None) -> None:
    if sequence_num is None:
        return
    if control["first_sequence_num"] is None:
        control["first_sequence_num"] = sequence_num
    control["last_sequence_num"] = sequence_num


def _has_recursive_snapshot_risk(event: dict[str, Any]) -> bool:
    payload = event.get("payload")
    if not isinstance(payload, dict):
        return False
    missed_events = payload.get("missed_events")
    if not isinstance(missed_events, list):
        return False
    return any(_contains_control_plane_event(item) for item in missed_events)


def _contains_control_plane_event(value: Any) -> bool:
    if isinstance(value, dict):
        event_type = str(value.get("type") or value.get("event_type") or "")
        if event_type in CONTROL_PLANE_EVENT_TYPES:
            return True
        return any(_contains_control_plane_event(child) for child in value.values())
    if isinstance(value, list):
        return any(_contains_control_plane_event(item) for item in value)
    return False


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
