/**
 * ══════════════════════════════════════════════════════════════════════
 * AEGIS RUNTIME PROTOCOL v1.0
 * ══════════════════════════════════════════════════════════════════════
 *
 * The Single Source of Truth for all communication between:
 *   - Python Backend (FastAPI + WebSocket)
 *   - Frontend Runtime (Next.js + Zustand)
 *   - Persistence Layer (IndexedDB)
 *   - Replay Engine
 *
 * RULES:
 *   1. Every event crossing the WebSocket boundary MUST validate
 *      against these schemas.
 *   2. The backend MUST emit events using the exact same enum values.
 *   3. No `any` types in production event handlers.
 *   4. Protocol version is checked on handshake. Mismatch = hard reject.
 *
 * ══════════════════════════════════════════════════════════════════════
 */

import { z } from 'zod';

// ─── PROTOCOL VERSION ──────────────────────────────────────────────
export const PROTOCOL_VERSION = '1.1.0';

// ─── FSM STATES (Canonical — must mirror backend) ──────────────────
export const RuntimeStateEnum = z.enum([
  'IDLE',
  'THINKING',
  'PLANNING',
  'EXECUTING',
  'VERIFYING',
  'RECOVERING',
  'FAILED',
  'COMPLETED',
]);
export type RuntimeStateValue = z.infer<typeof RuntimeStateEnum>;

// ─── EVENT TYPES (Exhaustive — must mirror backend EventType) ──────
export const EventTypeEnum = z.enum([
  // Lifecycle
  'SYSTEM_ONLINE',
  'SYSTEM_OFFLINE',
  'SESSION_START',
  'SESSION_END',

  // Command Pipeline
  'COMMAND_RECEIVED',
  'INTENT_PARSED',
  'PLAN_CREATED',

  // Action Lifecycle
  'ACTION_STARTED',
  'ACTION_COMPLETED',
  'ACTION_FAILED',
  'ACTION_RETRY',

  // Guard
  'GUARD_EVALUATED',

  // Command Governance
  'COMMAND_STATUS_CHANGED',
  'APPROVAL_REQUIRED',
  'COMMAND_APPROVED',
  'COMMAND_REJECTED',
  'COMMAND_CANCELLED',
  'COMMAND_BLOCKED',

  // Verification
  'VERIFICATION_PASSED',
  'VERIFICATION_FAILED',

  // Recovery
  'RECOVERY_TRIGGERED',
  'RECOVERY_COMPLETED',
  'RECOVERY_EXHAUSTED',

  // Focus & Determinism
  'FOCUS_ACQUIRED',
  'FOCUS_LOST',
  'DETERMINISM_BREACH',

  // Token Streaming
  'TOKEN_START',
  'TOKEN_CHUNK',
  'TOKEN_END',
  'TOKEN_ABORT',
  'TOKEN_ERROR',

  // Telemetry
  'TELEMETRY_UPDATE',
  'VRAM_UPDATE',
  'MODEL_SWITCH',

  // Task
  'TASK_FINISHED',

  // Maintenance
  'MAINTENANCE_SCAN_STARTED',
  'MAINTENANCE_SCAN_COMPLETED',

  // Vision
  'VISION_ESCALATION',
  'VISION_RESULT',

  // Internal
  'STATE_CHANGE',
  'SNAPSHOT_CREATED',
]);
export type EventTypeValue = z.infer<typeof EventTypeEnum>;

// ─── SEVERITY ──────────────────────────────────────────────────────
export const SeverityEnum = z.enum(['debug', 'info', 'warning', 'error', 'critical']);

// ─── COMPONENT SOURCE ──────────────────────────────────────────────
export const ComponentEnum = z.enum([
  'planner',
  'executor',
  'validator',
  'recovery',
  'guard',
  'intent_parser',
  'model_router',
  'memory',
  'orchestrator',
  'system',
]);

// ═══════════════════════════════════════════════════════════════════
// EVENT SCHEMAS — Typed payloads for every event type
// ═══════════════════════════════════════════════════════════════════

/** Base envelope for ALL events crossing the wire */
export const RuntimeEventSchema = z.object({
  event_id: z.string().uuid(),
  type: EventTypeEnum,
  timestamp: z.number(),                 // Unix ms
  trace_id: z.string().uuid().optional(), // Groups events in a command lifecycle
  causation_id: z.string().uuid().optional(), // ID of the event that caused this one
  span_id: z.string().uuid().optional(),  // Execution span within a trace
  session_id: z.string().optional(),
  source: ComponentEnum.optional(),
  severity: SeverityEnum.default('info'),
  sequence_num: z.number().int().nonnegative().optional(), // Monotonic ordering
  runtime_phase: RuntimeStateEnum.optional(),
  protocol_version: z.string().default(PROTOCOL_VERSION),
  schema_version: z.string().optional(),
  deterministic_hash: z.string().optional(),
  previous_hash: z.string().optional(),
  event_hash: z.string().optional(),
  payload: z.record(z.string(), z.unknown()).default({}),
  state: RuntimeStateEnum.optional(),
  previousHash: z.string().optional(),
  eventHash: z.string().optional(),
});
export type RuntimeEvent = z.infer<typeof RuntimeEventSchema>;

