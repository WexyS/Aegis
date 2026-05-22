from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from aegis.core.approval_semantics import DecisionStatus
from aegis.core.guard_policy import GuardDecision
from aegis.core.non_executable_projection import (
    project_guard_decision_to_journal_entries,
    project_guard_decision_to_snapshot_patch,
    reconstruct_non_executable_decision_from_journal,
)
from aegis.core.protocol import Component, ProtocolEventType, RuntimeEvent, Severity


SUPPORTED_NON_EXECUTABLE_DECISIONS = {
    DecisionStatus.APPROVAL_REQUIRED,
    DecisionStatus.CLARIFICATION_REQUIRED,
    DecisionStatus.BLOCKED,
}

FORBIDDEN_EVENT_TYPES = {
    ProtocolEventType.ACTION_STARTED.value,
    ProtocolEventType.ACTION_COMPLETED.value,
    ProtocolEventType.ACTION_FAILED.value,
    "ACTION_CANCELLED",
    ProtocolEventType.APPROVAL_REQUIRED.value,
}

FORBIDDEN_PAYLOAD_KEYS = {
    "execution_evidence",
}

FORBIDDEN_TRUTHY_PAYLOAD_KEYS = {
    "verified",
    "success",
    "action_started",
}

COMMAND_STATUS_REPRESENTATION_NOTE = (
    "CommandStatus has pending_approval/blocking states but no dedicated "
    "waiting_for_clarification enum yet; adapter projections expose the "
    "conservative string command_status='waiting_for_clarification' until a "
    "future command lifecycle migration is explicitly scoped."
)


@dataclass(frozen=True)
class NonExecutableEventBatch:
    events: list[RuntimeEvent]
    snapshot_patch: dict[str, Any]
    action_timeline_entries: list[dict[str, Any]]
    replay_state: dict[str, Any]
    command_status_representation_note: str = COMMAND_STATUS_REPRESENTATION_NOTE


def append_non_executable_decision_events_dry(
    batch: NonExecutableEventBatch,
    *,
    event_log: list[RuntimeEvent] | None = None,
) -> list[RuntimeEvent]:
    """Append a non-executable batch to an in-memory event log.

    This is a dry append helper for tests and future wiring shape only. It does
    not touch the runtime journal, websocket bus, or global snapshot.
    """

    target = event_log if event_log is not None else []
    for event in batch.events:
        if event.type in FORBIDDEN_EVENT_TYPES:
            raise ValueError(f"Non-executable adapter cannot append {event.type}")
        _assert_no_execution_shape(event.payload)
        target.append(event)
    return target


def build_non_executable_event_batch(
    guard_decision: GuardDecision,
    *,
    command_id: str,
    trace_id: str,
    causation_id: str | None = None,
    starting_sequence_num: int = 1,
    timestamp_ms: int | None = None,
    span_id: str | None = None,
    action_id: str | None = None,
) -> NonExecutableEventBatch:
    """Build the runtime-owned non-executable event/projection batch.

    This adapter is intentionally pure: it does not call the orchestrator,
    executor, tools, websocket bus, runtime journal, or snapshot mutators.
    Future wiring can call this before dispatch, then append the returned
    events through the canonical ws_bridge/journal path.
    """

    _require_supported(guard_decision)
    if starting_sequence_num < 1:
        raise ValueError("starting_sequence_num must be >= 1")

    stable_causation_id = causation_id or f"{command_id}:guard_decision"
    entries = project_guard_decision_to_journal_entries(
        guard_decision,
        command_id=command_id,
        trace_id=trace_id,
        span_id=span_id,
        causation_id=stable_causation_id,
        sequence_num=starting_sequence_num,
        timestamp=timestamp_ms,
    )

    events: list[RuntimeEvent] = []
    for entry in entries:
        event_type = ProtocolEventType(str(entry["event_type"]))
        if event_type.value in FORBIDDEN_EVENT_TYPES:
            raise ValueError(f"Non-executable adapter cannot create {event_type.value}")

        payload = _runtime_payload_from_entry(entry, action_id=action_id)
        _assert_no_execution_shape(payload)
        events.append(
            RuntimeEvent(
                type=event_type.value,
                timestamp=int(entry["timestamp"]),
                trace_id=str(entry["trace_id"]),
                causation_id=str(entry["causation_id"]),
                span_id=entry.get("span_id"),
                source=Component.GUARD.value,
                severity=Severity.WARNING.value,
                sequence_num=int(entry["sequence_num"]),
                payload=payload,
            )
        )

    snapshot_patch = project_guard_decision_to_snapshot_patch(guard_decision)
    _assert_no_execution_shape(snapshot_patch)

    action_timeline_entries = project_non_executable_events_to_action_timeline(events)
    replay_state = reconstruct_non_executable_decision_from_journal(
        runtime_events_to_journal_entries(events)
    )

    return NonExecutableEventBatch(
        events=events,
        snapshot_patch=snapshot_patch,
        action_timeline_entries=action_timeline_entries,
        replay_state=replay_state,
    )


