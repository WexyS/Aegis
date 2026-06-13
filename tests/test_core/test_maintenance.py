from __future__ import annotations

from aegis.core import app_map
from aegis.core import maintenance
from aegis.core import maintenance_actions
from aegis.core.commands import get_approval_manager
from aegis.core.constants import CommandStatus, RiskLevel
from aegis.core.protocol import ProtocolEventType, create_event
from aegis.tools.desktop_tools import FocusTool, OpenAppTool


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


def _evidence_audit_stub(
    *,
    status: str = "ok",
    current: int = 0,
    historical: int = 0,
    unknown: int = 0,
    current_missing: int = 0,
    historical_missing: int = 0,
    unknown_missing: int = 0,
) -> dict:
    return {
        "scan_version": "evidence-audit/2",
        "read_only": True,
        "status": status,
        "action_event_count": 0,
        "action_count": 0,
        "completed_or_failed_count": 0,
        "active_count": 0,
        "success_count": 0,
        "error_count": 0,
        "evidence_backed_count": 0,
        "missing_evidence_count": current_missing + historical_missing + unknown_missing,
        "verified_action_count": 0,
        "unverified_evidence_count": 0,
        "failed_evidence_count": 0,
        "negative_evidence_count": 0,
        "check_pass_count": 0,
        "check_fail_count": 0,
        "check_unknown_count": 0,
        "critical_failure_count": 0,
        "critical_failures": [],
        "verification_counts": {},
        "verifier_counts": {},
        "latest_sequence_num": 0,
        "limit": 50,
        "include_historical": True,
        "current_evidence_failure_count": current,
        "historical_evidence_debt_count": historical,
        "unknown_era_evidence_issue_count": unknown,
        "current_missing_evidence_count": current_missing,
        "historical_missing_evidence_count": historical_missing,
        "unknown_era_missing_evidence_count": unknown_missing,
        "current_unverified_completed_count": 0,
        "historical_unverified_completed_count": 0,
        "unknown_era_unverified_completed_count": 0,
        "verifier_check_failure_count": 0,
        "mutation_performed": False,
        "classification": {
            "scan_version": "evidence-classification/1",
            "read_only": True,
            "mutation_performed": False,
        },
    }


def _patch_closure_scan_dependencies(
    monkeypatch,
    tmp_path,
    *,
    evidence: dict | None = None,
    replay_status: str = "ok",
    replay_classification: str = "no_replay_gap_detected",
    system_status: str = "ok",
) -> None:
    journal_path = tmp_path / "runtime_events.jsonl"
    journal_path.write_text("", encoding="utf-8")

    class FakeJournal:
        def snapshot(self) -> dict:
            return {
                "journal_path": str(journal_path),
                "event_count": 0,
                "last_sequence_num": 0,
                "last_event_hash": None,
                "integrity_status": "hash-chain",
                "historical_integrity_status": "ok",
                "historical_integrity_breaks": 0,
            }

        def recent_events(self) -> list[dict]:
            return []

    monkeypatch.setattr(maintenance, "get_runtime_journal", lambda: FakeJournal())
    monkeypatch.setattr(
        maintenance,
        "audit_action_evidence",
        lambda *args, **kwargs: evidence or _evidence_audit_stub(),
    )
    monkeypatch.setattr(
        maintenance,
        "build_runtime_replay_gap_diagnostics",
        lambda *args, **kwargs: {
            "scan_version": "runtime-replay-gap-diagnostics/1",
            "read_only": True,
            "mutated": False,
            "status": replay_status,
            "parse_error_count": 0,
            "sequence": {},
            "control_plane": {},
            "replay_boundary": {
                "classification": replay_classification,
                "cleanup_execution_blocked": replay_status == "fail",
            },
        },
    )
    monkeypatch.setattr(
        maintenance,
        "build_configured_app_discovery_smoke",
        lambda: {
            "scan_version": "app-discovery-smoke/1",
            "read_only": True,
            "status": "ok",
            "entries": [],
            "actions_performed": [],
            "observation_errors": [],
        },
    )
    monkeypatch.setattr(
        maintenance,
        "collect_system_resource_snapshot",
        lambda: {"scan_version": "system-resources/1", "read_only": True, "status": system_status},
    )
    monkeypatch.setattr(
        maintenance,
        "collect_process_resource_snapshot",
        lambda: {
            "scan_version": "process-resources/1",
            "read_only": True,
            "status": "ok",
            "process_count": 0,
            "top_by_memory": [],
            "skipped": {},
            "skipped_count": 0,
        },
    )
    monkeypatch.setattr(
        maintenance,
        "collect_network_port_snapshot",
        lambda: {"scan_version": "network-ports/1", "read_only": True, "status": "ok", "ports": []},
    )
    monkeypatch.setattr(maintenance, "_load_local_closure_manifest_store", lambda *args, **kwargs: None)


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
    assert "app_discovery_smoke" in contract["allowed_observations"]
    assert contract["allowed_ephemeral_state"] == ["last_maintenance_scan_cache"]


