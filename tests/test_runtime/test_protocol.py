from __future__ import annotations

import re
from pathlib import Path

from aegis.core.fsm import is_valid_transition
from aegis.core.protocol import (
    GENESIS_HASH,
    PROTOCOL_VERSION,
    ProtocolEventType,
    RuntimeState,
    compute_deterministic_hash,
    create_event,
    ensure_sequence_at_least,
    finalize_event,
    reset_sequence_for_testing,
    RuntimeEvent,
)


ROOT = Path(__file__).resolve().parents[2]
FRONTEND_PROTOCOL = ROOT / "frontend" / "src" / "contracts" / "protocol.ts"
FRONTEND_RUNTIME_TYPES = ROOT / "frontend" / "src" / "types" / "runtime.ts"
FRONTEND_SOCKET = ROOT / "frontend" / "src" / "lib" / "socket.ts"
FRONTEND_RUNTIME_STORE = ROOT / "frontend" / "src" / "store" / "useRuntimeStore.ts"
FRONTEND_DASHBOARD = ROOT / "frontend" / "src" / "app" / "page.tsx"
FRONTEND_RUNTIME_STATS = ROOT / "frontend" / "src" / "features" / "runtime" / "components" / "RuntimeStatsPanel.tsx"
FRONTEND_API = ROOT / "frontend" / "src" / "lib" / "api.ts"
FRONTEND_VISION = ROOT / "frontend" / "src" / "features" / "runtime" / "components" / "VisionLabPanel.tsx"
FRONTEND_CHAOS = ROOT / "frontend" / "src" / "features" / "runtime" / "components" / "ChaosShieldPanel.tsx"
FRONTEND_TIMELINE = ROOT / "frontend" / "src" / "features" / "runtime" / "components" / "ScientificTimeline.tsx"

NON_EXECUTABLE_PROTOCOL_EVENTS = {
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
    "ACTION_STARTED",
    "ACTION_COMPLETED",
    "ACTION_FAILED",
    "ACTION_RETRY",
    "VERIFICATION_PASSED",
    "VERIFICATION_FAILED",
}


def _z_enum_values(source: str, const_name: str) -> set[str]:
    match = re.search(rf"{const_name}\s*=\s*z\.enum\(\[(.*?)\]\)", source, re.DOTALL)
    assert match, f"{const_name} z.enum not found"
    return set(re.findall(r"'([^']+)'", match.group(1)))


def _runtime_enum_values(source: str, enum_name: str) -> set[str]:
    match = re.search(rf"enum\s+{enum_name}\s*\{{(.*?)\}}", source, re.DOTALL)
    assert match, f"{enum_name} enum not found"
    return set(re.findall(r"=\s*'([^']+)'", match.group(1)))


def _payload_registry_keys(source: str) -> set[str]:
    match = re.search(r"PayloadRegistry:.*?=\s*\{(.*?)\};", source, re.DOTALL)
    assert match, "PayloadRegistry not found"
    return set(re.findall(r"\b([A-Z_]+):\s*[A-Za-z]", match.group(1)))


def _frontend_schema_body(source: str, schema_name: str) -> str:
    match = re.search(rf"{schema_name}\s*=\s*z\.object\(\{{(.*?)\n\}}\)(?:\.strict\(\))?;", source, re.DOTALL)
    assert match, f"{schema_name} schema not found"
    return match.group(1)


def test_protocol_v11_envelope_hash_chain() -> None:
    first = create_event(
        ProtocolEventType.STATE_CHANGE,
        {"from": "IDLE", "to": "THINKING"},
        trace_id="11111111-1111-4111-8111-111111111111",
        runtime_phase=RuntimeState.THINKING,
    )
    finalize_event(first, GENESIS_HASH)

    second = create_event(
        ProtocolEventType.STATE_CHANGE,
        {"from": "THINKING", "to": "PLANNING"},
        trace_id="11111111-1111-4111-8111-111111111111",
        runtime_phase=RuntimeState.PLANNING,
    )
    finalize_event(second, first.event_hash or GENESIS_HASH)

    assert first.protocol_version == PROTOCOL_VERSION == "1.1.0"
    assert first.schema_version == "runtime-event/1.1"
    assert first.previous_hash == GENESIS_HASH
    assert second.previous_hash == first.event_hash
    assert first.deterministic_hash == compute_deterministic_hash(first)
    assert first.event_hash != second.event_hash


