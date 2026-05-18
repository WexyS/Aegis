from __future__ import annotations

from aegis.core.action_timeline import project_action_timeline
from aegis.core.protocol import ProtocolEventType, create_event


def test_action_timeline_projects_completed_evidence_in_sequence_order() -> None:
    trace_id = "11111111-1111-4111-8111-111111111111"
    started = create_event(
        ProtocolEventType.ACTION_STARTED,
        {"action_id": "action-1", "tool": "open_app", "target": "steam"},
        trace_id=trace_id,
        session_id="session-one",
    ).to_dict()
    completed = create_event(
        ProtocolEventType.ACTION_COMPLETED,
        {
            "action_id": "action-1",
            "success": True,
            "latency_ms": 42,
            "execution_evidence": {
                "action": "open_app",
                "target": "steam",
                "target_type": "application",
                "method": "launch",
                "verification_state": "verified",
                "pids": [4242],
                "retry_count": 1,
                "recovery_triggered": True,
                "attempts": [],
                "fallback_chain": [{"method": "start_menu"}],
                "warnings": [],
            },
        },
        trace_id=trace_id,
        session_id="session-one",
    ).to_dict()

    timeline = project_action_timeline([started, completed], session_id="session-one")

    assert timeline == [
        {
            "action_id": "action-1",
            "tool": "open_app",
            "status": "success",
            "target": "steam",
            "started_at": started["timestamp"],
            "completed_at": completed["timestamp"],
            "latency_ms": 42,
            "execution_evidence": completed["payload"]["execution_evidence"],
            "trace_id": trace_id,
            "sequence_num": completed["sequence_num"],
        }
    ]


def test_action_timeline_projects_failed_or_active_actions_without_fake_evidence() -> None:
    active = create_event(
        ProtocolEventType.ACTION_STARTED,
        {"action_id": "action-active", "tool": "click", "target": "button"},
        session_id="session-one",
    ).to_dict()
    failed = create_event(
        ProtocolEventType.ACTION_FAILED,
        {
            "action_id": "action-failed",
            "error": "window not found",
            "execution_evidence": {
                "action": "open_app",
                "target": "notepad",
                "target_type": "application",
                "method": "launch",
                "verification_state": "failed",
                "pids": [],
                "retry_count": 0,
                "recovery_triggered": False,
                "attempts": [],
                "fallback_chain": [],
                "warnings": ["window not found"],
            },
        },
        session_id="session-one",
    ).to_dict()
    other_session = create_event(
        ProtocolEventType.ACTION_STARTED,
        {"action_id": "other", "tool": "open_app", "target": "calculator"},
        session_id="session-two",
    ).to_dict()

    timeline = project_action_timeline([active, failed, other_session], session_id="session-one")

    assert [item["action_id"] for item in timeline] == ["action-active", "action-failed"]
    assert timeline[0]["status"] == "active"
    assert timeline[0]["execution_evidence"] is None
    assert timeline[1]["status"] == "error"
    assert timeline[1]["execution_evidence"]["verification_state"] == "failed"


def test_action_timeline_updates_evidence_from_verification_events() -> None:
    started = create_event(
        ProtocolEventType.ACTION_STARTED,
        {"action_id": "action-verify", "tool": "focus_app", "target": "notepad"},
        session_id="session-one",
    ).to_dict()
    completed = create_event(
        ProtocolEventType.ACTION_COMPLETED,
        {"action_id": "action-verify", "success": True, "latency_ms": 25},
        session_id="session-one",
    ).to_dict()
    verification = create_event(
        ProtocolEventType.VERIFICATION_FAILED,
        {
            "action_id": "action-verify",
            "passed": False,
            "verification_state": "unverified",
            "verifier": "process-window-verifier/2",
            "execution_evidence": {
                "action": "focus_app",
                "target": "notepad",
                "target_type": "application",
                "method": "focus_window",
                "verifier": "process-window-verifier/2",
                "verification_state": "unverified",
                "verification_reason": "active window did not match target",
                "pids": [4242],
                "retry_count": 0,
                "recovery_triggered": False,
                "attempts": [],
                "fallback_chain": [],
                "warnings": ["active window did not match target"],
            },
        },
        session_id="session-one",
    ).to_dict()

    timeline = project_action_timeline([started, completed, verification], session_id="session-one")

    assert timeline[0]["action_id"] == "action-verify"
    assert timeline[0]["status"] == "error"
    assert timeline[0]["execution_evidence"]["verifier"] == "process-window-verifier/2"
    assert timeline[0]["execution_evidence"]["verification_state"] == "unverified"


