from __future__ import annotations

import asyncio
import hashlib
from types import SimpleNamespace
from typing import Any

import pytest

from aegis.api import ws_bridge
from aegis.core.action_timeline import project_action_timeline
from aegis.core.commands import get_approval_manager
from aegis.core.constants import ActionStatus, CommandStatus, RiskLevel
from aegis.core.context import ExecutionContext
from aegis.core.protocol import (
    GENESIS_HASH,
    ProtocolEventType,
    finalize_event,
    reset_sequence_for_testing,
)
from aegis.core.runtime_authority import RuntimeAuthority
from aegis.core.schemas import (
    ActionResult,
    CommandRequest,
    ExecutionEvidence,
    IntentResult,
    ReliabilityMetrics,
)
from aegis.intent.parser import IntentParser
from aegis.orchestrator.orchestrator import Orchestrator


class InMemoryRuntimeJournal:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []
        self._last_hash = GENESIS_HASH

    def append(self, event):
        finalize_event(event, self._last_hash)
        data = event.to_dict()
        self.events.append(data)
        self._last_hash = event.event_hash or self._last_hash
        return event

    def recent_events(self, limit: int | None = None) -> list[dict[str, Any]]:
        if limit is None:
            return list(self.events)
        return list(self.events)[-max(int(limit), 0) :]

    def events_after(self, sequence_num: int) -> list[dict[str, Any]]:
        return [event for event in self.events if int(event.get("sequence_num", 0)) > sequence_num]

    def snapshot(self) -> dict[str, Any]:
        last_event = self.events[-1] if self.events else None
        return {
            "event_count": len(self.events),
            "last_sequence_num": last_event.get("sequence_num", 0) if last_event else 0,
            "last_event_hash": self._last_hash,
            "journal_path": "in-memory",
            "integrity_status": "hash-chain",
            "integrity_checked_events": len(self.events),
        }


class FakeRouter:
    async def route(self, request: CommandRequest) -> SimpleNamespace:
        return SimpleNamespace(planner_model=None)


class PassthroughPlanner:
    def plan(self, intents: list[IntentResult]) -> list[IntentResult]:
        return intents


class PassingVerifier:
    async def verify_result(self, result: ActionResult) -> float:
        return 1.0


class NoopTraceJournal:
    def record(self, trace_id: str, goal: str, actions: list[ActionResult], summary: dict[str, Any]) -> None:
        return None


class NoopEventLogger:
    def log(self, *args, **kwargs) -> None:
        return None


class FakeExecutor:
    async def execute(
        self,
        intent_result: IntentResult,
        ctx: ExecutionContext,
        cancellation_token=None,
    ) -> ActionResult:
        if intent_result.intent == "open_app":
            return _verified_open_app_result(intent_result)
        if intent_result.intent == "type":
            return _unverified_type_result(intent_result)
        if intent_result.intent == "search_web":
            return _approval_required_browser_result(intent_result)
        raise AssertionError(f"Unexpected intent in runtime truth smoke: {intent_result.intent}")


@pytest.fixture
def runtime_truth_harness(monkeypatch):
    reset_sequence_for_testing()
    get_approval_manager().reset_for_tests()
    journal = InMemoryRuntimeJournal()
    authority = RuntimeAuthority(session_id="session-runtime-truth", queue_capacity=16)
    emitted: list[tuple[str, dict[str, Any], str | None]] = []

    async def fake_emit(event_name: str, payload: dict[str, Any], to: str | None = None):
        emitted.append((event_name, payload, to))

    monkeypatch.setattr(ws_bridge, "_session_id", "session-runtime-truth")
    monkeypatch.setattr(ws_bridge, "_connected_clients", set())
    monkeypatch.setattr(ws_bridge, "_journal_emit_lock", asyncio.Lock())
    monkeypatch.setattr(ws_bridge, "get_runtime_journal", lambda: journal)
    monkeypatch.setattr(
        ws_bridge,
        "get_runtime_authority",
        lambda session_id="session-runtime-truth", queue_capacity=0: authority,
    )
    monkeypatch.setattr(ws_bridge.sio, "emit", fake_emit)

    yield SimpleNamespace(journal=journal, authority=authority, emitted=emitted)

    get_approval_manager().reset_for_tests()
    reset_sequence_for_testing()


