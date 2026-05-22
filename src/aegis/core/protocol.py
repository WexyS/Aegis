"""
══════════════════════════════════════════════════════════════════════
AEGIS RUNTIME PROTOCOL v1.0 — Python Side
══════════════════════════════════════════════════════════════════════

Mirror of frontend/src/contracts/protocol.ts.

Both sides MUST agree on:
  - Event type enum values
  - FSM state enum values
  - Payload structures
  - Protocol version

This file is the canonical Python reference.
══════════════════════════════════════════════════════════════════════
"""

from enum import Enum, unique
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any
from uuid import uuid4
import hashlib
import json
import time
import threading


PROTOCOL_VERSION = "1.1.0"
SCHEMA_VERSION = "runtime-event/1.1"
# Historical journals use this literal genesis marker. Do not change it without
# a journal migration, or existing hash chains will appear broken.
GENESIS_HASH = "genesis"

# Monotonic sequence counter for event ordering
_sequence_lock = threading.Lock()
_sequence_counter = 0

def _next_sequence() -> int:
    global _sequence_counter
    with _sequence_lock:
        _sequence_counter += 1
        return _sequence_counter


def ensure_sequence_at_least(sequence_num: int) -> None:
    """Hydrate the monotonic sequence counter from persisted journal state."""
    global _sequence_counter
    with _sequence_lock:
        _sequence_counter = max(_sequence_counter, int(sequence_num))


def reset_sequence_for_testing(sequence_num: int = 0) -> None:
    """Reset the in-process event sequence counter for isolated tests only."""
    global _sequence_counter
    with _sequence_lock:
        _sequence_counter = int(sequence_num)


@unique
class RuntimeState(str, Enum):
    """FSM states — must match frontend RuntimeState enum exactly."""
    IDLE = "IDLE"
    THINKING = "THINKING"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    RECOVERING = "RECOVERING"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"


@unique
class ProtocolEventType(str, Enum):
    """Event types — must match frontend EventTypeEnum exactly."""
    # Lifecycle
    SYSTEM_ONLINE = "SYSTEM_ONLINE"
    SYSTEM_OFFLINE = "SYSTEM_OFFLINE"
    SESSION_START = "SESSION_START"
    SESSION_END = "SESSION_END"

    # Command Pipeline
    COMMAND_RECEIVED = "COMMAND_RECEIVED"
    INTENT_PARSED = "INTENT_PARSED"
    PLAN_CREATED = "PLAN_CREATED"
    COMMAND_CLASSIFIED = "COMMAND_CLASSIFIED"

    # Action Lifecycle
    ACTION_STARTED = "ACTION_STARTED"
    ACTION_COMPLETED = "ACTION_COMPLETED"
    ACTION_FAILED = "ACTION_FAILED"
    ACTION_RETRY = "ACTION_RETRY"

    # Guard
    GUARD_EVALUATED = "GUARD_EVALUATED"
    ACTION_BLOCKED_BY_POLICY = "ACTION_BLOCKED_BY_POLICY"

    # Command Governance
    COMMAND_STATUS_CHANGED = "COMMAND_STATUS_CHANGED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    APPROVAL_REQUESTED = "APPROVAL_REQUESTED"
    APPROVAL_RESOLVED = "APPROVAL_RESOLVED"
    APPROVAL_EXPIRED = "APPROVAL_EXPIRED"
    CLARIFICATION_REQUESTED = "CLARIFICATION_REQUESTED"
    CLARIFICATION_RESOLVED = "CLARIFICATION_RESOLVED"
    COMMAND_WAITING_FOR_APPROVAL = "COMMAND_WAITING_FOR_APPROVAL"
    COMMAND_WAITING_FOR_CLARIFICATION = "COMMAND_WAITING_FOR_CLARIFICATION"
    COMMAND_APPROVED = "COMMAND_APPROVED"
    COMMAND_REJECTED = "COMMAND_REJECTED"
    COMMAND_CANCELLED = "COMMAND_CANCELLED"
    COMMAND_BLOCKED = "COMMAND_BLOCKED"

    # Verification
    VERIFICATION_PASSED = "VERIFICATION_PASSED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"

    # Recovery
    RECOVERY_TRIGGERED = "RECOVERY_TRIGGERED"
    RECOVERY_COMPLETED = "RECOVERY_COMPLETED"
    RECOVERY_EXHAUSTED = "RECOVERY_EXHAUSTED"

    # Focus & Determinism
    FOCUS_ACQUIRED = "FOCUS_ACQUIRED"
    FOCUS_LOST = "FOCUS_LOST"
    DETERMINISM_BREACH = "DETERMINISM_BREACH"

    # Token Streaming
    TOKEN_START = "TOKEN_START"
    TOKEN_CHUNK = "TOKEN_CHUNK"
    TOKEN_END = "TOKEN_END"
    TOKEN_ABORT = "TOKEN_ABORT"
    TOKEN_ERROR = "TOKEN_ERROR"

    # Telemetry
    TELEMETRY_UPDATE = "TELEMETRY_UPDATE"
    VRAM_UPDATE = "VRAM_UPDATE"
    MODEL_SWITCH = "MODEL_SWITCH"

    # Task
    TASK_FINISHED = "TASK_FINISHED"

    # Maintenance
    MAINTENANCE_SCAN_STARTED = "MAINTENANCE_SCAN_STARTED"
    MAINTENANCE_SCAN_COMPLETED = "MAINTENANCE_SCAN_COMPLETED"

    # Vision
    VISION_ESCALATION = "VISION_ESCALATION"
    VISION_RESULT = "VISION_RESULT"

    # Internal
    STATE_CHANGE = "STATE_CHANGE"
    SNAPSHOT_CREATED = "SNAPSHOT_CREATED"