def test_fsm_transition_rules_match_runtime_contract() -> None:
    assert is_valid_transition("IDLE", "THINKING")
    assert is_valid_transition("THINKING", "PLANNING")
    assert is_valid_transition("VERIFYING", "EXECUTING")
    assert is_valid_transition("RECOVERING", "FAILED")
    assert not is_valid_transition("IDLE", "EXECUTING")
    assert not is_valid_transition("COMPLETED", "EXECUTING")


def test_sequence_counter_can_hydrate_from_journal_tail() -> None:
    ensure_sequence_at_least(1000)
    event = create_event(ProtocolEventType.SYSTEM_ONLINE, {})

    assert event.sequence_num >= 1001


def test_sequence_counter_can_reset_for_isolated_tests() -> None:
    reset_sequence_for_testing()

    event = create_event(ProtocolEventType.SYSTEM_ONLINE, {})

    assert event.sequence_num == 1


def test_deterministic_hash_excludes_sequence_and_wall_clock_fields() -> None:
    first = create_event(ProtocolEventType.COMMAND_RECEIVED, {"text": "same"})
    second = create_event(ProtocolEventType.COMMAND_RECEIVED, {"text": "same"})

    assert first.sequence_num != second.sequence_num
    assert compute_deterministic_hash(first) == compute_deterministic_hash(second)


def test_runtime_event_from_dict_does_not_consume_sequence_number() -> None:
    reset_sequence_for_testing()
    event = create_event(ProtocolEventType.SYSTEM_ONLINE, {})
    hydrated = RuntimeEvent.from_dict(event.to_dict())
    next_event = create_event(ProtocolEventType.SYSTEM_ONLINE, {})

    assert hydrated.sequence_num == event.sequence_num
    assert next_event.sequence_num == event.sequence_num + 1


def test_frontend_protocol_event_enum_matches_backend() -> None:
    frontend_source = FRONTEND_PROTOCOL.read_text(encoding="utf-8")
    runtime_types_source = FRONTEND_RUNTIME_TYPES.read_text(encoding="utf-8")
    backend_values = {event.value for event in ProtocolEventType}

    assert _z_enum_values(frontend_source, "EventTypeEnum") == backend_values
    assert _runtime_enum_values(runtime_types_source, "WebSocketEvent") == backend_values


def test_frontend_payload_registry_covers_authoritative_runtime_events() -> None:
    frontend_source = FRONTEND_PROTOCOL.read_text(encoding="utf-8")
    registry = _payload_registry_keys(frontend_source)

    required = {
        "SYSTEM_ONLINE",
        "SNAPSHOT_CREATED",
        "COMMAND_RECEIVED",
        "INTENT_PARSED",
        "PLAN_CREATED",
        "COMMAND_CLASSIFIED",
        "GUARD_EVALUATED",
        "ACTION_BLOCKED_BY_POLICY",
        "APPROVAL_REQUIRED",
        "APPROVAL_REQUESTED",
        "APPROVAL_RESOLVED",
        "APPROVAL_EXPIRED",
        "CLARIFICATION_REQUESTED",
        "CLARIFICATION_RESOLVED",
        "COMMAND_STATUS_CHANGED",
        "COMMAND_WAITING_FOR_APPROVAL",
        "COMMAND_WAITING_FOR_CLARIFICATION",
        "COMMAND_APPROVED",
        "COMMAND_REJECTED",
        "COMMAND_CANCELLED",
        "COMMAND_BLOCKED",
        "ACTION_STARTED",
        "ACTION_COMPLETED",
        "ACTION_FAILED",
        "VERIFICATION_PASSED",
        "VERIFICATION_FAILED",
        "STATE_CHANGE",
        "TELEMETRY_UPDATE",
        "TASK_FINISHED",
        "MAINTENANCE_SCAN_STARTED",
        "MAINTENANCE_SCAN_COMPLETED",
    }

    assert required.issubset(registry)


