import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from aegis.core import journal_cleanup, maintenance
from aegis.core.approval_hygiene import build_approval_hygiene_preview, reject_grant_like_payload
from aegis.core.commands import ApprovalManager, get_approval_manager
from aegis.core.constants import ActionStatus, CommandStatus, IntentSource, RiskLevel
from aegis.core.context import ExecutionContext
from aegis.core.evidence_audit import audit_action_evidence
from aegis.core.guard_policy import classify_intent_risk
from aegis.core.journal_cleanup import (
    build_runtime_journal_compaction_manifest,
    evaluate_runtime_journal_compaction_execution_readiness,
)
from aegis.core.non_executable_runtime_adapter import (
    build_non_executable_event_batch,
    project_non_executable_events_to_action_timeline,
    project_non_executable_events_to_snapshot,
)
from aegis.core.protocol import ProtocolEventType, reset_sequence_for_testing
from aegis.core.repo_audit_inventory_runner_readiness import (
    REPO_AUDIT_INVENTORY_RUNNER_EXECUTION_PERMISSION,
    validate_repo_audit_inventory_runner_readiness,
)
from aegis.core.runtime_timeout import (
    RuntimePhaseTimeoutInput,
    TimeoutEventProjectionInput,
    TimeoutKind,
    TimeoutPhase,
    build_timeout_event_projection,
    evaluate_runtime_timeout,
)
from aegis.core.schemas import ActionResult, CommandRequest, GuardResult, IntentResult, ReliabilityMetrics
from aegis.executor import desktop_verifier
from aegis.executor.desktop_verifier import verification_to_execution_evidence
from aegis.executor.provider_interstitials import classify_provider_interstitial
from aegis.orchestrator import orchestrator as orchestrator_module
from aegis.orchestrator.orchestrator import Orchestrator
from aegis.tools.desktop_tools import FocusTool, OpenAppTool
from aegis.tools.web_tools import ClickTool


@pytest.fixture(autouse=True)
def reset_approval_manager_state():
    manager = get_approval_manager()
    manager.reset_for_tests()
    yield
    manager.reset_for_tests()


class FakeRouter:
    async def route(self, _intent):
        return SimpleNamespace(planner_model=None)


class FakeParser:
    def __init__(self, intents):
        self._intents = intents

    async def parse(self, _text, model=None):
        return list(self._intents)


class FakePlanner:
    def __init__(self, intents):
        self._intents = intents

    def plan(self, _intents):
        return list(self._intents)


class FakeVerifier:
    async def verify_result(self, _result, _intended_effect=None):
        return 1.0


class SpyExecutor:
    def __init__(self):
        self.calls = []

    async def execute(self, intent, _context: ExecutionContext, cancellation_token=None):
        self.calls.append(intent)
        return ActionResult(
            action=intent.intent,
            params=intent.params,
            status=ActionStatus.EXECUTED,
            success=True,
            output=intent.intent,
            metrics=ReliabilityMetrics(),
        )


class AllowGuard:
    def __init__(self):
        self.decisions = []

    def evaluate(self, intent, context=None):
        decision = GuardResult(allowed=True, reason="allowed for threat-model test", risk=RiskLevel.LOW)
        self.decisions.append((intent, context, decision))
        return decision


class NonExecutableBoundaryJournal:
    def __init__(self):
        self.events = []

    def append(self, event):
        self.events.append(event)
        return event


def intent_result(tool_name, params=None, *, source=IntentSource.RULE, risk_level=RiskLevel.LOW):
    return IntentResult(
        raw_input=f"{tool_name} threat-model test",
        intent=tool_name,
        params=params or {},
        risk=risk_level,
        source=source,
        confidence=1.0,
    )


def build_orchestrator(intent, executor, guard=None):
    intents = [intent]
    orchestrator = Orchestrator()
    orchestrator.parser = FakeParser(intents)
    orchestrator.planner = FakePlanner(intents)
    orchestrator.executor = executor
    orchestrator.verifier = FakeVerifier()
    orchestrator.router = FakeRouter()
    orchestrator.guard = guard or AllowGuard()
    return orchestrator


