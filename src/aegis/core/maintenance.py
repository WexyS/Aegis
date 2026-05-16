from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from aegis.core.config import get_settings
from aegis.core.app_map import refresh_installed_app_registry
from aegis.core.action_timeline import project_action_timeline
from aegis.core.commands import get_approval_manager
from aegis.core.environment import collect_environment_diagnostics
from aegis.core.evidence_audit import audit_action_evidence
from aegis.core.event_journal import get_runtime_journal
from aegis.core.runtime_authority import peek_runtime_authority
from aegis.tools.registry import get_tool_registry_snapshot, list_tools, validate_registry_drift


_last_scan: dict[str, Any] | None = None


STATUS_RANK = {"ok": 0, "unknown": 1, "warning": 2, "fail": 3}


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
    statuses = {
        "event_journal": checks["event_journal"]["status"],
        "evidence_audit": checks["evidence_audit"]["status"],
        "tool_registry": checks["tool_registry"]["status"],
        "app_registry": checks["app_registry"].get("status", "ok"),
        "environment": checks["environment"]["overall_status"],
        "command_lifecycle": checks["command_lifecycle"]["status"],
        "runtime_snapshot": checks["runtime_snapshot"]["status"],
        "websocket": checks["websocket"]["status"],
        "action_timeline": checks["action_timeline"]["status"],
    }
    reasons = [
        name for name, status in statuses.items()
        if status not in {"ok", "unknown"}
    ]
    return {
        "scan_version": "runtime-health/1",
        "read_only": True,
        "status": _worst_status(*statuses.values()),
        "source_of_truth": "backend_snapshot_protocol_event_journal",
        "component_statuses": statuses,
        "attention": reasons[:10],
    }


def run_read_only_maintenance_scan(
    *,
    runtime_snapshot: dict[str, Any] | None = None,
    session_id: str | None = None,
    websocket_clients: int | None = None,
    queue_depth: int | None = None,
    queue_capacity: int | None = None,
) -> dict[str, Any]:
    """Read-only health report for runtime maintenance v1."""
    global _last_scan
    settings = get_settings()
    runtime_journal = get_runtime_journal()
    journal = runtime_journal.snapshot()
    recent_events = runtime_journal.recent_events()
    if runtime_snapshot is None:
        authority = peek_runtime_authority()
        runtime_snapshot = authority.snapshot(journal) if authority else None
    effective_session_id = session_id or (runtime_snapshot or {}).get("session_id")
    evidence_audit = audit_action_evidence(recent_events, limit=50, session_id=effective_session_id)
    app_registry = refresh_installed_app_registry()
    app_registry["read_only"] = True
    app_registry["status"] = "ok"
    log_dir = Path(settings.logging.directory)
    commands = get_approval_manager().snapshot()
    command_lifecycle = _command_lifecycle_snapshot(commands)
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
    logging_check = {
        "status": "ok" if log_dir.exists() else "warning",
        "directory": str(log_dir),
    }
    safety = {
        "status": "ok",
        "safe_mode": settings.safety.safe_mode,
        "dry_run_default": settings.safety.dry_run_default,
    }
    checks = {
        "tool_registry": tool_registry,
        "event_journal": event_journal,
        "evidence_audit": evidence_audit,
        "app_registry": app_registry,
        "environment": environment,
        "logging": logging_check,
        "safety": safety,
        "command_lifecycle": command_lifecycle,
        "runtime_snapshot": runtime_snapshot_check,
        "websocket": websocket,
        "action_timeline": action_timeline,
    }
    runtime_health = _runtime_health_summary(checks)
    checks["runtime_health"] = runtime_health
    report = {
        "scan_version": "maintenance-scan/1",
        "read_only": True,
        "started_at": int(time.time() * 1000),
        "summary": runtime_health,
        "checks": checks,
    }
    report["completed_at"] = int(time.time() * 1000)
    _last_scan = report
    return report


def get_last_maintenance_scan() -> dict[str, Any] | None:
    return _last_scan
