from __future__ import annotations

import pytest

from aegis.core.approval_semantics import (
    DecisionStatus,
    is_executable_decision,
    is_terminal_non_executed,
    requires_user_input,
)
from aegis.core.constants import RiskLevel
from aegis.core.guard_policy import classify_intent_risk


def test_read_file_with_path_is_low_ready_and_evidence_required() -> None:
    decision = classify_intent_risk("read_file", {"path": "README.md"})

    assert decision.decision_status == DecisionStatus.READY
    assert decision.risk_level == RiskLevel.LOW
    assert decision.evidence_required is True
    assert is_executable_decision(decision.decision_status) is True


@pytest.mark.parametrize(
    ("intent", "params"),
    [
        ("open_app", {"app": "notepad"}),
        ("focus_app", {"app": "notepad"}),
    ],
)
def test_known_app_intents_are_low_ready(intent: str, params: dict[str, str]) -> None:
    decision = classify_intent_risk(intent, params)

    assert decision.decision_status == DecisionStatus.READY
    assert decision.risk_level == RiskLevel.LOW
    assert decision.evidence_required is True


def test_search_web_with_query_is_low_ready() -> None:
    decision = classify_intent_risk("search_web", {"query": "python nedir"})

    assert decision.decision_status == DecisionStatus.READY
    assert decision.risk_level == RiskLevel.LOW
    assert decision.evidence_required is True


def test_open_url_valid_https_is_low_ready() -> None:
    decision = classify_intent_risk("open_url", {"url": "https://example.com"})

    assert decision.decision_status == DecisionStatus.READY
    assert decision.risk_level == RiskLevel.LOW
    assert decision.evidence_required is True


@pytest.mark.parametrize(
    ("intent", "params"),
    [
        ("read_file", {}),
        ("write_file", {"path": "notes.txt"}),
        ("write_file", {"content": "hello"}),
    ],
)
def test_missing_required_params_require_clarification(intent: str, params: dict[str, str]) -> None:
    decision = classify_intent_risk(intent, params)

    assert decision.decision_status == DecisionStatus.CLARIFICATION_REQUIRED
    assert decision.requires_clarification is True
    assert decision.clarification_request is not None
    assert is_executable_decision(decision.decision_status) is False
    assert requires_user_input(decision.decision_status) is True


def test_unknown_app_requires_clarification_not_open_app_ready() -> None:
    decision = classify_intent_risk("open_app", {"app": "unknownapp", "app_known": False})

    assert decision.decision_status == DecisionStatus.CLARIFICATION_REQUIRED
    assert decision.requires_clarification is True
    assert decision.risk_level == RiskLevel.LOW
    assert "unknown app" in decision.reason


@pytest.mark.parametrize(
    "params",
    [
        {},
        {"raw_target": "click that button"},
        {"raw_target": "suna tikla"},
    ],
)
def test_generic_click_without_resolved_target_requires_clarification(params: dict[str, str]) -> None:
    decision = classify_intent_risk("click", params)

    assert decision.decision_status == DecisionStatus.CLARIFICATION_REQUIRED
    assert decision.requires_clarification is True
    assert decision.clarification_request is not None
    assert "generic click quarantine" in decision.reason
    assert "browser_click/desktop_click target resolution" in decision.reason
    assert is_executable_decision(decision.decision_status) is False


def test_write_file_inside_workspace_requires_medium_approval_evidence_and_rollback() -> None:
    decision = classify_intent_risk("write_file", {"path": "scratch/a.txt", "content": "hello"})

    assert decision.decision_status == DecisionStatus.APPROVAL_REQUIRED
    assert decision.risk_level == RiskLevel.MEDIUM
    assert decision.requires_approval is True
    assert decision.evidence_required is True
    assert decision.rollback_required is True
    assert decision.approval_request is not None


def test_run_unknown_command_requires_high_approval() -> None:
    decision = classify_intent_risk("run_command", {"command": "custom-tool --mutate"})

    assert decision.decision_status == DecisionStatus.APPROVAL_REQUIRED
    assert decision.risk_level == RiskLevel.HIGH
    assert decision.requires_approval is True
    assert decision.evidence_required is True
    assert "unknown shell command" in decision.reason


