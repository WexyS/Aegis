from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Mapping
from uuid import uuid4


SOCIETY_RC1_VERSION = "deterministic-society-session-rc1/1"
SOCIETY_EXECUTION_PERMISSION = "not_granted_by_society_session_rc1"
DEFAULT_SOCIETY_NAME = "hackathon_rc_review_society"

ROLE_CONTEXT_PLANNER = "Context Planner"
ROLE_POLICY_REVIEWER = "Policy Reviewer"
ROLE_MEMORY_CURATOR = "Memory Curator"
ROLE_AUTOPILOT_PLANNER = "AutoPilot Planner"
ROLE_VERIFIER_REVIEWER = "Verifier Reviewer"
ROLE_REPORT_WRITER = "Report Writer"

ROLE_ORDER = (
    ROLE_CONTEXT_PLANNER,
    ROLE_POLICY_REVIEWER,
    ROLE_MEMORY_CURATOR,
    ROLE_AUTOPILOT_PLANNER,
    ROLE_VERIFIER_REVIEWER,
    ROLE_REPORT_WRITER,
)


@dataclass(frozen=True)
class SocietySessionStore:
    """Process-local store for deterministic Society Session RC1 output."""

    _sessions: dict[str, dict[str, Any]]

    def __init__(self) -> None:
        object.__setattr__(self, "_sessions", {})

    def save(self, session: Mapping[str, Any]) -> None:
        self._sessions[str(session["session_id"])] = dict(session)

    def get(self, session_id: str) -> dict[str, Any] | None:
        session = self._sessions.get(session_id)
        return dict(session) if session is not None else None

    def list(self) -> list[dict[str, Any]]:
        return sorted(
            (dict(session) for session in self._sessions.values()),
            key=lambda item: str(item.get("created_at") or ""),
            reverse=True,
        )


def run_deterministic_society_session(
    *,
    autopilot_report: Mapping[str, Any] | None,
    autopilot_report_id: str | None = None,
    memory_ids: tuple[str, ...] | list[str] | None = None,
    society_name: str = DEFAULT_SOCIETY_NAME,
) -> dict[str, Any]:
    created_at = _now()
    session_id = f"society_{uuid4().hex}"
    normalized_memory_ids = tuple(str(item).strip() for item in (memory_ids or ()) if str(item).strip())

    if not autopilot_report:
        completed_at = _now()
        return _base_session(
            session_id=session_id,
            status="input_missing",
            society_name=society_name,
            input_report_id=autopilot_report_id,
            input_report_summary={},
            memory_refs=_memory_refs(normalized_memory_ids),
            created_at=created_at,
            completed_at=completed_at,
            warnings=("autopilot_report_missing",),
            degraded_state=True,
        )

    report = dict(autopilot_report)
    input_summary = _input_report_summary(report)
    session = _base_session(
        session_id=session_id,
        status="completed",
        society_name=society_name,
        input_report_id=autopilot_report_id or _text(report.get("report_id")),
        input_report_summary=input_summary,
        memory_refs=_memory_refs(normalized_memory_ids),
        created_at=created_at,
        completed_at=created_at,
        warnings=(),
        degraded_state=bool(report.get("degraded_state") or report.get("status") != "completed"),
    )

    timeline: list[dict[str, Any]] = []
    proposals: list[dict[str, Any]] = []
    _add_event(timeline, "society_session_started", "session", "Society session started.")

    role_builders = (
        _context_planner,
        _policy_reviewer,
        _memory_curator,
        _autopilot_planner,
        _verifier_reviewer,
    )
    for builder in role_builders:
        proposal = builder(report, normalized_memory_ids)
        proposals.append(proposal)
        _add_event(
            timeline,
            _event_name_for_role(proposal["role"]),
            proposal["role"],
            f"{proposal['role']} completed.",
        )

    report_writer = _report_writer(report, proposals)
    proposals.append(report_writer)
    _add_event(timeline, _event_name_for_role(report_writer["role"]), report_writer["role"], "Report Writer completed.")
    _add_event(timeline, "society_session_completed", "session", "Society session completed.")

    completed_at = _now()
    final_summary = report_writer["claims"]["final_summary"]
    session.update(
        {
            "roles": tuple({"name": role, "status": "completed", "mode": "deterministic"} for role in ROLE_ORDER),
            "proposals": tuple(proposals),
            "timeline": tuple(timeline),
            "final_summary": final_summary,
            "completed_at": completed_at,
            "duration_ms": max(0, int((completed_at - created_at) * 1000)),
            "warnings": tuple(_session_warnings(report, normalized_memory_ids)),
            "degraded_state": bool(
                report.get("degraded_state")
                or report.get("status") not in {"completed", "completed_with_verifier_lite_warning"}
            ),
        }
    )
    if session["degraded_state"] and session["status"] == "completed":
        session["status"] = "degraded"
    return session


