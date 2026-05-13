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
from typing import Any, Dict, Optional, Set
from uuid import uuid4

import socketio

from aegis.core.protocol import (
    PROTOCOL_VERSION,
    ProtocolEventType,
    RuntimeState,
    Component,
    Severity,
    create_event,
)
from aegis.core.commands import get_approval_manager
from aegis.core.action_timeline import project_action_timeline
from aegis.core.app_map import get_app_registry_snapshot
from aegis.tools.registry import get_tool_registry_snapshot
from aegis.core.event_journal import get_runtime_journal
from aegis.core.maintenance import get_last_maintenance_scan, run_read_only_maintenance_scan
from aegis.core.runtime_authority import get_runtime_authority
from aegis.core.constants import CommandStatus, RiskLevel

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


@dataclass(frozen=True)
class QueuedCommand:
    sid: str
    text: str
    mode: str
    received_at: float
    command_id: str | None = None
    approval_granted: bool = False

# ─── LIFECYCLE ──────────────────────────────────────────────────────

@sio.event
async def connect(sid: str, environ: dict):
    _connected_clients.add(sid)
    logger.info(f"[WS] Client connected: {sid} (total: {len(_connected_clients)})")
    journal = get_runtime_journal()
    journal_snapshot, runtime_snapshot = _build_runtime_snapshot(journal)

    # Send handshake
    handshake = create_event(
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
    await asyncio.to_thread(get_runtime_journal().append, handshake)
    await sio.emit("SYSTEM_ONLINE", handshake.to_dict(), to=sid)
    await _emit_snapshot(to=sid, last_sequence_num=handshake.sequence_num)


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
        await emit_event(
            ProtocolEventType.COMMAND_APPROVED,
            {"command": record.to_dict()},
            trace_id=record.trace_id,
            source=Component.GUARD,
            runtime_phase=get_runtime_authority(_session_id).current_state(),
        )
        command = QueuedCommand(
            sid=sid,
            text=record.text,
            mode=payload.get("mode", "auto"),
            received_at=time.time(),
            command_id=record.command_id,
            approval_granted=True,
        )
        _command_queue.put_nowait(command)
        get_runtime_authority(_session_id, queue_capacity=_command_queue_capacity).set_queue(
            depth=_command_queue.qsize(),
            capacity=_command_queue_capacity,
        )
    except Exception as e:
        logger.error("[WS] Failed to approve command: %s", e)


@sio.event
async def reject_command(sid: str, data: dict):
    payload = data.get("payload", data)
    command_id = payload.get("command_id")
    if not command_id:
        return
    try:
        record = get_approval_manager().reject(str(command_id), reason=str(payload.get("reason") or "rejected by user"))
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
    report = await asyncio.to_thread(run_read_only_maintenance_scan)
    await emit_event(
        ProtocolEventType.MAINTENANCE_SCAN_COMPLETED,
        {"report": report},
        source=Component.SYSTEM,
        runtime_phase=get_runtime_authority(_session_id).current_state(),
    )
    await _emit_snapshot(to=sid)


async def _process_command(sid: str, data: dict):
    """Shared command processing logic for both event channels."""
    # Support both protocol envelope format and direct payload
    payload = data.get("payload", data)
    text = payload.get("text", "")
    mode_str = payload.get("mode", "auto")
    
    logger.info(f"[WS] Received command from {sid}: {text} (mode: {mode_str})")
    
    try:
        if text == "/force_idle":
            logger.warning("[WS] EMERGENCY HALT triggered by client.")
            current = get_runtime_authority(_session_id).current_state()
            await emit_state_change(current.value, RuntimeState.IDLE.value, reason="Emergency halt")
            return
            
        if text == "/reset_memory":
            logger.warning("[WS] CONTEXT RESET triggered by client.")
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

    event = create_event(
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

    await asyncio.to_thread(get_runtime_journal().append, event)

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


async def _emit_snapshot(to: str, last_sequence_num: int = 0):
    journal = get_runtime_journal()
    journal_snapshot, runtime_snapshot = _build_runtime_snapshot(journal)
    snapshot = create_event(
        ProtocolEventType.SNAPSHOT_CREATED,
        payload={
            "session_id": _session_id,
            "journal": journal_snapshot,
            "runtime": runtime_snapshot,
            "current_state": runtime_snapshot["fsm_state"],
            "snapshot_since_sequence": last_sequence_num,
            "missed_events": journal.events_after(last_sequence_num) if last_sequence_num > 0 else [],
        },
        session_id=_session_id,
        runtime_phase=runtime_snapshot["fsm_state"],
        source=Component.SYSTEM,
    )
    await asyncio.to_thread(journal.append, snapshot)
    await sio.emit(ProtocolEventType.SNAPSHOT_CREATED.value, snapshot.to_dict(), to=to)


def _build_runtime_snapshot(journal) -> tuple[dict[str, Any], dict[str, Any]]:
    journal_snapshot = journal.snapshot()
    runtime_snapshot = get_runtime_authority(_session_id, queue_capacity=_command_queue_capacity).snapshot(journal_snapshot)
    runtime_snapshot["commands"] = get_approval_manager().snapshot()
    runtime_snapshot["maintenance_scan"] = get_last_maintenance_scan()
    runtime_snapshot["app_registry"] = get_app_registry_snapshot()
    runtime_snapshot["tool_registry"] = get_tool_registry_snapshot()
    runtime_snapshot["action_timeline"] = project_action_timeline(
        journal.recent_events(),
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
):
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
        return

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
