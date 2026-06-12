from __future__ import annotations

import pytest

from aegis.core.agent_runtime import (
    AGENT_RUNTIME_EXECUTION_PERMISSION,
    DEFAULT_AGENT_IDS,
    VALID_AGENT_EXECUTION_MODES,
    build_agent_profile_catalog,
    get_agent_profile,
    list_agent_profiles,
    run_bounded_agent_session,
)
from aegis.core.skill_registry import get_skill_manifest


REQUIRED_PROFILE_FIELDS = {
    "agent_id",
    "name",
    "version",
    "description",
    "role",
    "status",
    "allowed_skill_ids",
    "requires_model",
    "model_optional",
    "allowed_input_types",
    "allowed_output_types",
    "risk_class",
    "execution_mode",
    "limitations",
    "non_authority_flags",
}

NON_AUTHORITY_FALSE_FIELDS = {
    "authority",
    "permission_granted",
    "approval_granted",
    "capability_lease_granted",
    "capability_grant",
    "lease_grant",
    "evidence_created",
    "verifier_success",
    "runtime_dispatch_allowed",
    "agent_output_is_truth",
    "agent_output_is_evidence",
    "agent_output_is_verifier_success",
}


def _assert_non_execution(data: dict[str, object]) -> None:
    assert data["authority"] is False
    assert data["permission_granted"] is False
    assert data["approval_granted"] is False
    assert data["capability_lease_granted"] is False
    assert data["capability_grant"] is False
    assert data["lease_grant"] is False
    assert data["evidence_created"] is False
    assert data["verifier_success"] is False
    assert data["runtime_dispatch_allowed"] is False
    assert data["execution_permission"] == AGENT_RUNTIME_EXECUTION_PERMISSION
    assert data["agent_execution_performed"] is False
    assert data["autonomous_loop_started"] is False
    assert data["skill_execution_performed"] is False
    assert data["memory_write_performed"] is False
    assert data["model_call_performed"] is False
    assert data["mcp_call_performed"] is False
    assert data["tool_call_performed"] is False
    assert data["shell_command_performed"] is False
    assert data["file_mutation_performed"] is False
    assert data["network_call_performed"] is False
    assert data["external_api_called"] is False
    assert data["data_sent_external"] is False


def test_built_in_agent_profiles_exist() -> None:
    catalog = build_agent_profile_catalog()

    assert catalog["status"] == "listed"
    assert catalog["profile_count"] == 6
    assert tuple(catalog["default_agent_ids"]) == DEFAULT_AGENT_IDS
    assert {profile["agent_id"] for profile in catalog["profiles"]} == set(DEFAULT_AGENT_IDS)
    assert catalog["agent_execution_allowed"] is False
    assert catalog["skill_execution_allowed"] is False
    assert catalog["model_call_allowed_by_agent_runtime"] is False
    _assert_non_execution(catalog)


def test_each_profile_has_required_fields_and_non_authority_flags() -> None:
    for profile in list_agent_profiles():
        assert REQUIRED_PROFILE_FIELDS <= set(profile)
        assert profile["status"] in {"available", "disabled", "future_gated"}
        assert profile["execution_mode"] in VALID_AGENT_EXECUTION_MODES
        assert profile["execution_mode"] != "executable"
        assert profile["allowed_skill_ids"]
        assert profile["allowed_output_types"] == ["proposal", "timeline_event"]
        non_authority = profile["non_authority_flags"]
        assert NON_AUTHORITY_FALSE_FIELDS <= set(non_authority)
        for field_name in NON_AUTHORITY_FALSE_FIELDS:
            assert non_authority[field_name] is False


def test_profile_allowed_skill_ids_exist_in_skill_registry() -> None:
    for profile in list_agent_profiles():
        for skill_id in profile["allowed_skill_ids"]:
            assert get_skill_manifest(skill_id) is not None, skill_id