def _build_orchestrator() -> Orchestrator:
    orchestrator = Orchestrator()
    orchestrator.router = FakeRouter()
    orchestrator.parser = IntentParser()
    orchestrator.planner = PassthroughPlanner()
    orchestrator.verifier = PassingVerifier()
    orchestrator.executor = FakeExecutor()
    orchestrator.journal = NoopTraceJournal()
    orchestrator.event_logger = NoopEventLogger()
    orchestrator.state_manager = SimpleNamespace(get_state=lambda: SimpleNamespace(active_app="notepad"))
    return orchestrator


def _execution_result(
    intent: IntentResult,
    *,
    evidence: ExecutionEvidence,
    success: bool,
    status: ActionStatus | None = None,
    output: str = "ok",
) -> ActionResult:
    proof = {"execution_evidence": evidence.model_dump()}
    return ActionResult(
        action=intent.intent,
        params=dict(intent.params),
        status=status or (ActionStatus.EXECUTED if success else ActionStatus.FAILED),
        success=success,
        output=output,
        proof=proof,
        execution_evidence=evidence,
        metrics=ReliabilityMetrics(determinism_score=1.0),
    )


def _passed_check(name: str) -> dict[str, Any]:
    return {
        "check_name": name,
        "expected": "present and passed",
        "observed": "ok",
        "passed": True,
        "reason": "ok",
    }


def _verified_open_app_result(intent: IntentResult) -> ActionResult:
    app = str(intent.params.get("app") or "app")
    evidence = ExecutionEvidence(
        action="open_app",
        target=app,
        target_type="application",
        method="process_window_verifier",
        verifier="process-window-verifier/2",
        verification_state="verified",
        verification_reason="target process and window were observed",
        process_name=str(intent.params.get("_process_name") or f"{app}.exe"),
        pids=[4242],
        process_alive=True,
        window={"title": app, "hwnd": 1001, "pid": 4242},
        verification_checks=[
            _passed_check("process_name_known"),
            _passed_check("single_matching_window"),
            _passed_check("process_alive"),
            _passed_check("window_manifested"),
            _passed_check("window_pid_matches_target_process"),
        ],
    )
    return _execution_result(intent, evidence=evidence, success=True, output="verified open_app")


def _unverified_type_result(intent: IntentResult) -> ActionResult:
    evidence = ExecutionEvidence(
        action="type",
        target="focused_input",
        target_type="focused_input",
        method="focus_stability_gate",
        verifier="type-focus-gate/1",
        verification_state="unverified",
        verification_reason="focus changed unexpectedly during type action",
        expected={"focus_stable": True, "required_focus": intent.params.get("_require_focus")},
        observed={"focus_stable": False},
        verification_checks=[
            {
                "check_name": "focus_did_not_change_unexpectedly",
                "expected": True,
                "observed": False,
                "passed": False,
                "reason": "Focus changed during type dispatch.",
            }
        ],
    )
    return _execution_result(
        intent,
        evidence=evidence,
        status=ActionStatus.EXECUTED,
        success=False,
        output="type evidence unverified",
    )


