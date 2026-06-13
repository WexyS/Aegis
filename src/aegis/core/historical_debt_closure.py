from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Mapping, MutableMapping
from uuid import uuid4


CLOSURE_PLAN_VERSION = "historical-evidence-replay-debt-closure-plan/1"
CLOSURE_ITEM_MANIFEST_VERSION = "historical-evidence-replay-debt-item-manifest/1"
CLOSURE_BACKUP_MANIFEST_VERSION = "historical-evidence-replay-debt-backup-manifest/1"
CLOSURE_REPLAY_GATE_VERSION = "historical-evidence-replay-debt-replay-hash-chain-gate/1"
CLOSURE_APPLY_READINESS_VERSION = "historical-evidence-replay-debt-closure-apply-readiness/1"
CLOSURE_APPLY_RESULT_VERSION = "historical-evidence-replay-debt-quarantine-apply/1"

DISPOSITION_ARCHIVE_HISTORICAL = "archive_historical"
DISPOSITION_QUARANTINE_UNKNOWN = "quarantine_unknown_era"
DISPOSITION_LEAVE_ACTIVE = "leave_active"
DISPOSITION_BLOCKED = "blocked"

REQUIRED_ITEM_FIELDS = {
    "stable_id",
    "source_category",
    "era_classification",
    "issue_type",
    "severity",
    "reason",
    "original_finding_ref",
    "proposed_disposition",
    "disposition_reason",
    "evidence_missing",
    "can_be_reconstructed",
    "must_remain_inspectable",
}


