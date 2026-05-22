from __future__ import annotations

from typing import Any

from aegis.core.approval_semantics import DecisionStatus
from aegis.core.constants import RiskLevel
from aegis.core.guard_policy import GuardDecision


NON_EXECUTABLE_DECISIONS = {
    DecisionStatus.APPROVAL_REQUIRED,
    DecisionStatus.CLARIFICATION_REQUIRED,
    DecisionStatus.BLOCKED,
}


def project_guard_decision_to_journal_entries(
    decision: GuardDecision,
    *,
    command_id: str | None = None,
    trace_id: str | None = None,
    span_id: str | None = None,
    causation_id: str | None = None,
    sequence_num: int | None = None,
    timestamp: int | None = None,
) -> list[dict[str, Any]]:
    """Project a non-executable guard decision to journal-style dicts.

    This helper is intentionally pure: it does not append to the runtime
    journal, emit protocol events, inspect OS state, or call tools.
    """

    _require_non_executable(decision)
    context = _projection_context(
        decision,
        command_id=command_id,
        trace_id=trace_id,
        span_id=span_id,
        causation_id=causation_id,
    )
    classified = _journal_entry(
        "COMMAND_CLASSIFIED",
        decision,
        context,
        sequence_num=sequence_num,
        timestamp=timestamp,
        payload={
            "command_id": context["command_id"],
            "trace_id": context["trace_id"],
            "decision_status": decision.decision_status.value,
            "risk_level": decision.risk_level.value,
            "policy_rule": decision.policy_rule,
            "reason": decision.reason,
            "not_executed": True,
            "guard_decision": _guard_decision_summary(decision),
            "requires_approval": decision.requires_approval,
            "requires_clarification": decision.requires_clarification,
            "blocked": decision.blocked,
        },
    )

    if decision.decision_status == DecisionStatus.APPROVAL_REQUIRED:
        request = _require_payload(decision.approval_request, "approval_request")
        return [
            classified,
            _journal_entry(
                "APPROVAL_REQUESTED",
                decision,
                context,
                sequence_num=_next_sequence(sequence_num, 1),
                timestamp=timestamp,
                payload={
                    "command_id": context["command_id"],
                    "trace_id": context["trace_id"],
                    "approval_request": _dump(request),
                    "approval_id": request.approval_id,
                    "proposed_action": _dump(request.proposed_action),
                    "normalized_params": request.normalized_params,
                    "risk_level": request.risk_level.value,
                    "reason": request.reason,
                    "approval_scope": request.approval_scope.value,
                    "required_confirmation_mode": request.required_confirmation_mode.value,
                    "expected_effect": request.expected_effect,
                    "possible_side_effects": request.possible_side_effects,
                    "rollback_note": request.rollback_note,
                    "evidence_refs": [_dump(ref) for ref in request.evidence_refs],
                    "expires_at": request.expires_at.isoformat() if request.expires_at else None,
                    "approval_status": request.status.value,
                    "not_executed": True,
                },
            ),
            _journal_entry(
                "COMMAND_WAITING_FOR_APPROVAL",
                decision,
                context,
                sequence_num=_next_sequence(sequence_num, 2),
                timestamp=timestamp,
                payload={
                    "command_id": context["command_id"],
                    "trace_id": context["trace_id"],
                    "approval_id": request.approval_id,
                    "command_status": "waiting_for_approval",
                    "blocked_execution": True,
                    "executed": False,
                    "not_executed": True,
                },
            ),
        ]

    if decision.decision_status == DecisionStatus.CLARIFICATION_REQUIRED:
        request = _require_payload(decision.clarification_request, "clarification_request")
        return [
            classified,
            _journal_entry(
                "CLARIFICATION_REQUESTED",
                decision,
                context,
                sequence_num=_next_sequence(sequence_num, 1),
                timestamp=timestamp,
                payload={
                    "command_id": context["command_id"],
                    "trace_id": context["trace_id"],
                    "clarification_request": _dump(request),
                    "clarification_id": request.clarification_id,
                    "original_user_text": request.original_user_text,
                    "ambiguity_type": request.ambiguity_type,
                    "question": request.question,
                    "options": [_dump(option) for option in request.options],
                    "recommended_default": _dump(request.recommended_default) if request.recommended_default else None,
                    "blocked_until_answer": request.blocked_until_answer,
                    "expires_at": request.expires_at.isoformat() if request.expires_at else None,
                    "not_executed": True,
                },
            ),
            _journal_entry(
                "COMMAND_WAITING_FOR_CLARIFICATION",
                decision,
                context,
                sequence_num=_next_sequence(sequence_num, 2),
                timestamp=timestamp,
                payload={
                    "command_id": context["command_id"],
                    "trace_id": context["trace_id"],
                    "clarification_id": request.clarification_id,
                    "command_status": "waiting_for_clarification",
                    "blocked_execution": True,
                    "executed": False,
                    "not_executed": True,
                },
            ),
        ]

    action = _require_payload(decision.blocked_action, "blocked_action")
    return [
        classified,
        _journal_entry(
            "ACTION_BLOCKED_BY_POLICY",
            decision,
            context,
            sequence_num=_next_sequence(sequence_num, 1),
            timestamp=timestamp,
            payload={
                "command_id": context["command_id"],
                "trace_id": context["trace_id"],
                "blocked_action": _dump(action),
                "blocked_id": action.blocked_id,
                "source_intent": _dump(action.source_intent),
                "policy_rule": action.policy_rule,
                "risk_level": action.risk_level.value,
                "reason": action.reason,
                "user_message": action.user_message,
                "retry_allowed": action.retry_allowed,
                "safe_alternatives": [_dump(alternative) for alternative in action.safe_alternatives],
                "terminal_non_executed": True,
                "not_executed": True,
            },
        ),
        _journal_entry(
            "COMMAND_BLOCKED",
            decision,
            context,
            sequence_num=_next_sequence(sequence_num, 2),
            timestamp=timestamp,
            payload={
                "command_id": context["command_id"],
                "trace_id": context["trace_id"],
                "blocked_id": action.blocked_id,
                "command_status": "blocked",
                "terminal": True,
                "terminal_non_executed": True,
                "executed": False,
                "not_executed": True,
            },
        ),
    ]