def test_maintenance_scan_surfaces_read_only_replay_diagnostics(monkeypatch, tmp_path) -> None:
    journal_path = tmp_path / "runtime_events.jsonl"
    journal_path.write_text(
        '{"type":"COMMAND_RECEIVED","sequence_num":5,"event_hash":"hash-5","payload":{}}\n'
        '{"type":"SNAPSHOT_CREATED","sequence_num":7,"event_hash":"hash-7","previous_hash":"hash-5","payload":{"missed_events":[]}}\n',
        encoding="utf-8",
    )
    before = journal_path.read_bytes()

    class FakeJournal:
        def snapshot(self) -> dict:
            return {
                "journal_path": str(journal_path),
                "event_count": 2,
                "last_sequence_num": 7,
                "last_event_hash": "hash-7",
                "integrity_status": "hash-chain",
                "historical_integrity_status": "ok",
                "historical_integrity_breaks": 0,
            }

        def recent_events(self) -> list[dict]:
            return []

    monkeypatch.setattr(maintenance, "get_runtime_journal", lambda: FakeJournal())
    monkeypatch.setattr(
        maintenance,
        "build_configured_app_discovery_smoke",
        lambda: {
            "scan_version": "app-discovery-smoke/1",
            "read_only": True,
            "status": "ok",
            "entries": [],
            "actions_performed": [],
            "observation_errors": [],
        },
    )

    report = maintenance.run_read_only_maintenance_scan(
        runtime_snapshot={
            "session_id": "test-replay-diagnostics",
            "last_event_sequence": 7,
            "queue_depth": 0,
            "queue_capacity": 1,
            "recovery_depth": 0,
        },
        websocket_clients=None,
    )

    replay = report["checks"]["replay_diagnostics"]
    replay_finding = next(
        finding for finding in report["findings"]
        if finding["finding_id"] == "runtime.replay_gap.diagnostics_attention"
    )

    assert journal_path.read_bytes() == before
    assert replay["read_only"] is True
    assert replay["mutated"] is False
    assert replay["status"] == "fail"
    assert replay["sequence"]["gap_count"] == 1
    assert replay["replay_boundary"]["cleanup_execution_blocked"] is True
    assert report["summary"]["component_statuses"]["replay_diagnostics"] == "fail"
    assert "runtime_replay_gap_diagnostics" in report["checks"]["read_only_contract"]["allowed_observations"]
    assert replay_finding["read_only"] is True
    assert replay_finding["evidence"]["gap_count"] == 1


