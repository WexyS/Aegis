from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError

import pytest

from aegis.core.runtime_timeout import (
    RecoveryDisposition,
    TIMEOUT_PROJECTION_EVENT_TYPE,
    TimeoutEventProjectionInput,
    RuntimePhaseTimeoutInput,
    RuntimeTimeoutBudget,
    TimeoutProjectionKind,
    TimeoutProjectionScope,
    TimeoutKind,
    TimeoutPhase,
    build_runtime_timeout_diagnostics,
    build_timeout_event_projection,
    evaluate_runtime_timeout,
    runtime_timeout_input_from_command_record,
)


def _input(**overrides):
    data = {
        "command_id": "cmd-timeout",
        "phase": TimeoutPhase.EXECUTING,
        "evaluated_at_ms": 10_000,
        "started_at_ms": 1_000,
        "updated_at_ms": 2_000,
    }
    data.update(overrides)
    return RuntimePhaseTimeoutInput(**data)


def _budget(**phase_budgets):
    return RuntimeTimeoutBudget(
        default_phase_budget_ms=1_000,
        max_retries=2,
        phase_budgets_ms=phase_budgets,
    )


def test_inside_budget_does_not_create_fallback_or_authority() -> None:
    decision = evaluate_runtime_timeout(
        _input(evaluated_at_ms=2_500, updated_at_ms=2_000),
        budget=_budget(executing=1_000),
    )

    assert decision.timeout_kind is TimeoutKind.NONE
    assert decision.overdue is False
    assert decision.finding is None
    assert decision.fallback_plan.disposition is RecoveryDisposition.NONE
    assert decision.runtime_dispatch_allowed is False
    assert decision.approval_granted is False
    assert decision.auto_resume_allowed is False
    assert decision.verified_success is False
    assert decision.mutation_performed is False


def test_overdue_pre_dispatch_stale_requires_attention_without_dispatch() -> None:
    decision = evaluate_runtime_timeout(
        _input(
            phase=TimeoutPhase.QUEUED,
            started_at_ms=1_000,
            updated_at_ms=None,
            evaluated_at_ms=3_000,
            dispatch_attempted=False,
        ),
        budget=_budget(queued=500),
    )

    assert decision.timeout_kind is TimeoutKind.PRE_DISPATCH_STALE
    assert decision.recovery_disposition is RecoveryDisposition.OPERATOR_ATTENTION
    assert decision.dispatch_attempted is False
    assert decision.fallback_plan.runtime_dispatch_allowed is False
    assert decision.fallback_plan.actions == ("surface_operator_attention",)


def test_overdue_execution_classifies_failed_safe_negative_evidence_required() -> None:
    decision = evaluate_runtime_timeout(
        _input(
            phase=TimeoutPhase.EXECUTING,
            evaluated_at_ms=5_000,
            last_heartbeat_at_ms=1_000,
            dispatch_attempted=True,
            dispatch_succeeded=False,
            evidence_required=True,
        ),
        budget=_budget(executing=1_000),
    )

    assert decision.timeout_kind is TimeoutKind.EXECUTION_TIMEOUT
    assert decision.verification_state == "failed"
    assert decision.recovery_disposition is RecoveryDisposition.RECORD_NEGATIVE_EVIDENCE_REQUIRED
    assert decision.finding is not None
    assert decision.finding.requires_negative_evidence is True
    assert "record_negative_evidence" in decision.fallback_plan.actions[0]
    assert decision.verified_success is False


def test_overdue_verifier_remains_unverified_and_does_not_change_criteria() -> None:
    decision = evaluate_runtime_timeout(
        _input(
            phase=TimeoutPhase.VERIFYING,
            evaluated_at_ms=10_000,
            updated_at_ms=1_000,
            verification_attempted=True,
            verification_state="verified",
        ),
        budget=_budget(verifying=1_000),
    )

    assert decision.timeout_kind is TimeoutKind.VERIFIER_TIMEOUT
    assert decision.recovery_disposition is RecoveryDisposition.VERIFIER_REMAINS_UNVERIFIED
    assert decision.verification_state == "unverified"
    assert decision.verified_success is False
    assert decision.fallback_plan.verified_success is False