def test_non_executable_protocol_events_are_canonical_and_not_execution_lifecycle() -> None:
    backend_values = {event.value for event in ProtocolEventType}
    frontend_source = FRONTEND_PROTOCOL.read_text(encoding="utf-8")
    runtime_types_source = FRONTEND_RUNTIME_TYPES.read_text(encoding="utf-8")

    assert NON_EXECUTABLE_PROTOCOL_EVENTS.issubset(backend_values)
    assert NON_EXECUTABLE_PROTOCOL_EVENTS.issubset(_z_enum_values(frontend_source, "EventTypeEnum"))
    assert NON_EXECUTABLE_PROTOCOL_EVENTS.issubset(_runtime_enum_values(runtime_types_source, "WebSocketEvent"))
    assert NON_EXECUTABLE_PROTOCOL_EVENTS.isdisjoint(EXECUTION_LIFECYCLE_EVENTS)
    assert {
        "ACTION_STARTED",
        "ACTION_COMPLETED",
        "ACTION_FAILED",
    }.issubset(EXECUTION_LIFECYCLE_EVENTS)


def test_non_executable_payload_schemas_are_strict_and_do_not_require_execution_evidence() -> None:
    protocol_source = FRONTEND_PROTOCOL.read_text(encoding="utf-8")
    schema_names = [
        "CommandClassifiedPayload",
        "ApprovalRequestedPayload",
        "ClarificationRequestedPayload",
        "ActionBlockedByPolicyPayload",
        "CommandWaitingForApprovalPayload",
        "CommandWaitingForClarificationPayload",
        "ApprovalResolvedPayload",
        "ApprovalExpiredPayload",
        "ClarificationResolvedPayload",
    ]

    for schema_name in schema_names:
        pattern = schema_name + r"\s*=\s*z\.object\(\{(?P<body>.*?)\n\}\)\.strict\(\);"
        match = re.search(pattern, protocol_source, re.DOTALL)
        assert match, f"{schema_name} strict schema not found"
        body = match.group("body")
        assert "not_executed: z.literal(true)" in body
        assert "execution_evidence" not in body
        assert "verified:" not in body
        assert "success:" not in body
        assert "action_started:" not in body


def test_non_executable_payload_registry_uses_new_explicit_schemas() -> None:
    protocol_source = FRONTEND_PROTOCOL.read_text(encoding="utf-8")
    expected_mappings = {
        "COMMAND_CLASSIFIED": "CommandClassifiedPayload",
        "APPROVAL_REQUESTED": "ApprovalRequestedPayload",
        "CLARIFICATION_REQUESTED": "ClarificationRequestedPayload",
        "ACTION_BLOCKED_BY_POLICY": "ActionBlockedByPolicyPayload",
        "COMMAND_WAITING_FOR_APPROVAL": "CommandWaitingForApprovalPayload",
        "COMMAND_WAITING_FOR_CLARIFICATION": "CommandWaitingForClarificationPayload",
        "APPROVAL_RESOLVED": "ApprovalResolvedPayload",
        "APPROVAL_EXPIRED": "ApprovalExpiredPayload",
        "CLARIFICATION_RESOLVED": "ClarificationResolvedPayload",
    }

    for event_name, schema_name in expected_mappings.items():
        assert f"{event_name}: {schema_name}" in protocol_source


