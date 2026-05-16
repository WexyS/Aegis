from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from aegis.core.commands import ApprovalManager, get_approval_manager, restore_approval_manager_from_journal
from aegis.core.constants import ActionStatus, CommandStatus, IntentSource, RiskLevel
from aegis.core.context import ExecutionContext
from aegis.core.runtime_authority import get_runtime_authority
from aegis.core.schemas import ActionResult, CommandRequest, ExecutionEvidence, IntentResult, ReliabilityMetrics
from aegis.orchestrator import orchestrator as orchestrator_module
from aegis.orchestrator.orchestrator import Orchestrator


class FakeRouter:
    async def route(self, request: CommandRequest) -> SimpleNamespace:
        return SimpleNamespace(planner_model=None)


class FakeParser:
    def __init__(self, intent: IntentResult) -> None:
        self.intent = intent

    async def parse(self, text: str, model: str | None = None) -> list[IntentResult]:
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


def build_orchestrator(intent: IntentResult, executor=None) -> Orchestrator:
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


@pytest.mark.asyncio
async def test_low_risk_command_runs_without_approval() -> None:
    orchestrator = build_orchestrator(intent_result("read_file", RiskLevel.LOW, {"path": "README.md"}))

    response = await orchestrator.process(CommandRequest(text="read README.md"))

    assert response.status == CommandStatus.EXECUTED
    assert response.actions[0].status == ActionStatus.EXECUTED


@pytest.mark.asyncio
async def test_medium_risk_command_requests_approval_before_execution() -> None:
    orchestrator = build_orchestrator(intent_result("click", RiskLevel.MEDIUM, {"count": 1}))

    response = await orchestrator.process(CommandRequest(text="click"))

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
        intent_result("click", RiskLevel.MEDIUM, {"count": 1}),
        executor=ProofBackedSideEffectExecutor("browser_evidence"),
    )
    manager = get_approval_manager()

    pending = await orchestrator.process(CommandRequest(text="click"))
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
    assert response.actions[0].proof["browser_evidence"]["tool"] == "click"
    assert snapshot["records"][-1]["verification_state"] == "verified"


@pytest.mark.asyncio
async def test_missing_side_effect_proof_keeps_completed_command_unverified() -> None:
    orchestrator = build_orchestrator(intent_result("click", RiskLevel.MEDIUM, {"count": 1}))
    manager = get_approval_manager()

    pending = await orchestrator.process(CommandRequest(text="click"))
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
async def test_approved_click_command_resumes_and_executes() -> None:
    orchestrator = build_orchestrator(intent_result("click", RiskLevel.MEDIUM, {"count": 1}))
    manager = get_approval_manager()

    pending = await orchestrator.process(CommandRequest(text="click"))
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
    assert response.actions[0].action == "click"
    assert snapshot["pending_approvals"] == []
    assert snapshot["records"][-1]["status"] == CommandStatus.EXECUTED.value


@pytest.mark.asyncio
async def test_approved_unverified_side_effect_still_blocks_at_execution_gate() -> None:
    orchestrator = build_orchestrator(intent_result("open_app", RiskLevel.MEDIUM, {"app": "notepad"}))
    manager = get_approval_manager()
    orchestrator_module.VERIFIED_TOOLS.discard("open_app")

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
        orchestrator_module.VERIFIED_TOOLS.add("open_app")

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
