from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from aegis.core.commands import ApprovalManager, get_approval_manager, restore_approval_manager_from_journal
from aegis.core.constants import ActionStatus, CommandStatus, IntentSource, RiskLevel
from aegis.core.context import ExecutionContext
from aegis.core.guard_policy import classify_intent_risk as real_classify_intent_risk
from aegis.core.non_executable_runtime_adapter import (
    project_non_executable_events_to_action_timeline,
    project_non_executable_events_to_snapshot,
)
from aegis.core.protocol import ProtocolEventType, RuntimeEvent, reset_sequence_for_testing
from aegis.core.runtime_authority import get_runtime_authority
from aegis.core.schemas import (
    ActionResult,
    CommandRequest,
    ExecutionEvidence,
    GuardResult,
    IntentResult,
    ReliabilityMetrics,
)
from aegis.orchestrator import orchestrator as orchestrator_module
from aegis.orchestrator.orchestrator import Orchestrator


class FakeRouter:
    async def route(self, request: CommandRequest) -> SimpleNamespace:
        return SimpleNamespace(planner_model=None)


class FakeParser:
    def __init__(self, intent: IntentResult | list[IntentResult]) -> None:
        self.intent = intent

    async def parse(self, text: str, model: str | None = None) -> list[IntentResult]:
        if isinstance(self.intent, list):
            return self.intent
        return [self.intent]


class FakePlanner:
    def plan(self, intents: list[IntentResult]) -> list[IntentResult]:
        return intents


class FakeVerifier:
    async def verify_result(self, result: ActionResult) -> float:
        return 1.0


class SuccessfulExecutor:
    async def execute(
        self,
        intent_result: IntentResult,
        ctx: ExecutionContext,
        cancellation_token=None,
    ) -> ActionResult:
        return ActionResult(
            action=intent_result.intent,
            params=intent_result.params,
            status=ActionStatus.EXECUTED,
            success=True,
            output="ok",
            metrics=ReliabilityMetrics(determinism_score=1.0),
        )


class SpyExecutor:
    def __init__(self) -> None:
        self.calls: list[tuple[IntentResult, ExecutionContext]] = []

    async def execute(
        self,
        intent_result: IntentResult,
        ctx: ExecutionContext,
        cancellation_token=None,
    ) -> ActionResult:
        self.calls.append((intent_result, ctx))
        return ActionResult(
            action=intent_result.intent,
            params=intent_result.params,
            status=ActionStatus.EXECUTED,
            success=True,
            output="ok",
            metrics=ReliabilityMetrics(determinism_score=1.0),
        )


class AllowGuard:
    def evaluate(self, intent: IntentResult) -> GuardResult:
        return GuardResult(
            allowed=True,
            reason="test allows legacy guard so boundary classifier is isolated",
            risk=intent.risk,
            requires_approval=False,
            warnings=[],
        )


class NonExecutableBoundaryJournal:
    def __init__(self) -> None:
        self.events: list[RuntimeEvent] = []

    def append(self, event: RuntimeEvent) -> RuntimeEvent:
        self.events.append(event)
        return event


class WaitingExecutor:
    async def execute(
        self,
        intent_result: IntentResult,
        ctx: ExecutionContext,
        cancellation_token=None,
    ) -> ActionResult:
        for _ in range(200):
            if cancellation_token and cancellation_token.cancelled:
                return ActionResult(
                    action=intent_result.intent,
                    params=intent_result.params,
                    status=ActionStatus.CANCELLED,
                    success=False,
                    output=cancellation_token.cancelled_reason or "cancelled",
                )
            await asyncio.sleep(0.01)
        return ActionResult(
            action=intent_result.intent,
            params=intent_result.params,
            status=ActionStatus.FAILED,
            success=False,
            output="cancel token was not observed",
        )


class UnverifiedEvidenceExecutor:
    async def execute(
        self,
        intent_result: IntentResult,
        ctx: ExecutionContext,
        cancellation_token=None,
    ) -> ActionResult:
        evidence = ExecutionEvidence(
            action=intent_result.intent,
            target=str(intent_result.params.get("app") or intent_result.intent),
            target_type="application",
            method="launch",
            verification_state="unverified",
            started_at_ms=1,
            completed_at_ms=2,
            warnings=["No process_name configured; launch cannot be process-verified."],
        )
        return ActionResult(
            action=intent_result.intent,
            params=intent_result.params,
            status=ActionStatus.EXECUTED,
            success=True,
            output="launched but not verified",
            metrics=ReliabilityMetrics(determinism_score=1.0),
            proof={"execution_evidence": evidence.model_dump()},
            execution_evidence=evidence,
        )


def passed_check(name: str) -> dict:
    return {
        "check_name": name,
        "expected": "present and passed",
        "observed": "ok",
        "passed": True,
        "reason": "ok",
    }


def verified_desktop_checks(action: str) -> list[dict]:
    if action == "open_app":
        return [
            passed_check("process_name_known"),
            passed_check("single_matching_window"),
            passed_check("process_alive"),
            passed_check("window_manifested"),
            passed_check("window_pid_matches_target_process"),
        ]
    if action == "focus_app":
        return [
            passed_check("process_name_known"),
            passed_check("single_matching_window"),
            passed_check("foreground_hwnd_present"),
            passed_check("foreground_title_matches_target"),
            passed_check("foreground_pid_matches_target_process"),
            passed_check("foreground_window_matches_target"),
        ]
    if action == "close_app":
        return [
            passed_check("process_name_known"),
            passed_check("process_not_alive"),
        ]
    return []


class VerifiedDesktopExecutor:
    async def execute(
        self,
        intent_result: IntentResult,
        ctx: ExecutionContext,
        cancellation_token=None,
    ) -> ActionResult:
        evidence = ExecutionEvidence(
            action=intent_result.intent,
            target=str(intent_result.params.get("app") or intent_result.intent),
            target_type="application",
            method="process_window_verifier",
            verifier="process-window-verifier/2",
            verification_state="verified",
            started_at_ms=1,
            completed_at_ms=2,
            process_name="notepad.exe",
            pids=[] if intent_result.intent == "close_app" else [4242],
            process_alive=False if intent_result.intent == "close_app" else True,
            verification_checks=verified_desktop_checks(intent_result.intent),
        )
        return ActionResult(
            action=intent_result.intent,
            params=intent_result.params,
            status=ActionStatus.EXECUTED,
            success=True,
            output="verified",
            metrics=ReliabilityMetrics(determinism_score=1.0),
            proof={"execution_evidence": evidence.model_dump()},
            execution_evidence=evidence,
        )


class CriticalCheckFailureExecutor:
    async def execute(
        self,
        intent_result: IntentResult,
        ctx: ExecutionContext,
        cancellation_token=None,
    ) -> ActionResult:
        evidence = ExecutionEvidence(
            action=intent_result.intent,
            target=str(intent_result.params.get("app") or intent_result.intent),
            target_type="application",
            method="focus_window",
            verification_state="verified",
            started_at_ms=1,
            completed_at_ms=2,
            process_name="portal.exe",
            pids=[4242],
            verification_checks=[
                {
                    "check_name": "process_name_known",
                    "expected": "configured process name",
                    "observed": "portal.exe",
                    "passed": True,
                    "reason": "ok",
                },
                {
                    "check_name": "single_matching_window",
                    "expected": "one matching target window",
                    "observed": 1,
                    "passed": True,
                    "reason": "ok",
                },
                {
                    "check_name": "foreground_hwnd_present",
                    "expected": "foreground HWND",
                    "observed": 1001,
                    "passed": True,
                    "reason": "ok",
                },
                {
                    "check_name": "foreground_title_matches_target",
                    "expected": "target title",
                    "observed": "Portal",
                    "passed": True,
                    "reason": "ok",
                },
                {
                    "check_name": "foreground_pid_matches_target_process",
                    "expected": {"pid": 4242},
                    "observed": {"pid": 5151},
                    "passed": False,
                    "reason": "foreground PID does not match target process",
                },
                {
                    "check_name": "foreground_window_matches_target",
                    "expected": "target foreground window",
                    "observed": "Portal",
                    "passed": True,
                    "reason": "ok",
                },
            ],
        )
        return ActionResult(
            action=intent_result.intent,
            params=intent_result.params,
            status=ActionStatus.EXECUTED,
            success=True,
            output="focused but critical check failed",
            metrics=ReliabilityMetrics(determinism_score=1.0),
            proof={"execution_evidence": evidence.model_dump()},
            execution_evidence=evidence,
        )


class FailedEvidenceExecutor:
    async def execute(
        self,
        intent_result: IntentResult,
        ctx: ExecutionContext,
        cancellation_token=None,
    ) -> ActionResult:
        evidence = ExecutionEvidence(
            action=intent_result.intent,
            target=str(intent_result.params.get("app") or intent_result.intent),
            target_type="application",
            method="launch",
            verification_state="failed",
            started_at_ms=1,
            completed_at_ms=2,
            process_name="steam.exe",
            pids=[],
            process_alive=False,
            warnings=["process crashed after launch"],
        )
        return ActionResult(
            action=intent_result.intent,
            params=intent_result.params,
            status=ActionStatus.FAILED,
            success=False,
            output="process crashed after launch",
            metrics=ReliabilityMetrics(determinism_score=0.0),
            proof={"execution_evidence": evidence.model_dump()},
            execution_evidence=evidence,
        )