def test_maintenance_scan_surfaces_read_only_pending_decision_hygiene() -> None:
    manager = get_approval_manager()
    manager.reset_for_tests()
    try:
        manager.register_pending(
            command_id="cmd-maintenance-restored",
            text="open notepad",
            trace_id="trace-maintenance-restored",
            risk_level=RiskLevel.MEDIUM,
            reason="approval required",
            metadata={
                "approval_id": "approval-maintenance-restored",
                "resume_allowed": True,
                "restored_from_journal": True,
                "restored_source": "command_event_replay",
                "restored_at": 20_000,
                "source_snapshot_sequence": 82251,
            },
        )

        report = maintenance.run_read_only_maintenance_scan(
            runtime_snapshot={
                "session_id": "test-pending-decision-hygiene",
                "last_event_sequence": 0,
                "queue_depth": 0,
                "queue_capacity": 1,
                "recovery_depth": 0,
            },
            websocket_clients=None,
        )
    finally:
        manager.reset_for_tests()

    hygiene = report["checks"]["pending_decision_hygiene"]
    finding = next(
        item for item in report["findings"]
        if item["finding_id"] == "runtime.pending_decision_hygiene.restored_unresolved"
    )

    assert hygiene["read_only"] is True
    assert hygiene["status"] == "warning"
    assert hygiene["pending_count"] == 1
    assert hygiene["restored_unresolved_count"] == 1
    assert hygiene["restored_unresolved_executable_count"] == 1
    assert hygiene["restored_requires_operator_attention_count"] == 1
    assert hygiene["restored_closure_blocked_count"] == 1
    assert hygiene["restored_closure_candidate_count"] == 0
    assert hygiene["current_session_pending_count"] == 0
    assert hygiene["approval_count"] == 1
    assert hygiene["clarification_count"] == 0
    assert hygiene["resumable_count"] == 1
    assert hygiene["mutation_performed"] is False
    assert hygiene["actions_performed"] == []
    assert hygiene["safety"]["approval_grant_exposed"] is False
    assert report["summary"]["component_statuses"]["pending_decision_hygiene"] == "warning"
    assert "pending_decision_hygiene_diagnostics" in report["checks"]["read_only_contract"]["allowed_observations"]
    assert finding["read_only"] is True
    assert finding["evidence"]["restored_unresolved_count"] == 1
    assert finding["evidence"]["restored_unresolved_executable_count"] == 1
    assert finding["evidence"]["restored_requires_operator_attention_count"] == 1
    assert finding["evidence"]["restored_closure_blocked_count"] == 1
    assert manager.snapshot()["pending_approvals"] == []


def test_maintenance_scan_surfaces_read_only_runtime_timeout_diagnostics() -> None:
    manager = get_approval_manager()
    manager.reset_for_tests()
    try:
        record = manager.create_received("open https://example.com", command_id="cmd-maintenance-timeout")
        record.status = CommandStatus.RUNNING
        record.active = True
        record.created_at = 1_000
        record.updated_at = 1_000
        record.metadata.update({
            "runtime_timeout_phase": "browser_dispatching",
            "deadline_at_ms": 2_000,
            "dispatch_attempted": True,
            "intent": "open_url",
            "requested_url": "https://example.com",
            "final_url": "https://example.com/",
        })

        report = maintenance.run_read_only_maintenance_scan(
            runtime_snapshot={
                "session_id": "test-runtime-timeout-diagnostics",
                "last_event_sequence": 0,
                "queue_depth": 0,
                "queue_capacity": 1,
                "recovery_depth": 0,
            },
            websocket_clients=None,
        )
        record_after_scan = manager.get("cmd-maintenance-timeout").to_dict()
    finally:
        manager.reset_for_tests()

    diagnostics = report["checks"]["runtime_timeout_diagnostics"]
    finding = next(
        item for item in report["findings"]
        if item["finding_id"] == "runtime.timeout.diagnostics_attention"
    )

    assert diagnostics["scan_version"] == "runtime-timeout-diagnostics/1"
    assert diagnostics["read_only"] is True
    assert diagnostics["mutation_performed"] is False
    assert diagnostics["status"] == "fail"
    assert diagnostics["finding_count"] == 1
    assert diagnostics["timeout_projection_count"] == 1
    assert diagnostics["stale_execution_projection_count"] == 1
    assert diagnostics["stale_pending_projection_count"] == 0
    assert diagnostics["projection_mutation_performed"] is False
    assert diagnostics["projection_dispatch_allowed"] is False
    assert diagnostics["projection_approval_grant_exposed"] is False
    assert diagnostics["negative_evidence_required_count"] == 1
    assert diagnostics["timeout_kind_counts"]["browser_dispatch_timeout"] == 1
    assert diagnostics["projections"][0]["payload"]["projection_kind"] == "browser_timeout_observed"
    assert diagnostics["projections"][0]["payload"]["runtime_dispatch_allowed"] is False
    assert diagnostics["projections"][0]["payload"]["approval_grant"] is False
    assert diagnostics["projections"][0]["payload"]["mutation_performed"] is False
    assert diagnostics["projections"][0]["journal_plan"]["append_now"] is False
    assert diagnostics["safety"]["no_auto_approval"] is True
    assert diagnostics["safety"]["no_auto_resume"] is True
    assert diagnostics["safety"]["no_runtime_dispatch"] is True
    assert diagnostics["safety"]["no_process_or_browser_kill"] is True
    assert diagnostics["safety"]["projection_does_not_append_journal"] is True
    assert diagnostics["actions_performed"] == []
    assert report["summary"]["component_statuses"]["runtime_timeout_diagnostics"] == "fail"
    assert "runtime_timeout_diagnostics" in report["checks"]["read_only_contract"]["allowed_observations"]
    assert finding["read_only"] is True
    assert finding["evidence"]["negative_evidence_required_count"] == 1
    assert record_after_scan["status"] == CommandStatus.RUNNING.value
    assert record_after_scan["active"] is True
    assert record_after_scan["metadata"]["dispatch_attempted"] is True