@pytest.mark.parametrize(
    ("phase", "kind"),
    [
        (TimeoutPhase.APPROVAL_PENDING, TimeoutKind.APPROVAL_STALE),
        (TimeoutPhase.CLARIFICATION_PENDING, TimeoutKind.CLARIFICATION_STALE),
    ],
)
def test_stale_approval_and_clarification_never_auto_resolve_or_execute(phase, kind) -> None:
    decision = evaluate_runtime_timeout(
        _input(
            phase=phase,
            started_at_ms=1_000,
            updated_at_ms=1_500,
            evaluated_at_ms=10_000,
            approval_required=phase is TimeoutPhase.APPROVAL_PENDING,
            clarification_required=phase is TimeoutPhase.CLARIFICATION_PENDING,
        ),
        budget=_budget(**{phase.value: 1_000}),
    )

    assert decision.timeout_kind is kind
    assert decision.approval_granted is False
    assert decision.auto_resume_allowed is False
    assert decision.runtime_dispatch_allowed is False
    assert decision.fallback_plan.approval_granted is False
    assert decision.fallback_plan.auto_resume_allowed is False


def test_stale_restored_pending_does_not_auto_resume() -> None:
    decision = evaluate_runtime_timeout(
        _input(
            phase=TimeoutPhase.RESTORED_PENDING,
            started_at_ms=1_000,
            evaluated_at_ms=10_000,
            restored=True,
        ),
        budget=_budget(restored_pending=1_000),
    )

    assert decision.timeout_kind is TimeoutKind.RESTORED_PENDING_STALE
    assert decision.recovery_disposition is RecoveryDisposition.RESTORED_DECISION_REVIEW_REQUIRED
    assert decision.auto_resume_allowed is False
    assert "do_not_auto_resume" in decision.fallback_plan.actions


def test_retry_budget_is_bounded_and_exhaustion_does_not_retry() -> None:
    decision = evaluate_runtime_timeout(
        _input(retry_count=2, max_retries=2, evaluated_at_ms=2_000, updated_at_ms=1_900),
        budget=_budget(executing=5_000),
    )

    assert decision.timeout_kind is TimeoutKind.RETRY_EXHAUSTED
    assert decision.retry_exhausted is True
    assert decision.retry_budget_remaining == 0
    assert decision.recovery_disposition is RecoveryDisposition.RETRY_BOUNDARY_EXHAUSTED
    assert "stop_implicit_retry" in decision.fallback_plan.actions
    assert decision.runtime_dispatch_allowed is False


def test_browser_dispatch_preserves_metadata_without_kill_or_success() -> None:
    decision = evaluate_runtime_timeout(
        _input(
            phase=TimeoutPhase.BROWSER_DISPATCHING,
            started_at_ms=1_000,
            updated_at_ms=1_000,
            evaluated_at_ms=5_000,
            dispatch_attempted=True,
            browser_metadata={
                "requested_url": "https://www.google.com",
                "final_url": "https://www.google.com/sorry/",
                "browser_runtime": "controlled_browser",
            },
        ),
        budget=_budget(browser_dispatching=1_000),
    )

    assert decision.timeout_kind is TimeoutKind.BROWSER_DISPATCH_TIMEOUT
    assert decision.finding is not None
    assert decision.finding.browser_metadata["final_url"] == "https://www.google.com/sorry/"
    assert decision.fallback_plan.fallback_executed is False
    assert decision.fallback_plan.runtime_dispatch_allowed is False
    assert "kill" not in " ".join(decision.fallback_plan.actions)


def test_bot_challenge_without_timing_is_not_timeout() -> None:
    decision = evaluate_runtime_timeout(
        RuntimePhaseTimeoutInput(
            command_id="cmd-bot",
            phase=TimeoutPhase.BROWSER_DISPATCHING,
            evaluated_at_ms=10_000,
            bot_challenge_detected=True,
            browser_metadata={"final_url": "https://www.google.com/sorry/"},
        )
    )

    assert decision.timeout_kind is TimeoutKind.INSUFFICIENT_TIMING
    assert decision.overdue is False
    assert decision.finding is None
    assert "bot_challenge_is_verifier_evidence_not_timeout_without_elapsed_deadline" in decision.notes


