"""
AEGIS Core Constants — Enums and canonical vocabulary.

Working Phase 1: all enums needed for the full pipeline
(intent → guard → executor → logger → response).
"""

from enum import Enum, unique


@unique
class RiskLevel(str, Enum):
    """Risk classification for intents and actions."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def requires_approval(self) -> bool:
        return self in (RiskLevel.MEDIUM, RiskLevel.HIGH)

    @property
    def is_critical(self) -> bool:
        return self == RiskLevel.CRITICAL

    @property
    def numeric(self) -> float:
        return {
            RiskLevel.NONE: 0.0,
            RiskLevel.LOW: 0.2,
            RiskLevel.MEDIUM: 0.5,
            RiskLevel.HIGH: 0.8,
            RiskLevel.CRITICAL: 1.0,
        }[self]


@unique
class IntentType(str, Enum):
    """Supported intent types."""
    OPEN_URL = "open_url"
    OPEN_APP = "open_app"
    CLOSE_APP = "close_app"
    FOCUS_APP = "focus_app"
    CLICK = "click"
    TYPE = "type"
    SEARCH_WEB = "search_web"
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    SUMMARIZE_FILE = "summarize_file"
    GENERAL_CHAT = "general_chat"
    UNKNOWN = "unknown"


@unique
class IntentSource(str, Enum):
    RULE = "rule"
    MODEL = "model"
    AI = "ai"
    HYBRID = "hybrid"


@unique
class ExecutionMode(str, Enum):
    AUTO = "auto"
    DRY_RUN = "dry_run"
    LIVE = "live"


@unique
class CommandStatus(str, Enum):
    RECEIVED = "received"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    RUNNING = "running"
    DRY_RUN = "dry_run"
    EXECUTED = "executed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"
    FAILED = "failed"
    ERROR = "error"
    REPLAY = "replay"
    UNKNOWN = "unknown"


@unique
class ActionStatus(str, Enum):
    """Outcome of a single action in the executor."""
    SIMULATED = "simulated"
    EXECUTED = "executed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"
    FAILED = "failed"


@unique
class EventType(str, Enum):
    COMMAND_RECEIVED = "COMMAND_RECEIVED"
    INTENT_PARSED = "INTENT_PARSED"
    PLAN_CREATED = "PLAN_CREATED"
    ACTION_START = "ACTION_START"
    ACTION_RETRY = "ACTION_RETRY"
    ACTION_SUCCESS = "ACTION_SUCCESS"
    ACTION_FAILED = "ACTION_FAILED"
    VERIFICATION_PASSED = "VERIFICATION_PASSED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    STATE_SNAPSHOT = "STATE_SNAPSHOT"
    RECOVERY_TRIGGERED = "RECOVERY_TRIGGERED"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    GUARD_EVALUATED = "GUARD_EVALUATED"


@unique
class Severity(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
