from __future__ import annotations

import pytest

from aegis.core import maintenance
from aegis.core.commands import ApprovalManager, restore_approval_manager_from_journal
from aegis.core.constants import CommandStatus, RiskLevel
from aegis.core.pending_decision_hygiene import build_pending_decision_hygiene_report
from aegis.core.restored_approval_resolution import (
    RESTORED_EXECUTABLE_APPROVAL_CONFIRMATION,
    RESTORED_EXECUTABLE_APPROVAL_DISPOSITION,
    apply_restored_executable_approval_resolution,
    build_restored_executable_approval_resolution_manifest,
)
from aegis.core.runtime_timeout import build_runtime_timeout_diagnostics


class FakeJournal:
    def __init__(self) -> None:
        self.appended: list[dict] = []

    def append(self, event):
        self.appended.append(event.to_dict())
        return event

    def recent_events(self) -> list[dict]:
        return list(self.appended)

    def events_after(self, sequence_num: int) -> list[dict]:
        return list(self.appended)


def _manager_with_restored_executable_backlog() -> ApprovalManager:
    manager = ApprovalManager()
    for index, text in enumerate(
        [
            "open notepad",
            "create file scratch/new.txt",
        ],
        start=1,
    ):
        manager.register_pending(
            command_id=f"cmd-restored-{index}",
            text=text,
            trace_id=f"trace-restored-{index}",
            risk_level=RiskLevel.MEDIUM,
            reason="restored approval requires operator review",
            metadata={
                "approval_id": f"approval-restored-{index}",
                "resume_allowed": True,
                "restored_from_journal": True,
                "restored_source": "command_event_replay",
                "restored_at": 20_000,
                "source_snapshot_sequence": 119632,
            },
        )
    return manager


def test_dry_run_manifest_includes_exact_restored_approvals_without_mutation() -> None:
    manager = _manager_with_restored_executable_backlog()
    before = manager.snapshot()

    manifest = build_restored_executable_approval_resolution_manifest(before)

    assert manifest["status"] == "ready"
    assert manifest["read_only"] is True
    assert manifest["mutation_performed"] is False
    assert manifest["operator_confirmation_required"] is True
    assert manifest["confirmation_phrase_required"] == RESTORED_EXECUTABLE_APPROVAL_CONFIRMATION
    assert manifest["eligible_count"] == 2
    assert manifest["blocked_count"] == 0
    assert {item["approval_id"] for item in manifest["items"]} == {
        "approval-restored-1",
        "approval-restored-2",
    }
    assert all(item["would_resolve"] is True for item in manifest["items"])
    assert manifest["safety"]["approval_grant_exposed"] is False
    assert manifest["safety"]["command_execution_allowed"] is False
    assert manager.snapshot() == before


def test_wrong_confirmation_is_rejected_and_no_lifecycle_event_is_written() -> None:
    manager = _manager_with_restored_executable_backlog()
    manifest = build_restored_executable_approval_resolution_manifest(manager.snapshot())
    journal = FakeJournal()

    with pytest.raises(ValueError, match="confirmation phrase mismatch"):
        apply_restored_executable_approval_resolution(
            manager=manager,
            journal=journal,
            approval_ids=manifest["approval_ids_bound"],
            confirmation_phrase="WRONG",
            manifest_id=manifest["manifest_id"],
        )

    assert journal.appended == []
    assert len(manager.snapshot()["pending_approvals"]) == 2


def test_manifest_id_must_match_exact_approval_ids() -> None:
    manager = _manager_with_restored_executable_backlog()
    manifest = build_restored_executable_approval_resolution_manifest(manager.snapshot())

    with pytest.raises(ValueError, match="manifest id mismatch"):
        apply_restored_executable_approval_resolution(
            manager=manager,
            journal=FakeJournal(),
            approval_ids=manifest["approval_ids_bound"][:1],
            confirmation_phrase=RESTORED_EXECUTABLE_APPROVAL_CONFIRMATION,
            manifest_id=manifest["manifest_id"],
        )