def test_close_app_arbitrary_process_requires_high_approval() -> None:
    decision = classify_intent_risk("close_app", {"app": "some-process"})

    assert decision.decision_status == DecisionStatus.APPROVAL_REQUIRED
    assert decision.risk_level == RiskLevel.HIGH
    assert decision.requires_approval is True


def test_install_package_command_requires_high_approval() -> None:
    decision = classify_intent_risk("run_command", {"command": "pip install package-name"})

    assert decision.decision_status == DecisionStatus.APPROVAL_REQUIRED
    assert decision.risk_level == RiskLevel.HIGH
    assert decision.requires_approval is True
    assert "package installation" in decision.reason


@pytest.mark.parametrize(
    "command",
    [
        "rm -rf /",
        "reg add HKCU\\Software\\Aegis /v unsafe /d 1",
        "Set-MpPreference -DisableRealtimeMonitoring $true",
        "del /s /q C:\\*",
    ],
)
def test_critical_run_command_patterns_are_blocked(command: str) -> None:
    decision = classify_intent_risk("run_command", {"command": command})

    assert decision.decision_status == DecisionStatus.BLOCKED
    assert decision.risk_level == RiskLevel.CRITICAL
    assert decision.blocked is True
    assert decision.blocked_action is not None
    assert is_terminal_non_executed(decision.decision_status) is True


def test_unknown_tool_is_blocked() -> None:
    decision = classify_intent_risk("mystery_tool", {"value": "x"})

    assert decision.decision_status == DecisionStatus.BLOCKED
    assert decision.blocked is True
    assert decision.risk_level == RiskLevel.HIGH


@pytest.mark.parametrize(
    "params",
    [
        {"selector": "#submit"},
        {"x": 100, "y": 200},
    ],
)
def test_generic_click_with_selector_or_coordinates_is_not_ready(params: dict[str, int | str]) -> None:
    decision = classify_intent_risk("click", params)

    assert decision.decision_status == DecisionStatus.APPROVAL_REQUIRED
    assert decision.risk_level == RiskLevel.HIGH
    assert decision.requires_approval is True
    assert "generic click quarantine" in decision.reason
    assert is_executable_decision(decision.decision_status) is False


@pytest.mark.parametrize("intent", ["browser_click", "desktop_click"])
def test_split_click_intents_before_target_resolution_are_not_ready(intent: str) -> None:
    decision = classify_intent_risk(intent, {"target": "first result"})

    assert decision.decision_status in {
        DecisionStatus.CLARIFICATION_REQUIRED,
        DecisionStatus.APPROVAL_REQUIRED,
        DecisionStatus.BLOCKED,
    }
    assert decision.decision_status != DecisionStatus.READY
    assert is_executable_decision(decision.decision_status) is False


def test_safe_test_command_policy_is_medium_approval_not_ready() -> None:
    decision = classify_intent_risk("run_command", {"command": "pytest tests/test_core -q"})

    assert decision.decision_status == DecisionStatus.APPROVAL_REQUIRED
    assert decision.risk_level == RiskLevel.MEDIUM
    assert decision.requires_approval is True
    assert "safe test/build command" in decision.reason


def test_helper_semantics_for_guard_decisions() -> None:
    ready = classify_intent_risk("open_app", {"app": "notepad"})
    approval = classify_intent_risk("run_command", {"command": "custom-tool --mutate"})
    clarification = classify_intent_risk("click", {})
    blocked = classify_intent_risk("run_command", {"command": "rm -rf /"})

    assert is_executable_decision(ready.decision_status) is True
    assert is_executable_decision(approval.decision_status) is False
    assert is_executable_decision(clarification.decision_status) is False
    assert is_executable_decision(blocked.decision_status) is False
    assert requires_user_input(approval.decision_status) is True
    assert requires_user_input(clarification.decision_status) is True
    assert is_terminal_non_executed(blocked.decision_status) is True