def test_maintenance_scan_surfaces_evidence_current_historical_unknown_split(monkeypatch, tmp_path) -> None:
    current_missing = create_event(
        ProtocolEventType.ACTION_FAILED,
        {"action_id": "action-current-missing", "error": "current missing evidence"},
        session_id="session-maintenance-current",
    ).to_dict()
    historical_failed = create_event(
        ProtocolEventType.ACTION_FAILED,
        {
            "action_id": "action-historical-negative",
            "error": "historical negative evidence",
            "execution_evidence": {
                "action": "create_file",
                "target": "scratch/new.txt",
                "target_type": "file",
                "method": "negative_result",
                "verifier": "executor-negative-evidence/1",
                "verification_state": "failed",
                "observed": {
                    "failure_kind": "tool_returned_error",
                    "verified_success": False,
                },
                "verification_checks": [
                    {
                        "check_name": "negative_evidence_recorded",
                        "expected": "explicit failed evidence",
                        "observed": "tool_returned_error",
                        "passed": True,
                        "reason": "negative evidence recorded",
                    },
                    {
                        "check_name": "verified_success",
                        "expected": True,
                        "observed": False,
                        "passed": False,
                        "reason": "failed action is not verified success",
                    },
                ],
            },
        },
        session_id="session-maintenance-old",
    ).to_dict()
    unknown_missing = create_event(
        ProtocolEventType.ACTION_COMPLETED,
        {"action_id": "action-unknown-missing", "success": True},
    ).to_dict()

    journal_path = tmp_path / "runtime_events.jsonl"
    journal_path.write_text("", encoding="utf-8")

    class FakeJournal:
        def snapshot(self) -> dict:
            return {
                "journal_path": str(journal_path),
                "event_count": 3,
                "last_sequence_num": 3,
                "last_event_hash": "hash-3",
                "integrity_status": "hash-chain",
                "historical_integrity_status": "ok",
                "historical_integrity_breaks": 0,
            }

        def recent_events(self) -> list[dict]:
            return [current_missing, historical_failed, unknown_missing]

    monkeypatch.setattr(maintenance, "get_runtime_journal", lambda: FakeJournal())
    monkeypatch.setattr(
        maintenance,
        "build_configured_app_discovery_smoke",
        lambda: {
            "scan_version": "app-discovery-smoke/1",
            "read_only": True,
            "status": "ok",
            "entries": [],
            "actions_performed": [],
            "observation_errors": [],
        },
    )

    manager = get_approval_manager()
    manager.reset_for_tests()
    try:
        record = manager.create_received("open notepad", command_id="cmd-old-unverified")
        record.status = CommandStatus.EXECUTED
        record.verification_state = "unverified"
        record.metadata.update({
            "restored_from_journal": True,
            "restored_source": "command_event_replay",
            "source_snapshot_sequence": 82251,
        })

        report = maintenance.run_read_only_maintenance_scan(
            runtime_snapshot={
                "session_id": "session-maintenance-current",
                "last_event_sequence": 3,
                "queue_depth": 0,
                "queue_capacity": 1,
                "recovery_depth": 0,
            },
            websocket_clients=None,
        )
    finally:
        manager.reset_for_tests()

    evidence = report["checks"]["evidence_audit"]
    classification = evidence["classification"]

    assert evidence["read_only"] is True
    assert evidence["mutation_performed"] is False
    assert evidence["status"] == "fail"
    assert evidence["current_missing_evidence_count"] == 1
    assert evidence["historical_missing_evidence_count"] == 0
    assert evidence["unknown_era_missing_evidence_count"] == 1
    assert evidence["historical_unverified_completed_count"] == 1
    assert evidence["negative_evidence_count"] == 1
    assert classification["scan_version"] == "evidence-classification/1"
    assert classification["current_evidence_failure_count"] == 1
    assert classification["historical_evidence_debt_count"] == 2
    assert classification["unknown_era_evidence_issue_count"] == 1
    assert "evidence_audit_classification" in report["checks"]["read_only_contract"]["allowed_observations"]
    assert any(
        finding["finding_id"] == "runtime.evidence_audit.missing_evidence"
        and finding["evidence"]["current_missing_evidence_count"] == 1
        and finding["evidence"]["unknown_era_missing_evidence_count"] == 1
        for finding in report["findings"]
    )
    assert any(
        finding["finding_id"] == "runtime.command_lifecycle.unverified_completed"
        and finding["evidence"]["historical_unverified_completed_count"] == 1
        for finding in report["findings"]
    )


