from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aegis.core.model_gateway import build_model_gateway_status
from aegis.core.skill_registry import get_skill_manifest


AGENT_RUNTIME_RC1_VERSION = "bounded-agent-runtime-rc1/1"
AGENT_RUNTIME_EXECUTION_PERMISSION = "not_granted_by_agent_runtime"

VALID_AGENT_STATUSES = frozenset({"available", "disabled", "future_gated"})
VALID_AGENT_EXECUTION_MODES = frozenset(
    {"proposal_only", "deterministic_fallback", "model_assisted_planned", "future_policy_gated"}
)

DEFAULT_AGENT_IDS = (
    "context_agent",
    "memory_agent",
    "autopilot_agent",
    "policy_agent",
    "verifier_agent",
    "report_agent",
)


@dataclass(frozen=True)
class AgentProfile:
    agent_id: str
    name: str
    version: str
    description: str
    role: str
    status: str
    allowed_skill_ids: tuple[str, ...]
    requires_model: bool
    model_optional: bool
    allowed_input_types: tuple[str, ...]
    allowed_output_types: tuple[str, ...]
    risk_class: str
    execution_mode: str
    limitations: tuple[str, ...]
    non_authority_flags: Mapping[str, bool] = field(default_factory=lambda: _non_authority_flags())

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "role": self.role,
            "status": self.status,
            "allowed_skill_ids": list(self.allowed_skill_ids),
            "requires_model": self.requires_model,
            "model_optional": self.model_optional,
            "allowed_input_types": list(self.allowed_input_types),
            "allowed_output_types": list(self.allowed_output_types),
            "risk_class": self.risk_class,
            "execution_mode": self.execution_mode,
            "limitations": list(self.limitations),
            "non_authority_flags": dict(self.non_authority_flags),
        }


class AgentSessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, dict[str, Any]] = {}

    def save(self, session: Mapping[str, Any]) -> None:
        session_id = str(session.get("session_id") or "")
        if session_id:
            self._sessions[session_id] = dict(session)

    def get(self, session_id: str) -> dict[str, Any] | None:
        session = self._sessions.get(str(session_id))
        return dict(session) if session is not None else None

    def list(self) -> list[dict[str, Any]]:
        return [dict(session) for session in self._sessions.values()]


def list_agent_profiles() -> list[dict[str, Any]]:
    return [profile.to_dict() for profile in BUILTIN_AGENT_PROFILES]


def get_agent_profile(agent_id: str) -> dict[str, Any] | None:
    requested = str(agent_id or "").strip()
    for profile in BUILTIN_AGENT_PROFILES:
        if profile.agent_id == requested:
            return profile.to_dict()
    return None


def build_agent_profile_catalog() -> dict[str, Any]:
    profiles = list_agent_profiles()
    return {
        "agent_runtime_version": AGENT_RUNTIME_RC1_VERSION,
        "status": "listed",
        "profile_count": len(profiles),
        "profiles": profiles,
        "default_agent_ids": list(DEFAULT_AGENT_IDS),
        "execution_modes": sorted(VALID_AGENT_EXECUTION_MODES),
        "profile_registry_source": "aegis_builtin_static_profiles",
        "agent_execution_allowed": False,
        "skill_execution_allowed": False,
        "model_call_allowed_by_agent_runtime": False,
        "session_persistence": "process_local_in_memory",
        **_runtime_non_execution_flags(),
    }


