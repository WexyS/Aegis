from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from aegis.core.config import PROJECT_ROOT, get_settings
from aegis.core.app_discovery_smoke import build_configured_app_discovery_smoke
from aegis.core.app_map import get_app_registry_snapshot
from aegis.core.action_timeline import project_action_timeline
from aegis.core.commands import get_approval_manager
from aegis.core.environment import collect_environment_diagnostics
from aegis.core.evidence_audit import audit_action_evidence
from aegis.core.event_journal import get_runtime_journal
from aegis.core.journal_cleanup import build_runtime_replay_gap_diagnostics
from aegis.core.maintenance_actions import build_maintenance_action_proposals
from aegis.core.pending_decision_hygiene import build_pending_decision_hygiene_report
from aegis.core.runtime_authority import peek_runtime_authority
from aegis.core.runtime_timeout import build_runtime_timeout_diagnostics
from aegis.core.system_diagnostics import (
    collect_network_port_snapshot,
    collect_process_resource_snapshot,
    collect_system_resource_snapshot,
)
from aegis.tools.registry import get_tool_registry_snapshot, list_tools, validate_registry_drift


_last_scan: dict[str, Any] | None = None


STATUS_RANK = {"ok": 0, "unknown": 1, "warning": 2, "fail": 3}
CLOSURE_READINESS_VERSION = "foundation-closure-readiness/1"
UNKNOWN_ERA_OPERATOR_ATTENTION_THRESHOLD = 1
LOCAL_CLOSURE_MANIFEST_PATH = Path("archive") / "historical-evidence-replay-quarantine-manifest.json"
FINDING_CATEGORIES = {
    "telemetry",
    "runtime",
    "config",
    "dependency",
    "security",
    "test",
    "documentation",
}
FINDING_SEVERITIES = {"info", "warning", "fail"}


def _worst_status(*statuses: str | None) -> str:
    values = [str(status or "unknown") for status in statuses]
    return max(values or ["unknown"], key=lambda value: STATUS_RANK.get(value, 1))


def _status_from_integrity(journal: dict[str, Any]) -> str:
    if not journal.get("journal_path"):
        return "warning"
    if journal.get("historical_integrity_status") == "broken":
        return "warning"
    return "ok" if journal.get("integrity_status") == "hash-chain" else "warning"


def _command_lifecycle_snapshot(commands: dict[str, Any]) -> dict[str, Any]:
    records = commands.get("records") if isinstance(commands, dict) else []
    records = records if isinstance(records, list) else []
    pending = commands.get("pending_approvals") if isinstance(commands, dict) else []
    pending = pending if isinstance(pending, list) else []
    active = commands.get("active_command") if isinstance(commands, dict) else None
    active_records = [record for record in records if isinstance(record, dict) and record.get("active")]
    stale_active = len(active_records) > 1
    unverified_completed = [
        record for record in records
        if isinstance(record, dict)
        and record.get("status") == "executed"
        and record.get("verification_state") != "verified"
    ]
    return {
        "scan_version": "command-lifecycle/1",
        "read_only": True,
        "status": "warning" if stale_active else "ok",
        "record_count": len(records),
        "pending_count": len(pending),
        "active_count": 1 if isinstance(active, dict) else 0,
        "active_record_count": len(active_records),
        "unverified_completed_count": len(unverified_completed),
        "latest_status": str(records[-1].get("status")) if records and isinstance(records[-1], dict) else None,
        "latest_verification_state": str(records[-1].get("verification_state")) if records and isinstance(records[-1], dict) else None,
    }


def _runtime_snapshot_report(runtime_snapshot: dict[str, Any] | None, journal: dict[str, Any]) -> dict[str, Any]:
    snapshot = runtime_snapshot or {}
    last_runtime_sequence = int(snapshot.get("last_event_sequence") or 0)
    last_journal_sequence = int(journal.get("last_sequence_num") or 0)
    sequence_aligned = last_runtime_sequence == last_journal_sequence
    return {
        "scan_version": "runtime-snapshot/1",
        "read_only": True,
        "status": "ok" if sequence_aligned else "warning",
        "session_id": snapshot.get("session_id"),
        "fsm_state": snapshot.get("fsm_state"),
        "queue_depth": int(snapshot.get("queue_depth") or 0),
        "queue_capacity": int(snapshot.get("queue_capacity") or 0),
        "recovery_depth": int(snapshot.get("recovery_depth") or 0),
        "active_trace_id": snapshot.get("active_trace_id"),
        "last_event_sequence": last_runtime_sequence,
        "journal_last_sequence_num": last_journal_sequence,
        "sequence_aligned": sequence_aligned,
    }


def _action_timeline_report(events: list[dict[str, Any]], *, session_id: str | None) -> dict[str, Any]:
    timeline = project_action_timeline(events, limit=50, session_id=session_id)
    active_count = sum(1 for item in timeline if item.get("status") == "active")
    error_count = sum(1 for item in timeline if item.get("status") == "error")
    evidence_backed = sum(1 for item in timeline if isinstance(item.get("execution_evidence"), dict))
    return {
        "scan_version": "action-timeline-health/1",
        "read_only": True,
        "status": "ok",
        "action_count": len(timeline),
        "active_count": active_count,
        "error_count": error_count,
        "evidence_backed_count": evidence_backed,
        "latest_sequence_num": max((int(item.get("sequence_num") or 0) for item in timeline), default=0),
    }


