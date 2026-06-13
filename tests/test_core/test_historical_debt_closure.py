from __future__ import annotations

from copy import deepcopy

from aegis.core.historical_debt_closure import (
    DISPOSITION_ARCHIVE_HISTORICAL,
    DISPOSITION_QUARANTINE_UNKNOWN,
    apply_manifest_only_historical_evidence_replay_quarantine,
    build_historical_debt_backup_manifest,
    build_historical_debt_item_manifest,
    build_historical_evidence_replay_debt_closure_plan,
    build_manifest_only_replay_hash_chain_gate,
    evaluate_historical_evidence_replay_debt_closure_apply_readiness,
)


def _scan(
    *,
    current: int = 0,
    current_missing: int = 0,
    historical: int = 2,
    historical_missing: int = 1,
    unknown: int = 2,
    unknown_missing: int = 1,
    replay_status: str = "fail",
    omitted: int = 0,
) -> dict:
    action_classifications = []
    for index in range(historical):
        action_classifications.append(
            {
                "action_id": f"historical-{index}",
                "status": "failed",
                "verification_state": "missing" if index < historical_missing else "failed",
                "era": "historical",
                "era_reason": "synthetic historical test item",
                "classes": ["historical_missing_evidence"] if index < historical_missing else ["historical_failed_evidence"],
            }
        )
    listed_unknown = max(0, unknown - omitted)
    for index in range(listed_unknown):
        action_classifications.append(
            {
                "action_id": f"unknown-{index}",
                "status": "success",
                "verification_state": "missing" if index < unknown_missing else "verified",
                "era": "unknown_era",
                "era_reason": "current session id unavailable",
                "classes": ["unknown_era_missing_evidence"] if index < unknown_missing else ["unknown_era_verified"],
            }
        )
    return {
        "scan_version": "maintenance-scan/1",
        "summary": {"status": "fail"},
        "checks": {
            "foundation_closure_readiness": {
                "closure_readiness_status": "needs_operator_attention",
                "current_blocker_count": current + current_missing,
                "current_evidence_failure_count": current,
                "current_missing_evidence_count": current_missing,
                "historical_evidence_debt_count": historical,
                "historical_missing_evidence_count": historical_missing,
                "unknown_era_evidence_issue_count": unknown,
                "unknown_era_missing_evidence_count": unknown_missing,
                "replay_diagnostics_status": replay_status,
                "replay_boundary_classification": "historical_mixed_sequence_eras_or_reset_boundaries",
            },
            "evidence_audit": {
                "status": "fail",
                "current_evidence_failure_count": current,
                "current_missing_evidence_count": current_missing,
                "historical_evidence_debt_count": historical,
                "historical_missing_evidence_count": historical_missing,
                "unknown_era_evidence_issue_count": unknown,
                "unknown_era_missing_evidence_count": unknown_missing,
                "mutation_performed": False,
                "classification": {
                    "action_classifications": action_classifications,
                    "command_lifecycle_classifications": [],
                    "omitted_action_classification_count": omitted,
                    "omitted_command_lifecycle_classification_count": 0,
                },
            },
            "replay_diagnostics": {
                "status": replay_status,
                "read_only": True,
                "mutated": False,
                "replay_boundary": {
                    "classification": "historical_mixed_sequence_eras_or_reset_boundaries",
                    "cleanup_execution_blocked": replay_status == "fail",
                },
            },
        },
    }


def _item(stable_id: str, era: str, disposition: str, *, evidence_missing: bool = False) -> dict:
    return {
        "stable_id": stable_id,
        "source_category": "evidence_audit_action",
        "era_classification": era,
        "issue_type": "missing_evidence" if evidence_missing else "evidence_issue",
        "severity": "warning",
        "reason": "synthetic test item",
        "original_finding_ref": stable_id,
        "proposed_disposition": disposition,
        "disposition_reason": "synthetic test disposition",
        "evidence_missing": evidence_missing,
        "can_be_reconstructed": False if evidence_missing else None,
        "must_remain_inspectable": True,
    }


def _exact_manifest() -> dict:
    return {
        "manifest_id": "item-manifest-1",
        "items": [
            _item("action:historical-0", "historical", DISPOSITION_ARCHIVE_HISTORICAL),
            _item("action:historical-1", "historical", DISPOSITION_ARCHIVE_HISTORICAL, evidence_missing=True),
            _item("action:unknown-0", "unknown_era", DISPOSITION_QUARANTINE_UNKNOWN, evidence_missing=True),
            _item("action:unknown-1", "unknown_era", DISPOSITION_QUARANTINE_UNKNOWN),
        ],
    }


