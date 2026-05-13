from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Literal

from pydantic import BaseModel, Field

from aegis.core.constants import RiskLevel

logger = logging.getLogger(__name__)

ToolCategory = Literal["desktop", "web", "file", "shell", "git", "system"]
EvidencePolicy = Literal[
    "none",
    "read_only_hash",
    "browser_context",
    "desktop_verifier",
    "file_diff",
    "shell_result",
    "git_status",
    "blocked",
]


class ToolSpec(BaseModel):
    """Canonical tool contract advertised to guard, executor, snapshot, and UI."""

    name: str
    category: ToolCategory
    description: str
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    risk_level: RiskLevel = RiskLevel.NONE
    requires_approval: bool = False
    timeout_seconds: float = 30.0
    cancellation_supported: bool = False
    evidence_policy: EvidencePolicy = "none"
    dry_run_supported: bool = False
    side_effecting: bool = False
    enabled: bool = True

    def public_dict(self) -> dict[str, Any]:
        data = self.model_dump(mode="json")
        data["risk"] = data.pop("risk_level")
        return data


class BaseTool(ABC):
    """Abstract base class for all AEGIS tools."""

    name: str
    description: str

    @abstractmethod
    async def run(self, **kwargs) -> str:
        """Execute the tool's primary action."""
        pass

    def log_action(self, **params) -> None:
        """Standardized logging for all tool executions."""
        logger.info("[TOOL] %s -> %s", self.name, params)
