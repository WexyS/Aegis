"""
AEGIS Core Schemas — Pydantic models for the working pipeline.

All models needed for: intent → guard → executor → logger → response.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator

from aegis.core.constants import (
    ActionStatus,
    CommandStatus,
    EventType,
    ExecutionMode,
    IntentSource,
    RiskLevel,
    Severity,
)


# ---------------------------------------------------------------------------
# Intent
# ---------------------------------------------------------------------------

class IntentResult(BaseModel):
    """Output of the intent parser."""

    intent: str = Field(..., pattern=r"^[a-z][a-z0-9_]{1,63}$")
    confidence: float = Field(..., ge=0.0, le=1.0)
    params: dict[str, Any] = Field(default_factory=dict)
    risk: RiskLevel = RiskLevel.NONE
    source: IntentSource = IntentSource.RULE
    raw_input: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Guard
# ---------------------------------------------------------------------------

class GuardResult(BaseModel):
    """Verdict from the action guard."""

    allowed: bool
    reason: str
    risk: RiskLevel
    requires_approval: bool = False
    warnings: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Executor
# ---------------------------------------------------------------------------

class ReliabilityMetrics(BaseModel):
    """Execution performance and reliability telemetry."""
    execution_time_ms: float = 0.0
    focus_acquire_ms: float = 0.0
    retries: int = 0
    recovery_triggered: bool = False
    vision_used: bool = False
    determinism_score: float = 0.0 # 0.0 to 1.0


class ExecutionEvidence(BaseModel):
    """Observed proof for a side-effecting action."""

    action: str
    target: str | None = None
    target_type: str = "unknown"
    method: str = "unknown"
    verifier: str | None = None
    verification_state: str = "unverified"
    verification_reason: str | None = None
    started_at_ms: int = 0
    completed_at_ms: int = 0
    launch_target: str | None = None
    resolved_path: str | None = None
    process_name: str | None = None
    pids: list[int] = Field(default_factory=list)
    process_alive: bool | None = None
    window: dict[str, Any] | None = None
    expected: dict[str, Any] = Field(default_factory=dict)
    observed: dict[str, Any] = Field(default_factory=dict)
    verification_checks: list[dict[str, Any]] = Field(default_factory=list)
    matching_windows: list[dict[str, Any]] = Field(default_factory=list)
    retry_count: int = 0
    recovery_triggered: bool = False
    attempts: list[dict[str, Any]] = Field(default_factory=list)
    fallback_chain: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ActionResult(BaseModel):
    """Result of a single executed action (Formal Production-Grade Contract)."""

    action: str
    params: dict[str, Any] = Field(default_factory=dict)
    status: ActionStatus
    
    # Formal Action Contract
    success: bool
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    output: str = ""
    recovery_hint: str | None = None
    state_changed: bool = False
    focus_verified: bool = False
    
    proof: dict[str, Any] = Field(default_factory=dict) # Tier 4 Determinism Proof
    execution_evidence: ExecutionEvidence | None = None
    metrics: ReliabilityMetrics = Field(default_factory=ReliabilityMetrics)
    semantic_score: float = 1.0 # 0.0 to 1.0 (Enterprise Verification)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

class LogEvent(BaseModel):
    """Structured log event for audit trail."""

    event_id: UUID = Field(default_factory=uuid4)
    event_type: EventType
    trace_id: UUID
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: dict[str, Any] = Field(default_factory=dict)
    source_component: str = ""
    severity: Severity = Severity.INFO
    duration_ms: float | None = None


# ---------------------------------------------------------------------------
# API Request / Response
# ---------------------------------------------------------------------------

class CommandRequest(BaseModel):
    """Incoming user command via POST /command."""

    text: str = Field(..., min_length=1, max_length=10000)
    mode: ExecutionMode = ExecutionMode.AUTO
    context: dict[str, Any] = Field(default_factory=dict)
    session_id: UUID | None = None
    language: str = "auto"


class CommandResponse(BaseModel):
    """Full pipeline response — includes guard + execution results."""

    trace_id: Union[UUID, str]
    status: CommandStatus
    intent: str
    message: str = ""
    actions: list[ActionResult] = Field(default_factory=list)
    guard: Union[GuardResult, dict[str, Any], None] = None
    warnings: list[str] = Field(default_factory=list)
    timestamp: Union[datetime, str] = Field(default_factory=datetime.utcnow)
    duration_ms: float = Field(0.0, ge=0.0)

    @model_validator(mode="after")
    def coerce_guard(self) -> "CommandResponse":
        """Coerce dict guard result to GuardResult model."""
        if isinstance(self.guard, dict):
            try:
                self.guard = GuardResult(**self.guard)
            except Exception:
                pass
        return self
