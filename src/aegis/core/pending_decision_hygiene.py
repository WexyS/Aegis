from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any

from aegis.core.commands import now_ms
from aegis.core.constants import CommandStatus


PENDING_DECISION_HYGIENE_VERSION = "pending-decision-hygiene/1"
DEFAULT_STALE_PENDING_DECISION_MS = 60 * 60 * 1000
MAX_CLASSIFICATION_RECORDS = 50


def build_pending_decision_hygiene_report(
    commands_snapshot: dict[str, Any] | None,
    *,
    generated_at_ms: int | None = None,
    stale_after_ms: int = DEFAULT_STALE_PENDING_DECISION_MS,
    max_records: int = MAX_CLASSIFICATION_RECORDS,
) -> dict[str, Any]:
    """Build a read-only pending decision hygiene report from backend command state.

    This helper intentionally accepts a command lifecycle snapshot instead of an
    ApprovalManager instance so it cannot resolve, deny, grant, or otherwise
    mutate decision lifecycle state.
    """

    generated_at = generated_at_ms if generated_at_ms is not None else now_ms()
    snapshot = deepcopy(commands_snapshot) if isinstance(commands_snapshot, dict) else {}
    pending_approvals = _list_of_dicts(snapshot.get("pending_approvals"))
    pending_clarifications = _list_of_dicts(snapshot.get("pending_clarifications"))

    classifications = [
        _classify_pending_decision(
            record,
            decision_type="approval",
            generated_at_ms=generated_at,
            stale_after_ms=stale_after_ms,
        )
        for record in pending_approvals
    ]
    classifications.extend(
        _classify_pending_decision(
            record,
            decision_type="clarification",
            generated_at_ms=generated_at,
            stale_after_ms=stale_after_ms,
        )
        for record in pending_clarifications
    )

    pending_count = len(classifications)
    restored_count = sum(1 for item in classifications if item["restored"] is True)
    current_session_count = sum(1 for item in classifications if item["current_session"] is True)
    stale_restored_count = sum(
        1 for item in classifications
        if item["restored"] is True and item["staleness"]["stale"] is True
    )
    unknown_age_count = sum(
        1 for item in classifications
        if item["staleness"]["age_source"] == "unknown"
    )
    missing_reference_count = sum(
        1 for item in classifications
        if item["decision_reference_present"] is False
    )
    already_resolved_conflict_count = sum(
        1 for item in classifications
        if "already_resolved_conflict" in item["classes"]
    )
    blocked_non_executable_count = sum(
        1 for item in classifications
        if "blocked_non_executable_historical" in item["classes"]
    )

    decision_type_distribution = Counter(item["decision_type"] for item in classifications)
    source_distribution = Counter(item["restored_source"] for item in classifications)
    risk_distribution = Counter(item["risk_level"] for item in classifications)
    resume_distribution = Counter(item["resume_classification"] for item in classifications)
    policy_unknown_count = sum(1 for item in classifications if item["policy_known"] is False)
    risk_unknown_count = sum(1 for item in classifications if item["risk_known"] is False)

    created_values = [
        int(item["created_at"])
        for item in classifications
        if isinstance(item.get("created_at"), int)
    ]
    updated_values = [
        int(item["updated_at"])
        for item in classifications
        if isinstance(item.get("updated_at"), int)
    ]

    status = "warning" if pending_count else "ok"
    return {
        "scan_version": PENDING_DECISION_HYGIENE_VERSION,
        "read_only": True,
        "status": status,
        "source_of_truth": "backend_command_lifecycle_snapshot",
        "generated_at_ms": generated_at,
        "pending_count": pending_count,
        "approval_count": decision_type_distribution.get("approval", 0),
        "clarification_count": decision_type_distribution.get("clarification", 0),
        "restored_unresolved_count": restored_count,
        "current_session_pending_count": current_session_count,
        "stale_restored_unresolved_count": stale_restored_count,
        "unknown_age_count": unknown_age_count,
        "missing_decision_reference_count": missing_reference_count,
        "already_resolved_conflict_count": already_resolved_conflict_count,
        "blocked_non_executable_historical_count": blocked_non_executable_count,
        "resumable_count": resume_distribution.get("resumable", 0),
        "state_only_count": resume_distribution.get("state_only", 0),
        "non_executing_count": resume_distribution.get("non_executing", 0),
        "unknown_resume_count": resume_distribution.get("unknown", 0),
        "policy_unknown_count": policy_unknown_count,
        "risk_unknown_count": risk_unknown_count,
        "decision_type_distribution": dict(sorted(decision_type_distribution.items())),
        "source_distribution": dict(sorted(source_distribution.items())),
        "risk_distribution": dict(sorted(risk_distribution.items())),
        "resume_distribution": dict(sorted(resume_distribution.items())),
        "top_command_texts": _top_counts(item["text"] for item in classifications),
        "top_actions": _top_counts(item["action"] for item in classifications if item["action"]),
        "oldest_created_at": min(created_values) if created_values else None,
        "oldest_updated_at": min(updated_values) if updated_values else None,
        "thresholds": {
            "stale_after_ms": stale_after_ms,
            "age_sources": ["created_at", "updated_at"],
            "restored_at_is_original_age": False,
        },
        "recommendation": (
            "Operator review required for pending restored decisions; maintenance scan performed no "
            "mutation and bulk hygiene actions are not available in this sprint."
            if pending_count
            else "No pending approval or clarification decisions were present in the backend lifecycle snapshot."
        ),
        "guidance": [
            "Restored pending decisions are backend command lifecycle truth.",
            "No decisions were resolved by this scan.",
            "No local/frontend deletion was performed.",
            "No approval was granted by this hygiene diagnostic.",
            "Future bulk deny or quarantine requires explicit operator confirmation and backend lifecycle handling.",
        ],
        "safety": {
            "no_mutation_performed": True,
            "no_auto_resolution": True,
            "no_auto_approval": True,
            "no_auto_deny": True,
            "bulk_action_available": False,
            "frontend_delete_allowed": False,
            "approval_grant_exposed": False,
            "journal_mutated": False,
            "operator_confirmation_required_for_bulk_hygiene": True,
        },
        "actions_performed": [],
        "mutation_performed": False,
        "classifications": classifications[:max_records],
        "omitted_classification_count": max(0, len(classifications) - max_records),
    }


