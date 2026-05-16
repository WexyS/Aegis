// src/types/runtime.ts

export enum RuntimeComponent {
  PLANNER = 'planner',
  EXECUTOR = 'executor',
  VALIDATOR = 'validator',
  RECOVERY = 'recovery',
}

export enum RuntimeStatus {
  PENDING = 'pending',
  ACTIVE = 'active',
  SUCCESS = 'success',
  ERROR = 'error',
}

export enum WebSocketEvent {
  SYSTEM_ONLINE = 'SYSTEM_ONLINE',
  SYSTEM_OFFLINE = 'SYSTEM_OFFLINE',
  SESSION_START = 'SESSION_START',
  SESSION_END = 'SESSION_END',
  COMMAND_RECEIVED = 'COMMAND_RECEIVED',
  INTENT_PARSED = 'INTENT_PARSED',
  PLAN_CREATED = 'PLAN_CREATED',
  ACTION_STARTED = 'ACTION_STARTED',
  ACTION_COMPLETED = 'ACTION_COMPLETED',
  ACTION_FAILED = 'ACTION_FAILED',
  ACTION_RETRY = 'ACTION_RETRY',
  GUARD_EVALUATED = 'GUARD_EVALUATED',
  COMMAND_STATUS_CHANGED = 'COMMAND_STATUS_CHANGED',
  APPROVAL_REQUIRED = 'APPROVAL_REQUIRED',
  COMMAND_APPROVED = 'COMMAND_APPROVED',
  COMMAND_REJECTED = 'COMMAND_REJECTED',
  COMMAND_CANCELLED = 'COMMAND_CANCELLED',
  COMMAND_BLOCKED = 'COMMAND_BLOCKED',
  VERIFICATION_PASSED = 'VERIFICATION_PASSED',
  VERIFICATION_FAILED = 'VERIFICATION_FAILED',
  RECOVERY_TRIGGERED = 'RECOVERY_TRIGGERED',
  RECOVERY_COMPLETED = 'RECOVERY_COMPLETED',
  RECOVERY_EXHAUSTED = 'RECOVERY_EXHAUSTED',
  FOCUS_ACQUIRED = 'FOCUS_ACQUIRED',
  FOCUS_LOST = 'FOCUS_LOST',
  DETERMINISM_BREACH = 'DETERMINISM_BREACH',
  TOKEN_START = 'TOKEN_START',
  TOKEN_CHUNK = 'TOKEN_CHUNK',
  TOKEN_END = 'TOKEN_END',
  TOKEN_ABORT = 'TOKEN_ABORT',
  TOKEN_ERROR = 'TOKEN_ERROR',
  TELEMETRY_UPDATE = 'TELEMETRY_UPDATE',
  VRAM_UPDATE = 'VRAM_UPDATE',
  MODEL_SWITCH = 'MODEL_SWITCH',
  TASK_FINISHED = 'TASK_FINISHED',
  MAINTENANCE_SCAN_STARTED = 'MAINTENANCE_SCAN_STARTED',
  MAINTENANCE_SCAN_COMPLETED = 'MAINTENANCE_SCAN_COMPLETED',
  VISION_ESCALATION = 'VISION_ESCALATION',
  VISION_RESULT = 'VISION_RESULT',
  STATE_CHANGE = 'STATE_CHANGE',
  SNAPSHOT_CREATED = 'SNAPSHOT_CREATED',
}

export interface StreamChunk {
  messageId: string;
  sequenceId: number;
  content: string;
  timestamp: number;
}

export interface RuntimeStep {
  id: string;
  component: RuntimeComponent | string;
  status: RuntimeStatus;
  label: string;
  detail: string;
  timestamp: string;
  executionEvidence?: ExecutionEvidence;
  metrics?: {
    determinism?: number;
    latency_ms?: number;
    retries?: number;
  };
}

export interface TelemetryData {
  determinismScore: number;
  recoveryBudget: number;
  vramUsage: string;
  activeApp: string;
  activeModel: string;
  connectionState?: 'disconnected' | 'connecting' | 'connected' | 'reconnecting' | 'failed';
  cpuPercent?: number;
  memoryPercent?: number;
  uptimeSeconds?: number;
  ioThroughput?: string;
  websocketClients?: number;
  eventThroughput?: number;
  wsRttMs?: number;
  lastSequenceNum?: number;
  runtimeIntegrity?: string;
}

export type RiskLevel = 'none' | 'low' | 'medium' | 'high' | 'critical';

export interface CommandRecord {
  command_id: string;
  text: string;
  status: string;
  risk_level: RiskLevel;
  trace_id?: string | null;
  approval_required: boolean;
  approved: boolean;
  rejected: boolean;
  active: boolean;
  verification_state: string;
  reason: string;
  warnings: string[];
  created_at?: number;
  updated_at?: number;
}