def test_frontend_non_executable_schemas_accept_backend_lifecycle_fields_without_passthrough() -> None:
    protocol_source = FRONTEND_PROTOCOL.read_text(encoding="utf-8")

    command_classified = _frontend_schema_body(protocol_source, "CommandClassifiedPayload")
    for field in [
        "guard_decision: z.record(z.string(), z.unknown()).optional()",
        "requires_approval: z.boolean().optional()",
        "requires_clarification: z.boolean().optional()",
        "blocked: z.boolean().optional()",
        "evidence_refs: z.array(z.record(z.string(), z.unknown())).default([])",
        "action_id: z.string().nullable().optional()",
    ]:
        assert field in command_classified

    approval_requested = _frontend_schema_body(protocol_source, "ApprovalRequestedPayload")
    for field in [
        "approval_request: z.record(z.string(), z.unknown()).optional()",
        "decision_status: DecisionStatusPayload.optional()",
        "policy_rule: z.string().optional()",
        "action_id: z.string().nullable().optional()",
    ]:
        assert field in approval_requested

    for schema_name, id_field in [
        ("CommandWaitingForApprovalPayload", "approval_id: z.string()"),
        ("CommandWaitingForClarificationPayload", "clarification_id: z.string()"),
    ]:
        body = _frontend_schema_body(protocol_source, schema_name)
        assert id_field in body
        for field in [
            "blocked_execution: z.literal(true).optional()",
            "executed: z.literal(false).optional()",
            "decision_status: DecisionStatusPayload.optional()",
            "risk_level: RiskLevelPayload.optional()",
            "policy_rule: z.string().optional()",
            "reason: z.string().optional()",
            "evidence_refs: z.array(z.record(z.string(), z.unknown())).default([])",
            "action_id: z.string().nullable().optional()",
        ]:
            assert field in body

    assert "CommandClassifiedPayload = z.object({" in protocol_source
    assert "}).strict();" in protocol_source
    assert ".catchall(z.unknown())" not in command_classified + approval_requested


def test_frontend_action_verification_method_details_are_nullable_without_implying_success() -> None:
    protocol_source = FRONTEND_PROTOCOL.read_text(encoding="utf-8")

    for schema_name in ["ActionCompletedPayload", "ActionFailedPayload", "VerificationPayload"]:
        body = _frontend_schema_body(protocol_source, schema_name)
        assert "passed: z.boolean()" in body
        assert "method: z.string().nullable().optional()" in body
        assert "details: z.string().nullable().optional()" in body
        assert "passed: z.literal(true)" not in body


def test_frontend_timeline_snapshot_mapping_handles_non_executed_ids_and_wording() -> None:
    protocol_source = FRONTEND_PROTOCOL.read_text(encoding="utf-8")
    runtime_types_source = FRONTEND_RUNTIME_TYPES.read_text(encoding="utf-8")
    store_source = FRONTEND_RUNTIME_STORE.read_text(encoding="utf-8")
    timeline_source = FRONTEND_TIMELINE.read_text(encoding="utf-8")

    action_timeline_body = _frontend_schema_body(protocol_source, "ActionTimelineItemPayload")
    for field in [
        "action_id: z.string().nullable().optional()",
        "timeline_id: z.string().nullable().optional()",
        "approval_id: z.string().nullable().optional()",
        "clarification_id: z.string().nullable().optional()",
        "blocked_id: z.string().nullable().optional()",
        "not_executed: z.literal(true).optional()",
        "executed: z.literal(false).optional()",
        "terminal_non_executed: z.literal(true).optional()",
    ]:
        assert field in action_timeline_body
        assert field.replace(": z.", "?: ").split("?: ")[0] in runtime_types_source

    assert "function timelineStepId" in store_source
    assert "item.action_id" in store_source
    assert "item.timeline_id" in store_source
    assert "item.approval_id" in store_source
    assert "item.clarification_id" in store_source
    assert "item.blocked_id" in store_source
    assert "Executing ${item.tool || 'executor'}" not in store_source
    assert "Approval granted; waiting for backend policy-gated resume." in store_source
    assert "Clarification resolved as state-only; command was not executed." in store_source
    assert "if (status === RuntimeStatus.ACTIVE) return `Executing ${tool}`;" in store_source
    assert "uniqueTimelineKeys(steps.slice(-20))" in timeline_source
    assert "key={key}" in timeline_source