// ─── ACTION LIFECYCLE ──────────────────────────────────────────────
export const ActionStartedPayload = z.object({
  action_id: z.string(),
  tool: z.string(),
  intent: z.string().optional(),
  target: z.string().optional(),
  params: z.record(z.string(), z.unknown()).optional(),
  risk_level: z.enum(['none', 'low', 'medium', 'high', 'critical']).default('none'),
  is_dry_run: z.boolean().default(false),
});

export const ExecutionEvidencePayload = z.object({
  action: z.string(),
  target: z.string().nullable().optional(),
  target_type: z.string().default('unknown'),
  method: z.string().default('unknown'),
  verifier: z.string().nullable().optional(),
  verification_state: z.string().default('unverified'),
  verification_reason: z.string().nullable().optional(),
  started_at_ms: z.number().optional(),
  completed_at_ms: z.number().optional(),
  launch_target: z.string().nullable().optional(),
  resolved_path: z.string().nullable().optional(),
  process_name: z.string().nullable().optional(),
  pids: z.array(z.number()).default([]),
  process_alive: z.boolean().nullable().optional(),
  window: z.record(z.string(), z.unknown()).nullable().optional(),
  expected: z.record(z.string(), z.unknown()).default({}),
  observed: z.record(z.string(), z.unknown()).default({}),
  verification_checks: z.array(z.record(z.string(), z.unknown())).default([]),
  matching_windows: z.array(z.record(z.string(), z.unknown())).default([]),
  retry_count: z.number().int().nonnegative().default(0),
  recovery_triggered: z.boolean().default(false),
  attempts: z.array(z.record(z.string(), z.unknown())).default([]),
  fallback_chain: z.array(z.record(z.string(), z.unknown())).default([]),
  warnings: z.array(z.string()).default([]),
});

export const ActionCompletedPayload = z.object({
  action_id: z.string(),
  success: z.boolean(),
  result: z.unknown().optional(),
  latency_ms: z.number(),
  retries: z.number().default(0),
  verification: z.object({
    passed: z.boolean(),
    method: z.string().optional(),
    details: z.string().optional(),
  }).optional(),
  execution_evidence: ExecutionEvidencePayload.optional(),
});

export const ActionFailedPayload = z.object({
  action_id: z.string(),
  error: z.string(),
  error_type: z.string().optional(),
  is_recoverable: z.boolean().default(true),
  retry_count: z.number().default(0),
  max_retries: z.number().default(3),
  verification: z.object({
    passed: z.boolean(),
    method: z.string().optional(),
    details: z.string().optional(),
  }).optional(),
  execution_evidence: ExecutionEvidencePayload.optional(),
});

export const ActionTimelineItemPayload = z.object({
  action_id: z.string(),
  tool: z.string(),
  status: z.enum(['pending', 'active', 'success', 'error']),
  target: z.string().nullable().optional(),
  started_at: z.number().nullable().optional(),
  completed_at: z.number().nullable().optional(),
  latency_ms: z.number().nullable().optional(),
  execution_evidence: ExecutionEvidencePayload.nullable().optional(),
  trace_id: z.string().nullable().optional(),
  sequence_num: z.number().int().nonnegative().nullable().optional(),
});

export const ToolSpecPayload = z.object({
  name: z.string(),
  category: z.string(),
  description: z.string(),
  input_schema: z.record(z.string(), z.unknown()).default({}),
  output_schema: z.record(z.string(), z.unknown()).default({}),
  risk: z.enum(['none', 'low', 'medium', 'high', 'critical']),
  requires_approval: z.boolean(),
  timeout_seconds: z.number(),
  cancellation_supported: z.boolean(),
  evidence_policy: z.string(),
  dry_run_supported: z.boolean(),
  side_effecting: z.boolean(),
  enabled: z.boolean().default(true),
});

export const ToolRegistrySnapshotPayload = z.object({
  scan_version: z.string(),
  read_only: z.boolean(),
  status: z.string(),
  registered_count: z.number().int().nonnegative(),
  configured_count: z.number().int().nonnegative(),
  spec_count: z.number().int().nonnegative(),
  drift: z.record(z.string(), z.unknown()),
  tools: z.array(ToolSpecPayload).default([]),
});

export const RuntimeSnapshotPayload = z.object({
  action_timeline: z.array(ActionTimelineItemPayload).optional(),
  tool_registry: ToolRegistrySnapshotPayload.optional(),
}).catchall(z.unknown());

