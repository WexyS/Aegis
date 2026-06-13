from __future__ import annotations

from copy import deepcopy

from aegis.core.commands import ApprovalManager
from aegis.core.constants import RiskLevel
from aegis.core.pending_decision_hygiene import build_pending_decision_hygiene_report


def _pending_record(
    command_id: str,
    text: str,
    *,
    status: str = "pending_approval",
    risk_level: str = "medium",
    created_at: int | None = 1_000,
    updated_at: int | None = 2_000,
    metadata: dict | None = None,
) -> dict:
    record = {
        "command_id": command_id,
        "text": text,
        "status": status,
        "risk_level": risk_level,
        "trace_id": f"trace-{command_id}",
        "verification_state": "unverified",
        "metadata": dict(metadata or {}),
    }
    if created_at is not None:
        record["created_at"] = created_at
    if updated_at is not None:
        record["updated_at"] = updated_at
    return record


def test_classifier_counts_current_and_restored_pending_decisions() -> None:
    snapshot = {
        "pending_approvals": [
            _pending_record(
                "cmd-current",
                "open calculator",
                metadata={"approval_id": "approval-current", "resume_allowed": True},
            ),
            _pending_record(
                "cmd-restored",
                "open notepad",
                metadata={
                    "approval_id": "approval-restored",
                    "resume_allowed": True,
                    "restored_from_journal": True,
                    "restored_source": "command_event_replay",
                    "restored_at": 20_000,
                    "source_snapshot_sequence": 82251,
                },
            ),
        ],
        "pending_clarifications": [
            _pending_record(
                "cmd-clarify",
                "click there",
                status="waiting_for_clarification",
                risk_level="high",
                metadata={"clarification_id": "clarification-current", "resume_allowed": False},
            ),
        ],
    }

    report = build_pending_decision_hygiene_report(snapshot, generated_at_ms=21_000)

    assert report["read_only"] is True
    assert report["mutation_performed"] is False
    assert report["pending_count"] == 3
    assert report["approval_count"] == 2
    assert report["clarification_count"] == 1
    assert report["current_session_pending_count"] == 2
    assert report["restored_unresolved_count"] == 1
    assert report["resumable_count"] == 2
    assert report["state_only_count"] == 1
    assert report["source_distribution"]["command_event_replay"] == 1
    assert report["source_distribution"]["current_session"] == 2
    assert report["safety"]["approval_grant_exposed"] is False


def test_classifier_handles_restored_backlog_shape_and_top_command_texts() -> None:
    pending = []
    for index in range(17):
        pending.append(
            _pending_record(
                f"cmd-notepad-{index}",
                "open notepad",
                metadata={
                    "approval_id": f"approval-notepad-{index}",
                    "resume_allowed": True,
                    "restored_from_journal": True,
                    "restored_source": "command_event_replay",
                    "restored_at": 30_000,
                    "source_snapshot_sequence": 82251,
                },
            )
        )
        pending.append(
            _pending_record(
                f"cmd-create-{index}",
                "create file scratch/new.txt",
                metadata={
                    "approval_id": f"approval-create-{index}",
                    "resume_allowed": True,
                    "restored_from_journal": True,
                    "restored_source": "command_event_replay",
                    "restored_at": 30_000,
                    "source_snapshot_sequence": 82251,
                },
            )
        )

    report = build_pending_decision_hygiene_report(
        {"pending_approvals": pending, "pending_clarifications": []},
        generated_at_ms=31_000,
    )
    top_texts = {item["value"]: item["count"] for item in report["top_command_texts"]}

    assert report["pending_count"] == 34
    assert report["restored_unresolved_count"] == 34
    assert report["current_session_pending_count"] == 0
    assert report["approval_count"] == 34
    assert report["clarification_count"] == 0
    assert top_texts == {
        "open notepad": 17,
        "create file scratch/new.txt": 17,
    }
    assert report["safety"]["bulk_action_available"] is False
    assert "No approval was granted" in " ".join(report["guidance"])


def test_classifier_uses_created_at_for_staleness_not_restored_at() -> None:
    record = _pending_record(
        "cmd-restored-old",
        "open notepad",
        created_at=1_000,
        updated_at=90_000,
        metadata={
            "approval_id": "approval-restored-old",
            "resume_allowed": True,
            "restored_from_journal": True,
            "restored_at": 99_000,
        },
    )

    report = build_pending_decision_hygiene_report(
        {"pending_approvals": [record]},
        generated_at_ms=100_000,
        stale_after_ms=50_000,
    )
    classification = report["classifications"][0]

    assert classification["staleness"]["age_source"] == "created_at"
    assert classification["staleness"]["age_ms"] == 99_000
    assert classification["staleness"]["stale"] is True
    assert classification["restored_at"] == 99_000
    assert report["stale_restored_unresolved_count"] == 1


def test_classifier_reports_unknown_age_when_original_timestamps_are_missing() -> None:
    record = _pending_record(
        "cmd-unknown-age",
        "open notepad",
        created_at=None,
        updated_at=None,
        metadata={
            "approval_id": "approval-unknown-age",
            "resume_allowed": True,
            "restored_from_journal": True,
            "restored_at": 99_000,
        },
    )

    report = build_pending_decision_hygiene_report(
        {"pending_approvals": [record]},
        generated_at_ms=100_000,
    )
    classification = report["classifications"][0]

    assert classification["staleness"]["age_source"] == "unknown"
    assert classification["staleness"]["age_ms"] is None
    assert classification["staleness"]["stale"] is None
    assert report["unknown_age_count"] == 1
    assert "unknown_age_restored_unresolved" in classification["classes"]