def test_maintenance_scan_adds_read_only_closure_readiness_diagnostic(monkeypatch, tmp_path) -> None:
    _patch_closure_scan_dependencies(
        monkeypatch,
        tmp_path,
        evidence=_evidence_audit_stub(status="warning", historical=3, historical_missing=2),
        replay_status="fail",
        replay_classification="historical_mixed_sequence_eras_or_reset_boundaries",
        system_status="warning",
    )

    report = maintenance.run_read_only_maintenance_scan(
        runtime_snapshot={
            "session_id": "closure-historical-debt",
            "last_event_sequence": 0,
            "queue_depth": 0,
            "queue_capacity": 1,
            "recovery_depth": 0,
        },
        websocket_clients=0,
    )

    closure = report["checks"]["foundation_closure_readiness"]

    assert closure["scan_version"] == "foundation-closure-readiness/1"
    assert closure["read_only"] is True
    assert closure["mutation_performed"] is False
    assert closure["closure_readiness_status"] == "ready_with_known_historical_debt"
    assert closure["status"] == "warning"
    assert closure["current_blocker_count"] == 0
    assert closure["historical_evidence_debt_count"] == 3
    assert closure["historical_missing_evidence_count"] == 2
    assert closure["active_operational_debt"] == {
        "status": "none",
        "current_blocker_count": 0,
        "current_evidence_failure_count": 0,
        "current_missing_evidence_count": 0,
        "pending_decision_blocker_count": 0,
        "runtime_timeout_blocker_count": 0,
    }
    assert closure["archived_historical_debt"] == {
        "status": "not_archived",
        "historical_evidence_debt_count": 0,
        "historical_missing_evidence_count": 0,
        "manifest_ref": None,
        "archive_created": False,
    }
    assert closure["quarantined_unknown_era_debt"] == {
        "status": "not_quarantined",
        "unknown_era_evidence_issue_count": 0,
        "unknown_era_missing_evidence_count": 0,
        "manifest_ref": None,
        "quarantine_created": False,
        "unknown_era_reclassified": False,
    }
    assert closure["closure_execution_status"] == "not_executed"
    assert closure["replay_historical_debt_present"] is True
    assert closure["system_resource_warning_count"] == 1
    assert report["summary"]["component_statuses"]["evidence_audit"] == "warning"
    assert report["summary"]["component_statuses"]["replay_diagnostics"] == "fail"
    assert "foundation_closure_readiness" not in report["summary"]["component_statuses"]
    assert "foundation_closure_readiness_projection" in report["checks"]["read_only_contract"]["allowed_observations"]
    assert any(
        finding["finding_id"] == "runtime.foundation_closure.readiness_attention"
        and finding["severity"] == "warning"
        and finding["evidence"]["closure_readiness_status"] == "ready_with_known_historical_debt"
        for finding in report["findings"]
    )


