from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum, unique
from typing import Any, Literal

from pydantic import BaseModel, Field

from aegis.core.constants import RiskLevel


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


@unique
class DecisionStatus(str, Enum):
    READY = "ready"
    CLARIFICATION_REQUIRED = "clarification_required"
    APPROVAL_REQUIRED = "approval_required"
    BLOCKED = "blocked"
    UNVERIFIED = "unverified"
    FAILED = "failed"
    CANCELLED = "cancelled"


@unique
class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


@unique
class ConfirmationMode(str, Enum):
    UI = "ui"
    VOICE = "voice"
    TYPED_PHRASE = "typed_phrase"
    BOTH = "both"


@unique
class ApprovalScope(str, Enum):
    SINGLE_ACTION = "single_action"
    COMMAND_STEP = "command_step"
    FULL_PLAN = "full_plan"


class SourceIntent(BaseModel):
    intent: str
    raw_input: str = ""
    source: str = "unknown"
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProposedAction(BaseModel):
    tool: str
    description: str = ""
    action_kind: str = "other"


class EvidenceRef(BaseModel):
    ref_id: str
    type: str
    summary: str = ""


class ExpirationPolicy(BaseModel):
    mode: Literal["never", "ttl", "command_lifetime", "session_lifetime"] = "command_lifetime"
    ttl_seconds: int | None = Field(default=None, ge=1)
    expire_on_context_change: bool = True


class ReplayPolicy(BaseModel):
    replayable_decision: bool = True
    replay_requires_same_context: bool = True
    context_fingerprint: str | None = None


class ApprovalRequest(BaseModel):
    approval_id: str
    command_id: str
    trace_id: str
    span_id: str | None = None
    action_id: str | None = None
    source_intent: SourceIntent
    proposed_action: ProposedAction
    normalized_params: dict[str, Any] = Field(default_factory=dict)
    risk_level: RiskLevel
    reason: str
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)
    expected_effect: str
    possible_side_effects: list[str] = Field(default_factory=list)
    rollback_note: str = ""
    expiration_policy: ExpirationPolicy = Field(default_factory=ExpirationPolicy)
    created_at: datetime = Field(default_factory=_now_utc)
    expires_at: datetime | None = None
    status: ApprovalStatus = ApprovalStatus.PENDING
    required_confirmation_mode: ConfirmationMode = ConfirmationMode.UI
    approval_scope: ApprovalScope = ApprovalScope.SINGLE_ACTION
    replay_policy: ReplayPolicy = Field(default_factory=ReplayPolicy)


class ClarificationOption(BaseModel):
    option_id: str
    label: str
    normalized_intent: dict[str, Any] | None = None
    risk_level: RiskLevel = RiskLevel.NONE
    safe: bool = False


class RecommendedDefault(BaseModel):
    option_id: str
    reason: str = ""


class ClarificationRequest(BaseModel):
    clarification_id: str
    command_id: str
    trace_id: str
    original_user_text: str
    ambiguity_type: str
    question: str
    options: list[ClarificationOption] = Field(default_factory=list)
    recommended_default: RecommendedDefault | None = None
    blocked_until_answer: bool = True
    created_at: datetime = Field(default_factory=_now_utc)
    expires_at: datetime | None = None


class SafeAlternative(BaseModel):
    label: str
    command_hint: str | None = None
    reason: str = ""


class BlockedAction(BaseModel):
    blocked_id: str
    command_id: str
    trace_id: str
    source_intent: SourceIntent
    reason: str
    policy_rule: str
    risk_level: RiskLevel
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)
    user_message: str
    retry_allowed: bool = False
    safe_alternatives: list[SafeAlternative] = Field(default_factory=list)


DecisionLike = DecisionStatus | ApprovalRequest | ClarificationRequest | BlockedAction | str


def _coerce_decision_status(value: DecisionLike) -> DecisionStatus | None:
    if isinstance(value, DecisionStatus):
        return value
    if isinstance(value, ApprovalRequest):
        return DecisionStatus.APPROVAL_REQUIRED
    if isinstance(value, ClarificationRequest):
        return DecisionStatus.CLARIFICATION_REQUIRED
    if isinstance(value, BlockedAction):
        return DecisionStatus.BLOCKED
    try:
        return DecisionStatus(str(value))
    except ValueError:
        return None


def is_executable_decision(value: DecisionLike) -> bool:
    """Return whether a decision is dispatchable by contract.

    This predicate is pure and intentionally does not inspect executor,
    orchestrator, parser, or runtime state.
    """

    return _coerce_decision_status(value) == DecisionStatus.READY


def is_terminal_non_executed(value: DecisionLike) -> bool:
    if isinstance(value, ApprovalRequest):
        return value.status in {
            ApprovalStatus.DENIED,
            ApprovalStatus.EXPIRED,
            ApprovalStatus.CANCELLED,
        }
    return _coerce_decision_status(value) in {
        DecisionStatus.BLOCKED,
        DecisionStatus.CANCELLED,
    }


def requires_user_input(value: DecisionLike) -> bool:
    if isinstance(value, ApprovalRequest):
        return value.status == ApprovalStatus.PENDING
    return _coerce_decision_status(value) in {
        DecisionStatus.APPROVAL_REQUIRED,
        DecisionStatus.CLARIFICATION_REQUIRED,
    }


def is_approval_pending(value: DecisionLike) -> bool:
    return isinstance(value, ApprovalRequest) and value.status == ApprovalStatus.PENDING


def is_blocked(value: DecisionLike) -> bool:
    return _coerce_decision_status(value) == DecisionStatus.BLOCKED


def approval_implies_verified(value: ApprovalRequest) -> bool:
    return False


def can_transition_decision(from_status: DecisionStatus | str, to_status: DecisionStatus | str) -> bool:
    try:
        source = from_status if isinstance(from_status, DecisionStatus) else DecisionStatus(str(from_status))
        target = to_status if isinstance(to_status, DecisionStatus) else DecisionStatus(str(to_status))
    except ValueError:
        return False
    if source == DecisionStatus.BLOCKED and target == DecisionStatus.APPROVAL_REQUIRED:
        return False
    return True
