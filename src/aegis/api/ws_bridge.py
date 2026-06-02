"""
══════════════════════════════════════════════════════════════════════
AEGIS WEBSOCKET EVENT BRIDGE
══════════════════════════════════════════════════════════════════════

Production-grade WebSocket server integrated with FastAPI.
Emits protocol-compliant RuntimeEvents to all connected clients.

Architecture:
  - Uses python-socketio (async mode)
  - Mounts on the existing ASGI app
  - Emits events from the orchestrator pipeline
  - Heartbeat keepalive
  - Connection state tracking
  - Protocol version handshake

This is the ONLY authorized event emission path.
Direct socket calls from other modules are forbidden.

══════════════════════════════════════════════════════════════════════
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Iterable, Optional, Set
from uuid import uuid4

import socketio

from aegis.core.protocol import (
    PROTOCOL_VERSION,
    ProtocolEventType,
    RuntimeEvent,
    RuntimeState,
    Component,
    Severity,
    create_event,
)
from aegis.core.commands import get_approval_manager
from aegis.core.action_timeline import project_action_timeline
from aegis.core.app_map import get_app_registry_snapshot
from aegis.core.approval_semantics import DecisionStatus
from aegis.tools.registry import get_tool_registry_snapshot
from aegis.core.event_journal import get_runtime_journal
from aegis.core.guard_policy import GuardDecision
from aegis.core.maintenance import get_last_maintenance_scan, run_read_only_maintenance_scan
from aegis.core.maintenance_actions import (
    execute_maintenance_action_proposal,
    is_maintenance_action_record,
    request_maintenance_action_approval,
    response_from_maintenance_action,
)
from aegis.core.non_executable_projection import (
    project_guard_decision_to_journal_entries,
    reconstruct_non_executable_decision_from_journal,
)
from aegis.core.non_executable_runtime_adapter import (
    project_non_executable_events_to_action_timeline,
    project_non_executable_events_to_snapshot,
    runtime_events_to_journal_entries,
)
from aegis.core.runtime_authority import get_runtime_authority
from aegis.core.constants import CommandStatus, RiskLevel
from aegis.core.schemas import CommandResponse

logger = logging.getLogger(__name__)

# ─── SOCKET.IO SERVER ───────────────────────────────────────────────
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=False,
    engineio_logger=False,
)

# ─── CONNECTION STATE ───────────────────────────────────────────────
_connected_clients: Set[str] = set()
_session_id: str = f"session-{int(time.time())}-{uuid4().hex[:8]}"
_heartbeat_task: Optional[asyncio.Task] = None
_command_worker_task: Optional[asyncio.Task] = None
_command_queue_capacity = 16
_command_queue: asyncio.Queue["QueuedCommand"] = asyncio.Queue(maxsize=_command_queue_capacity)
get_runtime_authority(_session_id, queue_capacity=_command_queue_capacity)
_journal_emit_lock = asyncio.Lock()

_NON_EXECUTABLE_BATCH_FORBIDDEN_EVENT_TYPES = {
    ProtocolEventType.ACTION_STARTED.value,
    ProtocolEventType.ACTION_COMPLETED.value,
    ProtocolEventType.ACTION_FAILED.value,
    "ACTION_CANCELLED",
    ProtocolEventType.APPROVAL_REQUIRED.value,
}
_NON_EXECUTABLE_BATCH_FORBIDDEN_PAYLOAD_KEYS = {"execution_evidence"}
_NON_EXECUTABLE_BATCH_FORBIDDEN_TRUTHY_KEYS = {"success", "verified", "action_started"}
_SUPPORTED_NON_EXECUTABLE_DECISIONS = {
    DecisionStatus.APPROVAL_REQUIRED,
    DecisionStatus.CLARIFICATION_REQUIRED,
    DecisionStatus.BLOCKED,
}
_CONTROL_PLANE_EVENT_TYPES = {
    ProtocolEventType.SYSTEM_ONLINE.value,
    ProtocolEventType.SNAPSHOT_CREATED.value,
}
RAW_CONTROL_COMMANDS = {
    "/force_idle": "raw control command is quarantined; runtime state cannot be forced by frontend text",
    "/reset_memory": "raw control command is quarantined; memory reset is not a frontend-authorized runtime action",
}


@dataclass(frozen=True)
class QueuedCommand:
    sid: str
    text: str
    mode: str
    received_at: float
    command_id: str | None = None
    approval_granted: bool = False


@dataclass(frozen=True)
class NonExecutableDecisionAppendResult:
    events: list[RuntimeEvent]
    snapshot_patch: dict[str, Any]
    action_timeline_entries: list[dict[str, Any]]
    replay_state: dict[str, Any]


def maintenance_scan_context() -> dict[str, Any]:
    journal = get_runtime_journal()
    _, runtime_snapshot = _build_runtime_snapshot(journal)
    return {
        "runtime_snapshot": runtime_snapshot,
        "session_id": _session_id,
        "websocket_clients": len(_connected_clients),
        "queue_depth": _command_queue.qsize(),
        "queue_capacity": _command_queue_capacity,
    }


async def _create_and_append_event(
    event_type: ProtocolEventType,
    payload: Dict[str, Any],
    *,
    trace_id: Optional[str] = None,
    causation_id: Optional[str] = None,
    span_id: Optional[str] = None,
    session_id: Optional[str] = None,
    runtime_phase: Optional[RuntimeState | str] = None,
    source: Optional[Component] = None,
    severity: Severity = Severity.INFO,
    mutate_before_append=None,
):
    """Create and persist a RuntimeEvent under one async ordering lock.

    RuntimeEvent.sequence_num is assigned at construction time, so creation and
    journal append must be serialized together. Locking only the append would
    still allow sequence numbers to be created in a different order than disk
    persistence under concurrent websocket emissions.
    """
    async with _journal_emit_lock:
        event = create_event(
            event_type,
            payload=payload,
            trace_id=trace_id,
            causation_id=causation_id,
            span_id=span_id,
            session_id=session_id,
            runtime_phase=runtime_phase,
            source=source,
            severity=severity,
        )
        if mutate_before_append is not None:
            mutate_before_append(event)
        await asyncio.to_thread(get_runtime_journal().append, event)
        return event


def _create_control_event(
    event_type: ProtocolEventType,
    payload: Dict[str, Any],
    *,
    trace_id: Optional[str] = None,
    causation_id: Optional[str] = None,
    span_id: Optional[str] = None,
    session_id: Optional[str] = None,
    runtime_phase: Optional[RuntimeState | str] = None,
    source: Optional[Component] = None,
    severity: Severity = Severity.INFO,
) -> RuntimeEvent:
    """Create a client-scoped control-plane event without consuming journal sequence.

    Handshake and snapshot payloads are emitted to one socket client. Persisting
    them in the global runtime journal creates sequence gaps for other clients
    and can recursively embed prior snapshots through missed-event replay.
    """
    return RuntimeEvent(
        type=event_type.value,
        payload=payload or {},
        trace_id=trace_id,
        causation_id=causation_id,
        span_id=span_id,
        session_id=session_id,
        runtime_phase=runtime_phase.value if isinstance(runtime_phase, RuntimeState) else runtime_phase,
        source=source.value if source else None,
        severity=severity.value,
        sequence_num=None,
    )


def _replayable_journal_events_after(journal, sequence_num: int) -> list[dict[str, Any]]:
    if sequence_num <= 0:
        return []
    return [
        event
        for event in journal.events_after(sequence_num)
        if str(event.get("type") or "") not in _CONTROL_PLANE_EVENT_TYPES
    ]


async def append_non_executable_event_batch(
    events: Iterable[RuntimeEvent],
    *,
    journal,
    session_id: str | None = None,
    fanout: Callable[[RuntimeEvent], Awaitable[None] | None] | None = None,
) -> list[RuntimeEvent]:
    """Append a prebuilt non-executable RuntimeEvent batch under ws_bridge.

    This readiness helper is intentionally isolated: callers must inject the
    journal-like sink and optional fan-out callable. It does not call
    get_runtime_journal(), mutate RuntimeAuthority, create events, allocate
    sequence numbers, or touch the orchestrator/executor/tool layers.
    """

    event_batch = list(events)
    if session_id is not None:
        for event in event_batch:
            if event.session_id is None:
                event.session_id = session_id
    _validate_non_executable_event_batch(event_batch)

    appended: list[RuntimeEvent] = []
    async with _journal_emit_lock:
        for event in event_batch:
            persisted = await asyncio.to_thread(journal.append, event)
            appended.append(persisted)

    if fanout is not None:
        for event in appended:
            maybe_awaitable = fanout(event)
            if maybe_awaitable is not None:
                await maybe_awaitable

    return appended


async def append_non_executable_decision(
    guard_decision: GuardDecision,
    *,
    command_id: str,
    trace_id: str,
    causation_id: str | None = None,
    span_id: str | None = None,
    action_id: str | None = None,
    journal=None,
    session_id: str | None = None,
    fanout: Callable[[RuntimeEvent], Awaitable[None] | None] | None = None,
) -> NonExecutableDecisionAppendResult:
    """Create and append canonical non-executable RuntimeEvents under ws_bridge.

    Unlike the dry-run adapter, this helper allocates sequence numbers through
    create_event(...) while holding the canonical journal emit lock. Callers may
    inject a journal and fanout in tests; default orchestration is not wired to
    this helper yet.
    """

    _require_non_executable_decision(guard_decision)
    stable_causation_id = causation_id or f"{command_id}:guard_decision"
    entries = project_guard_decision_to_journal_entries(
        guard_decision,
        command_id=command_id,
        trace_id=trace_id,
        span_id=span_id,
        causation_id=stable_causation_id,
        sequence_num=None,
        timestamp=None,
    )
    target_journal = journal if journal is not None else get_runtime_journal()

    appended: list[RuntimeEvent] = []
    async with _journal_emit_lock:
        events: list[RuntimeEvent] = []
        for entry in entries:
            event_type = ProtocolEventType(str(entry["event_type"]))
            if event_type.value in _NON_EXECUTABLE_BATCH_FORBIDDEN_EVENT_TYPES:
                raise ValueError(f"non-executable decision cannot append {event_type.value}")
            payload = _non_executable_payload_from_entry(entry, action_id=action_id)
            _assert_non_executable_payload_shape(payload)
            events.append(
                create_event(
                    event_type,
                    payload=payload,
                    trace_id=trace_id,
                    causation_id=stable_causation_id,
                    span_id=span_id,
                    session_id=session_id,
                    source=Component.GUARD,
                    severity=Severity.WARNING,
                )
            )

        _validate_non_executable_event_batch(events)
        for event in events:
            persisted = await asyncio.to_thread(target_journal.append, event)
            appended.append(persisted)

    if fanout is not None:
        for event in appended:
            maybe_awaitable = fanout(event)
            if maybe_awaitable is not None:
                await maybe_awaitable

    return NonExecutableDecisionAppendResult(
        events=appended,
        snapshot_patch=project_non_executable_events_to_snapshot(appended),
        action_timeline_entries=project_non_executable_events_to_action_timeline(appended),
        replay_state=reconstruct_non_executable_decision_from_journal(
            runtime_events_to_journal_entries(appended)
        ),
    )


def _require_non_executable_decision(decision: GuardDecision) -> None:
    if decision.decision_status not in _SUPPORTED_NON_EXECUTABLE_DECISIONS:
        raise ValueError(f"non-executable decision append does not support {decision.decision_status.value}")


def _non_executable_payload_from_entry(entry: dict[str, Any], *, action_id: str | None = None) -> dict[str, Any]:
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


def _validate_non_executable_event_batch(events: list[RuntimeEvent]) -> None:
    if not events:
        raise ValueError("non-executable event batch cannot be empty")

    seen_sequences: set[int] = set()
    previous_sequence: int | None = None
    for event in events:
        if not isinstance(event, RuntimeEvent):
            raise TypeError("non-executable event batch accepts RuntimeEvent objects only")
        if event.type in _NON_EXECUTABLE_BATCH_FORBIDDEN_EVENT_TYPES:
            raise ValueError(f"non-executable event batch cannot append {event.type}")
        if event.type != ProtocolEventType(event.type).value:
            raise ValueError(f"non-canonical protocol event type: {event.type}")
        if event.sequence_num in seen_sequences:
            raise ValueError(f"duplicate sequence_num in non-executable event batch: {event.sequence_num}")
        if previous_sequence is not None and event.sequence_num <= previous_sequence:
            raise ValueError("non-executable event batch must be strictly sequence ordered")
        seen_sequences.add(event.sequence_num)
        previous_sequence = event.sequence_num

        payload = event.payload
        if payload.get("not_executed") is not True:
            raise ValueError("non-executable event payload must set not_executed=true")
        for required in ("command_id", "trace_id", "decision_status", "risk_level", "policy_rule", "reason"):
            if not payload.get(required):
                raise ValueError(f"non-executable event payload missing {required}")
        if event.causation_id is None:
            raise ValueError("non-executable event must preserve causation_id")
        _assert_non_executable_payload_shape(payload)


def _assert_non_executable_payload_shape(value: Any) -> None:
    if isinstance(value, dict):
        for key in _NON_EXECUTABLE_BATCH_FORBIDDEN_PAYLOAD_KEYS:
            if key in value and value[key] is not None:
                raise ValueError(f"non-executable payload cannot include {key}")
        for key in _NON_EXECUTABLE_BATCH_FORBIDDEN_TRUTHY_KEYS:
            if value.get(key) is True:
                raise ValueError(f"non-executable payload cannot set {key}=true")
        for nested in value.values():
            _assert_non_executable_payload_shape(nested)
    elif isinstance(value, list):
        for nested in value:
            _assert_non_executable_payload_shape(nested)


async def enqueue_approved_command_for_resume(
    record,
    *,
    sid: str | None = None,
    mode: str = "auto",
) -> bool:
    """Queue an approved command for the normal worker/orchestrator policy path."""
    if record.status != CommandStatus.APPROVED:
        return False
    if is_maintenance_action_record(record):
        record.metadata["approval_resume_status"] = "maintenance_action_not_queued"
        record.metadata["approval_resume_reason"] = "maintenance actions use the dedicated approval execution path"
        record.touch()
        await emit_command_status(
            command_id=record.command_id,
            status=record.status,
            trace_id=record.trace_id,
            risk_level=record.risk_level,
            reason=record.reason,
            verification_state=record.verification_state,
        )
        if sid:
            await _emit_snapshot(to=sid)
        return False

    command = QueuedCommand(
        sid=sid or "",
        text=record.text,
        mode=str(mode or "auto"),
        received_at=time.time(),
        command_id=record.command_id,
        approval_granted=True,
    )
    try:
        _command_queue.put_nowait(command)
    except asyncio.QueueFull:
        reason = "Approved command queue full; command was not enqueued"
        blocked = get_approval_manager().mark_blocked(
            record.command_id,
            trace_id=record.trace_id or "",
            risk_level=record.risk_level,
            reason=reason,
            verification_state="unverified",
        )
        blocked.metadata["approval_resume_status"] = "queue_full"
        blocked.metadata["approval_resume_queue_depth"] = _command_queue.qsize()
        blocked.metadata["approval_resume_queue_capacity"] = _command_queue_capacity
        blocked.metadata["mutation_performed"] = False
        blocked.touch()
        await emit_command_status(
            command_id=blocked.command_id,
            status=blocked.status,
            trace_id=blocked.trace_id,
            risk_level=blocked.risk_level,
            reason=blocked.reason,
            verification_state=blocked.verification_state,
        )
        await emit_event(
            ProtocolEventType.DETERMINISM_BREACH,
            {
                "reason": reason,
                "queue_depth": _command_queue.qsize(),
                "queue_capacity": _command_queue_capacity,
                "command_id": blocked.command_id,
                "trace_id": blocked.trace_id,
            },
            trace_id=blocked.trace_id,
            source=Component.SYSTEM,
            severity=Severity.WARNING,
            runtime_phase=get_runtime_authority(_session_id).current_state(),
        )
        if sid:
            await _emit_snapshot(to=sid)
        return False

    record.metadata["approval_resume_status"] = "queued_for_execution"
    record.metadata["approval_resume_mode"] = str(mode or "auto")
    record.metadata["approval_resume_queued_at"] = int(time.time() * 1000)
    record.metadata["approval_resume_queue_depth"] = _command_queue.qsize()
    record.metadata["approval_resume_queue_capacity"] = _command_queue_capacity
    record.touch()
    get_runtime_authority(_session_id, queue_capacity=_command_queue_capacity).set_queue(
        depth=_command_queue.qsize(),
        capacity=_command_queue_capacity,
    )
    await emit_command_status(
        command_id=record.command_id,
        status=record.status,
        trace_id=record.trace_id,
        risk_level=record.risk_level,
        reason="Approved command queued for policy-gated execution",
        verification_state=record.verification_state,
    )
    if sid:
        await _emit_snapshot(to=sid)
    return True

# ─── LIFECYCLE ──────────────────────────────────────────────────────

@sio.event
async def connect(sid: str, environ: dict):
    _connected_clients.add(sid)
    logger.info(f"[WS] Client connected: {sid} (total: {len(_connected_clients)})")
    journal = get_runtime_journal()
    journal_snapshot, runtime_snapshot = _build_runtime_snapshot(journal)

    # Send handshake
    handshake = _create_control_event(
        ProtocolEventType.SYSTEM_ONLINE,
        payload={
            "protocol_version": PROTOCOL_VERSION,
            "session_id": _session_id,
            "capabilities": ["streaming", "telemetry", "replay"],
            "backend_version": "1.0.0",
            "journal": journal_snapshot,
            "runtime": runtime_snapshot,
        },
        session_id=_session_id,
        runtime_phase=runtime_snapshot["fsm_state"],
        source=Component.SYSTEM,
    )
    await sio.emit("SYSTEM_ONLINE", handshake.to_dict(), to=sid)
    await _emit_snapshot(to=sid)


@sio.event
async def disconnect(sid: str):
    _connected_clients.discard(sid)
    logger.info(f"[WS] Client disconnected: {sid} (remaining: {len(_connected_clients)})")


@sio.event
async def heartbeat(sid: str, data: dict):
    """Respond to client heartbeat with server timestamp."""
    await sio.emit("heartbeat_ack", {
        "server_time": int(time.time() * 1000),
        "client_time": data.get("timestamp"),
        "protocol_version": PROTOCOL_VERSION,
    }, to=sid)


@sio.event
async def handshake(sid: str, data: dict):
    """Validate client protocol version on connection."""
    client_version = data.get("protocol_version", "unknown")
    if client_version != PROTOCOL_VERSION:
        logger.warning(
            f"[WS] Protocol mismatch: client={client_version}, server={PROTOCOL_VERSION}"
        )
    await _emit_snapshot(to=sid, last_sequence_num=int(data.get("last_sequence_num", 0) or 0))


@sio.event
async def COMMAND_RECEIVED(sid: str, data: dict):
    """Handle incoming commands from the frontend UI (protocol envelope)."""
    await _process_command(sid, data)


@sio.event
async def command(sid: str, data: dict):
    """Handle incoming commands from the frontend UI (socket.emit('command'))."""
    await _process_command(sid, data)


@sio.event
async def approve_command(sid: str, data: dict):
    payload = data.get("payload", data)
    command_id = payload.get("command_id")
    if not command_id:
        return
    try:
        record = get_approval_manager().approve(str(command_id))
        await emit_approval_resolved(record, decision="granted")
        await emit_event(
            ProtocolEventType.COMMAND_APPROVED,
            {"command": record.to_dict()},
            trace_id=record.trace_id,
            source=Component.GUARD,
            runtime_phase=get_runtime_authority(_session_id).current_state(),
        )
        if record.status != CommandStatus.APPROVED:
            await emit_command_status(
                command_id=record.command_id,
                status=record.status,
                trace_id=record.trace_id,
                risk_level=record.risk_level,
                reason=record.reason,
                verification_state=record.verification_state,
            )
            await _emit_snapshot(to=sid)
            return
        if is_maintenance_action_record(record):
            await execute_maintenance_action_record(record, sid=sid)
            return
        await enqueue_approved_command_for_resume(record, sid=sid, mode=payload.get("mode", "auto"))
    except Exception as e:
        logger.error("[WS] Failed to approve command: %s", e)


@sio.event
async def request_maintenance_action(sid: str, data: dict):
    payload = data.get("payload", data)
    proposal_id = payload.get("proposal_id")
    if not proposal_id:
        return
    try:
        report = get_last_maintenance_scan() or await asyncio.to_thread(
            run_read_only_maintenance_scan,
            **maintenance_scan_context(),
        )
        record = request_maintenance_action_approval(str(proposal_id), report=report)
        await emit_approval_required(record.to_dict(), trace_id=record.trace_id)
        refreshed_report = await asyncio.to_thread(run_read_only_maintenance_scan, **maintenance_scan_context())
        await emit_event(
            ProtocolEventType.MAINTENANCE_SCAN_COMPLETED,
            {"report": refreshed_report, "reason": "maintenance_action_approval_requested"},
            trace_id=record.trace_id,
            source=Component.SYSTEM,
            runtime_phase=get_runtime_authority(_session_id).current_state(),
        )
        await _emit_snapshot(to=sid)
    except Exception as e:
        logger.error("[WS] Failed to request maintenance action approval: %s", e)


@sio.event
async def reject_command(sid: str, data: dict):
    payload = data.get("payload", data)
    command_id = payload.get("command_id")
    if not command_id:
        return
    try:
        record = get_approval_manager().reject(str(command_id), reason=str(payload.get("reason") or "rejected by user"))
        await emit_approval_resolved(record, decision="denied")
        await emit_event(
            ProtocolEventType.COMMAND_REJECTED,
            {"command": record.to_dict()},
            trace_id=record.trace_id,
            source=Component.GUARD,
            runtime_phase=get_runtime_authority(_session_id).current_state(),
        )
        current = get_runtime_authority(_session_id).current_state()
        if current not in (RuntimeState.IDLE, RuntimeState.COMPLETED, RuntimeState.FAILED):
            await emit_state_change(current.value, RuntimeState.IDLE.value, reason="Command rejected")
        await _emit_snapshot(to=sid)
    except Exception as e:
        logger.error("[WS] Failed to reject command: %s", e)


@sio.event
async def resolve_approval(sid: str, data: dict):
    payload = data.get("payload", data)
    approval_id = payload.get("approval_id") or payload.get("decision_id")
    decision = str(payload.get("decision") or "").strip().lower()
    if not approval_id or decision not in {"grant", "granted", "approve", "approved", "deny", "denied", "reject", "rejected"}:
        return
    approved = decision in {"grant", "granted", "approve", "approved"}
    try:
        record = get_approval_manager().resolve_approval(
            str(approval_id),
            approved=approved,
            reason=str(payload.get("reason") or ""),
        )
        await emit_approval_resolved(record, decision="granted" if approved else "denied")
        resume_attempted = False
        if approved and record.status == CommandStatus.APPROVED:
            resume_attempted = True
            await enqueue_approved_command_for_resume(record, sid=sid, mode=payload.get("mode", "auto"))
        elif not approved:
            await emit_event(
                ProtocolEventType.COMMAND_REJECTED,
                {"command": record.to_dict()},
                trace_id=record.trace_id,
                source=Component.GUARD,
                runtime_phase=get_runtime_authority(_session_id).current_state(),
            )
        if record.status != CommandStatus.APPROVED and not resume_attempted:
            await emit_command_status(
                command_id=record.command_id,
                status=record.status,
                trace_id=record.trace_id,
                risk_level=record.risk_level,
                reason=record.reason,
                verification_state=record.verification_state,
            )
        await _emit_snapshot(to=sid)
    except Exception as e:
        logger.error("[WS] Failed to resolve approval: %s", e)


@sio.event
async def resolve_clarification(sid: str, data: dict):
    payload = data.get("payload", data)
    clarification_id = payload.get("clarification_id") or payload.get("decision_id")
    if not clarification_id:
        return
    try:
        record = get_approval_manager().resolve_clarification(
            str(clarification_id),
            answer=payload.get("answer"),
            cancelled=bool(payload.get("cancelled", False)),
            reason=str(payload.get("reason") or ""),
        )
        await emit_clarification_resolved(record)
        await emit_command_status(
            command_id=record.command_id,
            status=record.status,
            trace_id=record.trace_id,
            risk_level=record.risk_level,
            reason=record.reason,
            verification_state=record.verification_state,
        )
        await _emit_snapshot(to=sid)
    except Exception as e:
        logger.error("[WS] Failed to resolve clarification: %s", e)


@sio.event
async def cancel_command(sid: str, data: dict):
    payload = data.get("payload", data)
    command_id = payload.get("command_id")
    if not command_id:
        active = get_approval_manager().snapshot().get("active_command")
        command_id = active.get("command_id") if active else None
    if not command_id:
        return
    try:
        record = get_approval_manager().cancel(str(command_id), reason=str(payload.get("reason") or "cancelled by user"))
        await emit_event(
            ProtocolEventType.COMMAND_CANCELLED,
            {"command": record.to_dict()},
            trace_id=record.trace_id,
            source=Component.SYSTEM,
            runtime_phase=get_runtime_authority(_session_id).current_state(),
            severity=Severity.WARNING,
        )
        current = get_runtime_authority(_session_id).current_state()
        if current not in (RuntimeState.IDLE, RuntimeState.COMPLETED, RuntimeState.FAILED):
            await emit_state_change(current.value, RuntimeState.IDLE.value, reason="Command cancelled")
        await _emit_snapshot(to=sid)
    except Exception as e:
        logger.error("[WS] Failed to cancel command: %s", e)


@sio.event
async def maintenance_scan(sid: str, data: dict | None = None):
    await emit_event(
        ProtocolEventType.MAINTENANCE_SCAN_STARTED,
        {"read_only": True, "scan_version": "maintenance-scan/1"},
        source=Component.SYSTEM,
        runtime_phase=get_runtime_authority(_session_id).current_state(),
    )
    report = await asyncio.to_thread(run_read_only_maintenance_scan, **maintenance_scan_context())
    await emit_event(
        ProtocolEventType.MAINTENANCE_SCAN_COMPLETED,
        {"report": report},
        source=Component.SYSTEM,
        runtime_phase=get_runtime_authority(_session_id).current_state(),
    )
    await _emit_snapshot(to=sid)


async def execute_maintenance_action_record(record, *, sid: str | None = None) -> CommandResponse:
    """Execute an approved maintenance action through existing journal/UI truth surfaces."""
    trace_id = record.trace_id or str(uuid4())
    started = time.perf_counter()
    manager = get_approval_manager()
    proposal = dict(record.metadata.get("proposal") or {})
    action_id = str(uuid4())
    action_name = str(proposal.get("action") or "maintenance_action")

    running = manager.mark_running(
        record.command_id,
        trace_id=trace_id,
        risk_level=RiskLevel.MEDIUM,
        verification_state="unverified",
    )
    await emit_command_status(
        command_id=record.command_id,
        status=CommandStatus.RUNNING,
        trace_id=trace_id,
        risk_level=running.risk_level,
        reason=running.reason,
        verification_state=running.verification_state,
    )
    await emit_action_started(
        action_id=action_id,
        tool=action_name,
        trace_id=trace_id,
        target=str(proposal.get("approval_text") or proposal.get("title") or action_name),
    )

    action_result = await asyncio.to_thread(execute_maintenance_action_proposal, proposal)
    verification_state = (
        action_result.execution_evidence.verification_state
        if action_result.execution_evidence
        else "unverified"
    )
    if action_result.success:
        await emit_action_completed(
            action_id=action_id,
            success=True,
            latency_ms=action_result.metrics.execution_time_ms,
            trace_id=trace_id,
            execution_evidence=action_result.execution_evidence,
        )
        final_status = CommandStatus.EXECUTED
        final_state = RuntimeState.COMPLETED.value
    else:
        await emit_action_failed(
            action_id=action_id,
            error=action_result.output,
            trace_id=trace_id,
            is_recoverable=False,
            execution_evidence=action_result.execution_evidence,
        )
        final_status = CommandStatus.FAILED
        final_state = RuntimeState.FAILED.value

    completed = manager.complete(
        record.command_id,
        final_status,
        reason=action_result.output,
        verification_state=verification_state,
    )
    await emit_command_status(
        command_id=record.command_id,
        status=final_status,
        trace_id=trace_id,
        risk_level=completed.risk_level,
        reason=completed.reason,
        verification_state=completed.verification_state,
    )
    await emit_task_finished(trace_id=trace_id, final_state=final_state)

    try:
        report = await asyncio.to_thread(run_read_only_maintenance_scan, **maintenance_scan_context())
        await emit_event(
            ProtocolEventType.MAINTENANCE_SCAN_COMPLETED,
            {"report": report, "reason": "maintenance_action_rescan"},
            trace_id=trace_id,
            source=Component.SYSTEM,
            runtime_phase=get_runtime_authority(_session_id).current_state(),
        )
    except Exception as exc:
        logger.warning("[WS] Maintenance rescan after action failed: %s", exc)
    if sid:
        await _emit_snapshot(to=sid)

    return response_from_maintenance_action(
        record=completed,
        action_result=action_result,
        trace_id=trace_id,
        duration_ms=(time.perf_counter() - started) * 1000,
    )


async def _process_command(sid: str, data: dict):
    """Shared command processing logic for both event channels."""
    # Support both protocol envelope format and direct payload
    payload = data.get("payload", data)
    text = payload.get("text", "")
    mode_str = payload.get("mode", "auto")
    
    logger.info(f"[WS] Received command from {sid}: {text} (mode: {mode_str})")
    
    try:
        if text in RAW_CONTROL_COMMANDS:
            trace_id = str(uuid4())
            logger.warning("[WS] Raw control command quarantined: %s", text)
            record = get_approval_manager().create_received(text)
            blocked = get_approval_manager().mark_blocked(
                record.command_id,
                trace_id=trace_id,
                risk_level=RiskLevel.HIGH,
                reason=RAW_CONTROL_COMMANDS[text],
                verification_state="unverified",
            )
            blocked.metadata.update(
                {
                    "not_executed": True,
                    "mutation_performed": False,
                    "raw_control_quarantined": True,
                    "frontend_authority": False,
                    "control_command": text,
                    "mode": mode_str,
                }
            )
            await emit_command_status(
                command_id=blocked.command_id,
                status=blocked.status,
                trace_id=blocked.trace_id,
                risk_level=blocked.risk_level,
                reason=blocked.reason,
                verification_state=blocked.verification_state,
            )
            await _emit_snapshot(to=sid)
            return

        record = get_approval_manager().create_received(text)
        command = QueuedCommand(
            sid=sid,
            text=text,
            mode=mode_str,
            received_at=time.time(),
            command_id=record.command_id,
        )
        try:
            _command_queue.put_nowait(command)
        except asyncio.QueueFull:
            await emit_event(
                ProtocolEventType.DETERMINISM_BREACH,
                {
                    "reason": "Command queue full",
                    "queue_depth": _command_queue.qsize(),
                    "queue_capacity": _command_queue_capacity,
                },
                source=Component.SYSTEM,
                severity=Severity.WARNING,
                runtime_phase=get_runtime_authority(_session_id).current_state(),
            )
            return

        get_runtime_authority(_session_id, queue_capacity=_command_queue_capacity).set_queue(
            depth=_command_queue.qsize(),
            capacity=_command_queue_capacity,
        )
        await emit_event(
            ProtocolEventType.COMMAND_RECEIVED,
            {
                "text": text,
                "mode": mode_str,
                "queued": True,
                "queue_depth": _command_queue.qsize(),
                "queue_capacity": _command_queue_capacity,
            },
            source=Component.SYSTEM,
            runtime_phase=get_runtime_authority(_session_id).current_state(),
        )
        
    except Exception as e:
        logger.error(f"[WS] Failed to dispatch command to orchestrator: {e}")


# ═══════════════════════════════════════════════════════════════════
# EVENT EMISSION API — Called by orchestrator/executor
# ═══════════════════════════════════════════════════════════════════

async def _command_worker_loop():
    """Serial command executor. Only one command pipeline mutates runtime state at a time."""
    from aegis.core.schemas import CommandRequest, ExecutionMode
    from aegis.orchestrator.orchestrator import get_orchestrator

    authority = get_runtime_authority(_session_id, queue_capacity=_command_queue_capacity)
    while True:
        command = await _command_queue.get()
        authority.set_queue(depth=_command_queue.qsize(), capacity=_command_queue_capacity)
        response = None
        try:
            current = authority.current_state()
            if current in (RuntimeState.COMPLETED, RuntimeState.FAILED):
                await emit_state_change(current.value, RuntimeState.IDLE.value, reason="Command worker reset terminal state")

            mode = ExecutionMode.LIVE if command.mode == "auto" else ExecutionMode.DRY_RUN
            request = CommandRequest(
                text=command.text,
                mode=mode,
                context={
                    "command_id": command.command_id,
                    "approval_granted": command.approval_granted,
                    "cancellation_token": get_approval_manager().token_for(command.command_id) if command.command_id else None,
                },
            )
            response = await get_orchestrator().process(request)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.exception("[WS] Command worker failed: %s", e)
            current = authority.current_state()
            if current != RuntimeState.FAILED:
                await emit_state_change(current.value, RuntimeState.FAILED.value, reason=str(e))
            await emit_task_finished(
                trace_id=response.trace_id if response else str(uuid4()),
                final_state=RuntimeState.FAILED.value,
            )
        finally:
            authority.finish_command(trace_id=response.trace_id if response else None)
            _command_queue.task_done()
            authority.set_queue(depth=_command_queue.qsize(), capacity=_command_queue_capacity)


def start_runtime_workers():
    start_telemetry_loop()
    start_command_worker_loop()


def start_command_worker_loop():
    global _command_worker_task
    if _command_worker_task is None or _command_worker_task.done():
        _command_worker_task = asyncio.create_task(_command_worker_loop())


def stop_runtime_workers():
    global _heartbeat_task, _command_worker_task
    for task in (_heartbeat_task, _command_worker_task):
        if task and not task.done():
            task.cancel()
    _heartbeat_task = None
    _command_worker_task = None


async def emit_event(
    event_type: ProtocolEventType,
    payload: Dict[str, Any],
    *,
    trace_id: Optional[str] = None,
    causation_id: Optional[str] = None,
    span_id: Optional[str] = None,
    runtime_phase: Optional[RuntimeState | str] = None,
    source: Optional[Component] = None,
    severity: Severity = Severity.INFO,
):
    """
    The ONLY authorized way to send events to the frontend.
    Creates a protocol-compliant event and broadcasts to all clients.
    """
    authority = get_runtime_authority(_session_id, queue_capacity=_command_queue_capacity)
    if event_type == ProtocolEventType.COMMAND_RECEIVED and trace_id:
        authority.start_command(
            trace_id=trace_id,
            command=str(payload.get("text", "")),
            task_id=span_id,
        )
    elif event_type == ProtocolEventType.ACTION_STARTED:
        authority.set_active_span(span_id=span_id, tool=str(payload.get("tool", "")))
    elif event_type == ProtocolEventType.RECOVERY_TRIGGERED:
        authority.set_recovery_depth(int(payload.get("depth", 0) or 0))
    elif event_type == ProtocolEventType.TASK_FINISHED:
        authority.finish_command(trace_id=trace_id)

    event = await _create_and_append_event(
        event_type,
        payload=payload,
        trace_id=trace_id,
        causation_id=causation_id,
        span_id=span_id,
        session_id=_session_id,
        runtime_phase=runtime_phase,
        source=source,
        severity=severity,
    )

    if _connected_clients:
        await sio.emit(event_type.value, event.to_dict())
    return event


async def emit_command_status(
    *,
    command_id: str,
    status: CommandStatus,
    trace_id: str | None = None,
    risk_level: RiskLevel = RiskLevel.NONE,
    reason: str = "",
    verification_state: str = "unverified",
):
    event_type = ProtocolEventType.COMMAND_STATUS_CHANGED
    if status == CommandStatus.BLOCKED:
        event_type = ProtocolEventType.COMMAND_BLOCKED
    elif status == CommandStatus.CANCELLED:
        event_type = ProtocolEventType.COMMAND_CANCELLED

    record = get_approval_manager().get(command_id)
    await emit_event(
        event_type,
        {
            "command_id": command_id,
            "status": status.value,
            "risk_level": risk_level.value,
            "reason": reason,
            "verification_state": verification_state,
            "command": record.to_dict() if record else None,
        },
        trace_id=trace_id,
        runtime_phase=get_runtime_authority(_session_id).current_state(),
        source=Component.ORCHESTRATOR,
        severity=Severity.WARNING if status in (CommandStatus.BLOCKED, CommandStatus.CANCELLED) else Severity.INFO,
    )


async def emit_approval_required(command: dict[str, Any], *, trace_id: str | None = None):
    await emit_event(
        ProtocolEventType.APPROVAL_REQUIRED,
        {"command": command},
        trace_id=trace_id,
        runtime_phase=get_runtime_authority(_session_id).current_state(),
        source=Component.GUARD,
        severity=Severity.WARNING,
    )


async def emit_approval_resolved(record, *, decision: str):
    approval_id = record.metadata.get("approval_id")
    await emit_event(
        ProtocolEventType.APPROVAL_RESOLVED,
        {
            "command_id": record.command_id,
            "approval_id": approval_id,
            "decision": decision,
            "approval_status": record.metadata.get("approval_resolution_status"),
            "command_status": record.status.value,
            "reason": record.reason,
            "not_executed": True,
            "executed": False,
            "mutation_performed": False,
            "command": record.to_dict(),
        },
        trace_id=record.trace_id,
        runtime_phase=get_runtime_authority(_session_id).current_state(),
        source=Component.GUARD,
        severity=Severity.WARNING if record.status in (CommandStatus.BLOCKED, CommandStatus.REJECTED) else Severity.INFO,
    )


async def emit_clarification_resolved(record):
    clarification_id = record.metadata.get("clarification_id")
    status = record.metadata.get("clarification_resolution_status")
    await emit_event(
        ProtocolEventType.CLARIFICATION_RESOLVED,
        {
            "command_id": record.command_id,
            "clarification_id": clarification_id,
            "clarification_status": status,
            "answer": record.metadata.get("clarification_answer"),
            "command_status": record.status.value,
            "reason": record.reason,
            "not_executed": True,
            "executed": False,
            "mutation_performed": False,
            "completed_without_execution": True,
            "command": record.to_dict(),
        },
        trace_id=record.trace_id,
        runtime_phase=get_runtime_authority(_session_id).current_state(),
        source=Component.GUARD,
        severity=Severity.WARNING,
    )


async def _emit_snapshot(to: str, last_sequence_num: int = 0):
    journal = get_runtime_journal()
    journal_snapshot, runtime_snapshot = _build_runtime_snapshot(journal)
    missed_events = _replayable_journal_events_after(journal, int(last_sequence_num or 0))
    journal_tail_sequence = int(journal_snapshot.get("last_sequence_num", 0) or 0)
    def add_truth_sync(snapshot) -> None:
        snapshot.payload["truth_sync"] = {
            "source_of_truth": "backend_snapshot_protocol_event_journal",
            "snapshot_sequence_num": journal_tail_sequence,
            "journal_tail_sequence_num": journal_tail_sequence,
            "client_last_sequence_num": int(last_sequence_num or 0),
            "missed_event_count": len(missed_events),
            "replay_required": bool(missed_events),
        }

    snapshot = _create_control_event(
        ProtocolEventType.SNAPSHOT_CREATED,
        payload={
            "session_id": _session_id,
            "journal": journal_snapshot,
            "runtime": runtime_snapshot,
            "current_state": runtime_snapshot["fsm_state"],
            "snapshot_since_sequence": last_sequence_num,
            "missed_events": missed_events,
            "missed_event_count": len(missed_events),
        },
        session_id=_session_id,
        runtime_phase=runtime_snapshot["fsm_state"],
        source=Component.SYSTEM,
    )
    add_truth_sync(snapshot)
    await sio.emit(ProtocolEventType.SNAPSHOT_CREATED.value, snapshot.to_dict(), to=to)


def _build_runtime_snapshot(journal) -> tuple[dict[str, Any], dict[str, Any]]:
    journal_snapshot = journal.snapshot()
    recent_events = journal.recent_events()
    scoped_events = [
        event
        for event in recent_events
        if not _session_id or event.get("session_id") == _session_id
    ]
    runtime_snapshot = get_runtime_authority(_session_id, queue_capacity=_command_queue_capacity).snapshot(journal_snapshot)
    runtime_snapshot["commands"] = get_approval_manager().snapshot()
    runtime_snapshot["non_executable_decisions"] = project_non_executable_events_to_snapshot(scoped_events)
    runtime_snapshot["maintenance_scan"] = get_last_maintenance_scan()
    runtime_snapshot["app_registry"] = get_app_registry_snapshot()
    runtime_snapshot["tool_registry"] = get_tool_registry_snapshot()
    runtime_snapshot["action_timeline"] = project_action_timeline(
        recent_events,
        limit=50,
        session_id=_session_id,
    )
    return journal_snapshot, runtime_snapshot


async def emit_action_started(
    action_id: str,
    tool: str,
    trace_id: str,
    target: Optional[str] = None,
    is_dry_run: bool = False,
):
    await emit_event(
        ProtocolEventType.ACTION_STARTED,
        payload={
            "action_id": action_id,
            "tool": tool,
            "target": target or f"Executing {tool}",
            "is_dry_run": is_dry_run,
        },
        trace_id=trace_id,
        runtime_phase=RuntimeState.EXECUTING,
        source=Component.EXECUTOR,
    )


async def emit_action_completed(
    action_id: str,
    success: bool,
    latency_ms: float,
    trace_id: str,
    retries: int = 0,
    execution_evidence: Any | None = None,
):
    evidence_payload = None
    if execution_evidence is not None:
        if hasattr(execution_evidence, "model_dump"):
            evidence_payload = execution_evidence.model_dump()
        elif isinstance(execution_evidence, dict):
            evidence_payload = execution_evidence
        else:
            evidence_payload = {"verification_state": "unverified", "details": str(execution_evidence)}

    verification_state = str((evidence_payload or {}).get("verification_state") or "")
    verification_passed = success if not verification_state else verification_state == "verified"
    verification = {
        "passed": verification_passed,
        "method": (evidence_payload or {}).get("method"),
        "details": (evidence_payload or {}).get("verification_state"),
    }
    payload = {
        "action_id": action_id,
        "success": success,
        "latency_ms": latency_ms,
        "retries": retries,
        "verification": verification,
    }
    if evidence_payload is not None:
        payload["execution_evidence"] = evidence_payload

    await emit_event(
        ProtocolEventType.ACTION_COMPLETED,
        payload=payload,
        trace_id=trace_id,
        runtime_phase=RuntimeState.VERIFYING,
        source=Component.EXECUTOR,
    )
    if evidence_payload is not None:
        await emit_verification_result(
            action_id=action_id,
            trace_id=trace_id,
            passed=verification_passed,
            execution_evidence=evidence_payload,
            details=verification["details"],
        )


async def emit_action_failed(
    action_id: str,
    error: str,
    trace_id: str,
    is_recoverable: bool = True,
    execution_evidence: Any | None = None,
):
    evidence_payload = None
    if execution_evidence is not None:
        if hasattr(execution_evidence, "model_dump"):
            evidence_payload = execution_evidence.model_dump()
        elif isinstance(execution_evidence, dict):
            evidence_payload = execution_evidence
        else:
            evidence_payload = {"verification_state": "failed", "details": str(execution_evidence)}

    verification = {
        "passed": False,
        "method": (evidence_payload or {}).get("method"),
        "details": (evidence_payload or {}).get("verification_state") or error,
    }
    payload = {
        "action_id": action_id,
        "error": error,
        "is_recoverable": is_recoverable,
        "verification": verification,
    }
    if evidence_payload is not None:
        payload["execution_evidence"] = evidence_payload

    await emit_event(
        ProtocolEventType.ACTION_FAILED,
        payload=payload,
        trace_id=trace_id,
        runtime_phase=RuntimeState.RECOVERING if is_recoverable else RuntimeState.FAILED,
        source=Component.EXECUTOR,
        severity=Severity.ERROR,
    )
    if evidence_payload is not None:
        await emit_verification_result(
            action_id=action_id,
            trace_id=trace_id,
            passed=False,
            execution_evidence=evidence_payload,
            details=verification["details"],
            error=error,
        )


async def emit_verification_result(
    *,
    action_id: str,
    trace_id: str,
    passed: bool,
    execution_evidence: dict[str, Any],
    details: str | None = None,
    error: str | None = None,
):
    """Emit a journal-backed verification event derived from real execution evidence."""
    event_type = ProtocolEventType.VERIFICATION_PASSED if passed else ProtocolEventType.VERIFICATION_FAILED
    payload: Dict[str, Any] = {
        "action_id": action_id,
        "passed": passed,
        "method": execution_evidence.get("method"),
        "details": details or execution_evidence.get("verification_reason") or execution_evidence.get("verification_state"),
        "verification_state": execution_evidence.get("verification_state", "unverified"),
        "verifier": execution_evidence.get("verifier"),
        "execution_evidence": execution_evidence,
    }
    if error:
        payload["error"] = error

    await emit_event(
        event_type,
        payload,
        trace_id=trace_id,
        runtime_phase=RuntimeState.VERIFYING if passed else RuntimeState.RECOVERING,
        source=Component.VALIDATOR,
        severity=Severity.INFO if passed else Severity.WARNING,
    )


async def emit_telemetry(
    determinism_score: Optional[float] = None,
    recovery_budget: Optional[float] = None,
    vram_usage_text: Optional[str] = None,
    active_app: Optional[str] = None,
    active_model: Optional[str] = None,
    cpu_percent: Optional[float] = None,
    memory_percent: Optional[float] = None,
    uptime_seconds: Optional[int] = None,
    io_throughput: Optional[str] = None,
    websocket_clients: Optional[int] = None,
):
    payload: Dict[str, Any] = {}
    if determinism_score is not None:
        payload["determinism_score"] = determinism_score
    if recovery_budget is not None:
        payload["recovery_budget"] = recovery_budget
    if vram_usage_text is not None:
        payload["vram_usage_text"] = vram_usage_text
    if active_app is not None:
        payload["active_app"] = active_app
    if active_model is not None:
        payload["active_model"] = active_model
    if cpu_percent is not None:
        payload["cpu_percent"] = cpu_percent
    if memory_percent is not None:
        payload["memory_percent"] = memory_percent
    if uptime_seconds is not None:
        payload["uptime_seconds"] = uptime_seconds
    if io_throughput is not None:
        payload["io_throughput"] = io_throughput
    if websocket_clients is not None:
        payload["websocket_clients"] = websocket_clients

    await emit_event(
        ProtocolEventType.TELEMETRY_UPDATE,
        payload=payload,
        runtime_phase=None,
        source=Component.SYSTEM,
    )


async def emit_state_change(
    from_state: str,
    to_state: str,
    reason: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> bool:
    authority = get_runtime_authority(_session_id, queue_capacity=_command_queue_capacity)
    effective_from, effective_to, legal = authority.transition(
        to_state,
        from_state=from_state,
        reason=reason,
    )

    if not legal:
        await emit_event(
            ProtocolEventType.DETERMINISM_BREACH,
            payload={
                "reason": "Illegal FSM transition requested",
                "from": effective_from.value,
                "to": effective_to.value,
            },
            trace_id=trace_id,
            runtime_phase=effective_from,
            source=Component.ORCHESTRATOR,
            severity=Severity.ERROR,
        )
        return False

    await emit_event(
        ProtocolEventType.STATE_CHANGE,
        payload={
            "from": effective_from.value,
            "to": effective_to.value,
            "reason": reason or "",
        },
        trace_id=trace_id,
        runtime_phase=effective_to,
        source=Component.ORCHESTRATOR,
    )
    return True


async def emit_task_finished(trace_id: str, final_state: str = "COMPLETED"):
    await emit_event(
        ProtocolEventType.TASK_FINISHED,
        payload={"final_state": final_state},
        trace_id=trace_id,
        runtime_phase=final_state,
        source=Component.ORCHESTRATOR,
    )


# ─── TELEMETRY HEARTBEAT LOOP ──────────────────────────────────────

async def _telemetry_loop():
    """Periodic telemetry broadcast (every 10s)."""
    import psutil
    start_time = time.time()
    
    # Store previous disk IO to calculate throughput
    try:
        last_disk_io = psutil.disk_io_counters()
        last_disk_time = time.time()
    except Exception:
        last_disk_io = None
        last_disk_time = time.time()

    while True:
        await asyncio.sleep(2)  # Update every 2 seconds for a more "live" feel
        if _connected_clients:
            try:
                mem = psutil.virtual_memory()
                cpu = psutil.cpu_percent(interval=None)
                uptime = int(time.time() - psutil.boot_time())
                
                # Calculate I/O throughput in MB/s
                io_str = "0.0 MB/s"
                try:
                    current_disk_io = psutil.disk_io_counters()
                    current_time = time.time()
                    if current_disk_io and last_disk_io:
                        read_bytes = current_disk_io.read_bytes - last_disk_io.read_bytes
                        write_bytes = current_disk_io.write_bytes - last_disk_io.write_bytes
                        time_diff = current_time - last_disk_time
                        if time_diff > 0:
                            total_mb_per_sec = ((read_bytes + write_bytes) / (1024 * 1024)) / time_diff
                            io_str = f"{total_mb_per_sec:.1f} MB/s"
                    
                    last_disk_io = current_disk_io
                    last_disk_time = current_time
                except Exception:
                    pass

                # Get active window using PyGetWindow
                active_app_title = "Desktop"
                try:
                    import pygetwindow as gw
                    active_window = gw.getActiveWindow()
                    if active_window and active_window.title:
                        active_app_title = active_window.title[:40] + ("..." if len(active_window.title) > 40 else "")
                except Exception:
                    pass
                from aegis.core.config import get_settings
                settings = get_settings()

                await emit_telemetry(
                    active_model=settings.models.chat_model,
                    cpu_percent=cpu,
                    memory_percent=mem.percent,
                    uptime_seconds=uptime,
                    io_throughput=io_str,
                    active_app=active_app_title,
                    websocket_clients=len(_connected_clients),
                )
            except Exception as e:
                logger.error(f"Failed to gather telemetry: {e}")

def start_telemetry_loop():
    global _heartbeat_task
    if _heartbeat_task is None or _heartbeat_task.done():
        _heartbeat_task = asyncio.create_task(_telemetry_loop())


# ─── ASGI APP ───────────────────────────────────────────────────────

def create_socketio_app(fastapi_app):
    """
    Wraps the FastAPI app with socket.io ASGI middleware.
    Call this in main.py instead of using app directly.
    """
    return socketio.ASGIApp(sio, other_asgi_app=fastapi_app)