def _approval_required_browser_result(intent: IntentResult) -> ActionResult:
    query = str(intent.params.get("query") or "")
    evidence = ExecutionEvidence(
        action="search_web",
        target=f"https://www.google.com/search?q={query.replace(' ', '+')}",
        target_type="browser",
        method="browser_url_gate",
        verifier="browser-url-gate/1",
        verification_state="approval_required",
        verification_reason="browser challenge detected",
        expected={"bot_challenge_detected": False, "query": query},
        observed={"bot_challenge_detected": True, "query": query},
        verification_checks=[
            {
                "check_name": "browser_challenge_absent",
                "expected": False,
                "observed": True,
                "passed": False,
                "reason": "Bot/CAPTCHA challenge blocks verified browser evidence.",
            }
        ],
    )
    return _execution_result(
        intent,
        evidence=evidence,
        status=ActionStatus.EXECUTED,
        success=False,
        output="browser challenge detected",
    )


async def _run_approved_command(
    orchestrator: Orchestrator,
    text: str,
    command_id: str,
) -> tuple[Any, list[IntentResult]]:
    parsed = await orchestrator.parser.parse(text)
    response = await orchestrator.process(CommandRequest(
        text=text,
        context={"command_id": command_id, "approval_granted": True},
    ))
    return response, parsed


def _sequence_numbers(events: list[dict[str, Any]]) -> list[int]:
    return [int(event["sequence_num"]) for event in events]


def _action_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    action_types = {
        ProtocolEventType.ACTION_STARTED.value,
        ProtocolEventType.ACTION_COMPLETED.value,
        ProtocolEventType.ACTION_FAILED.value,
        ProtocolEventType.VERIFICATION_PASSED.value,
        ProtocolEventType.VERIFICATION_FAILED.value,
    }
    return [event for event in events if event.get("type") in action_types]


def _terminal_action_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    terminal_types = {
        ProtocolEventType.ACTION_COMPLETED.value,
        ProtocolEventType.ACTION_FAILED.value,
    }
    return [event for event in events if event.get("type") in terminal_types]


def _assert_terminal_event_evidence_matches_results(response, events: list[dict[str, Any]]) -> None:
    terminal_events = _terminal_action_events(events)
    assert len(terminal_events) == len(response.actions)
    for action, event in zip(response.actions, terminal_events):
        assert action.execution_evidence is not None
        assert action.proof["execution_evidence"] == action.execution_evidence.model_dump()
        assert event["payload"]["execution_evidence"] == action.execution_evidence.model_dump()


@pytest.mark.asyncio
async def test_deterministic_open_type_flow_replays_to_journal_snapshot_and_timeline(runtime_truth_harness) -> None:
    orchestrator = _build_orchestrator()

    response, parsed = await _run_approved_command(
        orchestrator,
        "notepad açıp merhaba yaz",
        "cmd-runtime-open-type",
    )

    assert [intent.intent for intent in parsed] == ["open_app", "type"]
    assert parsed[1].params["_require_focus"] == "notepad"
    assert [action.action for action in response.actions] == ["open_app", "type"]
    assert response.status == CommandStatus.FAILED

    events = runtime_truth_harness.journal.recent_events()
    assert _sequence_numbers(events) == sorted(_sequence_numbers(events))
    action_events = _action_events(events)
    assert [event["payload"].get("tool") for event in action_events if event["type"] == "ACTION_STARTED"] == [
        "open_app",
        "type",
    ]

    timeline = project_action_timeline(events, session_id="session-runtime-truth")
    assert [item["tool"] for item in timeline] == ["open_app", "type"]
    assert [item["status"] for item in timeline] == ["success", "error"]
    assert timeline[1]["execution_evidence"]["verification_state"] == "unverified"
    assert timeline[1]["execution_evidence"]["verification_reason"]
    _assert_terminal_event_evidence_matches_results(response, events)

    _, runtime_snapshot = ws_bridge._build_runtime_snapshot(runtime_truth_harness.journal)
    latest_record = runtime_snapshot["commands"]["records"][-1]
    assert latest_record["status"] == CommandStatus.FAILED.value
    assert latest_record["verification_state"] == "unverified"
    assert runtime_snapshot["active_command"] is None
    assert runtime_snapshot["action_timeline"] == timeline
    assert runtime_snapshot["last_event_sequence"] == runtime_truth_harness.journal.snapshot()["last_sequence_num"]