// ─── TOKEN STREAMING ───────────────────────────────────────────────
export const TokenStartPayload = z.object({
  message_id: z.string().uuid(),
  model: z.string().optional(),
});

export const TokenChunkPayload = z.object({
  message_id: z.string().uuid(),
  sequence_id: z.number().int().nonnegative(),
  content: z.string(),
  is_tool_call: z.boolean().default(false),
});

export const TokenEndPayload = z.object({
  message_id: z.string().uuid(),
  total_tokens: z.number().int().optional(),
  finish_reason: z.enum(['stop', 'length', 'tool_calls', 'error']).optional(),
});

// ─── TELEMETRY ─────────────────────────────────────────────────────
export const TelemetryPayload = z.object({
  determinism_score: z.number().min(0).max(1).optional(),
  recovery_budget: z.number().min(0).max(1).optional(),
  vram_usage_gb: z.number().optional(),
  vram_usage_text: z.string().optional(),
  active_app: z.string().optional(),
  active_model: z.string().optional(),
  focus_stable: z.boolean().optional(),
  active_hwnd: z.number().optional(),
  cpu_percent: z.number().optional(),
  memory_percent: z.number().optional(),
  uptime_seconds: z.number().optional(),
  io_throughput: z.string().optional(),
  websocket_clients: z.number().optional(),
});

export const SnapshotPayload = z.object({
  session_id: z.string(),
  journal: z.record(z.string(), z.unknown()),
  runtime: RuntimeSnapshotPayload.optional(),
  current_state: RuntimeStateEnum.optional(),
  snapshot_since_sequence: z.number().int().nonnegative().optional(),
  missed_event_count: z.number().int().nonnegative().optional(),
  missed_events: z.array(z.unknown()).default([]),
  truth_sync: z.object({
    source_of_truth: z.literal('backend_snapshot_protocol_event_journal'),
    snapshot_sequence_num: z.number().int().nonnegative(),
    journal_tail_sequence_num: z.number().int().nonnegative(),
    client_last_sequence_num: z.number().int().nonnegative(),
    missed_event_count: z.number().int().nonnegative(),
    replay_required: z.boolean(),
  }).optional(),
});

// ─── STATE CHANGE ──────────────────────────────────────────────────
export const StateChangePayload = z.object({
  from: RuntimeStateEnum,
  to: RuntimeStateEnum,
  reason: z.string().optional(),
  is_hydration: z.boolean().default(false),
});

// ─── RECOVERY ──────────────────────────────────────────────────────
export const RecoveryPayload = z.object({
  reason: z.string(),
  depth: z.number().int(),
  max_depth: z.number().int(),
  strategy: z.enum(['retry', 'replan', 'escalate', 'abort']).optional(),
  failed_action_id: z.string().optional(),
});

// ─── GUARD ─────────────────────────────────────────────────────────
export const GuardPayload = z.object({
  command_id: z.string().optional(),
  action: z.string(),
  decision: z.enum(['allow', 'block', 'escalate']),
  risk_level: z.enum(['none', 'low', 'medium', 'high', 'critical']),
  requires_approval: z.boolean().default(false),
  reason: z.string().optional(),
  warnings: z.array(z.string()).optional(),
});

export const CommandRecordPayload = z.object({
  command_id: z.string(),
  text: z.string(),
  status: z.string(),
  risk_level: z.enum(['none', 'low', 'medium', 'high', 'critical']).default('none'),
  trace_id: z.string().optional().nullable(),
  approval_required: z.boolean().default(false),
  approved: z.boolean().default(false),
  rejected: z.boolean().default(false),
  active: z.boolean().default(false),
  verification_state: z.string().default('unverified'),
  reason: z.string().default(''),
  warnings: z.array(z.string()).default([]),
  created_at: z.number().optional(),
  updated_at: z.number().optional(),
  metadata: z.record(z.string(), z.unknown()).optional(),
});

export const CommandStatusPayload = z.object({
  command_id: z.string().optional(),
  status: z.string().optional(),
  risk_level: z.enum(['none', 'low', 'medium', 'high', 'critical']).optional(),
  reason: z.string().optional(),
  verification_state: z.string().optional(),
  command: CommandRecordPayload.nullable().optional(),
});

export const CommandReceivedPayload = z.object({
  command_id: z.string().optional(),
  text: z.string().optional(),
  mode: z.string().optional(),
  queued: z.boolean().optional(),
  queue_depth: z.number().int().nonnegative().optional(),
  queue_capacity: z.number().int().nonnegative().optional(),
});

export const IntentParsedPayload = z.object({
  intents: z.array(z.unknown()).default([]),
});

