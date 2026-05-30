from __future__ import annotations

from collections import Counter
from typing import Any, Iterable, Mapping

from aegis.core.action_timeline import project_action_timeline
from aegis.core.constants import CommandStatus
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

EVIDENCE_CLASSIFICATION_VERSION = "evidence-classification/1"
NEGATIVE_EVIDENCE_VERIFIER = "executor-negative-evidence/1"
UNKNOWN_ERA = "unknown_era"
CURRENT_ERA = "current_session"
HISTORICAL_ERA = "historical"


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
    include_historical: bool = False,
    commands_snapshot: Mapping[str, Any] | None = None,
    replay_diagnostics: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Read-only evidence quality report derived from action lifecycle and verification events."""
    all_action_events = [
        event
        for event in events
        if str(event.get("type") or "") in ACTION_EVENT_TYPES
    ]
    action_events = [
        event
        for event in all_action_events
        if include_historical or not session_id or event.get("session_id") == session_id
    ]
    timeline = project_action_timeline(
        action_events,
        limit=limit,
        session_id=None if include_historical else session_id,
    )
    action_event_index = _action_event_index(action_events)
    replay_context = _replay_context(replay_diagnostics)

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
    negative_evidence_count = 0
    verifier_counts: Counter[str] = Counter()
    critical_failures: list[dict[str, Any]] = []
    action_classifications: list[dict[str, Any]] = []

    era_issue_counts: Counter[str] = Counter()
    missing_by_era: Counter[str] = Counter()
    verified_by_era: Counter[str] = Counter()
    failed_by_era: Counter[str] = Counter()
    unverified_by_era: Counter[str] = Counter()
    class_counts: Counter[str] = Counter()

    for item in timeline:
        evidence = item.get("execution_evidence")
        status = str(item.get("status") or "")
        era, era_reason = _action_era(
            item,
            action_event_index=action_event_index,
            current_session_id=session_id,
            replay_context=replay_context,
        )
        action_critical_failures: list[dict[str, Any]] = []
        classes: list[str] = []
        issue_present = False
        verification_state = "missing"
        negative_evidence = False

        if isinstance(evidence, Mapping):
            evidence_backed_count += 1
            verification_state = str(evidence.get("verification_state") or "unverified")
            verification_counts[verification_state] += 1
            if verification_state == "verified":
                verified_action_count += 1
                verified_by_era[era] += 1
                classes.append(f"{era}_verified")
            elif verification_state == "failed":
                failed_evidence_count += 1
                failed_by_era[era] += 1
                classes.append(f"{era}_failed_evidence")
                issue_present = True
            else:
                unverified_evidence_count += 1
                unverified_by_era[era] += 1
                classes.append(f"{era}_unverified_evidence")
                issue_present = True

            verifier = str(evidence.get("verifier") or evidence.get("method") or "unknown")
            verifier_counts[verifier] += 1
            negative_evidence = _is_negative_evidence(evidence)
            if negative_evidence:
                negative_evidence_count += 1
                classes.append("negative_evidence_present")

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

            action_critical_failures = critical_check_failures(
                str(evidence.get("action") or item.get("tool") or ""),
                evidence,
                action_id=str(item.get("action_id") or ""),
                target=str(item.get("target") or evidence.get("target") or ""),
            )
            if action_critical_failures:
                classes.append("verifier_check_failed")
                issue_present = True
        elif status in {"success", "error"}:
            missing_evidence_count += 1
            missing_by_era[era] += 1
            verification_counts["missing"] += 1
            classes.extend([f"{era}_missing_evidence", "evidence_missing_but_expected"])
            issue_present = True

        if era == UNKNOWN_ERA and replay_context["replay_attention"]:
            classes.append("replay_era_unknown")
        if issue_present:
            era_issue_counts[era] += 1

        for failure in action_critical_failures:
            critical_failures.append({
                **failure,
                "era": era,
                "era_reason": era_reason,
                "classes": sorted(set(classes)),
            })

        for class_name in classes:
            class_counts[class_name] += 1

        action_classifications.append({
            "action_id": str(item.get("action_id") or ""),
            "action": str((evidence or {}).get("action") or item.get("tool") or ""),
            "target": item.get("target") or (evidence or {}).get("target") if isinstance(evidence, Mapping) else item.get("target"),
            "status": status,
            "verification_state": verification_state,
            "evidence_backed": isinstance(evidence, Mapping),
            "negative_evidence_present": negative_evidence,
            "era": era,
            "era_reason": era_reason,
            "classes": sorted(set(classes)),
        })

    command_lifecycle_classifications = _classify_unverified_completed_commands(
        commands_snapshot,
        current_session_id=session_id,
        replay_context=replay_context,
    )
    command_unverified_by_era = Counter(
        item["era"] for item in command_lifecycle_classifications
    )
    for item in command_lifecycle_classifications:
        for class_name in item["classes"]:
            class_counts[class_name] += 1
        if item["era"] in {HISTORICAL_ERA, UNKNOWN_ERA}:
            era_issue_counts[item["era"]] += 1
        elif item["era"] == CURRENT_ERA:
            era_issue_counts[CURRENT_ERA] += 1

    latest_sequence = max(
        (int(item.get("sequence_num") or 0) for item in timeline),
        default=0,
    )
    completed_or_failed = status_counts.get("success", 0) + status_counts.get("error", 0)
    if critical_failures or failed_evidence_count:
        status = "fail"
    elif missing_evidence_count or unverified_evidence_count or check_unknown_count or command_lifecycle_classifications:
        status = "warning"
    else:
        status = "ok"

    current_missing = missing_by_era[CURRENT_ERA]
    historical_missing = missing_by_era[HISTORICAL_ERA]
    unknown_missing = missing_by_era[UNKNOWN_ERA]
    current_unverified_completed = command_unverified_by_era[CURRENT_ERA]
    historical_unverified_completed = command_unverified_by_era[HISTORICAL_ERA]
    unknown_unverified_completed = command_unverified_by_era[UNKNOWN_ERA]

    classification = {
        "scan_version": EVIDENCE_CLASSIFICATION_VERSION,
        "read_only": True,
        "mutation_performed": False,
        "scope": "all_recent_action_events" if include_historical else "scoped_action_events",
        "current_session_id": session_id,
        "current_evidence_failure_count": era_issue_counts[CURRENT_ERA],
        "historical_evidence_debt_count": era_issue_counts[HISTORICAL_ERA],
        "unknown_era_evidence_issue_count": era_issue_counts[UNKNOWN_ERA],
        "current_missing_evidence_count": current_missing,
        "historical_missing_evidence_count": historical_missing,
        "unknown_era_missing_evidence_count": unknown_missing,
        "current_unverified_completed_count": current_unverified_completed,
        "historical_unverified_completed_count": historical_unverified_completed,
        "unknown_era_unverified_completed_count": unknown_unverified_completed,
        "failed_evidence_count": failed_evidence_count,
        "negative_evidence_count": negative_evidence_count,
        "verifier_check_failure_count": check_fail_count,
        "class_counts": dict(sorted(class_counts.items())),
        "era_counts": dict(sorted(Counter(item["era"] for item in action_classifications).items())),
        "replay_context": replay_context,
        "recommendation": _classification_recommendation(
            current_failures=era_issue_counts[CURRENT_ERA],
            historical_debt=era_issue_counts[HISTORICAL_ERA],
            unknown_issues=era_issue_counts[UNKNOWN_ERA],
        ),
        "guidance": [
            "No verification was fabricated by this audit.",
            "No evidence, journal, command lifecycle, approval, or runtime state was mutated.",
            "Current evidence failures require investigation before claiming runtime health.",
            "Historical evidence debt remains visible and requires a separate hygiene/classification flow.",
            "Unknown-era evidence issues remain non-success until source or session evidence is available.",
        ],
        "action_classifications": action_classifications[:20],
        "command_lifecycle_classifications": command_lifecycle_classifications[:20],
        "omitted_action_classification_count": max(0, len(action_classifications) - 20),
        "omitted_command_lifecycle_classification_count": max(0, len(command_lifecycle_classifications) - 20),
    }

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
        "negative_evidence_count": negative_evidence_count,
        "check_pass_count": check_pass_count,
        "check_fail_count": check_fail_count,
        "check_unknown_count": check_unknown_count,
        "critical_failure_count": len(critical_failures),
        "critical_failures": critical_failures[:20],
        "verification_counts": dict(sorted(verification_counts.items())),
        "verifier_counts": dict(sorted(verifier_counts.items())),
        "latest_sequence_num": latest_sequence,
        "limit": max(int(limit), 0),
        "include_historical": include_historical,
        "current_evidence_failure_count": classification["current_evidence_failure_count"],
        "historical_evidence_debt_count": classification["historical_evidence_debt_count"],
        "unknown_era_evidence_issue_count": classification["unknown_era_evidence_issue_count"],
        "current_missing_evidence_count": current_missing,
        "historical_missing_evidence_count": historical_missing,
        "unknown_era_missing_evidence_count": unknown_missing,
        "current_unverified_completed_count": current_unverified_completed,
        "historical_unverified_completed_count": historical_unverified_completed,
        "unknown_era_unverified_completed_count": unknown_unverified_completed,
        "verifier_check_failure_count": check_fail_count,
        "mutation_performed": False,
        "classification": classification,
    }


def _action_event_index(events: Iterable[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for event in events:
        payload = event.get("payload")
        if not isinstance(payload, Mapping):
            continue
        action_id = payload.get("action_id")
        if not action_id:
            continue
        key = str(action_id)
        item = index.setdefault(key, {"session_ids": set(), "sequence_nums": [], "timestamps": []})
        session_id = event.get("session_id")
        if session_id:
            item["session_ids"].add(str(session_id))
        if event.get("sequence_num") is not None:
            item["sequence_nums"].append(event.get("sequence_num"))
        if event.get("timestamp") is not None:
            item["timestamps"].append(event.get("timestamp"))
    return index


def _action_era(
    item: Mapping[str, Any],
    *,
    action_event_index: Mapping[str, Mapping[str, Any]],
    current_session_id: str | None,
    replay_context: Mapping[str, Any],
) -> tuple[str, str]:
    action_id = str(item.get("action_id") or "")
    indexed = action_event_index.get(action_id, {})
    session_ids = indexed.get("session_ids")
    sessions = {str(value) for value in session_ids} if isinstance(session_ids, set) else set()
    if current_session_id and sessions == {current_session_id}:
        return CURRENT_ERA, "action events match current session id"
    if current_session_id and sessions and current_session_id not in sessions:
        return HISTORICAL_ERA, "action events belong to a different session id"
    if current_session_id and len(sessions) > 1:
        return UNKNOWN_ERA, "action id spans multiple session ids"
    if not current_session_id:
        return UNKNOWN_ERA, "current session id unavailable"
    if replay_context.get("replay_attention"):
        return UNKNOWN_ERA, "session evidence unavailable with replay diagnostics attention"
    return UNKNOWN_ERA, "session evidence unavailable"


def _classify_unverified_completed_commands(
    commands_snapshot: Mapping[str, Any] | None,
    *,
    current_session_id: str | None,
    replay_context: Mapping[str, Any],
) -> list[dict[str, Any]]:
    if not isinstance(commands_snapshot, Mapping):
        return []
    records = _list_of_dicts(commands_snapshot.get("records"))
    classifications: list[dict[str, Any]] = []
    for record in records:
        status = str(record.get("status") or "")
        verification_state = str(record.get("verification_state") or "unverified")
        if status != CommandStatus.EXECUTED.value or verification_state == "verified":
            continue
        era, reason = _command_record_era(
            record,
            current_session_id=current_session_id,
            replay_context=replay_context,
        )
        classes = [f"{era}_unverified_completed"]
        if era == HISTORICAL_ERA:
            classes.append("historical_unverified_completed")
        elif era == UNKNOWN_ERA:
            classes.append("unknown_era_unverified_completed")
            if replay_context.get("replay_attention"):
                classes.append("replay_era_unknown")
        else:
            classes.append("current_session_unverified_completed")
        classifications.append({
            "command_id": _string_or_none(record.get("command_id")),
            "trace_id": _string_or_none(record.get("trace_id")),
            "text": str(record.get("text") or ""),
            "status": status,
            "verification_state": verification_state,
            "era": era,
            "era_reason": reason,
            "created_at": _int_or_none(record.get("created_at")),
            "updated_at": _int_or_none(record.get("updated_at")),
            "classes": sorted(set(classes)),
        })
    return classifications


def _command_record_era(
    record: Mapping[str, Any],
    *,
    current_session_id: str | None,
    replay_context: Mapping[str, Any],
) -> tuple[str, str]:
    metadata = record.get("metadata") if isinstance(record.get("metadata"), Mapping) else {}
    if (
        metadata.get("restored_from_journal") is True
        or metadata.get("restored_source")
        or metadata.get("source_snapshot_sequence") is not None
    ):
        return HISTORICAL_ERA, "command lifecycle record carries restored journal metadata"
    record_session = _string_or_none(record.get("session_id")) or _string_or_none(metadata.get("session_id"))
    if current_session_id and record_session == current_session_id:
        return CURRENT_ERA, "command lifecycle record matches current session id"
    if current_session_id and record_session and record_session != current_session_id:
        return HISTORICAL_ERA, "command lifecycle record belongs to a different session id"
    if not current_session_id:
        return UNKNOWN_ERA, "current session id unavailable"
    if replay_context.get("replay_attention"):
        return UNKNOWN_ERA, "command session evidence unavailable with replay diagnostics attention"
    return UNKNOWN_ERA, "command session evidence unavailable"


def _is_negative_evidence(evidence: Mapping[str, Any]) -> bool:
    observed = evidence.get("observed") if isinstance(evidence.get("observed"), Mapping) else {}
    return bool(
        evidence.get("verifier") == NEGATIVE_EVIDENCE_VERIFIER
        or evidence.get("method") == "negative_result"
        or observed.get("verified_success") is False
        or observed.get("failure_kind")
    )


def _replay_context(replay_diagnostics: Mapping[str, Any] | None) -> dict[str, Any]:
    replay = replay_diagnostics if isinstance(replay_diagnostics, Mapping) else {}
    boundary = replay.get("replay_boundary") if isinstance(replay.get("replay_boundary"), Mapping) else {}
    sequence = replay.get("sequence") if isinstance(replay.get("sequence"), Mapping) else {}
    status = str(replay.get("status") or "unknown")
    classification = str(boundary.get("classification") or "unknown")
    return {
        "status": status,
        "classification": classification,
        "replay_attention": status not in {"ok", "unknown"},
        "mixed_sequence_eras_suspected": bool(sequence.get("mixed_sequence_eras_suspected")),
        "cleanup_execution_blocked": bool(boundary.get("cleanup_execution_blocked")),
    }


def _classification_recommendation(
    *,
    current_failures: int,
    historical_debt: int,
    unknown_issues: int,
) -> str:
    parts: list[str] = []
    if current_failures:
        parts.append("Current evidence failures require investigation before claiming runtime health.")
    if historical_debt:
        parts.append("Historical evidence debt requires a separate hygiene/classification flow.")
    if unknown_issues:
        parts.append("Unknown-era evidence issues remain visible and non-success until source evidence is available.")
    if not parts:
        parts.append("No current, historical, or unknown evidence issues were classified in the audited scope.")
    parts.append("No verification was fabricated and no mutation was performed.")
    return " ".join(parts)


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _string_or_none(value: Any) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
