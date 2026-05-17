from __future__ import annotations

from aegis.core import app_map
from aegis.core import maintenance


REQUIRED_FINDING_FIELDS = {
    "finding_id",
    "category",
    "severity",
    "source",
    "reason",
    "evidence",
    "recommendation",
    "read_only",
}


def test_maintenance_scan_findings_have_source_contract() -> None:
    report = maintenance.run_read_only_maintenance_scan(
        runtime_snapshot={
            "session_id": "test-maintenance-contract",
            "last_event_sequence": -1,
            "queue_depth": 0,
            "queue_capacity": 1,
            "recovery_depth": 0,
        },
        websocket_clients=None,
    )

    findings = report["findings"]
    assert findings
    assert report["finding_version"] == "maintenance-finding/1"
    assert report["recommendations"] == findings
    assert set(report["categories"]) == maintenance.FINDING_CATEGORIES
    assert sum(report["categories"].values()) == len(findings)
    assert report["checks"]["finding_summary"]["total"] == len(findings)
    assert report["summary"]["finding_count"] == len(findings)

    for finding in findings:
        assert REQUIRED_FINDING_FIELDS <= set(finding)
        assert finding["category"] in maintenance.FINDING_CATEGORIES
        assert finding["severity"] in maintenance.FINDING_SEVERITIES
        assert finding["read_only"] is True
        assert isinstance(finding["source"], str) and finding["source"].startswith("checks.")
        assert isinstance(finding["reason"], str) and finding["reason"].strip()
        assert isinstance(finding["recommendation"], str) and finding["recommendation"].strip()
        assert isinstance(finding["evidence"], dict) and finding["evidence"]


def test_maintenance_scan_read_only_contract_has_no_observed_mutations() -> None:
    report = maintenance.run_read_only_maintenance_scan()

    contract = report["checks"]["read_only_contract"]
    assert contract["scan_version"] == "maintenance-read-only-contract/1"
    assert contract["read_only"] is True
    assert contract["status"] == "ok"
    assert contract["observed_mutations"] == []
    assert "files" in contract["prohibited_mutations"]
    assert "git" in contract["prohibited_mutations"]
    assert "app_registry_refresh" in contract["prohibited_mutations"]
    assert contract["allowed_ephemeral_state"] == ["last_maintenance_scan_cache"]


def test_maintenance_scan_does_not_mutate_discovered_app_registry() -> None:
    before = dict(app_map._discovered_registry)

    try:
        app_map._discovered_registry = {
            "sentinel_app": {
                "path": "sentinel.exe",
                "process_name": "sentinel.exe",
                "aliases": ["sentinel"],
                "source": "test",
            },
        }

        report = maintenance.run_read_only_maintenance_scan()

        assert report["checks"]["app_registry"]["discovered_count"] == 1
        assert app_map._discovered_registry == {
            "sentinel_app": {
                "path": "sentinel.exe",
                "process_name": "sentinel.exe",
                "aliases": ["sentinel"],
                "source": "test",
            },
        }
    finally:
        app_map._discovered_registry = before