export const VerificationPayload = z.object({
  action_id: z.string().optional(),
  passed: z.boolean().optional(),
  method: z.string().optional(),
  details: z.string().optional(),
  verification_state: z.string().optional(),
  verifier: z.string().nullable().optional(),
  error: z.string().optional(),
  execution_evidence: ExecutionEvidencePayload.optional(),
});

export const TaskFinishedPayload = z.object({
  final_state: RuntimeStateEnum.or(z.string()),
});

export const ApprovalRequiredPayload = z.object({
  command: CommandRecordPayload,
});

export const MaintenanceScanPayload = z.object({
  read_only: z.boolean().optional(),
  scan_version: z.string().optional(),
  report: z.record(z.string(), z.unknown()).optional(),
});

// ─── PLAN ──────────────────────────────────────────────────────────
export const PlanPayload = z.object({
  plan_id: z.string(),
  steps: z.array(z.object({
    step_id: z.string(),
    tool: z.string(),
    description: z.string(),
    params: z.record(z.string(), z.unknown()).optional(),
  })),
  estimated_duration_ms: z.number().optional(),
  feasible: z.boolean().optional(),
  blockers: z.array(z.string()).optional(),
});

// ─── HANDSHAKE ─────────────────────────────────────────────────────
export const HandshakePayload = z.object({
  protocol_version: z.string(),
  session_id: z.string(),
  capabilities: z.array(z.string()).default([]),
  backend_version: z.string().optional(),
  journal: z.record(z.string(), z.unknown()).optional(),
  runtime: RuntimeSnapshotPayload.optional(),
});

// ═══════════════════════════════════════════════════════════════════
// PAYLOAD REGISTRY — Maps event types to their typed payloads
// ═══════════════════════════════════════════════════════════════════

export const PayloadRegistry: Partial<Record<EventTypeValue, z.ZodTypeAny>> = {
  COMMAND_RECEIVED: CommandReceivedPayload,
  INTENT_PARSED: IntentParsedPayload,
  ACTION_STARTED: ActionStartedPayload,
  ACTION_COMPLETED: ActionCompletedPayload,
  ACTION_FAILED: ActionFailedPayload,
  TOKEN_START: TokenStartPayload,
  TOKEN_CHUNK: TokenChunkPayload,
  TOKEN_END: TokenEndPayload,
  TELEMETRY_UPDATE: TelemetryPayload,
  VRAM_UPDATE: TelemetryPayload,
  STATE_CHANGE: StateChangePayload,
  VERIFICATION_PASSED: VerificationPayload,
  VERIFICATION_FAILED: VerificationPayload,
  RECOVERY_TRIGGERED: RecoveryPayload,
  GUARD_EVALUATED: GuardPayload,
  COMMAND_STATUS_CHANGED: CommandStatusPayload,
  COMMAND_BLOCKED: CommandStatusPayload,
  COMMAND_CANCELLED: CommandStatusPayload,
  COMMAND_APPROVED: ApprovalRequiredPayload,
  COMMAND_REJECTED: ApprovalRequiredPayload,
  APPROVAL_REQUIRED: ApprovalRequiredPayload,
  MAINTENANCE_SCAN_STARTED: MaintenanceScanPayload,
  MAINTENANCE_SCAN_COMPLETED: MaintenanceScanPayload,
  PLAN_CREATED: PlanPayload,
  TASK_FINISHED: TaskFinishedPayload,
  SYSTEM_ONLINE: HandshakePayload,
  SNAPSHOT_CREATED: SnapshotPayload,
};

// ═══════════════════════════════════════════════════════════════════
// VALIDATION UTILITIES
// ═══════════════════════════════════════════════════════════════════

/**
 * Validates a raw event from the WebSocket against the protocol.
 * Returns typed event or null + logs violation.
 */
export function validateEvent(raw: unknown): RuntimeEvent | null {
  const envelope = RuntimeEventSchema.safeParse(raw);
  if (!envelope.success) {
    console.error('[PROTOCOL] Invalid event envelope:', envelope.error.issues);
    return null;
  }

  const event = envelope.data;
  const payloadSchema = PayloadRegistry[event.type];

  if (payloadSchema) {
    const payloadResult = payloadSchema.safeParse(event.payload);
    if (!payloadResult.success) {
      console.warn(`[PROTOCOL] Payload validation failed for ${event.type}:`, payloadResult.error.issues);
      // Non-fatal: we still accept the event but log the violation
    }
  }

  return event;
}

/**
 * Creates a typed event with automatic ID and timestamp.
 */
export function createEvent(
  type: EventTypeValue,
  payload: Record<string, unknown> = {},
  overrides: Partial<RuntimeEvent> = {}
): RuntimeEvent {
  return {
    event_id: crypto.randomUUID(),
    type,
    timestamp: Date.now(),
    severity: 'info',
    protocol_version: PROTOCOL_VERSION,
    payload,
    ...overrides,
  };
}