def _base_session(
    *,
    session_id: str,
    status: str,
    society_name: str,
    input_report_id: str | None,
    input_report_summary: Mapping[str, Any],
    memory_refs: tuple[Mapping[str, Any], ...],
    created_at: int,
    completed_at: int,
    warnings: tuple[str, ...],
    degraded_state: bool,
) -> dict[str, Any]:
    return {
        "society_session_version": SOCIETY_RC1_VERSION,
        "session_id": session_id,
        "status": status,
        "mode": "deterministic",
        "society_name": society_name or DEFAULT_SOCIETY_NAME,
        "input_report_id": input_report_id,
        "input_report_summary": dict(input_report_summary),
        "memory_refs": tuple(memory_refs),
        "roles": (),
        "proposals": (),
        "timeline": (),
        "final_summary": "",
        "warnings": warnings,
        "limitations": _limitations(),
        "degraded_state": degraded_state,
        "created_at": created_at,
        "completed_at": completed_at,
        "duration_ms": max(0, int((completed_at - created_at) * 1000)),
        "authority": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": SOCIETY_EXECUTION_PERMISSION,
        "approval_grant": False,
        "capability_grant": False,
        "lease_grant": False,
        "evidence_provided_by_society": False,
        "verifier_success": False,
        "frontend_authority": False,
        "autonomous_execution": False,
        "tool_call_performed": False,
        "shell_command_performed": False,
        "network_call_performed": False,
        "model_call_performed": False,
        "mcp_call_performed": False,
        "memory_write_performed": False,
        "memory_approval_performed": False,
        "memory_candidate_persisted": False,
        "context_package_created": False,
        "role_output_is_truth": False,
        "role_output_is_evidence": False,
        "report_draft_is_verifier": False,
    }


def _context_planner(report: Mapping[str, Any], memory_ids: tuple[str, ...]) -> dict[str, Any]:
    context = _mapping(report.get("context_preflight"))
    inventory = _mapping(report.get("source_inventory"))
    return _proposal(
        role=ROLE_CONTEXT_PLANNER,
        proposal_type="context_requirements",
        title="Context requirements proposal",
        summary="Use the AutoPilot report as bounded local read-only context; no model, network, MCP, or tool context is required.",
        inputs_used=("context_preflight", "root_path", "source_inventory.limitations", "memory_refs"),
        claims={
            "context_sources_used": ("autopilot_report", "source_inventory_metadata", "optional_memory_refs"),
            "root_path": report.get("root_path"),
            "included_file_count": inventory.get("included_file_count", 0),
            "local_read_only_boundary": bool(context.get("local_repo_read_only_context", True)),
            "model_provider_required": False,
            "network_context_allowed": False,
            "context_package_grants_execution_permission": False,
            "memory_ref_count": len(memory_ids),
        },
        limitations=(
            "context_requirements_are_proposals_only",
            "no_raw_unrestricted_context_consumed",
            "no_provider_token_budgeting_in_society_rc1",
        ),
    )


def _policy_reviewer(report: Mapping[str, Any], memory_ids: tuple[str, ...]) -> dict[str, Any]:
    policy = _mapping(report.get("policy_gate"))
    risk_ids = tuple(marker.get("id") for marker in _tuple_of_mappings(report.get("risk_markers")) if marker.get("id"))
    return _proposal(
        role=ROLE_POLICY_REVIEWER,
        proposal_type="risk_classification",
        title="Policy and risk classification proposal",
        summary="AutoPilot report policy gate remains read-only with mutation, shell, network, model, MCP, tool, and memory writes disallowed.",
        inputs_used=("policy_gate", "risk_markers", "warnings", "limitations"),
        claims={
            "read_only": policy.get("read_only") is True,
            "mutation_allowed": False,
            "shell_allowed": False,
            "network_allowed": False,
            "model_allowed": False,
            "mcp_allowed": False,
            "blocked_or_future_gated_capabilities": (
                "mutation",
                "shell",
                "network",
                "model",
                "mcp",
                "tool_execution",
                "memory_write",
            ),
            "risk_marker_ids": risk_ids,
            "memory_refs_are_authority": False,
            "memory_ref_count": len(memory_ids),
        },
        limitations=("policy_review_is_template_based", "risk_classification_is_not_evidence"),
    )