class ProofBackedSideEffectExecutor:
    def __init__(self, proof_key: str) -> None:
        self.proof_key = proof_key

    async def execute(
        self,
        intent_result: IntentResult,
        ctx: ExecutionContext,
        cancellation_token=None,
    ) -> ActionResult:
        return ActionResult(
            action=intent_result.intent,
            params=intent_result.params,
            status=ActionStatus.EXECUTED,
            success=True,
            output="ok",
            metrics=ReliabilityMetrics(determinism_score=1.0),
            proof={self.proof_key: {"tool": intent_result.intent}},
        )


def build_orchestrator(intent: IntentResult | list[IntentResult], executor=None) -> Orchestrator:
    orchestrator = Orchestrator()
    orchestrator.router = FakeRouter()
    orchestrator.parser = FakeParser(intent)
    orchestrator.planner = FakePlanner()
    orchestrator.verifier = FakeVerifier()
    orchestrator.executor = executor or SuccessfulExecutor()
    return orchestrator


def intent_result(intent: str, risk: RiskLevel, params: dict | None = None) -> IntentResult:
    return IntentResult(
        intent=intent,
        confidence=1.0,
        params=params or {},
        risk=risk,
        source=IntentSource.RULE,
        raw_input=intent,
    )


def test_approval_manager_restores_pending_approval_snapshot() -> None:
    source = ApprovalManager()
    source.register_pending(
        command_id="22222222-2222-4222-8222-222222222222",
        text="click",
        trace_id="trace-pending",
        risk_level=RiskLevel.MEDIUM,
        reason="medium risk requires approval",
        warnings=["needs confirmation"],
        metadata={"intent": "click"},
    )

    restored = ApprovalManager()
    restored.restore_from_snapshot(source.snapshot())

    snapshot = restored.snapshot()
    assert len(snapshot["pending_approvals"]) == 1
    assert snapshot["pending_approvals"][0]["command_id"] == "22222222-2222-4222-8222-222222222222"
    assert snapshot["pending_approvals"][0]["risk_level"] == RiskLevel.MEDIUM.value

    approved = restored.approve("22222222-2222-4222-8222-222222222222")
    assert approved.status == CommandStatus.APPROVED
    assert approved.approved is True


def test_approval_manager_tracks_pending_clarification_as_first_class_lifecycle() -> None:
    source = ApprovalManager()
    record = source.register_waiting_clarification(
        command_id="22222222-2222-4222-8333-222222222222",
        text="click that",
        trace_id="trace-clarification",
        risk_level=RiskLevel.HIGH,
        reason="generic click quarantine requires target resolution",
        warnings=["target resolution required"],
        metadata={"clarification_id": "clarification-policy"},
    )

    snapshot = source.snapshot()

    assert record.status == CommandStatus.WAITING_FOR_CLARIFICATION
    assert record.active is False
    assert record.approval_required is False
    assert record.clarification_required is True
    assert record.verification_state == "unverified"
    assert record.completed_at is None
    assert len(snapshot["pending_clarifications"]) == 1
    assert snapshot["pending_clarifications"][0]["command_id"] == record.command_id
    assert snapshot["pending_clarifications"][0]["status"] == "waiting_for_clarification"
    assert snapshot["pending_clarifications"][0]["clarification_required"] is True
    assert snapshot["pending_clarifications"][0]["approved"] is False
    assert snapshot["pending_clarifications"][0]["metadata"]["clarification_id"] == "clarification-policy"
    assert snapshot["pending_approvals"] == []


def test_approval_manager_restores_pending_clarification_snapshot() -> None:
    source = ApprovalManager()
    source.register_waiting_clarification(
        command_id="33333333-3333-4333-8444-333333333333",
        text="click that",
        trace_id="trace-clarification-restore",
        risk_level=RiskLevel.HIGH,
        reason="generic click quarantine requires target resolution",
        metadata={"clarification_id": "clarification-policy"},
    )

    restored = ApprovalManager()
    restored.restore_from_snapshot(source.snapshot())
    snapshot = restored.snapshot()
    record = restored.get("33333333-3333-4333-8444-333333333333")

    assert record is not None
    assert record.status == CommandStatus.WAITING_FOR_CLARIFICATION
    assert record.clarification_required is True
    assert record.active is False
    assert len(snapshot["pending_clarifications"]) == 1
    assert snapshot["pending_clarifications"][0]["command_id"] == record.command_id


def test_approval_manager_denies_pending_approval_by_decision_id_without_execution() -> None:
    manager = ApprovalManager()
    manager.register_pending(
        command_id="cmd-deny",
        text="write file",
        trace_id="trace-deny",
        risk_level=RiskLevel.MEDIUM,
        reason="approval required",
        metadata={"approval_id": "approval-deny"},
    )

    record = manager.resolve_approval("approval-deny", approved=False, reason="operator denied")

    assert record.status == CommandStatus.REJECTED
    assert record.rejected is True
    assert record.approved is False
    assert record.approval_required is False
    assert record.active is False
    assert record.reason == "operator denied"
    assert record.metadata["approval_resolution_status"] == "approval_denied"
    assert record.metadata["mutation_performed"] is False
    assert record.metadata["not_executed"] is True
    assert manager.snapshot()["pending_approvals"] == []


def test_approval_manager_grant_for_non_resumable_decision_stays_non_executed() -> None:
    manager = ApprovalManager()
    manager.register_pending(
        command_id="cmd-click-approval",
        text="click 10 20",
        trace_id="trace-click-approval",
        risk_level=RiskLevel.HIGH,
        reason="generic click quarantine",
        metadata={
            "approval_id": "approval-click",
            "resume_allowed": False,
            "policy_rule": "generic_click.quarantined.approval_required",
        },
    )

    record = manager.resolve_approval("approval-click", approved=True)

    assert record.status == CommandStatus.BLOCKED
    assert record.approved is True
    assert record.active is False
    assert record.approval_required is False
    assert record.metadata["approval_resolution_status"] == "approval_granted"
    assert record.metadata["completed_without_execution"] is True
    assert record.metadata["mutation_performed"] is False
    assert record.metadata["not_executed"] is True
    assert manager.snapshot()["pending_approvals"] == []


def test_approval_manager_resolves_and_cancels_clarification_without_execution() -> None:
    manager = ApprovalManager()
    manager.register_waiting_clarification(
        command_id="cmd-clarify",
        text="click that",
        trace_id="trace-clarify",
        risk_level=RiskLevel.HIGH,
        reason="target resolution required",
        metadata={"clarification_id": "clarification-click"},
    )

    resolved = manager.resolve_clarification("clarification-click", answer="the blue button")

    assert resolved.status == CommandStatus.BLOCKED
    assert resolved.clarification_required is False
    assert resolved.active is False
    assert resolved.metadata["clarification_resolution_status"] == "clarification_resolved"
    assert resolved.metadata["clarification_answer"] == "the blue button"
    assert resolved.metadata["completed_without_execution"] is True
    assert resolved.metadata["mutation_performed"] is False
    assert manager.snapshot()["pending_clarifications"] == []

    manager.register_waiting_clarification(
        command_id="cmd-clarify-cancel",
        text="click that",
        trace_id="trace-clarify-cancel",
        risk_level=RiskLevel.HIGH,
        reason="target resolution required",
        metadata={"clarification_id": "clarification-cancel"},
    )
    cancelled = manager.resolve_clarification("clarification-cancel", cancelled=True)

    assert cancelled.status == CommandStatus.CANCELLED
    assert cancelled.metadata["clarification_resolution_status"] == "clarification_cancelled"
    assert cancelled.metadata["mutation_performed"] is False
    assert cancelled.metadata["not_executed"] is True


def test_missing_and_already_resolved_decision_ids_fail_safely() -> None:
    manager = ApprovalManager()
    manager.register_pending(
        command_id="cmd-once",
        text="write file",
        trace_id="trace-once",
        risk_level=RiskLevel.MEDIUM,
        reason="approval required",
        metadata={"approval_id": "approval-once"},
    )

    with pytest.raises(KeyError):
        manager.resolve_approval("missing-approval", approved=True)

    manager.resolve_approval("approval-once", approved=False)

    with pytest.raises(ValueError):
        manager.resolve_approval("approval-once", approved=True)

    manager.register_waiting_clarification(
        command_id="cmd-clarify-once",
        text="click that",
        trace_id="trace-clarify-once",
        risk_level=RiskLevel.HIGH,
        reason="target resolution required",
        metadata={"clarification_id": "clarification-once"},
    )
    manager.resolve_clarification("clarification-once", cancelled=True)

    with pytest.raises(ValueError):
        manager.resolve_clarification("clarification-once", answer="late answer")


def test_approval_manager_marks_active_snapshot_cancelled_on_restore() -> None:
    source = ApprovalManager()
    source.create_received("read README.md", command_id="33333333-3333-4333-8333-333333333333")
    source.mark_running(
        "33333333-3333-4333-8333-333333333333",
        trace_id="trace-running",
        risk_level=RiskLevel.LOW,
        verification_state="verified",
    )

    restored = ApprovalManager()
    restored.restore_from_snapshot(source.snapshot())

    snapshot = restored.snapshot()
    record = restored.get("33333333-3333-4333-8333-333333333333")
    token = restored.token_for("33333333-3333-4333-8333-333333333333")

    assert snapshot["active_command"] is None
    assert record is not None
    assert record.status == CommandStatus.CANCELLED
    assert record.active is False
    assert record.approval_required is False
    assert record.reason == "runtime restarted before command completed"
    assert token.cancelled is True