def build_historical_debt_item_manifest(
    maintenance_scan: Mapping[str, Any],
    *,
    manifest_id: str | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    """Build an exact-item manifest from supplied scan classifications only."""

    scan = deepcopy(dict(maintenance_scan))
    checks = _mapping(scan.get("checks"))
    evidence = _mapping(checks.get("evidence_audit"))
    classification = _mapping(evidence.get("classification"))
    action_classifications = _list(classification.get("action_classifications"))
    command_classifications = _list(classification.get("command_lifecycle_classifications"))
    items: list[dict[str, Any]] = []

    for index, item in enumerate(action_classifications, start=1):
        items.append(_item_from_action_classification(item, index))
    for index, item in enumerate(command_classifications, start=1):
        items.append(_item_from_command_classification(item, index))

    expected = _expected_counts(scan)
    omitted_action_count = _count(classification.get("omitted_action_classification_count"))
    omitted_command_count = _count(classification.get("omitted_command_lifecycle_classification_count"))
    validation = _validate_item_manifest_items(
        items,
        expected,
        omitted_action_count=omitted_action_count,
        omitted_command_count=omitted_command_count,
    )

    return {
        "manifest_version": CLOSURE_ITEM_MANIFEST_VERSION,
        "manifest_id": manifest_id or f"closure-items-{uuid4().hex}",
        "created_at": created_at or _now_utc(),
        "source_scan_version": scan.get("scan_version"),
        "read_only": True,
        "mutation_performed": False,
        "items": items,
        "item_count": len(items),
        "expected_counts": expected,
        "listed_counts": _listed_counts(items),
        "omitted_action_classification_count": omitted_action_count,
        "omitted_command_lifecycle_classification_count": omitted_command_count,
        "valid": validation["passed"],
        "blockers": validation["blockers"],
        "limitations": validation["limitations"],
        "guidance": [
            "Unknown-era items remain unknown-era unless source/session evidence exists.",
            "Missing evidence remains missing unless real source evidence exists.",
            "Every closure item must remain inspectable after archive or quarantine.",
        ],
    }


def build_historical_debt_backup_manifest(
    *,
    backup_id: str,
    source_refs: list[Mapping[str, Any]],
    item_counts: Mapping[str, Any],
    created_at: str | None = None,
    covered_stores: list[str] | None = None,
    content_hashes: Mapping[str, Any] | None = None,
    status: str = "verified",
    limitations: list[str] | None = None,
) -> dict[str, Any]:
    """Create caller-supplied backup metadata without reading or copying files."""

    return {
        "manifest_version": CLOSURE_BACKUP_MANIFEST_VERSION,
        "backup_id": str(backup_id),
        "created_at": created_at or _now_utc(),
        "status": str(status),
        "read_only_metadata_only": True,
        "backup_artifact_created_by_helper": False,
        "source_refs": [dict(ref) for ref in source_refs],
        "covered_stores": list(covered_stores or []),
        "content_hashes": dict(content_hashes or {}),
        "item_counts": dict(item_counts),
        "readback_verification_status": "not_checked",
        "limitations": list(limitations or []),
    }


def build_manifest_only_replay_hash_chain_gate(
    *,
    gate_id: str,
    status: str,
    reason: str,
    mutation_scope: str = "manifest_only",
    original_stores_untouched: bool = True,
    archived_quarantined_debt_visible: bool = True,
) -> dict[str, Any]:
    """Describe replay/hash-chain sufficiency for manifest-only closure."""

    allowed_statuses = {"verified", "passed", "not_required_for_manifest_only"}
    passed = (
        status in allowed_statuses
        and mutation_scope == "manifest_only"
        and original_stores_untouched
        and archived_quarantined_debt_visible
        and bool(str(reason).strip())
    )
    return {
        "gate_version": CLOSURE_REPLAY_GATE_VERSION,
        "gate_id": str(gate_id),
        "status": str(status),
        "passed": passed,
        "reason": str(reason),
        "mutation_scope": mutation_scope,
        "original_stores_untouched": bool(original_stores_untouched),
        "archived_quarantined_debt_visible": bool(archived_quarantined_debt_visible),
        "hash_chain_rewrite_verification_required": mutation_scope != "manifest_only",
    }


def build_historical_evidence_replay_debt_closure_plan(
    maintenance_scan: Mapping[str, Any],
    *,
    backup_manifest: Mapping[str, Any] | None = None,
    restore_verification: Mapping[str, Any] | None = None,
    replay_hash_chain_verification: Mapping[str, Any] | None = None,
    operator_confirmation: Mapping[str, Any] | None = None,
    exact_item_manifest: Mapping[str, Any] | None = None,
    plan_id: str | None = None,
) -> dict[str, Any]:
    """Project historical debt closure readiness without touching runtime history."""

    scan = deepcopy(dict(maintenance_scan))
    checks = _mapping(scan.get("checks"))
    closure = _mapping(checks.get("foundation_closure_readiness"))
    evidence = _mapping(checks.get("evidence_audit"))
    replay = _mapping(checks.get("replay_diagnostics"))
    expected = _expected_counts(scan)

    replay_status = str(closure.get("replay_diagnostics_status") or replay.get("status") or "unknown")
    replay_boundary = _mapping(replay.get("replay_boundary"))
    replay_classification = str(
        closure.get("replay_boundary_classification")
        or replay_boundary.get("classification")
        or "unknown"
    )
    item_manifest = _normalize_item_manifest(exact_item_manifest)
    item_validation = validate_closure_item_manifest(item_manifest, expected_counts=expected)
    backup_gate = _backup_manifest_gate(backup_manifest)
    restore_gate = _restore_readback_gate(restore_verification)
    replay_gate = _replay_hash_chain_gate(replay_hash_chain_verification)
    derived_plan_id = plan_id or _stable_plan_id(scan, item_manifest, backup_manifest)
    operator_gate = _operator_confirmation_gate(
        operator_confirmation,
        plan_id=derived_plan_id,
        backup_id=backup_gate.get("backup_id"),
    )
    gates = {
        "backup_manifest": backup_gate,
        "restore_readback": restore_gate,
        "replay_hash_chain": replay_gate,
        "operator_confirmation": operator_gate,
        "exact_item_manifest": item_validation,
    }

    blockers = _closure_blockers(
        expected=expected,
        gates=gates,
        replay_status=replay_status,
        replay_gate=replay_gate,
    )
    has_debt = any(
        (
            expected["current_blocker_count"],
            expected["historical_evidence_debt_count"],
            expected["historical_missing_evidence_count"],
            expected["unknown_era_evidence_issue_count"],
            expected["unknown_era_missing_evidence_count"],
            replay_status not in {"ok", "unknown"},
        )
    )
    all_gates_passed = all(gate.get("passed") is True for gate in gates.values())
    status = "ready_for_manifest_only_apply" if has_debt and all_gates_passed and not blockers else "blocked_with_plan"
    if not has_debt:
        status = "no_debt_to_close"

    return {
        "plan_version": CLOSURE_PLAN_VERSION,
        "plan_id": derived_plan_id,
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
            "current_blocker_count": expected["current_blocker_count"],
            "current_evidence_failure_count": expected["current_evidence_failure_count"],
            "current_missing_evidence_count": expected["current_missing_evidence_count"],
        },
        "historical_archive_projection": {
            "status": (
                "pending_archive"
                if expected["historical_evidence_debt_count"] or expected["historical_missing_evidence_count"]
                else "not_needed"
            ),
            "historical_evidence_debt_count": expected["historical_evidence_debt_count"],
            "historical_missing_evidence_count": expected["historical_missing_evidence_count"],
            "listed_item_count": item_validation["listed_historical_count"],
            "manifest_ref": item_manifest.get("manifest_id"),
            "archive_created": False,
        },
        "unknown_era_quarantine_projection": {
            "status": (
                "requires_operator_quarantine"
                if expected["unknown_era_evidence_issue_count"] or expected["unknown_era_missing_evidence_count"]
                else "not_needed"
            ),
            "unknown_era_evidence_issue_count": expected["unknown_era_evidence_issue_count"],
            "unknown_era_missing_evidence_count": expected["unknown_era_missing_evidence_count"],
            "listed_item_count": item_validation["listed_unknown_era_count"],
            "unknown_era_reclassified": False,
            "quarantine_created": False,
        },
        "replay_projection": {
            "status": replay_status,
            "boundary_classification": replay_classification,
            "closed": False,
            "manifest_only_gate_status": replay_gate["status"],
        },
        "required_gates": gates,
        "all_required_gates_passed": all_gates_passed,
        "blocked_reasons": _unique(blockers),
        "operator_guidance": [
            "This plan is not closure execution.",
            "Do not mutate journals, evidence, replay state, or runtime health from this plan.",
            "Unknown-era items remain unknown unless source/session evidence exists.",
            "Missing evidence remains missing unless real source evidence exists.",
            "Manifest-only apply must keep archived and quarantined debt inspectable.",
        ],
    }


