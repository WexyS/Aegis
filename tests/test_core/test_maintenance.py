from __future__ import annotations

from aegis.core import app_map
from aegis.core import maintenance
from aegis.core import maintenance_actions


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
    assert isinstance(report["action_proposals"], list)
    assert "action_proposal_count" in report["summary"]
    assert set(report["categories"]) == maintenance.FINDING_CATEGORIES
    assert sum(report["categories"].values()) == len(findings)
    assert report["checks"]["finding_summary"]["total"] == len(findings)
    assert report["summary"]["finding_count"] == len(findings)
    assert "pending_action_proposal_count" in report["summary"]

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
    assert "system_resource_snapshot" in contract["allowed_observations"]
    assert "process_resource_snapshot" in contract["allowed_observations"]
    assert "network_port_snapshot" in contract["allowed_observations"]
    assert "workspace_directory_snapshot" in contract["allowed_observations"]
    assert contract["allowed_ephemeral_state"] == ["last_maintenance_scan_cache"]


def test_workspace_directory_report_is_read_only_and_evidence_backed(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(maintenance, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(maintenance_actions, "PROJECT_ROOT", tmp_path)

    report = maintenance.run_read_only_maintenance_scan(
        runtime_snapshot={
            "session_id": "test-workspace-directories",
            "last_event_sequence": 0,
            "queue_depth": 0,
            "queue_capacity": 1,
            "recovery_depth": 0,
        },
        websocket_clients=None,
    )

    workspace = report["checks"]["workspace_directories"]
    assert workspace["scan_version"] == "workspace-directories/1"
    assert workspace["read_only"] is True
    assert workspace["status"] == "warning"
    assert workspace["directories"]["scratch"]["exists"] is False
    assert not (tmp_path / "scratch").exists()
    scratch_finding = next(
        finding for finding in report["findings"]
        if finding["finding_id"] == "config.workspace.scratch_missing"
    )
    assert scratch_finding["evidence"]["path"] == str(tmp_path / "scratch")
    assert any(
        proposal["proposal_id"] == "maintenance.create_scratch_directory"
        for proposal in report["action_proposals"]
    )


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
