from __future__ import annotations

from collections import Counter
from typing import Any, Iterable, Mapping

from aegis.core.action_timeline import project_action_timeline
from aegis.core.protocol import ProtocolEventType


ACTION_EVENT_TYPES = {
    ProtocolEventType.ACTION_STARTED.value,
    ProtocolEventType.ACTION_COMPLETED.value,
    ProtocolEventType.ACTION_FAILED.value,
}


def audit_action_evidence(
    events: Iterable[Mapping[str, Any]],
    *,
    limit: int = 50,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Read-only evidence quality report derived from action lifecycle events."""
    action_events = [
        event
        for event in events
        if str(event.get("type") or "") in ACTION_EVENT_TYPES
        and (not session_id or event.get("session_id") == session_id)
    ]
    timeline = project_action_timeline(action_events, limit=limit, session_id=session_id)

    status_counts = Counter(str(item.get("status") or "unknown") for item in timeline)
    verification_counts: Counter[str] = Counter()
    missing_evidence_count = 0
    evidence_backed_count = 0

    for item in timeline:
        evidence = item.get("execution_evidence")
        status = str(item.get("status") or "")
        if isinstance(evidence, Mapping):
            evidence_backed_count += 1
            verification_counts[str(evidence.get("verification_state") or "unverified")] += 1
        elif status in {"success", "error"}:
            missing_evidence_count += 1
            verification_counts["missing"] += 1

    latest_sequence = max(
        (int(item.get("sequence_num") or 0) for item in timeline),
        default=0,
    )
    completed_or_failed = status_counts.get("success", 0) + status_counts.get("error", 0)
    status = "ok" if missing_evidence_count == 0 else "warning"

    return {
        "scan_version": "evidence-audit/1",
        "read_only": True,
        "status": status,
        "action_event_count": len(action_events),
        "action_count": len(timeline),
        "completed_or_failed_count": completed_or_failed,
        "active_count": status_counts.get("active", 0),
        "success_count": status_counts.get("success", 0),
        "error_count": status_counts.get("error", 0),
        "evidence_backed_count": evidence_backed_count,
        "missing_evidence_count": missing_evidence_count,
        "verification_counts": dict(sorted(verification_counts.items())),
        "latest_sequence_num": latest_sequence,
        "limit": max(int(limit), 0),
    }
