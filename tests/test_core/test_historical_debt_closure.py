from __future__ import annotations

from copy import deepcopy

from aegis.core.historical_debt_closure import (
    build_historical_evidence_replay_debt_closure_plan,
    evaluate_historical_evidence_replay_debt_closure_apply_readiness,
)


def _scan(
    *,
    current: int = 0,
    current_missing: int = 0,
    historical: int = 2,
    historical_missing: int = 1,
    unknown: int = 1,
    unknown_missing: int = 1,
    replay_status: str = "fail",
) -> dict:
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
    assert "backup_manifest_missing_or_unverified" in plan["blocked_reasons"]
    assert "restore_readback_not_verified" in plan["blocked_reasons"]
    assert "operator_confirmation_missing" in plan["blocked_reasons"]


def test_unknown_era_is_not_guessed_and_missing_evidence_is_not_fabricated() -> None:
    plan = build_historical_evidence_replay_debt_closure_plan(_scan())

    assert plan["unknown_era_quarantine_projection"]["status"] == "requires_operator_quarantine"
    assert plan["unknown_era_quarantine_projection"]["unknown_era_reclassified"] is False
    assert plan["unknown_era_reclassified"] is False
    assert plan["missing_evidence_fabricated"] is False
    assert plan["evidence_created"] is False
    assert plan["verifier_success_created"] is False
    assert "unknown_era_quarantine_requires_explicit_manifest" in plan["blocked_reasons"]


def test_exact_item_manifest_must_cover_historical_and_unknown_counts() -> None:
    incomplete = {
        "manifest_ref": "candidate-manifest",
        "historical_items": [{"id": "historical-1"}],
        "unknown_era_items": [{"id": "unknown-1"}],
    }

    plan = build_historical_evidence_replay_debt_closure_plan(_scan(), exact_item_manifest=incomplete)

    assert plan["required_gates"]["exact_item_listing"]["passed"] is False
    assert "exact_item_manifest_missing_or_incomplete" in plan["blocked_reasons"]
    assert plan["historical_archive_projection"]["listed_item_count"] == 1
    assert plan["unknown_era_quarantine_projection"]["listed_item_count"] == 1


def test_all_gate_metadata_can_make_plan_apply_ready_but_not_execute_closure() -> None:
    exact = {
        "manifest_ref": "candidate-manifest",
        "historical_items": [{"id": "h1"}, {"id": "h2"}, {"id": "hm1"}],
        "unknown_era_items": [{"id": "u1"}, {"id": "um1"}],
    }

    plan = build_historical_evidence_replay_debt_closure_plan(
        _scan(replay_status="warning"),
        backup_manifest={"status": "verified", "manifest_ref": "backup-1"},
        restore_verification={"status": "passed"},
        replay_hash_chain_verification={"status": "not_required_with_operator_reason"},
        operator_confirmation={"status": "confirmed"},
        exact_item_manifest=exact,
    )
    readiness = evaluate_historical_evidence_replay_debt_closure_apply_readiness(
        plan,
        apply_requested=True,
    )

    assert plan["all_required_gates_passed"] is True
    assert plan["status"] == "ready_for_operator_gated_apply"
    assert plan["apply_allowed"] is False
    assert plan["archive_created"] is False
    assert plan["quarantine_created"] is False
    assert readiness["apply_allowed"] is False
    assert readiness["execution_blocked"] is True
    assert "closure_apply_execution_not_implemented" in readiness["blocked_reasons"]
    assert readiness["mutation_performed"] is False


def test_current_operational_debt_blocks_closure_projection() -> None:
    plan = build_historical_evidence_replay_debt_closure_plan(_scan(current=1, current_missing=1))

    assert plan["active_operational_debt"]["current_blocker_count"] == 2
    assert "current_operational_debt_present" in plan["blocked_reasons"]
    assert "current_evidence_failures_present" in plan["blocked_reasons"]
    assert "current_missing_evidence_present" in plan["blocked_reasons"]
    assert plan["clean_baseline_created"] is False
