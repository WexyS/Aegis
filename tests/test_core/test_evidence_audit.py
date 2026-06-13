from __future__ import annotations

from copy import deepcopy

from aegis.core.evidence_audit import audit_action_evidence
from aegis.core.protocol import ProtocolEventType, create_event


def passed_check(name: str) -> dict:
    return {
        "check_name": name,
        "expected": "present and passed",
        "observed": "ok",
        "passed": True,
        "reason": "ok",
    }


def failed_check(name: str) -> dict:
    return {
        "check_name": name,
        "expected": "successful execution",
        "observed": "failed execution",
        "passed": False,
        "reason": "negative evidence records a failed outcome",
    }


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
                "verification_checks": [
                    passed_check("process_name_known"),
                    passed_check("single_matching_window"),
                    passed_check("foreground_hwnd_present"),
                    passed_check("foreground_title_matches_target"),
                    passed_check("foreground_pid_matches_target_process"),
                    passed_check("foreground_window_matches_target"),
                ],
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

    assert report["scan_version"] == "evidence-audit/2"
    assert report["read_only"] is True
    assert report["status"] == "warning"
    assert report["action_event_count"] == 2
    assert report["action_count"] == 2
    assert report["completed_or_failed_count"] == 2
    assert report["success_count"] == 1
    assert report["error_count"] == 1
    assert report["evidence_backed_count"] == 1
    assert report["missing_evidence_count"] == 1
    assert report["verified_action_count"] == 1
    assert report["unverified_evidence_count"] == 0
    assert report["failed_evidence_count"] == 0
    assert report["check_pass_count"] == 6
    assert report["check_fail_count"] == 0
    assert report["critical_failure_count"] == 0
    assert report["verification_counts"] == {"missing": 1, "verified": 1}
    assert report["latest_sequence_num"] == missing["sequence_num"]
    assert report["current_missing_evidence_count"] == 1
    assert report["historical_missing_evidence_count"] == 0
    assert report["unknown_era_missing_evidence_count"] == 0
    assert report["classification"]["class_counts"]["current_session_missing_evidence"] == 1


def test_evidence_audit_counts_failed_negative_evidence_as_backed_not_missing() -> None:
    failed = create_event(
        ProtocolEventType.ACTION_FAILED,
        {
            "action_id": "action-negative",
            "error": "Error: File already exists",
            "execution_evidence": {
                "action": "create_file",
                "target": "scratch/new.txt",
                "target_type": "file",
                "method": "negative_result",
                "verifier": "executor-negative-evidence/1",
                "verification_state": "failed",
                "verification_reason": "tool_returned_error: Error: File already exists",
                "retry_count": 0,
                "recovery_triggered": False,
                "attempts": [],
                "fallback_chain": [],
                "observed": {
                    "failure_kind": "tool_returned_error",
                    "dispatch_attempted": True,
                    "dispatch_succeeded": False,
                    "verified_success": False,
                },
                "verification_checks": [
                    passed_check("negative_evidence_recorded"),
                    failed_check("dispatch_succeeded"),
                    failed_check("verified_success"),
                ],
                "warnings": ["Error: File already exists"],
            },
        },
    ).to_dict()

    report = audit_action_evidence([failed])

    assert report["status"] == "fail"
    assert report["action_count"] == 1
    assert report["error_count"] == 1
    assert report["evidence_backed_count"] == 1
    assert report["missing_evidence_count"] == 0
    assert report["failed_evidence_count"] == 1
    assert report["verified_action_count"] == 0
    assert report["check_fail_count"] == 2
    assert report["negative_evidence_count"] == 1
    assert report["classification"]["negative_evidence_count"] == 1
    assert report["classification"]["class_counts"]["negative_evidence_present"] == 1
    assert report["verification_counts"] == {"failed": 1}
    assert report["verifier_counts"] == {"executor-negative-evidence/1": 1}


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
                "verification_checks": [
                    passed_check("process_name_known"),
                    passed_check("process_not_alive"),
                ],
                "warnings": [],
            },
        },
    ).to_dict()

    report = audit_action_evidence([completed])

    assert report["status"] == "ok"
    assert report["evidence_backed_count"] == 1
    assert report["missing_evidence_count"] == 0
    assert report["critical_failure_count"] == 0
    assert report["verification_counts"] == {"verified": 1}


def test_evidence_audit_fails_when_critical_check_is_failed() -> None:
    completed = create_event(
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
                "verification_checks": [
                    passed_check("process_name_known"),
                    passed_check("single_matching_window"),
                    passed_check("foreground_hwnd_present"),
                    passed_check("foreground_title_matches_target"),
                    {
                        "check_name": "foreground_pid_matches_target_process",
                        "expected": {"pid": 4242},
                        "observed": {"pid": 5151},
                        "passed": False,
                        "reason": "foreground PID does not match target process",
                    },
                    passed_check("foreground_window_matches_target"),
                ],
                "warnings": [],
            },
        },
    ).to_dict()

    report = audit_action_evidence([completed])

    assert report["status"] == "fail"
    assert report["check_fail_count"] == 1
    assert report["critical_failure_count"] == 1
    assert report["critical_failures"][0]["check_name"] == "foreground_pid_matches_target_process"