def _foundation_closure_readiness(checks: dict[str, Any]) -> dict[str, Any]:
    """Read-only closure projection kept separate from runtime health."""

    evidence_audit = checks["evidence_audit"]
    pending_decision_hygiene = checks["pending_decision_hygiene"]
    runtime_timeout_diagnostics = checks["runtime_timeout_diagnostics"]
    replay_diagnostics = checks["replay_diagnostics"]
    command_lifecycle = checks["command_lifecycle"]
    runtime_snapshot = checks["runtime_snapshot"]
    system_resources = checks["system_resources"]
    process_resources = checks["process_resources"]
    network_ports = checks["network_ports"]
    app_discovery = checks["app_discovery"]
    closure_manifest_store = checks.get("historical_debt_closure_manifest_store")
    closure_manifest_store = closure_manifest_store if isinstance(closure_manifest_store, dict) else {}

    current_evidence_failure_count = _int_count(evidence_audit.get("current_evidence_failure_count"))
    current_missing_evidence_count = _int_count(evidence_audit.get("current_missing_evidence_count"))
    historical_evidence_debt_count = _int_count(evidence_audit.get("historical_evidence_debt_count"))
    unknown_era_evidence_issue_count = _int_count(evidence_audit.get("unknown_era_evidence_issue_count"))
    historical_missing_evidence_count = _int_count(evidence_audit.get("historical_missing_evidence_count"))
    unknown_era_missing_evidence_count = _int_count(evidence_audit.get("unknown_era_missing_evidence_count"))
    restored_pending_count = _int_count(pending_decision_hygiene.get("restored_unresolved_count"))
    current_pending_count = _int_count(pending_decision_hygiene.get("current_session_pending_count"))
    pending_count = _int_count(pending_decision_hygiene.get("pending_count"))
    system_resource_warning_count = sum(
        1
        for status in (
            system_resources.get("status"),
            process_resources.get("status"),
            network_ports.get("status"),
        )
        if str(status or "unknown") not in {"ok", "unknown"}
    )
    app_discovery_warning_count = _app_discovery_warning_count(app_discovery)

    replay_status = str(replay_diagnostics.get("status") or "unknown")
    replay_boundary = replay_diagnostics.get("replay_boundary")
    replay_boundary = replay_boundary if isinstance(replay_boundary, dict) else {}
    replay_historical_debt_present = replay_status not in {"ok", "unknown"}
    replay_classification = str(replay_boundary.get("classification") or "unknown")
    manifest_visibility = _closure_manifest_visibility(closure_manifest_store)
    unknown_era_quarantined = _quarantine_covers_unknown_era_evidence(
        evidence_audit,
        manifest_visibility,
    )

    lifecycle_blocker_count = 1 if command_lifecycle.get("status") == "fail" else 0
    runtime_snapshot_blocker_count = 1 if runtime_snapshot.get("status") == "fail" else 0
    pending_decision_blocker_count = pending_count
    runtime_timeout_blocker_count = _int_count(runtime_timeout_diagnostics.get("finding_count"))
    current_blocker_count = (
        current_evidence_failure_count
        + pending_decision_blocker_count
        + runtime_timeout_blocker_count
        + lifecycle_blocker_count
        + runtime_snapshot_blocker_count
    )

    unknown_inputs = []
    if evidence_audit.get("classification") is None:
        unknown_inputs.append("evidence_audit_classification_unavailable")
    if replay_status == "unknown":
        unknown_inputs.append("replay_diagnostics_unknown")

    if current_evidence_failure_count > 0:
        closure_readiness_status = "blocked_current_issue"
    elif current_blocker_count > 0:
        closure_readiness_status = "needs_operator_attention"
    elif unknown_era_evidence_issue_count >= UNKNOWN_ERA_OPERATOR_ATTENTION_THRESHOLD and not unknown_era_quarantined:
        closure_readiness_status = "needs_operator_attention"
    elif unknown_inputs:
        closure_readiness_status = "unknown"
    elif historical_evidence_debt_count > 0 or replay_historical_debt_present or system_resource_warning_count > 0:
        closure_readiness_status = "ready_with_known_historical_debt"
    else:
        closure_readiness_status = "ready"

    status = {
        "ready": "ok",
        "ready_with_known_historical_debt": "warning",
        "needs_operator_attention": "warning",
        "blocked_current_issue": "fail",
        "unknown": "warning",
    }.get(closure_readiness_status, "warning")

    recommendations = _closure_readiness_recommendations(
        closure_readiness_status=closure_readiness_status,
        current_evidence_failure_count=current_evidence_failure_count,
        historical_evidence_debt_count=historical_evidence_debt_count,
        unknown_era_evidence_issue_count=unknown_era_evidence_issue_count,
        replay_historical_debt_present=replay_historical_debt_present,
        pending_decision_blocker_count=pending_decision_blocker_count,
        runtime_timeout_blocker_count=runtime_timeout_blocker_count,
        system_resource_warning_count=system_resource_warning_count,
    )

    return {
        "scan_version": CLOSURE_READINESS_VERSION,
        "read_only": True,
        "mutation_performed": False,
        "status": status,
        "closure_readiness_status": closure_readiness_status,
        "current_blocker_count": current_blocker_count,
        "current_evidence_failure_count": current_evidence_failure_count,
        "current_missing_evidence_count": current_missing_evidence_count,
        "pending_decision_blocker_count": pending_decision_blocker_count,
        "runtime_timeout_blocker_count": runtime_timeout_blocker_count,
        "restored_pending_count": restored_pending_count,
        "current_session_pending_count": current_pending_count,
        "historical_evidence_debt_count": historical_evidence_debt_count,
        "historical_missing_evidence_count": historical_missing_evidence_count,
        "unknown_era_evidence_issue_count": unknown_era_evidence_issue_count,
        "unknown_era_missing_evidence_count": unknown_era_missing_evidence_count,
        "unknown_era_quarantined_by_manifest": unknown_era_quarantined,
        "unknown_era_operator_attention_threshold": UNKNOWN_ERA_OPERATOR_ATTENTION_THRESHOLD,
        "active_operational_debt": {
            "status": "present" if current_blocker_count else "none",
            "current_blocker_count": current_blocker_count,
            "current_evidence_failure_count": current_evidence_failure_count,
            "current_missing_evidence_count": current_missing_evidence_count,
            "pending_decision_blocker_count": pending_decision_blocker_count,
            "runtime_timeout_blocker_count": runtime_timeout_blocker_count,
        },
        "archived_historical_debt": manifest_visibility["archived_historical_debt"],
        "quarantined_unknown_era_debt": manifest_visibility["quarantined_unknown_era_debt"],
        "closure_execution_status": manifest_visibility["closure_execution_status"],
        "closure_plan_id": manifest_visibility["closure_plan_id"],
        "closure_gate_statuses": manifest_visibility["closure_gate_statuses"],
        "closure_remaining_blockers": manifest_visibility["remaining_blockers"],
        "replay_historical_debt_present": replay_historical_debt_present,
        "replay_diagnostics_status": replay_status,
        "replay_boundary_classification": replay_classification,
        "system_resource_warning_count": system_resource_warning_count,
        "app_discovery_warning_count": app_discovery_warning_count,
        "component_inputs": {
            "evidence_audit": evidence_audit.get("status"),
            "pending_decision_hygiene": pending_decision_hygiene.get("status"),
            "runtime_timeout_diagnostics": runtime_timeout_diagnostics.get("status"),
            "command_lifecycle": command_lifecycle.get("status"),
            "runtime_snapshot": runtime_snapshot.get("status"),
            "replay_diagnostics": replay_status,
            "system_resources": system_resources.get("status"),
            "process_resources": process_resources.get("status"),
            "network_ports": network_ports.get("status"),
        },
        "active_runtime_projections": {
            "evidence_audit": _evidence_audit_active_projection(evidence_audit, manifest_visibility),
            "replay_diagnostics": _replay_diagnostics_active_projection(replay_diagnostics, manifest_visibility),
            "runtime_snapshot": _runtime_snapshot_active_projection(runtime_snapshot, manifest_visibility),
        },
        "unknown_inputs": unknown_inputs,
        "recommendation": " ".join(recommendations),
        "guidance": [
            "Runtime health remains the direct component health signal and is not greenwashed by closure readiness.",
            "Historical evidence and replay debt remain visible and require separate hygiene planning.",
            "Unknown-era evidence issues require operator attention until source or session evidence is available.",
            "Maintenance scan performed no mutation and did not resolve approvals, rewrite evidence, or alter journal history.",
            "Foundation release tagging should be a later explicit operator action.",
        ],
    }