def validate_closure_item_manifest(
    item_manifest: Mapping[str, Any],
    *,
    expected_counts: Mapping[str, Any],
) -> dict[str, Any]:
    items = _list(item_manifest.get("items"))
    blockers: list[str] = []
    limitations = list(_list(item_manifest.get("limitations")))
    if not items and _expected_debt_item_count(expected_counts):
        blockers.append("item_manifest_empty")
    listed_historical = 0
    listed_unknown = 0
    listed_active = 0
    missing_evidence_items = 0
    stable_ids: set[str] = set()
    for index, item in enumerate(items):
        data = _mapping(item)
        missing_fields = sorted(field for field in REQUIRED_ITEM_FIELDS if field not in data)
        if missing_fields:
            blockers.append(f"item_{index}_missing_fields:{','.join(missing_fields)}")
            continue
        stable_id = str(data.get("stable_id") or "")
        if not stable_id.strip():
            blockers.append(f"item_{index}_missing_stable_id")
        if stable_id in stable_ids:
            blockers.append(f"item_{index}_duplicate_stable_id")
        stable_ids.add(stable_id)
        disposition = str(data.get("proposed_disposition") or "")
        era = str(data.get("era_classification") or "")
        if disposition == DISPOSITION_ARCHIVE_HISTORICAL:
            listed_historical += 1
            if era != "historical":
                blockers.append(f"item_{stable_id}_historical_archive_requires_historical_era")
        elif disposition == DISPOSITION_QUARANTINE_UNKNOWN:
            listed_unknown += 1
            if era != "unknown_era":
                blockers.append(f"item_{stable_id}_unknown_quarantine_requires_unknown_era")
        elif disposition == DISPOSITION_LEAVE_ACTIVE:
            listed_active += 1
        elif disposition != DISPOSITION_BLOCKED:
            blockers.append(f"item_{stable_id}_unsupported_disposition")
        if data.get("evidence_missing") is True:
            missing_evidence_items += 1
            if data.get("can_be_reconstructed") is True:
                blockers.append(f"item_{stable_id}_missing_evidence_marked_reconstructable")
        if data.get("must_remain_inspectable") is not True:
            blockers.append(f"item_{stable_id}_must_remain_inspectable_false")

    expected_historical = _count(expected_counts.get("historical_evidence_debt_count"))
    expected_unknown = _count(expected_counts.get("unknown_era_evidence_issue_count"))
    expected_current = _count(expected_counts.get("current_blocker_count"))
    expected_unknown_missing = _count(expected_counts.get("unknown_era_missing_evidence_count"))
    expected_historical_missing = _count(expected_counts.get("historical_missing_evidence_count"))
    omitted = _count(item_manifest.get("omitted_action_classification_count")) + _count(
        item_manifest.get("omitted_command_lifecycle_classification_count")
    )

    if listed_historical < expected_historical:
        blockers.append("historical_item_count_mismatch")
    if listed_unknown < expected_unknown:
        blockers.append("unknown_era_item_count_mismatch")
    if expected_current and listed_active < expected_current:
        blockers.append("current_item_count_mismatch")
    if expected_unknown_missing + expected_historical_missing and missing_evidence_items < (
        expected_unknown_missing + expected_historical_missing
    ):
        blockers.append("missing_evidence_item_count_mismatch")
    if omitted:
        blockers.append("item_manifest_has_omitted_classifications")
        limitations.append("Evidence audit classification output omitted items; exact manifest is incomplete.")

    return {
        "passed": not blockers,
        "status": "complete" if not blockers else "invalid",
        "required": True,
        "manifest_id": item_manifest.get("manifest_id"),
        "listed_historical_count": listed_historical,
        "listed_unknown_era_count": listed_unknown,
        "listed_active_count": listed_active,
        "missing_evidence_item_count": missing_evidence_items,
        "blockers": _unique(blockers),
        "limitations": _unique([str(item) for item in limitations]),
    }