def _memory_curator(report: Mapping[str, Any], memory_ids: tuple[str, ...]) -> dict[str, Any]:
    candidates = tuple(_tuple_of_mappings(report.get("memory_candidate_proposals")))
    return _proposal(
        role=ROLE_MEMORY_CURATOR,
        proposal_type="memory_review",
        title="Memory candidate review proposal",
        summary=f"Reviewed {len(candidates)} AutoPilot memory candidates and {len(memory_ids)} optional memory refs as candidate-only material.",
        inputs_used=("memory_candidate_proposals", "memory_refs"),
        claims={
            "candidate_count": len(candidates),
            "candidate_statuses": tuple(str(item.get("status")) for item in candidates),
            "suggested_scopes": tuple(str(item.get("scope_suggestion")) for item in candidates),
            "suggested_sensitivities": tuple(str(item.get("sensitivity_suggestion")) for item in candidates),
            "selected_memory_refs": memory_ids,
            "memory_candidates_persisted": False,
            "active_memory_created": False,
            "user_approval_required_later": True,
        },
        limitations=(
            "memory_candidates_are_not_active_memory",
            "society_does_not_write_memory",
            "selected_memory_refs_are_not_treated_as_truth",
        ),
    )


def _autopilot_planner(report: Mapping[str, Any], memory_ids: tuple[str, ...]) -> dict[str, Any]:
    inventory = _mapping(report.get("source_inventory"))
    finding_ids = tuple(item.get("id") for item in _tuple_of_mappings(report.get("findings")) if item.get("id"))
    risk_ids = tuple(marker.get("id") for marker in _tuple_of_mappings(report.get("risk_markers")) if marker.get("id"))
    return _proposal(
        role=ROLE_AUTOPILOT_PLANNER,
        proposal_type="follow_up_plan",
        title="Safe follow-up plan proposal",
        summary="The audit produced a metadata-only repo structure report. Safe next steps should stay read-only until an explicit future sprint changes scope.",
        inputs_used=("source_inventory", "findings", "risk_markers"),
        claims={
            "audit_task": report.get("task_id"),
            "included_file_count": inventory.get("included_file_count", 0),
            "excluded_dir_count": len(inventory.get("excluded_dirs") or ()),
            "finding_ids": finding_ids,
            "risk_marker_ids": risk_ids,
            "recommended_next_steps": (
                "display_report_in_mission_control",
                "offer_explicit_memory_proposal_action",
                "keep_future_repo_reads_policy_gated",
            ),
            "mutation_required": False,
            "shell_required": False,
            "model_required": False,
            "mcp_required": False,
            "network_required": False,
            "memory_ref_count": len(memory_ids),
        },
        limitations=("follow_up_plan_is_proposal_only", "no_patch_generation_or_coding_agent_behavior"),
    )


def _verifier_reviewer(report: Mapping[str, Any], memory_ids: tuple[str, ...]) -> dict[str, Any]:
    verifier = _mapping(report.get("verifier_lite"))
    checks = _mapping(verifier.get("checks"))
    return _proposal(
        role=ROLE_VERIFIER_REVIEWER,
        proposal_type="verification_checklist",
        title="Verifier-lite review proposal",
        summary=f"Verifier-lite state is {verifier.get('state', 'unknown')}; it remains scope-bound and is not full evidence verification.",
        inputs_used=("verifier_lite", "report.status", "required_fields"),
        claims={
            "verifier_lite_state": verifier.get("state", "unknown"),
            "checks": dict(checks),
            "report_status": report.get("status"),
            "report_is_evidence": False,
            "verifier_lite_is_full_verifier": False,
            "verifier_success_claimed": False,
            "memory_ref_count": len(memory_ids),
        },
        limitations=(
            "verifier_lite_is_not_evidence",
            "verifier_lite_does_not_certify_all_findings",
            "report_draft_is_not_verifier_success",
        ),
    )


