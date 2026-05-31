from __future__ import annotations

import threading
import time
from dataclasses import asdict, dataclass, field, fields
from typing import Any
from uuid import uuid4

from aegis.core.constants import CommandStatus, RiskLevel


def now_ms() -> int:
    return int(time.time() * 1000)


@dataclass
class CancellationToken:
    command_id: str
    _cancelled: bool = False
    cancelled_reason: str | None = None
    cancelled_at: int | None = None

    def cancel(self, reason: str = "cancelled by user") -> None:
        self._cancelled = True
        self.cancelled_reason = reason
        self.cancelled_at = now_ms()

    @property
    def cancelled(self) -> bool:
        return self._cancelled


@dataclass
class CommandRecord:
    command_id: str
    text: str
    status: CommandStatus
    risk_level: RiskLevel = RiskLevel.NONE
    trace_id: str | None = None
    approval_required: bool = False
    clarification_required: bool = False
    approved: bool = False
    rejected: bool = False
    active: bool = False
    verification_state: str = "unverified"
    reason: str = ""
    warnings: list[str] = field(default_factory=list)
    created_at: int = field(default_factory=now_ms)
    updated_at: int = field(default_factory=now_ms)
    approved_at: int | None = None
    rejected_at: int | None = None
    cancelled_at: int | None = None
    completed_at: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def touch(self) -> None:
        self.updated_at = now_ms()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["risk_level"] = self.risk_level.value
        return data


