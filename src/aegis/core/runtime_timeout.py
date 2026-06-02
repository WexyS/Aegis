from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum, unique
from types import MappingProxyType
from typing import Any, Mapping

from aegis.core.commands import now_ms
from aegis.core.protocol import Component, RuntimeEvent, Severity


RUNTIME_TIMEOUT_DIAGNOSTICS_VERSION = "runtime-timeout-diagnostics/1"
RUNTIME_TIMEOUT_DECISION_VERSION = "runtime-timeout-decision/1"
TIMEOUT_EVENT_PROJECTION_VERSION = "backend-timeout-event-projection/1"
TIMEOUT_PROJECTION_EVENT_TYPE = "TIMEOUT_OBSERVED"


@unique
class TimeoutPhase(str, Enum):
    RECEIVED = "received"
    CLASSIFIED = "classified"
    GUARDED = "guarded"
    APPROVAL_PENDING = "approval_pending"
    CLARIFICATION_PENDING = "clarification_pending"
    QUEUED = "queued"
    DISPATCHING = "dispatching"
    EXECUTING = "executing"
    BROWSER_DISPATCHING = "browser_dispatching"
    VERIFYING = "verifying"
    RECORDING_EVIDENCE = "recording_evidence"
    FINALIZING = "finalizing"
    RESTORED_PENDING = "restored_pending"
    UNKNOWN = "unknown"


@unique
class TimeoutKind(str, Enum):
    NONE = "none"
    INSUFFICIENT_TIMING = "insufficient_timing"
    PRE_DISPATCH_STALE = "pre_dispatch_stale"
    APPROVAL_STALE = "approval_stale"
    CLARIFICATION_STALE = "clarification_stale"
    EXECUTION_TIMEOUT = "execution_timeout"
    BROWSER_DISPATCH_TIMEOUT = "browser_dispatch_timeout"
    VERIFIER_TIMEOUT = "verifier_timeout"
    EVIDENCE_RECORDING_TIMEOUT = "evidence_recording_timeout"
    FINALIZATION_TIMEOUT = "finalization_timeout"
    RESTORED_PENDING_STALE = "restored_pending_stale"
    RETRY_EXHAUSTED = "retry_exhausted"
    UNKNOWN_STALE = "unknown_stale"


@unique
class RecoveryDisposition(str, Enum):
    NONE = "none"
    OBSERVE_ONLY = "observe_only"
    OPERATOR_ATTENTION = "operator_attention"
    RECORD_NEGATIVE_EVIDENCE_REQUIRED = "record_negative_evidence_required"
    VERIFIER_REMAINS_UNVERIFIED = "verifier_remains_unverified"
    RETRY_BOUNDARY_EXHAUSTED = "retry_boundary_exhausted"
    RESTORED_DECISION_REVIEW_REQUIRED = "restored_decision_review_required"


@unique
class TimeoutProjectionKind(str, Enum):
    TIMEOUT_OBSERVED = "timeout_observed"
    STALE_PRE_DISPATCH_OBSERVED = "stale_pre_dispatch_observed"
    STALE_APPROVAL_OBSERVED = "stale_approval_observed"
    STALE_CLARIFICATION_OBSERVED = "stale_clarification_observed"
    EXECUTION_TIMEOUT_OBSERVED = "execution_timeout_observed"
    BROWSER_TIMEOUT_OBSERVED = "browser_timeout_observed"
    VERIFIER_TIMEOUT_OBSERVED = "verifier_timeout_observed"
    EVIDENCE_RECORDING_TIMEOUT_OBSERVED = "evidence_recording_timeout_observed"
    RETRY_EXHAUSTED_OBSERVED = "retry_exhausted_observed"
    RESTORED_PENDING_STALE_OBSERVED = "restored_pending_stale_observed"
    UNKNOWN_STALE_OBSERVED = "unknown_stale_observed"


@unique
class TimeoutProjectionScope(str, Enum):
    COMMAND_LIFECYCLE = "command_lifecycle"
    PENDING_DECISION = "pending_decision"
    EXECUTION = "execution"
    BROWSER = "browser"
    VERIFIER = "verifier"
    EVIDENCE = "evidence"
    RETRY = "retry"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class RuntimeTimeoutBudget:
    default_phase_budget_ms: int = 60_000
    max_retries: int = 2
    phase_budgets_ms: Mapping[TimeoutPhase | str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        coerced: dict[TimeoutPhase, int] = {}
        for phase, value in dict(self.phase_budgets_ms).items():
            coerced[_coerce_phase(phase)] = max(0, int(value))
        object.__setattr__(self, "phase_budgets_ms", MappingProxyType(coerced))

    def budget_for(self, phase: TimeoutPhase) -> int:
        return int(self.phase_budgets_ms.get(phase, self.default_phase_budget_ms))


@dataclass(frozen=True)
class RuntimePhaseTimeoutInput:
    command_id: str
    phase: TimeoutPhase | str
    evaluated_at_ms: int
    started_at_ms: int | None = None
    updated_at_ms: int | None = None
    deadline_at_ms: int | None = None
    last_heartbeat_at_ms: int | None = None
    retry_count: int = 0
    max_retries: int | None = None
    dispatch_attempted: bool = False
    dispatch_succeeded: bool = False
    verification_attempted: bool = False
    verification_state: str = "unverified"
    evidence_required: bool = False
    restored: bool = False
    frontend_authority_claimed: bool = False
    approval_required: bool = False
    clarification_required: bool = False
    bot_challenge_detected: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)
    browser_metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "phase", _coerce_phase(self.phase))
        object.__setattr__(self, "retry_count", max(0, int(self.retry_count)))
        if self.max_retries is not None:
            object.__setattr__(self, "max_retries", max(0, int(self.max_retries)))
        object.__setattr__(self, "metadata", MappingProxyType(deepcopy(dict(self.metadata))))
        object.__setattr__(self, "browser_metadata", MappingProxyType(deepcopy(dict(self.browser_metadata))))


