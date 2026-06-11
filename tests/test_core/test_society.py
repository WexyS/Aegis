from __future__ import annotations

from pathlib import Path

from aegis.core.autopilot import run_repo_structure_audit
from aegis.core.society import ROLE_ORDER, run_deterministic_society_session


def _write(path: Path, text: str = "x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _sample_report(tmp_path: Path) -> dict:
    root = tmp_path / "repo"
    _write(root / "README.md", "# Demo")
    _write(root / "pyproject.toml", "[project]\nname='demo'\n")
    _write(root / "src" / "demo" / "__init__.py", "")
    _write(root / "tests" / "test_demo.py", "def test_demo(): assert True\n")
    _write(root / "docs" / "index.md", "# Docs")
    return run_repo_structure_audit(root_path=str(root))


def test_society_run_from_valid_autopilot_report(tmp_path):
    report = _sample_report(tmp_path)

    session = run_deterministic_society_session(
        autopilot_report=report,
        autopilot_report_id=report["report_id"],
    )

    assert session["status"] == "completed"
    assert session["mode"] == "deterministic"
    assert session["input_report_id"] == report["report_id"]
    assert session["runtime_dispatch_allowed"] is False
    assert session["autonomous_execution"] is False
    assert session["model_call_performed"] is False
    assert session["mcp_call_performed"] is False
    assert session["tool_call_performed"] is False
    assert session["shell_command_performed"] is False
    assert session["network_call_performed"] is False


def test_society_returns_input_missing_for_missing_report():
    session = run_deterministic_society_session(
        autopilot_report=None,
        autopilot_report_id="missing",
    )

    assert session["status"] == "input_missing"
    assert session["degraded_state"] is True
    assert "autopilot_report_missing" in session["warnings"]
    assert session["proposals"] == ()


def test_all_six_roles_produce_proposals(tmp_path):
    session = run_deterministic_society_session(autopilot_report=_sample_report(tmp_path))

    assert [role["name"] for role in session["roles"]] == list(ROLE_ORDER)
    assert [proposal["role"] for proposal in session["proposals"]] == list(ROLE_ORDER)
    assert [proposal["proposal_type"] for proposal in session["proposals"]] == [
        "context_requirements",
        "risk_classification",
        "memory_review",
        "follow_up_plan",
        "verification_checklist",
        "report_draft",
    ]


def test_timeline_contains_completed_role_events_in_order(tmp_path):
    session = run_deterministic_society_session(autopilot_report=_sample_report(tmp_path))

    events = [item["event"] for item in session["timeline"]]

    assert events == [
        "society_session_started",
        "context_planner_completed",
        "policy_reviewer_completed",
        "memory_curator_completed",
        "autopilot_planner_completed",
        "verifier_reviewer_completed",
        "report_writer_completed",
        "society_session_completed",
    ]
    assert [item["sequence"] for item in session["timeline"]] == list(range(1, 9))


def test_report_writer_aggregates_proposal_summaries(tmp_path):
    report = _sample_report(tmp_path)
    session = run_deterministic_society_session(autopilot_report=report)
    report_writer = session["proposals"][-1]

    assert report_writer["role"] == "Report Writer"
    assert report["report_id"] in report_writer["summary"]
    assert len(report_writer["claims"]["proposal_summaries"]) == 5
    assert session["final_summary"] == report_writer["claims"]["final_summary"]


def test_memory_curator_marks_candidates_candidate_only_and_not_persisted(tmp_path):
    report = _sample_report(tmp_path)
    session = run_deterministic_society_session(
        autopilot_report=report,
        memory_ids=("mem_existing",),
    )
    memory_curator = session["proposals"][2]

    assert memory_curator["role"] == "Memory Curator"
    assert memory_curator["claims"]["candidate_count"] == len(report["memory_candidate_proposals"])
    assert set(memory_curator["claims"]["candidate_statuses"]) == {"candidate_only"}
    assert memory_curator["claims"]["memory_candidates_persisted"] is False
    assert memory_curator["claims"]["active_memory_created"] is False
    assert session["memory_write_performed"] is False
    assert session["memory_refs"][0]["retrieved"] is False
    assert session["memory_refs"][0]["authority"] is False


def test_role_proposals_are_non_authoritative(tmp_path):
    session = run_deterministic_society_session(autopilot_report=_sample_report(tmp_path))

    for proposal in session["proposals"]:
        assert proposal["authority"] is False
        assert proposal["can_execute_tools"] is False
        assert proposal["runtime_dispatch_allowed"] is False
        assert proposal["verifier_success"] is False
        assert proposal["evidence_provided"] is False
        assert proposal["model_call_performed"] is False
        assert proposal["mcp_call_performed"] is False
        assert proposal["tool_call_performed"] is False
        assert proposal["shell_command_performed"] is False
        assert proposal["network_call_performed"] is False


def test_society_can_run_without_active_memory(tmp_path):
    session = run_deterministic_society_session(autopilot_report=_sample_report(tmp_path))

    assert session["memory_refs"] == ()
    memory_curator = session["proposals"][2]
    assert memory_curator["claims"]["selected_memory_refs"] == ()
    assert memory_curator["claims"]["user_approval_required_later"] is True