def _closure_manifest_store_projection(
    store: dict[str, Any] | None,
    *,
    source: str = "supplied",
    path: str | None = None,
) -> dict[str, Any]:
    records = store if isinstance(store, dict) else {}
    entries = []
    for plan_id in sorted(str(key) for key in records):
        record = records.get(plan_id)
        if isinstance(record, dict):
            entries.append({"plan_id": plan_id, "record": dict(record)})
    latest = entries[-1] if entries else {}
    return {
        "scan_version": "historical-debt-closure-manifest-store-projection/1",
        "read_only": True,
        "mutation_performed": False,
        "status": "ok" if entries else "unknown",
        "source": source,
        "path": path,
        "entry_count": len(entries),
        "latest_plan_id": latest.get("plan_id"),
        "latest_record": latest.get("record"),
        "blockers": [],
    }


def _closure_manifest_store_error_projection(*, path: str, reason: str) -> dict[str, Any]:
    return {
        "scan_version": "historical-debt-closure-manifest-store-projection/1",
        "read_only": True,
        "mutation_performed": False,
        "status": "fail",
        "source": "local_file",
        "path": path,
        "entry_count": 0,
        "latest_plan_id": None,
        "latest_record": None,
        "blockers": [reason],
    }


def _load_local_closure_manifest_store(log_dir: Path) -> dict[str, Any] | None:
    manifest_path = log_dir / LOCAL_CLOSURE_MANIFEST_PATH
    if not manifest_path.exists():
        return None
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return _closure_manifest_store_error_projection(
            path=str(manifest_path),
            reason=f"closure_manifest_read_error:{type(exc).__name__}",
        )
    if not isinstance(payload, dict):
        return _closure_manifest_store_error_projection(
            path=str(manifest_path),
            reason="closure_manifest_not_object",
        )
    return _closure_manifest_store_projection(
        payload,
        source="local_file",
        path=str(manifest_path),
    )


def _closure_manifest_visibility(projection: dict[str, Any]) -> dict[str, Any]:
    record = projection.get("latest_record") if isinstance(projection.get("latest_record"), dict) else {}
    archive = record.get("archive_manifest") if isinstance(record.get("archive_manifest"), dict) else {}
    quarantine = record.get("quarantine_manifest") if isinstance(record.get("quarantine_manifest"), dict) else {}
    gates = record.get("required_gates") if isinstance(record.get("required_gates"), dict) else {}
    gate_statuses = {
        str(name): {
            "status": gate.get("status"),
            "passed": gate.get("passed"),
            "ref": gate.get("ref"),
        }
        for name, gate in gates.items()
        if isinstance(gate, dict)
    }
    if record:
        archived = {
            "status": str(archive.get("status") or "not_archived"),
            "historical_evidence_debt_count": _int_count(archive.get("historical_evidence_debt_count")),
            "historical_missing_evidence_count": _int_count(archive.get("historical_missing_evidence_count")),
            "manifest_ref": archive.get("manifest_ref"),
            "archive_created": archive.get("status") == "archived",
        }
        quarantined = {
            "status": str(quarantine.get("status") or "not_quarantined"),
            "unknown_era_evidence_issue_count": _int_count(quarantine.get("unknown_era_evidence_issue_count")),
            "unknown_era_missing_evidence_count": _int_count(quarantine.get("unknown_era_missing_evidence_count")),
            "manifest_ref": quarantine.get("manifest_ref"),
            "quarantine_created": quarantine.get("status") == "quarantined",
            "unknown_era_reclassified": quarantine.get("unknown_era_reclassified") is True,
        }
        return {
            "archived_historical_debt": archived,
            "quarantined_unknown_era_debt": quarantined,
            "closure_execution_status": str(record.get("status") or "executed_manifest_only"),
            "closure_plan_id": record.get("plan_id"),
            "closure_gate_statuses": gate_statuses,
            "baseline": record.get("baseline") if isinstance(record.get("baseline"), dict) else {},
            "remaining_blockers": [],
        }
    return {
        "archived_historical_debt": {
            "status": "not_archived",
            "historical_evidence_debt_count": 0,
            "historical_missing_evidence_count": 0,
            "manifest_ref": None,
            "archive_created": False,
        },
        "quarantined_unknown_era_debt": {
            "status": "not_quarantined",
            "unknown_era_evidence_issue_count": 0,
            "unknown_era_missing_evidence_count": 0,
            "manifest_ref": None,
            "quarantine_created": False,
            "unknown_era_reclassified": False,
        },
        "closure_execution_status": "not_executed",
        "closure_plan_id": None,
        "closure_gate_statuses": {},
        "baseline": {},
        "remaining_blockers": [],
    }


def _quarantine_covers_unknown_era_evidence(
    evidence_audit: dict[str, Any],
    manifest_visibility: dict[str, Any],
) -> bool:
    quarantined = manifest_visibility.get("quarantined_unknown_era_debt")
    quarantined = quarantined if isinstance(quarantined, dict) else {}
    return (
        manifest_visibility.get("closure_execution_status") == "executed_manifest_only"
        and quarantined.get("status") == "quarantined"
        and quarantined.get("unknown_era_reclassified") is False
        and bool(quarantined.get("manifest_ref"))
        and _int_count(quarantined.get("unknown_era_evidence_issue_count"))
        >= _int_count(evidence_audit.get("unknown_era_evidence_issue_count"))
        and _int_count(quarantined.get("unknown_era_missing_evidence_count"))
        >= _int_count(evidence_audit.get("unknown_era_missing_evidence_count"))
    )


def _evidence_audit_active_projection(
    evidence_audit: dict[str, Any],
    manifest_visibility: dict[str, Any],
) -> dict[str, Any]:
    current_failure = _int_count(evidence_audit.get("current_evidence_failure_count"))
    current_missing = _int_count(evidence_audit.get("current_missing_evidence_count"))
    critical_failure = _int_count(evidence_audit.get("critical_failure_count"))
    unknown_quarantined = _quarantine_covers_unknown_era_evidence(evidence_audit, manifest_visibility)
    historical_debt = _int_count(evidence_audit.get("historical_evidence_debt_count"))
    historical_missing = _int_count(evidence_audit.get("historical_missing_evidence_count"))
    active_failure = bool(current_failure or current_missing)
    if active_failure:
        status = "fail"
        classification = "active_evidence_failure"
    elif unknown_quarantined or historical_debt or historical_missing:
        status = "warning"
        classification = "quarantined_or_archived_evidence_attention"
    else:
        status = str(evidence_audit.get("status") or "unknown")
        classification = "raw_evidence_status"
    return {
        "status": status,
        "classification": classification,
        "raw_status": evidence_audit.get("status"),
        "active_evidence_failure_count": current_failure,
        "active_missing_evidence_count": current_missing,
        "critical_failure_count": critical_failure,
        "quarantined_unknown_era_evidence_issue_count": _int_count(evidence_audit.get("unknown_era_evidence_issue_count"))
        if unknown_quarantined else 0,
        "quarantined_unknown_era_missing_evidence_count": _int_count(evidence_audit.get("unknown_era_missing_evidence_count"))
        if unknown_quarantined else 0,
        "missing_evidence_fabricated": False,
        "evidence_created": False,
    }


