from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from aegis.core.approval_semantics import (
    ApprovalRequest,
    ApprovalScope,
    ApprovalStatus,
    BlockedAction,
    ClarificationRequest,
    ConfirmationMode,
    DecisionStatus,
    ProposedAction,
    SafeAlternative,
    SourceIntent,
)
from aegis.core.constants import RiskLevel


class GuardDecision(BaseModel):
    decision_status: DecisionStatus
    risk_level: RiskLevel
    reason: str
    policy_rule: str
    requires_approval: bool = False
    requires_clarification: bool = False
    blocked: bool = False
    evidence_required: bool = False
    rollback_required: bool = False
    safe_alternatives: list[SafeAlternative] = Field(default_factory=list)
    approval_request: ApprovalRequest | None = None
    clarification_request: ClarificationRequest | None = None
    blocked_action: BlockedAction | None = None


def classify_intent_risk(
    intent: str,
    params: dict[str, Any] | None,
    context: dict[str, Any] | None = None,
) -> GuardDecision:
    """Classify an intent without executing tools or inspecting live system state."""

    normalized_intent = _normalize_text(intent)
    normalized_params = dict(params or {})
    normalized_context = dict(context or {})

    if not normalized_intent:
        return _blocked(
            normalized_intent,
            normalized_params,
            normalized_context,
            RiskLevel.HIGH,
            "empty intent cannot be safely classified",
            "unknown_tool.blocked",
            retry_allowed=False,
        )

    if normalized_intent in {"read_file", "summarize_file"}:
        return _classify_read_file(normalized_intent, normalized_params, normalized_context)
    if normalized_intent in {"open_app", "focus_app"}:
        return _classify_app_intent(normalized_intent, normalized_params, normalized_context)
    if normalized_intent == "search_web":
        return _classify_search_web(normalized_intent, normalized_params, normalized_context)
    if normalized_intent == "open_url":
        return _classify_open_url(normalized_intent, normalized_params, normalized_context)
    if normalized_intent == "type":
        return _classify_type(normalized_intent, normalized_params, normalized_context)
    if normalized_intent == "write_file":
        return _classify_write_file(normalized_intent, normalized_params, normalized_context)
    if normalized_intent == "run_command":
        return _classify_run_command(normalized_intent, normalized_params, normalized_context)
    if normalized_intent == "close_app":
        return _classify_close_app(normalized_intent, normalized_params, normalized_context)
    if normalized_intent in {"click", "browser_click", "desktop_click"}:
        return _classify_click(normalized_intent, normalized_params, normalized_context)
    if normalized_intent in {"delete_file", "remove_directory", "kill_process", "install_package"}:
        return _approval_required(
            normalized_intent,
            normalized_params,
            normalized_context,
            RiskLevel.HIGH,
            f"{normalized_intent} is a high-risk mutation and requires explicit approval",
            f"{normalized_intent}.high_risk.approval_required",
            evidence_required=True,
            rollback_required=True,
        )

    return _blocked(
        normalized_intent,
        normalized_params,
        normalized_context,
        RiskLevel.HIGH,
        "unknown tool cannot be safely classified",
        "unknown_tool.blocked",
        retry_allowed=False,
    )


def _classify_read_file(
    intent: str,
    params: dict[str, Any],
    context: dict[str, Any],
) -> GuardDecision:
    if not _first_present(params, "path", "file_path", "source"):
        return _clarification_required(
            intent,
            params,
            context,
            RiskLevel.LOW,
            "read_file requires a path before it can be classified as ready",
            "read_file.missing_path.clarification_required",
            ambiguity_type="missing_param",
            question="Which file should Aegis read?",
        )
    return _ready(
        intent,
        params,
        context,
        RiskLevel.LOW,
        "read_file with a provided path is low risk but requires evidence",
        "read_file.path.ready",
        evidence_required=True,
    )