def test_maintenance_closure_readiness_blocks_current_evidence_failures(monkeypatch, tmp_path) -> None:
    _patch_closure_scan_dependencies(
        monkeypatch,
        tmp_path,
        evidence=_evidence_audit_stub(status="fail", current=1, current_missing=1),
    )

    report = maintenance.run_read_only_maintenance_scan(
        runtime_snapshot={
            "session_id": "closure-current-failure",
            "last_event_sequence": 0,
            "queue_depth": 0,
            "queue_capacity": 1,
            "recovery_depth": 0,
        },
        websocket_clients=0,
    )

    closure = report["checks"]["foundation_closure_readiness"]

    assert closure["closure_readiness_status"] == "blocked_current_issue"
    assert closure["status"] == "fail"
    assert closure["current_evidence_failure_count"] == 1
    assert closure["current_missing_evidence_count"] == 1
    assert closure["current_blocker_count"] == 1
    assert any(
        finding["finding_id"] == "runtime.foundation_closure.readiness_attention"
        and finding["severity"] == "fail"
        for finding in report["findings"]
    )


def test_maintenance_closure_readiness_requires_attention_for_pending_decisions(monkeypatch, tmp_path) -> None:
    _patch_closure_scan_dependencies(monkeypatch, tmp_path)
    manager = get_approval_manager()
    manager.reset_for_tests()
    try:
        manager.register_pending(
            command_id="cmd-closure-restored",
            text="open notepad",
            trace_id="trace-closure-restored",
            risk_level=RiskLevel.MEDIUM,
            reason="approval required",
            metadata={
                "approval_id": "approval-closure-restored",
                "resume_allowed": True,
                "restored_from_journal": True,
                "restored_source": "command_event_replay",
                "restored_at": 20_000,
                "source_snapshot_sequence": 82251,
            },
        )
        report = maintenance.run_read_only_maintenance_scan(
            runtime_snapshot={
                "session_id": "closure-pending",
                "last_event_sequence": 0,
                "queue_depth": 0,
                "queue_capacity": 1,
                "recovery_depth": 0,
            },
            websocket_clients=0,
        )
    finally:
        manager.reset_for_tests()

    closure = report["checks"]["foundation_closure_readiness"]

    assert closure["closure_readiness_status"] == "needs_operator_attention"
    assert closure["pending_decision_blocker_count"] == 1
    assert closure["restored_pending_count"] == 1
    assert closure["current_blocker_count"] == 1
    assert closure["mutation_performed"] is False
    hygiene = report["checks"]["pending_decision_hygiene"]
    assert hygiene["restored_unresolved_executable_count"] == 1
    assert hygiene["restored_requires_operator_attention_count"] == 1


def test_maintenance_closure_readiness_does_not_guess_unknown_era(monkeypatch, tmp_path) -> None:
    _patch_closure_scan_dependencies(
        monkeypatch,
        tmp_path,
        evidence=_evidence_audit_stub(status="warning", unknown=1, unknown_missing=1),
    )

    report = maintenance.run_read_only_maintenance_scan(
        runtime_snapshot={
            "session_id": "closure-unknown-era",
            "last_event_sequence": 0,
            "queue_depth": 0,
            "queue_capacity": 1,
            "recovery_depth": 0,
        },
        websocket_clients=0,
    )

    closure = report["checks"]["foundation_closure_readiness"]

    assert closure["closure_readiness_status"] == "needs_operator_attention"
    assert closure["unknown_era_evidence_issue_count"] == 1
    assert closure["unknown_era_missing_evidence_count"] == 1
    assert closure["unknown_era_operator_attention_threshold"] == 1
    assert closure["quarantined_unknown_era_debt"]["status"] == "not_quarantined"
    assert closure["quarantined_unknown_era_debt"]["unknown_era_reclassified"] is False
    assert closure["closure_execution_status"] == "not_executed"
    assert "Unknown-era evidence issues require operator attention" in closure["recommendation"]


