from __future__ import annotations

from collections import OrderedDict
from typing import Any, Iterable, Mapping

from aegis.core.protocol import ProtocolEventType


DEFAULT_ACTION_TIMELINE_LIMIT = 50


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


def _mapped_value(mapping: Mapping[str, Any], key: str) -> Any:
    return mapping[key] if key in mapping else None


def _tool_name(payload: Mapping[str, Any], evidence: Mapping[str, Any], fallback: Any = "executor") -> str:
    for mapping, key in ((payload, "tool"), (evidence, "action")):
        value = _mapped_value(mapping, key)
        if value is not None:
            return str(value)
    return str(fallback)


def project_action_timeline(
    events: Iterable[Mapping[str, Any]],
    *,
    limit: int = DEFAULT_ACTION_TIMELINE_LIMIT,
    session_id: str | None = None,
) -> list[dict[str, Any]]:
    """Build a bounded action lifecycle projection from journal events."""
    records: OrderedDict[str, dict[str, Any]] = OrderedDict()

    for event in sorted(events, key=_event_sort_key):
        if session_id and event.get("session_id") != session_id:
            continue

        event_type = str(event.get("type") or "")
        if event_type not in {
            ProtocolEventType.ACTION_STARTED.value,
            ProtocolEventType.ACTION_COMPLETED.value,
            ProtocolEventType.ACTION_FAILED.value,
            ProtocolEventType.VERIFICATION_PASSED.value,
            ProtocolEventType.VERIFICATION_FAILED.value,
        }:
            continue

        payload = event.get("payload")
        if not isinstance(payload, Mapping):
            continue

        action_id = payload.get("action_id")
        if not action_id:
            continue
        action_key = str(action_id)
        event_time = event.get("timestamp")
        evidence = payload.get("execution_evidence")
        evidence_map = evidence if isinstance(evidence, Mapping) else {}

        record = records.get(action_key)
        if record is None:
            record = {
                "action_id": action_key,
                "tool": _tool_name(payload, evidence_map),
                "status": "active",
                "target": payload.get("target") or evidence_map.get("target"),
                "started_at": event_time,
                "completed_at": None,
                "latency_ms": None,
                "execution_evidence": None,
                "trace_id": event.get("trace_id"),
                "sequence_num": event.get("sequence_num"),
            }
            records[action_key] = record

        record["sequence_num"] = event.get("sequence_num", record.get("sequence_num"))
        record["trace_id"] = event.get("trace_id") or record.get("trace_id")

        if event_type == ProtocolEventType.ACTION_STARTED.value:
            record["tool"] = _tool_name(payload, {}, record.get("tool") if record.get("tool") is not None else "executor")
            record["target"] = payload.get("target") or record.get("target")
            record["started_at"] = event_time or record.get("started_at")
            record["status"] = "active"
        elif event_type == ProtocolEventType.ACTION_COMPLETED.value:
            record["status"] = "success" if bool(payload.get("success", False)) else "error"
            record["completed_at"] = event_time
            record["latency_ms"] = payload.get("latency_ms")
            if isinstance(evidence, Mapping):
                record["execution_evidence"] = dict(evidence)
                record["tool"] = _tool_name({}, evidence, record.get("tool") if record.get("tool") is not None else "executor")
        elif event_type in {
            ProtocolEventType.VERIFICATION_PASSED.value,
            ProtocolEventType.VERIFICATION_FAILED.value,
        }:
            if isinstance(evidence, Mapping):
                record["execution_evidence"] = dict(evidence)
                record["tool"] = _tool_name({}, evidence, record.get("tool") if record.get("tool") is not None else "executor")
                record["target"] = record.get("target") or evidence.get("target")
            if event_type == ProtocolEventType.VERIFICATION_FAILED.value:
                record["status"] = "error"
                record["completed_at"] = record.get("completed_at") or event_time
                record["target"] = record.get("target") or evidence_map.get("target")
            elif event_type == ProtocolEventType.VERIFICATION_PASSED.value and record["status"] == "active":
                record["status"] = "success"
                record["completed_at"] = record.get("completed_at") or event_time
        elif event_type == ProtocolEventType.ACTION_FAILED.value:
            record["status"] = "error"
            record["completed_at"] = event_time
            record["target"] = record.get("target") or payload.get("error") or evidence_map.get("target")
            if isinstance(evidence, Mapping):
                record["execution_evidence"] = dict(evidence)
                record["tool"] = _tool_name({}, evidence, record.get("tool") if record.get("tool") is not None else "executor")

    bounded_limit = max(int(limit), 0)
    if bounded_limit == 0:
        return []
    bounded = list(records.values())[-bounded_limit:]
    return bounded
