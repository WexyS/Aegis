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
            record.approved = False
            record.rejected = False
            record.active = False
            record.reason = reason
            record.warnings = list(warnings or [])
            record.metadata.update(metadata or {})
            record.touch()
            return record

    def approve(self, command_id: str) -> CommandRecord:
        with self._lock:
            record = self._require(command_id)
            if record.status != CommandStatus.PENDING_APPROVAL:
                raise ValueError(f"Command {command_id} is not pending approval")
            record.status = CommandStatus.APPROVED
            record.approved = True
            record.approval_required = False
            record.approved_at = now_ms()
            record.touch()
            return record

    def reject(self, command_id: str, reason: str = "rejected by user") -> CommandRecord:
        with self._lock:
            record = self._require(command_id)
            record.status = CommandStatus.REJECTED
            record.rejected = True
            record.approval_required = False
            record.reason = reason
            record.rejected_at = now_ms()
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
            active = [r for r in records if r["active"]]
            return {
                "records": records[-50:],
                "pending_approvals": pending,
                "active_command": active[-1] if active else None,
            }

    def restore_from_snapshot(self, snapshot: dict[str, Any], *, replace: bool = True) -> None:
        """Restore command lifecycle state from a runtime snapshot.

        Pending approvals are safe to preserve across restarts. Running commands are not:
        their worker/cancellation-token context is gone, so they are marked cancelled
        instead of being presented as still active.
        """
        with self._lock:
            if replace:
                self._records.clear()
                self._tokens.clear()

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
                    record.reason = self.RESTART_CANCEL_REASON
                    record.cancelled_at = token.cancelled_at
                    record.touch()
                elif record.status == CommandStatus.CANCELLED:
                    token._cancelled = True
                    token.cancelled_reason = record.reason or "cancelled"
                    token.cancelled_at = record.cancelled_at

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

    def _iter_snapshot_records(self, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
        records_by_id: dict[str, dict[str, Any]] = {}
        candidates: list[Any] = []
        candidates.extend(snapshot.get("records") or [])
        candidates.extend(snapshot.get("pending_approvals") or [])
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
    events = journal.events_after(0)

    for event in reversed(events):
        payload = event.get("payload") if isinstance(event, dict) else None
        runtime = payload.get("runtime") if isinstance(payload, dict) else None
        command_snapshot = runtime.get("commands") if isinstance(runtime, dict) else None
        if isinstance(command_snapshot, dict):
            manager.restore_from_snapshot(command_snapshot)
            return True

    records_by_id: dict[str, dict[str, Any]] = {}
    for event in events:
        payload = event.get("payload") if isinstance(event, dict) else None
        command = payload.get("command") if isinstance(payload, dict) else None
        if not isinstance(command, dict):
            continue
        command_id = command.get("command_id")
        if isinstance(command_id, str) and command_id:
            records_by_id[command_id] = command

    if records_by_id:
        manager.restore_from_snapshot({"records": list(records_by_id.values())})
        return True
    return False
