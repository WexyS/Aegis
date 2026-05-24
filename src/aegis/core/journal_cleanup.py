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
SAFE_MANIFEST_OUTPUT_DIR_NAMES = {"archive", "manifests"}
BOUNDARY_VALIDATION_VERSION = "runtime-journal-compaction-boundary-validation/1"

BOUNDARY_STATUS_NO_COMPACTION_NEEDED = "no_compaction_needed"
BOUNDARY_STATUS_BOUNDARY_CANDIDATE = "boundary_candidate"
BOUNDARY_STATUS_BOUNDARY_CANDIDATE_WITH_WARNINGS = "boundary_candidate_with_warnings"
BOUNDARY_STATUS_MIXED_SEQUENCE_ERAS_BLOCKED = "mixed_sequence_eras_blocked"
BOUNDARY_STATUS_SEQUENCE_GAP_BLOCKED = "sequence_gap_blocked"
BOUNDARY_STATUS_HASH_CHAIN_BOUNDARY_REQUIRED = "hash_chain_boundary_required"
BOUNDARY_STATUS_MALFORMED_JOURNAL_BLOCKED = "malformed_journal_blocked"
BOUNDARY_STATUS_MISSING_JOURNAL_BLOCKED = "missing_journal_blocked"

COMPACTION_READINESS_NOT_NEEDED = "not_needed"
COMPACTION_READINESS_DRY_RUN_ONLY = "dry_run_only"
COMPACTION_READINESS_ARCHIVE_PLAN_ONLY = "archive_plan_only"
COMPACTION_READINESS_REQUIRES_EXPLICIT_BOUNDARY = "compact_plan_requires_explicit_boundary"
COMPACTION_READINESS_BLOCKED = "blocked"

EXECUTION_READINESS_VERSION = "runtime-journal-archive-compaction-execution-readiness/1"

EXECUTION_STATUS_NOT_NEEDED = "execution_not_needed"
EXECUTION_STATUS_ARCHIVE_PLAN_READY = "archive_execution_plan_ready"
EXECUTION_STATUS_COMPACTION_REQUIRES_BOUNDARY_APPROVAL = "compaction_execution_requires_boundary_approval"
EXECUTION_STATUS_BLOCKED_MISSING_BACKUP = "execution_blocked_missing_backup"
EXECUTION_STATUS_BLOCKED_MISSING_RESTORE_PLAN = "execution_blocked_missing_restore_plan"
EXECUTION_STATUS_BLOCKED_SEQUENCE_GAP = "execution_blocked_sequence_gap"
EXECUTION_STATUS_BLOCKED_MIXED_SEQUENCE_ERAS = "execution_blocked_mixed_sequence_eras"
EXECUTION_STATUS_BLOCKED_HASH_CHAIN_RISK = "execution_blocked_hash_chain_risk"
EXECUTION_STATUS_BLOCKED_MALFORMED_JOURNAL = "execution_blocked_malformed_journal"
EXECUTION_STATUS_BLOCKED_MISSING_JOURNAL = "execution_blocked_missing_journal"

REQUIRED_OPERATOR_CONFIRMATIONS = [
    "confirm_original_journal_sha256_matches_manifest",
    "confirm_backup_path_is_writable_and_not_source_journal",
    "confirm_restore_plan_is_documented",
    "confirm_no_in_place_mutation",
    "confirm_evidence_audit_records_remain_preserved",
]

REQUIRED_PREFLIGHT_CHECKS = [
    "verify original journal path exists",
    "verify original journal sha256 matches manifest",
    "verify backup path is separate from source journal",
    "verify restore plan exists before mutation",
    "verify boundary validation is not blocked",
    "verify replay validation plan is present",
    "verify evidence audit preservation statement is present",
]

REQUIRED_POST_EXECUTION_CHECKS = [
    "verify source journal backup exists and matches original sha256",
    "verify replay succeeds from archive or compacted journal",
    "verify sequence continuity across any explicit boundary",
    "verify hash-chain handling matches manifest strategy",
    "verify failed and unverified evidence records remain visible",
    "verify historical control-plane events remain excluded from live missed_events replay",
]


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