@unique
class Severity(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@unique
class Component(str, Enum):
    PLANNER = "planner"
    EXECUTOR = "executor"
    VALIDATOR = "validator"
    RECOVERY = "recovery"
    GUARD = "guard"
    INTENT_PARSER = "intent_parser"
    MODEL_ROUTER = "model_router"
    MEMORY = "memory"
    ORCHESTRATOR = "orchestrator"
    SYSTEM = "system"


@dataclass
class RuntimeEvent:
    """
    The canonical event envelope.
    Every event emitted over WebSocket MUST be serialized from this.
    """
    event_id: str = field(default_factory=lambda: str(uuid4()))
    type: str = ""
    timestamp: int = field(default_factory=lambda: int(time.time() * 1000))
    trace_id: Optional[str] = None
    causation_id: Optional[str] = None   # ID of the event that caused this one
    span_id: Optional[str] = None        # Execution span within a trace
    session_id: Optional[str] = None
    source: Optional[str] = None
    severity: str = "info"
    sequence_num: int = field(default_factory=_next_sequence)  # Monotonic ordering
    runtime_phase: Optional[str] = None
    protocol_version: str = PROTOCOL_VERSION
    schema_version: str = SCHEMA_VERSION
    deterministic_hash: Optional[str] = None
    previous_hash: Optional[str] = None
    event_hash: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialize to wire format (JSON-safe dict)."""
        d = asdict(self)
        return {k: v for k, v in d.items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RuntimeEvent":
        """Hydrate a persisted event without consuming a new sequence number."""
        return cls(
            event_id=str(data.get("event_id") or uuid4()),
            type=str(data.get("type") or ""),
            timestamp=int(data.get("timestamp") or 0),
            trace_id=data.get("trace_id"),
            causation_id=data.get("causation_id"),
            span_id=data.get("span_id"),
            session_id=data.get("session_id"),
            source=data.get("source"),
            severity=str(data.get("severity") or "info"),
            sequence_num=int(data.get("sequence_num") or 0),
            runtime_phase=data.get("runtime_phase"),
            protocol_version=str(data.get("protocol_version") or PROTOCOL_VERSION),
            schema_version=str(data.get("schema_version") or SCHEMA_VERSION),
            deterministic_hash=data.get("deterministic_hash"),
            previous_hash=data.get("previous_hash"),
            event_hash=data.get("event_hash"),
            payload=dict(data.get("payload") or {}),
        )


def _canonical_json(data: Dict[str, Any]) -> str:
    """Stable JSON encoding used for replay/hash validation."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def compute_deterministic_hash(event: RuntimeEvent) -> str:
    """
    Hash the deterministic event content.

    Excludes event_id, timestamp, sequence_num, previous_hash, and event_hash so
    replay can compare semantic event equivalence separately from wall-clock,
    emission order, and persistence chain data.
    """
    data = event.to_dict()
    for key in ("event_id", "timestamp", "sequence_num", "previous_hash", "event_hash", "deterministic_hash"):
        data.pop(key, None)
    return hashlib.sha256(_canonical_json(data).encode("utf-8")).hexdigest()


def compute_event_hash(event: RuntimeEvent, previous_hash: str) -> str:
    """Hash the persisted event plus its previous chain link.

    Unlike deterministic_hash, this intentionally includes timestamp and
    event_id. It answers "was this persisted journal event tampered with?",
    while deterministic_hash answers "is this semantically equivalent under
    replay?".
    """
    data = event.to_dict()
    data["previous_hash"] = previous_hash
    data.pop("event_hash", None)
    return hashlib.sha256(_canonical_json(data).encode("utf-8")).hexdigest()


def finalize_event(event: RuntimeEvent, previous_hash: str = GENESIS_HASH) -> RuntimeEvent:
    """Attach deterministic and hash-chain proof fields before persistence/emission."""
    event.previous_hash = previous_hash
    event.deterministic_hash = compute_deterministic_hash(event)
    event.event_hash = compute_event_hash(event, previous_hash)
    return event


def create_event(
    event_type: ProtocolEventType,
    payload: Dict[str, Any] = None,
    *,
    trace_id: Optional[str] = None,
    causation_id: Optional[str] = None,
    span_id: Optional[str] = None,
    session_id: Optional[str] = None,
    runtime_phase: Optional[RuntimeState | str] = None,
    source: Optional[Component] = None,
    severity: Severity = Severity.INFO,
) -> RuntimeEvent:
    """Factory for creating protocol-compliant events."""
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
    )
