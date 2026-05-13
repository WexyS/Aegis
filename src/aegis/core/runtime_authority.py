from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any, Optional

from aegis.core.fsm import coerce_state, is_valid_transition
from aegis.core.protocol import RuntimeState


def _now_ms() -> int:
    return int(time.time() * 1000)


@dataclass
class RuntimeSnapshot:
    session_id: str
    fsm_state: str = RuntimeState.IDLE.value
    previous_fsm_state: Optional[str] = None
    active_trace_id: Optional[str] = None
    active_span_id: Optional[str] = None
    active_command: Optional[str] = None
    active_task_id: Optional[str] = None
    active_tool: Optional[str] = None
    queue_depth: int = 0
    queue_capacity: int = 0
    recovery_depth: int = 0
    last_transition_reason: Optional[str] = None
    version: int = 0
    started_at: int = 0
    updated_at: int = 0

    def to_dict(self, journal: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        data = {
            "session_id": self.session_id,
            "fsm_state": self.fsm_state,
            "previous_fsm_state": self.previous_fsm_state,
            "active_trace_id": self.active_trace_id,
            "active_span_id": self.active_span_id,
            "active_command": self.active_command,
            "active_task_id": self.active_task_id,
            "active_tool": self.active_tool,
            "queue_depth": self.queue_depth,
            "queue_capacity": self.queue_capacity,
            "recovery_depth": self.recovery_depth,
            "last_transition_reason": self.last_transition_reason,
            "version": self.version,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
        }
        if journal:
            data["last_event_sequence"] = journal.get("last_sequence_num", 0)
            data["last_event_hash"] = journal.get("last_event_hash")
        return data


class RuntimeAuthority:
    """Thread-safe source of truth for the current runtime projection."""

    def __init__(self, session_id: str, queue_capacity: int = 0) -> None:
        now = _now_ms()
        self._lock = threading.RLock()
        self._snapshot = RuntimeSnapshot(
            session_id=session_id,
            queue_capacity=queue_capacity,
            started_at=now,
            updated_at=now,
        )

    def configure_session(self, session_id: str) -> None:
        with self._lock:
            if self._snapshot.session_id == session_id:
                return
            now = _now_ms()
            self._snapshot = RuntimeSnapshot(
                session_id=session_id,
                queue_capacity=self._snapshot.queue_capacity,
                started_at=now,
                updated_at=now,
                version=self._snapshot.version + 1,
            )

    def set_queue(self, *, depth: int, capacity: int) -> None:
        with self._lock:
            self._snapshot.queue_depth = max(depth, 0)
            self._snapshot.queue_capacity = max(capacity, 0)
            self._touch()

    def start_command(self, *, trace_id: str, command: str, task_id: str | None = None) -> None:
        with self._lock:
            self._snapshot.active_trace_id = trace_id
            self._snapshot.active_span_id = None
            self._snapshot.active_command = command
            self._snapshot.active_task_id = task_id
            self._snapshot.active_tool = None
            self._snapshot.recovery_depth = 0
            self._touch()

    def finish_command(self, *, trace_id: str | None = None) -> None:
        with self._lock:
            if trace_id and self._snapshot.active_trace_id and self._snapshot.active_trace_id != trace_id:
                return
            self._snapshot.active_trace_id = None
            self._snapshot.active_span_id = None
            self._snapshot.active_command = None
            self._snapshot.active_task_id = None
            self._snapshot.active_tool = None
            self._touch()

    def set_active_span(self, *, span_id: str | None = None, tool: str | None = None) -> None:
        with self._lock:
            self._snapshot.active_span_id = span_id
            self._snapshot.active_tool = tool
            self._touch()

    def set_recovery_depth(self, depth: int) -> None:
        with self._lock:
            self._snapshot.recovery_depth = max(depth, 0)
            self._touch()

    def current_state(self) -> RuntimeState:
        with self._lock:
            return RuntimeState(self._snapshot.fsm_state)

    def can_transition(self, from_state: RuntimeState | str, to_state: RuntimeState | str) -> bool:
        return is_valid_transition(from_state, to_state)

    def transition(
        self,
        to_state: RuntimeState | str,
        *,
        from_state: RuntimeState | str | None = None,
        reason: str | None = None,
        force: bool = False,
    ) -> tuple[RuntimeState, RuntimeState, bool]:
        with self._lock:
            current = RuntimeState(self._snapshot.fsm_state)
            target = coerce_state(to_state)
            source = coerce_state(from_state) if from_state is not None else current
            effective_source = current if source != current else source
            legal = is_valid_transition(effective_source, target)
            if not legal and not force:
                return effective_source, target, False

            self._snapshot.previous_fsm_state = effective_source.value
            self._snapshot.fsm_state = target.value
            self._snapshot.last_transition_reason = reason
            if target in (RuntimeState.IDLE, RuntimeState.COMPLETED, RuntimeState.FAILED):
                self._snapshot.recovery_depth = 0
            self._touch()
            return effective_source, target, legal

    def snapshot(self, journal: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        with self._lock:
            return self._snapshot.to_dict(journal=journal)

    def _touch(self) -> None:
        self._snapshot.version += 1
        self._snapshot.updated_at = _now_ms()


_instance: RuntimeAuthority | None = None
_lock = threading.Lock()


def get_runtime_authority(session_id: str = "session-uninitialized", queue_capacity: int = 0) -> RuntimeAuthority:
    global _instance
    with _lock:
        if _instance is None:
            _instance = RuntimeAuthority(session_id=session_id, queue_capacity=queue_capacity)
        else:
            _instance.configure_session(session_id)
            if queue_capacity:
                current = _instance.snapshot()
                _instance.set_queue(depth=current.get("queue_depth", 0), capacity=queue_capacity)
        return _instance