def validate_runtime_journal_compaction_boundary(journal_path: str | Path) -> dict[str, Any]:
    """Classify journal compaction boundary readiness without mutating history."""

    path = Path(journal_path)
    validation: dict[str, Any] = {
        "validation_version": BOUNDARY_VALIDATION_VERSION,
        "journal_path": str(path),
        "exists": path.exists(),
        "mutated": False,
        "status": BOUNDARY_STATUS_NO_COMPACTION_NEEDED,
        "compaction_readiness": COMPACTION_READINESS_NOT_NEEDED,
        "blockers": [],
        "warnings": [],
        "event_count": 0,
        "parse_error_count": 0,
        "control_plane": {
            "event_count": 0,
            "block_count": 0,
            "interleaved_with_runtime_events": False,
            "first_line": None,
            "last_line": None,
            "first_sequence_num": None,
            "last_sequence_num": None,
        },
        "sequence": {
            "first_sequence_num": None,
            "last_sequence_num": None,
            "monotonic": True,
            "gap_count": 0,
            "gaps": [],
            "decrease_count": 0,
            "decreases": [],
            "mixed_sequence_eras_suspected": False,
        },
        "hash_chain": {
            "checked_links": 0,
            "mismatch_count": 0,
            "mismatches": [],
            "explicit_boundary_required": False,
        },
        "evidence": {
            "failed_or_unverified_count": 0,
            "sequences": [],
            "preservation_required": False,
        },
    }

    if not path.exists():
        validation["status"] = BOUNDARY_STATUS_MISSING_JOURNAL_BLOCKED
        validation["compaction_readiness"] = COMPACTION_READINESS_BLOCKED
        validation["blockers"].append("journal_missing")
        return validation

    control_lines: list[int] = []
    previous_sequence: int | None = None
    previous_hash: str | None = None
    previous_line: int | None = None

    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                validation["parse_error_count"] += 1
                continue

            validation["event_count"] += 1
            event_type = str(event.get("type") or event.get("event_type") or "")
            sequence_num = _coerce_sequence(event.get("sequence_num"))
            _record_boundary_sequence(validation["sequence"], sequence_num, line_number, previous_sequence)
            if sequence_num is not None:
                previous_sequence = sequence_num

            if previous_hash is not None:
                current_previous_hash = event.get("previous_hash")
                if isinstance(current_previous_hash, str):
                    validation["hash_chain"]["checked_links"] += 1
                    if current_previous_hash != previous_hash:
                        validation["hash_chain"]["mismatch_count"] += 1
                        validation["hash_chain"]["mismatches"].append(
                            {
                                "line": line_number,
                                "sequence_num": sequence_num,
                                "expected_previous_hash": previous_hash,
                                "observed_previous_hash": current_previous_hash,
                                "previous_line": previous_line,
                            }
                        )
            event_hash = event.get("event_hash")
            if isinstance(event_hash, str) and event_hash:
                previous_hash = event_hash
                previous_line = line_number

            if event_type in CONTROL_PLANE_EVENT_TYPES:
                control_lines.append(line_number)
                control = validation["control_plane"]
                control["event_count"] += 1
                if control["first_line"] is None:
                    control["first_line"] = line_number
                control["last_line"] = line_number
                _record_control_sequence(control, sequence_num)

            if _event_has_failed_or_unverified_evidence(event, event_type):
                evidence = validation["evidence"]
                evidence["failed_or_unverified_count"] += 1
                if sequence_num is not None:
                    evidence["sequences"].append(sequence_num)

    _record_control_blocks(validation["control_plane"], control_lines)
    _classify_boundary_validation(validation)
    return validation


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
    boundary = validate_runtime_journal_compaction_boundary(path)
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
    for blocker in boundary["blockers"]:
        if blocker not in blockers:
            blockers.append(blocker)
    for warning in boundary["warnings"]:
        if warning not in warnings:
            warnings.append(warning)

    if mode == "compact_plan" and not has_control_plane_bloat:
        blockers.append("nothing_to_compact")
    if mode in {"archive_plan", "compact_plan"} and not exists:
        blockers.append("cannot_plan_missing_journal")

    execution_readiness = evaluate_runtime_journal_compaction_execution_readiness(
        {
            "mode": mode,
            "original_journal_path": str(path),
            "original_sha256": original_sha256,
            "candidate_archive_path": candidate_archive_path,
            "candidate_compacted_journal_path": candidate_compacted_journal_path,
            "backup_path": backup_path,
            "destructive_default": False,
            "requires_explicit_operator_confirmation": True,
            "in_place_compaction_allowed": False,
            "boundary_validation": boundary,
            "boundary_validation_status": boundary["status"],
            "future_compaction_readiness": boundary["compaction_readiness"],
            "blockers": blockers,
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
        }
    )

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
        "boundary_validation": boundary,
        "boundary_validation_status": boundary["status"],
        "boundary_blockers": boundary["blockers"],
        "boundary_warnings": boundary["warnings"],
        "future_compaction_readiness": boundary["compaction_readiness"],
        "execution_readiness": execution_readiness,
        "execution_readiness_status": execution_readiness["status"],
        "execution_blockers": execution_readiness["blockers"],
        "required_operator_confirmations": execution_readiness["required_operator_confirmations"],
        "required_preflight_checks": execution_readiness["required_preflight_checks"],
        "required_post_execution_checks": execution_readiness["required_post_execution_checks"],
        "restore_plan_required": execution_readiness["restore_plan_required"],
        "backup_required": execution_readiness["backup_required"],
        "mutation_performed": False,
        "warnings": warnings,
        "blockers": blockers,
        "scan": scan,
    }