@dataclass(frozen=True)
class SafeFallbackPlan:
    disposition: RecoveryDisposition
    reason: str
    operator_attention_required: bool
    actions: tuple[str, ...] = ()
    runtime_dispatch_allowed: bool = False
    approval_granted: bool = False
    auto_resume_allowed: bool = False
    mutation_performed: bool = False
    verified_success: bool = False
    fallback_executed: bool = False
    frontend_authority_allowed: bool = False


@dataclass(frozen=True)
class RuntimeTimeoutFinding:
    finding_id: str
    timeout_kind: TimeoutKind
    phase: TimeoutPhase
    severity: str
    reason: str
    elapsed_ms: int | None
    deadline_at_ms: int | None
    age_source: str
    requires_negative_evidence: bool = False
    browser_metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "browser_metadata", MappingProxyType(deepcopy(dict(self.browser_metadata))))


@dataclass(frozen=True)
class RuntimeTimeoutDecision:
    scan_version: str
    command_id: str
    phase: TimeoutPhase
    timeout_kind: TimeoutKind
    recovery_disposition: RecoveryDisposition
    overdue: bool
    elapsed_ms: int | None
    deadline_at_ms: int | None
    age_source: str
    retry_count: int
    max_retries: int
    retry_budget_remaining: int
    retry_exhausted: bool
    dispatch_attempted: bool
    dispatch_succeeded: bool
    verification_state: str
    verified_success: bool
    fallback_plan: SafeFallbackPlan
    finding: RuntimeTimeoutFinding | None = None
    notes: tuple[str, ...] = ()
    read_only: bool = True
    mutation_performed: bool = False
    runtime_dispatch_allowed: bool = False
    approval_granted: bool = False
    auto_resume_allowed: bool = False
    frontend_authority_allowed: bool = False


@dataclass(frozen=True)
class TimeoutEventProjectionInput:
    timeout_input: RuntimePhaseTimeoutInput
    observed_at_ms: int
    trace_id: str | None = None
    lifecycle_id: str | None = None
    causation_id: str | None = None
    session_id: str | None = None
    sequence_num: int = 0
    frontend_authority_claimed: bool = False


@dataclass(frozen=True)
class TimeoutOperatorAttention:
    required: bool
    suggested_operator_action: str
    reason: str


@dataclass(frozen=True)
class TimeoutJournalProjectionPlan:
    event_type: str
    append_only: bool = True
    append_now: bool = False
    journal_append_required_for_future_enforcement: bool = True
    existing_history_mutation_allowed: bool = False
    replay_safe: bool = True
    mutation_performed: bool = False
    reason: str = "projection_contract_only_no_journal_append"


@dataclass(frozen=True)
class TimeoutEventProjection:
    projection_version: str
    projection_id: str
    projection_kind: TimeoutProjectionKind
    projection_scope: TimeoutProjectionScope
    payload: Mapping[str, Any]
    runtime_event: RuntimeEvent
    journal_plan: TimeoutJournalProjectionPlan
    operator_attention: TimeoutOperatorAttention
    read_only: bool = True
    mutation_performed: bool = False
    runtime_dispatch_allowed: bool = False
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    verified_success: bool = False
    evidence_created: bool = False
    frontend_authority: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", MappingProxyType(deepcopy(dict(self.payload))))


@dataclass(frozen=True)
class TimeoutProjectionDecision:
    scan_version: str
    projection_created: bool
    reason: str
    timeout_decision: RuntimeTimeoutDecision
    projection: TimeoutEventProjection | None = None
    read_only: bool = True
    mutation_performed: bool = False
    runtime_dispatch_allowed: bool = False
    approval_grant: bool = False
    capability_grant: bool = False
    lease_grant: bool = False
    verified_success: bool = False
    evidence_created: bool = False
    frontend_authority: bool = False


