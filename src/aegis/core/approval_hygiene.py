from __future__ import annotations

from collections import Counter
from typing import Any

from aegis.core.constants import CommandStatus


HYGIENE_CONFIRMATION_PHRASE = "DENY RESTORED APPROVALS"
HYGIENE_OPERATOR_ACTION = "restored_pending_hygiene_deny"
HYGIENE_SCOPE = "selected_restored_approvals"


GRANT_LIKE_VALUES = {"grant", "granted", "approve", "approved"}
GRANT_LIKE_KEYS = {"grant", "approve", "approved"}


def reject_grant_like_payload(payload: dict[str, Any]) -> str | None:
    for key in GRANT_LIKE_KEYS:
        if key in payload:
            return f"Grant-like field is not allowed in approval hygiene: {key}"
    for key in ("decision", "action", "operator_action"):
        value = str(payload.get(key) or "").strip().lower()
        if value in GRANT_LIKE_VALUES:
            return f"Grant-like value is not allowed in approval hygiene: {key}={value}"
    return None


def approval_hygiene_resolution_metadata(
    *,
    reason: str,
    selected_count: int,
    restored_only: bool,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "operator_action": HYGIENE_OPERATOR_ACTION,
        "bulk_hygiene": True,
        "hygiene_scope": HYGIENE_SCOPE,
        "hygiene_reason": reason,
        "selected_count": selected_count,
        "restored_only": restored_only,
        "not_executed": True,
        "completed_without_execution": True,
        "source": "operator_hygiene",
    }
    if idempotency_key:
        metadata["hygiene_idempotency_key"] = idempotency_key
    return metadata


def build_approval_hygiene_preview(
    commands_snapshot: dict[str, Any] | None,
    approval_ids: list[str] | None = None,
    *,
    restored_only: bool = True,
    include_current_session: bool = False,
) -> dict[str, Any]:
    snapshot = commands_snapshot if isinstance(commands_snapshot, dict) else {}
    pending_approvals = _list_of_dicts(snapshot.get("pending_approvals"))
    records = _list_of_dicts(snapshot.get("records"))
    all_approvals = _records_by_approval_id([*records, *pending_approvals])

    requested_ids = _normalize_ids(approval_ids)
    if requested_ids:
        candidate_ids = requested_ids
    else:
        candidate_ids = [
            approval_id
            for approval_id, record in all_approvals.items()
            if record.get("status") == CommandStatus.PENDING_APPROVAL.value
        ]

    duplicate_ids = _duplicate_ids(approval_ids or [])
    items = [
        _preview_item(
            approval_id,
            all_approvals.get(approval_id),
            restored_only=restored_only,
            include_current_session=include_current_session,
            duplicate=approval_id in duplicate_ids,
        )
        for approval_id in candidate_ids
    ]
    eligible_items = [item for item in items if item["eligible"] is True]
    ineligible_items = [item for item in items if item["eligible"] is False]
    warnings = [
        {
            "approval_id": item["approval_id"],
            "reason": item["ineligible_reason"],
        }
        for item in ineligible_items
    ]

    return {
        "read_only": True,
        "mutation_performed": False,
        "approval_grant_exposed": False,
        "restored_only": restored_only,
        "include_current_session": include_current_session,
        "requested_count": len(candidate_ids),
        "eligible_count": len(eligible_items),
        "ineligible_count": len(ineligible_items),
        "restored_count": sum(1 for item in items if item["restored"] is True),
        "current_session_count": sum(1 for item in items if item["current_session"] is True),
        "top_command_texts": _top_counts(item["text"] for item in eligible_items),
        "items": items,
        "warnings": warnings,
    }


def _preview_item(
    approval_id: str,
    record: dict[str, Any] | None,
    *,
    restored_only: bool,
    include_current_session: bool,
    duplicate: bool,
) -> dict[str, Any]:
    if not record:
        return {
            "approval_id": approval_id,
            "command_id": None,
            "eligible": False,
            "ineligible_reason": "missing_approval_id",
            "restored": False,
            "current_session": False,
            "status": "missing",
            "text": "",
            "risk_level": "unknown",
            "source": "unknown",
        }

    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    restored = metadata.get("restored_from_journal") is True
    status = str(record.get("status") or "")
    reason = _ineligible_reason(
        record,
        metadata,
        restored=restored,
        status=status,
        restored_only=restored_only,
        include_current_session=include_current_session,
        duplicate=duplicate,
    )
    return {
        "approval_id": approval_id,
        "command_id": record.get("command_id"),
        "eligible": reason is None,
        "ineligible_reason": reason,
        "restored": restored,
        "current_session": not restored,
        "status": status,
        "text": str(record.get("text") or ""),
        "risk_level": str(record.get("risk_level") or "unknown"),
        "source": str(metadata.get("restored_source") or ("current_session" if not restored else "unknown")),
        "source_snapshot_sequence": metadata.get("source_snapshot_sequence"),
        "resume_allowed": metadata.get("resume_allowed") if "resume_allowed" in metadata else "unknown",
        "approval_resolution_status": metadata.get("approval_resolution_status"),
    }


def _ineligible_reason(
    record: dict[str, Any],
    metadata: dict[str, Any],
    *,
    restored: bool,
    status: str,
    restored_only: bool,
    include_current_session: bool,
    duplicate: bool,
) -> str | None:
    if duplicate:
        return "duplicate_approval_id"
    if not record.get("command_id"):
        return "missing_command_id"
    if status != CommandStatus.PENDING_APPROVAL.value:
        resolution = str(metadata.get("approval_resolution_status") or "")
        if status == CommandStatus.REJECTED.value and resolution == "approval_denied":
            return "already_denied"
        if resolution == "approval_granted":
            return "already_granted"
        return "already_resolved"
    if restored_only and not restored:
        return "current_session_excluded"
    if not include_current_session and not restored:
        return "current_session_excluded"
    return None


def _records_by_approval_id(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for record in records:
        metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
        approval_id = metadata.get("approval_id") or record.get("command_id")
        if isinstance(approval_id, str) and approval_id:
            by_id[approval_id] = record
    return by_id


def _normalize_ids(values: list[str] | None) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values or []:
        if not isinstance(value, str):
            continue
        approval_id = value.strip()
        if not approval_id or approval_id in seen:
            continue
        seen.add(approval_id)
        result.append(approval_id)
    return result


def _duplicate_ids(values: list[str]) -> set[str]:
    counts = Counter(value.strip() for value in values if isinstance(value, str) and value.strip())
    return {value for value, count in counts.items() if count > 1}


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _top_counts(values: Any, *, limit: int = 5) -> list[dict[str, Any]]:
    counter = Counter(value for value in values if isinstance(value, str) and value.strip())
    return [
        {"value": value, "count": count}
        for value, count in counter.most_common(limit)
    ]