def _backup() -> dict:
    return build_historical_debt_backup_manifest(
        backup_id="backup-1",
        source_refs=[{"kind": "runtime_journal", "ref": "runtime_events.jsonl"}],
        covered_stores=["journal", "evidence", "replay"],
        item_counts={"historical": 2, "unknown_era": 2},
        content_hashes={"runtime_events.jsonl": "sha256:test"},
    )


def _restore() -> dict:
    return {"status": "passed", "verification_id": "restore-1"}


def _replay_gate() -> dict:
    return build_manifest_only_replay_hash_chain_gate(
        gate_id="replay-gate-1",
        status="not_required_for_manifest_only",
        reason="Manifest-only quarantine leaves original journal, evidence, and replay stores untouched.",
    )


def test_item_manifest_lists_dispositions_and_preserves_unknown_era() -> None:
    scan = _scan()

    manifest = build_historical_debt_item_manifest(scan, manifest_id="items-1")

    assert manifest["read_only"] is True
    assert manifest["mutation_performed"] is False
    assert manifest["valid"] is True
    assert manifest["listed_counts"]["historical"] == 2
    assert manifest["listed_counts"]["unknown_era"] == 2
    assert manifest["listed_counts"]["missing_evidence"] == 2
    unknown_items = [item for item in manifest["items"] if item["era_classification"] == "unknown_era"]
    assert all(item["proposed_disposition"] == DISPOSITION_QUARANTINE_UNKNOWN for item in unknown_items)
    assert all(item["must_remain_inspectable"] is True for item in manifest["items"])


def test_item_manifest_omitted_classifications_block_exact_apply() -> None:
    manifest = build_historical_debt_item_manifest(_scan(unknown=25, unknown_missing=19, omitted=5))

    assert manifest["valid"] is False
    assert "unknown_era_item_count_mismatch" in manifest["blockers"]
    assert "item_manifest_has_omitted_classifications" in manifest["blockers"]


def test_dry_run_plan_is_non_mutating_and_blocks_without_gates() -> None:
    scan = _scan()
    before = deepcopy(scan)

    plan = build_historical_evidence_replay_debt_closure_plan(scan)

    assert scan == before
    assert plan["read_only"] is True
    assert plan["dry_run"] is True
    assert plan["mutation_performed"] is False
    assert plan["journal_mutated"] is False
    assert plan["evidence_mutated"] is False
    assert plan["replay_mutated"] is False
    assert plan["apply_allowed"] is False
    assert plan["status"] == "blocked_with_plan"
    assert "backup_manifest_unverified" in plan["blocked_reasons"]
    assert "restore_readback_not_verified" in plan["blocked_reasons"]
    assert "operator_confirmation_missing" in plan["blocked_reasons"]


def test_unknown_era_is_quarantined_not_guessed_and_missing_evidence_not_fabricated() -> None:
    plan = build_historical_evidence_replay_debt_closure_plan(_scan(), exact_item_manifest=_exact_manifest())

    assert plan["unknown_era_quarantine_projection"]["status"] == "requires_operator_quarantine"
    assert plan["unknown_era_quarantine_projection"]["unknown_era_reclassified"] is False
    assert plan["unknown_era_reclassified"] is False
    assert plan["missing_evidence_fabricated"] is False
    assert plan["evidence_created"] is False
    assert plan["verifier_success_created"] is False


def test_item_count_mismatch_blocks_apply() -> None:
    incomplete = {
        "manifest_id": "candidate-manifest",
        "items": [
            _item("action:historical-0", "historical", DISPOSITION_ARCHIVE_HISTORICAL),
            _item("action:unknown-0", "unknown_era", DISPOSITION_QUARANTINE_UNKNOWN),
        ],
    }

    plan = build_historical_evidence_replay_debt_closure_plan(_scan(), exact_item_manifest=incomplete)

    assert plan["required_gates"]["exact_item_manifest"]["passed"] is False
    assert "historical_item_count_mismatch" in plan["blocked_reasons"]
    assert "unknown_era_item_count_mismatch" in plan["blocked_reasons"]


def test_backup_and_readback_failures_block_apply() -> None:
    plan = build_historical_evidence_replay_debt_closure_plan(
        _scan(),
        exact_item_manifest=_exact_manifest(),
        backup_manifest={**_backup(), "status": "failed"},
        restore_verification={"status": "failed"},
        replay_hash_chain_verification=_replay_gate(),
        operator_confirmation={"status": "confirmed", "backup_id": "backup-1"},
    )

    assert "backup_manifest_unverified" in plan["blocked_reasons"]
    assert "restore_readback_not_verified" in plan["blocked_reasons"]
    assert plan["status"] == "blocked_with_plan"