@pytest.mark.asyncio
async def test_deterministic_open_search_flow_preserves_browser_context_without_verified_challenge(
    runtime_truth_harness,
) -> None:
    orchestrator = _build_orchestrator()

    response, parsed = await _run_approved_command(
        orchestrator,
        "brave açıp python nedir ara",
        "cmd-runtime-open-search",
    )

    assert [intent.intent for intent in parsed] == ["search_web"]
    assert parsed[0].params["query"] == "python nedir"
    assert parsed[0].params["browser"] == "brave"
    assert parsed[0].params["preferred_browser"] == "brave"
    assert parsed[0].metadata["route_kind"] == "browser_search"
    assert [action.action for action in response.actions] == ["search_web"]
    assert response.actions[0].params["browser"] == "brave"
    assert response.status == CommandStatus.FAILED

    timeline = project_action_timeline(runtime_truth_harness.journal.recent_events(), session_id="session-runtime-truth")
    assert [item["tool"] for item in timeline] == ["search_web"]
    assert timeline[0]["status"] == "approval_required"
    assert timeline[0]["execution_evidence"]["verification_state"] == "approval_required"
    assert timeline[0]["execution_evidence"]["observed"]["bot_challenge_detected"] is True
    _assert_terminal_event_evidence_matches_results(response, runtime_truth_harness.journal.recent_events())

    _, runtime_snapshot = ws_bridge._build_runtime_snapshot(runtime_truth_harness.journal)
    latest_record = runtime_snapshot["commands"]["records"][-1]
    assert latest_record["status"] == CommandStatus.FAILED.value
    assert latest_record["verification_state"] == "unverified"
    assert runtime_snapshot["action_timeline"] == timeline


def _evidence_result(
    *,
    action: str,
    evidence: ExecutionEvidence,
    success: bool,
) -> ActionResult:
    return ActionResult(
        action=action,
        params={},
        status=ActionStatus.EXECUTED if success else ActionStatus.FAILED,
        success=success,
        output="ok" if success else evidence.verification_reason or "unverified",
        proof={"execution_evidence": evidence.model_dump()},
        execution_evidence=evidence,
        metrics=ReliabilityMetrics(determinism_score=1.0),
    )


def _events_for_result(action_id: str, result: ActionResult) -> list[dict[str, Any]]:
    started = ws_bridge.create_event(
        ProtocolEventType.ACTION_STARTED,
        {"action_id": action_id, "tool": result.action, "target": result.execution_evidence.target},
        session_id="session-runtime-truth",
    ).to_dict()
    event_type = ProtocolEventType.ACTION_COMPLETED if result.success else ProtocolEventType.ACTION_FAILED
    payload = {
        "action_id": action_id,
        "success": result.success,
        "latency_ms": result.metrics.execution_time_ms,
        "execution_evidence": result.execution_evidence.model_dump(),
    }
    if not result.success:
        payload["error"] = result.output
    terminal = ws_bridge.create_event(
        event_type,
        payload,
        session_id="session-runtime-truth",
    ).to_dict()
    verification = ws_bridge.create_event(
        ProtocolEventType.VERIFICATION_PASSED
        if result.execution_evidence.verification_state == "verified"
        else ProtocolEventType.VERIFICATION_FAILED,
        {
            "action_id": action_id,
            "passed": result.execution_evidence.verification_state == "verified",
            "verification_state": result.execution_evidence.verification_state,
            "execution_evidence": result.execution_evidence.model_dump(),
        },
        session_id="session-runtime-truth",
    ).to_dict()
    return [started, terminal, verification]