def test_helper_is_immutable_and_rejects_frontend_authority() -> None:
    metadata = {"frontend_timeout_authority": True, "nested": {"value": "original"}}
    timeout_input = _input(metadata=metadata, frontend_authority_claimed=True)
    metadata["nested"]["value"] = "mutated"

    with pytest.raises(FrozenInstanceError):
        timeout_input.command_id = "changed"

    assert timeout_input.metadata["nested"]["value"] == "original"
    decision = evaluate_runtime_timeout(timeout_input, budget=_budget(executing=1_000))
    assert "frontend_timeout_authority_rejected" in decision.notes
    assert decision.frontend_authority_allowed is False
    assert decision.fallback_plan.frontend_authority_allowed is False
    assert decision.runtime_dispatch_allowed is False


def test_command_record_mapping_uses_backend_lifecycle_and_restored_pending() -> None:
    record = {
        "command_id": "cmd-restored",
        "text": "open notepad",
        "status": "pending_approval",
        "approval_required": True,
        "verification_state": "unverified",
        "created_at": 1_000,
        "updated_at": 2_000,
        "metadata": {
            "restored_from_journal": True,
            "restored_source": "command_event_replay",
            "approval_id": "approval-restored",
        },
    }

    timeout_input = runtime_timeout_input_from_command_record(record, evaluated_at_ms=100_000)

    assert timeout_input.phase is TimeoutPhase.RESTORED_PENDING
    assert timeout_input.restored is True
    assert timeout_input.approval_required is True


def test_diagnostics_are_read_only_and_do_not_mutate_snapshot() -> None:
    snapshot = {
        "records": [
            {
                "command_id": "cmd-running",
                "text": "open https://example.com",
                "status": "running",
                "active": True,
                "verification_state": "unverified",
                "created_at": 1_000,
                "updated_at": 1_000,
                "metadata": {
                    "intent": "open_url",
                    "requested_url": "https://example.com",
                    "dispatch_attempted": True,
                    "retry_count": 3,
                    "max_retries": 3,
                },
            }
        ],
        "pending_approvals": [],
        "pending_clarifications": [],
        "active_command": None,
    }
    before = deepcopy(snapshot)

    report = build_runtime_timeout_diagnostics(
        snapshot,
        generated_at_ms=10_000,
        budget=_budget(browser_dispatching=1_000),
    )

    assert snapshot == before
    assert report["read_only"] is True
    assert report["mutation_performed"] is False
    assert report["actions_performed"] == []
    assert report["status"] == "fail"
    assert report["retry_exhausted_count"] == 1
    assert report["safety"]["no_runtime_dispatch"] is True
    assert report["safety"]["no_auto_approval"] is True
    assert report["safety"]["no_auto_resume"] is True
    assert report["safety"]["no_process_or_browser_kill"] is True


def _projection(timeout_input: RuntimePhaseTimeoutInput):
    return build_timeout_event_projection(
        TimeoutEventProjectionInput(
            timeout_input=timeout_input,
            observed_at_ms=10_000,
            trace_id="trace-timeout",
            lifecycle_id="lifecycle-timeout",
            sequence_num=7,
        ),
        budget=_budget(
            queued=1_000,
            executing=1_000,
            browser_dispatching=1_000,
            verifying=1_000,
            approval_pending=1_000,
            clarification_pending=1_000,
            restored_pending=1_000,
        ),
    )


def _assert_projection_no_authority(payload: dict) -> None:
    assert payload["verified_success"] is False
    assert payload["evidence_created"] is False
    assert payload["approval_grant"] is False
    assert payload["capability_grant"] is False
    assert payload["lease_grant"] is False
    assert payload["runtime_dispatch_allowed"] is False
    assert payload["execution_permission"] == "not_granted_by_timeout_projection"
    assert payload["mutation_performed"] is False
    assert payload["frontend_authority"] is False
    assert payload["not_executed"] is True
    assert payload["executed"] is False
    assert "execution_evidence" not in payload