def test_frontend_action_completed_payload_carries_execution_evidence_to_timeline() -> None:
    protocol_source = FRONTEND_PROTOCOL.read_text(encoding="utf-8")
    runtime_types_source = FRONTEND_RUNTIME_TYPES.read_text(encoding="utf-8")
    socket_source = FRONTEND_SOCKET.read_text(encoding="utf-8")
    timeline_source = FRONTEND_TIMELINE.read_text(encoding="utf-8")

    assert "ExecutionEvidencePayload" in protocol_source
    assert "execution_evidence: ExecutionEvidencePayload.optional()" in protocol_source
    assert "export interface ExecutionEvidence" in runtime_types_source
    assert "executionEvidence?: ExecutionEvidence" in runtime_types_source
    assert "retry_count: z.number().int().nonnegative().default(0)" in protocol_source
    assert "attempts: z.array(z.record(z.string(), z.unknown())).default([])" in protocol_source
    assert "fallback_chain: z.array(z.record(z.string(), z.unknown())).default([])" in protocol_source
    assert "retry_count: number" in runtime_types_source
    assert "attempts: Array<Record<string, unknown>>" in runtime_types_source
    assert "fallback_chain: Array<Record<string, unknown>>" in runtime_types_source
    assert "executionEvidence: payload.execution_evidence" in socket_source
    assert "step.executionEvidence" in timeline_source
    assert "Retries" in timeline_source
    assert "Fallback" in timeline_source
    assert "verification_checks: z.array(z.record(z.string(), z.unknown())).default([])" in protocol_source
    assert "verification_reason?: string | null" in runtime_types_source
    assert "checkLabel(check)" in timeline_source
    assert "formatObserved(check.observed)" in timeline_source


def test_frontend_action_failed_payload_carries_execution_evidence_to_timeline() -> None:
    protocol_source = FRONTEND_PROTOCOL.read_text(encoding="utf-8")
    socket_source = FRONTEND_SOCKET.read_text(encoding="utf-8")

    action_failed_match = re.search(r"ActionFailedPayload\s*=\s*z\.object\(\{(.*?)\n\}\);", protocol_source, re.DOTALL)
    assert action_failed_match, "ActionFailedPayload not found"
    assert "execution_evidence: ExecutionEvidencePayload.optional()" in action_failed_match.group(1)
    assert "executionEvidence: payload.execution_evidence" in socket_source


def test_frontend_verification_events_are_evidence_backed() -> None:
    protocol_source = FRONTEND_PROTOCOL.read_text(encoding="utf-8")
    socket_source = FRONTEND_SOCKET.read_text(encoding="utf-8")

    verification_match = re.search(r"VerificationPayload\s*=\s*z\.object\(\{(.*?)\n\}\);", protocol_source, re.DOTALL)
    assert verification_match, "VerificationPayload not found"
    assert "action_id: z.string().optional()" in verification_match.group(1)
    assert "execution_evidence: ExecutionEvidencePayload.optional()" in verification_match.group(1)
    assert "on('VERIFICATION_PASSED'" in socket_source
    assert "on('VERIFICATION_FAILED'" in socket_source
    assert "executionEvidence: payload.execution_evidence" in socket_source