def test_maintenance_closure_manifest_projection_keeps_quarantined_debt_visible_without_greenwash(monkeypatch, tmp_path) -> None:
    _patch_closure_scan_dependencies(
        monkeypatch,
        tmp_path,
        evidence=_evidence_audit_stub(status="warning", unknown=25, unknown_missing=19),
        replay_status="fail",
        replay_classification="historical_mixed_sequence_eras_or_reset_boundaries",
    )
    store = {
        "closure-plan-test": {
            "apply_version": "historical-evidence-replay-debt-quarantine-apply/1",
            "status": "executed_manifest_only",
            "plan_id": "closure-plan-test",
            "required_gates": {
                "backup_manifest": {"status": "verified", "passed": True, "ref": "backup-1"},
                "restore_readback": {"status": "passed", "passed": True, "ref": "readback-1"},
                "replay_hash_chain": {
                    "status": "not_required_for_manifest_only",
                    "passed": True,
                    "ref": "replay-gate-1",
                },
                "operator_confirmation": {"status": "confirmed", "passed": True, "ref": "operator-1"},
            },
            "archive_manifest": {
                "status": "not_needed",
                "historical_evidence_debt_count": 0,
                "historical_missing_evidence_count": 0,
                "manifest_ref": "items-full-export",
                "archive_created": False,
            },
            "quarantine_manifest": {
                "status": "quarantined",
                "unknown_era_evidence_issue_count": 25,
                "unknown_era_missing_evidence_count": 19,
                "manifest_ref": "items-full-export",
                "unknown_era_reclassified": False,
                "must_remain_inspectable": True,
            },
            "baseline": {
                "status": "clean_current_operational_baseline",
                "current_blocker_count": 0,
                "runtime_health_greenwashed": False,
            },
        }
    }

    report = maintenance.run_read_only_maintenance_scan(
        runtime_snapshot={
            "session_id": "closure-quarantine-projection",
            "last_event_sequence": 0,
            "queue_depth": 0,
            "queue_capacity": 1,
            "recovery_depth": 0,
        },
        websocket_clients=0,
        closure_manifest_store=store,
    )

    closure = report["checks"]["foundation_closure_readiness"]

    assert closure["closure_execution_status"] == "executed_manifest_only"
    assert closure["closure_plan_id"] == "closure-plan-test"
    assert closure["quarantined_unknown_era_debt"] == {
        "status": "quarantined",
        "unknown_era_evidence_issue_count": 25,
        "unknown_era_missing_evidence_count": 19,
        "manifest_ref": "items-full-export",
        "quarantine_created": True,
        "unknown_era_reclassified": False,
    }
    assert closure["closure_gate_statuses"]["backup_manifest"]["passed"] is True
    assert closure["replay_diagnostics_status"] == "fail"
    assert report["summary"]["status"] == "warning"
    assert report["summary"]["component_statuses"]["evidence_audit"] == "warning"
    assert report["summary"]["component_statuses"]["replay_diagnostics"] == "warning"
    assert report["summary"]["raw_component_statuses"]["replay_diagnostics"] == "fail"
    assert report["summary"]["active_failure_components"] == []
    assert closure["active_runtime_projections"]["evidence_audit"]["classification"] == (
        "quarantined_or_archived_evidence_attention"
    )
    assert closure["active_runtime_projections"]["replay_diagnostics"]["classification"] == (
        "manifest_backed_quarantined_replay_boundary"
    )
    assert report["checks"]["historical_debt_closure_manifest_store"]["status"] == "ok"


def test_maintenance_manifest_backed_projection_does_not_downgrade_active_replay_failure(monkeypatch, tmp_path) -> None:
    _patch_closure_scan_dependencies(
        monkeypatch,
        tmp_path,
        evidence=_evidence_audit_stub(status="warning", unknown=25, unknown_missing=19),
        replay_status="fail",
        replay_classification="sequence_gap_or_snapshot_resync_boundary",
    )
    store = {
        "closure-plan-test": {
            "status": "executed_manifest_only",
            "plan_id": "closure-plan-test",
            "required_gates": {
                "replay_hash_chain": {
                    "status": "not_required_for_manifest_only",
                    "passed": True,
                    "ref": "replay-gate-1",
                },
            },
            "archive_manifest": {"status": "not_needed", "manifest_ref": "items-full-export"},
            "quarantine_manifest": {
                "status": "quarantined",
                "unknown_era_evidence_issue_count": 25,
                "unknown_era_missing_evidence_count": 19,
                "manifest_ref": "items-full-export",
                "unknown_era_reclassified": False,
            },
            "baseline": {"status": "clean_current_operational_baseline", "current_blocker_count": 0},
        }
    }

    report = maintenance.run_read_only_maintenance_scan(
        runtime_snapshot={
            "session_id": "closure-active-replay",
            "last_event_sequence": 0,
            "queue_depth": 0,
            "queue_capacity": 1,
            "recovery_depth": 0,
        },
        websocket_clients=0,
        closure_manifest_store=store,
    )

    closure = report["checks"]["foundation_closure_readiness"]

    assert closure["active_runtime_projections"]["replay_diagnostics"]["active_replay_failure"] is True
    assert report["summary"]["component_statuses"]["replay_diagnostics"] == "fail"
    assert "replay_diagnostics" in report["summary"]["active_failure_components"]
    assert report["summary"]["status"] == "fail"