def evaluate_runtime_timeout(
    timeout_input: RuntimePhaseTimeoutInput,
    *,
    budget: RuntimeTimeoutBudget | None = None,
) -> RuntimeTimeoutDecision:
    budget = budget or DEFAULT_RUNTIME_TIMEOUT_BUDGET
    phase = _coerce_phase(timeout_input.phase)
    max_retries = timeout_input.max_retries if timeout_input.max_retries is not None else budget.max_retries
    retry_exhausted = timeout_input.retry_count >= max_retries
    retry_budget_remaining = max(0, max_retries - timeout_input.retry_count)
    elapsed_ms, deadline_at_ms, age_source = _timing(timeout_input, budget=budget, phase=phase)
    overdue = deadline_at_ms is not None and timeout_input.evaluated_at_ms >= deadline_at_ms

    notes: list[str] = []
    if timeout_input.bot_challenge_detected and not overdue:
        notes.append("bot_challenge_is_verifier_evidence_not_timeout_without_elapsed_deadline")
    if timeout_input.frontend_authority_claimed:
        notes.append("frontend_timeout_authority_rejected")

    if retry_exhausted:
        kind = TimeoutKind.RETRY_EXHAUSTED
        disposition = RecoveryDisposition.RETRY_BOUNDARY_EXHAUSTED
        reason = "retry budget exhausted; timeout contract cannot launch another retry"
    elif deadline_at_ms is None:
        kind = TimeoutKind.INSUFFICIENT_TIMING
        disposition = RecoveryDisposition.OBSERVE_ONLY
        reason = "deadline and elapsed timing are unavailable; no timeout is classified"
    elif not overdue:
        kind = TimeoutKind.NONE
        disposition = RecoveryDisposition.NONE
        reason = "phase is within runtime-owned timeout budget"
    else:
        kind, disposition, reason = _overdue_classification(phase)

    finding = None
    if kind not in {TimeoutKind.NONE, TimeoutKind.INSUFFICIENT_TIMING}:
        finding = RuntimeTimeoutFinding(
            finding_id=f"runtime.timeout.{timeout_input.command_id}.{kind.value}",
            timeout_kind=kind,
            phase=phase,
            severity="fail" if kind in _FAILURE_TIMEOUT_KINDS else "warning",
            reason=reason,
            elapsed_ms=elapsed_ms,
            deadline_at_ms=deadline_at_ms,
            age_source=age_source,
            requires_negative_evidence=disposition == RecoveryDisposition.RECORD_NEGATIVE_EVIDENCE_REQUIRED,
            browser_metadata=timeout_input.browser_metadata,
        )

    fallback_plan = _fallback_plan(
        disposition=disposition,
        kind=kind,
        phase=phase,
        reason=reason,
    )
    verification_state = _verification_state(timeout_input.verification_state, kind=kind, phase=phase)
    return RuntimeTimeoutDecision(
        scan_version=RUNTIME_TIMEOUT_DECISION_VERSION,
        command_id=timeout_input.command_id,
        phase=phase,
        timeout_kind=kind,
        recovery_disposition=disposition,
        overdue=overdue,
        elapsed_ms=elapsed_ms,
        deadline_at_ms=deadline_at_ms,
        age_source=age_source,
        retry_count=timeout_input.retry_count,
        max_retries=max_retries,
        retry_budget_remaining=retry_budget_remaining,
        retry_exhausted=retry_exhausted,
        dispatch_attempted=timeout_input.dispatch_attempted,
        dispatch_succeeded=timeout_input.dispatch_succeeded,
        verification_state=verification_state,
        verified_success=False,
        fallback_plan=fallback_plan,
        finding=finding,
        notes=tuple(notes),
    )


def build_runtime_timeout_diagnostics(
    commands_snapshot: dict[str, Any] | None,
    *,
    generated_at_ms: int | None = None,
    budget: RuntimeTimeoutBudget | None = None,
    max_records: int = 50,
) -> dict[str, Any]:
    budget = budget or DEFAULT_RUNTIME_TIMEOUT_BUDGET
    generated_at = generated_at_ms if generated_at_ms is not None else now_ms()
    records = _command_records(commands_snapshot)
    timeout_inputs = [
        runtime_timeout_input_from_command_record(record, evaluated_at_ms=generated_at)
        for record in records
        if _record_is_timeout_relevant(record)
    ]
    decisions = [evaluate_runtime_timeout(timeout_input, budget=budget) for timeout_input in timeout_inputs]
    findings = [decision.finding for decision in decisions if decision.finding is not None]
    projection_decisions = [
        build_timeout_event_projection(
            TimeoutEventProjectionInput(
                timeout_input=timeout_input,
                observed_at_ms=generated_at,
                trace_id=_string_or_none(timeout_input.metadata.get("trace_id")),
                lifecycle_id=_string_or_none(timeout_input.metadata.get("lifecycle_id")),
                session_id=_string_or_none(timeout_input.metadata.get("session_id")),
                frontend_authority_claimed=timeout_input.frontend_authority_claimed,
            ),
            budget=budget,
            timeout_decision=decision,
        )
        for timeout_input, decision in zip(timeout_inputs, decisions)
    ]
    projections = [item.projection for item in projection_decisions if item.projection is not None]
    status = "fail" if any(finding.severity == "fail" for finding in findings) else "warning" if findings else "ok"
    return {
        "scan_version": RUNTIME_TIMEOUT_DIAGNOSTICS_VERSION,
        "read_only": True,
        "mutation_performed": False,
        "status": status,
        "source_of_truth": "backend_command_lifecycle_snapshot",
        "generated_at_ms": generated_at,
        "record_count": len(records),
        "evaluated_count": len(decisions),
        "finding_count": len(findings),
        "overdue_count": sum(1 for decision in decisions if decision.overdue),
        "retry_exhausted_count": sum(1 for decision in decisions if decision.retry_exhausted),
        "timeout_projection_count": len(projections),
        "stale_pending_projection_count": sum(
            1
            for projection in projections
            if projection.projection_scope == TimeoutProjectionScope.PENDING_DECISION
        ),
        "stale_execution_projection_count": sum(
            1
            for projection in projections
            if projection.projection_scope
            in {
                TimeoutProjectionScope.EXECUTION,
                TimeoutProjectionScope.BROWSER,
                TimeoutProjectionScope.VERIFIER,
                TimeoutProjectionScope.EVIDENCE,
                TimeoutProjectionScope.RETRY,
            }
        ),
        "projection_status": status,
        "projection_mutation_performed": False,
        "projection_dispatch_allowed": False,
        "projection_approval_grant_exposed": False,
        "negative_evidence_required_count": sum(
            1
            for decision in decisions
            if decision.recovery_disposition == RecoveryDisposition.RECORD_NEGATIVE_EVIDENCE_REQUIRED
        ),
        "phase_counts": _count_by(decisions, "phase"),
        "timeout_kind_counts": _count_by(decisions, "timeout_kind"),
        "safety": {
            "no_mutation_performed": True,
            "no_auto_approval": True,
            "no_auto_resume": True,
            "no_runtime_dispatch": True,
            "no_frontend_authority": True,
            "no_verifier_success": True,
            "no_process_or_browser_kill": True,
            "retry_requires_runtime_policy": True,
            "projection_does_not_append_journal": True,
            "projection_existing_history_mutation_allowed": False,
        },
        "actions_performed": [],
        "guidance": [
            "Timeout diagnostics classify overdue phases only; they do not resolve approvals or clarifications.",
            "Timeout fallback is not verifier success and does not create execution permission.",
            "Retry budget exhaustion blocks implicit retry; any future retry execution requires a separate runtime policy path.",
            "Browser timeout diagnostics preserve metadata and do not kill browser or process state.",
        ],
        "decisions": [_to_plain(decision) for decision in decisions[:max_records]],
        "projections": [_to_plain(projection) for projection in projections[:max_records]],
        "findings": [_to_plain(finding) for finding in findings[:max_records]],
        "omitted_decision_count": max(0, len(decisions) - max_records),
        "omitted_projection_count": max(0, len(projections) - max_records),
        "omitted_finding_count": max(0, len(findings) - max_records),
    }


