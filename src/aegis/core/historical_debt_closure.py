from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping


CLOSURE_PLAN_VERSION = "historical-evidence-replay-debt-closure-plan/1"
CLOSURE_APPLY_READINESS_VERSION = "historical-evidence-replay-debt-closure-apply-readiness/1"


def build_historical_evidence_replay_debt_closure_plan(
    maintenance_scan: Mapping[str, Any],
    *,
    backup_manifest: Mapping[str, Any] | None = None,
    restore_verification: Mapping[str, Any] | None = None,
    replay_hash_chain_verification: Mapping[str, Any] | None = None,
    operator_confirmation: Mapping[str, Any] | None = None,
    exact_item_manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Project historical debt closure readiness without touching runtime history.

    The helper consumes caller-supplied maintenance/evidence/replay metadata only.
    It never reads journals, writes archives, fabricates evidence, or marks
    unknown-era items as historical.
    """

    scan = deepcopy(dict(maintenance_scan))
    checks = _mapping(scan.get("checks"))
    closure = _mapping(checks.get("foundation_closure_readiness"))
    evidence = _mapping(checks.get("evidence_audit"))
    replay = _mapping(checks.get("replay_diagnostics"))

    current_blocker_count = _count(
        closure.get("current_blocker_count"),
        evidence.get("current_evidence_failure_count"),
        evidence.get("current_missing_evidence_count"),
    )
    current_evidence_failure_count = _count(
        closure.get("current_evidence_failure_count"),
        evidence.get("current_evidence_failure_count"),
    )
    current_missing_evidence_count = _count(
        closure.get("current_missing_evidence_count"),
        evidence.get("current_missing_evidence_count"),
    )
    historical_evidence_debt_count = _count(
        closure.get("historical_evidence_debt_count"),
        evidence.get("historical_evidence_debt_count"),
    )
    historical_missing_evidence_count = _count(
        closure.get("historical_missing_evidence_count"),
        evidence.get("historical_missing_evidence_count"),
    )
    unknown_era_evidence_issue_count = _count(
        closure.get("unknown_era_evidence_issue_count"),
        evidence.get("unknown_era_evidence_issue_count"),
    )
    unknown_era_missing_evidence_count = _count(
        closure.get("unknown_era_missing_evidence_count"),
        evidence.get("unknown_era_missing_evidence_count"),
    )
    replay_status = str(closure.get("replay_diagnostics_status") or replay.get("status") or "unknown")
    replay_boundary = _mapping(replay.get("replay_boundary"))
    replay_classification = str(
        closure.get("replay_boundary_classification")
        or replay_boundary.get("classification")
        or "unknown"
    )

    exact_items = _mapping(exact_item_manifest)
    historical_items = _list(exact_items.get("historical_items"))
    unknown_era_items = _list(exact_items.get("unknown_era_items"))
    exact_item_listing_complete = _exact_listing_complete(
        historical_items=historical_items,
        unknown_era_items=unknown_era_items,
        historical_evidence_debt_count=historical_evidence_debt_count,
        historical_missing_evidence_count=historical_missing_evidence_count,
        unknown_era_evidence_issue_count=unknown_era_evidence_issue_count,
        unknown_era_missing_evidence_count=unknown_era_missing_evidence_count,
    )

    gates = {
        "backup_manifest": _gate_status(backup_manifest, expected_statuses={"ok", "verified"}),
        "restore_readback": _gate_status(restore_verification, expected_statuses={"ok", "verified", "passed"}),
        "replay_hash_chain": _gate_status(
            replay_hash_chain_verification,
            expected_statuses={"ok", "verified", "passed", "not_required_with_operator_reason"},
        ),
        "operator_confirmation": _gate_status(
            operator_confirmation,
            expected_statuses={"confirmed", "approved"},
        ),
        "exact_item_listing": {
            "passed": exact_item_listing_complete,
            "status": "complete" if exact_item_listing_complete else "missing_or_incomplete",
            "required": True,
        },
    }

    blockers: list[str] = []
    if current_blocker_count:
        blockers.append("current_operational_debt_present")
    if current_evidence_failure_count:
        blockers.append("current_evidence_failures_present")
    if current_missing_evidence_count:
        blockers.append("current_missing_evidence_present")
    if not gates["backup_manifest"]["passed"]:
        blockers.append("backup_manifest_missing_or_unverified")
    if not gates["restore_readback"]["passed"]:
        blockers.append("restore_readback_not_verified")
    if not gates["replay_hash_chain"]["passed"]:
        blockers.append("replay_hash_chain_not_verified")
    if not gates["operator_confirmation"]["passed"]:
        blockers.append("operator_confirmation_missing")
    if not exact_item_listing_complete:
        blockers.append("exact_item_manifest_missing_or_incomplete")
    if (unknown_era_evidence_issue_count or unknown_era_missing_evidence_count) and not exact_item_listing_complete:
        blockers.append("unknown_era_quarantine_requires_explicit_manifest")
    if replay_status not in {"ok", "warning"}:
        blockers.append("replay_diagnostics_not_closed")

    has_debt = any(
        (
            current_blocker_count,
            historical_evidence_debt_count,
            historical_missing_evidence_count,
            unknown_era_evidence_issue_count,
            unknown_era_missing_evidence_count,
            replay_status not in {"ok", "unknown"},
        )
    )
    all_gates_passed = all(gate["passed"] for gate in gates.values())
    status = "ready_for_operator_gated_apply" if has_debt and all_gates_passed and not blockers else "blocked_with_plan"
    if not has_debt:
        status = "no_debt_to_close"

    return {
        "plan_version": CLOSURE_PLAN_VERSION,
        "read_only": True,
        "dry_run": True,
        "status": status,
        "apply_allowed": False,
        "mutation_performed": False,
        "journal_mutated": False,
        "evidence_mutated": False,
        "replay_mutated": False,
        "archive_created": False,
        "quarantine_created": False,
        "clean_baseline_created": False,
        "evidence_created": False,
        "verifier_success_created": False,
        "unknown_era_reclassified": False,
        "missing_evidence_fabricated": False,
        "runtime_health_greenwashed": False,
        "source_scan": {
            "scan_version": scan.get("scan_version"),
            "summary_status": _mapping(scan.get("summary")).get("status"),
            "foundation_closure_status": closure.get("closure_readiness_status"),
            "evidence_audit_status": evidence.get("status"),
            "replay_diagnostics_status": replay_status,
            "replay_boundary_classification": replay_classification,
        },
        "active_operational_debt": {
            "current_blocker_count": current_blocker_count,
            "current_evidence_failure_count": current_evidence_failure_count,
            "current_missing_evidence_count": current_missing_evidence_count,
        },
        "historical_archive_projection": {
            "status": "pending_archive" if historical_evidence_debt_count or historical_missing_evidence_count else "not_needed",
            "historical_evidence_debt_count": historical_evidence_debt_count,
            "historical_missing_evidence_count": historical_missing_evidence_count,
            "listed_item_count": len(historical_items),
            "manifest_ref": exact_items.get("manifest_ref"),
            "archive_created": False,
        },
        "unknown_era_quarantine_projection": {
            "status": (
                "requires_operator_quarantine"
                if unknown_era_evidence_issue_count or unknown_era_missing_evidence_count
                else "not_needed"
            ),
            "unknown_era_evidence_issue_count": unknown_era_evidence_issue_count,
            "unknown_era_missing_evidence_count": unknown_era_missing_evidence_count,
            "listed_item_count": len(unknown_era_items),
            "unknown_era_reclassified": False,
            "quarantine_created": False,
        },
        "replay_projection": {
            "status": replay_status,
            "boundary_classification": replay_classification,
            "closed": False,
        },
        "required_gates": gates,
        "all_required_gates_passed": all_gates_passed,
        "blocked_reasons": _unique(blockers),
        "operator_guidance": [
            "This plan is not closure execution.",
            "Do not mutate journals, evidence, replay state, or runtime health from this plan.",
            "Unknown-era items remain unknown unless source/session evidence exists.",
            "Missing evidence remains missing unless real source evidence exists.",
            "A future apply path must keep archived and quarantined debt inspectable.",
        ],
    }


def evaluate_historical_evidence_replay_debt_closure_apply_readiness(
    closure_plan: Mapping[str, Any],
    *,
    apply_requested: bool = False,
) -> dict[str, Any]:
    """Fail closed for closure execution.

    Aegis does not yet implement mutation-bearing debt closure. This evaluator
    makes that boundary explicit so dry-run readiness cannot be confused with an
    archive/quarantine operation.
    """

    plan = deepcopy(dict(closure_plan))
    blockers = list(_list(plan.get("blocked_reasons")))
    if not apply_requested:
        blockers.append("apply_not_requested")
    if plan.get("status") != "ready_for_operator_gated_apply":
        blockers.append("closure_plan_not_apply_ready")
    blockers.append("closure_apply_execution_not_implemented")

    return {
        "readiness_version": CLOSURE_APPLY_READINESS_VERSION,
        "read_only": True,
        "apply_requested": bool(apply_requested),
        "apply_allowed": False,
        "execution_blocked": True,
        "mutation_performed": False,
        "archive_created": False,
        "quarantine_created": False,
        "clean_baseline_created": False,
        "journal_mutated": False,
        "evidence_mutated": False,
        "replay_mutated": False,
        "blocked_reasons": _unique(blockers),
        "required_future_work": [
            "explicit backup writer and restore verification",
            "operator-approved archive/quarantine manifest writer",
            "post-apply maintenance comparison that preserves archived debt visibility",
        ],
    }


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _count(*values: Any) -> int:
    for value in values:
        try:
            if isinstance(value, bool):
                continue
            return max(0, int(value))
        except (TypeError, ValueError):
            continue
    return 0


def _gate_status(value: Mapping[str, Any] | None, *, expected_statuses: set[str]) -> dict[str, Any]:
    data = _mapping(value)
    status = str(data.get("status") or data.get("result") or "missing")
    explicit = data.get("verified")
    passed = bool(explicit is True or status in expected_statuses)
    return {
        "passed": passed,
        "status": status,
        "required": True,
        "ref": data.get("ref") or data.get("manifest_ref") or data.get("id"),
    }


def _exact_listing_complete(
    *,
    historical_items: list[Any],
    unknown_era_items: list[Any],
    historical_evidence_debt_count: int,
    historical_missing_evidence_count: int,
    unknown_era_evidence_issue_count: int,
    unknown_era_missing_evidence_count: int,
) -> bool:
    required_historical = historical_evidence_debt_count + historical_missing_evidence_count
    required_unknown = unknown_era_evidence_issue_count + unknown_era_missing_evidence_count
    if required_historical and len(historical_items) < required_historical:
        return False
    if required_unknown and len(unknown_era_items) < required_unknown:
        return False
    return True


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_values: list[str] = []
    for value in values:
        if value not in seen:
            unique_values.append(value)
            seen.add(value)
    return unique_values
