from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any

from aegis.core.commands import ApprovalManager, get_approval_manager
from aegis.core.constants import CommandStatus
from aegis.core.event_journal import get_runtime_journal
from aegis.core.pending_decision_hygiene import build_pending_decision_hygiene_report
from aegis.core.protocol import Component, ProtocolEventType, Severity, create_event


RESTORED_EXECUTABLE_APPROVAL_CONFIRMATION = (
    "CONFIRM_CANCEL_RESTORED_EXECUTABLE_APPROVALS_NO_GRANT_NO_EXECUTE"
)
RESTORED_EXECUTABLE_APPROVAL_DISPOSITION = "operator_cancelled_restored_executable"
ALLOWED_RESTORED_EXECUTABLE_COMMAND_TEXTS = frozenset(
    {
        "open notepad",
        "create file scratch/new.txt",
    }
)
RESTORED_APPROVAL_RESOLUTION_MANIFEST_VERSION = "restored-approval-resolution/1"


def build_restored_executable_approval_resolution_manifest(
    commands_snapshot: dict[str, Any] | None,
    *,
    approval_ids: list[str] | None = None,
    allowed_command_texts: set[str] | frozenset[str] = ALLOWED_RESTORED_EXECUTABLE_COMMAND_TEXTS,
) -> dict[str, Any]:
    """Build a read-only manifest for restored executable approval cleanup."""

    snapshot = deepcopy(commands_snapshot) if isinstance(commands_snapshot, dict) else {}
    selected_ids = [str(item) for item in approval_ids] if approval_ids is not None else None
    allowed_texts = {str(item).strip().lower() for item in allowed_command_texts}
    hygiene = build_pending_decision_hygiene_report(snapshot)
    classifications = [
        item
        for item in hygiene.get("classifications", [])
        if isinstance(item, dict) and item.get("decision_type") == "approval"
    ]
    pending_ids = [
        str(item.get("decision_reference") or "")
        for item in classifications
        if item.get("decision_reference")
    ]
    target_ids = selected_ids if selected_ids is not None else pending_ids
    target_id_set = set(target_ids)
    items = []
    selected_seen: set[str] = set()

    for classification in classifications:
        approval_id = str(classification.get("decision_reference") or "")
        if selected_ids is not None and approval_id not in target_id_set:
            continue
        selected_seen.add(approval_id)
        normalized_text = str(classification.get("text") or "").strip().lower()
        blockers: list[str] = []
        if classification.get("restored") is not True:
            blockers.append("current_session_decision_not_in_restored_scope")
        if classification.get("classification") != "restored_unresolved_executable":
            blockers.append("decision_is_not_restored_unresolved_executable")
        if normalized_text not in allowed_texts:
            blockers.append("command_text_outside_operator_resolution_scope")

        would_resolve = not blockers
        items.append(
            {
                "approval_id": approval_id,
                "command_id": classification.get("command_id"),
                "text": classification.get("text"),
                "normalized_text": normalized_text,
                "source_event_reference": classification.get("source_event_reference"),
                "classification": classification.get("classification"),
                "executable": classification.get("executable") is True,
                "restored": classification.get("restored") is True,
                "current_session": classification.get("current_session") is True,
                "staleness": classification.get("staleness"),
                "allowed_scope_match": normalized_text in allowed_texts,
                "would_resolve": would_resolve,
                "resolution_disposition": RESTORED_EXECUTABLE_APPROVAL_DISPOSITION,
                "reason": (
                    "explicit operator lifecycle cancellation for restored non-current executable approval"
                    if would_resolve
                    else "blocked from restored executable operator resolution"
                ),
                "blockers": blockers,
            }
        )

    missing_selected_ids = sorted(
        item for item in target_id_set if item and item not in selected_seen
    )
    if selected_ids is not None:
        for missing_id in missing_selected_ids:
            items.append(
                {
                    "approval_id": missing_id,
                    "command_id": None,
                    "text": None,
                    "normalized_text": None,
                    "source_event_reference": None,
                    "classification": "missing_selected_approval",
                    "executable": False,
                    "restored": False,
                    "current_session": False,
                    "staleness": None,
                    "allowed_scope_match": False,
                    "would_resolve": False,
                    "resolution_disposition": RESTORED_EXECUTABLE_APPROVAL_DISPOSITION,
                    "reason": "selected approval id is not present as a pending approval",
                    "blockers": ["selected_approval_id_not_pending"],
                }
            )

    eligible_count = sum(1 for item in items if item["would_resolve"] is True)
    blocked_count = sum(1 for item in items if item["would_resolve"] is not True)
    all_pending_restored_in_scope = (
        bool(items)
        and blocked_count == 0
        and int(hygiene.get("pending_count") or 0) == len(items)
        and int(hygiene.get("restored_unresolved_count") or 0) == len(items)
    )
    status = "ready" if all_pending_restored_in_scope else "blocked"
    manifest_id = _manifest_id(items)

    return {
        "manifest_version": RESTORED_APPROVAL_RESOLUTION_MANIFEST_VERSION,
        "manifest_id": manifest_id,
        "read_only": True,
        "status": status,
        "mutation_performed": False,
        "operator_confirmation_required": True,
        "confirmation_phrase_required": RESTORED_EXECUTABLE_APPROVAL_CONFIRMATION,
        "approval_ids_bound": list(target_ids),
        "allowed_command_texts": sorted(allowed_texts),
        "eligible_count": eligible_count,
        "blocked_count": blocked_count,
        "pending_count": hygiene.get("pending_count", 0),
        "restored_unresolved_count": hygiene.get("restored_unresolved_count", 0),
        "restored_unresolved_executable_count": hygiene.get(
            "restored_unresolved_executable_count", 0
        ),
        "current_session_pending_count": hygiene.get("current_session_pending_count", 0),
        "all_pending_restored_in_scope": all_pending_restored_in_scope,
        "items": items,
        "safety": {
            "approval_grant_exposed": False,
            "approval_grant_created": False,
            "auto_approval": False,
            "auto_denial": False,
            "command_execution_allowed": False,
            "file_creation_allowed": False,
            "app_launch_allowed": False,
            "journal_rewrite_allowed": False,
            "frontend_authority": False,
        },
    }