def _classify_app_intent(
    intent: str,
    params: dict[str, Any],
    context: dict[str, Any],
) -> GuardDecision:
    app = _first_present(params, "app", "name", "target")
    if not app or params.get("app_known") is False or params.get("_app_known") is False or params.get("unknown_app"):
        return _clarification_required(
            intent,
            params,
            context,
            RiskLevel.LOW,
            f"{intent} has an unknown app and requires a known app alias before execution",
            f"{intent}.unknown_app.clarification_required",
            ambiguity_type="unknown_app",
            question="Which installed application should Aegis use?",
        )
    if _normalize_text(str(app)) == "unknownapp":
        return _clarification_required(
            intent,
            params,
            context,
            RiskLevel.LOW,
            "unknown app must not become executable open_app",
            f"{intent}.unknown_app.clarification_required",
            ambiguity_type="unknown_app",
            question="Which installed application should Aegis use?",
        )
    return _ready(
        intent,
        params,
        context,
        RiskLevel.LOW,
        f"{intent} with a known app is low risk",
        f"{intent}.known_app.ready",
        evidence_required=True,
    )


def _classify_search_web(
    intent: str,
    params: dict[str, Any],
    context: dict[str, Any],
) -> GuardDecision:
    if not _first_present(params, "query", "q"):
        return _clarification_required(
            intent,
            params,
            context,
            RiskLevel.LOW,
            "search_web requires a non-empty query",
            "search_web.missing_query.clarification_required",
            ambiguity_type="missing_param",
            question="What should Aegis search for?",
        )
    return _ready(
        intent,
        params,
        context,
        RiskLevel.LOW,
        "search_web with a non-empty query is low risk but requires browser evidence",
        "search_web.query.ready",
        evidence_required=True,
    )


def _classify_open_url(
    intent: str,
    params: dict[str, Any],
    context: dict[str, Any],
) -> GuardDecision:
    url = _first_present(params, "url", "href")
    if not url:
        return _clarification_required(
            intent,
            params,
            context,
            RiskLevel.LOW,
            "open_url requires a URL",
            "open_url.missing_url.clarification_required",
            ambiguity_type="missing_param",
            question="Which URL should Aegis open?",
        )
    if not _is_http_url(str(url)):
        return _blocked(
            intent,
            params,
            context,
            RiskLevel.MEDIUM,
            "open_url only allows http(s) URLs at the guard-policy layer",
            "open_url.non_http.blocked",
            retry_allowed=True,
        )
    return _ready(
        intent,
        params,
        context,
        RiskLevel.LOW,
        "open_url with an http(s) URL is low risk but requires browser evidence",
        "open_url.http.ready",
        evidence_required=True,
    )


def _classify_type(
    intent: str,
    params: dict[str, Any],
    context: dict[str, Any],
) -> GuardDecision:
    if not _first_present(params, "text", "content"):
        return _clarification_required(
            intent,
            params,
            context,
            RiskLevel.MEDIUM,
            "type requires text content",
            "type.missing_text.clarification_required",
            ambiguity_type="missing_param",
            question="What text should Aegis type?",
        )
    if not _first_present(params, "_require_focus", "require_focus", "focused_app"):
        return _approval_required(
            intent,
            params,
            context,
            RiskLevel.MEDIUM,
            "type without an explicit focus requirement can mutate the wrong UI target",
            "type.missing_focus.approval_required",
            evidence_required=True,
        )
    return _ready(
        intent,
        params,
        context,
        RiskLevel.MEDIUM,
        "type with bounded focus requirement is medium risk and evidence-gated",
        "type.focus_bounded.ready",
        evidence_required=True,
    )


def _classify_write_file(
    intent: str,
    params: dict[str, Any],
    context: dict[str, Any],
) -> GuardDecision:
    path = _first_present(params, "path", "file_path", "target")
    content = _first_present(params, "content", "text", "data")
    if not path or content is None:
        return _clarification_required(
            intent,
            params,
            context,
            RiskLevel.MEDIUM,
            "write_file requires both path and content",
            "write_file.missing_param.clarification_required",
            ambiguity_type="missing_param",
            question="Which file and content should Aegis write?",
        )
    if _looks_system_sensitive_path(str(path)):
        return _blocked(
            intent,
            params,
            context,
            RiskLevel.CRITICAL,
            "write_file targets a system-sensitive path",
            "write_file.system_path.blocked",
            retry_allowed=False,
        )
    if _looks_outside_workspace(str(path)):
        return _approval_required(
            intent,
            params,
            context,
            RiskLevel.HIGH,
            "write_file outside the allowed workspace requires explicit approval",
            "write_file.outside_workspace.approval_required",
            evidence_required=True,
            rollback_required=True,
        )
    return _approval_required(
        intent,
        params,
        context,
        RiskLevel.MEDIUM,
        "write_file inside the workspace is a bounded mutation requiring approval and evidence",
        "write_file.workspace.approval_required",
        evidence_required=True,
        rollback_required=True,
    )