def test_evidence_audit_counts_verification_protocol_events() -> None:
    verified = create_event(
        ProtocolEventType.VERIFICATION_PASSED,
        {
            "action_id": "action-verified",
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
                "verification_checks": [
                    passed_check("process_name_known"),
                    passed_check("process_not_alive"),
                ],
                "warnings": [],
            },
        },
    ).to_dict()

    report = audit_action_evidence([verified])

    assert report["action_event_count"] == 1
    assert report["evidence_backed_count"] == 1
    assert report["status"] == "ok"


def test_evidence_audit_classifies_current_historical_and_unknown_era_issues() -> None:
    current_missing = create_event(
        ProtocolEventType.ACTION_FAILED,
        {"action_id": "action-current-missing", "error": "current missing evidence"},
        session_id="session-current",
    ).to_dict()
    historical_failed = create_event(
        ProtocolEventType.ACTION_FAILED,
        {
            "action_id": "action-historical-negative",
            "error": "old failure with negative evidence",
            "execution_evidence": {
                "action": "create_file",
                "target": "scratch/new.txt",
                "target_type": "file",
                "method": "negative_result",
                "verifier": "executor-negative-evidence/1",
                "verification_state": "failed",
                "observed": {
                    "failure_kind": "tool_returned_error",
                    "verified_success": False,
                },
                "verification_checks": [
                    passed_check("negative_evidence_recorded"),
                    failed_check("verified_success"),
                ],
            },
        },
        session_id="session-old",
    ).to_dict()
    unknown_missing = create_event(
        ProtocolEventType.ACTION_COMPLETED,
        {"action_id": "action-unknown-missing", "success": True},
    ).to_dict()

    report = audit_action_evidence(
        [current_missing, historical_failed, unknown_missing],
        session_id="session-current",
        include_historical=True,
    )

    classes = report["classification"]["class_counts"]
    assert report["status"] == "fail"
    assert report["action_event_count"] == 3
    assert report["missing_evidence_count"] == 2
    assert report["current_missing_evidence_count"] == 1
    assert report["historical_missing_evidence_count"] == 0
    assert report["unknown_era_missing_evidence_count"] == 1
    assert report["historical_evidence_debt_count"] == 1
    assert report["unknown_era_evidence_issue_count"] == 1
    assert report["negative_evidence_count"] == 1
    assert classes["current_session_missing_evidence"] == 1
    assert classes["historical_failed_evidence"] == 1
    assert classes["unknown_era_missing_evidence"] == 1
    assert classes["negative_evidence_present"] == 1


def test_evidence_audit_classifies_historical_unverified_completed_without_verifying_it() -> None:
    commands_snapshot = {
        "records": [
            {
                "command_id": "cmd-old-unverified",
                "text": "open notepad",
                "status": "executed",
                "verification_state": "unverified",
                "trace_id": "trace-old",
                "metadata": {
                    "restored_from_journal": True,
                    "restored_source": "command_event_replay",
                    "source_snapshot_sequence": 82251,
                },
            }
        ]
    }
    before = deepcopy(commands_snapshot)

    report = audit_action_evidence(
        [],
        session_id="session-current",
        commands_snapshot=commands_snapshot,
    )

    assert commands_snapshot == before
    assert report["status"] == "warning"
    assert report["verified_action_count"] == 0
    assert report["historical_unverified_completed_count"] == 1
    assert report["current_unverified_completed_count"] == 0
    assert report["unknown_era_unverified_completed_count"] == 0
    assert report["historical_evidence_debt_count"] == 1
    command_classes = report["classification"]["command_lifecycle_classifications"][0]["classes"]
    assert "historical_unverified_completed" in command_classes


def test_evidence_audit_does_not_guess_unknown_era_unverified_completed() -> None:
    commands_snapshot = {
        "records": [
            {
                "command_id": "cmd-unknown-unverified",
                "text": "type text",
                "status": "executed",
                "verification_state": "unverified",
                "trace_id": "trace-unknown",
                "metadata": {},
            }
        ]
    }

    report = audit_action_evidence(
        [],
        session_id="session-current",
        commands_snapshot=commands_snapshot,
    )

    assert report["status"] == "warning"
    assert report["unknown_era_unverified_completed_count"] == 1
    assert report["historical_unverified_completed_count"] == 0
    assert report["current_unverified_completed_count"] == 0
    command_classification = report["classification"]["command_lifecycle_classifications"][0]
    assert command_classification["era"] == "unknown_era"
    assert "unknown_era_unverified_completed" in command_classification["classes"]


def test_full_classification_export_is_uncapped_and_stable_for_closure() -> None:
    events = [
        create_event(
            ProtocolEventType.ACTION_COMPLETED,
            {"action_id": f"unknown-missing-{index}", "success": True},
        ).to_dict()
        for index in range(25)
    ]

    report = audit_action_evidence(
        events,
        include_historical=True,
        include_full_classification_export=True,
    )

    display = report["classification"]
    export = report["full_classification_export"]
    assert display["action_classification_count"] == 25
    assert len(display["action_classifications"]) == 20
    assert display["omitted_action_classification_count"] == 5
    assert export["display_limit_applied"] is False
    assert export["action_classification_count"] == 25
    assert len(export["action_classifications"]) == 25
    assert export["omitted_action_classification_count"] == 0
    assert export["summary_counts"]["unknown_era_evidence_issue_count"] == 25
    assert export["summary_counts"]["unknown_era_missing_evidence_count"] == 25
    assert export["action_classifications"][0]["stable_classification_id"] == "action:unknown-missing-0"
    assert export["action_classifications"][-1]["stable_classification_id"] == "action:unknown-missing-24"
    assert report["mutation_performed"] is False