def test_classifier_does_not_mutate_approval_manager_state() -> None:
    manager = ApprovalManager()
    manager.register_pending(
        command_id="cmd-read-only",
        text="open notepad",
        trace_id="trace-read-only",
        risk_level=RiskLevel.MEDIUM,
        reason="approval required",
        metadata={
            "approval_id": "approval-read-only",
            "restored_from_journal": True,
            "restored_source": "command_event_replay",
        },
    )
    before = deepcopy(manager.snapshot())

    report = build_pending_decision_hygiene_report(manager.snapshot(), generated_at_ms=10_000)

    assert report["actions_performed"] == []
    assert report["safety"]["no_auto_resolution"] is True
    assert report["safety"]["no_auto_approval"] is True
    assert report["safety"]["no_auto_deny"] is True
    assert manager.snapshot() == before


def test_classifier_keeps_non_executable_historical_decision_non_executing() -> None:
    record = _pending_record(
        "cmd-click",
        "click 10 20",
        risk_level="high",
        metadata={
            "approval_id": "approval-click",
            "resume_allowed": False,
            "policy_rule": "generic_click.quarantined.approval_required",
            "restored_from_journal": True,
            "restored_source": "command_event_replay",
        },
    )

    report = build_pending_decision_hygiene_report({"pending_approvals": [record]})
    classification = report["classifications"][0]

    assert classification["resume_classification"] == "non_executing"
    assert "blocked_non_executable_historical" in classification["classes"]
    assert report["non_executing_count"] == 1
    assert report["resumable_count"] == 0


def test_classifier_marks_restored_executable_approval_as_operator_attention_blocker() -> None:
    record = _pending_record(
        "cmd-restored-executable",
        "create file scratch/new.txt",
        metadata={
            "approval_id": "approval-restored-executable",
            "resume_allowed": True,
            "restored_from_journal": True,
            "restored_source": "command_event_replay",
            "source_snapshot_sequence": 119248,
        },
    )

    report = build_pending_decision_hygiene_report({"pending_approvals": [record]})
    classification = report["classifications"][0]

    assert classification["classification"] == "restored_unresolved_executable"
    assert classification["executable"] is True
    assert classification["closure_allowed"] is False
    assert classification["closure_blocker"] == "restored_executable_requires_explicit_operator_resolution"
    assert classification["source_event_reference"] == {
        "restored_source": "command_event_replay",
        "source_snapshot_sequence": 119248,
    }
    assert "restored_requires_operator_attention" in classification["classes"]
    assert "restored_closure_blocked" in classification["classes"]
    assert report["restored_unresolved_executable_count"] == 1
    assert report["restored_requires_operator_attention_count"] == 1
    assert report["restored_closure_blocked_count"] == 1
    assert report["restored_closure_candidate_count"] == 0


def test_classifier_marks_stale_restored_non_executable_as_closure_candidate() -> None:
    record = _pending_record(
        "cmd-restored-click",
        "click 10 20",
        created_at=1_000,
        updated_at=1_000,
        metadata={
            "approval_id": "approval-restored-click",
            "resume_allowed": False,
            "policy_rule": "generic_click.quarantined.approval_required",
            "restored_from_journal": True,
            "restored_source": "command_event_replay",
        },
    )

    report = build_pending_decision_hygiene_report(
        {"pending_approvals": [record]},
        generated_at_ms=100_000,
        stale_after_ms=50_000,
    )
    classification = report["classifications"][0]

    assert classification["classification"] == "restored_stale_non_executable"
    assert classification["executable"] is False
    assert classification["closure_allowed"] is True
    assert classification["closure_reason"] == "stale restored decision is non-executable"
    assert classification["closure_blocker"] is None
    assert "restored_closure_candidate" in classification["classes"]
    assert report["restored_stale_non_executable_count"] == 1
    assert report["restored_closure_candidate_count"] == 1


def test_classifier_marks_restored_state_only_clarification_as_closure_candidate() -> None:
    record = _pending_record(
        "cmd-restored-clarification",
        "click that",
        status="waiting_for_clarification",
        metadata={
            "clarification_id": "clarification-restored",
            "resume_allowed": False,
            "restored_from_journal": True,
            "restored_source": "runtime_snapshot",
        },
    )

    report = build_pending_decision_hygiene_report({"pending_clarifications": [record]})
    classification = report["classifications"][0]

    assert classification["classification"] == "restored_orphaned_state_only"
    assert classification["executable"] is False
    assert classification["closure_allowed"] is True
    assert "restored_closure_candidate" in classification["classes"]
    assert report["restored_orphaned_state_only_count"] == 1
    assert report["restored_closure_candidate_count"] == 1


def test_classifier_marks_restored_later_resolved_conflict_as_reconciled() -> None:
    record = _pending_record(
        "cmd-restored-resolved",
        "open notepad",
        status="rejected",
        metadata={
            "approval_id": "approval-restored-resolved",
            "approval_resolution_status": "approval_denied",
            "restored_from_journal": True,
            "restored_source": "command_event_replay",
            "resolution_event_sequence": 119300,
        },
    )

    report = build_pending_decision_hygiene_report({"pending_approvals": [record]})
    classification = report["classifications"][0]

    assert classification["classification"] == "restored_resolved_by_later_event"
    assert classification["closure_allowed"] is False
    assert classification["closure_reason"] == "already reconciled by lifecycle state"
    assert classification["later_resolution_reference"] == {
        "sequence_num": 119300,
        "metadata_key": "resolution_event_sequence",
    }
    assert "already_resolved_conflict" in classification["classes"]
    assert report["restored_resolved_by_later_event_count"] == 1