def _classify_run_command(
    intent: str,
    params: dict[str, Any],
    context: dict[str, Any],
) -> GuardDecision:
    command = str(_first_present(params, "command", "cmd", "args") or "").strip()
    if not command:
        return _clarification_required(
            intent,
            params,
            context,
            RiskLevel.MEDIUM,
            "run_command requires a command string",
            "run_command.missing_command.clarification_required",
            ambiguity_type="missing_param",
            question="Which command should Aegis run?",
        )
    if _looks_critical_command(command):
        return _blocked(
            intent,
            params,
            context,
            RiskLevel.CRITICAL,
            "critical destructive, registry, security, or mass deletion command is blocked",
            "run_command.critical_pattern.blocked",
            retry_allowed=False,
        )
    if _looks_install_command(command):
        return _approval_required(
            intent,
            params,
            context,
            RiskLevel.HIGH,
            "package installation command is high risk and requires approval",
            "run_command.install.approval_required",
            evidence_required=True,
        )
    if _looks_safe_test_command(command):
        return _approval_required(
            intent,
            params,
            context,
            RiskLevel.MEDIUM,
            "safe test/build command is medium risk and requires approval before execution",
            "run_command.safe_test.approval_required",
            evidence_required=True,
        )
    return _approval_required(
        intent,
        params,
        context,
        RiskLevel.HIGH,
        "unknown shell command is high risk and requires approval",
        "run_command.unknown.approval_required",
        evidence_required=True,
    )


def _classify_close_app(
    intent: str,
    params: dict[str, Any],
    context: dict[str, Any],
) -> GuardDecision:
    risk = RiskLevel.MEDIUM if params.get("own_process") or params.get("known_process") else RiskLevel.HIGH
    return _approval_required(
        intent,
        params,
        context,
        risk,
        "close_app can terminate running work and requires approval",
        "close_app.approval_required",
        evidence_required=True,
        rollback_required=False,
    )


def _classify_click(
    intent: str,
    params: dict[str, Any],
    context: dict[str, Any],
) -> GuardDecision:
    if intent == "click":
        reason = (
            "generic click quarantine: missing browser_click/desktop_click target resolution, "
            "so generic click must not be executable"
        )
        try:
            click_count = int(params.get("count", 1))
        except (TypeError, ValueError):
            click_count = 1
        if click_count > 20:
            return _blocked(
                intent,
                params,
                context,
                RiskLevel.HIGH,
                (
                    f"generic click quarantine: click count {click_count} exceeds maximum (20) "
                    "and target resolution is missing, so generic click must not be executable"
                ),
                "generic_click.quarantined.count_limit.blocked",
                retry_allowed=True,
            )
        has_low_level_target = any(key in params for key in ("selector", "x", "y", "coordinates"))
        if has_low_level_target:
            return _approval_required(
                intent,
                params,
                context,
                RiskLevel.HIGH,
                reason,
                "generic_click.quarantined.approval_required",
                evidence_required=True,
            )
        return _clarification_required(
            intent,
            params,
            context,
            RiskLevel.HIGH,
            reason,
            "generic_click.quarantined.clarification_required",
            ambiguity_type="unresolved_click_target",
            question="Should this be a browser_click or desktop_click, and what exact target should be resolved?",
        )
    if intent == "browser_click":
        return _clarification_required(
            intent,
            params,
            context,
            RiskLevel.MEDIUM,
            "browser_click target resolution is not implemented, so the action is not ready",
            "browser_click.target_resolution_missing.clarification_required",
            ambiguity_type="unresolved_browser_target",
            question="Which resolved browser target should Aegis click?",
        )
    return _approval_required(
        intent,
        params,
        context,
        RiskLevel.HIGH,
        "desktop_click target resolution is not implemented and unknown desktop UI is high risk",
        "desktop_click.target_resolution_missing.approval_required",
        evidence_required=True,
    )