def evaluate_runtime_journal_compaction_execution_readiness(manifest: dict[str, Any]) -> dict[str, Any]:
    """Evaluate future archive/compaction execution gates without executing them."""

    boundary = manifest.get("boundary_validation")
    if not isinstance(boundary, dict):
        boundary = {}
    boundary_status = str(manifest.get("boundary_validation_status") or boundary.get("status") or "")
    compaction_readiness = str(
        manifest.get("future_compaction_readiness") or boundary.get("compaction_readiness") or ""
    )
    backup_path = manifest.get("backup_path")
    has_backup_path = isinstance(backup_path, str) and bool(backup_path.strip())
    original_sha256 = manifest.get("original_sha256")
    has_original_sha256 = isinstance(original_sha256, str) and bool(original_sha256.strip())
    blockers = list(manifest.get("blockers") or [])
    readiness: dict[str, Any] = {
        "readiness_version": EXECUTION_READINESS_VERSION,
        "status": EXECUTION_STATUS_NOT_NEEDED,
        "archive_execution_allowed": False,
        "compaction_execution_allowed": False,
        "execution_blocked": False,
        "blockers": [],
        "warnings": [],
        "required_operator_confirmations": list(REQUIRED_OPERATOR_CONFIRMATIONS),
        "required_preflight_checks": list(REQUIRED_PREFLIGHT_CHECKS),
        "required_post_execution_checks": list(REQUIRED_POST_EXECUTION_CHECKS),
        "backup_required": True,
        "restore_plan_required": True,
        "requires_explicit_boundary_approval": False,
        "requires_explicit_operator_confirmation": True,
        "destructive_default": False,
        "in_place_mutation_allowed": False,
        "mutation_performed": False,
    }

    def block(status: str, blocker: str) -> dict[str, Any]:
        readiness["status"] = status
        readiness["execution_blocked"] = True
        readiness["blockers"].append(blocker)
        return readiness

    if boundary_status == BOUNDARY_STATUS_NO_COMPACTION_NEEDED:
        readiness["status"] = EXECUTION_STATUS_NOT_NEEDED
        readiness["warnings"].append("No historical control-plane bloat detected; execution is not needed.")
        return readiness
    if boundary_status == BOUNDARY_STATUS_MISSING_JOURNAL_BLOCKED or "journal_missing" in blockers:
        return block(EXECUTION_STATUS_BLOCKED_MISSING_JOURNAL, "journal_missing")
    if boundary_status == BOUNDARY_STATUS_MALFORMED_JOURNAL_BLOCKED or "journal_parse_errors" in blockers:
        return block(EXECUTION_STATUS_BLOCKED_MALFORMED_JOURNAL, "journal_parse_errors")
    if boundary_status == BOUNDARY_STATUS_SEQUENCE_GAP_BLOCKED or "sequence_gaps" in blockers:
        return block(EXECUTION_STATUS_BLOCKED_SEQUENCE_GAP, "sequence_gaps")
    if boundary_status == BOUNDARY_STATUS_MIXED_SEQUENCE_ERAS_BLOCKED or "mixed_sequence_eras" in blockers:
        return block(EXECUTION_STATUS_BLOCKED_MIXED_SEQUENCE_ERAS, "mixed_sequence_eras")
    if boundary_status == BOUNDARY_STATUS_HASH_CHAIN_BOUNDARY_REQUIRED:
        readiness["requires_explicit_boundary_approval"] = True
        return block(EXECUTION_STATUS_BLOCKED_HASH_CHAIN_RISK, "hash_chain_boundary_required")
    if not has_original_sha256:
        return block(EXECUTION_STATUS_BLOCKED_MISSING_JOURNAL, "original_journal_sha256_missing")
    if not has_backup_path:
        return block(EXECUTION_STATUS_BLOCKED_MISSING_BACKUP, "backup_path_missing")

    if compaction_readiness == COMPACTION_READINESS_ARCHIVE_PLAN_ONLY:
        readiness["status"] = EXECUTION_STATUS_ARCHIVE_PLAN_READY
        readiness["archive_execution_allowed"] = True
        readiness["warnings"].append("Archive planning may proceed later, but this helper performs no mutation.")
        return readiness

    if compaction_readiness == COMPACTION_READINESS_REQUIRES_EXPLICIT_BOUNDARY:
        readiness["status"] = EXECUTION_STATUS_COMPACTION_REQUIRES_BOUNDARY_APPROVAL
        readiness["archive_execution_allowed"] = True
        readiness["requires_explicit_boundary_approval"] = True
        readiness["warnings"].append("Compaction requires explicit boundary approval before any future execution.")
        return readiness

    return block(EXECUTION_STATUS_BLOCKED_MISSING_RESTORE_PLAN, "unsupported_execution_readiness_state")