def test_local_closure_manifest_loader_reports_corruption_without_mutation(tmp_path) -> None:
    manifest_path = tmp_path / "archive" / "historical-evidence-replay-quarantine-manifest.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text("{not-json", encoding="utf-8")

    projection = maintenance._load_local_closure_manifest_store(tmp_path)

    assert projection["status"] == "fail"
    assert projection["read_only"] is True
    assert projection["mutation_performed"] is False
    assert projection["source"] == "local_file"
    assert projection["path"] == str(manifest_path)
    assert projection["blockers"]


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


def test_maintenance_scan_includes_read_only_app_discovery_diagnostics() -> None:
    report = maintenance.run_read_only_maintenance_scan()
    app_discovery = report["checks"]["app_discovery"]
    entries = {entry["app_id"]: entry for entry in app_discovery["entries"]}

    assert app_discovery["scan_version"] == "app-discovery-smoke/1"
    assert app_discovery["read_only"] is True
    assert app_discovery["actions_performed"] == []
    assert "antigravity" in entries
    assert "antigravity_agent_manager" in entries
    assert entries["antigravity"]["process_name_candidates"] == ["Antigravity IDE.exe"]
    assert entries["antigravity_agent_manager"]["process_name_candidates"] == ["Antigravity.exe"]
    assert "success" not in entries["antigravity"]
    assert "verification_state" not in entries["antigravity"]
    assert "execution_evidence" not in entries["antigravity"]


def test_maintenance_scan_app_discovery_does_not_call_desktop_actions(monkeypatch) -> None:
    calls = {"open": 0, "focus": 0}

    async def forbidden_open(*args, **kwargs):
        calls["open"] += 1
        raise AssertionError("maintenance app discovery must not launch apps")

    async def forbidden_focus(*args, **kwargs):
        calls["focus"] += 1
        raise AssertionError("maintenance app discovery must not focus windows")

    monkeypatch.setattr(OpenAppTool, "run", forbidden_open)
    monkeypatch.setattr(FocusTool, "run", forbidden_focus)
    monkeypatch.setattr("aegis.core.app_discovery_smoke.gw.getAllWindows", lambda: [])
    monkeypatch.setattr("aegis.core.app_discovery_smoke.get_running_pids", lambda process_name: [])

    report = maintenance.run_read_only_maintenance_scan()

    assert report["checks"]["app_discovery"]["actions_performed"] == []
    assert calls == {"open": 0, "focus": 0}


def test_maintenance_scan_preserves_app_discovery_missing_and_ambiguous_states(monkeypatch, tmp_path) -> None:
    class FakeWindow:
        title = "Antigravity Agent Manager"
        _hWnd = 101
        visible = True
        isMinimized = False

    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setattr("aegis.core.app_discovery_smoke.gw.getAllWindows", lambda: [FakeWindow()])
    monkeypatch.setattr("aegis.core.app_discovery_smoke.get_window_pid", lambda hwnd: None)
    monkeypatch.setattr("aegis.core.app_discovery_smoke.get_running_pids", lambda process_name: [])

    report = maintenance.run_read_only_maintenance_scan()
    entries = {entry["app_id"]: entry for entry in report["checks"]["app_discovery"]["entries"]}
    antigravity = entries["antigravity"]

    assert antigravity["executable_candidates"][0]["path_exists"] is False
    assert antigravity["matching_window_count"] == 1
    assert antigravity["deterministic_verification_possible"] is False
    assert antigravity["ambiguity_status"] == "ambiguous"
    assert "running_process_not_observed" in antigravity["verification_blockers"]
    assert "ambiguous_title_matches_multiple_configured_apps" in antigravity["verification_blockers"]
    assert "title_only_overlap_without_process_identity" in antigravity["verification_blockers"]