def _replay_diagnostics_active_projection(
    replay_diagnostics: dict[str, Any],
    manifest_visibility: dict[str, Any],
) -> dict[str, Any]:
    raw_status = str(replay_diagnostics.get("status") or "unknown")
    boundary = replay_diagnostics.get("replay_boundary")
    boundary = boundary if isinstance(boundary, dict) else {}
    classification = str(boundary.get("classification") or "unknown")
    gates = manifest_visibility.get("closure_gate_statuses")
    gates = gates if isinstance(gates, dict) else {}
    replay_gate = gates.get("replay_hash_chain") if isinstance(gates.get("replay_hash_chain"), dict) else {}
    manifest_backed = (
        manifest_visibility.get("closure_execution_status") == "executed_manifest_only"
        and replay_gate.get("passed") is True
        and replay_gate.get("status") in {"not_required_for_manifest_only", "passed", "verified", "ok"}
    )
    legacy_boundary = classification in {
        "historical_mixed_sequence_eras_or_reset_boundaries",
        "historical_control_plane_bloat",
    }
    if raw_status == "fail" and manifest_backed and legacy_boundary:
        status = "warning"
        active_failure = False
        projection = "manifest_backed_quarantined_replay_boundary"
    else:
        status = raw_status
        active_failure = raw_status == "fail"
        projection = "raw_replay_status"
    return {
        "status": status,
        "classification": projection,
        "raw_status": raw_status,
        "replay_boundary_classification": classification,
        "manifest_backed": manifest_backed,
        "active_replay_failure": active_failure,
        "original_replay_state_touched": False,
    }


def _runtime_snapshot_active_projection(
    runtime_snapshot: dict[str, Any],
    manifest_visibility: dict[str, Any],
) -> dict[str, Any]:
    baseline = manifest_visibility.get("baseline")
    baseline = baseline if isinstance(baseline, dict) else {}
    sequence_aligned = runtime_snapshot.get("sequence_aligned") is True
    baseline_clean = baseline.get("status") == "clean_current_operational_baseline"
    if sequence_aligned:
        status = "ok"
        classification = "snapshot_aligned"
    elif baseline_clean and runtime_snapshot.get("status") == "warning":
        status = "warning"
        classification = "stale_snapshot_projection_with_clean_current_baseline"
    else:
        status = str(runtime_snapshot.get("status") or "unknown")
        classification = "raw_runtime_snapshot_status"
    return {
        "status": status,
        "classification": classification,
        "raw_status": runtime_snapshot.get("status"),
        "sequence_aligned": sequence_aligned,
        "clean_operational_baseline_status": baseline.get("status"),
        "snapshot_rewritten": False,
    }


def _websocket_report(
    *,
    session_id: str | None,
    websocket_clients: int | None,
    queue_depth: int | None,
    queue_capacity: int | None,
) -> dict[str, Any]:
    known = websocket_clients is not None
    return {
        "scan_version": "websocket-runtime/1",
        "read_only": True,
        "status": "ok" if known else "unknown",
        "session_id": session_id,
        "connected_clients": websocket_clients,
        "queue_depth": queue_depth,
        "queue_capacity": queue_capacity,
    }


def _runtime_health_summary(checks: dict[str, Any]) -> dict[str, Any]:
    raw_statuses = {
        "event_journal": checks["event_journal"]["status"],
        "evidence_audit": checks["evidence_audit"]["status"],
        "tool_registry": checks["tool_registry"]["status"],
        "app_registry": checks["app_registry"].get("status", "ok"),
        "environment": checks["environment"]["overall_status"],
        "command_lifecycle": checks["command_lifecycle"]["status"],
        "pending_decision_hygiene": checks["pending_decision_hygiene"]["status"],
        "runtime_timeout_diagnostics": checks["runtime_timeout_diagnostics"]["status"],
        "runtime_snapshot": checks["runtime_snapshot"]["status"],
        "replay_diagnostics": checks["replay_diagnostics"]["status"],
        "websocket": checks["websocket"]["status"],
        "action_timeline": checks["action_timeline"]["status"],
        "system_resources": checks["system_resources"]["status"],
        "process_resources": checks["process_resources"]["status"],
        "network_ports": checks["network_ports"]["status"],
        "workspace_directories": checks["workspace_directories"]["status"],
    }
    if "historical_debt_closure_manifest_store" in checks:
        raw_statuses["historical_debt_closure_manifest_store"] = checks[
            "historical_debt_closure_manifest_store"
        ].get("status", "unknown")
    statuses = dict(raw_statuses)
    closure = checks.get("foundation_closure_readiness")
    projections = closure.get("active_runtime_projections") if isinstance(closure, dict) else {}
    projections = projections if isinstance(projections, dict) else {}
    for name in ("evidence_audit", "replay_diagnostics", "runtime_snapshot"):
        projection = projections.get(name) if isinstance(projections.get(name), dict) else {}
        projected_status = projection.get("status")
        if projected_status:
            statuses[name] = str(projected_status)
    reasons = [
        name for name, status in statuses.items()
        if status not in {"ok", "unknown"}
    ]
    active_failures = [
        name for name, status in statuses.items()
        if status == "fail"
    ]
    return {
        "scan_version": "runtime-health/1",
        "read_only": True,
        "status": _worst_status(*statuses.values()),
        "source_of_truth": "backend_snapshot_protocol_event_journal",
        "component_statuses": statuses,
        "raw_component_statuses": raw_statuses,
        "active_failure_components": active_failures,
        "active_runtime_projections": projections,
        "attention": reasons[:10],
    }


def _documentation_report(project_root: Path) -> dict[str, Any]:
    readme = project_root / "README.md"
    return {
        "scan_version": "documentation-check/1",
        "read_only": True,
        "status": "ok" if readme.exists() else "warning",
        "readme_path": str(readme),
        "readme_present": readme.exists(),
    }


def _workspace_directories_report(project_root: Path) -> dict[str, Any]:
    directories = {
        "logs": project_root / "logs",
        "scratch": project_root / "scratch",
    }
    directory_status = {
        name: {
            "path": str(path),
            "exists": path.exists(),
            "is_dir": path.is_dir() if path.exists() else False,
        }
        for name, path in directories.items()
    }
    missing = [
        name
        for name, status in directory_status.items()
        if not status["exists"] or not status["is_dir"]
    ]
    return {
        "scan_version": "workspace-directories/1",
        "read_only": True,
        "status": "ok" if not missing else "warning",
        "directories": directory_status,
        "missing": missing,
    }


def _read_only_contract() -> dict[str, Any]:
    return {
        "scan_version": "maintenance-read-only-contract/1",
        "read_only": True,
        "status": "ok",
        "prohibited_mutations": [
            "files",
            "config",
            "database",
            "runtime_fsm",
            "git",
            "app_registry_refresh",
        ],
        "observed_mutations": [],
        "allowed_observations": [
            "backend_snapshot",
            "event_journal_snapshot",
            "runtime_replay_gap_diagnostics",
            "pending_decision_hygiene_diagnostics",
            "runtime_timeout_diagnostics",
            "evidence_audit_classification",
            "recent_event_tail",
            "tool_registry_snapshot",
            "app_registry_snapshot",
            "app_discovery_smoke",
            "environment_version_checks",
            "system_resource_snapshot",
            "process_resource_snapshot",
            "network_port_snapshot",
            "workspace_directory_snapshot",
            "foundation_closure_readiness_projection",
            "historical_debt_closure_manifest_projection",
        ],
        "allowed_ephemeral_state": [
            "last_maintenance_scan_cache",
        ],
    }