def test_timeout_finding_projects_to_non_executing_timeout_observed_payload() -> None:
    decision = _projection(
        _input(
            phase=TimeoutPhase.EXECUTING,
            started_at_ms=1_000,
            updated_at_ms=1_000,
            evaluated_at_ms=10_000,
            deadline_at_ms=2_000,
            dispatch_attempted=True,
            evidence_required=True,
        )
    )

    assert decision.projection_created is True
    assert decision.projection is not None
    payload = dict(decision.projection.payload)
    assert decision.projection.projection_kind is TimeoutProjectionKind.EXECUTION_TIMEOUT_OBSERVED
    assert decision.projection.projection_scope is TimeoutProjectionScope.EXECUTION
    assert decision.projection.runtime_event.type == TIMEOUT_PROJECTION_EVENT_TYPE
    assert decision.projection.runtime_event.sequence_num == 7
    assert payload["projection_version"] == "backend-timeout-event-projection/1"
    assert payload["projection_kind"] == "execution_timeout_observed"
    assert payload["source_timeout_kind"] == "execution_timeout"
    assert payload["requires_operator_attention"] is True
    assert payload["evidence_required"] is True
    assert payload["journal_plan"]["append_only"] is True
    assert payload["journal_plan"]["append_now"] is False
    _assert_projection_no_authority(payload)


def test_pre_dispatch_stale_projection_has_no_dispatch_attempt() -> None:
    decision = _projection(
        _input(
            phase=TimeoutPhase.QUEUED,
            started_at_ms=1_000,
            updated_at_ms=None,
            evaluated_at_ms=10_000,
            dispatch_attempted=False,
        )
    )

    payload = dict(decision.projection.payload)
    assert decision.projection.projection_kind is TimeoutProjectionKind.STALE_PRE_DISPATCH_OBSERVED
    assert payload["dispatch_attempted"] is False
    assert payload["dispatch_succeeded"] is False
    _assert_projection_no_authority(payload)


def test_verifier_timeout_projection_remains_unverified() -> None:
    decision = _projection(
        _input(
            phase=TimeoutPhase.VERIFYING,
            started_at_ms=1_000,
            updated_at_ms=1_000,
            evaluated_at_ms=10_000,
            deadline_at_ms=2_000,
            verification_attempted=True,
            verification_state="verified",
        )
    )

    payload = dict(decision.projection.payload)
    assert decision.projection.projection_kind is TimeoutProjectionKind.VERIFIER_TIMEOUT_OBSERVED
    assert payload["verification_attempted"] is True
    assert payload["verification_state"] == "unverified"
    assert payload["suggested_operator_action"] == "review_verifier_evidence"
    _assert_projection_no_authority(payload)


@pytest.mark.parametrize(
    ("phase", "projection_kind", "stale_decision_kind"),
    [
        (TimeoutPhase.APPROVAL_PENDING, TimeoutProjectionKind.STALE_APPROVAL_OBSERVED, "approval"),
        (TimeoutPhase.CLARIFICATION_PENDING, TimeoutProjectionKind.STALE_CLARIFICATION_OBSERVED, "clarification"),
        (TimeoutPhase.RESTORED_PENDING, TimeoutProjectionKind.RESTORED_PENDING_STALE_OBSERVED, "restored_pending"),
    ],
)
def test_stale_decision_projection_does_not_approve_deny_execute_or_resume(
    phase,
    projection_kind,
    stale_decision_kind,
) -> None:
    decision = _projection(
        _input(
            phase=phase,
            started_at_ms=1_000,
            updated_at_ms=1_000,
            evaluated_at_ms=10_000,
            deadline_at_ms=2_000,
            approval_required=phase is TimeoutPhase.APPROVAL_PENDING,
            clarification_required=phase is TimeoutPhase.CLARIFICATION_PENDING,
            restored=phase is TimeoutPhase.RESTORED_PENDING,
        )
    )

    payload = dict(decision.projection.payload)
    assert decision.projection.projection_kind is projection_kind
    assert decision.projection.projection_scope is TimeoutProjectionScope.PENDING_DECISION
    assert payload["stale_decision_kind"] == stale_decision_kind
    assert payload["suggested_operator_action"] == "review_pending_decision"
    assert "approve" not in " ".join(payload["recovery_proposal"])
    if phase is TimeoutPhase.RESTORED_PENDING:
        assert "do_not_auto_resume" in payload["recovery_proposal"]
    else:
        assert "resume" not in " ".join(payload["recovery_proposal"])
    _assert_projection_no_authority(payload)