def run_bounded_agent_session(request: Mapping[str, Any] | None) -> dict[str, Any]:
    request_data = dict(request or {})
    started_at = _now()
    session_id = str(request_data.get("session_id") or f"agent_session_{uuid4().hex}")
    objective = _text(request_data.get("objective"))
    context_summary = _text(request_data.get("context_summary")) or ""
    requested_agent_ids = _requested_values(request_data.get("agent_ids"), DEFAULT_AGENT_IDS)
    requested_skill_ids = _requested_values(request_data.get("skill_ids"), ())
    use_model = bool(request_data.get("use_model", False))
    dry_run = bool(request_data.get("dry_run", True))

    failures: list[str] = []
    if not objective:
        failures.append("missing_objective")

    profiles = _profiles_for(requested_agent_ids)
    found_agent_ids = {profile.agent_id for profile in profiles}
    for agent_id in requested_agent_ids:
        if agent_id not in found_agent_ids:
            failures.append(f"unknown_agent:{agent_id}")

    referenced_skills = _skill_metadata_for(requested_skill_ids)
    found_skill_ids = {skill["skill_id"] for skill in referenced_skills}
    for skill_id in requested_skill_ids:
        if skill_id not in found_skill_ids:
            failures.append(f"unknown_skill:{skill_id}")

    if failures:
        return _session_envelope(
            session_id=session_id,
            status="input_missing" if "missing_objective" in failures else "failed",
            mode="dry_run" if dry_run else "deterministic_proposal_only",
            objective=objective or "",
            context_summary=context_summary,
            requested_agent_ids=requested_agent_ids,
            requested_skill_ids=requested_skill_ids,
            profiles=[],
            proposals=[],
            timeline=[
                _timeline_event(1, "agent_session_started", "agent_runtime", "Agent session request received."),
                _timeline_event(2, "agent_session_failed", "agent_runtime", "Agent session failed validation."),
            ],
            warnings=(),
            limitations=_common_limitations(),
            failure_reasons=tuple(dict.fromkeys(failures)),
            started_at=started_at,
            degraded_state="none",
            model_gateway_awareness=_model_gateway_awareness(use_model),
            dry_run=dry_run,
            referenced_skills=referenced_skills,
        )

    warnings: list[str] = []
    degraded_state = "none"
    status = "completed"
    mode = "deterministic_proposal_only"
    if use_model:
        status = "degraded"
        mode = "model_assisted_planned"
        degraded_state = "model_assistance_future_gated"
        warnings.append("model_assisted_agents_future_gated")

    timeline: list[dict[str, Any]] = [
        _timeline_event(1, "agent_session_started", "agent_runtime", "Agent session started.")
    ]
    proposals: list[dict[str, Any]] = []
    event_index = 2
    for profile in profiles:
        profile_dict = profile.to_dict()
        timeline.append(
            _timeline_event(
                event_index,
                "agent_profile_loaded",
                profile.agent_id,
                f"{profile.name} profile loaded as metadata.",
            )
        )
        event_index += 1
        proposal = _proposal_for(profile, session_id, objective or "", context_summary, request_data, proposals)
        proposals.append(proposal)
        timeline.append(
            _timeline_event(
                event_index,
                "report_agent_summary_created" if profile.agent_id == "report_agent" else f"{profile.agent_id}_proposal_created",
                profile.agent_id,
                f"{profile.name} proposal created.",
                {"proposal_id": proposal["proposal_id"]},
            )
        )
        event_index += 1
        _append_external_skill_warnings(profile_dict, warnings)

    timeline.append(
        _timeline_event(event_index, "agent_session_completed", "agent_runtime", "Agent session completed.")
    )

    return _session_envelope(
        session_id=session_id,
        status=status,
        mode=mode,
        objective=objective or "",
        context_summary=context_summary,
        requested_agent_ids=requested_agent_ids,
        requested_skill_ids=requested_skill_ids,
        profiles=[profile.to_dict() for profile in profiles],
        proposals=proposals,
        timeline=timeline,
        warnings=tuple(dict.fromkeys(warnings)),
        limitations=_common_limitations(),
        failure_reasons=(),
        started_at=started_at,
        degraded_state=degraded_state,
        model_gateway_awareness=_model_gateway_awareness(use_model),
        dry_run=dry_run,
        referenced_skills=referenced_skills,
    )