def _classify_pending_decision(
    record: dict[str, Any],
    *,
    decision_type: str,
    generated_at_ms: int,
    stale_after_ms: int,
) -> dict[str, Any]:
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    status = str(record.get("status") or "")
    expected_status = (
        CommandStatus.PENDING_APPROVAL.value
        if decision_type == "approval"
        else CommandStatus.WAITING_FOR_CLARIFICATION.value
    )
    command_id = _string_or_none(record.get("command_id"))
    decision_key = "approval_id" if decision_type == "approval" else "clarification_id"
    decision_reference = _string_or_none(metadata.get(decision_key)) or command_id
    restored = metadata.get("restored_from_journal") is True
    staleness = _staleness(record, generated_at_ms=generated_at_ms, stale_after_ms=stale_after_ms)
    resolution_status = _resolution_status(metadata, decision_type=decision_type)
    resume_classification = _resume_classification(record, metadata, decision_type=decision_type)
    policy_rule = _string_or_none(metadata.get("policy_rule"))
    risk_level = _string_or_none(record.get("risk_level")) or "unknown"
    action = _action_name(record, metadata)
    classes = _classes_for_decision(
        restored=restored,
        staleness=staleness,
        status=status,
        expected_status=expected_status,
        resolution_status=resolution_status,
        decision_reference=decision_reference,
        resume_classification=resume_classification,
        metadata=metadata,
        policy_rule=policy_rule,
    )

    return {
        "command_id": command_id,
        "decision_type": decision_type,
        "status": status,
        "expected_pending_status": expected_status,
        "text": str(record.get("text") or ""),
        "risk_level": risk_level,
        "risk_known": risk_level != "unknown",
        "trace_id": _string_or_none(record.get("trace_id")),
        "created_at": _int_or_none(record.get("created_at")),
        "updated_at": _int_or_none(record.get("updated_at")),
        "restored": restored,
        "current_session": not restored,
        "restored_source": _string_or_none(metadata.get("restored_source")) or (
            "restored_unknown_source" if restored else "current_session"
        ),
        "restored_at": _int_or_none(metadata.get("restored_at")),
        "source_snapshot_sequence": _int_or_none(metadata.get("source_snapshot_sequence")),
        "staleness": staleness,
        "decision_reference_present": bool(decision_reference),
        "decision_reference_key": decision_key if decision_reference else None,
        "decision_reference": decision_reference,
        "resolution_status": resolution_status,
        "resume_classification": resume_classification,
        "resume_allowed": metadata.get("resume_allowed") if "resume_allowed" in metadata else "unknown",
        "policy_rule": policy_rule or "unknown",
        "policy_known": bool(policy_rule),
        "action": action,
        "classes": classes,
    }