def project_guard_decision_to_snapshot_patch(decision: GuardDecision) -> dict[str, Any]:
    _require_non_executable(decision)
    patch = {
        "last_guard_decision": _guard_decision_summary(decision),
        "last_risk_level": decision.risk_level.value,
        "not_executed": True,
    }
    if decision.decision_status == DecisionStatus.APPROVAL_REQUIRED:
        request = _require_payload(decision.approval_request, "approval_request")
        patch.update(
            {
                "pending_approval": _dump(request),
                "pending_clarification": None,
                "last_blocked_action": None,
                "command_status": "waiting_for_approval",
                "terminal_non_executed": False,
            }
        )
        return patch
    if decision.decision_status == DecisionStatus.CLARIFICATION_REQUIRED:
        request = _require_payload(decision.clarification_request, "clarification_request")
        patch.update(
            {
                "pending_approval": None,
                "pending_clarification": _dump(request),
                "last_blocked_action": None,
                "command_status": "waiting_for_clarification",
                "terminal_non_executed": False,
            }
        )
        return patch

    action = _require_payload(decision.blocked_action, "blocked_action")
    patch.update(
        {
            "pending_approval": None,
            "pending_clarification": None,
            "last_blocked_action": _dump(action),
            "command_status": "blocked",
            "terminal_non_executed": True,
        }
    )
    return patch


def project_guard_decision_to_timeline_entry(decision: GuardDecision) -> dict[str, Any]:
    _require_non_executable(decision)
    base = {
        "status": decision.decision_status.value,
        "risk_level": decision.risk_level.value,
        "policy_rule": decision.policy_rule,
        "reason": decision.reason,
        "not_executed": True,
        "executed": False,
        "verified": False,
        "safe_alternatives": [_dump(alternative) for alternative in decision.safe_alternatives],
    }
    if decision.decision_status == DecisionStatus.APPROVAL_REQUIRED:
        request = _require_payload(decision.approval_request, "approval_request")
        base.update(
            {
                "kind": "approval_requested",
                "terminal": False,
                "approval_request": _dump(request),
                "approval_id": request.approval_id,
                "proposed_action": _dump(request.proposed_action),
            }
        )
        return base
    if decision.decision_status == DecisionStatus.CLARIFICATION_REQUIRED:
        request = _require_payload(decision.clarification_request, "clarification_request")
        base.update(
            {
                "kind": "clarification_requested",
                "terminal": False,
                "clarification_request": _dump(request),
                "clarification_id": request.clarification_id,
                "ambiguity_type": request.ambiguity_type,
                "question": request.question,
                "options": [_dump(option) for option in request.options],
            }
        )
        return base

    action = _require_payload(decision.blocked_action, "blocked_action")
    base.update(
        {
            "kind": "blocked_by_policy",
            "terminal": True,
            "terminal_non_executed": True,
            "blocked_action": _dump(action),
            "blocked_id": action.blocked_id,
            "user_message": action.user_message,
            "retry_allowed": action.retry_allowed,
        }
    )
    return base