def _ready(
    intent: str,
    params: dict[str, Any],
    context: dict[str, Any],
    risk_level: RiskLevel,
    reason: str,
    policy_rule: str,
    *,
    evidence_required: bool = False,
) -> GuardDecision:
    return GuardDecision(
        decision_status=DecisionStatus.READY,
        risk_level=risk_level,
        reason=reason,
        policy_rule=policy_rule,
        evidence_required=evidence_required,
    )


def _clarification_required(
    intent: str,
    params: dict[str, Any],
    context: dict[str, Any],
    risk_level: RiskLevel,
    reason: str,
    policy_rule: str,
    *,
    ambiguity_type: str,
    question: str,
) -> GuardDecision:
    request = ClarificationRequest(
        clarification_id=_context_id(context, "clarification_id", "clarification-policy"),
        command_id=_context_id(context, "command_id", "command-policy"),
        trace_id=_context_id(context, "trace_id", "trace-policy"),
        original_user_text=str(context.get("original_user_text") or context.get("raw_input") or ""),
        ambiguity_type=ambiguity_type,
        question=question,
        blocked_until_answer=True,
    )
    return GuardDecision(
        decision_status=DecisionStatus.CLARIFICATION_REQUIRED,
        risk_level=risk_level,
        reason=reason,
        policy_rule=policy_rule,
        requires_clarification=True,
        clarification_request=request,
        safe_alternatives=_default_safe_alternatives(intent),
    )


def _approval_required(
    intent: str,
    params: dict[str, Any],
    context: dict[str, Any],
    risk_level: RiskLevel,
    reason: str,
    policy_rule: str,
    *,
    evidence_required: bool = False,
    rollback_required: bool = False,
) -> GuardDecision:
    request = ApprovalRequest(
        approval_id=_context_id(context, "approval_id", "approval-policy"),
        command_id=_context_id(context, "command_id", "command-policy"),
        trace_id=_context_id(context, "trace_id", "trace-policy"),
        span_id=context.get("span_id"),
        action_id=context.get("action_id"),
        source_intent=_source_intent(intent, context),
        proposed_action=ProposedAction(
            tool=intent,
            description=reason,
            action_kind="mutation" if risk_level in {RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL} else "other",
        ),
        normalized_params=params,
        risk_level=risk_level,
        reason=reason,
        expected_effect=f"{intent} would run only after approval is resolved",
        possible_side_effects=_possible_side_effects(intent),
        rollback_note="Rollback depends on action-specific evidence captured before execution."
        if rollback_required
        else "",
        status=ApprovalStatus.PENDING,
        required_confirmation_mode=ConfirmationMode.UI,
        approval_scope=ApprovalScope.SINGLE_ACTION,
    )
    return GuardDecision(
        decision_status=DecisionStatus.APPROVAL_REQUIRED,
        risk_level=risk_level,
        reason=reason,
        policy_rule=policy_rule,
        requires_approval=True,
        evidence_required=evidence_required,
        rollback_required=rollback_required,
        approval_request=request,
        safe_alternatives=_default_safe_alternatives(intent),
    )


def _blocked(
    intent: str,
    params: dict[str, Any],
    context: dict[str, Any],
    risk_level: RiskLevel,
    reason: str,
    policy_rule: str,
    *,
    retry_allowed: bool,
) -> GuardDecision:
    action = BlockedAction(
        blocked_id=_context_id(context, "blocked_id", "blocked-policy"),
        command_id=_context_id(context, "command_id", "command-policy"),
        trace_id=_context_id(context, "trace_id", "trace-policy"),
        source_intent=_source_intent(intent, context),
        reason=reason,
        policy_rule=policy_rule,
        risk_level=risk_level,
        user_message=reason,
        retry_allowed=retry_allowed,
        safe_alternatives=_default_safe_alternatives(intent),
    )
    return GuardDecision(
        decision_status=DecisionStatus.BLOCKED,
        risk_level=risk_level,
        reason=reason,
        policy_rule=policy_rule,
        blocked=True,
        blocked_action=action,
        safe_alternatives=action.safe_alternatives,
    )