def test_restores_approval_manager_from_latest_journal_runtime_snapshot() -> None:
    source = ApprovalManager()
    source.register_pending(
        command_id="44444444-4444-4444-8444-444444444444",
        text="type hello",
        trace_id="trace-journal",
        risk_level=RiskLevel.MEDIUM,
        reason="medium risk requires approval",
    )

    class FakeJournal:
        def events_after(self, sequence_num: int) -> list[dict]:
            assert sequence_num == 0
            return [
                {"event_type": "COMMAND_RECEIVED", "payload": {"text": "old"}},
                {
                    "event_type": "SNAPSHOT_CREATED",
                    "payload": {
                        "runtime": {
                            "commands": source.snapshot(),
                        },
                    },
                },
            ]

    restored = ApprovalManager()

    assert restore_approval_manager_from_journal(journal=FakeJournal(), manager=restored) is True
    assert restored.snapshot()["pending_approvals"][0]["command_id"] == "44444444-4444-4444-8444-444444444444"


def test_restores_approval_manager_from_recent_journal_tail_before_full_scan() -> None:
    source = ApprovalManager()
    source.register_pending(
        command_id="44444444-4444-4444-9444-444444444444",
        text="type hello",
        trace_id="trace-recent-journal",
        risk_level=RiskLevel.MEDIUM,
        reason="medium risk requires approval",
    )

    class FakeJournal:
        def recent_events(self) -> list[dict]:
            return [
                {
                    "event_type": "SNAPSHOT_CREATED",
                    "payload": {
                        "runtime": {
                            "commands": source.snapshot(),
                        },
                    },
                },
            ]

        def events_after(self, sequence_num: int) -> list[dict]:
            raise AssertionError("startup restore should use recent journal tail before full scan")

    restored = ApprovalManager()

    assert restore_approval_manager_from_journal(journal=FakeJournal(), manager=restored) is True
    assert restored.snapshot()["pending_approvals"][0]["command_id"] == "44444444-4444-4444-9444-444444444444"


def test_restores_approval_manager_falls_back_to_full_journal_when_recent_tail_has_no_state() -> None:
    source = ApprovalManager()
    command = source.register_pending(
        command_id="55555555-5555-4555-9555-555555555555",
        text="open notepad",
        trace_id="trace-full-journal",
        risk_level=RiskLevel.MEDIUM,
        reason="medium risk requires approval",
    )

    class FakeJournal:
        def recent_events(self) -> list[dict]:
            return [{"event_type": "TELEMETRY_UPDATE", "payload": {"cpu": 1}}]

        def events_after(self, sequence_num: int) -> list[dict]:
            assert sequence_num == 0
            return [
                {
                    "event_type": "APPROVAL_REQUIRED",
                    "payload": {"command": command.to_dict()},
                },
            ]

    restored = ApprovalManager()

    assert restore_approval_manager_from_journal(journal=FakeJournal(), manager=restored) is True
    assert restored.snapshot()["pending_approvals"][0]["command_id"] == "55555555-5555-4555-9555-555555555555"


def test_restores_approval_manager_from_command_events_when_snapshot_missing() -> None:
    source = ApprovalManager()
    command = source.register_pending(
        command_id="55555555-5555-4555-8555-555555555555",
        text="open notepad",
        trace_id="trace-approval-event",
        risk_level=RiskLevel.MEDIUM,
        reason="medium risk requires approval",
    )

    class FakeJournal:
        def events_after(self, sequence_num: int) -> list[dict]:
            assert sequence_num == 0
            return [
                {
                    "event_type": "APPROVAL_REQUIRED",
                    "payload": {"command": command.to_dict()},
                },
            ]

    restored = ApprovalManager()

    assert restore_approval_manager_from_journal(journal=FakeJournal(), manager=restored) is True
    assert restored.snapshot()["pending_approvals"][0]["command_id"] == "55555555-5555-4555-8555-555555555555"


@pytest.fixture(autouse=True)
def reset_approval_manager() -> None:
    get_approval_manager().reset_for_tests()


def _boundary_context(
    journal: NonExecutableBoundaryJournal,
    *,
    start: int = 9000,
    fanout=None,
) -> dict:
    context = {
        "enable_non_executable_guard_boundary": True,
        "non_executable_journal": journal,
        "non_executable_starting_sequence_num": start,
    }
    if fanout is not None:
        context["non_executable_fanout"] = fanout
    return context


def _default_non_executable_context(
    journal: NonExecutableBoundaryJournal,
    *,
    fanout=None,
) -> dict:
    context = {"non_executable_journal": journal}
    if fanout is not None:
        context["non_executable_fanout"] = fanout
    return context


