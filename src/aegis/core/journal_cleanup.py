from __future__ import annotations

import json
from pathlib import Path
from typing import Any


CONTROL_PLANE_EVENT_TYPES = {"SNAPSHOT_CREATED", "SYSTEM_ONLINE"}


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
