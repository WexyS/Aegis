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


def _missing_scratch_report(tmp_path):
    finding = {
        "finding_id": "config.workspace.scratch_missing",
        "category": "config",
        "severity": "info",
        "source": "checks.workspace_directories.directories.scratch",
        "reason": "Local scratch directory does not exist.",
        "evidence": {"path": str(tmp_path / "scratch"), "exists": False, "is_dir": False},
        "recommendation": "Create the scratch directory before writing local test or smoke artifacts.",
        "read_only": True,
    }
    checks = {
        "workspace_directories": {
            "status": "warning",
            "directories": {
                "scratch": {
                    "path": str(tmp_path / "scratch"),
                    "exists": False,
                    "is_dir": False,
                },
            },
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
    assert proposal["safety_gate"]["gate_version"] == "maintenance-mutation-safety-gate/1"
    assert proposal["safety_gate"]["approved_operation"] == "mkdir"


def test_builds_approval_gated_scratch_directory_proposal(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(maintenance_actions, "PROJECT_ROOT", tmp_path)
    finding, checks = _missing_scratch_report(tmp_path)

    proposals = maintenance_actions.build_maintenance_action_proposals([finding], checks)

    assert len(proposals) == 1
    proposal = proposals[0]
    assert proposal["proposal_id"] == "maintenance.create_scratch_directory"
    assert proposal["action"] == "create_scratch_directory"
    assert proposal["source"] == "checks.workspace_directories.directories.scratch.path"
    assert proposal["read_only"] is True
    assert proposal["status"] == "proposed"
    assert proposal["affected_resources"][0]["path"] == str(tmp_path / "scratch")
    assert proposal["safety_gate"]["gate_version"] == "maintenance-mutation-safety-gate/1"


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


def test_request_maintenance_action_reuses_active_proposal_command(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(maintenance_actions, "PROJECT_ROOT", tmp_path)
    manager = ApprovalManager()
    finding, checks = _missing_logging_report(tmp_path)
    proposals = maintenance_actions.build_maintenance_action_proposals([finding], checks)
    report = {"action_proposals": proposals}

    first = maintenance_actions.request_maintenance_action_approval(
        "maintenance.create_logging_directory",
        report=report,
        manager=manager,
        command_id="cmd-maintenance",
        trace_id="trace-maintenance",
    )
    second = maintenance_actions.request_maintenance_action_approval(
        "maintenance.create_logging_directory",
        report=report,
        manager=manager,
    )

    assert second.command_id == first.command_id
    assert len(manager.snapshot()["pending_approvals"]) == 1


def test_proposal_lifecycle_is_derived_from_command_snapshot(monkeypatch, tmp_path) -> None:
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

    annotated = maintenance_actions.build_maintenance_action_proposals(
        [finding],
        checks,
        commands_snapshot=manager.snapshot(),
    )

    assert annotated[0]["status"] == "approval_requested"
    assert annotated[0]["lifecycle"]["source"] == "commands_snapshot"
    assert annotated[0]["lifecycle"]["command_id"] == record.command_id
    assert annotated[0]["lifecycle"]["command_status"] == "pending_approval"


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
    assert result.execution_evidence.expected["safety_gate_version"] == "maintenance-mutation-safety-gate/1"
    assert result.execution_evidence.observed["preflight_passed"] is True
    checks_by_name = {
        check["check_name"]: check
        for check in result.execution_evidence.verification_checks
    }
    assert checks_by_name["mutation_safety_gate"]["passed"] is True
    assert checks_by_name["proposal_requires_approval"]["passed"] is True
    assert checks_by_name["mutation_operation_allowlisted"]["passed"] is True
    assert checks_by_name["precondition_target_absent_or_directory"]["passed"] is True
    assert checks_by_name["target_within_project_root"]["passed"] is True
    assert checks_by_name["directory_exists_after"]["passed"] is True
    assert checks_by_name["approved_mutation_scope"]["passed"] is True


def test_execute_scratch_directory_action_produces_verified_evidence(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(maintenance_actions, "PROJECT_ROOT", tmp_path)
    finding, checks = _missing_scratch_report(tmp_path)
    proposal = maintenance_actions.build_maintenance_action_proposals([finding], checks)[0]
    target = tmp_path / "scratch"

    result = maintenance_actions.execute_maintenance_action_proposal(proposal)

    assert target.is_dir()
    assert result.success is True
    assert result.action == "create_scratch_directory"
    assert result.execution_evidence is not None
    assert result.execution_evidence.verification_state == "verified"
    assert result.execution_evidence.verification_reason == "scratch directory created"
    assert result.execution_evidence.observed["safety_gate_version"] == "maintenance-mutation-safety-gate/1"


def test_execute_logging_directory_blocks_out_of_scope_target(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(maintenance_actions, "PROJECT_ROOT", tmp_path / "project")
    proposal = {
        "proposal_id": "maintenance.create_logging_directory",
        "action": "create_logging_directory",
        "requires_approval": True,
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
    checks_by_name = {
        check["check_name"]: check
        for check in result.execution_evidence.verification_checks
    }
    assert checks_by_name["target_within_project_root"]["passed"] is False
    assert result.execution_evidence.observed["preflight_passed"] is False


def test_mutation_safety_gate_blocks_unapproved_operation(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(maintenance_actions, "PROJECT_ROOT", tmp_path)
    target = tmp_path / "logs"
    proposal = {
        "proposal_id": "maintenance.create_logging_directory",
        "action": "create_logging_directory",
        "requires_approval": True,
        "affected_resources": [{
            "type": "directory",
            "path": str(target),
            "operation": "delete",
        }],
        "evidence": {"directory": str(target)},
        "expected_outcome": {"directory_exists": True},
    }

    result = maintenance_actions.execute_maintenance_action_proposal(proposal)

    assert result.success is False
    assert not target.exists()
    assert result.execution_evidence is not None
    checks_by_name = {
        check["check_name"]: check
        for check in result.execution_evidence.verification_checks
    }
    assert checks_by_name["mutation_operation_allowlisted"]["passed"] is False
    assert result.execution_evidence.verification_reason == "mutation safety gate blocked: mutation_operation_allowlisted"


def test_mutation_safety_gate_blocks_existing_file_target(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(maintenance_actions, "PROJECT_ROOT", tmp_path)
    target = tmp_path / "logs"
    target.write_text("not a directory", encoding="utf-8")
    proposal = {
        "proposal_id": "maintenance.create_logging_directory",
        "action": "create_logging_directory",
        "requires_approval": True,
        "affected_resources": [{
            "type": "directory",
            "path": str(target),
            "operation": "mkdir",
        }],
        "evidence": {"directory": str(target)},
        "expected_outcome": {"directory_exists": True},
    }

    result = maintenance_actions.execute_maintenance_action_proposal(proposal)

    assert result.success is False
    assert target.is_file()
    assert result.execution_evidence is not None
    checks_by_name = {
        check["check_name"]: check
        for check in result.execution_evidence.verification_checks
    }
    assert checks_by_name["precondition_target_absent_or_directory"]["passed"] is False
    assert result.execution_evidence.observed["pre_exists"] is True
    assert result.execution_evidence.observed["pre_is_dir"] is False


def test_mutation_safety_gate_blocks_evidence_resource_mismatch(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(maintenance_actions, "PROJECT_ROOT", tmp_path)
    target = tmp_path / "logs"
    proposal = {
        "proposal_id": "maintenance.create_logging_directory",
        "action": "create_logging_directory",
        "requires_approval": True,
        "affected_resources": [{
            "type": "directory",
            "path": str(target),
            "operation": "mkdir",
        }],
        "evidence": {"directory": str(tmp_path / "other")},
        "expected_outcome": {"directory_exists": True},
    }

    result = maintenance_actions.execute_maintenance_action_proposal(proposal)

    assert result.success is False
    assert not target.exists()
    assert result.execution_evidence is not None
    checks_by_name = {
        check["check_name"]: check
        for check in result.execution_evidence.verification_checks
    }
    assert checks_by_name["evidence_matches_approved_resource"]["passed"] is False
    assert result.execution_evidence.verification_reason == "mutation safety gate blocked: evidence_matches_approved_resource"