def _report_writer(report: Mapping[str, Any], proposals: list[Mapping[str, Any]]) -> dict[str, Any]:
    proposal_summaries = tuple(str(proposal.get("summary") or "") for proposal in proposals)
    risk_ids = tuple(marker.get("id") for marker in _tuple_of_mappings(report.get("risk_markers")) if marker.get("id"))
    final_summary = (
        f"Deterministic Society Session reviewed AutoPilot report {report.get('report_id')} "
        f"for task {report.get('task_id')}. It produced role proposals for context, policy, "
        f"memory, follow-up planning, verifier-lite review, and reporting. Risk markers: "
        f"{', '.join(risk_ids) if risk_ids else 'none'}."
    )
    return _proposal(
        role=ROLE_REPORT_WRITER,
        proposal_type="report_draft",
        title="Society report draft proposal",
        summary=final_summary,
        inputs_used=("all_role_proposals", "findings", "risk_markers", "verifier_lite"),
        claims={
            "final_summary": final_summary,
            "proposal_summaries": proposal_summaries,
            "findings_summary": tuple(
                str(item.get("title")) for item in _tuple_of_mappings(report.get("findings")) if item.get("title")
            ),
            "memory_candidate_summary": f"{len(_tuple_of_mappings(report.get('memory_candidate_proposals')))} candidate-only memory proposals",
            "policy_context_summary": "read-only, no shell/network/model/MCP/tool execution",
            "verifier_lite_summary": _mapping(report.get("verifier_lite")).get("state", "unknown"),
            "next_actions": (
                "show_session_report_in_mission_control",
                "allow_explicit_memory_proposal_review_later",
                "keep_live_multi_agent_runtime_future_gated",
            ),
        },
        limitations=("report_draft_is_not_evidence", "report_draft_is_not_verifier_success"),
    )


def _proposal(
    *,
    role: str,
    proposal_type: str,
    title: str,
    summary: str,
    inputs_used: tuple[str, ...],
    claims: Mapping[str, Any],
    limitations: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "role": role,
        "proposal_type": proposal_type,
        "title": title,
        "summary": summary,
        "inputs_used": inputs_used,
        "claims": dict(claims),
        "limitations": limitations,
        "authority": False,
        "can_execute_tools": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": SOCIETY_EXECUTION_PERMISSION,
        "approval_grant": False,
        "capability_grant": False,
        "lease_grant": False,
        "verifier_success": False,
        "evidence_provided": False,
        "model_call_performed": False,
        "mcp_call_performed": False,
        "tool_call_performed": False,
        "shell_command_performed": False,
        "network_call_performed": False,
    }


def _input_report_summary(report: Mapping[str, Any]) -> dict[str, Any]:
    inventory = _mapping(report.get("source_inventory"))
    return {
        "report_id": report.get("report_id"),
        "task_id": report.get("task_id"),
        "status": report.get("status"),
        "root_path": report.get("root_path"),
        "included_file_count": inventory.get("included_file_count", 0),
        "risk_marker_count": len(_tuple_of_mappings(report.get("risk_markers"))),
        "memory_candidate_count": len(_tuple_of_mappings(report.get("memory_candidate_proposals"))),
        "verifier_lite_state": _mapping(report.get("verifier_lite")).get("state", "unknown"),
        "report_is_evidence": False,
        "report_is_verifier": False,
    }


def _memory_refs(memory_ids: tuple[str, ...]) -> tuple[Mapping[str, Any], ...]:
    return tuple(
        {
            "memory_id": memory_id,
            "status": "reference_only",
            "retrieved": False,
            "authority": False,
            "active_memory_claimed": False,
        }
        for memory_id in memory_ids
    )


def _session_warnings(report: Mapping[str, Any], memory_ids: tuple[str, ...]) -> tuple[str, ...]:
    warnings = list(str(item) for item in (report.get("warnings") or ()) if str(item))
    if memory_ids:
        warnings.append("memory_ids_are_reference_only_not_retrieved_or_authoritative")
    if report.get("status") not in {"completed", "completed_with_verifier_lite_warning"}:
        warnings.append("autopilot_report_status_not_clean_completed")
    return tuple(dict.fromkeys(warnings))


def _add_event(timeline: list[dict[str, Any]], event: str, role: str, summary: str) -> None:
    timeline.append(
        {
            "sequence": len(timeline) + 1,
            "event": event,
            "role": role,
            "summary": summary,
            "created_at": _now(),
            "backend_owned": True,
            "authority": False,
            "runtime_dispatch_allowed": False,
        }
    )


def _event_name_for_role(role: str) -> str:
    return role.lower().replace(" ", "_") + "_completed"


def _tuple_of_mappings(value: Any) -> tuple[Mapping[str, Any], ...]:
    if isinstance(value, tuple):
        return tuple(item for item in value if isinstance(item, Mapping))
    if isinstance(value, list):
        return tuple(item for item in value if isinstance(item, Mapping))
    return ()


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _now() -> int:
    return int(time.time())


def _limitations() -> tuple[str, ...]:
    return (
        "deterministic_role_templates_only",
        "not_live_autonomous_multi_agent_runtime",
        "no_llm_model_mcp_tool_shell_or_network_calls",
        "role_outputs_are_proposals_not_truth_evidence_or_verifier_success",
        "memory_refs_are_reference_only",
        "memory_candidates_are_not_persisted_or_active",
        "process_local_session_persistence_only",
    )
