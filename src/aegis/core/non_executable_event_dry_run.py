from __future__ import annotations

from typing import Any

from aegis.core.approval_semantics import DecisionStatus
from aegis.core.guard_policy import GuardDecision
from aegis.core.non_executable_projection import project_guard_decision_to_journal_entries
from aegis.core.protocol import Component, ProtocolEventType, RuntimeEvent, Severity


NON_EXECUTABLE_DRY_RUN_DECISIONS = {
    DecisionStatus.APPROVAL_REQUIRED,
    DecisionStatus.CLARIFICATION_REQUIRED,
    DecisionStatus.BLOCKED,
}

FORBIDDEN_EXECUTION_EVENT_TYPES = {
    ProtocolEventType.ACTION_STARTED.value,
    ProtocolEventType.ACTION_COMPLETED.value,
    ProtocolEventType.ACTION_FAILED.value,
    "ACTION_CANCELLED",
}

FORBIDDEN_EXECUTION_PAYLOAD_KEYS = {
    "execution_evidence",
}

FORBIDDEN_TRUTHY_PAYLOAD_KEYS = {
    "verified",
    "success",
    "action_started",
}


def build_non_executable_runtime_events(
    guard_decision: GuardDecision,
    *,
    command_id: str,
    trace_id: str,
    causation_id: str | None = None,
    starting_sequence_num: int = 1,
    timestamp_ms: int | None = None,
) -> list[RuntimeEvent]:
    """Build RuntimeEvent-shaped dry-run events for non-executable decisions.

    The helper is intentionally pure: it does not emit to the event bus, append
    to the journal, mutate snapshots, inspect live state, or call tools.
    """

    if guard_decision.decision_status not in NON_EXECUTABLE_DRY_RUN_DECISIONS:
        raise ValueError(f"Non-executable dry-run does not support {guard_decision.decision_status.value}")
    if starting_sequence_num < 1:
        raise ValueError("starting_sequence_num must be >= 1")

    entries = project_guard_decision_to_journal_entries(
        guard_decision,
        command_id=command_id,
        trace_id=trace_id,
        causation_id=causation_id,
        sequence_num=starting_sequence_num,
        timestamp=timestamp_ms,
    )

    events: list[RuntimeEvent] = []
    for entry in entries:
        event_type = ProtocolEventType(str(entry["event_type"]))
        if event_type.value in FORBIDDEN_EXECUTION_EVENT_TYPES:
            raise ValueError(f"Non-executable dry-run cannot create {event_type.value}")

        payload = _runtime_payload_from_entry(entry)
        _assert_payload_does_not_imply_execution(payload)
        events.append(
            RuntimeEvent(
                type=event_type.value,
                timestamp=int(entry["timestamp"]),
                trace_id=str(entry["trace_id"]),
                causation_id=entry.get("causation_id"),
                span_id=entry.get("span_id"),
                source=Component.GUARD.value,
                severity=Severity.WARNING.value,
                sequence_num=int(entry["sequence_num"]),
                payload=payload,
            )
        )

    return events


def _runtime_payload_from_entry(entry: dict[str, Any]) -> dict[str, Any]:
    payload = dict(entry.get("payload") or {})
    payload.setdefault("command_id", entry["command_id"])
    payload.setdefault("trace_id", entry["trace_id"])
    payload.setdefault("decision_status", entry["decision_status"])
    payload.setdefault("risk_level", entry["risk_level"])
    payload.setdefault("policy_rule", entry["policy_rule"])
    payload.setdefault("reason", entry["reason"])
    payload.setdefault("evidence_refs", entry.get("evidence_refs") or [])
    payload["not_executed"] = True
    return payload


def _assert_payload_does_not_imply_execution(value: Any) -> None:
    if isinstance(value, dict):
        for key in FORBIDDEN_EXECUTION_PAYLOAD_KEYS:
            if key in value:
                raise ValueError(f"Non-executable dry-run payload cannot include {key}")
        for key in FORBIDDEN_TRUTHY_PAYLOAD_KEYS:
            if value.get(key) is True:
                raise ValueError(f"Non-executable dry-run payload cannot set {key}=true")
        for nested in value.values():
            _assert_payload_does_not_imply_execution(nested)
    elif isinstance(value, list):
        for nested in value:
            _assert_payload_does_not_imply_execution(nested)