def project_non_executable_events_to_snapshot(
    events: Iterable[RuntimeEvent | Mapping[str, Any]],
) -> dict[str, Any]:
    """Project non-executable runtime events into a snapshot-compatible patch."""

    replay = reconstruct_non_executable_decision_from_journal(
        runtime_events_to_journal_entries(events)
    )
    patch = {
        "pending_approval": replay["pending_approval"],
        "pending_clarification": replay["pending_clarification"],
        "last_blocked_action": replay["last_blocked_action"],
        "last_guard_decision": replay["last_guard_decision"],
        "command_status": replay["command_status"],
        "terminal_non_executed": replay["terminal_non_executed"],
        "not_executed": True,
        "executed": False,
    }
    if replay["last_guard_decision"]:
        patch["last_risk_level"] = replay["last_guard_decision"].get("risk_level")
    _assert_no_execution_shape(patch)
    return patch


def project_non_executable_events_to_action_timeline(
    events: Iterable[RuntimeEvent | Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Project guard decision events into action timeline entries."""

    entries: list[dict[str, Any]] = []
    for event in sorted((_event_mapping(event) for event in events), key=_event_sort_key):
        event_type = str(event.get("type") or "")
        payload = event.get("payload")
        if not isinstance(payload, Mapping):
            continue

        if event_type == ProtocolEventType.APPROVAL_REQUESTED.value:
            entry = _timeline_base(event, payload)
            entry.update(
                {
                    "timeline_id": str(payload.get("approval_id") or _fallback_timeline_id(event)),
                    "kind": "approval_requested",
                    "status": DecisionStatus.APPROVAL_REQUIRED.value,
                    "terminal": False,
                    "approval_id": payload.get("approval_id"),
                    "approval_request": payload.get("approval_request"),
                    "proposed_action": payload.get("proposed_action"),
                }
            )
            entries.append(entry)
        elif event_type == ProtocolEventType.CLARIFICATION_REQUESTED.value:
            entry = _timeline_base(event, payload)
            entry.update(
                {
                    "timeline_id": str(payload.get("clarification_id") or _fallback_timeline_id(event)),
                    "kind": "clarification_requested",
                    "status": DecisionStatus.CLARIFICATION_REQUIRED.value,
                    "terminal": False,
                    "clarification_id": payload.get("clarification_id"),
                    "clarification_request": payload.get("clarification_request"),
                    "ambiguity_type": payload.get("ambiguity_type"),
                    "question": payload.get("question"),
                    "options": payload.get("options") or [],
                }
            )
            entries.append(entry)
        elif event_type == ProtocolEventType.ACTION_BLOCKED_BY_POLICY.value:
            entry = _timeline_base(event, payload)
            entry.update(
                {
                    "timeline_id": str(payload.get("blocked_id") or _fallback_timeline_id(event)),
                    "kind": "blocked_by_policy",
                    "status": DecisionStatus.BLOCKED.value,
                    "terminal": True,
                    "terminal_non_executed": True,
                    "blocked_id": payload.get("blocked_id"),
                    "blocked_action": payload.get("blocked_action"),
                    "user_message": payload.get("user_message") or payload.get("reason"),
                    "retry_allowed": bool(payload.get("retry_allowed", False)),
                }
            )
            entries.append(entry)

    for entry in entries:
        _assert_no_execution_shape(entry)
    return entries


def runtime_events_to_journal_entries(
    events: Iterable[RuntimeEvent | Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Convert RuntimeEvent values into journal-style entries for replay tests."""

    entries: list[dict[str, Any]] = []
    for event in events:
        data = _event_mapping(event)
        payload = data.get("payload") if isinstance(data.get("payload"), Mapping) else {}
        entries.append(
            {
                "event_type": data.get("type"),
                "type": data.get("type"),
                "timestamp": data.get("timestamp"),
                "command_id": payload.get("command_id"),
                "trace_id": data.get("trace_id") or payload.get("trace_id"),
                "span_id": data.get("span_id"),
                "sequence_num": data.get("sequence_num"),
                "causation_id": data.get("causation_id"),
                "decision_status": payload.get("decision_status"),
                "risk_level": payload.get("risk_level"),
                "policy_rule": payload.get("policy_rule"),
                "reason": payload.get("reason"),
                "not_executed": payload.get("not_executed"),
                "executed": payload.get("executed", False),
                "payload": dict(payload),
            }
        )
    return entries


def _runtime_payload_from_entry(entry: Mapping[str, Any], *, action_id: str | None = None) -> dict[str, Any]:
    payload = dict(entry.get("payload") or {})
    payload.setdefault("command_id", entry["command_id"])
    payload.setdefault("trace_id", entry["trace_id"])
    payload.setdefault("decision_status", entry["decision_status"])
    payload.setdefault("risk_level", entry["risk_level"])
    payload.setdefault("policy_rule", entry["policy_rule"])
    payload.setdefault("reason", entry["reason"])
    payload.setdefault("evidence_refs", entry.get("evidence_refs") or [])
    if action_id is not None:
        payload.setdefault("action_id", action_id)
    payload["not_executed"] = True
    return payload


def _timeline_base(event: Mapping[str, Any], payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "command_id": payload.get("command_id"),
        "trace_id": event.get("trace_id") or payload.get("trace_id"),
        "span_id": event.get("span_id"),
        "action_id": payload.get("action_id"),
        "sequence_num": event.get("sequence_num"),
        "timestamp": event.get("timestamp"),
        "risk_level": payload.get("risk_level"),
        "policy_rule": payload.get("policy_rule"),
        "reason": payload.get("reason"),
        "not_executed": True,
        "executed": False,
        "verified": False,
        "safe_alternatives": _safe_alternatives(payload),
    }


def _safe_alternatives(payload: Mapping[str, Any]) -> list[Any]:
    for key in ("approval_request", "clarification_request", "blocked_action"):
        nested = payload.get(key)
        if isinstance(nested, Mapping):
            value = nested.get("safe_alternatives")
            if isinstance(value, list):
                return value
    value = payload.get("safe_alternatives")
    return list(value) if isinstance(value, list) else []


def _fallback_timeline_id(event: Mapping[str, Any]) -> str:
    return f"{event.get('type')}:{event.get('sequence_num')}"


def _event_mapping(event: RuntimeEvent | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(event, RuntimeEvent):
        return event.to_dict()
    return dict(event)


def _event_sort_key(event: Mapping[str, Any]) -> tuple[int, int]:
    sequence = event.get("sequence_num")
    timestamp = event.get("timestamp")
    try:
        sequence_num = int(sequence)
    except (TypeError, ValueError):
        sequence_num = 0
    try:
        timestamp_num = int(timestamp)
    except (TypeError, ValueError):
        timestamp_num = 0
    return sequence_num, timestamp_num


def _require_supported(decision: GuardDecision) -> None:
    if decision.decision_status not in SUPPORTED_NON_EXECUTABLE_DECISIONS:
        raise ValueError(f"Non-executable runtime adapter does not support {decision.decision_status.value}")


def _assert_no_execution_shape(value: Any) -> None:
    if isinstance(value, Mapping):
        for key in FORBIDDEN_PAYLOAD_KEYS:
            if key in value and value[key] is not None:
                raise ValueError(f"Non-executable payload cannot include {key}")
        for key in FORBIDDEN_TRUTHY_PAYLOAD_KEYS:
            if value.get(key) is True:
                raise ValueError(f"Non-executable payload cannot set {key}=true")
        if value.get("type") in FORBIDDEN_EVENT_TYPES:
            raise ValueError(f"Non-executable adapter cannot create {value.get('type')}")
        for nested in value.values():
            _assert_no_execution_shape(nested)
    elif isinstance(value, list):
        for nested in value:
            _assert_no_execution_shape(nested)
