from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from aegis.core.config import PROJECT_ROOT, get_settings
from aegis.core.app_map import get_app_registry_snapshot
from aegis.core.action_timeline import project_action_timeline
from aegis.core.commands import get_approval_manager
from aegis.core.environment import collect_environment_diagnostics
from aegis.core.evidence_audit import audit_action_evidence
from aegis.core.event_journal import get_runtime_journal
from aegis.core.maintenance_actions import build_maintenance_action_proposals
from aegis.core.runtime_authority import peek_runtime_authority
from aegis.core.system_diagnostics import (
    collect_network_port_snapshot,
    collect_process_resource_snapshot,
    collect_system_resource_snapshot,
)
from aegis.tools.registry import get_tool_registry_snapshot, list_tools, validate_registry_drift


_last_scan: dict[str, Any] | None = None


STATUS_RANK = {"ok": 0, "unknown": 1, "warning": 2, "fail": 3}
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
        "system_resources": checks["system_resources"]["status"],
        "process_resources": checks["process_resources"]["status"],
        "network_ports": checks["network_ports"]["status"],
        "workspace_directories": checks["workspace_directories"]["status"],
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
            "recent_event_tail",
            "tool_registry_snapshot",
            "app_registry_snapshot",
            "environment_version_checks",
            "system_resource_snapshot",
            "process_resource_snapshot",
            "network_port_snapshot",
            "workspace_directory_snapshot",
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
        findings.append(_finding(
            "runtime.command_lifecycle.unverified_completed",
            category="runtime",
            severity="warning",
            source="checks.command_lifecycle.unverified_completed_count",
            reason="At least one executed command is not backed by verified evidence.",
            evidence={"unverified_completed_count": command_lifecycle.get("unverified_completed_count")},
            recommendation="Route completed commands through evidence audit before displaying success.",
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
            evidence={"missing_evidence_count": evidence_audit.get("missing_evidence_count")},
            recommendation="Prevent optimistic completion when execution evidence is absent.",
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
    app_registry = get_app_registry_snapshot()
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
    checks = {
        "tool_registry": tool_registry,
        "event_journal": event_journal,
        "evidence_audit": evidence_audit,
        "app_registry": app_registry,
        "environment": environment,
        "logging": logging_check,
        "safety": safety,
        "documentation": documentation,
        "workspace_directories": workspace_directories,
        "read_only_contract": read_only_contract,
        "command_lifecycle": command_lifecycle,
        "runtime_snapshot": runtime_snapshot_check,
        "websocket": websocket,
        "action_timeline": action_timeline,
        "system_resources": system_resources,
        "process_resources": process_resources,
        "network_ports": network_ports,
    }
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
