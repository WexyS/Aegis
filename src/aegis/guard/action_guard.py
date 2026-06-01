"""
AEGIS Action Guard — Security gate for the pipeline.

Simple but real. Every action passes through here.
Rules:
  - NONE/LOW risk → allow
  - MEDIUM/HIGH risk → require explicit approval
  - CRITICAL → block
  - Unknown intent → block
  - Loop protection: max 20 clicks per command
"""

from __future__ import annotations

import logging

from aegis.core.constants import RiskLevel
from aegis.core.schemas import GuardResult, IntentResult
from aegis.tools.file_tools import _is_allowed_write_path, _is_forbidden_write_path, _resolve_write_path
from aegis.tools.registry import get_tool_spec
from aegis.tools.shell_tools import is_allowlisted_shell_command, is_destructive_shell_command


logger = logging.getLogger(__name__)

# Hard limits
MAX_CLICK_COUNT = 20
MAX_PARAM_LENGTH = 5000


class ActionGuard:
    """Evaluates intent safety and decides allow/block."""

    def evaluate(self, intent: IntentResult) -> GuardResult:
        """Check if an intent is safe to execute.

        Args:
            intent: Parsed intent from the parser.

        Returns:
            GuardResult with allow/block decision.
        """
        warnings: list[str] = []

        # --- Rule 1: Unknown intent → block ---
        if intent.intent == "unknown":
            logger.info("Guard: blocking unknown intent")
            return GuardResult(
                allowed=False,
                reason="Unknown intent — cannot execute unrecognized commands",
                risk=RiskLevel.NONE,
                warnings=[],
            )

        spec = get_tool_spec(intent.intent)
        if spec is None:
            logger.info("Guard: blocking unregistered tool %s", intent.intent)
            return GuardResult(
                allowed=False,
                reason=f"Tool '{intent.intent}' is not registered in the canonical tool registry",
                risk=RiskLevel.CRITICAL,
                warnings=[],
            )

        # --- Rule 2: Click count limit ---
        if intent.intent == "click":
            count = intent.params.get("count", 1)
            if count > MAX_CLICK_COUNT:
                logger.warning("Guard: blocking excessive click count: %d", count)
                return GuardResult(
                    allowed=False,
                    reason=f"Click count {count} exceeds maximum ({MAX_CLICK_COUNT})",
                    risk=RiskLevel.HIGH,
                    warnings=[],
                )
            if count > 5:
                warnings.append(f"High click count: {count} clicks requested")

        # --- Rule 3: URL validation ---
        if intent.intent in {"open_app", "focus_app"}:
            app = str(intent.params.get("app") or "")
            if (
                intent.params.get("_app_known") is False
                or intent.params.get("app_known") is False
                or intent.params.get("unknown_app")
                or _looks_like_search_phrase(app)
            ):
                return GuardResult(
                    allowed=False,
                    reason="Unknown or query-like app target cannot be executed as a local application",
                    risk=RiskLevel.MEDIUM,
                    warnings=[],
                )

        # --- Rule 3: URL validation ---
        if intent.intent == "open_url":
            url = intent.params.get("url", "")
            if not url:
                return GuardResult(
                    allowed=False,
                    reason="open_url intent has no URL parameter",
                    risk=RiskLevel.MEDIUM,
                    warnings=[],
                )
            if not url.startswith(("http://", "https://")):
                return GuardResult(
                    allowed=False,
                    reason=f"URL scheme not allowed: {url}",
                    risk=RiskLevel.HIGH,
                    warnings=[],
                )

        # --- Rule 4: Type/Keyboard check ---
        if intent.intent == "type":
            text = intent.params.get("text", "")
            if not text:
                return GuardResult(
                    allowed=False,
                    reason="type intent has no text parameter",
                    risk=RiskLevel.MEDIUM,
                    warnings=[],
                )
            # Add a warning for typing (it's active interaction)
            warnings.append("Active keyboard interaction requested")

        # --- Rule 5: File write safety ---
        if intent.intent in {"write_file", "create_file", "edit_file"}:
            path = str(intent.params.get("path", ""))
            resolved_path = _resolve_write_path(path)
            forbidden = _is_forbidden_write_path(resolved_path)
            if forbidden:
                return GuardResult(
                    allowed=False,
                    reason=f"Writing to {forbidden} is forbidden for security reasons",
                    risk=RiskLevel.CRITICAL,
                    warnings=[],
                )
            if not _is_allowed_write_path(resolved_path):
                return GuardResult(
                    allowed=False,
                    reason="Writing outside allowed roots is forbidden for security reasons",
                    risk=RiskLevel.CRITICAL,
                    warnings=[],
                )

        # --- Rule 6: Critical file mutations stay blocked in v1 ---
        if intent.intent in {"delete_file", "move_file"}:
            return GuardResult(
                allowed=False,
                reason=f"{intent.intent} is critical-risk and blocked in Tool Contract & Sandbox v1",
                risk=RiskLevel.CRITICAL,
                warnings=[],
            )

        # --- Rule 7: Shell safety ---
        if intent.intent == "run_command":
            command = str(intent.params.get("command", "")).strip()
            if not command:
                return GuardResult(
                    allowed=False,
                    reason="run_command intent has no command parameter",
                    risk=RiskLevel.CRITICAL,
                    warnings=[],
                )
            if is_destructive_shell_command(command):
                return GuardResult(
                    allowed=False,
                    reason="Destructive shell command blocked by policy",
                    risk=RiskLevel.CRITICAL,
                    warnings=[],
                )
            if not is_allowlisted_shell_command(command):
                return GuardResult(
                    allowed=False,
                    reason="Shell command is not in the read-only allowlist",
                    risk=RiskLevel.CRITICAL,
                    warnings=[],
                )

        # --- Rule 8: Git safety ---
        if intent.intent == "git_action":
            git_cmd = str(intent.params.get("git_cmd", "")).lower().strip()
            if git_cmd != "status":
                return GuardResult(
                    allowed=False,
                    reason=f"Git action '{git_cmd or 'unknown'}' is blocked until verified git mutations are implemented",
                    risk=RiskLevel.CRITICAL,
                    warnings=[],
                )

        # --- Rule 9: Risk-based decision ---
        risk = spec.risk_level if spec.risk_level.numeric > intent.risk.numeric else intent.risk

        if risk.is_critical:
            logger.info("Guard: blocking critical intent %s", intent.intent)
            return GuardResult(
                allowed=False,
                reason=f"Critical-risk action '{intent.intent}' is blocked by policy",
                risk=risk,
                warnings=[],
            )

        if risk == RiskLevel.MEDIUM:
            warnings.append(f"Medium risk action: {intent.intent}")

        if risk.requires_approval:
            logger.info("Guard: requiring approval for %s (risk=%s)", intent.intent, risk.value)
            return GuardResult(
                allowed=True,
                reason=f"Action '{intent.intent}' requires approval (risk: {risk.value})",
                risk=risk,
                requires_approval=True,
                warnings=warnings,
            )

        # --- Allow ---
        logger.info("Guard: allowing %s (risk=%s)", intent.intent, risk.value)
        return GuardResult(
            allowed=True,
            reason=f"Action '{intent.intent}' approved (risk: {risk.value})",
            risk=risk,
            requires_approval=False,
            warnings=warnings,
        )


def _looks_like_search_phrase(value: str) -> bool:
    lowered = value.lower()
    markers = (
        " ara",
        " arat",
        " search",
        " find",
        " googlela",
        " diye",
    )
    return any(marker in lowered for marker in markers)


# Singleton
_guard: ActionGuard | None = None


def get_guard() -> ActionGuard:
    global _guard
    if _guard is None:
        _guard = ActionGuard()
    return _guard