def apply_restored_executable_approval_resolution(
    *,
    manager: ApprovalManager | None = None,
    journal: Any | None = None,
    approval_ids: list[str],
    confirmation_phrase: str,
    manifest_id: str,
    reason: str = "operator cancelled restored executable approval as non-current historical intent",
) -> dict[str, Any]:
    """Apply explicit restored executable approval cancellation and append lifecycle events."""

    if confirmation_phrase != RESTORED_EXECUTABLE_APPROVAL_CONFIRMATION:
        raise ValueError("restored executable approval cancellation confirmation phrase mismatch")
    if not approval_ids:
        raise ValueError("restored executable approval cancellation requires explicit approval ids")

    manager = manager or get_approval_manager()
    journal = journal or get_runtime_journal()
    manifest = build_restored_executable_approval_resolution_manifest(
        manager.snapshot(),
        approval_ids=approval_ids,
    )
    if manifest["manifest_id"] != manifest_id:
        raise ValueError("restored executable approval cancellation manifest id mismatch")
    if manifest["status"] != "ready":
        raise ValueError("restored executable approval cancellation manifest is not ready")

    events: list[dict[str, Any]] = []
    resolved: list[dict[str, Any]] = []
    resolved_records: list[dict[str, Any]] = []
    for item in manifest["items"]:
        approval_id = str(item["approval_id"])
        record = manager.cancel_restored_executable_approval(
            approval_id,
            manifest_id=manifest_id,
            reason=reason,
            resolution_metadata={
                "operator_confirmation_ref": manifest_id,
                "resolution_disposition": RESTORED_EXECUTABLE_APPROVAL_DISPOSITION,
                "source_event_reference": item.get("source_event_reference"),
            },
        )
        event = create_event(
            ProtocolEventType.COMMAND_CANCELLED,
            {
                "command_id": record.command_id,
                "approval_id": approval_id,
                "decision": RESTORED_EXECUTABLE_APPROVAL_DISPOSITION,
                "resolution_disposition": RESTORED_EXECUTABLE_APPROVAL_DISPOSITION,
                "reason": reason,
                "operator_confirmation_ref": manifest_id,
                "not_executed": True,
                "executed": False,
                "mutation_performed": False,
                "approval_grant": False,
                "auto_approval": False,
                "auto_denial": False,
                "command": record.to_dict(),
            },
            trace_id=record.trace_id,
            source=Component.GUARD,
            severity=Severity.WARNING,
        )
        appended = journal.append(event)
        resolved_records.append(record.to_dict())
        events.append(appended.to_dict())
        resolved.append(
            {
                "approval_id": approval_id,
                "command_id": record.command_id,
                "status": record.status.value,
                "resolution_disposition": RESTORED_EXECUTABLE_APPROVAL_DISPOSITION,
            }
        )
    snapshot = manager.snapshot()
    records_by_id = {
        str(record.get("command_id")): record
        for record in snapshot.get("records", [])
        if isinstance(record, dict) and record.get("command_id")
    }
    for record in resolved_records:
        records_by_id[str(record["command_id"])] = record
    snapshot["records"] = list(records_by_id.values())
    snapshot_event = create_event(
        ProtocolEventType.SNAPSHOT_CREATED,
        {
            "runtime": {"commands": snapshot},
            "manifest_id": manifest_id,
            "reason": "snapshot after restored executable approval operator cancellation",
            "mutation_performed": False,
            "approval_grant": False,
            "auto_approval": False,
            "auto_denial": False,
            "command_execution_performed": False,
        },
        source=Component.SYSTEM,
        severity=Severity.INFO,
    )
    appended_snapshot = journal.append(snapshot_event)

    return {
        "status": "resolved",
        "manifest_id": manifest_id,
        "resolved_count": len(resolved),
        "resolved": resolved,
        "events": [
            {
                "event_id": event.get("event_id"),
                "type": event.get("type"),
                "sequence_num": event.get("sequence_num"),
            }
            for event in events
        ],
        "snapshot_event": {
            "event_id": appended_snapshot.event_id,
            "type": appended_snapshot.type,
            "sequence_num": appended_snapshot.sequence_num,
        },
        "safety": {
            "approval_grant_created": False,
            "auto_approval": False,
            "auto_denial": False,
            "command_execution_performed": False,
            "file_creation_performed": False,
            "app_launch_performed": False,
            "journal_rewrite_performed": False,
        },
    }


def _manifest_id(items: list[dict[str, Any]]) -> str:
    basis = [
        {
            "approval_id": item.get("approval_id"),
            "command_id": item.get("command_id"),
            "text": item.get("normalized_text"),
            "would_resolve": item.get("would_resolve"),
            "source": item.get("source_event_reference"),
        }
        for item in sorted(items, key=lambda value: str(value.get("approval_id") or ""))
    ]
    digest = hashlib.sha256(
        json.dumps(
            {
                "version": RESTORED_APPROVAL_RESOLUTION_MANIFEST_VERSION,
                "disposition": RESTORED_EXECUTABLE_APPROVAL_DISPOSITION,
                "items": basis,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return f"restored-executable-approval-resolution:{digest[:24]}"
