from __future__ import annotations

from aegis.core.evidence_audit import audit_action_evidence
from aegis.core.protocol import ProtocolEventType, create_event


def test_evidence_audit_reports_verified_and_missing_evidence_counts() -> None:
    verified = create_event(
        ProtocolEventType.ACTION_COMPLETED,
        {
            "action_id": "action-1",
            "success": True,
            "latency_ms": 10,
            "execution_evidence": {
                "action": "focus_app",
                "target": "notepad",
                "target_type": "application",
                "method": "focus_window",
                "verification_state": "verified",
                "pids": [4242],
                "retry_count": 0,
                "recovery_triggered": False,
                "attempts": [],
                "fallback_chain": [],
                "warnings": [],
            },
        },
        session_id="session-one",
    ).to_dict()
    missing = create_event(
        ProtocolEventType.ACTION_FAILED,
        {"action_id": "action-2", "error": "failed without evidence"},
        session_id="session-one",
    ).to_dict()
    other_session = create_event(
        ProtocolEventType.ACTION_COMPLETED,
        {"action_id": "action-3", "success": True, "latency_ms": 1},
        session_id="session-two",
    ).to_dict()

    report = audit_action_evidence([verified, missing, other_session], session_id="session-one")

    assert report["scan_version"] == "evidence-audit/1"
    assert report["read_only"] is True
    assert report["status"] == "warning"
    assert report["action_event_count"] == 2
    assert report["action_count"] == 2
    assert report["completed_or_failed_count"] == 2
    assert report["success_count"] == 1
    assert report["error_count"] == 1
    assert report["evidence_backed_count"] == 1
    assert report["missing_evidence_count"] == 1
    assert report["verification_counts"] == {"missing": 1, "verified": 1}
    assert report["latest_sequence_num"] == missing["sequence_num"]


def test_evidence_audit_is_ok_when_completed_actions_are_evidence_backed() -> None:
    completed = create_event(
        ProtocolEventType.ACTION_COMPLETED,
        {
            "action_id": "action-1",
            "success": True,
            "latency_ms": 10,
            "execution_evidence": {
                "action": "close_app",
                "target": "notepad",
                "target_type": "application",
                "method": "terminate_process",
                "verification_state": "verified",
                "pids": [],
                "process_alive": False,
                "retry_count": 0,
                "recovery_triggered": False,
                "attempts": [],
                "fallback_chain": [],
                "warnings": [],
            },
        },
    ).to_dict()

    report = audit_action_evidence([completed])

    assert report["status"] == "ok"
    assert report["evidence_backed_count"] == 1
    assert report["missing_evidence_count"] == 0
    assert report["verification_counts"] == {"verified": 1}