export interface AppRegistryEntry {
  app_id: string;
  display_name: string;
  source: string;
  aliases: string[];
  process_name?: string | null;
  launch_target_type: string;
}

export interface ExecutionEvidence {
  action: string;
  target?: string | null;
  target_type: string;
  method: string;
  verifier?: string | null;
  verification_state: string;
  verification_reason?: string | null;
  started_at_ms?: number;
  completed_at_ms?: number;
  launch_target?: string | null;
  resolved_path?: string | null;
  process_name?: string | null;
  pids: number[];
  process_alive?: boolean | null;
  window?: Record<string, unknown> | null;
  expected: Record<string, unknown>;
  observed: Record<string, unknown>;
  verification_checks: Array<Record<string, unknown>>;
  matching_windows: Array<Record<string, unknown>>;
  retry_count: number;
  recovery_triggered: boolean;
  attempts: Array<Record<string, unknown>>;
  fallback_chain: Array<Record<string, unknown>>;
  warnings: string[];
}

export interface ActionTimelineItem {
  action_id: string;
  tool: string;
  status: RuntimeStatus | string;
  target?: string | null;
  started_at?: number | null;
  completed_at?: number | null;
  latency_ms?: number | null;
  execution_evidence?: ExecutionEvidence | null;
  trace_id?: string | null;
  sequence_num?: number | null;
}

export interface AppRegistrySnapshot {
  scan_version: string;
  read_only?: boolean;
  configured_count: number;
  discovered_count: number;
  entry_count: number;
  entries: AppRegistryEntry[];
  truncated: boolean;
}

export interface ToolSpec {
  name: string;
  category: 'desktop' | 'web' | 'file' | 'shell' | 'git' | 'system' | string;
  description: string;
  input_schema: Record<string, unknown>;
  output_schema: Record<string, unknown>;
  risk: RiskLevel;
  requires_approval: boolean;
  timeout_seconds: number;
  cancellation_supported: boolean;
  evidence_policy: string;
  dry_run_supported: boolean;
  side_effecting: boolean;
  enabled: boolean;
}

export interface ToolRegistrySnapshot {
  scan_version: string;
  read_only: boolean;
  status: 'ok' | 'warning' | string;
  registered_count: number;
  configured_count: number;
  spec_count: number;
  drift: {
    status: string;
    missing_in_config: string[];
    missing_in_code: string[];
    missing_specs: string[];
    mismatches: Array<Record<string, unknown>>;
  };
  tools: ToolSpec[];
}

export interface EnvironmentDiagnostics {
  scan_version: string;
  read_only: boolean;
  overall_status: string;
  checks: Record<string, Record<string, unknown>>;
  recommendations: string[];
}

export interface EvidenceAudit {
  scan_version: string;
  read_only: boolean;
  status: string;
  action_event_count: number;
  action_count: number;
  completed_or_failed_count: number;
  active_count: number;
  success_count: number;
  error_count: number;
  evidence_backed_count: number;
  missing_evidence_count: number;
  verified_action_count: number;
  unverified_evidence_count: number;
  failed_evidence_count: number;
  check_pass_count: number;
  check_fail_count: number;
  check_unknown_count: number;
  critical_failure_count: number;
  critical_failures: Array<Record<string, unknown>>;
  verification_counts: Record<string, number>;
  verifier_counts: Record<string, number>;
  latest_sequence_num: number;
  limit: number;
}

export interface RuntimeHealth {
  scan_version: string;
  read_only: boolean;
  status: string;
  source_of_truth: string;
  component_statuses: Record<string, string>;
  attention: string[];
}

export interface CommandLifecycleDiagnostics {
  scan_version: string;
  read_only: boolean;
  status: string;
  record_count: number;
  pending_count: number;
  active_count: number;
  active_record_count: number;
  unverified_completed_count: number;
  latest_status?: string | null;
  latest_verification_state?: string | null;
}

export interface RuntimeSnapshotDiagnostics {
  scan_version: string;
  read_only: boolean;
  status: string;
  session_id?: string | null;
  fsm_state?: string | null;
  queue_depth: number;
  queue_capacity: number;
  recovery_depth: number;
  active_trace_id?: string | null;
  last_event_sequence: number;
  journal_last_sequence_num: number;
  sequence_aligned: boolean;
}

export interface WebSocketDiagnostics {
  scan_version: string;
  read_only: boolean;
  status: string;
  session_id?: string | null;
  connected_clients?: number | null;
  queue_depth?: number | null;
  queue_capacity?: number | null;
}

export interface ActionTimelineDiagnostics {
  scan_version: string;
  read_only: boolean;
  status: string;
  action_count: number;
  active_count: number;
  error_count: number;
  evidence_backed_count: number;
  latest_sequence_num: number;
}