def test_replay_hash_chain_unavailable_does_not_pass_silently() -> None:
    plan = build_historical_evidence_replay_debt_closure_plan(
        _scan(),
        exact_item_manifest=_exact_manifest(),
        backup_manifest=_backup(),
        restore_verification=_restore(),
        replay_hash_chain_verification={"status": "unavailable"},
        operator_confirmation={"status": "confirmed", "backup_id": "backup-1"},
    )

    assert "replay_hash_chain_not_verified" in plan["blocked_reasons"]
    assert plan["required_gates"]["replay_hash_chain"]["passed"] is False


def test_manifest_only_replay_gate_can_pass_with_explicit_untouched_store_reason() -> None:
    gate = _replay_gate()

    assert gate["passed"] is True
    assert gate["status"] == "not_required_for_manifest_only"
    assert gate["original_stores_untouched"] is True
    assert gate["archived_quarantined_debt_visible"] is True


def test_operator_confirmation_must_reference_plan_or_backup() -> None:
    scan = _scan(replay_status="warning")
    plan = build_historical_evidence_replay_debt_closure_plan(
        scan,
        exact_item_manifest=_exact_manifest(),
        backup_manifest=_backup(),
        restore_verification=_restore(),
        replay_hash_chain_verification=_replay_gate(),
        operator_confirmation={"status": "confirmed", "plan_id": "wrong"},
    )

    assert plan["required_gates"]["operator_confirmation"]["passed"] is False
    assert "operator_confirmation_missing_plan_or_backup_ref" in plan["blocked_reasons"]


def test_all_gates_allow_readiness_but_apply_requires_manifest_store() -> None:
    provisional = build_historical_evidence_replay_debt_closure_plan(
        _scan(replay_status="warning"),
        exact_item_manifest=_exact_manifest(),
        backup_manifest=_backup(),
        restore_verification=_restore(),
        replay_hash_chain_verification=_replay_gate(),
    )
    plan = build_historical_evidence_replay_debt_closure_plan(
        _scan(replay_status="warning"),
        exact_item_manifest=_exact_manifest(),
        backup_manifest=_backup(),
        restore_verification=_restore(),
        replay_hash_chain_verification=_replay_gate(),
        operator_confirmation={"status": "confirmed", "plan_id": provisional["plan_id"]},
    )
    readiness = evaluate_historical_evidence_replay_debt_closure_apply_readiness(
        plan,
        apply_requested=True,
    )
    blocked_apply = apply_manifest_only_historical_evidence_replay_quarantine(
        plan,
        apply_requested=True,
    )

    assert plan["all_required_gates_passed"] is True
    assert plan["status"] == "ready_for_manifest_only_apply"
    assert readiness["apply_allowed"] is True
    assert blocked_apply["apply_allowed"] is False
    assert "manifest_store_missing" in blocked_apply["blocked_reasons"]
    assert blocked_apply["mutation_performed"] is False


def test_manifest_only_apply_writes_only_supplied_manifest_store() -> None:
    provisional = build_historical_evidence_replay_debt_closure_plan(
        _scan(replay_status="warning"),
        exact_item_manifest=_exact_manifest(),
        backup_manifest=_backup(),
        restore_verification=_restore(),
        replay_hash_chain_verification=_replay_gate(),
    )
    plan = build_historical_evidence_replay_debt_closure_plan(
        _scan(replay_status="warning"),
        exact_item_manifest=_exact_manifest(),
        backup_manifest=_backup(),
        restore_verification=_restore(),
        replay_hash_chain_verification=_replay_gate(),
        operator_confirmation={"status": "confirmed", "plan_id": provisional["plan_id"]},
    )
    store: dict = {}

    result = apply_manifest_only_historical_evidence_replay_quarantine(
        plan,
        apply_requested=True,
        manifest_store=store,
    )

    assert result["status"] == "executed_manifest_only"
    assert result["mutation_performed"] is True
    assert result["manifest_store_mutated"] is True
    assert result["original_journal_store_touched"] is False
    assert result["original_evidence_store_touched"] is False
    assert result["original_replay_state_touched"] is False
    assert result["archive_manifest_created"] is True
    assert result["quarantine_manifest_created"] is True
    assert result["evidence_created"] is False
    assert result["verifier_success_created"] is False
    assert result["unknown_era_reclassified"] is False
    assert result["missing_evidence_fabricated"] is False
    assert plan["plan_id"] in store


def test_current_operational_debt_blocks_closure_projection() -> None:
    plan = build_historical_evidence_replay_debt_closure_plan(
        _scan(current=1, current_missing=1),
        exact_item_manifest=_exact_manifest(),
    )

    assert plan["active_operational_debt"]["current_blocker_count"] == 2
    assert "current_operational_debt_present" in plan["blocked_reasons"]
    assert "current_evidence_failures_present" in plan["blocked_reasons"]
    assert "current_missing_evidence_present" in plan["blocked_reasons"]
    assert plan["clean_baseline_created"] is False