def _quiet_runtime_emissions(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_emit_event(*args, **kwargs):
        return None

    async def fake_emit_state_change(*args, **kwargs):
        return True

    async def fake_emit_command_status(*args, **kwargs):
        return None

    async def fake_emit_task_finished(*args, **kwargs):
        return None

    monkeypatch.setattr(orchestrator_module.ws_bridge, "emit_event", fake_emit_event)
    monkeypatch.setattr(orchestrator_module.ws_bridge, "emit_state_change", fake_emit_state_change)
    monkeypatch.setattr(orchestrator_module.ws_bridge, "emit_command_status", fake_emit_command_status)
    monkeypatch.setattr(orchestrator_module.ws_bridge, "emit_task_finished", fake_emit_task_finished)


def _event_types(events: list[RuntimeEvent]) -> list[str]:
    return [event.type for event in events]


def _assert_non_executable_event_shape(events: list[RuntimeEvent]) -> None:
    assert events
    sequences = [event.sequence_num for event in events]
    assert sequences == sorted(sequences)
    assert len(sequences) == len(set(sequences))

    forbidden_event_types = {
        ProtocolEventType.ACTION_STARTED.value,
        ProtocolEventType.ACTION_COMPLETED.value,
        ProtocolEventType.ACTION_FAILED.value,
        ProtocolEventType.APPROVAL_REQUIRED.value,
    }
    assert not forbidden_event_types.intersection(_event_types(events))
    for event in events:
        assert event.causation_id
        payload = event.payload
        assert payload["not_executed"] is True
        assert payload["command_id"]
        assert payload["trace_id"]
        assert payload["decision_status"]
        assert payload["risk_level"]
        assert payload["policy_rule"]
        assert payload["reason"]
        assert "execution_evidence" not in payload
        assert payload.get("success") is not True
        assert payload.get("verified") is not True
        assert payload.get("action_started") is not True


def test_resolution_events_clear_pending_projection_without_success_shape() -> None:
    approval_requested = RuntimeEvent(
        type=ProtocolEventType.APPROVAL_REQUESTED.value,
        sequence_num=1,
        trace_id="trace-resolution",
        payload={
            "command_id": "cmd-resolution",
            "trace_id": "trace-resolution",
            "approval_id": "approval-resolution",
            "decision_status": "approval_required",
            "risk_level": "high",
            "policy_rule": "generic_click.quarantined.approval_required",
            "reason": "generic click quarantine",
            "not_executed": True,
        },
    )
    approval_resolved = RuntimeEvent(
        type=ProtocolEventType.APPROVAL_RESOLVED.value,
        sequence_num=2,
        trace_id="trace-resolution",
        payload={
            "command_id": "cmd-resolution",
            "trace_id": "trace-resolution",
            "approval_id": "approval-resolution",
            "decision": "granted",
            "approval_status": "approval_granted",
            "command_status": "blocked",
            "risk_level": "high",
            "policy_rule": "generic_click.quarantined.approval_required",
            "reason": "approval recorded but target resolution is missing",
            "not_executed": True,
            "executed": False,
            "mutation_performed": False,
        },
    )
    clarification_requested = RuntimeEvent(
        type=ProtocolEventType.CLARIFICATION_REQUESTED.value,
        sequence_num=3,
        trace_id="trace-resolution",
        payload={
            "command_id": "cmd-clarification-resolution",
            "trace_id": "trace-resolution",
            "clarification_id": "clarification-resolution",
            "decision_status": "clarification_required",
            "risk_level": "high",
            "policy_rule": "generic_click.quarantined.clarification_required",
            "reason": "generic click quarantine",
            "not_executed": True,
        },
    )
    clarification_resolved = RuntimeEvent(
        type=ProtocolEventType.CLARIFICATION_RESOLVED.value,
        sequence_num=4,
        trace_id="trace-resolution",
        payload={
            "command_id": "cmd-clarification-resolution",
            "trace_id": "trace-resolution",
            "clarification_id": "clarification-resolution",
            "clarification_status": "clarification_resolved",
            "command_status": "blocked",
            "risk_level": "high",
            "policy_rule": "generic_click.quarantined.clarification_required",
            "reason": "clarification recorded without execution",
            "not_executed": True,
            "executed": False,
            "mutation_performed": False,
        },
    )

    snapshot = project_non_executable_events_to_snapshot([
        approval_requested,
        approval_resolved,
        clarification_requested,
        clarification_resolved,
    ])
    timeline = project_non_executable_events_to_action_timeline([
        approval_requested,
        approval_resolved,
        clarification_requested,
        clarification_resolved,
    ])

    assert snapshot["pending_approval"] is None
    assert snapshot["pending_clarification"] is None
    assert snapshot["command_status"] == "blocked"
    assert snapshot["terminal_non_executed"] is True
    assert snapshot["last_resolution"]["kind"] == "clarification_resolved"
    assert len(snapshot["resolved_decisions"]) == 2
    assert [entry["kind"] for entry in timeline] == [
        "approval_requested",
        "approval_resolved",
        "clarification_requested",
        "clarification_resolved",
    ]
    assert all(entry.get("executed") is False for entry in timeline)
    assert all(entry.get("verified") is not True for entry in timeline)
    assert all("execution_evidence" not in entry for entry in timeline)


def _force_guard_decision(monkeypatch: pytest.MonkeyPatch, intent: str, params: dict) -> None:
    def fake_classify_intent_risk(
        _intent: str,
        _params: dict | None,
        context: dict | None = None,
    ):
        return real_classify_intent_risk(intent, params, context)

    monkeypatch.setattr(
        orchestrator_module,
        "classify_intent_risk",
        fake_classify_intent_risk,
        raising=False,
    )


def _spy_action_started(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    calls: list[dict] = []

    async def fake_emit_action_started(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(orchestrator_module.ws_bridge, "emit_action_started", fake_emit_action_started)
    return calls


@pytest.mark.asyncio
async def test_non_executable_boundary_ready_intent_still_reaches_executor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reset_sequence_for_testing()
    _quiet_runtime_emissions(monkeypatch)
    executor = SpyExecutor()
    journal = NonExecutableBoundaryJournal()
    action_started_calls = _spy_action_started(monkeypatch)

    async def fail_append_non_executable_decision(*args, **kwargs):
        raise AssertionError("ready decisions must not call non-executable append")

    monkeypatch.setattr(
        orchestrator_module.ws_bridge,
        "append_non_executable_decision",
        fail_append_non_executable_decision,
    )
    orchestrator = build_orchestrator(
        intent_result("read_file", RiskLevel.LOW, {"path": "README.md"}),
        executor=executor,
    )
    orchestrator.guard = AllowGuard()

    response = await orchestrator.process(
        CommandRequest(text="read README.md", context=_boundary_context(journal))
    )

    assert response.status == CommandStatus.EXECUTED
    assert len(executor.calls) == 1
    assert len(action_started_calls) == 1
    assert journal.events == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("forced_intent", "forced_params", "expected_status", "expected_events", "projection_key"),
    [
        (
            "write_file",
            {"path": "scratch/out.txt", "content": "unsafe write"},
            CommandStatus.PENDING_APPROVAL,
            [
                ProtocolEventType.COMMAND_CLASSIFIED.value,
                ProtocolEventType.APPROVAL_REQUESTED.value,
                ProtocolEventType.COMMAND_WAITING_FOR_APPROVAL.value,
            ],
            "pending_approval",
        ),
        (
            "read_file",
            {},
            CommandStatus.WAITING_FOR_CLARIFICATION,
            [
                ProtocolEventType.COMMAND_CLASSIFIED.value,
                ProtocolEventType.CLARIFICATION_REQUESTED.value,
                ProtocolEventType.COMMAND_WAITING_FOR_CLARIFICATION.value,
            ],
            "pending_clarification",
        ),
        (
            "run_command",
            {"command": "rm -rf /"},
            CommandStatus.BLOCKED,
            [
                ProtocolEventType.COMMAND_CLASSIFIED.value,
                ProtocolEventType.ACTION_BLOCKED_BY_POLICY.value,
                ProtocolEventType.COMMAND_BLOCKED.value,
            ],
            "last_blocked_action",
        ),
    ],
)
async def test_non_executable_boundary_prevents_executor_and_action_started(
    monkeypatch: pytest.MonkeyPatch,
    forced_intent: str,
    forced_params: dict,
    expected_status: CommandStatus,
    expected_events: list[str],
    projection_key: str,
) -> None:
    reset_sequence_for_testing()
    _quiet_runtime_emissions(monkeypatch)
    executor = SpyExecutor()
    journal = NonExecutableBoundaryJournal()
    emitted: list[RuntimeEvent] = []
    append_calls = []
    action_started_calls = _spy_action_started(monkeypatch)
    _force_guard_decision(monkeypatch, forced_intent, forced_params)
    real_append = orchestrator_module.ws_bridge.append_non_executable_decision

    async def fanout(event: RuntimeEvent) -> None:
        assert any(stored.event_id == event.event_id for stored in journal.events)
        emitted.append(event)

    async def spy_append_non_executable_decision(*args, **kwargs):
        append_calls.append((args, kwargs))
        return await real_append(*args, **kwargs)

    monkeypatch.setattr(
        orchestrator_module.ws_bridge,
        "append_non_executable_decision",
        spy_append_non_executable_decision,
    )
    orchestrator = build_orchestrator(
        intent_result("read_file", RiskLevel.LOW, {"path": "README.md"}),
        executor=executor,
    )
    orchestrator.guard = AllowGuard()

    response = await orchestrator.process(
        CommandRequest(text="read README.md", context=_boundary_context(journal, fanout=fanout))
    )

    assert response.status == expected_status
    assert executor.calls == []
    assert action_started_calls == []
    assert len(append_calls) == 1
    assert append_calls[0][1]["journal"] is journal
    assert _event_types(journal.events) == expected_events
    assert [event.sequence_num for event in journal.events] == [1, 2, 3]
    assert emitted == journal.events
    assert all(event.causation_id == event.span_id for event in journal.events)
    assert all(event.payload.get("action_id") == event.span_id for event in journal.events)
    assert all(event.payload["command_id"] == response.trace_id for event in journal.events)
    assert all(event.payload["trace_id"] == response.trace_id for event in journal.events)
    _assert_non_executable_event_shape(journal.events)
    snapshot_patch = project_non_executable_events_to_snapshot(journal.events)
    assert snapshot_patch[projection_key] is not None
    assert "execution_evidence" not in snapshot_patch
    timeline_entries = project_non_executable_events_to_action_timeline(journal.events)
    assert timeline_entries
    assert all("execution_evidence" not in entry for entry in timeline_entries)


@pytest.mark.asyncio
async def test_generic_click_boundary_quarantines_before_executor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reset_sequence_for_testing()
    _quiet_runtime_emissions(monkeypatch)
    executor = SpyExecutor()
    journal = NonExecutableBoundaryJournal()
    append_calls = []
    action_started_calls = _spy_action_started(monkeypatch)
    real_append = orchestrator_module.ws_bridge.append_non_executable_decision

    async def spy_append_non_executable_decision(*args, **kwargs):
        append_calls.append((args, kwargs))
        return await real_append(*args, **kwargs)

    monkeypatch.setattr(
        orchestrator_module.ws_bridge,
        "append_non_executable_decision",
        spy_append_non_executable_decision,
    )
    orchestrator = build_orchestrator(intent_result("click", RiskLevel.LOW, {}), executor=executor)
    orchestrator.guard = AllowGuard()

    response = await orchestrator.process(
        CommandRequest(text="click", context=_boundary_context(journal, start=200))
    )

    assert response.status == CommandStatus.WAITING_FOR_CLARIFICATION
    assert executor.calls == []
    assert action_started_calls == []
    assert len(append_calls) == 1
    assert _event_types(journal.events) == [
        ProtocolEventType.COMMAND_CLASSIFIED.value,
        ProtocolEventType.CLARIFICATION_REQUESTED.value,
        ProtocolEventType.COMMAND_WAITING_FOR_CLARIFICATION.value,
    ]
    assert [event.sequence_num for event in journal.events] == [1, 2, 3]
    _assert_non_executable_event_shape(journal.events)
    assert all(event.type != ProtocolEventType.APPROVAL_REQUIRED.value for event in journal.events)
    reasons = " ".join(str(event.payload.get("reason", "")) for event in journal.events)
    policy_rules = " ".join(str(event.payload.get("policy_rule", "")) for event in journal.events)
    assert "generic click quarantine" in reasons
    assert "target resolution" in reasons
    assert "generic_click.quarantined" in policy_rules
    timeline_entries = project_non_executable_events_to_action_timeline(journal.events)
    assert [entry["kind"] for entry in timeline_entries] == ["clarification_requested"]
    assert all("execution_evidence" not in entry for entry in timeline_entries)


@pytest.mark.asyncio
async def test_default_generic_click_quarantine_prevents_executor_without_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reset_sequence_for_testing()
    _quiet_runtime_emissions(monkeypatch)
    executor = SpyExecutor()
    journal = NonExecutableBoundaryJournal()
    emitted: list[RuntimeEvent] = []
    append_calls = []
    action_started_calls = _spy_action_started(monkeypatch)
    real_append = orchestrator_module.ws_bridge.append_non_executable_decision

    async def fanout(event: RuntimeEvent) -> None:
        assert any(stored.event_id == event.event_id for stored in journal.events)
        emitted.append(event)

    async def spy_append_non_executable_decision(*args, **kwargs):
        append_calls.append((args, kwargs))
        return await real_append(*args, **kwargs)

    monkeypatch.setattr(
        orchestrator_module.ws_bridge,
        "append_non_executable_decision",
        spy_append_non_executable_decision,
    )
    orchestrator = build_orchestrator(intent_result("click", RiskLevel.LOW, {}), executor=executor)
    orchestrator.guard = AllowGuard()

    response = await orchestrator.process(
        CommandRequest(text="click", context=_default_non_executable_context(journal, fanout=fanout))
    )

    assert response.status == CommandStatus.WAITING_FOR_CLARIFICATION
    assert executor.calls == []
    assert action_started_calls == []
    assert len(append_calls) == 1
    assert append_calls[0][1]["journal"] is journal
    assert _event_types(journal.events) == [
        ProtocolEventType.COMMAND_CLASSIFIED.value,
        ProtocolEventType.CLARIFICATION_REQUESTED.value,
        ProtocolEventType.COMMAND_WAITING_FOR_CLARIFICATION.value,
    ]
    assert emitted == journal.events
    _assert_non_executable_event_shape(journal.events)
    reasons = " ".join(str(event.payload.get("reason", "")) for event in journal.events)
    assert "generic click quarantine" in reasons
    assert "target resolution" in reasons
    assert ProtocolEventType.APPROVAL_REQUIRED.value not in _event_types(journal.events)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("intent_name", "params", "text", "expected_status", "expected_events", "projection_key"),
    [
        (
            "read_file",
            {},
            "read a file",
            CommandStatus.WAITING_FOR_CLARIFICATION,
            [
                ProtocolEventType.COMMAND_CLASSIFIED.value,
                ProtocolEventType.CLARIFICATION_REQUESTED.value,
                ProtocolEventType.COMMAND_WAITING_FOR_CLARIFICATION.value,
            ],
            "pending_clarification",
        ),
        (
            "open_app",
            {"app": "unknownapp"},
            "open unknownapp",
            CommandStatus.WAITING_FOR_CLARIFICATION,
            [
                ProtocolEventType.COMMAND_CLASSIFIED.value,
                ProtocolEventType.CLARIFICATION_REQUESTED.value,
                ProtocolEventType.COMMAND_WAITING_FOR_CLARIFICATION.value,
            ],
            "pending_clarification",
        ),
    ],
)
async def test_default_non_executable_guard_stops_non_click_before_executor(
    monkeypatch: pytest.MonkeyPatch,
    intent_name: str,
    params: dict,
    text: str,
    expected_status: CommandStatus,
    expected_events: list[str],
    projection_key: str,
) -> None:
    reset_sequence_for_testing()
    _quiet_runtime_emissions(monkeypatch)
    executor = SpyExecutor()
    journal = NonExecutableBoundaryJournal()
    action_started_calls = _spy_action_started(monkeypatch)
    orchestrator = build_orchestrator(intent_result(intent_name, RiskLevel.LOW, params), executor=executor)
    orchestrator.guard = AllowGuard()

    response = await orchestrator.process(
        CommandRequest(text=text, context=_default_non_executable_context(journal))
    )

    assert response.status == expected_status
    assert executor.calls == []
    assert action_started_calls == []
    assert _event_types(journal.events) == expected_events
    _assert_non_executable_event_shape(journal.events)
    snapshot_patch = project_non_executable_events_to_snapshot(journal.events)
    assert snapshot_patch[projection_key] is not None
    timeline_entries = project_non_executable_events_to_action_timeline(journal.events)
    assert timeline_entries
    assert all(entry.get("executed") is False for entry in timeline_entries)
    assert all(entry.get("verified") is not True for entry in timeline_entries)
    assert all("execution_evidence" not in entry for entry in timeline_entries)


@pytest.mark.asyncio
async def test_default_mixed_ready_then_non_executable_non_click_plan_stops_before_partial_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reset_sequence_for_testing()
    _quiet_runtime_emissions(monkeypatch)
    executor = SpyExecutor()
    journal = NonExecutableBoundaryJournal()
    action_started_calls = _spy_action_started(monkeypatch)
    orchestrator = build_orchestrator(
        [
            intent_result("open_app", RiskLevel.LOW, {"app": "notepad"}),
            intent_result("read_file", RiskLevel.LOW, {}),
        ],
        executor=executor,
    )
    orchestrator.guard = AllowGuard()

    response = await orchestrator.process(
        CommandRequest(
            text="open notepad and read a file",
            context=_default_non_executable_context(journal),
        )
    )

    assert response.status == CommandStatus.WAITING_FOR_CLARIFICATION
    assert executor.calls == []
    assert action_started_calls == []
    assert _event_types(journal.events) == [
        ProtocolEventType.COMMAND_CLASSIFIED.value,
        ProtocolEventType.CLARIFICATION_REQUESTED.value,
        ProtocolEventType.COMMAND_WAITING_FOR_CLARIFICATION.value,
    ]
    _assert_non_executable_event_shape(journal.events)


@pytest.mark.asyncio
async def test_approval_granted_context_does_not_bypass_non_resumable_click_guard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reset_sequence_for_testing()
    _quiet_runtime_emissions(monkeypatch)
    executor = SpyExecutor()
    journal = NonExecutableBoundaryJournal()
    action_started_calls = _spy_action_started(monkeypatch)
    orchestrator = build_orchestrator(intent_result("click", RiskLevel.LOW, {"x": 10, "y": 20}), executor=executor)
    orchestrator.guard = AllowGuard()

    response = await orchestrator.process(
        CommandRequest(
            text="click 10 20",
            context={**_default_non_executable_context(journal), "approval_granted": True},
        )
    )

    pending = get_approval_manager().snapshot()["pending_approvals"][0]
    assert response.status == CommandStatus.PENDING_APPROVAL
    assert pending["metadata"]["resume_allowed"] is False
    assert pending["metadata"]["mutation_performed"] is False
    assert executor.calls == []
    assert action_started_calls == []
    _assert_non_executable_event_shape(journal.events)


@pytest.mark.asyncio
async def test_clarification_resolution_for_quarantined_click_remains_non_executed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reset_sequence_for_testing()
    _quiet_runtime_emissions(monkeypatch)
    executor = SpyExecutor()
    journal = NonExecutableBoundaryJournal()
    action_started_calls = _spy_action_started(monkeypatch)
    orchestrator = build_orchestrator(intent_result("click", RiskLevel.LOW, {}), executor=executor)
    orchestrator.guard = AllowGuard()

    response = await orchestrator.process(
        CommandRequest(text="click", context=_default_non_executable_context(journal))
    )

    manager = get_approval_manager()
    pending = manager.snapshot()["pending_clarifications"][0]
    resolved = manager.resolve_clarification(
        pending["metadata"]["clarification_id"],
        answer="the blue button",
    )

    assert response.status == CommandStatus.WAITING_FOR_CLARIFICATION
    assert resolved.status == CommandStatus.BLOCKED
    assert resolved.metadata["clarification_resolution_status"] == "clarification_resolved"
    assert resolved.metadata["completed_without_execution"] is True
    assert resolved.metadata["mutation_performed"] is False
    assert executor.calls == []
    assert action_started_calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize("text", ["tıkla", "şuna tıkla", "buna tıkla"])
async def test_default_turkish_generic_click_phrases_are_quarantined(
    monkeypatch: pytest.MonkeyPatch,
    text: str,
) -> None:
    reset_sequence_for_testing()
    _quiet_runtime_emissions(monkeypatch)
    executor = SpyExecutor()
    journal = NonExecutableBoundaryJournal()
    action_started_calls = _spy_action_started(monkeypatch)
    orchestrator = build_orchestrator(intent_result("click", RiskLevel.LOW, {}), executor=executor)
    orchestrator.guard = AllowGuard()

    response = await orchestrator.process(
        CommandRequest(text=text, context=_default_non_executable_context(journal))
    )

    assert response.status == CommandStatus.WAITING_FOR_CLARIFICATION
    assert executor.calls == []
    assert action_started_calls == []
    assert _event_types(journal.events) == [
        ProtocolEventType.COMMAND_CLASSIFIED.value,
        ProtocolEventType.CLARIFICATION_REQUESTED.value,
        ProtocolEventType.COMMAND_WAITING_FOR_CLARIFICATION.value,
    ]
    _assert_non_executable_event_shape(journal.events)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("text", "params", "expected_status", "expected_events"),
    [
        (
            "5 kere tıkla",
            {"count": 5},
            CommandStatus.WAITING_FOR_CLARIFICATION,
            [
                ProtocolEventType.COMMAND_CLASSIFIED.value,
                ProtocolEventType.CLARIFICATION_REQUESTED.value,
                ProtocolEventType.COMMAND_WAITING_FOR_CLARIFICATION.value,
            ],
        ),
        (
            "click 10 20",
            {"x": 10, "y": 20},
            CommandStatus.PENDING_APPROVAL,
            [
                ProtocolEventType.COMMAND_CLASSIFIED.value,
                ProtocolEventType.APPROVAL_REQUESTED.value,
                ProtocolEventType.COMMAND_WAITING_FOR_APPROVAL.value,
            ],
        ),
        (
            "click .primary",
            {"selector": ".primary"},
            CommandStatus.PENDING_APPROVAL,
            [
                ProtocolEventType.COMMAND_CLASSIFIED.value,
                ProtocolEventType.APPROVAL_REQUESTED.value,
                ProtocolEventType.COMMAND_WAITING_FOR_APPROVAL.value,
            ],
        ),
    ],
)
async def test_default_count_coordinate_and_selector_click_are_quarantined(
    monkeypatch: pytest.MonkeyPatch,
    text: str,
    params: dict,
    expected_status: CommandStatus,
    expected_events: list[str],
) -> None:
    reset_sequence_for_testing()
    _quiet_runtime_emissions(monkeypatch)
    executor = SpyExecutor()
    journal = NonExecutableBoundaryJournal()
    action_started_calls = _spy_action_started(monkeypatch)
    orchestrator = build_orchestrator(intent_result("click", RiskLevel.LOW, params), executor=executor)
    orchestrator.guard = AllowGuard()

    response = await orchestrator.process(
        CommandRequest(text=text, context=_default_non_executable_context(journal))
    )

    assert response.status == expected_status
    assert executor.calls == []
    assert action_started_calls == []
    assert _event_types(journal.events) == expected_events
    _assert_non_executable_event_shape(journal.events)
    reasons = " ".join(str(event.payload.get("reason", "")) for event in journal.events)
    policy_rules = " ".join(str(event.payload.get("policy_rule", "")) for event in journal.events)
    assert "generic click quarantine" in reasons
    assert "target resolution" in reasons
    assert "generic_click.quarantined" in policy_rules
    assert ProtocolEventType.APPROVAL_REQUIRED.value not in _event_types(journal.events)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("text", "params"),
    [
        ("click 10 20", {"x": 10, "y": 20}),
        ("click .primary", {"selector": ".primary"}),
    ],
)
async def test_coordinate_or_selector_click_approval_resolution_does_not_execute(
    monkeypatch: pytest.MonkeyPatch,
    text: str,
    params: dict,
) -> None:
    reset_sequence_for_testing()
    _quiet_runtime_emissions(monkeypatch)
    executor = SpyExecutor()
    journal = NonExecutableBoundaryJournal()
    action_started_calls = _spy_action_started(monkeypatch)
    orchestrator = build_orchestrator(intent_result("click", RiskLevel.LOW, params), executor=executor)
    orchestrator.guard = AllowGuard()

    response = await orchestrator.process(
        CommandRequest(text=text, context=_default_non_executable_context(journal))
    )

    manager = get_approval_manager()
    pending = manager.snapshot()["pending_approvals"][0]
    approved = manager.resolve_approval(pending["metadata"]["approval_id"], approved=True)

    assert response.status == CommandStatus.PENDING_APPROVAL
    assert approved.status == CommandStatus.BLOCKED
    assert approved.metadata["approval_resolution_status"] == "approval_granted"
    assert approved.metadata["completed_without_execution"] is True
    assert approved.metadata["mutation_performed"] is False
    assert executor.calls == []
    assert action_started_calls == []