def reconstruct_non_executable_decision_from_journal(entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Reconstruct non-executable projection state from journal-style entries.

    Ordering is based on journal order after stable sequence sorting, not
    timestamps. Replay does not execute or approve anything.
    """

    ordered = sorted(enumerate(entries), key=lambda item: (item[1].get("sequence_num") is None, item[1].get("sequence_num") or item[0], item[0]))
    state: dict[str, Any] = {
        "pending_approval": None,
        "pending_clarification": None,
        "last_blocked_action": None,
        "last_guard_decision": None,
        "command_status": None,
        "terminal_non_executed": False,
        "executed": False,
        "auto_approved": False,
        "journal_order": [],
    }
    for _, entry in ordered:
        event_type = entry.get("event_type")
        state["journal_order"].append(event_type)
        payload = dict(entry.get("payload") or {})
        if event_type == "COMMAND_CLASSIFIED":
            state["last_guard_decision"] = payload.get("guard_decision")
        elif event_type == "APPROVAL_REQUESTED":
            state["pending_approval"] = payload
            state["command_status"] = "waiting_for_approval"
        elif event_type == "CLARIFICATION_REQUESTED":
            state["pending_clarification"] = payload
            state["command_status"] = "waiting_for_clarification"
        elif event_type == "ACTION_BLOCKED_BY_POLICY":
            state["last_blocked_action"] = payload
            state["command_status"] = "blocked"
            state["terminal_non_executed"] = True
        elif event_type == "COMMAND_WAITING_FOR_APPROVAL":
            state["command_status"] = "waiting_for_approval"
        elif event_type == "COMMAND_WAITING_FOR_CLARIFICATION":
            state["command_status"] = "waiting_for_clarification"
        elif event_type == "COMMAND_BLOCKED":
            state["command_status"] = "blocked"
            state["terminal_non_executed"] = True
    return state


def _require_non_executable(decision: GuardDecision) -> None:
    if decision.decision_status not in NON_EXECUTABLE_DECISIONS:
        raise ValueError(f"Non-executable projection does not support {decision.decision_status.value}")


def _projection_context(
    decision: GuardDecision,
    *,
    command_id: str | None,
    trace_id: str | None,
    span_id: str | None,
    causation_id: str | None,
) -> dict[str, Any]:
    payload = decision.approval_request or decision.clarification_request or decision.blocked_action
    return {
        "command_id": command_id or getattr(payload, "command_id", "command-policy"),
        "trace_id": trace_id or getattr(payload, "trace_id", "trace-policy"),
        "span_id": span_id or getattr(payload, "span_id", None),
        "causation_id": causation_id,
    }


def _journal_entry(
    event_type: str,
    decision: GuardDecision,
    context: dict[str, Any],
    *,
    sequence_num: int | None,
    timestamp: int | None = None,
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "event_type": event_type,
        "type": event_type,
        "timestamp": 0 if timestamp is None else timestamp,
        "command_id": context["command_id"],
        "trace_id": context["trace_id"],
        "span_id": context["span_id"],
        "sequence_num": sequence_num,
        "causation_id": context["causation_id"],
        "decision_status": decision.decision_status.value,
        "risk_level": decision.risk_level.value,
        "policy_rule": decision.policy_rule,
        "reason": decision.reason,
        "user_message": decision.reason,
        "evidence_refs": _evidence_refs(decision),
        "not_executed": True,
        "executed": False,
        "payload": payload,
    }


def _guard_decision_summary(decision: GuardDecision) -> dict[str, Any]:
    return {
        "decision_status": decision.decision_status.value,
        "risk_level": decision.risk_level.value,
        "reason": decision.reason,
        "policy_rule": decision.policy_rule,
        "requires_approval": decision.requires_approval,
        "requires_clarification": decision.requires_clarification,
        "blocked": decision.blocked,
        "evidence_required": decision.evidence_required,
        "rollback_required": decision.rollback_required,
        "safe_alternatives": [_dump(alternative) for alternative in decision.safe_alternatives],
    }


def _evidence_refs(decision: GuardDecision) -> list[dict[str, Any]]:
    if decision.approval_request:
        return [_dump(ref) for ref in decision.approval_request.evidence_refs]
    if decision.blocked_action:
        return [_dump(ref) for ref in decision.blocked_action.evidence_refs]
    return []


def _next_sequence(sequence_num: int | None, offset: int) -> int | None:
    if sequence_num is None:
        return None
    return sequence_num + offset


def _require_payload(value: Any, field_name: str) -> Any:
    if value is None:
        raise ValueError(f"GuardDecision missing {field_name}")
    return value


def _dump(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return value