def _source_intent(intent: str, context: dict[str, Any]) -> SourceIntent:
    return SourceIntent(
        intent=intent,
        raw_input=str(context.get("original_user_text") or context.get("raw_input") or ""),
        source=str(context.get("source") or "guard_policy"),
        confidence=context.get("confidence"),
        metadata={"policy_only": True},
    )


def _default_safe_alternatives(intent: str) -> list[SafeAlternative]:
    if intent in {"click", "browser_click", "desktop_click"}:
        return [
            SafeAlternative(
                label="Resolve target first",
                reason="Click actions require browser_click or desktop_click target resolution before dispatch.",
            )
        ]
    if intent == "run_command":
        return [
            SafeAlternative(
                label="Use a known test command",
                reason="Known test/build commands are lower risk than arbitrary shell commands.",
            )
        ]
    return []


def _possible_side_effects(intent: str) -> list[str]:
    if intent in {"write_file", "delete_file", "remove_directory"}:
        return ["filesystem content changes"]
    if intent == "run_command":
        return ["process execution", "filesystem or environment changes"]
    if intent in {"click", "browser_click", "desktop_click"}:
        return ["unintended UI mutation"]
    if intent == "close_app":
        return ["process termination", "unsaved work loss"]
    return []


def _first_present(params: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = params.get(key)
        if value is not None and value != "":
            return value
    return None


def _context_id(context: dict[str, Any], key: str, default: str) -> str:
    return str(context.get(key) or default)


def _normalize_text(value: str | None) -> str:
    return (value or "").strip().lower()


def _is_http_url(value: str) -> bool:
    lowered = value.strip().lower()
    return lowered.startswith("https://") or lowered.startswith("http://")


def _looks_system_sensitive_path(path: str) -> bool:
    lowered = path.strip().lower().replace("/", "\\")
    return lowered.startswith(("c:\\windows", "c:\\program files", "c:\\programdata", "\\windows", "/etc", "/usr"))


def _looks_outside_workspace(path: str) -> bool:
    stripped = path.strip()
    lowered = stripped.lower().replace("/", "\\")
    if lowered.startswith(("..\\", "~\\", "\\\\")):
        return True
    if len(stripped) >= 3 and stripped[1:3] == ":\\":
        return not lowered.startswith("c:\\users\\nemes\\desktop\\aegis")
    return False


def _looks_safe_test_command(command: str) -> bool:
    lowered = " ".join(command.strip().lower().split())
    safe_prefixes = (
        "pytest",
        "python -m pytest",
        ".\\.venv\\scripts\\python.exe -m pytest",
        "npm test",
        "npm.cmd test",
        "npm run test",
        "npm.cmd run test",
        "npm run build",
        "npm.cmd run build",
    )
    return lowered.startswith(safe_prefixes)


def _looks_install_command(command: str) -> bool:
    lowered = " ".join(command.strip().lower().split())
    install_markers = (
        "pip install",
        "python -m pip install",
        "uv pip install",
        "npm install",
        "npm i ",
        "pnpm add",
        "yarn add",
        "winget install",
        "choco install",
    )
    return any(marker in lowered for marker in install_markers)


def _looks_critical_command(command: str) -> bool:
    lowered = " ".join(command.strip().lower().split())
    critical_markers = (
        "rm -rf",
        "format ",
        "mkfs",
        "del /s /q",
        "remove-item -recurse -force",
        "rmdir /s /q",
        "reg add",
        "reg delete",
        "set-mppreference",
        "disableantispyware",
        "disablerealtimemonitoring",
        "bcdedit",
        "cipher /w",
        "shutdown /s",
    )
    return any(marker in lowered for marker in critical_markers)