class ApprovalManager:
    """In-memory authority for command lifecycle and approval state."""

    RESTART_CANCEL_REASON = "runtime restarted before command completed"
    NON_EXECUTED_APPROVAL_REASON = (
        "Approval was recorded, but this decision is non-executable until a "
        "deterministic execution contract exists."
    )
    NON_EXECUTED_CLARIFICATION_REASON = (
        "Clarification was recorded, but v1 does not resume execution from "
        "clarification answers."
    )

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._records: dict[str, CommandRecord] = {}
        self._tokens: dict[str, CancellationToken] = {}

    def create_received(self, text: str, *, command_id: str | None = None) -> CommandRecord:
        with self._lock:
            command_id = command_id or str(uuid4())
            existing = self._records.get(command_id)
            if existing:
                return existing
            record = CommandRecord(
                command_id=command_id,
                text=text,
                status=CommandStatus.RECEIVED,
            )
            self._records[command_id] = record
            self._tokens[command_id] = CancellationToken(command_id=command_id)
            return record

    def register_pending(
        self,
        *,
        command_id: str,
        text: str,
        trace_id: str,
        risk_level: RiskLevel,
        reason: str,
        warnings: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> CommandRecord:
        with self._lock:
            record = self._records.get(command_id) or self.create_received(text, command_id=command_id)
            record.trace_id = trace_id
            record.risk_level = risk_level
            record.status = CommandStatus.PENDING_APPROVAL
            record.approval_required = True
            record.clarification_required = False
            record.approved = False
            record.rejected = False
            record.active = False
            record.verification_state = "unverified"
            record.reason = reason
            record.warnings = list(warnings or [])
            record.metadata.update(metadata or {})
            record.metadata.setdefault("approval_id", record.metadata.get("decision_id") or command_id)
            record.metadata.setdefault("approval_resolution_status", "waiting_for_approval")
            record.metadata.setdefault("resume_allowed", True)
            record.metadata.setdefault("mutation_performed", False)
            record.touch()
            return record

    def register_waiting_clarification(
        self,
        *,
        command_id: str,
        text: str,
        trace_id: str,
        risk_level: RiskLevel,
        reason: str,
        warnings: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> CommandRecord:
        with self._lock:
            record = self._records.get(command_id) or self.create_received(text, command_id=command_id)
            record.trace_id = trace_id
            record.risk_level = risk_level
            record.status = CommandStatus.WAITING_FOR_CLARIFICATION
            record.approval_required = False
            record.clarification_required = True
            record.approved = False
            record.rejected = False
            record.active = False
            record.verification_state = "unverified"
            record.reason = reason
            record.warnings = list(warnings or [])
            record.metadata.update(metadata or {})
            record.metadata.setdefault("clarification_id", record.metadata.get("decision_id") or command_id)
            record.metadata.setdefault("clarification_resolution_status", "waiting_for_clarification")
            record.metadata.setdefault("resume_allowed", False)
            record.metadata.setdefault("mutation_performed", False)
            record.touch()
            return record

    def approve(self, command_id: str) -> CommandRecord:
        with self._lock:
            record = self._require(command_id)
            return self._approve_record(record)

    def resolve_approval(
        self,
        approval_id: str,
        *,
        approved: bool,
        reason: str = "",
    ) -> CommandRecord:
        with self._lock:
            record = self._find_pending_decision("approval_id", approval_id, CommandStatus.PENDING_APPROVAL)
            if approved:
                return self._approve_record(record, decision_id=approval_id, reason=reason)
            return self._reject_record(
                record,
                reason=reason or "approval denied by user",
                decision_id=approval_id,
            )

    def reject(self, command_id: str, reason: str = "rejected by user") -> CommandRecord:
        with self._lock:
            record = self._require(command_id)
            return self._reject_record(record, reason=reason)

    def resolve_clarification(
        self,
        clarification_id: str,
        *,
        answer: str | None = None,
        cancelled: bool = False,
        reason: str = "",
    ) -> CommandRecord:
        with self._lock:
            record = self._find_pending_decision(
                "clarification_id",
                clarification_id,
                CommandStatus.WAITING_FOR_CLARIFICATION,
            )
            record.clarification_required = False
            record.approval_required = False
            record.active = False
            record.completed_at = now_ms()
            record.metadata["clarification_id"] = clarification_id
            record.metadata["clarification_answer"] = answer
            record.metadata["mutation_performed"] = False
            record.metadata["not_executed"] = True
            record.metadata["completed_without_execution"] = True
            if cancelled:
                record.status = CommandStatus.CANCELLED
                record.reason = reason or "clarification cancelled by user"
                record.cancelled_at = record.completed_at
                record.metadata["clarification_resolution_status"] = "clarification_cancelled"
            else:
                record.status = CommandStatus.BLOCKED
                record.reason = reason or self.NON_EXECUTED_CLARIFICATION_REASON
                record.metadata["clarification_resolution_status"] = "clarification_resolved"
            record.touch()
            return record

    def mark_running(
        self,
        command_id: str,
        *,
        trace_id: str,
        risk_level: RiskLevel | None = None,
        verification_state: str | None = None,
    ) -> CommandRecord:
        with self._lock:
            record = self._require(command_id)
            record.trace_id = trace_id
            record.status = CommandStatus.RUNNING
            record.active = True
            record.clarification_required = False
            if risk_level is not None:
                record.risk_level = risk_level
            if verification_state is not None:
                record.verification_state = verification_state
            record.touch()
            return record

    def mark_blocked(
        self,
        command_id: str,
        *,
        trace_id: str,
        risk_level: RiskLevel,
        reason: str,
        verification_state: str = "unverified",
    ) -> CommandRecord:
        with self._lock:
            record = self._require(command_id)
            record.trace_id = trace_id
            record.risk_level = risk_level
            record.status = CommandStatus.BLOCKED
            record.active = False
            record.approval_required = False
            record.clarification_required = False
            record.verification_state = verification_state
            record.reason = reason
            record.completed_at = now_ms()
            record.touch()
            return record

    def complete(
        self,
        command_id: str,
        status: CommandStatus,
        *,
        reason: str = "",
        verification_state: str | None = None,
    ) -> CommandRecord:
        with self._lock:
            record = self._require(command_id)
            record.status = status
            record.active = False
            record.clarification_required = False
            record.reason = reason or record.reason
            if verification_state is not None:
                record.verification_state = verification_state
            record.completed_at = now_ms()
            record.touch()
            return record

    def cancel(self, command_id: str, reason: str = "cancelled by user") -> CommandRecord:
        with self._lock:
            record = self._require(command_id)
            token = self._tokens.setdefault(command_id, CancellationToken(command_id=command_id))
            token.cancel(reason)
            record.status = CommandStatus.CANCELLED
            record.active = False
            record.approval_required = False
            record.clarification_required = False
            record.reason = reason
            record.cancelled_at = token.cancelled_at
            record.touch()
            return record

    def token_for(self, command_id: str) -> CancellationToken:
        with self._lock:
            self._require(command_id)
            return self._tokens.setdefault(command_id, CancellationToken(command_id=command_id))

    def get(self, command_id: str) -> CommandRecord | None:
        with self._lock:
            return self._records.get(command_id)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            records = [record.to_dict() for record in self._records.values()]
            pending = [r for r in records if r["status"] == CommandStatus.PENDING_APPROVAL.value]
            pending_clarifications = [
                r for r in records if r["status"] == CommandStatus.WAITING_FOR_CLARIFICATION.value
            ]
            active = [r for r in records if r["active"]]
            return {
                "records": records[-50:],
                "pending_approvals": pending,
                "pending_clarifications": pending_clarifications,
                "active_command": active[-1] if active else None,
            }

    def restore_from_snapshot(
        self,
        snapshot: dict[str, Any],
        *,
        replace: bool = True,
        restored_source: str = "runtime_snapshot",
        source_snapshot_sequence: int | None = None,
        restored_at: int | None = None,
    ) -> None:
        """Restore command lifecycle state from a runtime snapshot.

        Pending approvals are safe to preserve across restarts. Running commands are not:
        their worker/cancellation-token context is gone, so they are marked cancelled
        instead of being presented as still active.
        """
        with self._lock:
            if replace:
                self._records.clear()
                self._tokens.clear()

            restore_time = restored_at if restored_at is not None else now_ms()
            for record_data in self._iter_snapshot_records(snapshot):
                record = self._record_from_dict(record_data)
                if record is None:
                    continue
                token = CancellationToken(command_id=record.command_id)

                if record.active or record.status == CommandStatus.RUNNING:
                    token.cancel(self.RESTART_CANCEL_REASON)
                    record.status = CommandStatus.CANCELLED
                    record.active = False
                    record.approval_required = False
                    record.clarification_required = False
                    record.reason = self.RESTART_CANCEL_REASON
                    record.cancelled_at = token.cancelled_at
                    record.touch()
                elif record.status == CommandStatus.CANCELLED:
                    token._cancelled = True
                    token.cancelled_reason = record.reason or "cancelled"
                    token.cancelled_at = record.cancelled_at

                if record.status in {
                    CommandStatus.PENDING_APPROVAL,
                    CommandStatus.WAITING_FOR_CLARIFICATION,
                }:
                    record.metadata["restored_from_journal"] = True
                    record.metadata["restored_source"] = restored_source
                    record.metadata["restored_at"] = restore_time
                    if source_snapshot_sequence is not None:
                        record.metadata["source_snapshot_sequence"] = source_snapshot_sequence

                self._records[record.command_id] = record
                self._tokens[record.command_id] = token

    def reset_for_tests(self) -> None:
        with self._lock:
            self._records.clear()
            self._tokens.clear()

    def _require(self, command_id: str) -> CommandRecord:
        record = self._records.get(command_id)
        if record is None:
            raise KeyError(f"Unknown command_id: {command_id}")
        return record

    def _find_pending_decision(
        self,
        metadata_key: str,
        decision_id: str,
        expected_status: CommandStatus,
    ) -> CommandRecord:
        if not decision_id:
            raise KeyError("Missing decision_id")
        matches = [
            record
            for record in self._records.values()
            if str(record.metadata.get(metadata_key) or "") == str(decision_id)
        ]
        if not matches:
            raise KeyError(f"Unknown {metadata_key}: {decision_id}")
        record = matches[-1]
        if record.status != expected_status:
            raise ValueError(
                f"Decision {decision_id} is not pending; current status is {record.status.value}"
            )
        return record

    def _approve_record(
        self,
        record: CommandRecord,
        *,
        decision_id: str | None = None,
        reason: str = "",
    ) -> CommandRecord:
        if record.status != CommandStatus.PENDING_APPROVAL:
            raise ValueError(f"Command {record.command_id} is not pending approval")

        record.approved = True
        record.rejected = False
        record.approval_required = False
        record.clarification_required = False
        record.approved_at = now_ms()
        if decision_id is not None:
            record.metadata["approval_id"] = decision_id
        record.metadata["approval_resolution_status"] = "approval_granted"
        record.metadata["mutation_performed"] = False

        if record.metadata.get("resume_allowed") is False:
            record.status = CommandStatus.BLOCKED
            record.active = False
            record.reason = reason or self.NON_EXECUTED_APPROVAL_REASON
            record.completed_at = now_ms()
            record.metadata["not_executed"] = True
            record.metadata["completed_without_execution"] = True
        else:
            record.status = CommandStatus.APPROVED
            record.reason = reason or record.reason
        record.touch()
        return record

    def _reject_record(
        self,
        record: CommandRecord,
        *,
        reason: str,
        decision_id: str | None = None,
    ) -> CommandRecord:
        if record.status != CommandStatus.PENDING_APPROVAL:
            raise ValueError(f"Command {record.command_id} is not pending approval")
        record.status = CommandStatus.REJECTED
        record.rejected = True
        record.approved = False
        record.approval_required = False
        record.clarification_required = False
        record.active = False
        record.reason = reason
        record.rejected_at = now_ms()
        record.metadata["approval_resolution_status"] = "approval_denied"
        record.metadata["mutation_performed"] = False
        record.metadata["not_executed"] = True
        if decision_id is not None:
            record.metadata["approval_id"] = decision_id
        record.touch()
        return record

    def _iter_snapshot_records(self, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
        records_by_id: dict[str, dict[str, Any]] = {}
        candidates: list[Any] = []
        candidates.extend(snapshot.get("records") or [])
        candidates.extend(snapshot.get("pending_approvals") or [])
        candidates.extend(snapshot.get("pending_clarifications") or [])
        if active := snapshot.get("active_command"):
            candidates.append(active)

        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            command_id = candidate.get("command_id")
            if isinstance(command_id, str) and command_id:
                records_by_id[command_id] = candidate
        return list(records_by_id.values())

    def _record_from_dict(self, data: dict[str, Any]) -> CommandRecord | None:
        command_id = data.get("command_id")
        text = data.get("text")
        if not isinstance(command_id, str) or not command_id:
            return None
        if not isinstance(text, str):
            text = ""

        try:
            status = CommandStatus(data.get("status", CommandStatus.UNKNOWN.value))
        except ValueError:
            status = CommandStatus.UNKNOWN
        try:
            risk_level = RiskLevel(data.get("risk_level", RiskLevel.NONE.value))
        except ValueError:
            risk_level = RiskLevel.NONE

        field_names = {item.name for item in fields(CommandRecord)}
        values = {key: value for key, value in data.items() if key in field_names}
        values.update({
            "command_id": command_id,
            "text": text,
            "status": status,
            "risk_level": risk_level,
            "warnings": list(data.get("warnings") or []),
            "metadata": dict(data.get("metadata") or {}),
        })
        return CommandRecord(**values)


_approval_manager: ApprovalManager | None = None
_approval_manager_lock = threading.Lock()


def get_approval_manager() -> ApprovalManager:
    global _approval_manager
    with _approval_manager_lock:
        if _approval_manager is None:
            _approval_manager = ApprovalManager()
        return _approval_manager


def restore_approval_manager_from_journal(
    *,
    journal: Any | None = None,
    manager: ApprovalManager | None = None,
) -> bool:
    """Restore command lifecycle state from the latest journaled runtime snapshot."""
    if journal is None:
        from aegis.core.event_journal import get_runtime_journal

        journal = get_runtime_journal()
    manager = manager or get_approval_manager()
    recent_events = getattr(journal, "recent_events", None)
    if callable(recent_events):
        events = list(recent_events())
    else:
        events = []

    if not _restore_approval_manager_from_events(events, manager):
        events = journal.events_after(0)
        return _restore_approval_manager_from_events(events, manager)
    return True


def _restore_approval_manager_from_events(events: list[dict[str, Any]], manager: ApprovalManager) -> bool:
    if not events:
        return False

    for snapshot_index in range(len(events) - 1, -1, -1):
        event = events[snapshot_index]
        payload = event.get("payload") if isinstance(event, dict) else None
        runtime = payload.get("runtime") if isinstance(payload, dict) else None
        command_snapshot = runtime.get("commands") if isinstance(runtime, dict) else None
        if isinstance(command_snapshot, dict):
            sequence = event.get("sequence_num")
            manager.restore_from_snapshot(
                command_snapshot,
                restored_source="runtime_snapshot",
                source_snapshot_sequence=sequence if isinstance(sequence, int) else None,
            )
            post_snapshot_records = _command_records_from_events(events[snapshot_index + 1:])
            if post_snapshot_records:
                manager.restore_from_snapshot(
                    {"records": post_snapshot_records},
                    replace=False,
                    restored_source="command_event_replay",
                    source_snapshot_sequence=_max_event_sequence(events[snapshot_index + 1:]),
                )
            return True

    records_by_id = _command_records_by_id(events)
    if records_by_id:
        manager.restore_from_snapshot(
            {"records": list(records_by_id.values())},
            restored_source="command_event_replay",
            source_snapshot_sequence=_max_event_sequence(events),
        )
        return True
    return False


def _command_records_from_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return list(_command_records_by_id(events).values())


def _command_records_by_id(events: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    records_by_id: dict[str, dict[str, Any]] = {}
    for event in events:
        payload = event.get("payload") if isinstance(event, dict) else None
        command = payload.get("command") if isinstance(payload, dict) else None
        if not isinstance(command, dict):
            continue
        command_id = command.get("command_id")
        if isinstance(command_id, str) and command_id:
            records_by_id[command_id] = command
    return records_by_id


def _max_event_sequence(events: list[dict[str, Any]]) -> int | None:
    sequences = [
        event.get("sequence_num")
        for event in events
        if isinstance(event.get("sequence_num"), int)
    ]
    return max(sequences) if sequences else None