def _session_envelope(
    *,
    session_id: str,
    status: str,
    mode: str,
    objective: str,
    context_summary: str,
    requested_agent_ids: tuple[str, ...],
    requested_skill_ids: tuple[str, ...],
    profiles: list[dict[str, Any]],
    proposals: list[dict[str, Any]],
    timeline: list[dict[str, Any]],
    warnings: tuple[str, ...],
    limitations: tuple[str, ...],
    failure_reasons: tuple[str, ...],
    started_at: str,
    degraded_state: str,
    model_gateway_awareness: Mapping[str, Any],
    dry_run: bool,
    referenced_skills: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "agent_runtime_version": AGENT_RUNTIME_RC1_VERSION,
        "session_id": session_id,
        "status": status,
        "mode": mode,
        "dry_run": dry_run,
        "input_summary": {
            "objective": objective,
            "context_summary": context_summary,
            "has_context_summary": bool(context_summary),
        },
        "requested_agent_ids": list(requested_agent_ids),
        "requested_skill_ids": list(requested_skill_ids),
        "agents": profiles,
        "referenced_skills": referenced_skills,
        "proposals": proposals,
        "timeline": timeline,
        "warnings": list(warnings),
        "limitations": list(limitations),
        "failure_reasons": list(failure_reasons),
        "created_at": started_at,
        "completed_at": _now(),
        "degraded_state": degraded_state,
        "model_gateway_awareness": dict(model_gateway_awareness),
        "session_persistence": "process_local_in_memory",
        **_runtime_non_execution_flags(),
    }