@pytest.mark.asyncio
async def test_blocked_excessive_click_cannot_be_approved_into_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reset_sequence_for_testing()
    _quiet_runtime_emissions(monkeypatch)
    executor = SpyExecutor()
    journal = NonExecutableBoundaryJournal()
    action_started_calls = _spy_action_started(monkeypatch)
    orchestrator = build_orchestrator(intent_result("click", RiskLevel.LOW, {"count": 50}), executor=executor)
    orchestrator.guard = AllowGuard()

    response = await orchestrator.process(
        CommandRequest(text="click 50 times", context=_default_non_executable_context(journal))
    )

    manager = get_approval_manager()
    record = manager.get(response.trace_id)
    assert response.status == CommandStatus.BLOCKED
    assert record is not None
    assert record.status == CommandStatus.BLOCKED
    with pytest.raises(ValueError):
        manager.approve(record.command_id)
    with pytest.raises(KeyError):
        manager.resolve_approval("blocked-click", approved=True)
    assert executor.calls == []
    assert action_started_calls == []


@pytest.mark.asyncio
async def test_default_compound_unresolved_click_quarantines_before_partial_open(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reset_sequence_for_testing()
    _quiet_runtime_emissions(monkeypatch)
    executor = SpyExecutor()
    journal = NonExecutableBoundaryJournal()
    action_started_calls = _spy_action_started(monkeypatch)
    orchestrator = build_orchestrator(
        [
            intent_result("open_app", RiskLevel.LOW, {"app": "brave"}),
            intent_result("click", RiskLevel.LOW, {"target": "first result"}),
        ],
        executor=executor,
    )
    orchestrator.guard = AllowGuard()

    response = await orchestrator.process(
        CommandRequest(
            text="brave aç ve ilk sonuca tıkla",
            context=_default_non_executable_context(journal),
        )
    )

    assert response.status == CommandStatus.WAITING_FOR_CLARIFICATION
    assert executor.calls == []
    assert action_started_calls == []
    assert _event_types(journal.events) == [
        ProtocolEventType.COMMAND_CLASSIFIED.value,
        ProtocolEventType.CLARIFICATION_REQUESTED.value,
        ProtocolEventType.COMMAND_WAITING_FOR_CLARIFICATION.value,
    ]
    _assert_non_executable_event_shape(journal.events)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("intent_name", "params", "text"),
    [
        ("read_file", {"path": "README.md"}, "read README.md"),
        ("search_web", {"query": "aegis"}, "search web for aegis"),
    ],
)
async def test_default_non_click_ready_intents_still_reach_executor(
    monkeypatch: pytest.MonkeyPatch,
    intent_name: str,
    params: dict,
    text: str,
) -> None:
    reset_sequence_for_testing()
    _quiet_runtime_emissions(monkeypatch)
    executor = SpyExecutor()
    journal = NonExecutableBoundaryJournal()
    action_started_calls = _spy_action_started(monkeypatch)

    async def fail_append_non_executable_decision(*args, **kwargs):
        raise AssertionError("default generic click quarantine must not catch non-click intents")

    monkeypatch.setattr(
        orchestrator_module.ws_bridge,
        "append_non_executable_decision",
        fail_append_non_executable_decision,
    )
    orchestrator = build_orchestrator(intent_result(intent_name, RiskLevel.LOW, params), executor=executor)
    orchestrator.guard = AllowGuard()

    response = await orchestrator.process(
        CommandRequest(text=text, context=_default_non_executable_context(journal))
    )

    assert response.status == CommandStatus.EXECUTED
    assert len(executor.calls) == 1
    assert len(action_started_calls) == 1
    assert journal.events == []


