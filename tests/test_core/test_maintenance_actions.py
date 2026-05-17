from __future__ import annotations

from aegis.core import maintenance_actions
from aegis.core.commands import ApprovalManager


def _missing_logging_report(tmp_path):
    finding = {
        "finding_id": "config.logging.directory_missing",
        "category": "config",
        "severity": "warning",
        "source": "checks.logging.directory",
        "reason": "Configured logging directory does not exist.",
        "evidence": {"directory": str(tmp_path / "logs")},
        "recommendation": "Create the configured logging directory before long-running runtime sessions.",
        "read_only": True,
    }
    checks = {
        "logging": {
            "status": "warning",
            "directory": str(tmp_path / "logs"),
        },
    }
    return finding, checks


def test_builds_approval_gated_logging_directory_proposal(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(maintenance_actions, "PROJECT_ROOT", tmp_path)
    finding, checks = _missing_logging_report(tmp_path)

    proposals = maintenance_actions.build_maintenance_action_proposals([finding], checks)

    assert len(proposals) == 1
    proposal = proposals[0]
    assert proposal["proposal_version"] == "maintenance-action-proposal/1"
    assert proposal["proposal_id"] == "maintenance.create_logging_directory"
    assert proposal["action"] == "create_logging_directory"
    assert proposal["risk_level"] == "medium"
    assert proposal["requires_approval"] is True
    assert proposal["read_only"] is True
    assert proposal["evidence_refs"] == [
        "checks.logging.directory",
        "findings.config.logging.directory_missing",
    ]
    assert proposal["affected_resources"][0]["path"] == str(tmp_path / "logs")


def test_request_maintenance_action_registers_pending_approval(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(maintenance_actions, "PROJECT_ROOT", tmp_path)
    manager = ApprovalManager()
    finding, checks = _missing_logging_report(tmp_path)
    proposals = maintenance_actions.build_maintenance_action_proposals([finding], checks)
    report = {"action_proposals": proposals}

    record = maintenance_actions.request_maintenance_action_approval(
        "maintenance.create_logging_directory",
        report=report,
        manager=manager,
        command_id="cmd-maintenance",
        trace_id="trace-maintenance",
    )

    assert record.status.value == "pending_approval"
    assert record.approval_required is True
    assert record.risk_level.value == "medium"
    assert record.metadata["kind"] == "maintenance_action"
    assert record.metadata["proposal"]["proposal_id"] == "maintenance.create_logging_directory"
    assert manager.snapshot()["pending_approvals"][0]["command_id"] == "cmd-maintenance"


def test_execute_logging_directory_action_produces_verified_evidence(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(maintenance_actions, "PROJECT_ROOT", tmp_path)
    finding, checks = _missing_logging_report(tmp_path)
    proposal = maintenance_actions.build_maintenance_action_proposals([finding], checks)[0]
    target = tmp_path / "logs"

    result = maintenance_actions.execute_maintenance_action_proposal(proposal)

    assert target.is_dir()
    assert result.success is True
    assert result.state_changed is True
    assert result.execution_evidence is not None
    assert result.execution_evidence.verifier == "maintenance-action-verifier/1"
    assert result.execution_evidence.verification_state == "verified"
    checks_by_name = {
        check["check_name"]: check
        for check in result.execution_evidence.verification_checks
    }
    assert checks_by_name["target_within_project_root"]["passed"] is True
    assert checks_by_name["directory_exists_after"]["passed"] is True
    assert checks_by_name["approved_mutation_scope"]["passed"] is True


def test_execute_logging_directory_blocks_out_of_scope_target(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(maintenance_actions, "PROJECT_ROOT", tmp_path / "project")
    proposal = {
        "proposal_id": "maintenance.create_logging_directory",
        "action": "create_logging_directory",
        "affected_resources": [{
            "type": "directory",
            "path": str(tmp_path / "outside"),
            "operation": "mkdir",
        }],
        "expected_outcome": {"directory_exists": True},
    }

    result = maintenance_actions.execute_maintenance_action_proposal(proposal)

    assert result.success is False
    assert not (tmp_path / "outside").exists()
    assert result.execution_evidence is not None
    assert result.execution_evidence.verification_state == "failed"
    assert result.execution_evidence.verification_checks[0]["check_name"] == "target_within_project_root"
    assert result.execution_evidence.verification_checks[0]["passed"] is False