def test_operator_cancel_restored_executable_without_grant_or_execution() -> None:
    manager = _manager_with_restored_executable_backlog()
    manifest = build_restored_executable_approval_resolution_manifest(manager.snapshot())
    journal = FakeJournal()

    result = apply_restored_executable_approval_resolution(
        manager=manager,
        journal=journal,
        approval_ids=manifest["approval_ids_bound"],
        confirmation_phrase=RESTORED_EXECUTABLE_APPROVAL_CONFIRMATION,
        manifest_id=manifest["manifest_id"],
    )

    assert result["status"] == "resolved"
    assert result["resolved_count"] == 2
    assert result["safety"]["approval_grant_created"] is False
    assert result["safety"]["auto_approval"] is False
    assert result["safety"]["auto_denial"] is False
    assert result["safety"]["command_execution_performed"] is False
    assert result["safety"]["file_creation_performed"] is False
    assert result["safety"]["app_launch_performed"] is False
    command_events = [event for event in journal.appended if event["type"] == "COMMAND_CANCELLED"]
    snapshot_events = [event for event in journal.appended if event["type"] == "SNAPSHOT_CREATED"]
    assert len(command_events) == 2
    assert len(snapshot_events) == 1
    assert result["snapshot_event"]["type"] == "SNAPSHOT_CREATED"
    for event in command_events:
        payload = event["payload"]
        command = payload["command"]
        assert payload["decision"] == RESTORED_EXECUTABLE_APPROVAL_DISPOSITION
        assert payload["not_executed"] is True
        assert payload["executed"] is False
        assert payload["approval_grant"] is False
        assert payload["auto_approval"] is False
        assert payload["auto_denial"] is False
        assert command["status"] == CommandStatus.CANCELLED.value
        assert command["approved"] is False
        assert command["rejected"] is False
        assert command["metadata"]["approval_resolution_status"] == RESTORED_EXECUTABLE_APPROVAL_DISPOSITION
        assert command["metadata"]["not_executed"] is True
        assert command["metadata"]["completed_without_execution"] is True


def test_current_session_pending_approval_cannot_use_restored_operator_path() -> None:
    manager = ApprovalManager()
    manager.register_pending(
        command_id="cmd-current",
        text="open notepad",
        trace_id="trace-current",
        risk_level=RiskLevel.MEDIUM,
        reason="current approval requires normal resolution",
        metadata={"approval_id": "approval-current", "resume_allowed": True},
    )

    manifest = build_restored_executable_approval_resolution_manifest(manager.snapshot())

    assert manifest["status"] == "blocked"
    assert manifest["eligible_count"] == 0
    assert manifest["blocked_count"] == 1
    assert "current_session_decision_not_in_restored_scope" in manifest["items"][0]["blockers"]
    assert "decision_is_not_restored_unresolved_executable" in manifest["items"][0]["blockers"]


def test_restored_approval_outside_allowed_command_scope_remains_active() -> None:
    manager = ApprovalManager()
    manager.register_pending(
        command_id="cmd-restored-other",
        text="open calculator",
        trace_id="trace-restored-other",
        risk_level=RiskLevel.MEDIUM,
        reason="restored approval requires operator review",
        metadata={
            "approval_id": "approval-restored-other",
            "resume_allowed": True,
            "restored_from_journal": True,
            "restored_source": "command_event_replay",
        },
    )

    manifest = build_restored_executable_approval_resolution_manifest(manager.snapshot())

    assert manifest["status"] == "blocked"
    assert manifest["eligible_count"] == 0
    assert manifest["blocked_count"] == 1
    assert "command_text_outside_operator_resolution_scope" in manifest["items"][0]["blockers"]
    assert manager.find_by_approval_id("approval-restored-other").status == CommandStatus.PENDING_APPROVAL