def quiet_runtime_emissions(monkeypatch, action_started_calls=None):
    async def fake_emit_event(*args, **kwargs):
        return None

    async def fake_emit_command_status(*args, **kwargs):
        return None

    async def fake_emit_task_finished(*args, **kwargs):
        return None

    async def fake_emit_state_change(*args, **kwargs):
        return True

    monkeypatch.setattr(orchestrator_module.ws_bridge, "emit_event", fake_emit_event)
    monkeypatch.setattr(orchestrator_module.ws_bridge, "emit_command_status", fake_emit_command_status)
    monkeypatch.setattr(orchestrator_module.ws_bridge, "emit_task_finished", fake_emit_task_finished)
    monkeypatch.setattr(orchestrator_module.ws_bridge, "emit_state_change", fake_emit_state_change)

    if action_started_calls is not None:
        async def fake_emit_action_started(*args, **kwargs):
            action_started_calls.append((args, kwargs))
            return True

        monkeypatch.setattr(orchestrator_module.ws_bridge, "emit_action_started", fake_emit_action_started)


def assert_no_execution_shape(value):
    if isinstance(value, dict):
        assert "execution_evidence" not in value
        assert value.get("success") is not True
        assert value.get("verified") is not True
        assert value.get("action_started") is not True
        for nested in value.values():
            assert_no_execution_shape(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            assert_no_execution_shape(nested)


def write_jsonl(path: Path, entries):
    path.write_text("\n".join(json.dumps(entry, sort_keys=True) for entry in entries) + "\n", encoding="utf-8")


@pytest.mark.asyncio
async def test_threat_approval_granted_cannot_bypass_policy_boundary_for_quarantined_click(monkeypatch):
    reset_sequence_for_testing()
    action_started_calls = []
    quiet_runtime_emissions(monkeypatch, action_started_calls)
    executor = SpyExecutor()
    journal = NonExecutableBoundaryJournal()
    click_intent = intent_result("click", {"x": 10, "y": 20}, risk_level=RiskLevel.HIGH)
    orchestrator = build_orchestrator(click_intent, executor)

    response = await orchestrator.process(
        CommandRequest(
            text="click at 10 20",
            context={
                "trace_id": "threat-approval-boundary",
                "approval_granted": True,
                "non_executable_journal": journal,
            },
        )
    )

    assert response.status is CommandStatus.PENDING_APPROVAL
    assert executor.calls == []
    assert action_started_calls == []
    assert response.guard is not None
    assert response.guard.allowed is False
    assert "generic click quarantine" in response.guard.reason
    assert [event.type for event in journal.events] == [
        ProtocolEventType.COMMAND_CLASSIFIED.value,
        ProtocolEventType.APPROVAL_REQUESTED.value,
        ProtocolEventType.COMMAND_WAITING_FOR_APPROVAL.value,
    ]
    assert all(event.payload.get("executed") is not True for event in journal.events)
    assert all(event.payload.get("not_executed") is True for event in journal.events)
    assert_no_execution_shape([event.payload for event in journal.events])


def test_threat_stale_missing_and_already_resolved_approval_ids_fail_without_execution():
    manager = ApprovalManager()
    state = manager.register_pending(
        command_id="cmd-threat-approval",
        text="open calculator",
        trace_id="trace-threat-approval",
        reason="test approval",
        risk_level=RiskLevel.MEDIUM,
        metadata={"approval_id": "approval-threat", "resume_allowed": False},
    )

    with pytest.raises(KeyError):
        manager.resolve_approval("missing-approval", approved=True)

    denied = manager.resolve_approval(state.metadata["approval_id"], approved=False)
    assert denied.status is CommandStatus.REJECTED
    assert denied.metadata["approval_resolution_status"] == "approval_denied"
    assert denied.metadata["not_executed"] is True
    assert denied.metadata["mutation_performed"] is False

    with pytest.raises(ValueError):
        manager.resolve_approval(state.metadata["approval_id"], approved=True)


def test_threat_restored_hygiene_preview_does_not_authorize_grant_or_current_session_sweep():
    manager = ApprovalManager()
    manager.register_pending(
        command_id="cmd-threat-restored-hygiene",
        text="open notepad",
        trace_id="trace-threat-restored-hygiene",
        reason="restored approval",
        risk_level=RiskLevel.MEDIUM,
        metadata={
            "approval_id": "approval-threat-restored-hygiene",
            "restored_from_journal": True,
            "restored_source": "command_event_replay",
        },
    )
    manager.register_pending(
        command_id="cmd-threat-current-hygiene",
        text="open notepad",
        trace_id="trace-threat-current-hygiene",
        reason="current approval",
        risk_level=RiskLevel.MEDIUM,
        metadata={"approval_id": "approval-threat-current-hygiene"},
    )

    assert reject_grant_like_payload({"decision": "grant"}) is not None
    assert reject_grant_like_payload({"approved": True}) is not None
    preview = build_approval_hygiene_preview(
        manager.snapshot(),
        ["approval-threat-restored-hygiene", "approval-threat-current-hygiene"],
    )

    by_id = {item["approval_id"]: item for item in preview["items"]}
    assert preview["approval_grant_exposed"] is False
    assert by_id["approval-threat-restored-hygiene"]["eligible"] is True
    assert by_id["approval-threat-current-hygiene"]["eligible"] is False
    assert by_id["approval-threat-current-hygiene"]["ineligible_reason"] == "current_session_excluded"
    assert manager.get("cmd-threat-restored-hygiene").status is CommandStatus.PENDING_APPROVAL
    assert manager.get("cmd-threat-current-hygiene").status is CommandStatus.PENDING_APPROVAL


def test_threat_clarification_answer_is_state_only_not_replanned_or_executed():
    manager = ApprovalManager()
    state = manager.register_waiting_clarification(
        command_id="cmd-threat-clarification",
        text="click there",
        trace_id="trace-threat-clarification",
        risk_level=RiskLevel.HIGH,
        reason="Which target?",
        metadata={"clarification_id": "clarification-threat"},
    )

    resolved = manager.resolve_clarification(state.metadata["clarification_id"], answer="click the blue button")

    assert resolved.status is CommandStatus.BLOCKED
    assert resolved.metadata["clarification_resolution_status"] == "clarification_resolved"
    assert resolved.metadata["clarification_answer"] == "click the blue button"
    assert resolved.metadata["not_executed"] is True
    assert resolved.metadata["completed_without_execution"] is True
    assert resolved.metadata["mutation_performed"] is False


def test_threat_clarification_cancel_remains_non_executed():
    manager = ApprovalManager()
    state = manager.register_waiting_clarification(
        command_id="cmd-threat-clarification-cancel",
        text="open app",
        trace_id="trace-threat-clarification-cancel",
        risk_level=RiskLevel.MEDIUM,
        reason="Which app?",
        metadata={"clarification_id": "clarification-cancel-threat"},
    )

    cancelled = manager.resolve_clarification(state.metadata["clarification_id"], cancelled=True)

    assert cancelled.status is CommandStatus.CANCELLED
    assert cancelled.metadata["clarification_resolution_status"] == "clarification_cancelled"
    assert cancelled.metadata["not_executed"] is True
    assert cancelled.metadata["completed_without_execution"] is True
    assert cancelled.metadata["mutation_performed"] is False


def test_threat_non_executable_projection_cannot_convert_quarantine_to_executable():
    decision = classify_intent_risk("click", {})
    batch = build_non_executable_event_batch(
        decision,
        command_id="cmd-threat-projection",
        trace_id="trace-threat-projection",
        timestamp_ms=123,
    )

    snapshot = project_non_executable_events_to_snapshot(batch.events)
    timeline = project_non_executable_events_to_action_timeline(batch.events)

    assert snapshot["executed"] is False
    assert snapshot["not_executed"] is True
    assert snapshot["command_status"] == CommandStatus.WAITING_FOR_CLARIFICATION.value
    assert snapshot["pending_clarification"] is not None
    assert snapshot["pending_approval"] is None
    assert timeline
    assert timeline[-1]["kind"] == "clarification_requested"
    assert_no_execution_shape(snapshot)
    assert_no_execution_shape(timeline)


def test_threat_window_title_only_app_match_remains_unverified(monkeypatch):
    window = SimpleNamespace(title="Antigravity IDE", _hWnd=101)

    monkeypatch.setattr(desktop_verifier, "resolve_app_name", lambda _app: "antigravity")
    monkeypatch.setattr(
        desktop_verifier,
        "get_app_config",
        lambda _app: {
            "process_name": "Antigravity IDE.exe",
            "window_keywords": ["Antigravity IDE"],
        },
    )
    monkeypatch.setattr(desktop_verifier, "get_running_pids", lambda _process_name: [])
    monkeypatch.setattr(desktop_verifier, "get_window_pid", lambda _window: None)
    monkeypatch.setattr(desktop_verifier.gw, "getAllWindows", lambda: [window])
    monkeypatch.setattr(desktop_verifier.gw, "getActiveWindow", lambda: None)

    verification = desktop_verifier.verify_desktop_action(action="open_app", app="Antigravity IDE")
    evidence = verification_to_execution_evidence(verification=verification, app="Antigravity IDE", started_at_ms=1)

    checks = {check["name"]: check for check in verification.checks}
    assert verification.verified is False
    assert verification.verification_state == "unverified"
    assert checks["window_manifested"]["passed"] is True
    assert checks["process_alive"]["passed"] is False
    assert checks["window_pid_matches_target_process"]["passed"] is None
    assert "verified" not in evidence.model_dump()
    assert evidence.verification_state == "unverified"


def test_threat_dispatch_success_without_evidence_is_audit_warning_not_verified():
    report = audit_action_evidence(
        [
            {
                "type": "ACTION_COMPLETED",
                "sequence_num": 1,
                "timestamp": 1.0,
                "payload": {
                    "action_id": "action-without-evidence",
                    "tool": "open_app",
                    "success": True,
                },
            }
        ]
    )

    assert report["status"] == "warning"
    assert report["missing_evidence_count"] == 1
    assert report["verified_action_count"] == 0
    assert report["verification_counts"]["missing"] == 1


def test_threat_failed_verifier_evidence_does_not_become_success_or_verified():
    report = audit_action_evidence(
        [
            {
                "type": "ACTION_FAILED",
                "sequence_num": 1,
                "timestamp": 1.0,
                "payload": {
                    "action_id": "failed-verification",
                    "tool": "open_app",
                    "success": False,
                    "execution_evidence": {
                        "verified": False,
                        "verification_state": "failed",
                        "checks": {
                            "process_alive": {
                                "passed": False,
                                "critical": True,
                                "reason": "process not alive",
                            }
                        },
                    },
                },
            }
        ]
    )

    assert report["status"] == "fail"
    assert report["failed_evidence_count"] == 1
    assert report["critical_failure_count"] >= 1
    assert report["verified_action_count"] == 0


def test_threat_journal_cleanup_readiness_does_not_mutate_history_or_expose_execution_helpers(tmp_path):
    journal_path = tmp_path / "runtime_events.jsonl"
    write_jsonl(
        journal_path,
        [
            {
                "type": "COMMAND_RECEIVED",
                "sequence_num": 1,
                "timestamp": 1.0,
                "payload": {"command_id": "cmd-1"},
            },
            {
                "type": "ACTION_FAILED",
                "sequence_num": 2,
                "timestamp": 2.0,
                "payload": {
                    "action_id": "action-1",
                    "execution_evidence": {"verified": False, "verification_state": "failed"},
                },
            },
            {
                "type": "SNAPSHOT_CREATED",
                "sequence_num": 3,
                "timestamp": 3.0,
                "payload": {"snapshot_id": "snap-1"},
            },
        ],
    )
    before = journal_path.read_bytes()

    manifest = build_runtime_journal_compaction_manifest(journal_path)
    readiness = evaluate_runtime_journal_compaction_execution_readiness(manifest)

    assert journal_path.read_bytes() == before
    assert manifest["mutation_performed"] is False
    assert readiness["mutation_performed"] is False
    assert readiness["compaction_execution_allowed"] is False
    assert readiness["in_place_mutation_allowed"] is False


def test_threat_repo_audit_runner_readiness_rejects_frontend_model_and_read_claims():
    decision = validate_repo_audit_inventory_runner_readiness(
        {
            "request_id": "threat:repo-audit-runner-readiness",
            "project_ref": "project:aegis",
            "repo_id": "WexyS/Aegis",
            "repo_name": "Aegis",
            "repo_root_ref": "workspace:aegis",
            "tenant_scope": "local",
            "namespace": "repo_audit",
            "read_plan_ref": "repo-audit-read-plan:threat",
            "runner_scope": ["metadata_only_runner_readiness"],
            "file_access_mode": "future_read_only",
            "path_normalization_policy": "relative_path_only",
            "secret_exclusion_policy": "deny_by_default",
            "generated_artifact_policy": "deny_by_default",
            "runtime_journal_policy": "blocked",
            "log_policy": "blocked",
            "dependency_policy": "blocked",
            "build_artifact_policy": "blocked",
            "model_artifact_policy": "blocked",
            "vector_db_policy": "blocked",
            "hidden_path_policy": "explicit_future_gate_required",
            "symlink_policy": "explicit_future_gate_required",
            "content_logging_policy": "no_raw_content_logging",
            "redaction_policy": "redaction_required",
            "privacy_class": "project_internal",
            "data_sensitivity": "source_code",
            "budget_policy": {
                "max_file_count": 1,
                "max_file_size_bytes": 1000,
                "max_total_bytes": 1000,
                "budget_policy": "human_review_required_above_limits",
            },
            "evidence_expectation": ["file_read_attempt_evidence_expected"],
            "verifier_expectation": ["path_within_repo_root_verifier"],
            "planned_targets": [
                {
                    "original_path": "src/aegis/core/repo_audit_pack.py",
                    "normalized_relative_path": "src/aegis/core/repo_audit_pack.py",
                    "category": "future_read_candidate",
                    "expected_evidence": ["file_read_attempt_evidence_expected"],
                    "expected_verifier": ["path_within_repo_root_verifier"],
                }
            ],
            "frontend_authority": True,
            "requested_models": ["model-said-ready"],
            "file_read_performed": True,
            "read_result_created": True,
            "claims": ["proof file content", "official audit result"],
            "execution_permission": REPO_AUDIT_INVENTORY_RUNNER_EXECUTION_PERMISSION,
        }
    )

    assert decision.readiness_status == "blocked_by_unsafe_related_decision"
    assert "frontend_authority_not_allowed" in decision.failure_reasons
    assert "model_call_request_denied" in decision.failure_reasons
    assert "file_read_request_denied" in decision.failure_reasons
    assert "read_result_creation_denied" in decision.failure_reasons
    assert "proof_file_content_claim_denied" in decision.failure_reasons
    assert "official_audit_result_claim_denied" in decision.failure_reasons
    assert decision.runtime_dispatch_allowed is False
    assert decision.file_read_performed is False
    assert decision.read_result_created is False
    assert decision.evidence_provided_by_readiness is False
    assert decision.verifier_success is False
    for forbidden_name in (
        "execute_runtime_journal_compaction",
        "apply_runtime_journal_compaction",
        "archive_runtime_journal_events",
        "compact_runtime_journal",
        "truncate_runtime_journal",
    ):
        assert not hasattr(journal_cleanup, forbidden_name)


def test_threat_maintenance_scan_and_app_discovery_remain_read_only(monkeypatch):
    calls = []

    def forbidden_action(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("maintenance diagnostics must remain read-only")

    monkeypatch.setattr(OpenAppTool, "run", forbidden_action)
    monkeypatch.setattr(FocusTool, "run", forbidden_action)
    monkeypatch.setattr(ClickTool, "run", forbidden_action)
    monkeypatch.setattr("aegis.core.app_discovery_smoke.gw.getAllWindows", lambda: [])
    monkeypatch.setattr("aegis.core.app_discovery_smoke.get_running_pids", lambda _process_name: [])

    report = maintenance.run_read_only_maintenance_scan(
        runtime_snapshot={
            "last_runtime_state": "idle",
            "pending_approvals": [],
            "event_journal": {"hash_chain_valid": True},
        },
        websocket_clients=0,
    )

    assert calls == []
    assert report["read_only"] is True
    assert report["checks"]["read_only_contract"]["observed_mutations"] == []
    assert report["checks"]["app_discovery"]["read_only"] is True
    assert report["checks"]["app_discovery"]["actions_performed"] == []
    for proposal in report["action_proposals"]:
        assert proposal["requires_approval"] is True
        assert proposal["read_only"] is True
        assert proposal["dry_run_preview"]["would_mutate"] is False


def test_threat_runtime_timeout_payload_cannot_grant_frontend_authority_or_success():
    decision = evaluate_runtime_timeout(
        RuntimePhaseTimeoutInput(
            command_id="cmd-threat-timeout",
            phase=TimeoutPhase.EXECUTING,
            evaluated_at_ms=10_000,
            started_at_ms=1_000,
            updated_at_ms=1_000,
            deadline_at_ms=2_000,
            dispatch_attempted=True,
            dispatch_succeeded=True,
            verification_state="verified",
            frontend_authority_claimed=True,
            metadata={
                "frontend_timeout_authority": True,
                "approval_granted": True,
                "runtime_dispatch_allowed": True,
                "verified_success": True,
            },
        )
    )

    assert decision.timeout_kind is TimeoutKind.EXECUTION_TIMEOUT
    assert "frontend_timeout_authority_rejected" in decision.notes
    assert decision.runtime_dispatch_allowed is False
    assert decision.approval_granted is False
    assert decision.auto_resume_allowed is False
    assert decision.frontend_authority_allowed is False
    assert decision.verified_success is False
    assert decision.fallback_plan.runtime_dispatch_allowed is False
    assert decision.fallback_plan.approval_granted is False
    assert decision.fallback_plan.verified_success is False
    assert decision.fallback_plan.mutation_performed is False


def test_threat_provider_interstitial_is_not_timeout_without_backend_deadline():
    interstitial = classify_provider_interstitial(
        "https://www.google.com/sorry/index?continue=https://www.google.com/search%3Fq%3Daegis%2Bruntime",
        requested_provider="google",
        requested_url="https://www.google.com/search?q=aegis+runtime",
    )

    decision = evaluate_runtime_timeout(
        RuntimePhaseTimeoutInput(
            command_id="cmd-threat-google-sorry",
            phase=TimeoutPhase.VERIFYING,
            evaluated_at_ms=10_000,
            started_at_ms=9_000,
            updated_at_ms=9_000,
            deadline_at_ms=None,
            dispatch_attempted=True,
            dispatch_succeeded=True,
            verification_state="approval_required",
            bot_challenge_detected=interstitial.blocked_by_bot_challenge,
            browser_metadata={
                "requested_provider": "google",
                "requested_url": "https://www.google.com/search?q=aegis+runtime",
                "final_url": "https://www.google.com/sorry/index?continue=https://www.google.com/search%3Fq%3Daegis%2Bruntime",
                "provider_interstitial_detected": interstitial.detected,
                "provider_interstitial_reason": interstitial.reason,
            },
        )
    )

    assert interstitial.detected is True
    assert decision.timeout_kind is TimeoutKind.NONE
    assert decision.finding is None
    assert decision.verified_success is False
    assert decision.runtime_dispatch_allowed is False
    assert "bot_challenge_is_verifier_evidence_not_timeout_without_elapsed_deadline" in decision.notes


def test_threat_timeout_projection_payload_cannot_grant_authority_or_execution():
    decision = build_timeout_event_projection(
        TimeoutEventProjectionInput(
            timeout_input=RuntimePhaseTimeoutInput(
                command_id="cmd-threat-timeout-projection",
                phase=TimeoutPhase.EXECUTING,
                evaluated_at_ms=10_000,
                started_at_ms=1_000,
                updated_at_ms=1_000,
                deadline_at_ms=2_000,
                dispatch_attempted=True,
                dispatch_succeeded=True,
                verification_state="verified",
                frontend_authority_claimed=True,
                metadata={
                    "frontend_timeout_authority": True,
                    "approval_grant": True,
                    "capability_grant": True,
                    "lease_grant": True,
                    "runtime_dispatch_allowed": True,
                    "verified_success": True,
                },
            ),
            observed_at_ms=10_000,
            frontend_authority_claimed=True,
        )
    )

    assert decision.projection_created is True
    payload = decision.projection.payload
    assert payload["not_executed"] is True
    assert payload["executed"] is False
    assert payload["approval_grant"] is False
    assert payload["capability_grant"] is False
    assert payload["lease_grant"] is False
    assert payload["runtime_dispatch_allowed"] is False
    assert payload["verified_success"] is False
    assert payload["evidence_created"] is False
    assert payload["frontend_authority"] is False
    assert payload["mutation_performed"] is False
    assert payload["journal_plan"]["append_now"] is False
    assert "execution_evidence" not in payload


def test_threat_lifecycle_resolution_wording_keeps_execution_separate_from_resolution():
    pending_panel = Path("frontend/src/features/runtime/components/PendingApprovalPanel.tsx").read_text(encoding="utf-8")
    socket_client = Path("frontend/src/lib/socket.ts").read_text(encoding="utf-8")

    assert "without execution" in pending_panel
    assert "state-only" in pending_panel
    assert "does not reparse or execute" in pending_panel
    assert "Grant records the decision only" in pending_panel
    assert "restored grant blocked" in pending_panel
    assert "Restored approvals cannot be granted from this panel" in pending_panel
    assert "Review only" in pending_panel
    assert "APPROVAL_RESOLVED" in socket_client
    assert "CLARIFICATION_RESOLVED" in socket_client