def _staleness(
    record: dict[str, Any],
    *,
    generated_at_ms: int,
    stale_after_ms: int,
) -> dict[str, Any]:
    created_at = _int_or_none(record.get("created_at"))
    updated_at = _int_or_none(record.get("updated_at"))
    if created_at is not None:
        age_source = "created_at"
        age_basis = created_at
    elif updated_at is not None:
        age_source = "updated_at"
        age_basis = updated_at
    else:
        return {
            "age_source": "unknown",
            "age_ms": None,
            "stale": None,
            "reason": "created_at/updated_at unavailable; restored_at is restore time only",
        }

    age_ms = max(0, generated_at_ms - age_basis)
    return {
        "age_source": age_source,
        "age_ms": age_ms,
        "stale": age_ms >= stale_after_ms,
        "reason": f"staleness derived from {age_source}",
    }


def _resolution_status(metadata: dict[str, Any], *, decision_type: str) -> str:
    key = (
        "approval_resolution_status"
        if decision_type == "approval"
        else "clarification_resolution_status"
    )
    default = "waiting_for_approval" if decision_type == "approval" else "waiting_for_clarification"
    return _string_or_none(metadata.get(key)) or default


def _resume_classification(
    record: dict[str, Any],
    metadata: dict[str, Any],
    *,
    decision_type: str,
) -> str:
    if decision_type == "clarification":
        return "state_only"
    if metadata.get("resume_allowed") is True:
        return "resumable"
    if metadata.get("resume_allowed") is False:
        policy_rule = str(metadata.get("policy_rule") or "").lower()
        text = str(record.get("text") or "").lower()
        if (
            metadata.get("not_executed") is True
            or metadata.get("completed_without_execution") is True
            or "quarantine" in policy_rule
            or "quarantined" in policy_rule
            or "click" in text
        ):
            return "non_executing"
        return "state_only"
    return "unknown"


def _classes_for_decision(
    *,
    restored: bool,
    staleness: dict[str, Any],
    status: str,
    expected_status: str,
    resolution_status: str,
    decision_reference: str | None,
    resume_classification: str,
    metadata: dict[str, Any],
    policy_rule: str | None,
) -> list[str]:
    classes: list[str] = []
    if restored:
        classes.append("restored_unresolved")
        if staleness.get("stale") is True:
            classes.append("stale_restored_unresolved")
        elif staleness.get("age_source") == "unknown":
            classes.append("unknown_age_restored_unresolved")
    else:
        classes.append("current_session_pending")

    if not decision_reference:
        classes.append("missing_decision_reference")
    if status and status != expected_status:
        classes.append("already_resolved_conflict")
    if resolution_status not in {"waiting_for_approval", "waiting_for_clarification", "pending"}:
        classes.append("already_resolved_conflict")

    policy = (policy_rule or "").lower()
    if (
        resume_classification == "non_executing"
        or metadata.get("not_executed") is True
        or metadata.get("completed_without_execution") is True
        or "quarantine" in policy
        or "quarantined" in policy
    ):
        classes.append("blocked_non_executable_historical")

    return sorted(set(classes))


def _action_name(record: dict[str, Any], metadata: dict[str, Any]) -> str | None:
    for key in ("intent", "action", "tool", "planned_action", "kind"):
        value = _string_or_none(metadata.get(key))
        if value:
            return value
    text = _string_or_none(record.get("text"))
    if not text:
        return None
    normalized = text.strip().lower()
    if normalized.startswith("open "):
        return "open_app"
    if normalized.startswith("create file "):
        return "create_file"
    return None


def _top_counts(values: Any, *, limit: int = 5) -> list[dict[str, Any]]:
    counter = Counter(value for value in values if isinstance(value, str) and value.strip())
    return [
        {"value": value, "count": count}
        for value, count in counter.most_common(limit)
    ]


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _string_or_none(value: Any) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return None