def write_runtime_journal_compaction_manifest_artifact(
    journal_path: str | Path,
    output_path: str | Path,
    *,
    mode: str = "dry_run",
    operation_id: str | None = None,
    created_at: str | None = None,
    archive_dir: str | Path | None = None,
    overwrite: bool = False,
    create_parent_dirs: bool = False,
) -> dict[str, Any]:
    """Write a dry-run manifest JSON artifact to an explicit safe path.

    This writes only the manifest. It never archives, compacts, rewrites, or
    truncates the runtime journal.
    """

    journal = Path(journal_path)
    output = Path(output_path)
    _validate_manifest_output_path(
        journal,
        output,
        overwrite=overwrite,
        create_parent_dirs=create_parent_dirs,
    )

    manifest = build_runtime_journal_compaction_manifest(
        journal,
        mode=mode,
        operation_id=operation_id,
        created_at=created_at,
        archive_dir=archive_dir,
    )
    fatal_blockers = {"journal_missing", "journal_parse_errors", "cannot_plan_missing_journal"}
    if fatal_blockers.intersection(manifest["blockers"]):
        raise ValueError(f"manifest artifact not written because blockers are present: {manifest['blockers']}")

    if create_parent_dirs:
        output.parent.mkdir(parents=True, exist_ok=True)

    data = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    output.write_text(data, encoding="utf-8")
    bytes_written = len(data.encode("utf-8"))

    return {
        "output_path": str(output),
        "bytes_written": bytes_written,
        "manifest_operation_id": manifest["operation_id"],
        "original_journal_sha256": manifest["original_sha256"],
        "dry_run": manifest["mode"] == "dry_run",
        "destructive_default": manifest["destructive_default"],
        "journal_mutated": False,
        "archive_created": False,
        "compacted_journal_created": False,
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


def _record_boundary_sequence(
    sequence: dict[str, Any],
    sequence_num: int | None,
    line_number: int,
    previous_sequence: int | None,
) -> None:
    if sequence_num is None:
        return
    if sequence["first_sequence_num"] is None:
        sequence["first_sequence_num"] = sequence_num
    sequence["last_sequence_num"] = sequence_num
    if previous_sequence is None:
        return
    if sequence_num < previous_sequence:
        sequence["monotonic"] = False
        sequence["decrease_count"] += 1
        sequence["mixed_sequence_eras_suspected"] = True
        sequence["decreases"].append(
            {
                "line": line_number,
                "previous_sequence_num": previous_sequence,
                "sequence_num": sequence_num,
            }
        )
    elif sequence_num > previous_sequence + 1:
        sequence["gap_count"] += 1
        sequence["gaps"].append(
            {
                "line": line_number,
                "after_sequence_num": previous_sequence,
                "sequence_num": sequence_num,
                "missing_count": sequence_num - previous_sequence - 1,
            }
        )


def _record_control_blocks(control: dict[str, Any], control_lines: list[int]) -> None:
    if not control_lines:
        return
    block_count = 1
    for previous, current in zip(control_lines, control_lines[1:]):
        if current != previous + 1:
            block_count += 1
    control["block_count"] = block_count
    first_line = control_lines[0]
    last_line = control_lines[-1]
    control["interleaved_with_runtime_events"] = (last_line - first_line + 1) != len(control_lines)


def _classify_boundary_validation(validation: dict[str, Any]) -> None:
    if validation["parse_error_count"]:
        validation["status"] = BOUNDARY_STATUS_MALFORMED_JOURNAL_BLOCKED
        validation["compaction_readiness"] = COMPACTION_READINESS_BLOCKED
        validation["blockers"].append("journal_parse_errors")
        validation["warnings"].append("Malformed journal lines block archive/compaction planning.")
        return

    sequence = validation["sequence"]
    if sequence["decrease_count"]:
        validation["status"] = BOUNDARY_STATUS_MIXED_SEQUENCE_ERAS_BLOCKED
        validation["compaction_readiness"] = COMPACTION_READINESS_BLOCKED
        validation["blockers"].append("mixed_sequence_eras")
        validation["warnings"].append("Sequence number decreases indicate mixed historical sequence eras.")
        return
    if sequence["gap_count"]:
        validation["status"] = BOUNDARY_STATUS_SEQUENCE_GAP_BLOCKED
        validation["compaction_readiness"] = COMPACTION_READINESS_BLOCKED
        validation["blockers"].append("sequence_gaps")
        validation["warnings"].append("Sequence gaps require explicit replay analysis before compaction.")
        return

    hash_chain = validation["hash_chain"]
    if hash_chain["mismatch_count"]:
        hash_chain["explicit_boundary_required"] = True
        validation["status"] = BOUNDARY_STATUS_HASH_CHAIN_BOUNDARY_REQUIRED
        validation["compaction_readiness"] = COMPACTION_READINESS_REQUIRES_EXPLICIT_BOUNDARY
        validation["warnings"].append("Hash-chain mismatch requires an explicit compaction boundary.")
        return

    control = validation["control_plane"]
    evidence = validation["evidence"]
    if evidence["failed_or_unverified_count"]:
        evidence["preservation_required"] = True
        validation["warnings"].append("Failed or unverified evidence records must be preserved.")

    if not control["event_count"]:
        validation["status"] = BOUNDARY_STATUS_NO_COMPACTION_NEEDED
        validation["compaction_readiness"] = COMPACTION_READINESS_NOT_NEEDED
        return

    hash_chain["explicit_boundary_required"] = True
    if control["interleaved_with_runtime_events"] or control["block_count"] > 1:
        validation["status"] = BOUNDARY_STATUS_BOUNDARY_CANDIDATE_WITH_WARNINGS
        validation["compaction_readiness"] = COMPACTION_READINESS_ARCHIVE_PLAN_ONLY
        validation["warnings"].append("Control-plane bloat is interleaved with runtime events.")
    else:
        validation["status"] = BOUNDARY_STATUS_BOUNDARY_CANDIDATE
        validation["compaction_readiness"] = COMPACTION_READINESS_REQUIRES_EXPLICIT_BOUNDARY
    validation["warnings"].append("Control-plane removal would require an explicit hash-chain boundary.")


def _event_has_failed_or_unverified_evidence(event: dict[str, Any], event_type: str) -> bool:
    payload = event.get("payload")
    if not isinstance(payload, dict):
        return event_type in {"ACTION_FAILED", "VERIFICATION_FAILED"}
    if event_type in {"ACTION_FAILED", "VERIFICATION_FAILED"}:
        return True
    if payload.get("success") is False or payload.get("verified") is False:
        return True
    evidence = payload.get("execution_evidence")
    if not isinstance(evidence, dict):
        return False
    verification_state = str(evidence.get("verification_state") or "").lower()
    return verification_state in {"failed", "unverified"}


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


def _validate_manifest_output_path(
    journal_path: Path,
    output_path: Path,
    *,
    overwrite: bool,
    create_parent_dirs: bool,
) -> None:
    if str(output_path).strip() == "":
        raise ValueError("manifest output path must be explicit")

    resolved_journal = journal_path.resolve(strict=False)
    resolved_output = output_path.resolve(strict=False)
    if resolved_output == resolved_journal:
        raise ValueError("manifest output path cannot be the source journal path")
    if resolved_output.name == resolved_journal.name:
        raise ValueError("manifest output path cannot use the runtime journal filename")
    if output_path.suffix.lower() != ".json":
        raise ValueError("manifest output path must end with .json")
    if any(part in {".next", "node_modules"} for part in resolved_output.parts):
        raise ValueError("manifest output path cannot target frontend build or dependency output")

    allowed_roots = [
        (resolved_journal.parent / dirname).resolve(strict=False)
        for dirname in SAFE_MANIFEST_OUTPUT_DIR_NAMES
    ]
    if not any(_is_relative_to(resolved_output, root) for root in allowed_roots):
        raise ValueError("manifest output path must be under the journal archive or manifests directory")

    if output_path.exists() and not overwrite:
        raise FileExistsError(f"manifest output already exists: {output_path}")
    if not output_path.parent.exists() and not create_parent_dirs:
        raise FileNotFoundError(f"manifest output parent does not exist: {output_path.parent}")


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
