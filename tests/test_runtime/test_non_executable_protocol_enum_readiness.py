from __future__ import annotations

import re
from pathlib import Path

from aegis.core.non_executable_projection import project_guard_decision_to_journal_entries
from aegis.core.protocol import ProtocolEventType
from aegis.core.guard_policy import classify_intent_risk


ROOT = Path(__file__).resolve().parents[2]
FRONTEND_PROTOCOL = ROOT / "frontend" / "src" / "contracts" / "protocol.ts"
FRONTEND_RUNTIME_TYPES = ROOT / "frontend" / "src" / "types" / "runtime.ts"
READINESS_REPORT = ROOT / "docs" / "audit" / "non-executable-protocol-enum-readiness.md"

PROPOSED_NON_EXECUTABLE_EVENTS = {
    "COMMAND_CLASSIFIED",
    "APPROVAL_REQUESTED",
    "CLARIFICATION_REQUESTED",
    "ACTION_BLOCKED_BY_POLICY",
    "COMMAND_WAITING_FOR_APPROVAL",
    "COMMAND_WAITING_FOR_CLARIFICATION",
    "COMMAND_BLOCKED",
    "APPROVAL_RESOLVED",
    "APPROVAL_EXPIRED",
    "CLARIFICATION_RESOLVED",
}

EXECUTION_LIFECYCLE_EVENTS = {
    ProtocolEventType.ACTION_STARTED.value,
    ProtocolEventType.ACTION_COMPLETED.value,
    ProtocolEventType.ACTION_FAILED.value,
    ProtocolEventType.ACTION_RETRY.value,
    ProtocolEventType.VERIFICATION_PASSED.value,
    ProtocolEventType.VERIFICATION_FAILED.value,
}


def _z_enum_values(source: str, const_name: str) -> set[str]:
    match = re.search(rf"{const_name}\s*=\s*z\.enum\(\[(.*?)\]\)", source, re.DOTALL)
    assert match, f"{const_name} z.enum not found"
    return set(re.findall(r"'([^']+)'", match.group(1)))


def _runtime_enum_values(source: str, enum_name: str) -> set[str]:
    match = re.search(rf"enum\s+{enum_name}\s*\{{(.*?)\}}", source, re.DOTALL)
    assert match, f"{enum_name} enum not found"
    return set(re.findall(r"=\s*'([^']+)'", match.group(1)))


def test_non_executable_protocol_enum_addition_is_synchronized_with_frontend_mirrors() -> None:
    backend_values = {event.value for event in ProtocolEventType}
    frontend_protocol_values = _z_enum_values(FRONTEND_PROTOCOL.read_text(encoding="utf-8"), "EventTypeEnum")
    frontend_runtime_values = _runtime_enum_values(FRONTEND_RUNTIME_TYPES.read_text(encoding="utf-8"), "WebSocketEvent")

    assert frontend_protocol_values == backend_values
    assert frontend_runtime_values == backend_values
    assert PROPOSED_NON_EXECUTABLE_EVENTS.issubset(backend_values)
    assert PROPOSED_NON_EXECUTABLE_EVENTS.issubset(frontend_protocol_values)
    assert PROPOSED_NON_EXECUTABLE_EVENTS.issubset(frontend_runtime_values)


def test_projection_event_names_are_now_canonical_protocol_values() -> None:
    approval = classify_intent_risk(
        "write_file",
        {"path": "scratch/a.txt", "content": "hello"},
        {"command_id": "cmd-protocol-readiness", "trace_id": "trace-protocol-readiness"},
    )
    entries = project_guard_decision_to_journal_entries(approval)
    projected_event_names = {entry["event_type"] for entry in entries}
    backend_values = {event.value for event in ProtocolEventType}

    assert projected_event_names == {
        "COMMAND_CLASSIFIED",
        "APPROVAL_REQUESTED",
        "COMMAND_WAITING_FOR_APPROVAL",
    }
    assert projected_event_names <= PROPOSED_NON_EXECUTABLE_EVENTS
    assert projected_event_names.isdisjoint(EXECUTION_LIFECYCLE_EVENTS)
    assert projected_event_names.issubset(backend_values)


def test_existing_command_blocked_and_policy_block_events_are_canonical_non_execution_events() -> None:
    backend_values = {event.value for event in ProtocolEventType}

    assert "COMMAND_BLOCKED" in backend_values
    assert "ACTION_BLOCKED_BY_POLICY" in backend_values
    assert ProtocolEventType.COMMAND_BLOCKED.value not in EXECUTION_LIFECYCLE_EVENTS
    assert ProtocolEventType.ACTION_BLOCKED_BY_POLICY.value not in EXECUTION_LIFECYCLE_EVENTS


def test_execution_lifecycle_classification_stays_separate_from_non_executable_projection_names() -> None:
    backend_values = {event.value for event in ProtocolEventType}

    assert {
        "ACTION_STARTED",
        "ACTION_COMPLETED",
        "ACTION_FAILED",
    }.issubset(EXECUTION_LIFECYCLE_EVENTS)
    assert PROPOSED_NON_EXECUTABLE_EVENTS.isdisjoint(EXECUTION_LIFECYCLE_EVENTS)
    assert EXECUTION_LIFECYCLE_EVENTS.issubset(backend_values)


def test_readiness_report_documents_prior_deferral_and_protocol_migration_path() -> None:
    report = READINESS_REPORT.read_text(encoding="utf-8")

    assert "enum_values_added: no" in report
    assert "backend ProtocolEventType must exactly mirror frontend EventTypeEnum" in report
    assert "frontend protocol mirror" in report
    assert "PayloadRegistry" in report
    assert "ACTION_BLOCKED_BY_POLICY" in report
    assert "APPROVAL_REQUESTED" in report
    assert "CLARIFICATION_REQUESTED" in report