@pytest.mark.asyncio
async def test_default_open_app_ready_path_still_reaches_executor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reset_sequence_for_testing()
    _quiet_runtime_emissions(monkeypatch)
    journal = NonExecutableBoundaryJournal()
    action_started_calls = _spy_action_started(monkeypatch)

    async def fail_append_non_executable_decision(*args, **kwargs):
        raise AssertionError("default generic click quarantine must not catch open_app")

    monkeypatch.setattr(
        orchestrator_module.ws_bridge,
        "append_non_executable_decision",
        fail_append_non_executable_decision,
    )
    orchestrator = build_orchestrator(
        intent_result("open_app", RiskLevel.LOW, {"app": "notepad"}),
        executor=VerifiedDesktopExecutor(),
    )
    orchestrator.guard = AllowGuard()

    response = await orchestrator.process(
        CommandRequest(text="open notepad", context=_default_non_executable_context(journal))
    )

    assert response.status == CommandStatus.EXECUTED
    assert response.actions[0].action == "open_app"
    assert len(action_started_calls) == 1
    assert journal.events == []


@pytest.mark.asyncio
async def test_non_executable_boundary_repeated_calls_use_unique_live_sequences(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reset_sequence_for_testing()
    _quiet_runtime_emissions(monkeypatch)
    journal = NonExecutableBoundaryJournal()
    action_started_calls = _spy_action_started(monkeypatch)

    for _ in range(2):
        orchestrator = build_orchestrator(intent_result("click", RiskLevel.LOW, {}), executor=SpyExecutor())
        orchestrator.guard = AllowGuard()
        response = await orchestrator.process(
            CommandRequest(text="click", context=_boundary_context(journal))
        )
        assert response.status == CommandStatus.WAITING_FOR_CLARIFICATION

    assert action_started_calls == []
    assert [event.sequence_num for event in journal.events] == [1, 2, 3, 4, 5, 6]
    assert len({event.sequence_num for event in journal.events}) == 6
    assert _event_types(journal.events[:3]) == [
        ProtocolEventType.COMMAND_CLASSIFIED.value,
        ProtocolEventType.CLARIFICATION_REQUESTED.value,
        ProtocolEventType.COMMAND_WAITING_FOR_CLARIFICATION.value,
    ]
    assert _event_types(journal.events[3:]) == [
        ProtocolEventType.COMMAND_CLASSIFIED.value,
        ProtocolEventType.CLARIFICATION_REQUESTED.value,
        ProtocolEventType.COMMAND_WAITING_FOR_CLARIFICATION.value,
    ]
    _assert_non_executable_event_shape(journal.events)


@pytest.mark.asyncio
async def test_low_risk_command_runs_without_approval() -> None:
    orchestrator = build_orchestrator(intent_result("read_file", RiskLevel.LOW, {"path": "README.md"}))

    response = await orchestrator.process(CommandRequest(text="read README.md"))

    assert response.status == CommandStatus.EXECUTED
    assert response.actions[0].status == ActionStatus.EXECUTED


@pytest.mark.asyncio
async def test_medium_risk_command_requests_approval_before_execution() -> None:
    orchestrator = build_orchestrator(intent_result("open_app", RiskLevel.MEDIUM, {"app": "notepad"}))

    response = await orchestrator.process(CommandRequest(text="open notepad"))

    assert response.status == CommandStatus.PENDING_APPROVAL
    assert response.actions == []
    assert get_runtime_authority().current_state().value == "IDLE"
    snapshot = get_approval_manager().snapshot()
    assert len(snapshot["pending_approvals"]) == 1


@pytest.mark.asyncio
async def test_approved_verified_medium_risk_command_resumes_and_executes() -> None:
    orchestrator = build_orchestrator(
        intent_result("open_app", RiskLevel.MEDIUM, {"app": "notepad"}),
        executor=VerifiedDesktopExecutor(),
    )
    manager = get_approval_manager()

    pending = await orchestrator.process(CommandRequest(text="open notepad"))
    command_id = manager.snapshot()["pending_approvals"][0]["command_id"]
    approved = manager.approve(command_id)

    response = await orchestrator.process(CommandRequest(
        text=approved.text,
        context={
            "command_id": command_id,
            "approval_granted": True,
            "cancellation_token": manager.token_for(command_id),
        },
    ))

    snapshot = manager.snapshot()
    assert pending.status == CommandStatus.PENDING_APPROVAL
    assert response.status == CommandStatus.EXECUTED
    assert response.actions[0].action == "open_app"
    assert response.actions[0].status == ActionStatus.EXECUTED
    assert snapshot["pending_approvals"] == []
    assert snapshot["active_command"] is None
    assert snapshot["records"][-1]["command_id"] == command_id
    assert snapshot["records"][-1]["status"] == CommandStatus.EXECUTED.value
    assert snapshot["records"][-1]["approved"] is True


@pytest.mark.asyncio
async def test_unverified_execution_evidence_fails_process_window_action() -> None:
    orchestrator = build_orchestrator(
        intent_result("open_app", RiskLevel.MEDIUM, {"app": "portal"}),
        executor=UnverifiedEvidenceExecutor(),
    )
    manager = get_approval_manager()

    await orchestrator.process(CommandRequest(text="open portal"))
    command_id = manager.snapshot()["pending_approvals"][0]["command_id"]
    approved = manager.approve(command_id)

    response = await orchestrator.process(CommandRequest(
        text=approved.text,
        context={
            "command_id": command_id,
            "approval_granted": True,
            "cancellation_token": manager.token_for(command_id),
        },
    ))

    snapshot = manager.snapshot()
    assert response.status == CommandStatus.FAILED
    assert response.actions[0].execution_evidence is not None
    assert response.actions[0].status == ActionStatus.FAILED
    assert response.actions[0].execution_evidence.verification_state == "failed"
    assert snapshot["records"][-1]["status"] == CommandStatus.FAILED.value
    assert snapshot["records"][-1]["verification_state"] == "unverified"


@pytest.mark.asyncio
async def test_critical_check_failure_fails_before_action_completed(monkeypatch) -> None:
    orchestrator = build_orchestrator(
        intent_result("focus_app", RiskLevel.MEDIUM, {"app": "portal"}),
        executor=CriticalCheckFailureExecutor(),
    )
    manager = get_approval_manager()
    completed_payloads: list[dict] = []
    failed_payloads: list[dict] = []

    async def fake_emit_action_completed(**kwargs):
        completed_payloads.append(kwargs)

    async def fake_emit_action_failed(**kwargs):
        failed_payloads.append(kwargs)

    monkeypatch.setattr(orchestrator_module.ws_bridge, "emit_action_completed", fake_emit_action_completed)
    monkeypatch.setattr(orchestrator_module.ws_bridge, "emit_action_failed", fake_emit_action_failed)

    await orchestrator.process(CommandRequest(text="focus portal"))
    command_id = manager.snapshot()["pending_approvals"][0]["command_id"]
    approved = manager.approve(command_id)

    response = await orchestrator.process(CommandRequest(
        text=approved.text,
        context={
            "command_id": command_id,
            "approval_granted": True,
            "cancellation_token": manager.token_for(command_id),
        },
    ))

    snapshot = manager.snapshot()
    assert response.status == CommandStatus.FAILED
    assert response.actions[0].execution_evidence is not None
    assert response.actions[0].status == ActionStatus.FAILED
    assert response.actions[0].execution_evidence.verification_state == "failed"
    assert completed_payloads == []
    assert failed_payloads
    assert "Critical verifier check failed" in failed_payloads[0]["error"]
    assert snapshot["records"][-1]["status"] == CommandStatus.FAILED.value
    assert snapshot["records"][-1]["verification_state"] == "unverified"


@pytest.mark.asyncio
async def test_action_completed_protocol_event_receives_execution_evidence(monkeypatch) -> None:
    orchestrator = build_orchestrator(
        intent_result("open_app", RiskLevel.MEDIUM, {"app": "portal"}),
        executor=VerifiedDesktopExecutor(),
    )
    manager = get_approval_manager()
    completed_payloads: list[dict] = []

    async def fake_emit_action_completed(**kwargs):
        completed_payloads.append(kwargs)

    monkeypatch.setattr(orchestrator_module.ws_bridge, "emit_action_completed", fake_emit_action_completed)

    await orchestrator.process(CommandRequest(text="open portal"))
    command_id = manager.snapshot()["pending_approvals"][0]["command_id"]
    approved = manager.approve(command_id)

    response = await orchestrator.process(CommandRequest(
        text=approved.text,
        context={
            "command_id": command_id,
            "approval_granted": True,
            "cancellation_token": manager.token_for(command_id),
        },
    ))

    assert response.status == CommandStatus.EXECUTED
    assert completed_payloads
    assert completed_payloads[0]["execution_evidence"].verification_state == "verified"
    assert completed_payloads[0]["execution_evidence"].target == "portal"


@pytest.mark.asyncio
async def test_action_failed_protocol_event_receives_execution_evidence(monkeypatch) -> None:
    orchestrator = build_orchestrator(
        intent_result("open_app", RiskLevel.MEDIUM, {"app": "steam"}),
        executor=FailedEvidenceExecutor(),
    )
    manager = get_approval_manager()
    failed_payloads: list[dict] = []

    async def fake_emit_action_failed(**kwargs):
        failed_payloads.append(kwargs)

    monkeypatch.setattr(orchestrator_module.ws_bridge, "emit_action_failed", fake_emit_action_failed)

    await orchestrator.process(CommandRequest(text="open steam"))
    command_id = manager.snapshot()["pending_approvals"][0]["command_id"]
    approved = manager.approve(command_id)

    response = await orchestrator.process(CommandRequest(
        text=approved.text,
        context={
            "command_id": command_id,
            "approval_granted": True,
            "cancellation_token": manager.token_for(command_id),
        },
    ))

    assert response.status == CommandStatus.FAILED
    assert failed_payloads
    assert failed_payloads[0]["execution_evidence"].verification_state == "failed"
    assert failed_payloads[0]["execution_evidence"].process_alive is False


@pytest.mark.asyncio
async def test_approved_focus_app_command_resumes_and_executes() -> None:
    orchestrator = build_orchestrator(
        intent_result("focus_app", RiskLevel.MEDIUM, {"app": "notepad"}),
        executor=VerifiedDesktopExecutor(),
    )
    manager = get_approval_manager()

    pending = await orchestrator.process(CommandRequest(text="focus notepad"))
    command_id = manager.snapshot()["pending_approvals"][0]["command_id"]
    approved = manager.approve(command_id)

    response = await orchestrator.process(CommandRequest(
        text=approved.text,
        context={
            "command_id": command_id,
            "approval_granted": True,
            "cancellation_token": manager.token_for(command_id),
        },
    ))

    assert pending.status == CommandStatus.PENDING_APPROVAL
    assert response.status == CommandStatus.EXECUTED
    assert response.actions[0].action == "focus_app"
    assert manager.snapshot()["records"][-1]["verification_state"] == "verified"


@pytest.mark.asyncio
async def test_proof_backed_side_effect_completes_verified() -> None:
    orchestrator = build_orchestrator(
        intent_result("open_url", RiskLevel.MEDIUM, {"url": "https://example.com"}),
        executor=ProofBackedSideEffectExecutor("browser_evidence"),
    )
    manager = get_approval_manager()

    pending = await orchestrator.process(CommandRequest(text="open https://example.com"))
    command_id = manager.snapshot()["pending_approvals"][0]["command_id"]
    approved = manager.approve(command_id)

    response = await orchestrator.process(CommandRequest(
        text=approved.text,
        context={
            "command_id": command_id,
            "approval_granted": True,
            "cancellation_token": manager.token_for(command_id),
        },
    ))

    snapshot = manager.snapshot()
    assert pending.status == CommandStatus.PENDING_APPROVAL
    assert response.status == CommandStatus.EXECUTED
    assert response.actions[0].proof["browser_evidence"]["tool"] == "open_url"
    assert snapshot["records"][-1]["verification_state"] == "verified"


@pytest.mark.asyncio
async def test_missing_side_effect_proof_keeps_completed_command_unverified() -> None:
    orchestrator = build_orchestrator(
        intent_result("open_url", RiskLevel.MEDIUM, {"url": "https://example.com"})
    )
    manager = get_approval_manager()

    pending = await orchestrator.process(CommandRequest(text="open https://example.com"))
    command_id = manager.snapshot()["pending_approvals"][0]["command_id"]
    approved = manager.approve(command_id)

    response = await orchestrator.process(CommandRequest(
        text=approved.text,
        context={
            "command_id": command_id,
            "approval_granted": True,
            "cancellation_token": manager.token_for(command_id),
        },
    ))

    snapshot = manager.snapshot()
    assert pending.status == CommandStatus.PENDING_APPROVAL
    assert response.status == CommandStatus.EXECUTED
    assert response.actions[0].proof == {}
    assert snapshot["records"][-1]["verification_state"] == "unverified"


@pytest.mark.asyncio
async def test_approved_close_app_command_resumes_and_executes() -> None:
    orchestrator = build_orchestrator(
        intent_result("close_app", RiskLevel.MEDIUM, {"app": "notepad"}),
        executor=VerifiedDesktopExecutor(),
    )
    manager = get_approval_manager()

    pending = await orchestrator.process(CommandRequest(text="close notepad"))
    command_id = manager.snapshot()["pending_approvals"][0]["command_id"]
    approved = manager.approve(command_id)

    response = await orchestrator.process(CommandRequest(
        text=approved.text,
        context={
            "command_id": command_id,
            "approval_granted": True,
            "cancellation_token": manager.token_for(command_id),
        },
    ))

    assert pending.status == CommandStatus.PENDING_APPROVAL
    assert response.status == CommandStatus.EXECUTED
    assert response.actions[0].action == "close_app"


@pytest.mark.asyncio
async def test_approved_write_file_command_resumes_and_executes() -> None:
    orchestrator = build_orchestrator(intent_result("write_file", RiskLevel.MEDIUM, {"path": "x", "content": "y"}))
    manager = get_approval_manager()

    pending = await orchestrator.process(CommandRequest(text="write y to x"))
    command_id = manager.snapshot()["pending_approvals"][0]["command_id"]
    approved = manager.approve(command_id)

    response = await orchestrator.process(CommandRequest(
        text=approved.text,
        context={
            "command_id": command_id,
            "approval_granted": True,
            "cancellation_token": manager.token_for(command_id),
        },
    ))

    assert pending.status == CommandStatus.PENDING_APPROVAL
    assert response.status == CommandStatus.EXECUTED
    assert response.actions[0].action == "write_file"


@pytest.mark.asyncio
async def test_approval_granted_does_not_bypass_default_generic_click_quarantine(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reset_sequence_for_testing()
    _quiet_runtime_emissions(monkeypatch)
    executor = SpyExecutor()
    journal = NonExecutableBoundaryJournal()
    action_started_calls = _spy_action_started(monkeypatch)
    orchestrator = build_orchestrator(intent_result("click", RiskLevel.MEDIUM, {"x": 10, "y": 20}), executor=executor)
    orchestrator.guard = AllowGuard()

    response = await orchestrator.process(CommandRequest(
        text="click 10 20",
        context={
            "approval_granted": True,
            **_default_non_executable_context(journal),
        },
    ))

    assert response.status == CommandStatus.PENDING_APPROVAL
    assert executor.calls == []
    assert action_started_calls == []
    assert _event_types(journal.events) == [
        ProtocolEventType.COMMAND_CLASSIFIED.value,
        ProtocolEventType.APPROVAL_REQUESTED.value,
        ProtocolEventType.COMMAND_WAITING_FOR_APPROVAL.value,
    ]
    _assert_non_executable_event_shape(journal.events)


@pytest.mark.asyncio
async def test_approved_unverified_side_effect_still_blocks_at_execution_gate() -> None:
    orchestrator = build_orchestrator(intent_result("open_app", RiskLevel.MEDIUM, {"app": "notepad"}))
    manager = get_approval_manager()
    orchestrator_module.DISPATCHABLE_TOOLS.discard("open_app")

    try:
        pending = await orchestrator.process(CommandRequest(text="open notepad"))
        command_id = manager.snapshot()["pending_approvals"][0]["command_id"]
        approved = manager.approve(command_id)

        response = await orchestrator.process(CommandRequest(
            text=approved.text,
            context={
                "command_id": command_id,
                "approval_granted": True,
                "cancellation_token": manager.token_for(command_id),
            },
        ))
    finally:
        orchestrator_module.DISPATCHABLE_TOOLS.add("open_app")

    snapshot = manager.snapshot()
    assert pending.status == CommandStatus.PENDING_APPROVAL
    assert response.status == CommandStatus.BLOCKED
    assert response.actions[0].action == "verification_gate"
    assert "Unverified execution gate blocked" in response.actions[0].output
    assert snapshot["pending_approvals"] == []
    assert snapshot["records"][-1]["status"] == CommandStatus.BLOCKED.value


@pytest.mark.asyncio
async def test_low_risk_git_status_runs_without_approval() -> None:
    orchestrator = build_orchestrator(intent_result("git_action", RiskLevel.LOW, {"git_cmd": "status"}))

    response = await orchestrator.process(CommandRequest(text="git status"))

    assert response.status == CommandStatus.EXECUTED
    assert response.actions[0].action == "git_action"


@pytest.mark.asyncio
async def test_low_risk_file_inspection_runs_without_approval() -> None:
    orchestrator = build_orchestrator(intent_result("list_directory", RiskLevel.LOW, {"path": "scratch"}))

    response = await orchestrator.process(CommandRequest(text="list scratch"))

    assert response.status == CommandStatus.EXECUTED
    assert response.actions[0].action == "list_directory"


@pytest.mark.asyncio
async def test_medium_risk_create_file_requests_approval() -> None:
    orchestrator = build_orchestrator(intent_result(
        "create_file",
        RiskLevel.MEDIUM,
        {"path": "scratch/new.txt", "content": "hello"},
    ))

    response = await orchestrator.process(CommandRequest(text="create file scratch/new.txt"))

    assert response.status == CommandStatus.PENDING_APPROVAL
    assert response.actions == []
    assert get_approval_manager().snapshot()["pending_approvals"][0]["risk_level"] == RiskLevel.MEDIUM.value


@pytest.mark.asyncio
async def test_critical_delete_file_blocks() -> None:
    orchestrator = build_orchestrator(intent_result("delete_file", RiskLevel.CRITICAL, {"path": "scratch/old.txt"}))

    response = await orchestrator.process(CommandRequest(text="delete scratch/old.txt"))

    assert response.status == CommandStatus.BLOCKED
    assert response.actions[0].action == "delete_file"


@pytest.mark.asyncio
async def test_destructive_shell_command_blocks() -> None:
    orchestrator = build_orchestrator(intent_result("run_command", RiskLevel.CRITICAL, {"command": "del C:\\temp\\x.txt"}))

    response = await orchestrator.process(CommandRequest(text="run command del C:\\temp\\x.txt"))

    assert response.status == CommandStatus.BLOCKED
    assert response.actions[0].action == "run_command"
    assert "Destructive shell command" in response.actions[0].output


@pytest.mark.asyncio
async def test_mutating_git_action_blocks() -> None:
    orchestrator = build_orchestrator(intent_result("git_action", RiskLevel.MEDIUM, {"git_cmd": "push"}))

    response = await orchestrator.process(CommandRequest(text="git push"))

    assert response.status == CommandStatus.BLOCKED
    assert response.actions[0].action == "git_action"
    assert "Git action" in response.actions[0].output


@pytest.mark.asyncio
async def test_forbidden_write_file_path_blocks_before_execution() -> None:
    orchestrator = build_orchestrator(intent_result(
        "write_file",
        RiskLevel.CRITICAL,
        {"path": "c:\\windows\\temp\\aegis-test.txt", "content": "nope"},
    ))

    response = await orchestrator.process(CommandRequest(text="write nope to c:\\windows\\temp\\aegis-test.txt"))

    assert response.status == CommandStatus.BLOCKED
    assert response.actions[0].action == "write_file"


@pytest.mark.asyncio
async def test_approved_open_url_command_resumes_and_executes() -> None:
    orchestrator = build_orchestrator(intent_result("open_url", RiskLevel.MEDIUM, {"url": "https://example.com"}))
    manager = get_approval_manager()

    pending = await orchestrator.process(CommandRequest(text="open https://example.com"))
    command_id = manager.snapshot()["pending_approvals"][0]["command_id"]
    approved = manager.approve(command_id)

    response = await orchestrator.process(CommandRequest(
        text=approved.text,
        context={
            "command_id": command_id,
            "approval_granted": True,
            "cancellation_token": manager.token_for(command_id),
        },
    ))

    snapshot = manager.snapshot()
    assert pending.status == CommandStatus.PENDING_APPROVAL
    assert response.status == CommandStatus.EXECUTED
    assert response.actions[0].action == "open_url"
    assert snapshot["pending_approvals"] == []
    assert snapshot["records"][-1]["status"] == CommandStatus.EXECUTED.value


@pytest.mark.asyncio
async def test_approved_type_command_resumes_and_executes() -> None:
    orchestrator = build_orchestrator(intent_result("type", RiskLevel.MEDIUM, {"text": "hello"}))
    manager = get_approval_manager()

    pending = await orchestrator.process(CommandRequest(text="type hello"))
    command_id = manager.snapshot()["pending_approvals"][0]["command_id"]
    approved = manager.approve(command_id)

    response = await orchestrator.process(CommandRequest(
        text=approved.text,
        context={
            "command_id": command_id,
            "approval_granted": True,
            "cancellation_token": manager.token_for(command_id),
        },
    ))

    snapshot = manager.snapshot()
    assert pending.status == CommandStatus.PENDING_APPROVAL
    assert response.status == CommandStatus.EXECUTED
    assert response.actions[0].action == "type"
    assert snapshot["pending_approvals"] == []
    assert snapshot["records"][-1]["status"] == CommandStatus.EXECUTED.value


@pytest.mark.asyncio
async def test_critical_risk_command_blocks() -> None:
    orchestrator = build_orchestrator(intent_result("write_file", RiskLevel.CRITICAL, {"path": "x", "content": "y"}))

    response = await orchestrator.process(CommandRequest(text="critical write"))

    assert response.status == CommandStatus.BLOCKED
    assert response.actions[0].status == ActionStatus.BLOCKED
    assert "Critical-risk" in response.actions[0].output


@pytest.mark.asyncio
async def test_cancel_active_command_is_observed() -> None:
    command_id = "11111111-1111-4111-8111-111111111111"
    manager = get_approval_manager()
    manager.create_received("read README.md", command_id=command_id)
    token = manager.token_for(command_id)
    orchestrator = build_orchestrator(
        intent_result("read_file", RiskLevel.LOW, {"path": "README.md"}),
        executor=WaitingExecutor(),
    )

    task = asyncio.create_task(orchestrator.process(CommandRequest(
        text="read README.md",
        context={"command_id": command_id, "cancellation_token": token},
    )))

    for _ in range(200):
        active = manager.snapshot()["active_command"]
        if active:
            break
        await asyncio.sleep(0.01)
    manager.cancel(command_id, reason="test cancellation")

    response = await task

    assert response.status == CommandStatus.CANCELLED
    assert response.actions[0].status == ActionStatus.CANCELLED
    snapshot = manager.snapshot()
    assert snapshot["active_command"] is None
    assert snapshot["records"][-1]["status"] == CommandStatus.CANCELLED.value
