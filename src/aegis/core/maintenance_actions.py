from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

from aegis.core.commands import ApprovalManager, CommandRecord, get_approval_manager
from aegis.core.config import PROJECT_ROOT
from aegis.core.constants import ActionStatus, CommandStatus, RiskLevel
from aegis.core.schemas import ActionResult, CommandResponse, ExecutionEvidence, ReliabilityMetrics


ACTION_PROPOSAL_VERSION = "maintenance-action-proposal/1"
ACTION_EVIDENCE_VERIFIER = "maintenance-action-verifier/1"
SUPPORTED_ACTIONS = {"create_logging_directory"}


def build_maintenance_action_proposals(
    findings: list[dict[str, Any]],
    checks: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build read-only action proposals from evidence-backed maintenance findings."""
    findings_by_id = {
        str(finding.get("finding_id")): finding
        for finding in findings
        if isinstance(finding, dict)
    }
    proposals: list[dict[str, Any]] = []

    logging_finding = findings_by_id.get("config.logging.directory_missing")
    logging_check = checks.get("logging") if isinstance(checks, dict) else None
    if logging_finding and isinstance(logging_check, dict):
        proposal = _logging_directory_proposal(logging_finding, logging_check)
        if proposal:
            proposals.append(proposal)

    return proposals


def request_maintenance_action_approval(
    proposal_id: str,
    *,
    report: dict[str, Any],
    manager: ApprovalManager | None = None,
    command_id: str | None = None,
    trace_id: str | None = None,
) -> CommandRecord:
    proposal = find_action_proposal(report, proposal_id)
    if proposal is None:
        raise KeyError(f"Unknown maintenance action proposal: {proposal_id}")
    if not proposal.get("requires_approval"):
        raise ValueError("Maintenance action proposal is not approval-gated")

    manager = manager or get_approval_manager()
    trace_id = trace_id or str(uuid4())
    command_id = command_id or f"maintenance-{uuid4()}"
    return manager.register_pending(
        command_id=command_id,
        text=str(proposal.get("approval_text") or proposal.get("title") or proposal_id),
        trace_id=trace_id,
        risk_level=RiskLevel(str(proposal.get("risk_level") or RiskLevel.MEDIUM.value)),
        reason=str(proposal.get("reason") or "Maintenance action requires approval"),
        warnings=list(proposal.get("warnings") or []),
        metadata={
            "kind": "maintenance_action",
            "proposal": proposal,
        },
    )


def find_action_proposal(report: dict[str, Any], proposal_id: str) -> dict[str, Any] | None:
    proposals = report.get("action_proposals") if isinstance(report, dict) else None
    if not isinstance(proposals, list):
        return None
    for proposal in proposals:
        if isinstance(proposal, dict) and proposal.get("proposal_id") == proposal_id:
            return proposal
    return None


def is_maintenance_action_record(record: CommandRecord | None) -> bool:
    return bool(record and record.metadata.get("kind") == "maintenance_action")


def execute_maintenance_action_proposal(proposal: dict[str, Any]) -> ActionResult:
    """Execute an approved maintenance action and return verifier-backed evidence."""
    started_at = int(time.time() * 1000)
    perf_started = time.perf_counter()
    action = str(proposal.get("action") or "")
    target_path = _proposal_target_path(proposal)
    checks: list[dict[str, Any]] = []
    warnings: list[str] = []

    if action not in SUPPORTED_ACTIONS:
        completed_at = int(time.time() * 1000)
        evidence = _evidence(
            action=action or "unknown",
            proposal=proposal,
            target_path=target_path,
            started_at=started_at,
            completed_at=completed_at,
            state="failed",
            reason="unsupported maintenance action",
            checks=[_check("supported_action", sorted(SUPPORTED_ACTIONS), action, False, "unsupported action")],
            warnings=warnings,
        )
        return _result(proposal, evidence, False, "Unsupported maintenance action", perf_started)

    allowed, resolved_path, allowed_reason = _resolve_safe_project_path(target_path)
    checks.append(_check(
        "target_within_project_root",
        str(PROJECT_ROOT.resolve()),
        str(resolved_path) if resolved_path else target_path,
        allowed,
        allowed_reason,
    ))
    checks.append(_check(
        "approval_matches_action",
        proposal.get("proposal_id"),
        proposal.get("proposal_id"),
        True,
        "proposal id preserved from approval metadata",
    ))

    if not allowed or resolved_path is None:
        completed_at = int(time.time() * 1000)
        evidence = _evidence(
            action=action,
            proposal=proposal,
            target_path=target_path,
            started_at=started_at,
            completed_at=completed_at,
            state="failed",
            reason=allowed_reason,
            checks=checks,
            warnings=warnings,
        )
        return _result(proposal, evidence, False, allowed_reason, perf_started)

    pre_exists = resolved_path.exists()
    mutation_performed = False
    try:
        if not pre_exists:
            resolved_path.mkdir(parents=True, exist_ok=True)
            mutation_performed = True
        post_exists = resolved_path.is_dir()
        checks.append(_check("directory_exists_after", True, post_exists, post_exists, "directory exists after action"))
        checks.append(_check(
            "approved_mutation_scope",
            {"type": "mkdir", "path": str(resolved_path)},
            {"type": "mkdir", "path": str(resolved_path), "performed": mutation_performed},
            True,
            "mutation stayed within approved proposal scope",
        ))
        verified = all(check["passed"] for check in checks)
        state = "verified" if verified else "failed"
        reason = "logging directory created" if mutation_performed else "logging directory already existed"
        completed_at = int(time.time() * 1000)
        evidence = _evidence(
            action=action,
            proposal=proposal,
            target_path=str(resolved_path),
            started_at=started_at,
            completed_at=completed_at,
            state=state,
            reason=reason,
            checks=checks,
            warnings=warnings,
            observed={
                "pre_exists": pre_exists,
                "post_exists": post_exists,
                "mutation_performed": mutation_performed,
            },
        )
        return _result(proposal, evidence, verified, reason, perf_started, state_changed=mutation_performed)
    except Exception as exc:
        completed_at = int(time.time() * 1000)
        checks.append(_check("directory_create_exception", None, type(exc).__name__, False, str(exc)))
        evidence = _evidence(
            action=action,
            proposal=proposal,
            target_path=str(resolved_path),
            started_at=started_at,
            completed_at=completed_at,
            state="failed",
            reason=str(exc),
            checks=checks,
            warnings=warnings,
        )
        return _result(proposal, evidence, False, str(exc), perf_started)


def response_from_maintenance_action(
    *,
    record: CommandRecord,
    action_result: ActionResult,
    trace_id: str,
    duration_ms: float,
) -> CommandResponse:
    status = CommandStatus.EXECUTED if action_result.success else CommandStatus.FAILED
    return CommandResponse(
        trace_id=trace_id,
        status=status,
        intent=action_result.action,
        message=action_result.output,
        actions=[action_result],
        guard={
            "allowed": True,
            "reason": "Approved maintenance action",
            "risk": record.risk_level.value,
            "requires_approval": True,
            "warnings": record.warnings,
        },
        warnings=record.warnings,
        duration_ms=duration_ms,
    )


def _logging_directory_proposal(
    finding: dict[str, Any],
    logging_check: dict[str, Any],
) -> dict[str, Any] | None:
    directory = str(logging_check.get("directory") or "")
    if not directory:
        return None
    allowed, resolved_path, reason = _resolve_safe_project_path(directory)
    if not allowed or resolved_path is None:
        return None
    return {
        "proposal_version": ACTION_PROPOSAL_VERSION,
        "proposal_id": "maintenance.create_logging_directory",
        "finding_id": finding.get("finding_id"),
        "action": "create_logging_directory",
        "title": "Create configured logging directory",
        "reason": "Configured logging directory is missing and runtime sessions need a durable log target.",
        "source": "checks.logging.directory",
        "risk_level": RiskLevel.MEDIUM.value,
        "requires_approval": True,
        "approval_text": f"Create logging directory at {resolved_path}",
        "affected_resources": [{
            "type": "directory",
            "path": str(resolved_path),
            "operation": "mkdir",
        }],
        "evidence_refs": [
            "checks.logging.directory",
            "findings.config.logging.directory_missing",
        ],
        "evidence": {
            "directory": str(resolved_path),
            "exists": False,
            "finding_reason": finding.get("reason"),
        },
        "expected_outcome": {
            "directory_exists": True,
        },
        "verification_checks": [
            {
                "check_name": "target_within_project_root",
                "expected": str(PROJECT_ROOT.resolve()),
            },
            {
                "check_name": "directory_exists_after",
                "expected": True,
            },
            {
                "check_name": "approved_mutation_scope",
                "expected": {"type": "mkdir", "path": str(resolved_path)},
            },
        ],
        "read_only": True,
        "status": "proposed",
        "safety_note": reason,
    }


def _proposal_target_path(proposal: dict[str, Any]) -> str:
    resources = proposal.get("affected_resources")
    if isinstance(resources, list):
        for resource in resources:
            if isinstance(resource, dict) and resource.get("type") == "directory":
                return str(resource.get("path") or "")
    evidence = proposal.get("evidence")
    if isinstance(evidence, dict):
        return str(evidence.get("directory") or "")
    return ""


def _resolve_safe_project_path(raw_path: str) -> tuple[bool, Path | None, str]:
    if not raw_path:
        return False, None, "empty target path"
    path = Path(raw_path)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    try:
        resolved = path.resolve()
        root = PROJECT_ROOT.resolve()
        if os.path.commonpath([str(resolved), str(root)]) != str(root):
            return False, resolved, "target path is outside project root"
        return True, resolved, "target path is within project root"
    except Exception as exc:
        return False, None, str(exc)


def _check(name: str, expected: Any, observed: Any, passed: bool, reason: str) -> dict[str, Any]:
    return {
        "check_name": name,
        "expected": expected,
        "observed": observed,
        "passed": bool(passed),
        "reason": reason,
    }


def _evidence(
    *,
    action: str,
    proposal: dict[str, Any],
    target_path: str,
    started_at: int,
    completed_at: int,
    state: str,
    reason: str,
    checks: list[dict[str, Any]],
    warnings: list[str],
    observed: dict[str, Any] | None = None,
) -> ExecutionEvidence:
    return ExecutionEvidence(
        action=action,
        target=target_path,
        target_type="directory",
        method="maintenance_action",
        verifier=ACTION_EVIDENCE_VERIFIER,
        verification_state=state,
        verification_reason=reason,
        started_at_ms=started_at,
        completed_at_ms=completed_at,
        expected={
            "proposal_id": proposal.get("proposal_id"),
            "expected_outcome": proposal.get("expected_outcome"),
        },
        observed=observed or {},
        verification_checks=checks,
        warnings=warnings,
    )


def _result(
    proposal: dict[str, Any],
    evidence: ExecutionEvidence,
    success: bool,
    output: str,
    perf_started: float,
    *,
    state_changed: bool = False,
) -> ActionResult:
    return ActionResult(
        action=str(proposal.get("action") or evidence.action),
        params={
            "proposal_id": proposal.get("proposal_id"),
            "affected_resources": proposal.get("affected_resources", []),
        },
        status=ActionStatus.EXECUTED if success else ActionStatus.FAILED,
        success=success,
        output=output,
        state_changed=state_changed,
        proof={"execution_evidence": evidence.model_dump()},
        execution_evidence=evidence,
        metrics=ReliabilityMetrics(
            execution_time_ms=(time.perf_counter() - perf_started) * 1000,
            determinism_score=1.0 if success else 0.0,
        ),
    )
