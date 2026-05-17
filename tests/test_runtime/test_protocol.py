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
FRONTEND_TIMELINE = ROOT / "frontend" / "src" / "features" / "runtime" / "components" / "ScientificTimeline.tsx"


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
        "GUARD_EVALUATED",
        "APPROVAL_REQUIRED",
        "COMMAND_STATUS_CHANGED",
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


def test_frontend_vision_stream_uses_configured_backend_url() -> None:
    api_source = FRONTEND_API.read_text(encoding="utf-8")
    dashboard_source = FRONTEND_DASHBOARD.read_text(encoding="utf-8")
    vision_source = FRONTEND_VISION.read_text(encoding="utf-8")

    assert "export const API_URL" in api_source
    assert "getVisionStreamUrl" in api_source
    assert "new URL('/vision/stream', API_URL)" in api_source
    assert "http://127.0.0.1:8400/vision/stream" not in dashboard_source
    assert "http://127.0.0.1:8400/vision/stream" not in vision_source
    assert "src={visionStreamUrl}" in dashboard_source
    assert "src={visionStreamUrl}" in vision_source