def test_closed_restored_approvals_do_not_reappear_after_replay() -> None:
    manager = _manager_with_restored_executable_backlog()
    pending_snapshot = manager.snapshot()
    manifest = build_restored_executable_approval_resolution_manifest(pending_snapshot)
    journal = FakeJournal()

    apply_restored_executable_approval_resolution(
        manager=manager,
        journal=journal,
        approval_ids=manifest["approval_ids_bound"],
        confirmation_phrase=RESTORED_EXECUTABLE_APPROVAL_CONFIRMATION,
        manifest_id=manifest["manifest_id"],
    )

    class ReplayJournal:
        def recent_events(self) -> list[dict]:
            return [
                {
                    "type": "SNAPSHOT_CREATED",
                    "sequence_num": 119632,
                    "payload": {"runtime": {"commands": pending_snapshot}},
                },
                *journal.appended,
            ]

        def events_after(self, sequence_num: int) -> list[dict]:
            raise AssertionError("recent journal tail has enough state")

    restored = ApprovalManager()

    assert restore_approval_manager_from_journal(journal=ReplayJournal(), manager=restored) is True
    restored_snapshot = restored.snapshot()
    hygiene = build_pending_decision_hygiene_report(restored_snapshot, generated_at_ms=40_000)
    timeout = build_runtime_timeout_diagnostics(restored_snapshot, generated_at_ms=40_000)

    assert restored_snapshot["pending_approvals"] == []
    assert hygiene["pending_count"] == 0
    assert hygiene["restored_unresolved_count"] == 0
    assert hygiene["restored_operator_cancelled_count"] == 2
    assert all(item["approval_grant"] is False for item in hygiene["restored_operator_cancelled_records"])
    assert all(item["auto_approval"] is False for item in hygiene["restored_operator_cancelled_records"])
    assert all(item["auto_denial"] is False for item in hygiene["restored_operator_cancelled_records"])
    assert timeout["finding_count"] == 0


def test_foundation_closure_blockers_drop_after_safe_operator_resolution() -> None:
    manager = _manager_with_restored_executable_backlog()
    pending_snapshot = manager.snapshot()
    before_closure = _foundation_closure_for_commands(pending_snapshot)
    manifest = build_restored_executable_approval_resolution_manifest(pending_snapshot)
    journal = FakeJournal()

    apply_restored_executable_approval_resolution(
        manager=manager,
        journal=journal,
        approval_ids=manifest["approval_ids_bound"],
        confirmation_phrase=RESTORED_EXECUTABLE_APPROVAL_CONFIRMATION,
        manifest_id=manifest["manifest_id"],
    )
    after_closure = _foundation_closure_for_commands(manager.snapshot())

    assert before_closure["pending_decision_blocker_count"] == 2
    assert before_closure["current_blocker_count"] == 2
    assert after_closure["pending_decision_blocker_count"] == 0
    assert after_closure["restored_pending_count"] == 0
    assert after_closure["current_blocker_count"] == 0


def _foundation_closure_for_commands(commands_snapshot: dict) -> dict:
    return maintenance._foundation_closure_readiness(
        {
            "evidence_audit": {
                "current_evidence_failure_count": 0,
                "current_missing_evidence_count": 0,
                "historical_evidence_debt_count": 0,
                "unknown_era_evidence_issue_count": 0,
                "historical_missing_evidence_count": 0,
                "unknown_era_missing_evidence_count": 0,
                "classification": {},
            },
            "pending_decision_hygiene": build_pending_decision_hygiene_report(commands_snapshot),
            "runtime_timeout_diagnostics": build_runtime_timeout_diagnostics(commands_snapshot),
            "replay_diagnostics": {
                "status": "ok",
                "replay_boundary": {"classification": "no_replay_gap_detected"},
            },
            "command_lifecycle": {"status": "ok"},
            "runtime_snapshot": {"status": "ok"},
            "system_resources": {"status": "ok"},
            "process_resources": {"status": "ok"},
            "network_ports": {"status": "ok"},
            "app_discovery": {"entries": []},
        }
    )