def test_action_timeline_preserves_approval_required_verification_state() -> None:
    started = create_event(
        ProtocolEventType.ACTION_STARTED,
        {"action_id": "action-browser", "tool": "search_web", "target": "aegis runtime"},
        session_id="session-one",
    ).to_dict()
    completed = create_event(
        ProtocolEventType.ACTION_COMPLETED,
        {
            "action_id": "action-browser",
            "success": False,
            "latency_ms": 30,
            "execution_evidence": {
                "action": "search_web",
                "target": "https://www.google.com/search?q=aegis+runtime",
                "target_type": "browser",
                "method": "browser",
                "verifier": "browser-url-gate/1",
                "verification_state": "approval_required",
                "verification_reason": "browser challenge detected",
                "expected": {"bot_challenge_detected": False},
                "observed": {"bot_challenge_detected": True},
            },
        },
        session_id="session-one",
    ).to_dict()
    verification = create_event(
        ProtocolEventType.VERIFICATION_FAILED,
        {
            "action_id": "action-browser",
            "passed": False,
            "verification_state": "approval_required",
            "verifier": "browser-url-gate/1",
            "execution_evidence": completed["payload"]["execution_evidence"],
        },
        session_id="session-one",
    ).to_dict()

    timeline = project_action_timeline([started, completed, verification], session_id="session-one")

    assert timeline[0]["status"] == "approval_required"
    assert timeline[0]["execution_evidence"]["verification_state"] == "approval_required"
    assert timeline[0]["execution_evidence"]["verifier"] == "browser-url-gate/1"


def test_action_timeline_replay_is_sequence_ordered() -> None:
    trace_id = "11111111-1111-4111-8111-111111111111"
    started = create_event(
        ProtocolEventType.ACTION_STARTED,
        {"action_id": "action-shuffled", "tool": "close_app", "target": "notepad"},
        trace_id=trace_id,
        session_id="session-one",
    ).to_dict()
    completed = create_event(
        ProtocolEventType.ACTION_COMPLETED,
        {"action_id": "action-shuffled", "success": True, "latency_ms": 20},
        trace_id=trace_id,
        session_id="session-one",
    ).to_dict()
    verification = create_event(
        ProtocolEventType.VERIFICATION_FAILED,
        {
            "action_id": "action-shuffled",
            "passed": False,
            "execution_evidence": {
                "action": "close_app",
                "target": "notepad",
                "target_type": "application",
                "method": "close_window",
                "verifier": "process-window-verifier/2",
                "verification_state": "failed",
                "verification_reason": "process still alive",
                "pids": [4242],
                "retry_count": 0,
                "recovery_triggered": False,
                "attempts": [],
                "fallback_chain": [],
                "warnings": ["process still alive"],
            },
        },
        trace_id=trace_id,
        session_id="session-one",
    ).to_dict()

    ordered = project_action_timeline([started, completed, verification], session_id="session-one")
    shuffled = project_action_timeline([verification, completed, started], session_id="session-one")

    assert shuffled == ordered
    assert shuffled[0]["status"] == "error"
    assert shuffled[0]["execution_evidence"]["verification_reason"] == "process still alive"


def test_action_timeline_is_bounded_to_latest_actions() -> None:
    events = [
        create_event(
            ProtocolEventType.ACTION_STARTED,
            {"action_id": f"action-{index}", "tool": "open_app", "target": str(index)},
            session_id="session-one",
        ).to_dict()
        for index in range(5)
    ]

    timeline = project_action_timeline(events, limit=2, session_id="session-one")

    assert [item["action_id"] for item in timeline] == ["action-3", "action-4"]


def test_action_timeline_zero_or_negative_limit_returns_empty_projection() -> None:
    event = create_event(
        ProtocolEventType.ACTION_STARTED,
        {"action_id": "action-1", "tool": "open_app", "target": "notepad"},
        session_id="session-one",
    ).to_dict()

    assert project_action_timeline([event], limit=0, session_id="session-one") == []
    assert project_action_timeline([event], limit=-1, session_id="session-one") == []


def test_action_timeline_preserves_explicit_empty_tool_name() -> None:
    started = create_event(
        ProtocolEventType.ACTION_STARTED,
        {"action_id": "action-empty-tool", "tool": "", "target": "notepad"},
        session_id="session-one",
    ).to_dict()

    timeline = project_action_timeline([started], session_id="session-one")

    assert timeline[0]["tool"] == ""