def build_timeout_event_projection(
    projection_input: TimeoutEventProjectionInput,
    *,
    budget: RuntimeTimeoutBudget | None = None,
    timeout_decision: RuntimeTimeoutDecision | None = None,
) -> TimeoutProjectionDecision:
    budget = budget or DEFAULT_RUNTIME_TIMEOUT_BUDGET
    timeout_decision = timeout_decision or evaluate_runtime_timeout(projection_input.timeout_input, budget=budget)
    if timeout_decision.finding is None:
        reason = "no_backend_timeout_finding_to_project"
        if projection_input.frontend_authority_claimed or projection_input.timeout_input.frontend_authority_claimed:
            reason = "frontend_timeout_authority_rejected_without_backend_timeout_finding"
        return TimeoutProjectionDecision(
            scan_version=TIMEOUT_EVENT_PROJECTION_VERSION,
            projection_created=False,
            reason=reason,
            timeout_decision=timeout_decision,
        )

    timeout_input = projection_input.timeout_input
    projection_kind = _projection_kind(timeout_decision.timeout_kind)
    projection_scope = _projection_scope(timeout_decision)
    budget_ms = _projection_budget_ms(timeout_input, budget=budget, phase=timeout_decision.phase)
    lifecycle_id = (
        projection_input.lifecycle_id
        or _string_or_none(timeout_input.metadata.get("lifecycle_id"))
        or timeout_input.command_id
    )
    stale_decision_kind = _stale_decision_kind(timeout_decision.phase)
    evidence_required = bool(timeout_input.evidence_required or timeout_decision.finding.requires_negative_evidence)
    operator_attention = TimeoutOperatorAttention(
        required=timeout_decision.fallback_plan.operator_attention_required,
        suggested_operator_action=_suggested_operator_action(timeout_decision),
        reason=timeout_decision.finding.reason,
    )
    journal_plan = TimeoutJournalProjectionPlan(event_type=TIMEOUT_PROJECTION_EVENT_TYPE)
    projection_id = (
        f"timeout-projection:{timeout_input.command_id}:"
        f"{projection_kind.value}:{projection_input.observed_at_ms}"
    )
    payload = {
        "projection_version": TIMEOUT_EVENT_PROJECTION_VERSION,
        "projection_id": projection_id,
        "projection_kind": projection_kind.value,
        "projection_scope": projection_scope.value,
        "command_id": timeout_input.command_id,
        "lifecycle_id": lifecycle_id,
        "source_timeout_kind": timeout_decision.timeout_kind.value,
        "source_phase": timeout_decision.phase.value,
        "observed_at": projection_input.observed_at_ms,
        "started_at": timeout_input.started_at_ms,
        "updated_at": timeout_input.updated_at_ms,
        "deadline_at": timeout_decision.deadline_at_ms,
        "elapsed_ms": timeout_decision.elapsed_ms,
        "budget_ms": budget_ms,
        "dispatch_attempted": timeout_decision.dispatch_attempted,
        "dispatch_succeeded": timeout_decision.dispatch_succeeded,
        "verification_attempted": timeout_input.verification_attempted,
        "verification_state": timeout_decision.verification_state,
        "verified_success": False,
        "evidence_created": False,
        "evidence_required": evidence_required,
        "requires_operator_attention": operator_attention.required,
        "suggested_operator_action": operator_attention.suggested_operator_action,
        "recovery_proposal": tuple(timeout_decision.fallback_plan.actions),
        "retry_count": timeout_decision.retry_count,
        "max_retries": timeout_decision.max_retries,
        "stale_decision_kind": stale_decision_kind,
        "approval_grant": False,
        "capability_grant": False,
        "lease_grant": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": "not_granted_by_timeout_projection",
        "mutation_performed": False,
        "frontend_authority": False,
        "journal_append_required_for_future_enforcement": True,
        "existing_history_mutation_allowed": False,
        "replay_safe": True,
        "not_executed": True,
        "executed": False,
        "projection_only": True,
        "journal_plan": _to_plain(journal_plan),
    }
    if timeout_input.browser_metadata:
        payload["browser_metadata"] = dict(timeout_input.browser_metadata)
    if timeout_input.bot_challenge_detected:
        payload["bot_challenge_detected"] = True

    _assert_timeout_projection_payload_is_non_authoritative(payload)
    event = RuntimeEvent(
        type=TIMEOUT_PROJECTION_EVENT_TYPE,
        timestamp=int(projection_input.observed_at_ms),
        trace_id=projection_input.trace_id,
        causation_id=projection_input.causation_id,
        session_id=projection_input.session_id,
        source=Component.SYSTEM.value,
        severity=Severity.WARNING.value,
        sequence_num=max(0, int(projection_input.sequence_num)),
        runtime_phase=timeout_decision.phase.value,
        payload=payload,
    )
    projection = TimeoutEventProjection(
        projection_version=TIMEOUT_EVENT_PROJECTION_VERSION,
        projection_id=projection_id,
        projection_kind=projection_kind,
        projection_scope=projection_scope,
        payload=payload,
        runtime_event=event,
        journal_plan=journal_plan,
        operator_attention=operator_attention,
    )
    return TimeoutProjectionDecision(
        scan_version=TIMEOUT_EVENT_PROJECTION_VERSION,
        projection_created=True,
        reason="backend_timeout_finding_projected_as_non_executing_event",
        timeout_decision=timeout_decision,
        projection=projection,
    )


