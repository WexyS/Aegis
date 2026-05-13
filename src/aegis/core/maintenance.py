from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from aegis.core.config import get_settings
from aegis.core.app_map import refresh_installed_app_registry
from aegis.core.environment import collect_environment_diagnostics
from aegis.core.evidence_audit import audit_action_evidence
from aegis.core.event_journal import get_runtime_journal
from aegis.tools.registry import get_tool_registry_snapshot, list_tools, validate_registry_drift


_last_scan: dict[str, Any] | None = None


def run_read_only_maintenance_scan() -> dict[str, Any]:
    """Read-only health report for runtime maintenance v1."""
    global _last_scan
    settings = get_settings()
    runtime_journal = get_runtime_journal()
    journal = runtime_journal.snapshot()
    evidence_audit = audit_action_evidence(runtime_journal.recent_events(), limit=50)
    app_registry = refresh_installed_app_registry()
    app_registry["read_only"] = True
    log_dir = Path(settings.logging.directory)
    report = {
        "scan_version": "maintenance-scan/1",
        "read_only": True,
        "started_at": int(time.time() * 1000),
        "checks": {
            "tool_registry": {
                "status": validate_registry_drift()["status"],
                "registered_tools": sorted(list_tools()),
                "registry": get_tool_registry_snapshot(),
            },
            "event_journal": {
                "status": "ok" if journal.get("journal_path") else "warning",
                "event_count": journal.get("event_count", 0),
                "last_sequence_num": journal.get("last_sequence_num", 0),
                "last_event_hash": journal.get("last_event_hash"),
                "integrity_status": journal.get("integrity_status"),
                "historical_integrity_status": journal.get("historical_integrity_status"),
                "historical_integrity_breaks": journal.get("historical_integrity_breaks", 0),
                "journal_path": journal.get("journal_path"),
            },
            "evidence_audit": evidence_audit,
            "app_registry": app_registry,
            "environment": collect_environment_diagnostics(),
            "logging": {
                "status": "ok" if log_dir.exists() else "warning",
                "directory": str(log_dir),
            },
            "safety": {
                "status": "ok",
                "safe_mode": settings.safety.safe_mode,
                "dry_run_default": settings.safety.dry_run_default,
            },
        },
    }
    report["completed_at"] = int(time.time() * 1000)
    _last_scan = report
    return report


def get_last_maintenance_scan() -> dict[str, Any] | None:
    return _last_scan
