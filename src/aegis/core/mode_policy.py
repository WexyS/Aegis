from __future__ import annotations

from dataclasses import dataclass
from typing import Any


MODE_POLICY_CONTRACT = "aegis-mode-policy"
MODE_POLICY_EXECUTION_PERMISSION = "not_granted_by_mode_policy"

VALID_MODES = frozenset({"safe", "balanced", "power", "yolo_lab"})


@dataclass(frozen=True)
class ModePolicy:
    mode: str
    display_name: str
    memory_silent_write: bool
    memory_ledger_required: bool
    external_api_allowed: bool
    external_api_preview_required: bool
    model_gateway_allowed: bool
    tool_execution_allowed: bool
    agent_execution_allowed: bool
    workflow_execution_allowed: bool
    computer_control_allowed: bool
    filesystem_write_allowed: bool
    approval_required_for_medium_risk: bool
    approval_required_for_high_risk: bool
    kill_switch_required: bool
    session_timebox_required: bool
    activity_ledger_required: bool
    post_run_report_required: bool
    current_execution_grant: bool
    notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "display_name": self.display_name,
            "memory_silent_write": self.memory_silent_write,
            "memory_ledger_required": self.memory_ledger_required,
            "external_api_allowed": self.external_api_allowed,
            "external_api_preview_required": self.external_api_preview_required,
            "model_gateway_allowed": self.model_gateway_allowed,
            "tool_execution_allowed": self.tool_execution_allowed,
            "agent_execution_allowed": self.agent_execution_allowed,
            "workflow_execution_allowed": self.workflow_execution_allowed,
            "computer_control_allowed": self.computer_control_allowed,
            "filesystem_write_allowed": self.filesystem_write_allowed,
            "approval_required_for_medium_risk": self.approval_required_for_medium_risk,
            "approval_required_for_high_risk": self.approval_required_for_high_risk,
            "kill_switch_required": self.kill_switch_required,
            "session_timebox_required": self.session_timebox_required,
            "activity_ledger_required": self.activity_ledger_required,
            "post_run_report_required": self.post_run_report_required,
            "current_execution_grant": self.current_execution_grant,
            "notes": list(self.notes),
            "authority": False,
            "runtime_dispatch_allowed": False,
            "execution_permission": MODE_POLICY_EXECUTION_PERMISSION,
            "mode_allows_execution_now": False,
            "evidence_created": False,
            "verifier_success": False,
            "approval_granted": False,
            "approval_grant": False,
            "capability_lease_granted": False,
            "capability_grant": False,
            "lease_grant": False,
            "frontend_authority": False,
        }


def list_mode_policies() -> list[dict[str, Any]]:
    return [policy.to_dict() for policy in MODE_POLICIES]


def get_mode_policy(mode: str) -> dict[str, Any] | None:
    requested = _normalize_mode(mode)
    for policy in MODE_POLICIES:
        if policy.mode == requested:
            return policy.to_dict()
    return None


def mode_allows_execution_now(mode: str) -> bool:
    policy = get_mode_policy(mode)
    if policy is None:
        return False
    return False


def _normalize_mode(mode: str) -> str:
    return str(mode or "").strip().lower().replace(" ", "_").replace("-", "_")


MODE_POLICIES: tuple[ModePolicy, ...] = (
    ModePolicy(
        mode="safe",
        display_name="Safe",
        memory_silent_write=False,
        memory_ledger_required=True,
        external_api_allowed=False,
        external_api_preview_required=True,
        model_gateway_allowed=True,
        tool_execution_allowed=False,
        agent_execution_allowed=False,
        workflow_execution_allowed=False,
        computer_control_allowed=False,
        filesystem_write_allowed=False,
        approval_required_for_medium_risk=True,
        approval_required_for_high_risk=True,
        kill_switch_required=False,
        session_timebox_required=False,
        activity_ledger_required=True,
        post_run_report_required=False,
        current_execution_grant=False,
        notes=(
            "default_local_first_mode",
            "model_gateway_status_or_proposal_readiness_only",
            "no_tool_agent_workflow_computer_or_filesystem_write_execution",
        ),
    ),
    ModePolicy(
        mode="balanced",
        display_name="Balanced",
        memory_silent_write=False,
        memory_ledger_required=True,
        external_api_allowed=False,
        external_api_preview_required=True,
        model_gateway_allowed=True,
        tool_execution_allowed=False,
        agent_execution_allowed=False,
        workflow_execution_allowed=False,
        computer_control_allowed=False,
        filesystem_write_allowed=False,
        approval_required_for_medium_risk=True,
        approval_required_for_high_risk=True,
        kill_switch_required=True,
        session_timebox_required=True,
        activity_ledger_required=True,
        post_run_report_required=True,
        current_execution_grant=False,
        notes=(
            "future_low_risk_memory_candidates_may_be_planned_not_implemented_here",
            "external_api_requires_preview_and_approval_before_any_future_use",
            "no_current_execution_grant",
        ),
    ),
    ModePolicy(
        mode="power",
        display_name="Power",
        memory_silent_write=False,
        memory_ledger_required=True,
        external_api_allowed=False,
        external_api_preview_required=True,
        model_gateway_allowed=True,
        tool_execution_allowed=False,
        agent_execution_allowed=False,
        workflow_execution_allowed=False,
        computer_control_allowed=False,
        filesystem_write_allowed=False,
        approval_required_for_medium_risk=True,
        approval_required_for_high_risk=True,
        kill_switch_required=True,
        session_timebox_required=True,
        activity_ledger_required=True,
        post_run_report_required=True,
        current_execution_grant=False,
        notes=(
            "future_broader_execution_posture_requires_ledger_and_approval_strategy",
            "no_current_execution_grant",
        ),
    ),
    ModePolicy(
        mode="yolo_lab",
        display_name="YOLO Lab",
        memory_silent_write=False,
        memory_ledger_required=True,
        external_api_allowed=False,
        external_api_preview_required=True,
        model_gateway_allowed=True,
        tool_execution_allowed=False,
        agent_execution_allowed=False,
        workflow_execution_allowed=False,
        computer_control_allowed=False,
        filesystem_write_allowed=False,
        approval_required_for_medium_risk=True,
        approval_required_for_high_risk=True,
        kill_switch_required=True,
        session_timebox_required=True,
        activity_ledger_required=True,
        post_run_report_required=True,
        current_execution_grant=False,
        notes=(
            "future_high_autonomy_lab_mode_only",
            "requires_kill_switch_timebox_activity_ledger_memory_ledger_and_post_run_report",
            "no_current_execution_grant",
        ),
    ),
)
