from __future__ import annotations

from collections import Counter
from typing import Any, Iterable, Mapping

from aegis.core.action_timeline import project_action_timeline
from aegis.core.protocol import ProtocolEventType


ACTION_EVENT_TYPES = {
    ProtocolEventType.ACTION_STARTED.value,
    ProtocolEventType.ACTION_COMPLETED.value,
    ProtocolEventType.ACTION_FAILED.value,
    ProtocolEventType.VERIFICATION_PASSED.value,
    ProtocolEventType.VERIFICATION_FAILED.value,
}

CRITICAL_CHECKS_BY_ACTION = {
    "open_app": {
        "process_name_known",
        "single_matching_window",
        "process_alive",
        "window_manifested",
        "window_pid_matches_target_process",
    },
    "focus_app": {
        "process_name_known",
        "single_matching_window",
        "foreground_hwnd_present",
        "foreground_title_matches_target",
        "foreground_pid_matches_target_process",
        "foreground_window_matches_target",
    },
    "close_app": {
        "process_name_known",
        "process_not_alive",
    },
}


def evidence_check_name(check: Mapping[str, Any]) -> str:
    return str(check.get("check_name") or check.get("name") or "")


def evidence_check_reason(check: Mapping[str, Any]) -> str:
    return str(check.get("reason") or check.get("detail") or "")


def critical_check_failures(
    action: str,
    evidence: Mapping[str, Any] | None,
    *,
    action_id: str | None = None,
    target: str | None = None,
) -> list[dict[str, Any]]:
    """Return required desktop verification checks that are absent, failed, or unknown."""
    required = CRITICAL_CHECKS_BY_ACTION.get(action)
    if not required or not isinstance(evidence, Mapping):
        return []

    raw_checks = evidence.get("verification_checks")
    checks = raw_checks if isinstance(raw_checks, list) else []
    by_name = {
        evidence_check_name(check): check
        for check in checks
        if isinstance(check, Mapping) and evidence_check_name(check)
    }
    failures: list[dict[str, Any]] = []
    for check_name in sorted(required):
        check = by_name.get(check_name)
        passed = check.get("passed") if isinstance(check, Mapping) else None
        if passed is True:
            continue
        failures.append({
            "action_id": action_id,
            "action": action,
            "target": target or evidence.get("target"),
            "check_name": check_name,
            "passed": passed,
            "expected": check.get("expected") if isinstance(check, Mapping) else "present and passed",
            "observed": check.get("observed") if isinstance(check, Mapping) else None,
            "reason": evidence_check_reason(check) if isinstance(check, Mapping) else "required verification check missing",
        })
    return failures


def audit_action_evidence(
    events: Iterable[Mapping[str, Any]],
    *,
    limit: int = 50,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Read-only evidence quality report derived from action lifecycle and verification events."""
    action_events = [
        event
        for event in events
        if str(event.get("type") or "") in ACTION_EVENT_TYPES
        and (not session_id or event.get("session_id") == session_id)
    ]
    timeline = project_action_timeline(action_events, limit=limit, session_id=session_id)

    status_counts = Counter(str(item.get("status") or "unknown") for item in timeline)
    verification_counts: Counter[str] = Counter()
    missing_evidence_count = 0
    evidence_backed_count = 0
    verified_action_count = 0
    unverified_evidence_count = 0
    failed_evidence_count = 0
    check_pass_count = 0
    check_fail_count = 0
    check_unknown_count = 0
    verifier_counts: Counter[str] = Counter()
    critical_failures: list[dict[str, Any]] = []

    for item in timeline:
        evidence = item.get("execution_evidence")
        status = str(item.get("status") or "")
        if isinstance(evidence, Mapping):
            evidence_backed_count += 1
            verification_state = str(evidence.get("verification_state") or "unverified")
            verification_counts[verification_state] += 1
            if verification_state == "verified":
                verified_action_count += 1
            elif verification_state == "failed":
                failed_evidence_count += 1
            else:
                unverified_evidence_count += 1

            verifier = str(evidence.get("verifier") or evidence.get("method") or "unknown")
            verifier_counts[verifier] += 1

            raw_checks = evidence.get("verification_checks")
            checks = raw_checks if isinstance(raw_checks, list) else []
            for check in checks:
                if not isinstance(check, Mapping):
                    continue
                passed = check.get("passed")
                if passed is True:
                    check_pass_count += 1
                elif passed is False:
                    check_fail_count += 1
                else:
                    check_unknown_count += 1

            critical_failures.extend(critical_check_failures(
                str(evidence.get("action") or item.get("tool") or ""),
                evidence,
                action_id=str(item.get("action_id") or ""),
                target=str(item.get("target") or evidence.get("target") or ""),
            ))
        elif status in {"success", "error"}:
            missing_evidence_count += 1
            verification_counts["missing"] += 1

    latest_sequence = max(
        (int(item.get("sequence_num") or 0) for item in timeline),
        default=0,
    )
    completed_or_failed = status_counts.get("success", 0) + status_counts.get("error", 0)
    if critical_failures or failed_evidence_count:
        status = "fail"
    elif missing_evidence_count or unverified_evidence_count or check_unknown_count:
        status = "warning"
    else:
        status = "ok"

    return {
        "scan_version": "evidence-audit/2",
        "read_only": True,
        "status": status,
        "action_event_count": len(action_events),
        "action_count": len(timeline),
        "completed_or_failed_count": completed_or_failed,
        "active_count": status_counts.get("active", 0),
        "success_count": status_counts.get("success", 0),
        "error_count": status_counts.get("error", 0),
        "evidence_backed_count": evidence_backed_count,
        "missing_evidence_count": missing_evidence_count,
        "verified_action_count": verified_action_count,
        "unverified_evidence_count": unverified_evidence_count,
        "failed_evidence_count": failed_evidence_count,
        "check_pass_count": check_pass_count,
        "check_fail_count": check_fail_count,
        "check_unknown_count": check_unknown_count,
        "critical_failure_count": len(critical_failures),
        "critical_failures": critical_failures[:20],
        "verification_counts": dict(sorted(verification_counts.items())),
        "verifier_counts": dict(sorted(verifier_counts.items())),
        "latest_sequence_num": latest_sequence,
        "limit": max(int(limit), 0),
    }