def test_frontend_snapshot_truth_sync_uses_backend_snapshot_as_authority() -> None:
    protocol_source = FRONTEND_PROTOCOL.read_text(encoding="utf-8")
    socket_source = FRONTEND_SOCKET.read_text(encoding="utf-8")

    assert "source_of_truth: z.literal('backend_snapshot_protocol_event_journal')" in protocol_source
    assert "snapshot_sequence_num: z.number().int().nonnegative()" in protocol_source
    assert "journal_tail_sequence_num: z.number().int().nonnegative()" in protocol_source
    assert "missed_event_count: z.number().int().nonnegative().optional()" in protocol_source
    assert "applyRuntimeSnapshotPayload(payload, 'system online')" in socket_source
    assert "applyRuntimeSnapshotPayload(payload, 'snapshot sync')" in socket_source
    assert "applySnapshotTruthTelemetry(event, payload)" in socket_source
    assert "truthSync.snapshot_sequence_num" in socket_source
    assert "ingestOnly?: boolean" in socket_source
    assert "ingestOnly: true" in socket_source
    assert "if (!options.ingestOnly)" in socket_source
    assert "syncActionTimelineSnapshot(payload.runtime?.action_timeline)" in socket_source
    assert "Object.prototype.hasOwnProperty.call(runtime, 'maintenance_scan')" in socket_source
    assert "runtimeStore.setMaintenanceScan(runtime.maintenance_scan" in socket_source


def test_frontend_live_events_upsert_missing_timeline_steps_from_backend_payload() -> None:
    socket_source = FRONTEND_SOCKET.read_text(encoding="utf-8")
    store_source = FRONTEND_RUNTIME_STORE.read_text(encoding="utf-8")

    assert "upsertStep: (step: RuntimeStep) => void" in store_source
    assert "function upsertActionStepFromPayload" in socket_source
    assert "upsertActionStepFromPayload(event, payload, payload.success ? RuntimeStatus.SUCCESS : RuntimeStatus.ERROR)" in socket_source
    assert "upsertActionStepFromPayload(event, payload, RuntimeStatus.ERROR)" in socket_source
    assert "evidence?.action || 'executor'" in socket_source
    assert "evidence?.verification_state === 'verified'" in socket_source


def test_frontend_backend_fsm_breach_does_not_apply_illegal_projection() -> None:
    store_source = FRONTEND_RUNTIME_STORE.read_text(encoding="utf-8")

    illegal_branch = re.search(
        r"if \(!isLegalTransition\(authoritativeFrom, newState\)\) \{(?P<body>.*?)\n    \} else if",
        store_source,
        re.DOTALL,
    )
    assert illegal_branch, "applyBackendTransition illegal-transition branch not found"
    assert "return;" in illegal_branch.group("body")


def test_frontend_rejects_non_protocol_events_without_runtime_projection() -> None:
    socket_source = FRONTEND_SOCKET.read_text(encoding="utf-8")

    assert "quarantineProtocolViolation(eventName, data)" in socket_source
    assert "Dropped non-protocol socket event" in socket_source
    assert "function handleLegacyEvent" not in socket_source
    assert "runtimeStore.transitionTo" not in socket_source
    assert "runtimeStore.addStep({" not in socket_source


def test_frontend_runtime_telemetry_is_unavailable_until_backend_data_arrives() -> None:
    store_source = FRONTEND_RUNTIME_STORE.read_text(encoding="utf-8")
    dashboard_source = FRONTEND_DASHBOARD.read_text(encoding="utf-8")
    stats_source = FRONTEND_RUNTIME_STATS.read_text(encoding="utf-8")

    assert "cpuPercent: undefined" in store_source
    assert "determinismScore: undefined" in store_source
    assert "memoryPercent: undefined" in store_source
    assert "uptimeSeconds: undefined" in store_source
    assert "ioThroughput: undefined" in store_source
    assert "websocketClients: undefined" in store_source
    assert "eventThroughput: undefined" in store_source
    assert "wsRttMs: undefined" in store_source
    assert "lastSequenceNum: undefined" in store_source
    assert "memoryPercent = 0" not in dashboard_source
    assert "determinismScore === undefined ? 'Unavailable'" in dashboard_source
    assert "wsRttMs = 0" not in dashboard_source
    assert "lastSequenceNum = 0" not in dashboard_source
    assert "cpuPercent = 0" not in stats_source
    assert "memoryPercent = 0" not in stats_source
    assert "ioThroughput = '0 MB/s'" not in stats_source
    assert "determinismScore === undefined ? undefined : determinismScore * 100" in stats_source
    assert "determinismScore: 0.0" not in (ROOT / "frontend" / "src" / "features" / "runtime" / "services" / "EventSourcing.ts").read_text(encoding="utf-8")
    assert "Unavailable" in stats_source