def test_create_default_session_succeeds_with_proposals_and_deterministic_timeline() -> None:
    session = run_bounded_agent_session(
        {
            "objective": "Prepare a safe RC review.",
            "context_summary": "Use current Model Gateway and Skill Registry foundations.",
            "autopilot_report_id": "report_123",
            "memory_refs": ["mem_1"],
        }
    )

    assert session["status"] == "completed"
    assert session["mode"] == "deterministic_proposal_only"
    assert session["requested_agent_ids"] == list(DEFAULT_AGENT_IDS)
    assert len(session["proposals"]) == 6
    assert [proposal["agent_id"] for proposal in session["proposals"]] == list(DEFAULT_AGENT_IDS)
    assert [event["event_type"] for event in session["timeline"]] == [
        "agent_session_started",
        "agent_profile_loaded",
        "context_agent_proposal_created",
        "agent_profile_loaded",
        "memory_agent_proposal_created",
        "agent_profile_loaded",
        "autopilot_agent_proposal_created",
        "agent_profile_loaded",
        "policy_agent_proposal_created",
        "agent_profile_loaded",
        "verifier_agent_proposal_created",
        "agent_profile_loaded",
        "report_agent_summary_created",
        "agent_session_completed",
    ]
    _assert_non_execution(session)


def test_create_subset_session_runs_only_requested_agents() -> None:
    session = run_bounded_agent_session(
        {
            "objective": "Review policy only.",
            "agent_ids": ["context_agent", "policy_agent"],
        }
    )

    assert session["status"] == "completed"
    assert session["requested_agent_ids"] == ["context_agent", "policy_agent"]
    assert [proposal["agent_id"] for proposal in session["proposals"]] == ["context_agent", "policy_agent"]
    assert "report_agent_summary_created" not in [event["event_type"] for event in session["timeline"]]
    _assert_non_execution(session)


def test_requested_missing_agent_fails_clearly() -> None:
    session = run_bounded_agent_session({"objective": "Run missing agent.", "agent_ids": ["missing_agent"]})

    assert session["status"] == "failed"
    assert "unknown_agent:missing_agent" in session["failure_reasons"]
    assert session["proposals"] == []
    _assert_non_execution(session)


def test_requested_missing_skill_fails_clearly() -> None:
    session = run_bounded_agent_session({"objective": "Use missing skill.", "skill_ids": ["missing_skill"]})

    assert session["status"] == "failed"
    assert "unknown_skill:missing_skill" in session["failure_reasons"]
    assert session["referenced_skills"] == []
    _assert_non_execution(session)


def test_external_future_gated_skill_refs_do_not_execute() -> None:
    session = run_bounded_agent_session(
        {
            "objective": "Review external policy candidate.",
            "agent_ids": ["policy_agent"],
            "skill_ids": ["ecc_security_config_review"],
        }
    )

    assert session["status"] == "completed"
    assert session["referenced_skills"][0]["skill_id"] == "ecc_security_config_review"
    assert session["referenced_skills"][0]["executable_in_agent_runtime_rc1"] is False
    assert "skill_reference_not_executable_in_agent_runtime_rc1:ecc_security_config_review" in session["warnings"]
    _assert_non_execution(session)


def test_use_model_true_is_future_gated_and_does_not_call_model_gateway_completion() -> None:
    session = run_bounded_agent_session({"objective": "Use model assistance.", "use_model": True})

    assert session["status"] == "degraded"
    assert session["mode"] == "model_assisted_planned"
    assert session["degraded_state"] == "model_assistance_future_gated"
    assert "model_assisted_agents_future_gated" in session["warnings"]
    assert session["model_gateway_awareness"]["model_assistance_requested"] is True
    assert session["model_gateway_awareness"]["model_completion_called"] is False
    assert session["model_gateway_awareness"]["http_request_performed"] is False
    assert session["model_gateway_awareness"]["model_call_performed"] is False
    _assert_non_execution(session)


def test_report_agent_aggregates_prior_proposals() -> None:
    session = run_bounded_agent_session({"objective": "Summarize the agent review."})
    report = session["proposals"][-1]

    assert report["agent_id"] == "report_agent"
    assert report["proposal_type"] == "session_summary"
    assert "context_agent" in report["summary"]
    assert "verifier_agent" in report["summary"]
    assert "summary_is_proposal_only" in report["claims"]


def test_missing_objective_is_input_missing() -> None:
    session = run_bounded_agent_session({"context_summary": "No objective."})

    assert session["status"] == "input_missing"
    assert "missing_objective" in session["failure_reasons"]
    assert session["proposals"] == []
    _assert_non_execution(session)