def runtime_timeout_input_from_command_record(
    record: dict[str, Any],
    *,
    evaluated_at_ms: int,
) -> RuntimePhaseTimeoutInput:
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    phase = _phase_from_record(record, metadata)
    browser_metadata = _browser_metadata(record, metadata)
    return RuntimePhaseTimeoutInput(
        command_id=str(record.get("command_id") or "unknown-command"),
        phase=phase,
        evaluated_at_ms=evaluated_at_ms,
        started_at_ms=_int_or_none(record.get("created_at")),
        updated_at_ms=_int_or_none(record.get("updated_at")),
        deadline_at_ms=_int_or_none(metadata.get("deadline_at_ms")),
        last_heartbeat_at_ms=_int_or_none(metadata.get("last_heartbeat_at_ms")),
        retry_count=_int_or_zero(metadata.get("retry_count", record.get("retry_count"))),
        max_retries=_int_or_none(metadata.get("max_retries")),
        dispatch_attempted=metadata.get("dispatch_attempted") is True,
        dispatch_succeeded=metadata.get("dispatch_succeeded") is True,
        verification_attempted=metadata.get("verification_attempted") is True,
        verification_state=str(record.get("verification_state") or metadata.get("verification_state") or "unverified"),
        evidence_required=metadata.get("evidence_required") is True,
        restored=metadata.get("restored_from_journal") is True,
        frontend_authority_claimed=metadata.get("frontend_timeout_authority") is True,
        approval_required=record.get("approval_required") is True,
        clarification_required=record.get("clarification_required") is True,
        bot_challenge_detected=metadata.get("bot_challenge_detected") is True,
        metadata=metadata,
        browser_metadata=browser_metadata,
    )


_FAILURE_TIMEOUT_KINDS = {
    TimeoutKind.EXECUTION_TIMEOUT,
    TimeoutKind.BROWSER_DISPATCH_TIMEOUT,
    TimeoutKind.VERIFIER_TIMEOUT,
    TimeoutKind.EVIDENCE_RECORDING_TIMEOUT,
    TimeoutKind.RETRY_EXHAUSTED,
}


def _coerce_phase(value: TimeoutPhase | str) -> TimeoutPhase:
    if isinstance(value, TimeoutPhase):
        return value
    try:
        return TimeoutPhase(str(value))
    except ValueError:
        return TimeoutPhase.UNKNOWN


def _projection_kind(timeout_kind: TimeoutKind) -> TimeoutProjectionKind:
    return {
        TimeoutKind.PRE_DISPATCH_STALE: TimeoutProjectionKind.STALE_PRE_DISPATCH_OBSERVED,
        TimeoutKind.APPROVAL_STALE: TimeoutProjectionKind.STALE_APPROVAL_OBSERVED,
        TimeoutKind.CLARIFICATION_STALE: TimeoutProjectionKind.STALE_CLARIFICATION_OBSERVED,
        TimeoutKind.EXECUTION_TIMEOUT: TimeoutProjectionKind.EXECUTION_TIMEOUT_OBSERVED,
        TimeoutKind.BROWSER_DISPATCH_TIMEOUT: TimeoutProjectionKind.BROWSER_TIMEOUT_OBSERVED,
        TimeoutKind.VERIFIER_TIMEOUT: TimeoutProjectionKind.VERIFIER_TIMEOUT_OBSERVED,
        TimeoutKind.EVIDENCE_RECORDING_TIMEOUT: TimeoutProjectionKind.EVIDENCE_RECORDING_TIMEOUT_OBSERVED,
        TimeoutKind.RETRY_EXHAUSTED: TimeoutProjectionKind.RETRY_EXHAUSTED_OBSERVED,
        TimeoutKind.RESTORED_PENDING_STALE: TimeoutProjectionKind.RESTORED_PENDING_STALE_OBSERVED,
        TimeoutKind.UNKNOWN_STALE: TimeoutProjectionKind.UNKNOWN_STALE_OBSERVED,
    }.get(timeout_kind, TimeoutProjectionKind.TIMEOUT_OBSERVED)