def test_frontend_vision_feed_is_disabled_and_future_gated_by_default() -> None:
    api_source = FRONTEND_API.read_text(encoding="utf-8")
    dashboard_source = FRONTEND_DASHBOARD.read_text(encoding="utf-8")
    store_source = FRONTEND_RUNTIME_STORE.read_text(encoding="utf-8")
    vision_source = FRONTEND_VISION.read_text(encoding="utf-8")

    assert "export const API_URL" in api_source
    assert "getVisionStreamUrl" in api_source
    assert "new URL('/vision/stream', API_URL)" in api_source
    assert "http://127.0.0.1:8400/vision/stream" not in dashboard_source
    assert "http://127.0.0.1:8400/vision/stream" not in vision_source
    assert "visionFeedEnabled: false" in store_source
    assert "setVisionFeedEnabled: () => set({ visionFeedEnabled: false })" in store_source
    assert "src={visionStreamUrl}" not in dashboard_source
    assert "src={visionStreamUrl}" not in vision_source
    assert "LIVE DESKTOP FEED" not in vision_source
    assert "Vision future-gated" in dashboard_source
    assert "Vision future-gated" in vision_source


def test_frontend_raw_controls_are_disabled_not_authoritative() -> None:
    chaos_source = FRONTEND_CHAOS.read_text(encoding="utf-8")

    assert "sendCommand" not in chaos_source
    assert "/force_idle" not in chaos_source
    assert "/reset_memory" not in chaos_source
    assert "RAW CONTROLS QUARANTINED" in chaos_source
    assert "Raw frontend control commands are quarantined" in chaos_source


def test_frontend_maintenance_actions_are_backend_proposal_driven() -> None:
    socket_source = FRONTEND_SOCKET.read_text(encoding="utf-8")
    runtime_types = (ROOT / "frontend" / "src" / "types" / "runtime.ts").read_text(encoding="utf-8")
    maintenance_panel_source = (ROOT / "frontend" / "src" / "features" / "runtime" / "components" / "MaintenanceScanPanel.tsx").read_text(encoding="utf-8")
    pending_panel_source = (ROOT / "frontend" / "src" / "features" / "runtime" / "components" / "PendingApprovalPanel.tsx").read_text(encoding="utf-8")
    protocol_source = FRONTEND_PROTOCOL.read_text(encoding="utf-8")

    assert "export interface MaintenanceActionProposal" in runtime_types
    assert "pending_action_proposal_count?: number" in runtime_types
    assert "lifecycle?: {" in runtime_types
    assert "safety_gate?: Record<string, unknown>" in runtime_types
    assert "dry_run_preview?: Record<string, unknown>" in runtime_types
    assert "metadata?: Record<string, unknown>" in runtime_types
    assert "metadata: z.record(z.string(), z.unknown()).optional()" in protocol_source
    assert "function getMaintenanceActionProposals" in maintenance_panel_source
    assert "getMaintenanceProposalFromCommand(command)" in pending_panel_source
    assert "const ProposalPreviewDetails" in maintenance_panel_source
    assert "proposal.dry_run_preview" in maintenance_panel_source
    assert "dry-run preview" in maintenance_panel_source
    assert "disabled={proposal.status !== 'proposed'}" in maintenance_panel_source
    assert "requestMaintenanceAction(proposal.proposal_id)" in maintenance_panel_source
    assert "socket.emit('request_maintenance_action', { proposal_id: proposalId })" in socket_source
    assert "action_proposals" in maintenance_panel_source
    assert "maintenance_action_rescan" in (ROOT / "src" / "aegis" / "api" / "ws_bridge.py").read_text(encoding="utf-8")
    assert "maintenance_action_approval_requested" in (ROOT / "src" / "aegis" / "api" / "ws_bridge.py").read_text(encoding="utf-8")