def test_retry_exhausted_projection_does_not_retry() -> None:
    decision = _projection(
        _input(
            phase=TimeoutPhase.EXECUTING,
            started_at_ms=1_000,
            updated_at_ms=9_500,
            evaluated_at_ms=10_000,
            retry_count=2,
            max_retries=2,
        )
    )

    payload = dict(decision.projection.payload)
    assert decision.projection.projection_kind is TimeoutProjectionKind.RETRY_EXHAUSTED_OBSERVED
    assert decision.projection.projection_scope is TimeoutProjectionScope.RETRY
    assert payload["retry_count"] == 2
    assert payload["max_retries"] == 2
    assert payload["suggested_operator_action"] == "review_retry_policy"
    assert "stop_implicit_retry" in payload["recovery_proposal"]
    _assert_projection_no_authority(payload)


def test_browser_timeout_projection_preserves_url_metadata_without_verifying_url() -> None:
    decision = _projection(
        _input(
            phase=TimeoutPhase.BROWSER_DISPATCHING,
            started_at_ms=1_000,
            updated_at_ms=1_000,
            evaluated_at_ms=10_000,
            deadline_at_ms=2_000,
            dispatch_attempted=True,
            browser_metadata={
                "requested_url": "https://www.google.com/search?q=aegis",
                "final_url": "https://www.google.com/sorry/",
                "browser_runtime": "controlled_browser",
            },
        )
    )

    payload = dict(decision.projection.payload)
    assert decision.projection.projection_kind is TimeoutProjectionKind.BROWSER_TIMEOUT_OBSERVED
    assert payload["browser_metadata"]["requested_url"] == "https://www.google.com/search?q=aegis"
    assert payload["browser_metadata"]["final_url"] == "https://www.google.com/sorry/"
    assert payload["verification_state"] == "failed"
    assert payload["verified_success"] is False
    assert "verify" not in payload["suggested_operator_action"]
    _assert_projection_no_authority(payload)


def test_bot_challenge_is_not_projected_without_backend_timeout_condition() -> None:
    decision = build_timeout_event_projection(
        TimeoutEventProjectionInput(
            timeout_input=RuntimePhaseTimeoutInput(
                command_id="cmd-bot-only",
                phase=TimeoutPhase.BROWSER_DISPATCHING,
                evaluated_at_ms=10_000,
                bot_challenge_detected=True,
                browser_metadata={"final_url": "https://www.google.com/sorry/"},
            ),
            observed_at_ms=10_000,
        )
    )

    assert decision.projection_created is False
    assert decision.projection is None
    assert decision.reason == "no_backend_timeout_finding_to_project"


def test_projection_cannot_be_created_from_frontend_authority_alone() -> None:
    decision = build_timeout_event_projection(
        TimeoutEventProjectionInput(
            timeout_input=RuntimePhaseTimeoutInput(
                command_id="cmd-frontend-only",
                phase=TimeoutPhase.EXECUTING,
                evaluated_at_ms=10_000,
                frontend_authority_claimed=True,
                metadata={"frontend_timeout_authority": True},
            ),
            observed_at_ms=10_000,
            frontend_authority_claimed=True,
        )
    )

    assert decision.projection_created is False
    assert decision.projection is None
    assert decision.reason == "frontend_timeout_authority_rejected_without_backend_timeout_finding"
    assert decision.runtime_dispatch_allowed is False
    assert decision.approval_grant is False


def test_projection_input_is_not_mutated() -> None:
    metadata = {"nested": {"value": "original"}, "lifecycle_id": "lifecycle-input"}
    browser_metadata = {"requested_url": "https://example.com"}
    timeout_input = _input(
        phase=TimeoutPhase.BROWSER_DISPATCHING,
        deadline_at_ms=2_000,
        metadata=metadata,
        browser_metadata=browser_metadata,
    )
    metadata["nested"]["value"] = "mutated"
    browser_metadata["requested_url"] = "https://mutated.example"

    decision = _projection(timeout_input)

    assert timeout_input.metadata["nested"]["value"] == "original"
    assert timeout_input.browser_metadata["requested_url"] == "https://example.com"
    assert decision.projection.payload["lifecycle_id"] == "lifecycle-timeout"