def _projection_scope(decision: RuntimeTimeoutDecision) -> TimeoutProjectionScope:
    if decision.timeout_kind in {
        TimeoutKind.APPROVAL_STALE,
        TimeoutKind.CLARIFICATION_STALE,
        TimeoutKind.RESTORED_PENDING_STALE,
    }:
        return TimeoutProjectionScope.PENDING_DECISION
    if decision.timeout_kind == TimeoutKind.BROWSER_DISPATCH_TIMEOUT:
        return TimeoutProjectionScope.BROWSER
    if decision.timeout_kind == TimeoutKind.VERIFIER_TIMEOUT:
        return TimeoutProjectionScope.VERIFIER
    if decision.timeout_kind == TimeoutKind.EVIDENCE_RECORDING_TIMEOUT:
        return TimeoutProjectionScope.EVIDENCE
    if decision.timeout_kind == TimeoutKind.RETRY_EXHAUSTED:
        return TimeoutProjectionScope.RETRY
    if decision.timeout_kind == TimeoutKind.EXECUTION_TIMEOUT:
        return TimeoutProjectionScope.EXECUTION
    if decision.timeout_kind == TimeoutKind.PRE_DISPATCH_STALE:
        return TimeoutProjectionScope.COMMAND_LIFECYCLE
    return TimeoutProjectionScope.UNKNOWN


def _projection_budget_ms(
    timeout_input: RuntimePhaseTimeoutInput,
    *,
    budget: RuntimeTimeoutBudget,
    phase: TimeoutPhase,
) -> int | None:
    basis = _age_basis(timeout_input, phase=phase)
    if timeout_input.deadline_at_ms is not None and basis is not None:
        return max(0, timeout_input.deadline_at_ms - basis)
    if basis is not None:
        return budget.budget_for(phase)
    return None


def _stale_decision_kind(phase: TimeoutPhase) -> str | None:
    if phase == TimeoutPhase.APPROVAL_PENDING:
        return "approval"
    if phase == TimeoutPhase.CLARIFICATION_PENDING:
        return "clarification"
    if phase == TimeoutPhase.RESTORED_PENDING:
        return "restored_pending"
    return None


def _suggested_operator_action(decision: RuntimeTimeoutDecision) -> str:
    if decision.timeout_kind == TimeoutKind.PRE_DISPATCH_STALE:
        return "review_command_lifecycle"
    if decision.timeout_kind in {
        TimeoutKind.APPROVAL_STALE,
        TimeoutKind.CLARIFICATION_STALE,
        TimeoutKind.RESTORED_PENDING_STALE,
    }:
        return "review_pending_decision"
    if decision.timeout_kind in {
        TimeoutKind.EXECUTION_TIMEOUT,
        TimeoutKind.BROWSER_DISPATCH_TIMEOUT,
        TimeoutKind.EVIDENCE_RECORDING_TIMEOUT,
    }:
        return "inspect_execution_evidence_boundary"
    if decision.timeout_kind == TimeoutKind.VERIFIER_TIMEOUT:
        return "review_verifier_evidence"
    if decision.timeout_kind == TimeoutKind.RETRY_EXHAUSTED:
        return "review_retry_policy"
    return "inspect_runtime_lifecycle"