def evaluate_historical_evidence_replay_debt_closure_apply_readiness(
    closure_plan: Mapping[str, Any],
    *,
    apply_requested: bool = False,
) -> dict[str, Any]:
    plan = deepcopy(dict(closure_plan))
    blockers = list(_list(plan.get("blocked_reasons")))
    if not apply_requested:
        blockers.append("apply_not_requested")
    if plan.get("status") != "ready_for_manifest_only_apply":
        blockers.append("closure_plan_not_apply_ready")
    apply_allowed = not blockers

    return {
        "readiness_version": CLOSURE_APPLY_READINESS_VERSION,
        "read_only": True,
        "apply_requested": bool(apply_requested),
        "apply_allowed": apply_allowed,
        "execution_blocked": not apply_allowed,
        "mutation_performed": False,
        "archive_created": False,
        "quarantine_created": False,
        "clean_baseline_created": False,
        "journal_mutated": False,
        "evidence_mutated": False,
        "replay_mutated": False,
        "blocked_reasons": _unique(blockers),
        "required_future_work": [] if apply_allowed else [
            "complete all closure gates before manifest-only apply",
            "post-apply maintenance comparison that preserves archived debt visibility",
        ],
    }


def apply_manifest_only_historical_evidence_replay_quarantine(
    closure_plan: Mapping[str, Any],
    *,
    apply_requested: bool = False,
    manifest_store: MutableMapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Apply closure only to a caller-supplied manifest store.

    Original journals, evidence stores, replay state, and runtime health are not
    touched by this helper. Without an explicit manifest store, apply blocks.
    """

    plan = deepcopy(dict(closure_plan))
    readiness = evaluate_historical_evidence_replay_debt_closure_apply_readiness(
        plan,
        apply_requested=apply_requested,
    )
    blockers = list(_list(readiness.get("blocked_reasons")))
    if manifest_store is None:
        blockers.append("manifest_store_missing")
    if blockers:
        return _blocked_apply_result(plan, blockers)

    archive_manifest = {
        "status": "archived" if plan["historical_archive_projection"]["historical_evidence_debt_count"] else "not_needed",
        "historical_evidence_debt_count": plan["historical_archive_projection"]["historical_evidence_debt_count"],
        "historical_missing_evidence_count": plan["historical_archive_projection"]["historical_missing_evidence_count"],
        "manifest_ref": plan["historical_archive_projection"].get("manifest_ref"),
        "must_remain_inspectable": True,
    }
    quarantine_manifest = {
        "status": (
            "quarantined"
            if plan["unknown_era_quarantine_projection"]["unknown_era_evidence_issue_count"]
            else "not_needed"
        ),
        "unknown_era_evidence_issue_count": plan["unknown_era_quarantine_projection"]["unknown_era_evidence_issue_count"],
        "unknown_era_missing_evidence_count": plan["unknown_era_quarantine_projection"]["unknown_era_missing_evidence_count"],
        "unknown_era_reclassified": False,
        "must_remain_inspectable": True,
    }
    baseline = {
        "status": "clean_current_operational_baseline"
        if plan["active_operational_debt"]["current_blocker_count"] == 0
        else "active_debt_remains",
        "current_blocker_count": plan["active_operational_debt"]["current_blocker_count"],
        "runtime_health_greenwashed": False,
    }
    manifest_store[str(plan["plan_id"])] = {
        "archive_manifest": archive_manifest,
        "quarantine_manifest": quarantine_manifest,
        "baseline": baseline,
    }

    return {
        "apply_version": CLOSURE_APPLY_RESULT_VERSION,
        "status": "executed_manifest_only",
        "plan_id": plan["plan_id"],
        "apply_allowed": True,
        "execution_blocked": False,
        "mutation_performed": True,
        "manifest_store_mutated": True,
        "original_journal_store_touched": False,
        "original_evidence_store_touched": False,
        "original_replay_state_touched": False,
        "archive_manifest_created": True,
        "quarantine_manifest_created": True,
        "clean_operational_baseline_created": baseline["status"] == "clean_current_operational_baseline",
        "evidence_created": False,
        "verifier_success_created": False,
        "unknown_era_reclassified": False,
        "missing_evidence_fabricated": False,
        "runtime_health_greenwashed": False,
        "archive_manifest": archive_manifest,
        "quarantine_manifest": quarantine_manifest,
        "baseline": baseline,
        "blocked_reasons": [],
    }


def _blocked_apply_result(plan: Mapping[str, Any], blockers: list[str]) -> dict[str, Any]:
    return {
        "apply_version": CLOSURE_APPLY_RESULT_VERSION,
        "status": "blocked",
        "plan_id": plan.get("plan_id"),
        "apply_allowed": False,
        "execution_blocked": True,
        "mutation_performed": False,
        "manifest_store_mutated": False,
        "original_journal_store_touched": False,
        "original_evidence_store_touched": False,
        "original_replay_state_touched": False,
        "archive_manifest_created": False,
        "quarantine_manifest_created": False,
        "clean_operational_baseline_created": False,
        "evidence_created": False,
        "verifier_success_created": False,
        "unknown_era_reclassified": False,
        "missing_evidence_fabricated": False,
        "runtime_health_greenwashed": False,
        "blocked_reasons": _unique(blockers),
    }


def _item_from_action_classification(item: Any, index: int) -> dict[str, Any]:
    data = _mapping(item)
    action_id = str(data.get("action_id") or f"unknown-action-{index}")
    era = str(data.get("era") or "unknown_era")
    classes = [str(value) for value in _list(data.get("classes"))]
    evidence_missing = str(data.get("verification_state") or "") == "missing" or any(
        "missing_evidence" in value for value in classes
    )
    disposition = _disposition_for_era(era)
    return {
        "stable_id": f"action:{action_id}",
        "source_category": "evidence_audit_action",
        "era_classification": era,
        "issue_type": _issue_type(classes, evidence_missing=evidence_missing),
        "severity": "warning" if era != "current_session" else "fail",
        "reason": str(data.get("era_reason") or ",".join(classes) or "classified by evidence audit"),
        "original_finding_ref": action_id,
        "proposed_disposition": disposition,
        "disposition_reason": _disposition_reason(disposition),
        "evidence_missing": evidence_missing,
        "can_be_reconstructed": False if evidence_missing else None,
        "must_remain_inspectable": True,
    }


def _item_from_command_classification(item: Any, index: int) -> dict[str, Any]:
    data = _mapping(item)
    command_id = str(data.get("command_id") or f"unknown-command-{index}")
    era = str(data.get("era") or "unknown_era")
    classes = [str(value) for value in _list(data.get("classes"))]
    disposition = _disposition_for_era(era)
    return {
        "stable_id": f"command:{command_id}",
        "source_category": "evidence_audit_command_lifecycle",
        "era_classification": era,
        "issue_type": "unverified_completed_command",
        "severity": "warning" if era != "current_session" else "fail",
        "reason": str(data.get("era_reason") or ",".join(classes) or "classified by command lifecycle audit"),
        "original_finding_ref": command_id,
        "proposed_disposition": disposition,
        "disposition_reason": _disposition_reason(disposition),
        "evidence_missing": str(data.get("verification_state") or "") != "verified",
        "can_be_reconstructed": False,
        "must_remain_inspectable": True,
    }


def _disposition_for_era(era: str) -> str:
    if era == "historical":
        return DISPOSITION_ARCHIVE_HISTORICAL
    if era == "unknown_era":
        return DISPOSITION_QUARANTINE_UNKNOWN
    if era == "current_session":
        return DISPOSITION_LEAVE_ACTIVE
    return DISPOSITION_BLOCKED


def _disposition_reason(disposition: str) -> str:
    return {
        DISPOSITION_ARCHIVE_HISTORICAL: "known historical debt can only be archived and kept inspectable",
        DISPOSITION_QUARANTINE_UNKNOWN: "unknown-era debt cannot be guessed and must remain quarantined",
        DISPOSITION_LEAVE_ACTIVE: "current operational debt must remain active",
        DISPOSITION_BLOCKED: "unsupported era classification blocks closure",
    }.get(disposition, "unsupported disposition")


def _issue_type(classes: list[str], *, evidence_missing: bool) -> str:
    if evidence_missing:
        return "missing_evidence"
    if any("failed_evidence" in value for value in classes):
        return "failed_evidence"
    if any("unverified" in value for value in classes):
        return "unverified"
    return "evidence_issue"


def _expected_counts(scan: Mapping[str, Any]) -> dict[str, int]:
    checks = _mapping(scan.get("checks"))
    closure = _mapping(checks.get("foundation_closure_readiness"))
    evidence = _mapping(checks.get("evidence_audit"))
    current_evidence_failure_count = _count(
        closure.get("current_evidence_failure_count"),
        evidence.get("current_evidence_failure_count"),
    )
    current_missing_evidence_count = _count(
        closure.get("current_missing_evidence_count"),
        evidence.get("current_missing_evidence_count"),
    )
    current_blocker_count = _count(
        closure.get("current_blocker_count"),
        current_evidence_failure_count + current_missing_evidence_count,
    )
    return {
        "current_blocker_count": current_blocker_count,
        "current_evidence_failure_count": current_evidence_failure_count,
        "current_missing_evidence_count": current_missing_evidence_count,
        "historical_evidence_debt_count": _count(
            closure.get("historical_evidence_debt_count"),
            evidence.get("historical_evidence_debt_count"),
        ),
        "historical_missing_evidence_count": _count(
            closure.get("historical_missing_evidence_count"),
            evidence.get("historical_missing_evidence_count"),
        ),
        "unknown_era_evidence_issue_count": _count(
            closure.get("unknown_era_evidence_issue_count"),
            evidence.get("unknown_era_evidence_issue_count"),
        ),
        "unknown_era_missing_evidence_count": _count(
            closure.get("unknown_era_missing_evidence_count"),
            evidence.get("unknown_era_missing_evidence_count"),
        ),
    }


def _listed_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "historical": sum(1 for item in items if item.get("proposed_disposition") == DISPOSITION_ARCHIVE_HISTORICAL),
        "unknown_era": sum(1 for item in items if item.get("proposed_disposition") == DISPOSITION_QUARANTINE_UNKNOWN),
        "active": sum(1 for item in items if item.get("proposed_disposition") == DISPOSITION_LEAVE_ACTIVE),
        "missing_evidence": sum(1 for item in items if item.get("evidence_missing") is True),
    }


def _normalize_item_manifest(value: Mapping[str, Any] | None) -> dict[str, Any]:
    data = _mapping(value)
    if "items" in data:
        return deepcopy(data)
    historical_items = _list(data.get("historical_items"))
    unknown_items = _list(data.get("unknown_era_items"))
    if historical_items or unknown_items:
        items = []
        for item in historical_items:
            normalized = _mapping(item)
            normalized.setdefault("era_classification", "historical")
            normalized.setdefault("proposed_disposition", DISPOSITION_ARCHIVE_HISTORICAL)
            items.append(normalized)
        for item in unknown_items:
            normalized = _mapping(item)
            normalized.setdefault("era_classification", "unknown_era")
            normalized.setdefault("proposed_disposition", DISPOSITION_QUARANTINE_UNKNOWN)
            items.append(normalized)
        data["items"] = items
    return data


def _validate_item_manifest_items(
    items: list[dict[str, Any]],
    expected: Mapping[str, int],
    *,
    omitted_action_count: int,
    omitted_command_count: int,
) -> dict[str, Any]:
    manifest = {
        "items": items,
        "omitted_action_classification_count": omitted_action_count,
        "omitted_command_lifecycle_classification_count": omitted_command_count,
    }
    return validate_closure_item_manifest(manifest, expected_counts=expected)


def _expected_debt_item_count(expected_counts: Mapping[str, Any]) -> int:
    return (
        _count(expected_counts.get("current_blocker_count"))
        + _count(expected_counts.get("historical_evidence_debt_count"))
        + _count(expected_counts.get("unknown_era_evidence_issue_count"))
    )


def _backup_manifest_gate(value: Mapping[str, Any] | None) -> dict[str, Any]:
    data = _mapping(value)
    status = str(data.get("status") or "missing")
    covered = set(str(item) for item in _list(data.get("covered_stores")))
    required = {"journal", "evidence", "replay"}
    blockers: list[str] = []
    if status not in {"ok", "verified"}:
        blockers.append("backup_manifest_unverified")
    if not str(data.get("backup_id") or "").strip():
        blockers.append("backup_id_missing")
    if not required.issubset(covered):
        blockers.append("backup_missing_required_stores")
    if not isinstance(data.get("item_counts"), Mapping):
        blockers.append("backup_item_counts_missing")
    if not _list(data.get("source_refs")):
        blockers.append("backup_source_refs_missing")
    return {
        "passed": not blockers,
        "status": "verified" if not blockers else status,
        "required": True,
        "backup_id": data.get("backup_id"),
        "ref": data.get("backup_id") or data.get("manifest_ref"),
        "blockers": blockers,
    }


def _restore_readback_gate(value: Mapping[str, Any] | None) -> dict[str, Any]:
    data = _mapping(value)
    status = str(data.get("status") or "missing")
    passed = status in {"ok", "verified", "passed"} or data.get("verified") is True
    return {
        "passed": passed,
        "status": status,
        "required": True,
        "ref": data.get("ref") or data.get("verification_id"),
        "blockers": [] if passed else ["restore_readback_not_verified"],
    }


def _replay_hash_chain_gate(value: Mapping[str, Any] | None) -> dict[str, Any]:
    data = _mapping(value)
    status = str(data.get("status") or "missing")
    original_untouched = data.get("original_stores_untouched") is True
    visible = data.get("archived_quarantined_debt_visible") is True
    explicit_reason = bool(str(data.get("reason") or "").strip())
    passed = status in {"ok", "verified", "passed"} or (
        status in {"not_required_for_manifest_only", "not_required_with_operator_reason"}
        and str(data.get("mutation_scope") or "") == "manifest_only"
        and original_untouched
        and visible
        and explicit_reason
    )
    return {
        "passed": passed,
        "status": status,
        "required": True,
        "ref": data.get("ref") or data.get("gate_id"),
        "mutation_scope": data.get("mutation_scope"),
        "original_stores_untouched": original_untouched,
        "archived_quarantined_debt_visible": visible,
        "reason": data.get("reason"),
        "blockers": [] if passed else ["replay_hash_chain_not_verified"],
    }


def _operator_confirmation_gate(
    value: Mapping[str, Any] | None,
    *,
    plan_id: str,
    backup_id: Any,
) -> dict[str, Any]:
    data = _mapping(value)
    status = str(data.get("status") or "missing")
    references_plan = data.get("plan_id") == plan_id
    references_backup = bool(backup_id and data.get("backup_id") == backup_id)
    passed = status in {"confirmed", "approved"} and (references_plan or references_backup)
    blockers = []
    if status not in {"confirmed", "approved"}:
        blockers.append("operator_confirmation_missing")
    if status in {"confirmed", "approved"} and not (references_plan or references_backup):
        blockers.append("operator_confirmation_missing_plan_or_backup_ref")
    return {
        "passed": passed,
        "status": status,
        "required": True,
        "ref": data.get("confirmation_id"),
        "plan_id": data.get("plan_id"),
        "backup_id": data.get("backup_id"),
        "blockers": blockers,
    }


def _closure_blockers(
    *,
    expected: Mapping[str, int],
    gates: Mapping[str, Mapping[str, Any]],
    replay_status: str,
    replay_gate: Mapping[str, Any],
) -> list[str]:
    blockers: list[str] = []
    if _count(expected.get("current_blocker_count")):
        blockers.append("current_operational_debt_present")
    if _count(expected.get("current_evidence_failure_count")):
        blockers.append("current_evidence_failures_present")
    if _count(expected.get("current_missing_evidence_count")):
        blockers.append("current_missing_evidence_present")
    for gate_name, gate in gates.items():
        if gate.get("passed") is True:
            continue
        blockers.extend(_list(gate.get("blockers")) or [f"{gate_name}_failed"])
    manifest_only_replay_ok = replay_gate.get("passed") is True and replay_gate.get("status") in {
        "not_required_for_manifest_only",
        "not_required_with_operator_reason",
    }
    if replay_status not in {"ok", "warning"} and not manifest_only_replay_ok:
        blockers.append("replay_diagnostics_not_closed")
    return _unique([str(item) for item in blockers])


def _stable_plan_id(
    scan: Mapping[str, Any],
    item_manifest: Mapping[str, Any],
    backup_manifest: Mapping[str, Any] | None,
) -> str:
    expected = _expected_counts(scan)
    parts = [
        str(scan.get("scan_version") or "scan"),
        str(item_manifest.get("manifest_id") or "no-items"),
        str(_mapping(backup_manifest).get("backup_id") or "no-backup"),
        str(expected["current_blocker_count"]),
        str(expected["historical_evidence_debt_count"]),
        str(expected["unknown_era_evidence_issue_count"]),
        str(expected["unknown_era_missing_evidence_count"]),
    ]
    return "closure-plan-" + "-".join(part.replace(" ", "_") for part in parts)


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


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_values: list[str] = []
    for value in values:
        if value not in seen:
            unique_values.append(value)
            seen.add(value)
    return unique_values


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