def _proposal_for(
    profile: AgentProfile,
    session_id: str,
    objective: str,
    context_summary: str,
    request_data: Mapping[str, Any],
    prior_proposals: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    builders = {
        "context_agent": _context_proposal,
        "memory_agent": _memory_proposal,
        "autopilot_agent": _autopilot_proposal,
        "policy_agent": _policy_proposal,
        "verifier_agent": _verifier_proposal,
        "report_agent": _report_proposal,
    }
    builder = builders[profile.agent_id]
    content = builder(profile, objective, context_summary, request_data, prior_proposals)
    return {
        "proposal_id": f"{session_id}:{profile.agent_id}:proposal",
        "agent_id": profile.agent_id,
        "proposal_type": content["proposal_type"],
        "title": content["title"],
        "summary": content["summary"],
        "inputs_used": content["inputs_used"],
        "referenced_skill_ids": list(profile.allowed_skill_ids),
        "claims": content["claims"],
        "limitations": content["limitations"],
        "recommended_next_steps": content["recommended_next_steps"],
        "non_authority_flags": _non_authority_flags(),
    }


def _context_proposal(
    profile: AgentProfile,
    objective: str,
    context_summary: str,
    request_data: Mapping[str, Any],
    prior_proposals: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    inputs = ["objective"]
    if context_summary:
        inputs.append("context_summary")
    return {
        "proposal_type": "context_review",
        "title": "Context boundary review",
        "summary": "Context inputs were identified for proposal planning; context does not grant execution permission.",
        "inputs_used": inputs,
        "claims": [
            "context_is_metadata_for_this_session",
            "context_does_not_authorize_runtime_dispatch",
        ],
        "limitations": [
            "no_context_retrieval_performed",
            "context_summary_not_evidence",
            "context_package_not_permission",
        ],
        "recommended_next_steps": [
            "keep private or sensitive context behind future context policy gates",
            "attach source refs before model-assisted use",
        ],
    }


def _memory_proposal(
    profile: AgentProfile,
    objective: str,
    context_summary: str,
    request_data: Mapping[str, Any],
    prior_proposals: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    memory_refs = _requested_values(request_data.get("memory_refs"), ())
    memory_state = "memory_refs_provided" if memory_refs else "no_memory_refs_provided"
    return {
        "proposal_type": "memory_review",
        "title": "Memory candidate review",
        "summary": f"Memory input state: {memory_state}. No memory write occurred.",
        "inputs_used": ["memory_refs"] if memory_refs else [],
        "claims": [
            "memory_is_not_authority",
            "memory_write_not_performed",
        ],
        "limitations": [
            "no_memory_retrieval_performed",
            "no_memory_write_performed",
            "future_memory_candidates_require_explicit_review",
        ],
        "recommended_next_steps": [
            "review candidate memories explicitly before persistence",
            "preserve source refs for future memory candidates",
        ],
    }


def _autopilot_proposal(
    profile: AgentProfile,
    objective: str,
    context_summary: str,
    request_data: Mapping[str, Any],
    prior_proposals: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    report_id = _text(request_data.get("autopilot_report_id"))
    return {
        "proposal_type": "autopilot_review",
        "title": "AutoPilot read-only planning review",
        "summary": (
            f"AutoPilot report reference {report_id} was noted as input metadata."
            if report_id
            else "No AutoPilot report reference was supplied."
        ),
        "inputs_used": ["autopilot_report_id"] if report_id else [],
        "claims": [
            "autopilot_report_is_not_evidence",
            "autopilot_execution_not_performed",
        ],
        "limitations": [
            "no_repo_scan_performed",
            "no_autopilot_run_triggered",
            "read_only_next_steps_only",
        ],
        "recommended_next_steps": [
            "use AutoPilot API explicitly for future read-only report generation",
            "keep report interpretation proposal-only",
        ],
    }


def _policy_proposal(
    profile: AgentProfile,
    objective: str,
    context_summary: str,
    request_data: Mapping[str, Any],
    prior_proposals: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "proposal_type": "policy_review",
        "title": "Policy and capability boundary review",
        "summary": "Backend policy remains authoritative; this session grants no execution capability.",
        "inputs_used": ["objective"],
        "claims": [
            "tool_execution_blocked",
            "shell_execution_blocked",
            "mcp_execution_blocked",
            "file_mutation_blocked",
            "memory_write_blocked",
            "approval_and_lease_not_granted",
        ],
        "limitations": [
            "policy_review_is_not_policy_allow",
            "allowed_skill_ids_are_not_execution_permission",
        ],
        "recommended_next_steps": [
            "require explicit policy and approval gates before side effects",
            "keep external candidates future-gated",
        ],
    }


def _verifier_proposal(
    profile: AgentProfile,
    objective: str,
    context_summary: str,
    request_data: Mapping[str, Any],
    prior_proposals: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "proposal_type": "verifier_review",
        "title": "Verifier boundary review",
        "summary": "Checklist-style review was produced; no verifier success was created.",
        "inputs_used": ["objective"],
        "claims": [
            "checklist_is_not_verification",
            "verifier_success_not_created",
        ],
        "limitations": [
            "no_backend_verifier_invoked",
            "verifier_lite_limitations_preserved_if_referenced",
        ],
        "recommended_next_steps": [
            "define backend verifier checks before claiming success",
            "keep evidence expectations separate from proposals",
        ],
    }


def _report_proposal(
    profile: AgentProfile,
    objective: str,
    context_summary: str,
    request_data: Mapping[str, Any],
    prior_proposals: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    prior_agent_ids = [str(proposal.get("agent_id")) for proposal in prior_proposals]
    return {
        "proposal_type": "session_summary",
        "title": "Agent session proposal summary",
        "summary": (
            "Aggregated prior proposal outputs for the session: "
            + (", ".join(prior_agent_ids) if prior_agent_ids else "none before report agent")
            + "."
        ),
        "inputs_used": ["prior_proposals"],
        "claims": [
            "summary_is_proposal_only",
            "prior_agent_outputs_are_not_authority",
        ],
        "limitations": [
            "report_is_not_evidence",
            "report_does_not_grant_permission",
            "model_summarization_not_called",
        ],
        "recommended_next_steps": [
            "use summary as planning material only",
            "request explicit gates before execution",
        ],
    }


def _model_gateway_awareness(use_model: bool) -> dict[str, Any]:
    status = build_model_gateway_status()
    return {
        "model_gateway_status": status["status"],
        "provider": status["provider"],
        "enabled": status["enabled"],
        "model_configured": status["model_configured"],
        "model_assistance_requested": use_model,
        "model_assistance_available_to_agent_runtime": False,
        "model_completion_called": False,
        "http_request_performed": False,
        "model_call_performed": False,
        "degraded_reason": "model_assisted_agents_future_gated" if use_model else None,
    }


def _profiles_for(agent_ids: Sequence[str]) -> list[AgentProfile]:
    requested = set(agent_ids)
    return [profile for profile in BUILTIN_AGENT_PROFILES if profile.agent_id in requested]


def _skill_metadata_for(skill_ids: Sequence[str]) -> list[dict[str, Any]]:
    skills: list[dict[str, Any]] = []
    for skill_id in skill_ids:
        manifest = get_skill_manifest(skill_id)
        if manifest is not None:
            skills.append(
                {
                    "skill_id": manifest["skill_id"],
                    "status": manifest["status"],
                    "risk_class": manifest["risk_class"],
                    "execution_mode": manifest["execution_mode"],
                    "external_source": manifest["external_source"],
                    "executable_in_agent_runtime_rc1": False,
                }
            )
    return skills


def _append_external_skill_warnings(profile: Mapping[str, Any], warnings: list[str]) -> None:
    for skill_id in profile.get("allowed_skill_ids", []):
        manifest = get_skill_manifest(str(skill_id))
        if manifest is None:
            continue
        if manifest["status"] in {"candidate", "future_gated"} or manifest["execution_mode"] in {
            "external_candidate",
            "future_policy_gated",
        }:
            warnings.append(f"skill_reference_not_executable_in_agent_runtime_rc1:{skill_id}")


def _timeline_event(
    index: int,
    event_type: str,
    actor: str,
    summary: str,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "event_index": index,
        "event_type": event_type,
        "actor": actor,
        "summary": summary,
        "metadata": dict(metadata or {}),
        "non_authority_flags": _non_authority_flags(),
    }


def _requested_values(value: Any, default: Sequence[str]) -> tuple[str, ...]:
    if value is None:
        return tuple(default)
    if isinstance(value, str):
        text = value.strip()
        return (text,) if text else tuple(default)
    if isinstance(value, Sequence):
        values = tuple(str(item).strip() for item in value if str(item).strip())
        return values or tuple(default)
    return tuple(default)


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _common_limitations() -> tuple[str, ...]:
    return (
        "proposal_only_agent_runtime",
        "no_autonomous_loop",
        "no_skill_execution",
        "no_tool_mcp_shell_or_file_mutation",
        "no_memory_write",
        "no_evidence_or_verifier_success",
        "no_model_completion_call_by_agent_runtime_rc1",
    )


def _non_authority_flags() -> dict[str, bool]:
    return {
        "authority": False,
        "permission_granted": False,
        "approval_granted": False,
        "capability_lease_granted": False,
        "capability_grant": False,
        "lease_grant": False,
        "evidence_created": False,
        "verifier_success": False,
        "runtime_dispatch_allowed": False,
        "agent_output_is_truth": False,
        "agent_output_is_evidence": False,
        "agent_output_is_verifier_success": False,
    }


def _runtime_non_execution_flags() -> dict[str, Any]:
    return {
        "authority": False,
        "permission_granted": False,
        "approval_granted": False,
        "capability_lease_granted": False,
        "capability_grant": False,
        "lease_grant": False,
        "evidence_created": False,
        "verifier_success": False,
        "runtime_dispatch_allowed": False,
        "execution_permission": AGENT_RUNTIME_EXECUTION_PERMISSION,
        "agent_execution_performed": False,
        "autonomous_loop_started": False,
        "skill_execution_performed": False,
        "memory_write_performed": False,
        "model_call_performed": False,
        "mcp_call_performed": False,
        "tool_call_performed": False,
        "shell_command_performed": False,
        "file_mutation_performed": False,
        "network_call_performed": False,
        "external_api_called": False,
        "data_sent_external": False,
    }


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _profile(
    *,
    agent_id: str,
    name: str,
    description: str,
    role: str,
    allowed_skill_ids: Sequence[str],
    allowed_input_types: Sequence[str],
    limitations: Sequence[str],
    requires_model: bool = False,
    model_optional: bool = True,
    execution_mode: str = "proposal_only",
    risk_class: str = "local_read_only",
    status: str = "available",
) -> AgentProfile:
    return AgentProfile(
        agent_id=agent_id,
        name=name,
        version="rc1",
        description=description,
        role=role,
        status=status,
        allowed_skill_ids=tuple(allowed_skill_ids),
        requires_model=requires_model,
        model_optional=model_optional,
        allowed_input_types=tuple(allowed_input_types),
        allowed_output_types=("proposal", "timeline_event"),
        risk_class=risk_class,
        execution_mode=execution_mode,
        limitations=tuple(limitations),
    )


BUILTIN_AGENT_PROFILES: tuple[AgentProfile, ...] = (
    _profile(
        agent_id="context_agent",
        name="Context Agent",
        description="Reviews supplied context metadata and context boundaries.",
        role="context_planner",
        allowed_skill_ids=("context_package_review", "model_assisted_explanation"),
        allowed_input_types=("objective", "context_summary", "source_refs"),
        limitations=("context_is_not_permission", "model_assisted_explanation_not_called_in_rc1"),
        requires_model=False,
    ),
    _profile(
        agent_id="memory_agent",
        name="Memory Agent",
        description="Reviews memory references and future memory candidate boundaries.",
        role="memory_reviewer",
        allowed_skill_ids=("memory_candidate_review", "report_summarization"),
        allowed_input_types=("objective", "memory_refs", "context_summary"),
        limitations=("memory_is_not_authority", "memory_write_not_performed"),
        requires_model=False,
    ),
    _profile(
        agent_id="autopilot_agent",
        name="AutoPilot Agent",
        description="Reviews AutoPilot report references and read-only next-step candidates.",
        role="autopilot_planner",
        allowed_skill_ids=("repo_structure_audit", "model_assisted_explanation"),
        allowed_input_types=("objective", "autopilot_report_id", "context_summary"),
        limitations=("autopilot_report_is_not_evidence", "autopilot_not_executed_by_agent_runtime"),
        requires_model=False,
    ),
    _profile(
        agent_id="policy_agent",
        name="Policy Agent",
        description="Reviews policy and capability boundaries for proposal-only sessions.",
        role="policy_reviewer",
        allowed_skill_ids=("context_package_review", "ecc_security_config_review"),
        allowed_input_types=("objective", "context_summary", "skill_ids"),
        limitations=("policy_review_is_not_policy_allow", "external_skill_reference_not_executable"),
        requires_model=False,
    ),
    _profile(
        agent_id="verifier_agent",
        name="Verifier Agent",
        description="Separates checklist review from backend verifier success.",
        role="verifier_reviewer",
        allowed_skill_ids=("context_package_review",),
        allowed_input_types=("objective", "context_summary"),
        limitations=("no_verifier_success_created", "checklist_is_not_verification"),
        requires_model=False,
    ),
    _profile(
        agent_id="report_agent",
        name="Report Agent",
        description="Aggregates prior proposal outputs into a proposal-only summary.",
        role="report_writer",
        allowed_skill_ids=("report_summarization", "model_assisted_explanation"),
        allowed_input_types=("objective", "prior_proposals", "context_summary"),
        limitations=("report_is_not_evidence", "model_summarization_not_called_in_rc1"),
        requires_model=True,
        model_optional=True,
        execution_mode="model_assisted_planned",
        risk_class="local_model_required",
    ),
)