def _assert_timeout_projection_payload_is_non_authoritative(value: Any) -> None:
    if isinstance(value, dict):
        forbidden_true = (
            "success",
            "verified",
            "verified_success",
            "approval_grant",
            "capability_grant",
            "lease_grant",
            "runtime_dispatch_allowed",
            "mutation_performed",
            "frontend_authority",
            "evidence_created",
        )
        if "execution_evidence" in value:
            raise ValueError("timeout projection cannot include execution_evidence")
        for key in forbidden_true:
            if value.get(key) is True:
                raise ValueError(f"timeout projection cannot set {key}=true")
        for nested in value.values():
            _assert_timeout_projection_payload_is_non_authoritative(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _assert_timeout_projection_payload_is_non_authoritative(nested)


DEFAULT_RUNTIME_TIMEOUT_BUDGET = RuntimeTimeoutBudget(
    default_phase_budget_ms=60_000,
    max_retries=2,
    phase_budgets_ms={
        TimeoutPhase.RECEIVED: 30_000,
        TimeoutPhase.CLASSIFIED: 30_000,
        TimeoutPhase.GUARDED: 30_000,
        TimeoutPhase.QUEUED: 30_000,
        TimeoutPhase.DISPATCHING: 120_000,
        TimeoutPhase.EXECUTING: 120_000,
        TimeoutPhase.BROWSER_DISPATCHING: 120_000,
        TimeoutPhase.VERIFYING: 60_000,
        TimeoutPhase.RECORDING_EVIDENCE: 60_000,
        TimeoutPhase.FINALIZING: 30_000,
        TimeoutPhase.APPROVAL_PENDING: 60 * 60 * 1000,
        TimeoutPhase.CLARIFICATION_PENDING: 60 * 60 * 1000,
        TimeoutPhase.RESTORED_PENDING: 60 * 60 * 1000,
    },
)


def _timing(
    timeout_input: RuntimePhaseTimeoutInput,
    *,
    budget: RuntimeTimeoutBudget,
    phase: TimeoutPhase,
) -> tuple[int | None, int | None, str]:
    if timeout_input.deadline_at_ms is not None:
        basis = _age_basis(timeout_input, phase=phase)
        elapsed = None if basis is None else max(0, timeout_input.evaluated_at_ms - basis)
        return elapsed, timeout_input.deadline_at_ms, "explicit_deadline"

    basis = _age_basis(timeout_input, phase=phase)
    if basis is None:
        return None, None, "unknown"
    return (
        max(0, timeout_input.evaluated_at_ms - basis),
        basis + budget.budget_for(phase),
        _age_basis_name(timeout_input, phase=phase),
    )


def _age_basis(timeout_input: RuntimePhaseTimeoutInput, *, phase: TimeoutPhase) -> int | None:
    if phase in {
        TimeoutPhase.DISPATCHING,
        TimeoutPhase.EXECUTING,
        TimeoutPhase.BROWSER_DISPATCHING,
        TimeoutPhase.VERIFYING,
        TimeoutPhase.RECORDING_EVIDENCE,
        TimeoutPhase.FINALIZING,
    }:
        return (
            timeout_input.last_heartbeat_at_ms
            if timeout_input.last_heartbeat_at_ms is not None
            else timeout_input.updated_at_ms
            if timeout_input.updated_at_ms is not None
            else timeout_input.started_at_ms
        )
    return timeout_input.started_at_ms if timeout_input.started_at_ms is not None else timeout_input.updated_at_ms


def _age_basis_name(timeout_input: RuntimePhaseTimeoutInput, *, phase: TimeoutPhase) -> str:
    if phase in {
        TimeoutPhase.DISPATCHING,
        TimeoutPhase.EXECUTING,
        TimeoutPhase.BROWSER_DISPATCHING,
        TimeoutPhase.VERIFYING,
        TimeoutPhase.RECORDING_EVIDENCE,
        TimeoutPhase.FINALIZING,
    }:
        if timeout_input.last_heartbeat_at_ms is not None:
            return "last_heartbeat_at_ms"
        if timeout_input.updated_at_ms is not None:
            return "updated_at_ms"
    if timeout_input.started_at_ms is not None:
        return "started_at_ms"
    if timeout_input.updated_at_ms is not None:
        return "updated_at_ms"
    return "unknown"


def _overdue_classification(phase: TimeoutPhase) -> tuple[TimeoutKind, RecoveryDisposition, str]:
    if phase in {TimeoutPhase.RECEIVED, TimeoutPhase.CLASSIFIED, TimeoutPhase.GUARDED, TimeoutPhase.QUEUED}:
        return (
            TimeoutKind.PRE_DISPATCH_STALE,
            RecoveryDisposition.OPERATOR_ATTENTION,
            "pre-dispatch phase is overdue; no dispatch permission is granted",
        )
    if phase == TimeoutPhase.APPROVAL_PENDING:
        return (
            TimeoutKind.APPROVAL_STALE,
            RecoveryDisposition.OPERATOR_ATTENTION,
            "approval is stale; timeout does not grant or deny approval",
        )
    if phase == TimeoutPhase.CLARIFICATION_PENDING:
        return (
            TimeoutKind.CLARIFICATION_STALE,
            RecoveryDisposition.OPERATOR_ATTENTION,
            "clarification is stale; timeout does not infer intent or execute",
        )
    if phase == TimeoutPhase.RESTORED_PENDING:
        return (
            TimeoutKind.RESTORED_PENDING_STALE,
            RecoveryDisposition.RESTORED_DECISION_REVIEW_REQUIRED,
            "restored pending decision is stale; timeout does not auto-resume",
        )
    if phase == TimeoutPhase.BROWSER_DISPATCHING:
        return (
            TimeoutKind.BROWSER_DISPATCH_TIMEOUT,
            RecoveryDisposition.RECORD_NEGATIVE_EVIDENCE_REQUIRED,
            "browser dispatch is overdue; classify failed-safe without killing browser state",
        )
    if phase in {TimeoutPhase.DISPATCHING, TimeoutPhase.EXECUTING}:
        return (
            TimeoutKind.EXECUTION_TIMEOUT,
            RecoveryDisposition.RECORD_NEGATIVE_EVIDENCE_REQUIRED,
            "execution phase is overdue; negative evidence is required before any failure claim",
        )
    if phase == TimeoutPhase.VERIFYING:
        return (
            TimeoutKind.VERIFIER_TIMEOUT,
            RecoveryDisposition.VERIFIER_REMAINS_UNVERIFIED,
            "verification is overdue; verifier state remains unverified",
        )
    if phase == TimeoutPhase.RECORDING_EVIDENCE:
        return (
            TimeoutKind.EVIDENCE_RECORDING_TIMEOUT,
            RecoveryDisposition.RECORD_NEGATIVE_EVIDENCE_REQUIRED,
            "evidence recording is overdue; fallback cannot mark success",
        )
    if phase == TimeoutPhase.FINALIZING:
        return (
            TimeoutKind.FINALIZATION_TIMEOUT,
            RecoveryDisposition.OPERATOR_ATTENTION,
            "finalization is overdue; history must not be rewritten",
        )
    return (
        TimeoutKind.UNKNOWN_STALE,
        RecoveryDisposition.OPERATOR_ATTENTION,
        "unknown runtime phase is overdue; operator review is required",
    )


def _fallback_plan(
    *,
    disposition: RecoveryDisposition,
    kind: TimeoutKind,
    phase: TimeoutPhase,
    reason: str,
) -> SafeFallbackPlan:
    actions = {
        RecoveryDisposition.NONE: (),
        RecoveryDisposition.OBSERVE_ONLY: ("observe_backend_snapshot",),
        RecoveryDisposition.OPERATOR_ATTENTION: ("surface_operator_attention",),
        RecoveryDisposition.RECORD_NEGATIVE_EVIDENCE_REQUIRED: (
            "record_negative_evidence_if_runtime_reaches_evidence_boundary",
            "surface_operator_attention",
        ),
        RecoveryDisposition.VERIFIER_REMAINS_UNVERIFIED: (
            "keep_verification_state_unverified",
            "surface_operator_attention",
        ),
        RecoveryDisposition.RETRY_BOUNDARY_EXHAUSTED: (
            "stop_implicit_retry",
            "surface_operator_attention",
        ),
        RecoveryDisposition.RESTORED_DECISION_REVIEW_REQUIRED: (
            "surface_restored_pending_review",
            "do_not_auto_resume",
        ),
    }[disposition]
    return SafeFallbackPlan(
        disposition=disposition,
        reason=f"{kind.value}:{phase.value}:{reason}",
        operator_attention_required=disposition not in {RecoveryDisposition.NONE, RecoveryDisposition.OBSERVE_ONLY},
        actions=actions,
    )


def _verification_state(current: str, *, kind: TimeoutKind, phase: TimeoutPhase) -> str:
    normalized = str(current or "unverified")
    if kind in {
        TimeoutKind.EXECUTION_TIMEOUT,
        TimeoutKind.BROWSER_DISPATCH_TIMEOUT,
        TimeoutKind.EVIDENCE_RECORDING_TIMEOUT,
        TimeoutKind.RETRY_EXHAUSTED,
    }:
        return "failed"
    if phase == TimeoutPhase.VERIFYING or kind == TimeoutKind.VERIFIER_TIMEOUT:
        return "unverified"
    return normalized if normalized == "failed" else "unverified"


def _command_records(commands_snapshot: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(commands_snapshot, dict):
        return []
    records_by_id: dict[str, dict[str, Any]] = {}
    for key in ("records", "pending_approvals", "pending_clarifications"):
        value = commands_snapshot.get(key)
        if not isinstance(value, list):
            continue
        for item in value:
            if not isinstance(item, dict):
                continue
            command_id = item.get("command_id")
            if isinstance(command_id, str) and command_id:
                records_by_id[command_id] = deepcopy(item)
    active = commands_snapshot.get("active_command")
    if isinstance(active, dict) and isinstance(active.get("command_id"), str):
        records_by_id[active["command_id"]] = deepcopy(active)
    return list(records_by_id.values())


def _record_is_timeout_relevant(record: dict[str, Any]) -> bool:
    status = str(record.get("status") or "")
    return status in {
        "received",
        "pending_approval",
        "waiting_for_clarification",
        "approved",
        "running",
        "unknown",
    } or record.get("active") is True


def _phase_from_record(record: dict[str, Any], metadata: dict[str, Any]) -> TimeoutPhase:
    explicit = metadata.get("runtime_timeout_phase") or metadata.get("phase")
    if explicit:
        return _coerce_phase(str(explicit))
    status = str(record.get("status") or "")
    restored = metadata.get("restored_from_journal") is True
    if status == "received":
        return TimeoutPhase.RECEIVED
    if status == "pending_approval":
        return TimeoutPhase.RESTORED_PENDING if restored else TimeoutPhase.APPROVAL_PENDING
    if status == "waiting_for_clarification":
        return TimeoutPhase.RESTORED_PENDING if restored else TimeoutPhase.CLARIFICATION_PENDING
    if status == "approved":
        return TimeoutPhase.QUEUED
    if status == "running" or record.get("active") is True:
        if _browser_metadata(record, metadata):
            return TimeoutPhase.BROWSER_DISPATCHING
        return TimeoutPhase.EXECUTING
    return TimeoutPhase.UNKNOWN


def _browser_metadata(record: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    browser_keys = (
        "requested_url",
        "final_url",
        "browser_runtime",
        "controlled_browser",
        "browser_context_observable",
        "bot_challenge_detected",
    )
    data = {key: metadata[key] for key in browser_keys if key in metadata}
    intent = str(metadata.get("intent") or metadata.get("action") or "")
    if intent in {"open_url", "search_web", "browser_click"}:
        data.setdefault("intent", intent)
    if str(record.get("text") or "").lower().startswith(("open http", "search ")):
        data.setdefault("text_browser_candidate", True)
    return data


def _count_by(decisions: list[RuntimeTimeoutDecision], attr: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for decision in decisions:
        value = getattr(decision, attr)
        key = value.value if isinstance(value, Enum) else str(value)
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _to_plain(value: Any) -> Any:
    if is_dataclass(value):
        return {
            item.name: _to_plain(getattr(value, item.name))
            for item in fields(value)
        }
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, MappingProxyType):
        return _to_plain(dict(value))
    if isinstance(value, dict):
        return {str(key): _to_plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_plain(item) for item in value]
    return value


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return None


def _int_or_zero(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _string_or_none(value: Any) -> str | None:
    return value if isinstance(value, str) and value.strip() else None