def _finding(
    finding_id: str,
    *,
    category: str,
    severity: str,
    source: str,
    reason: str,
    evidence: dict[str, Any],
    recommendation: str,
) -> dict[str, Any]:
    if category not in FINDING_CATEGORIES:
        category = "runtime"
    if severity not in FINDING_SEVERITIES:
        severity = "warning"
    return {
        "finding_id": finding_id,
        "category": category,
        "severity": severity,
        "source": source,
        "reason": reason,
        "evidence": evidence,
        "recommendation": recommendation,
        "read_only": True,
    }


def _environment_findings(environment: dict[str, Any]) -> list[dict[str, Any]]:
    checks = environment.get("checks") if isinstance(environment, dict) else {}
    checks = checks if isinstance(checks, dict) else {}
    category_by_check = {
        "python": "dependency",
        "pytest": "test",
        "playwright": "test",
        "git": "dependency",
        "node": "dependency",
        "npm": "dependency",
        "frontend": "config",
    }
    recommendation_by_check = {
        "python": r"Use the project virtualenv before running backend validation.",
        "pytest": "Install Python dev dependencies before relying on backend tests.",
        "playwright": "Install Playwright before running browser smoke validation.",
        "git": "Install Git for Windows or add the detected Git executable to PATH.",
        "node": "Install Node.js 20+ before running the frontend.",
        "npm": "Install npm with Node.js and prefer npm.cmd on Windows.",
        "frontend": "Keep frontend/package.json available before running UI checks.",
    }
    findings: list[dict[str, Any]] = []
    for name, check in checks.items():
        if not isinstance(check, dict) or check.get("status") == "ok":
            continue
        findings.append(_finding(
            f"environment.{name}",
            category=category_by_check.get(str(name), "dependency"),
            severity="warning",
            source=f"checks.environment.checks.{name}",
            reason=f"Environment check '{name}' reported {check.get('status', 'unknown')}.",
            evidence=dict(check),
            recommendation=recommendation_by_check.get(str(name), "Resolve the reported environment check before release validation."),
        ))
    return findings