def test_file_and_browser_evidence_projection_does_not_invent_verified_success() -> None:
    requested_hash = hashlib.sha256(b"hello").hexdigest()
    stale_hash = hashlib.sha256(b"stale").hexdigest()
    verified_write = _evidence_result(
        action="write_file",
        evidence=ExecutionEvidence(
            action="write_file",
            target="scratch/a.txt",
            target_type="file",
            method="write-file-gate",
            verifier="file-write-gate/1",
            verification_state="verified",
            verification_reason="after hash matches requested content",
            expected={"content_sha256": requested_hash},
            observed={"after_sha256": requested_hash},
            verification_checks=[_passed_check("write_after_hash_matches_requested_content")],
        ),
        success=True,
    )
    unverified_write = _evidence_result(
        action="write_file",
        evidence=ExecutionEvidence(
            action="write_file",
            target="scratch/a.txt",
            target_type="file",
            method="write-file-gate",
            verifier="file-write-gate/1",
            verification_state="unverified",
            verification_reason="after hash differs from requested content",
            expected={"content_sha256": requested_hash},
            observed={"after_sha256": stale_hash},
            verification_checks=[
                {
                    "check_name": "write_after_hash_matches_requested_content",
                    "expected": requested_hash,
                    "observed": stale_hash,
                    "passed": False,
                    "reason": "After hash must match requested content.",
                }
            ],
        ),
        success=False,
    )
    verified_read = _evidence_result(
        action="read_file",
        evidence=ExecutionEvidence(
            action="read_file",
            target="README.md",
            target_type="file",
            method="read-file-gate",
            verifier="file-read-gate/1",
            verification_state="verified",
            verification_reason="disk hash matches output hash",
            expected={"disk_sha256": requested_hash},
            observed={"output_sha256": requested_hash},
            verification_checks=[_passed_check("read_content_hash_matches_disk")],
        ),
        success=True,
    )
    failed_read = _evidence_result(
        action="read_file",
        evidence=ExecutionEvidence(
            action="read_file",
            target="missing.txt",
            target_type="file",
            method="read-file-gate",
            verifier="file-read-gate/1",
            verification_state="unverified",
            verification_reason="source file missing",
            expected={"file_exists": True},
            observed={"file_exists": False},
            verification_checks=[
                {
                    "check_name": "read_file_exists",
                    "expected": True,
                    "observed": False,
                    "passed": False,
                    "reason": "Missing source cannot be verified.",
                }
            ],
        ),
        success=False,
    )
    browser_challenge = _evidence_result(
        action="open_url",
        evidence=ExecutionEvidence(
            action="open_url",
            target="https://example.com",
            target_type="browser",
            method="browser-url-gate",
            verifier="browser-url-gate/1",
            verification_state="approval_required",
            verification_reason="browser challenge detected",
            expected={"bot_challenge_detected": False},
            observed={"bot_challenge_detected": True},
            verification_checks=[
                {
                    "check_name": "browser_challenge_absent",
                    "expected": False,
                    "observed": True,
                    "passed": False,
                    "reason": "Challenge state is not verified success.",
                }
            ],
        ),
        success=False,
    )

    results = [verified_write, unverified_write, verified_read, failed_read, browser_challenge]
    events = [
        event
        for index, result in enumerate(results)
        for event in _events_for_result(f"action-{index}", result)
    ]
    timeline = project_action_timeline(events, session_id="session-runtime-truth")

    assert [item["status"] for item in timeline] == [
        "success",
        "error",
        "success",
        "error",
        "approval_required",
    ]
    for result, item in zip(results, timeline):
        assert result.proof["execution_evidence"] == result.execution_evidence.model_dump()
        assert item["execution_evidence"] == result.execution_evidence.model_dump()
    assert timeline[0]["execution_evidence"]["verification_state"] == "verified"
    assert timeline[1]["execution_evidence"]["verification_state"] == "unverified"
    assert timeline[3]["execution_evidence"]["verification_state"] == "unverified"
    assert timeline[4]["execution_evidence"]["verification_state"] == "approval_required"