def _findings_from_checks(checks: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    runtime_snapshot = checks["runtime_snapshot"]
    if runtime_snapshot.get("sequence_aligned") is False:
        findings.append(_finding(
            "runtime.snapshot.sequence_drift",
            category="runtime",
            severity="warning",
            source="checks.runtime_snapshot.sequence_aligned",
            reason="Runtime snapshot sequence does not match the event journal tail.",
            evidence={
                "last_event_sequence": runtime_snapshot.get("last_event_sequence"),
                "journal_last_sequence_num": runtime_snapshot.get("journal_last_sequence_num"),
            },
            recommendation="Replay from the event journal before trusting runtime snapshot state.",
        ))

    command_lifecycle = checks["command_lifecycle"]
    if int(command_lifecycle.get("active_record_count") or 0) > 1:
        findings.append(_finding(
            "runtime.command_lifecycle.multiple_active_records",
            category="runtime",
            severity="fail",
            source="checks.command_lifecycle.active_record_count",
            reason="More than one command record is marked active.",
            evidence={"active_record_count": command_lifecycle.get("active_record_count")},
            recommendation="Inspect command lifecycle emission before accepting new command work.",
        ))
    if int(command_lifecycle.get("unverified_completed_count") or 0) > 0:
        evidence_audit = checks["evidence_audit"]
        findings.append(_finding(
            "runtime.command_lifecycle.unverified_completed",
            category="runtime",
            severity="warning",
            source="checks.command_lifecycle.unverified_completed_count",
            reason="At least one executed command is not backed by verified evidence.",
            evidence={
                "unverified_completed_count": command_lifecycle.get("unverified_completed_count"),
                "current_unverified_completed_count": evidence_audit.get("current_unverified_completed_count"),
                "historical_unverified_completed_count": evidence_audit.get("historical_unverified_completed_count"),
                "unknown_era_unverified_completed_count": evidence_audit.get("unknown_era_unverified_completed_count"),
            },
            recommendation=(
                "Route completed commands through evidence audit before displaying success; historical "
                "or unknown-era debt must stay visible and must not be marked verified without evidence."
            ),
        ))

    pending_decision_hygiene = checks["pending_decision_hygiene"]
    if int(pending_decision_hygiene.get("restored_unresolved_count") or 0) > 0:
        findings.append(_finding(
            "runtime.pending_decision_hygiene.restored_unresolved",
            category="runtime",
            severity="warning",
            source="checks.pending_decision_hygiene.restored_unresolved_count",
            reason="Backend command lifecycle contains restored unresolved pending decisions.",
            evidence={
                "pending_count": pending_decision_hygiene.get("pending_count"),
                "restored_unresolved_count": pending_decision_hygiene.get("restored_unresolved_count"),
                "stale_restored_unresolved_count": pending_decision_hygiene.get("stale_restored_unresolved_count"),
                "restored_unresolved_executable_count": pending_decision_hygiene.get(
                    "restored_unresolved_executable_count"
                ),
                "restored_closure_candidate_count": pending_decision_hygiene.get(
                    "restored_closure_candidate_count"
                ),
                "restored_requires_operator_attention_count": pending_decision_hygiene.get(
                    "restored_requires_operator_attention_count"
                ),
                "restored_closure_blocked_count": pending_decision_hygiene.get(
                    "restored_closure_blocked_count"
                ),
                "unknown_age_count": pending_decision_hygiene.get("unknown_age_count"),
                "approval_count": pending_decision_hygiene.get("approval_count"),
                "clarification_count": pending_decision_hygiene.get("clarification_count"),
                "top_command_texts": pending_decision_hygiene.get("top_command_texts", []),
            },
            recommendation=(
                "Review restored decisions through backend lifecycle controls; do not hide, delete, "
                "or bulk-resolve them without a future explicit operator-confirmed hygiene flow."
            ),
        ))

    runtime_timeout_diagnostics = checks["runtime_timeout_diagnostics"]
    if int(runtime_timeout_diagnostics.get("finding_count") or 0) > 0:
        findings.append(_finding(
            "runtime.timeout.diagnostics_attention",
            category="runtime",
            severity="fail" if runtime_timeout_diagnostics.get("status") == "fail" else "warning",
            source="checks.runtime_timeout_diagnostics.finding_count",
            reason="Runtime timeout diagnostics classified overdue or retry-exhausted command lifecycle phases.",
            evidence={
                "finding_count": runtime_timeout_diagnostics.get("finding_count"),
                "overdue_count": runtime_timeout_diagnostics.get("overdue_count"),
                "retry_exhausted_count": runtime_timeout_diagnostics.get("retry_exhausted_count"),
                "negative_evidence_required_count": runtime_timeout_diagnostics.get("negative_evidence_required_count"),
                "phase_counts": runtime_timeout_diagnostics.get("phase_counts", {}),
                "timeout_kind_counts": runtime_timeout_diagnostics.get("timeout_kind_counts", {}),
            },
            recommendation=(
                "Review the backend command lifecycle snapshot; timeout fallback cannot approve, resume, "
                "dispatch, retry, kill browser/process state, or mark verifier success."
            ),
        ))

    evidence_audit = checks["evidence_audit"]
    if int(evidence_audit.get("critical_failure_count") or 0) > 0:
        findings.append(_finding(
            "runtime.evidence_audit.critical_failure",
            category="runtime",
            severity="fail",
            source="checks.evidence_audit.critical_failure_count",
            reason="Evidence audit found failed critical verification checks.",
            evidence={
                "critical_failure_count": evidence_audit.get("critical_failure_count"),
                "current_evidence_failure_count": evidence_audit.get("current_evidence_failure_count"),
                "historical_evidence_debt_count": evidence_audit.get("historical_evidence_debt_count"),
                "unknown_era_evidence_issue_count": evidence_audit.get("unknown_era_evidence_issue_count"),
                "verifier_check_failure_count": evidence_audit.get("verifier_check_failure_count"),
                "critical_failures": evidence_audit.get("critical_failures", []),
            },
            recommendation="Treat affected actions as failed or unverified until verifier evidence is corrected.",
        ))
    if int(evidence_audit.get("missing_evidence_count") or 0) > 0:
        findings.append(_finding(
            "runtime.evidence_audit.missing_evidence",
            category="runtime",
            severity="warning",
            source="checks.evidence_audit.missing_evidence_count",
            reason="Some completed or failed actions have no execution evidence.",
            evidence={
                "missing_evidence_count": evidence_audit.get("missing_evidence_count"),
                "current_missing_evidence_count": evidence_audit.get("current_missing_evidence_count"),
                "historical_missing_evidence_count": evidence_audit.get("historical_missing_evidence_count"),
                "unknown_era_missing_evidence_count": evidence_audit.get("unknown_era_missing_evidence_count"),
            },
            recommendation=(
                "Prevent optimistic completion when execution evidence is absent; current missing "
                "evidence requires investigation and historical or unknown-era gaps require hygiene classification."
            ),
        ))

    websocket = checks["websocket"]
    if websocket.get("status") == "unknown":
        findings.append(_finding(
            "telemetry.websocket.client_count_unknown",
            category="telemetry",
            severity="info",
            source="checks.websocket.connected_clients",
            reason="Maintenance scan did not receive live websocket client count.",
            evidence={"connected_clients": websocket.get("connected_clients")},
            recommendation="Pass websocket runtime context when invoking scan from a live socket session.",
        ))

    system_resources = checks["system_resources"]
    if system_resources.get("status") == "unknown":
        findings.append(_finding(
            "telemetry.system_resources.unavailable",
            category="telemetry",
            severity="warning",
            source="checks.system_resources.status",
            reason="System resource snapshot could not be collected.",
            evidence={"status": system_resources.get("status"), "error": system_resources.get("error")},
            recommendation="Verify psutil can read local system resource counters before relying on telemetry.",
        ))
    elif system_resources.get("status") == "warning":
        findings.append(_finding(
            "telemetry.system_resources.pressure",
            category="telemetry",
            severity="warning",
            source="checks.system_resources",
            reason="System resource snapshot reported high CPU, memory, or disk pressure.",
            evidence={
                "cpu_percent": system_resources.get("cpu_percent"),
                "memory": system_resources.get("memory"),
                "disk": system_resources.get("disk"),
            },
            recommendation="Review resource pressure before starting long-running desktop automation.",
        ))

    process_resources = checks["process_resources"]
    if process_resources.get("status") == "unknown":
        findings.append(_finding(
            "telemetry.process_resources.unavailable",
            category="telemetry",
            severity="warning",
            source="checks.process_resources.status",
            reason="Process resource snapshot could not be collected.",
            evidence={"status": process_resources.get("status"), "error": process_resources.get("error")},
            recommendation="Verify psutil can enumerate local processes before relying on process diagnostics.",
        ))
    elif int(process_resources.get("skipped_count") or 0) > 0:
        findings.append(_finding(
            "telemetry.process_resources.partial",
            category="telemetry",
            severity="info",
            source="checks.process_resources.skipped_count",
            reason="Process resource snapshot skipped at least one process due to access or lifecycle changes.",
            evidence={
                "skipped": process_resources.get("skipped"),
                "skipped_count": process_resources.get("skipped_count"),
            },
            recommendation="Treat process resource rankings as partial when skipped process count is non-zero.",
        ))

    network_ports = checks["network_ports"]
    if network_ports.get("status") == "unknown":
        findings.append(_finding(
            "telemetry.network_ports.unavailable",
            category="telemetry",
            severity="warning",
            source="checks.network_ports.status",
            reason="Development port listener snapshot could not be collected.",
            evidence={"status": network_ports.get("status"), "error": network_ports.get("error")},
            recommendation="Verify psutil can inspect local network connections before relying on port diagnostics.",
        ))
    else:
        ports = network_ports.get("ports") if isinstance(network_ports.get("ports"), list) else []
        for port in ports:
            if not isinstance(port, dict) or port.get("status") != "listening":
                continue
            port_number = port.get("port")
            findings.append(_finding(
                f"telemetry.network_ports.{port_number}.listening",
                category="telemetry",
                severity="info",
                source=f"checks.network_ports.ports.{port_number}",
                reason=f"Development port {port_number} is currently listening.",
                evidence=dict(port),
                recommendation="Use listener PID and process evidence before assuming which service owns this port.",
            ))

    action_timeline = checks["action_timeline"]
    if int(action_timeline.get("error_count") or 0) > 0:
        findings.append(_finding(
            "telemetry.action_timeline.errors_present",
            category="telemetry",
            severity="warning",
            source="checks.action_timeline.error_count",
            reason="Action timeline contains failed actions.",
            evidence={"error_count": action_timeline.get("error_count")},
            recommendation="Use the action timeline evidence to inspect the latest failed actions.",
        ))

    event_journal = checks["event_journal"]
    if event_journal.get("status") != "ok":
        findings.append(_finding(
            "runtime.event_journal.integrity_attention",
            category="runtime",
            severity="warning",
            source="checks.event_journal.status",
            reason="Event journal integrity is not fully healthy.",
            evidence={
                "status": event_journal.get("status"),
                "integrity_status": event_journal.get("integrity_status"),
                "historical_integrity_status": event_journal.get("historical_integrity_status"),
                "historical_integrity_breaks": event_journal.get("historical_integrity_breaks"),
                "journal_path": event_journal.get("journal_path"),
            },
            recommendation="Repair or rotate the journal only after preserving evidence for replay.",
        ))

    replay_diagnostics = checks["replay_diagnostics"]
    if replay_diagnostics.get("status") not in {"ok", "unknown"}:
        sequence = replay_diagnostics.get("sequence") if isinstance(replay_diagnostics, dict) else {}
        sequence = sequence if isinstance(sequence, dict) else {}
        control_plane = replay_diagnostics.get("control_plane") if isinstance(replay_diagnostics, dict) else {}
        control_plane = control_plane if isinstance(control_plane, dict) else {}
        replay_boundary = replay_diagnostics.get("replay_boundary") if isinstance(replay_diagnostics, dict) else {}
        replay_boundary = replay_boundary if isinstance(replay_boundary, dict) else {}
        findings.append(_finding(
            "runtime.replay_gap.diagnostics_attention",
            category="runtime",
            severity="fail" if replay_diagnostics.get("status") == "fail" else "warning",
            source="checks.replay_diagnostics.status",
            reason="Runtime replay diagnostics found journal sequence or replay-boundary attention.",
            evidence={
                "status": replay_diagnostics.get("status"),
                "classification": replay_boundary.get("classification"),
                "cleanup_execution_blocked": replay_boundary.get("cleanup_execution_blocked"),
                "parse_error_count": replay_diagnostics.get("parse_error_count"),
                "decrease_count": sequence.get("decrease_count"),
                "gap_count": sequence.get("gap_count"),
                "duplicate_occurrence_count": sequence.get("duplicate_occurrence_count"),
                "duplicate_sequence_count": sequence.get("duplicate_sequence_count"),
                "snapshot_created_count": control_plane.get("snapshot_created_count"),
                "system_online_count": control_plane.get("system_online_count"),
                "recursive_snapshot_risk_count": control_plane.get("recursive_snapshot_risk_count"),
            },
            recommendation=(
                "Treat replay diagnostics as read-only planning input; do not archive, compact, resequence, "
                "or hide restored decisions without an explicit operator-approved cleanup sprint."
            ),
        ))

    foundation_closure = checks.get("foundation_closure_readiness")
    if isinstance(foundation_closure, dict) and foundation_closure.get("status") not in {"ok", "unknown"}:
        closure_status = str(foundation_closure.get("closure_readiness_status") or "unknown")
        findings.append(_finding(
            "runtime.foundation_closure.readiness_attention",
            category="runtime",
            severity="fail" if closure_status == "blocked_current_issue" else "warning",
            source="checks.foundation_closure_readiness.closure_readiness_status",
            reason=f"Foundation closure readiness is {closure_status}; runtime health remains separate.",
            evidence={
                "closure_readiness_status": closure_status,
                "current_blocker_count": foundation_closure.get("current_blocker_count"),
                "current_evidence_failure_count": foundation_closure.get("current_evidence_failure_count"),
                "pending_decision_blocker_count": foundation_closure.get("pending_decision_blocker_count"),
                "restored_pending_count": foundation_closure.get("restored_pending_count"),
                "historical_evidence_debt_count": foundation_closure.get("historical_evidence_debt_count"),
                "unknown_era_evidence_issue_count": foundation_closure.get("unknown_era_evidence_issue_count"),
                "replay_historical_debt_present": foundation_closure.get("replay_historical_debt_present"),
                "system_resource_warning_count": foundation_closure.get("system_resource_warning_count"),
            },
            recommendation=str(foundation_closure.get("recommendation") or "Review closure readiness inputs without mutating runtime history."),
        ))

    tool_registry = checks["tool_registry"]
    if tool_registry.get("status") != "ok":
        findings.append(_finding(
            "config.tool_registry.drift",
            category="config",
            severity="warning",
            source="checks.tool_registry.status",
            reason="Tool registry drift check did not return ok.",
            evidence={"status": tool_registry.get("status"), "registry": tool_registry.get("registry")},
            recommendation="Resolve config/code/spec drift before exposing new tool behavior.",
        ))

    logging_check = checks["logging"]
    if logging_check.get("status") != "ok":
        findings.append(_finding(
            "config.logging.directory_missing",
            category="config",
            severity="warning",
            source="checks.logging.directory",
            reason="Configured logging directory does not exist.",
            evidence=dict(logging_check),
            recommendation="Create the configured logging directory before long-running runtime sessions.",
        ))

    workspace_directories = checks["workspace_directories"]
    directories = workspace_directories.get("directories") if isinstance(workspace_directories, dict) else {}
    scratch = directories.get("scratch") if isinstance(directories, dict) else None
    if isinstance(scratch, dict) and (scratch.get("exists") is False or scratch.get("is_dir") is False):
        findings.append(_finding(
            "config.workspace.scratch_missing",
            category="config",
            severity="info",
            source="checks.workspace_directories.directories.scratch",
            reason="Local scratch directory does not exist.",
            evidence=dict(scratch),
            recommendation="Create the scratch directory before writing local test or smoke artifacts.",
        ))

    safety = checks["safety"]
    if not safety.get("safe_mode") or not safety.get("dry_run_default"):
        findings.append(_finding(
            "security.safety_defaults.live_mode",
            category="security",
            severity="info",
            source="checks.safety",
            reason="Runtime safety defaults permit live execution when approval policy allows it.",
            evidence={"safe_mode": safety.get("safe_mode"), "dry_run_default": safety.get("dry_run_default")},
            recommendation="Keep medium and higher risk actions approval-gated when live execution is enabled.",
        ))

    documentation = checks["documentation"]
    if documentation.get("status") != "ok":
        findings.append(_finding(
            "documentation.readme.missing",
            category="documentation",
            severity="warning",
            source="checks.documentation.readme_present",
            reason="Project README was not found.",
            evidence=dict(documentation),
            recommendation="Restore README.md before sharing or packaging the project.",
        ))

    findings.extend(_environment_findings(checks["environment"]))
    return findings


def _int_count(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _app_discovery_warning_count(app_discovery: dict[str, Any]) -> int:
    entries = app_discovery.get("entries") if isinstance(app_discovery, dict) else []
    if not isinstance(entries, list):
        return 0
    warning_count = 0
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        blockers = entry.get("verification_blockers")
        if isinstance(blockers, list) and blockers:
            warning_count += 1
            continue
        state = str(entry.get("diagnostic_state") or entry.get("ambiguity_status") or "unknown")
        if state not in {"ok", "known", "verifiable", "unknown"}:
            warning_count += 1
    return warning_count


def _closure_readiness_recommendations(
    *,
    closure_readiness_status: str,
    current_evidence_failure_count: int,
    historical_evidence_debt_count: int,
    unknown_era_evidence_issue_count: int,
    replay_historical_debt_present: bool,
    pending_decision_blocker_count: int,
    runtime_timeout_blocker_count: int,
    system_resource_warning_count: int,
) -> list[str]:
    recommendations = []
    if closure_readiness_status == "blocked_current_issue":
        recommendations.append("Current runtime blockers require investigation before closure.")
    if pending_decision_blocker_count:
        recommendations.append("Pending decisions require backend lifecycle resolution; no auto-resolution was performed.")
    if runtime_timeout_blocker_count:
        recommendations.append("Runtime timeout diagnostics require operator review; no fallback execution was performed.")
    if current_evidence_failure_count:
        recommendations.append("Current evidence failures remain visible and must not be marked verified without evidence.")
    if historical_evidence_debt_count:
        recommendations.append("Historical evidence debt remains visible and should be handled by a separate hygiene design.")
    if unknown_era_evidence_issue_count:
        recommendations.append("Unknown-era evidence issues require operator attention instead of guessed historical classification.")
    if replay_historical_debt_present:
        recommendations.append("Replay diagnostics still show historical journal debt; cleanup execution remains out of scope.")
    if system_resource_warning_count:
        recommendations.append("System resource warnings are environmental and should be reviewed before long-running automation.")
    if not recommendations:
        recommendations.append("No current blockers, pending decisions, historical evidence debt, replay debt, or resource warnings were classified.")
    recommendations.append("No mutation was performed by this maintenance scan.")
    return recommendations


def _finding_summary(findings: list[dict[str, Any]]) -> dict[str, Any]:
    by_category = {category: 0 for category in sorted(FINDING_CATEGORIES)}
    by_severity = {severity: 0 for severity in sorted(FINDING_SEVERITIES)}
    for finding in findings:
        by_category[str(finding.get("category"))] = by_category.get(str(finding.get("category")), 0) + 1
        by_severity[str(finding.get("severity"))] = by_severity.get(str(finding.get("severity")), 0) + 1
    return {
        "scan_version": "maintenance-finding-summary/1",
        "read_only": True,
        "total": len(findings),
        "by_category": by_category,
        "by_severity": by_severity,
    }


def run_read_only_maintenance_scan(
    *,
    runtime_snapshot: dict[str, Any] | None = None,
    session_id: str | None = None,
    websocket_clients: int | None = None,
    queue_depth: int | None = None,
    queue_capacity: int | None = None,
    closure_manifest_store: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Read-only health report for runtime maintenance v1."""
    global _last_scan
    settings = get_settings()
    runtime_journal = get_runtime_journal()
    journal = runtime_journal.snapshot()
    journal_path = journal.get("journal_path") or (Path(settings.logging.directory) / "runtime_events.jsonl")
    replay_diagnostics = build_runtime_replay_gap_diagnostics(journal_path)
    recent_events = runtime_journal.recent_events()
    if runtime_snapshot is None:
        authority = peek_runtime_authority()
        runtime_snapshot = authority.snapshot(journal) if authority else None
    effective_session_id = session_id or (runtime_snapshot or {}).get("session_id")
    app_registry = get_app_registry_snapshot()
    app_registry["read_only"] = True
    app_registry["status"] = "ok"
    app_discovery = build_configured_app_discovery_smoke()
    log_dir = Path(settings.logging.directory)
    commands = get_approval_manager().snapshot()
    evidence_audit = audit_action_evidence(
        recent_events,
        limit=50,
        include_full_classification_export=True,
        session_id=effective_session_id,
        include_historical=True,
        commands_snapshot=commands,
        replay_diagnostics=replay_diagnostics,
    )
    command_lifecycle = _command_lifecycle_snapshot(commands)
    pending_decision_hygiene = build_pending_decision_hygiene_report(commands)
    runtime_timeout_diagnostics = build_runtime_timeout_diagnostics(commands)
    runtime_snapshot_check = _runtime_snapshot_report(runtime_snapshot, journal)
    websocket = _websocket_report(
        session_id=effective_session_id,
        websocket_clients=websocket_clients,
        queue_depth=queue_depth if queue_depth is not None else runtime_snapshot_check.get("queue_depth"),
        queue_capacity=queue_capacity if queue_capacity is not None else runtime_snapshot_check.get("queue_capacity"),
    )
    action_timeline = _action_timeline_report(recent_events, session_id=effective_session_id)
    tool_registry = {
        "status": validate_registry_drift()["status"],
        "registered_tools": sorted(list_tools()),
        "registry": get_tool_registry_snapshot(),
    }
    event_journal = {
        "status": _status_from_integrity(journal),
        "event_count": journal.get("event_count", 0),
        "last_sequence_num": journal.get("last_sequence_num", 0),
        "last_event_hash": journal.get("last_event_hash"),
        "integrity_status": journal.get("integrity_status"),
        "historical_integrity_status": journal.get("historical_integrity_status"),
        "historical_integrity_breaks": journal.get("historical_integrity_breaks", 0),
        "journal_path": journal.get("journal_path"),
    }
    environment = collect_environment_diagnostics()
    system_resources = collect_system_resource_snapshot()
    process_resources = collect_process_resource_snapshot()
    network_ports = collect_network_port_snapshot()
    logging_check = {
        "status": "ok" if log_dir.exists() else "warning",
        "directory": str(log_dir),
    }
    safety = {
        "status": "ok",
        "safe_mode": settings.safety.safe_mode,
        "dry_run_default": settings.safety.dry_run_default,
    }
    documentation = _documentation_report(PROJECT_ROOT)
    workspace_directories = _workspace_directories_report(PROJECT_ROOT)
    read_only_contract = _read_only_contract()
    closure_manifest_projection = (
        _closure_manifest_store_projection(closure_manifest_store)
        if closure_manifest_store is not None
        else _load_local_closure_manifest_store(log_dir)
    )
    checks = {
        "tool_registry": tool_registry,
        "event_journal": event_journal,
        "replay_diagnostics": replay_diagnostics,
        "evidence_audit": evidence_audit,
        "app_registry": app_registry,
        "app_discovery": app_discovery,
        "environment": environment,
        "logging": logging_check,
        "safety": safety,
        "documentation": documentation,
        "workspace_directories": workspace_directories,
        "read_only_contract": read_only_contract,
        "command_lifecycle": command_lifecycle,
        "pending_decision_hygiene": pending_decision_hygiene,
        "runtime_timeout_diagnostics": runtime_timeout_diagnostics,
        "runtime_snapshot": runtime_snapshot_check,
        "websocket": websocket,
        "action_timeline": action_timeline,
        "system_resources": system_resources,
        "process_resources": process_resources,
        "network_ports": network_ports,
    }
    if closure_manifest_projection is not None:
        checks["historical_debt_closure_manifest_store"] = closure_manifest_projection
    checks["foundation_closure_readiness"] = _foundation_closure_readiness(checks)
    findings = _findings_from_checks(checks)
    action_proposals = build_maintenance_action_proposals(findings, checks, commands_snapshot=commands)
    finding_summary = _finding_summary(findings)
    runtime_health = _runtime_health_summary(checks)
    runtime_health["finding_count"] = finding_summary["total"]
    runtime_health["finding_severity_counts"] = finding_summary["by_severity"]
    runtime_health["action_proposal_count"] = len(action_proposals)
    runtime_health["pending_action_proposal_count"] = sum(
        1 for proposal in action_proposals
        if proposal.get("status") in {"approval_requested", "approved", "executing"}
    )
    checks["runtime_health"] = runtime_health
    checks["finding_summary"] = finding_summary
    report = {
        "scan_version": "maintenance-scan/1",
        "finding_version": "maintenance-finding/1",
        "read_only": True,
        "started_at": int(time.time() * 1000),
        "summary": runtime_health,
        "findings": findings,
        "recommendations": findings,
        "action_proposals": action_proposals,
        "categories": finding_summary["by_category"],
        "checks": checks,
    }
    report["completed_at"] = int(time.time() * 1000)
    _last_scan = report
    return report


def get_last_maintenance_scan() -> dict[str, Any] | None:
    return _last_scan
