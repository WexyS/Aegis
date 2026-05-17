/**
 * ══════════════════════════════════════════════════════════════════════
 * AEGIS RUNTIME BRIDGE v2.0
 * ══════════════════════════════════════════════════════════════════════
 *
 * Production-grade WebSocket layer with:
 *   - Protocol-validated event handling
 *   - Automatic reconnection with exponential backoff
 *   - Sequence integrity & gap detection
 *   - Event ordering guarantees
 *   - Connection state machine
 *   - Heartbeat / keepalive
 *
 * This replaces the naive socket.io wrapper from v1.
 * ══════════════════════════════════════════════════════════════════════
 */

import { io, Socket } from 'socket.io-client';
import { useChatStore } from '@/store/useChatStore';
import { useRuntimeStore } from '@/store/useRuntimeStore';
import {
  validateEvent,
  createEvent,
  RuntimeEvent,
  EventTypeValue,
  PROTOCOL_VERSION,
} from '@/contracts/protocol';
import { RuntimeState } from '@/types/fsm';
import { AppRegistrySnapshot, ExecutionEvidence, RuntimeStatus, ToolRegistrySnapshot } from '@/types/runtime';
import { eventSourcing } from '@/features/runtime/services/EventSourcing';

// ─── CONNECTION CONFIG ─────────────────────────────────────────────
const SOCKET_URL = process.env.NEXT_PUBLIC_WS_URL || 'http://localhost:8400';

const RECONNECT_CONFIG = {
  initialDelay: 1000,
  maxDelay: 30000,
  factor: 2,
  maxAttempts: 20,
  jitter: true,
} as const;

const HEARTBEAT_INTERVAL = 15000; // 15s

// ─── CONNECTION STATE ──────────────────────────────────────────────
type ConnectionState = 'disconnected' | 'connecting' | 'connected' | 'reconnecting' | 'failed';

let connectionState: ConnectionState = 'disconnected';
let reconnectAttempts = 0;
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
let heartbeatTimer: ReturnType<typeof setInterval> | null = null;
let lastServerTime = 0;
let lastSequenceNum = 0;
let lastThroughputTick = Date.now();
let eventsThisSecond = 0;
let handlersRegistered = false;
let socketLifecycleRegistered = false;
let lastSnapshotRequestAt = 0;

// Sequence tracking per stream
const sequenceTrackers = new Map<string, number>();
const seenBackendEventIds = new Set<string>();

// ─── SOCKET INSTANCE ───────────────────────────────────────────────
export const socket: Socket = io(SOCKET_URL, {
  autoConnect: false,
  reconnection: false, // We handle this ourselves
  transports: ['polling', 'websocket'],
  timeout: 10000,
});

// ─── EVENT DISPATCH TABLE ──────────────────────────────────────────
type EventHandler = (event: RuntimeEvent) => void;
const handlers = new Map<EventTypeValue, EventHandler>();

function on(type: EventTypeValue, handler: EventHandler) {
  handlers.set(type, handler);
}

function dispatch(event: RuntimeEvent) {
  const handler = handlers.get(event.type);
  if (handler) {
    handler(event);
  } else {
    console.debug(`[BRIDGE] Unhandled event type: ${event.type}`);
  }
}

type AcceptRuntimeEventOptions = {
  allowHistoricalDispatch?: boolean;
  ingestOnly?: boolean;
  suppressGapLog?: boolean;
};

function eventSessionId(event: RuntimeEvent): string | undefined {
  return event.session_id || (event.payload?.session_id as string | undefined);
}

function resetBridgeProjectionForSession(sessionId: string) {
  const changed = eventSourcing.setSessionId(sessionId);
  if (!changed) return;
  lastSequenceNum = 0;
  seenBackendEventIds.clear();
  sequenceTrackers.clear();
  useRuntimeStore.getState().setTelemetry({
    lastSequenceNum: 0,
    runtimeIntegrity: 'session-reset',
  });
  useRuntimeStore.getState().clearSteps();
}

function requestSnapshotResync(reason: string) {
  const now = Date.now();
  if (!socket.connected || now - lastSnapshotRequestAt < 1500) return;
  lastSnapshotRequestAt = now;
  useRuntimeStore.getState().setTelemetry({ runtimeIntegrity: 'resyncing' });
  useRuntimeStore.getState().addLog({ level: 'WARN', message: `Snapshot resync requested: ${reason}`, color: 'text-warning' });
  socket.emit('handshake', {
    protocol_version: PROTOCOL_VERSION,
    client_type: 'aegis-ui',
    timestamp: now,
    last_sequence_num: lastSequenceNum,
  });
}

async function acceptRuntimeEvent(event: RuntimeEvent, options: AcceptRuntimeEventOptions = {}) {
  const incomingSessionId = eventSessionId(event);
  if (incomingSessionId) {
    resetBridgeProjectionForSession(incomingSessionId);
  }

  if (seenBackendEventIds.has(event.event_id)) {
    return;
  }
  seenBackendEventIds.add(event.event_id);

  const runtimeStore = useRuntimeStore.getState();
  let sequence = event.sequence_num ?? lastSequenceNum;

  if (event.sequence_num !== undefined) {
    if (event.sequence_num <= lastSequenceNum) {
      if (!options.allowHistoricalDispatch) {
        return;
      }
      sequence = lastSequenceNum;
    } else {
      if (event.sequence_num > lastSequenceNum + 1 && lastSequenceNum !== 0 && !options.suppressGapLog) {
        runtimeStore.addLog({ level: 'WARN', message: `Event gap: expected ${lastSequenceNum + 1}, got ${event.sequence_num}`, color: 'text-warning' });
        requestSnapshotResync(`expected ${lastSequenceNum + 1}, got ${event.sequence_num}`);
      }
      lastSequenceNum = event.sequence_num;
      sequence = lastSequenceNum;
    }
  }

  const now = Date.now();
  eventsThisSecond += 1;
  if (now - lastThroughputTick >= 1000) {
    runtimeStore.setTelemetry({ eventThroughput: eventsThisSecond });
    eventsThisSecond = 0;
    lastThroughputTick = now;
  }

  runtimeStore.setTelemetry({
    lastSequenceNum: sequence,
    runtimeIntegrity: event.event_hash || event.eventHash ? 'hash-chain' : 'unverified',
  });

  await eventSourcing.ingestBackendEvent(event);
  if (!options.ingestOnly) {
    dispatch(event);
  }
}

function applyRuntimeSnapshotPayload(payload: any, reason: string) {
  const runtimeStore = useRuntimeStore.getState();
  const runtime = payload.runtime;
  const snapshotState = payload.runtime?.fsm_state || payload.current_state;
  if (snapshotState) {
    runtimeStore.syncBackendSnapshot(snapshotState as RuntimeState, { reason });
  }
  runtimeStore.syncCommandSnapshot(payload.runtime?.commands);
  runtimeStore.syncActionTimelineSnapshot(payload.runtime?.action_timeline);
  if (runtime && Object.prototype.hasOwnProperty.call(runtime, 'app_registry')) {
    runtimeStore.setAppRegistry(runtime.app_registry as AppRegistrySnapshot | null);
  }
  if (runtime && Object.prototype.hasOwnProperty.call(runtime, 'tool_registry')) {
    runtimeStore.setToolRegistry(runtime.tool_registry as ToolRegistrySnapshot | null);
  }
  if (runtime && Object.prototype.hasOwnProperty.call(runtime, 'maintenance_scan')) {
    runtimeStore.setMaintenanceScan(runtime.maintenance_scan as Record<string, unknown> | null);
  }
}

function actionStepFromPayload(event: RuntimeEvent, payload: any, status: RuntimeStatus): any | null {
  if (!payload.action_id) return null;
  const evidence = payload.execution_evidence as ExecutionEvidence | undefined;
  const tool = payload.tool || evidence?.action || 'executor';
  const target = payload.target || evidence?.target || payload.error || `Executing ${tool}`;
  return {
    id: payload.action_id,
    component: tool,
    status,
    label: tool,
    detail: target,
    timestamp: new Date(event.timestamp).toLocaleTimeString(),
    executionEvidence: evidence,
    metrics: {
      latency_ms: payload.latency_ms,
      retries: payload.retries || evidence?.retry_count || 0,
      determinism: evidence?.verification_state === 'verified' || payload.verification?.passed ? 1.0 : undefined,
    },
  };
}

function upsertActionStepFromPayload(event: RuntimeEvent, payload: any, status: RuntimeStatus) {
  const step = actionStepFromPayload(event, payload, status);
  if (step) {
    useRuntimeStore.getState().upsertStep(step);
  }
}

function applySnapshotTruthTelemetry(event: RuntimeEvent, payload: any) {
  const journal = payload.journal || {};
  const truthSync = payload.truth_sync || {};
  const snapshotSequence = Number(
    truthSync.snapshot_sequence_num ??
    event.sequence_num ??
    journal.last_sequence_num ??
    lastSequenceNum
  );
  if (Number.isFinite(snapshotSequence) && snapshotSequence > lastSequenceNum) {
    lastSequenceNum = snapshotSequence;
  }
  useRuntimeStore.getState().setTelemetry({
    lastSequenceNum: lastSequenceNum,
    runtimeIntegrity: (journal.integrity_status as string | undefined) || (journal.last_event_hash ? 'hash-chain' : 'unverified'),
  });
}

async function ingestSnapshotMissedEvents(payload: any) {
  const missed = Array.isArray(payload.missed_events) ? payload.missed_events : [];
  for (const raw of missed.sort((a: any, b: any) => (a.sequence_num ?? 0) - (b.sequence_num ?? 0))) {
    const missedEvent = validateEvent(raw);
    if (!missedEvent) continue;
    await acceptRuntimeEvent(missedEvent, {
      allowHistoricalDispatch: true,
      ingestOnly: true,
      suppressGapLog: true,
    });
  }
  return missed.length;
}

// ─── RECONNECTION LOGIC ───────────────────────────────────────────
function getReconnectDelay(): number {
  const { initialDelay, maxDelay, factor, jitter } = RECONNECT_CONFIG;
  let delay = initialDelay * Math.pow(factor, reconnectAttempts);
  if (jitter) {
    delay += Math.random() * initialDelay;
  }
  return Math.min(delay, maxDelay);
}

function scheduleReconnect() {
  if (reconnectAttempts >= RECONNECT_CONFIG.maxAttempts) {
    connectionState = 'failed';
    useRuntimeStore.getState().setTelemetry({ connectionState });
    console.error(`[BRIDGE] Max reconnection attempts (${RECONNECT_CONFIG.maxAttempts}) exhausted.`);
    return;
  }

  connectionState = 'reconnecting';
  useRuntimeStore.getState().setTelemetry({ connectionState });
  const delay = getReconnectDelay();
  reconnectAttempts++;

  console.warn(`[BRIDGE] Reconnecting in ${Math.round(delay)}ms (attempt ${reconnectAttempts}/${RECONNECT_CONFIG.maxAttempts})`);

  reconnectTimer = setTimeout(() => {
    socket.connect();
  }, delay);
}

function cancelReconnect() {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
}

// ─── HEARTBEAT ─────────────────────────────────────────────────────
function startHeartbeat() {
  stopHeartbeat();
  heartbeatTimer = setInterval(() => {
    if (socket.connected) {
      socket.emit('heartbeat', { timestamp: Date.now(), protocol_version: PROTOCOL_VERSION });
    }
  }, HEARTBEAT_INTERVAL);
}

function stopHeartbeat() {
  if (heartbeatTimer) {
    clearInterval(heartbeatTimer);
    heartbeatTimer = null;
  }
}

// ═══════════════════════════════════════════════════════════════════
// EVENT HANDLERS — Wired to protocol-validated payloads
// ═══════════════════════════════════════════════════════════════════

function registerEventHandlers() {
  if (handlersRegistered) return;
  handlersRegistered = true;

  const getChatStore = () => useChatStore.getState();
  const getRuntimeStore = () => useRuntimeStore.getState();

  // ── HANDSHAKE ────────────────────────────────────────────────────
  on('SYSTEM_ONLINE', (event) => {
    const payload = event.payload as any;
    if (payload.protocol_version && payload.protocol_version !== PROTOCOL_VERSION) {
      getRuntimeStore().addLog({ level: 'ERR', message: `Protocol mismatch! Server: ${payload.protocol_version}, Client: ${PROTOCOL_VERSION}`, color: 'text-danger' });
    }
    if (payload.session_id) resetBridgeProjectionForSession(payload.session_id);
    applyRuntimeSnapshotPayload(payload, 'system online');
    getRuntimeStore().addLog({ level: 'SYS', message: `Aegis Runtime Protocol v${PROTOCOL_VERSION} Online. Session: ${payload.session_id || 'unknown'}`, color: 'text-accent' });
  });

  on('SNAPSHOT_CREATED', (event) => {
    void (async () => {
    const payload = event.payload as any;
    const journal = payload.journal || {};
    if (payload.session_id) resetBridgeProjectionForSession(payload.session_id);
    const missedCount = await ingestSnapshotMissedEvents(payload);
    applyRuntimeSnapshotPayload(payload, 'snapshot sync');
    applySnapshotTruthTelemetry(event, payload);
    getRuntimeStore().addLog({
      level: 'SYS',
      message: `Runtime snapshot synced (${journal.event_count ?? 0} events, ${payload.missed_event_count ?? missedCount} replayed).`,
      color: 'text-accent',
    });
    })();
  });

  // ── TOKEN STREAMING ──────────────────────────────────────────────
  on('TOKEN_START', (event) => {
    const payload = event.payload as any;
    sequenceTrackers.set(payload.message_id, -1);
    getChatStore().addMessage({ id: payload.message_id, role: 'assistant', isComplete: false });
    getRuntimeStore().addLog({ level: 'INFO', message: 'Token stream initiated.' });
  });

  on('TOKEN_CHUNK', (event) => {
    const payload = event.payload as any;
    const lastSeq = sequenceTrackers.get(payload.message_id) ?? -1;

    // Dedupe
    if (payload.sequence_id <= lastSeq) {
      return;
    }

    // Gap detection
    if (payload.sequence_id > lastSeq + 1) {
      getRuntimeStore().addLog({ level: 'WARN', message: `Stream gap: expected seq ${lastSeq + 1}, got ${payload.sequence_id}`, color: 'text-warning' });
    }

    sequenceTrackers.set(payload.message_id, payload.sequence_id);
    getChatStore().handleStreamChunk({
      messageId: payload.message_id,
      sequenceId: payload.sequence_id,
      content: payload.content,
      timestamp: event.timestamp,
    });
  });

  on('TOKEN_END', (event) => {
    const payload = event.payload as any;
    sequenceTrackers.delete(payload.message_id);
    getChatStore().finalizeMessage(payload.message_id);
    getRuntimeStore().addLog({ level: 'OK', message: 'Token stream completed.', color: 'text-success' });
  });

  on('TOKEN_ABORT', (event) => {
    const payload = event.payload as any;
    sequenceTrackers.delete(payload.message_id);
    getChatStore().finalizeMessage(payload.message_id);
    getRuntimeStore().addLog({ level: 'WARN', message: 'Token stream aborted.', color: 'text-warning' });
  });

  // ── ACTION LIFECYCLE ─────────────────────────────────────────────
  on('ACTION_STARTED', (event) => {
    const payload = event.payload as any;
    getRuntimeStore().addStep({
      id: payload.action_id,
      component: payload.tool || 'executor',
      status: RuntimeStatus.ACTIVE,
      label: payload.tool,
      detail: payload.target || `Executing ${payload.tool}`,
      timestamp: new Date(event.timestamp).toLocaleTimeString(),
      metrics: {},
    });
    getRuntimeStore().addLog({ level: 'EXEC', message: `Action Started: ${payload.tool} (${payload.target || 'no target'})`, color: 'text-secondary-light' });
  });

  on('APPROVAL_REQUIRED', (event) => {
    const payload = event.payload as any;
    if (payload.command) {
      getRuntimeStore().upsertCommand(payload.command);
      getRuntimeStore().addLog({ level: 'WARN', message: `Approval required: ${payload.command.risk_level} risk`, color: 'text-warning' });
    }
  });

  on('COMMAND_APPROVED', (event) => {
    const payload = event.payload as any;
    if (payload.command) {
      getRuntimeStore().upsertCommand(payload.command);
      getRuntimeStore().addLog({ level: 'OK', message: `Command approved`, color: 'text-success' });
    }
  });

  on('COMMAND_REJECTED', (event) => {
    const payload = event.payload as any;
    if (payload.command) {
      getRuntimeStore().upsertCommand(payload.command);
      getRuntimeStore().addLog({ level: 'WARN', message: `Command rejected: ${payload.command.reason || 'user decision'}`, color: 'text-warning' });
    }
  });

  on('COMMAND_STATUS_CHANGED', (event) => {
    const payload = event.payload as any;
    if (payload.command) {
      getRuntimeStore().upsertCommand(payload.command);
    }
    getRuntimeStore().addLog({ level: 'SYS', message: `Command status: ${payload.status || 'updated'}`, color: 'text-accent' });
  });

  on('COMMAND_BLOCKED', (event) => {
    const payload = event.payload as any;
    if (payload.command) {
      getRuntimeStore().upsertCommand(payload.command);
    }
    getRuntimeStore().addLog({ level: 'ERR', message: `Command blocked: ${payload.reason || 'policy gate'}`, color: 'text-danger' });
  });

  on('COMMAND_CANCELLED', (event) => {
    const payload = event.payload as any;
    if (payload.command) {
      getRuntimeStore().upsertCommand(payload.command);
    }
    getRuntimeStore().addLog({ level: 'WARN', message: `Command cancelled`, color: 'text-warning' });
  });

  on('ACTION_COMPLETED', (event) => {
    const payload = event.payload as any;
    upsertActionStepFromPayload(event, payload, payload.success ? RuntimeStatus.SUCCESS : RuntimeStatus.ERROR);
    getRuntimeStore().updateStep(payload.action_id, {
      status: payload.success ? RuntimeStatus.SUCCESS : RuntimeStatus.ERROR,
      executionEvidence: payload.execution_evidence as ExecutionEvidence | undefined,
      metrics: {
        latency_ms: payload.latency_ms,
        retries: payload.retries || 0,
        determinism: payload.verification?.passed ? 1.0 : 0.5,
      },
    });
    if (payload.success) {
      getRuntimeStore().addLog({ level: 'OK', message: `Action Completed`, duration: `${payload.latency_ms}ms`, color: 'text-success' });
    }
  });

  on('ACTION_FAILED', (event) => {
    const payload = event.payload as any;
    upsertActionStepFromPayload(event, payload, RuntimeStatus.ERROR);
    getRuntimeStore().updateStep(payload.action_id, {
      status: RuntimeStatus.ERROR,
      detail: payload.error,
      executionEvidence: payload.execution_evidence as ExecutionEvidence | undefined,
    });
    getRuntimeStore().addLog({ level: 'ERR', message: `Action Failed: ${payload.error}`, color: 'text-danger' });
  });

  on('VERIFICATION_PASSED', (event) => {
    const payload = event.payload as any;
    if (payload.action_id && payload.execution_evidence) {
      upsertActionStepFromPayload(event, payload, RuntimeStatus.SUCCESS);
    }
    if (payload.action_id && payload.execution_evidence) {
      getRuntimeStore().updateStep(payload.action_id, {
        executionEvidence: payload.execution_evidence as ExecutionEvidence,
      });
    }
    getRuntimeStore().addLog({ level: 'OK', message: `Verification passed: ${payload.verifier || payload.method || 'evidence'}`, color: 'text-success' });
  });

  on('VERIFICATION_FAILED', (event) => {
    const payload = event.payload as any;
    if (payload.action_id && payload.execution_evidence) {
      upsertActionStepFromPayload(event, payload, RuntimeStatus.ERROR);
    }
    if (payload.action_id && payload.execution_evidence) {
      getRuntimeStore().updateStep(payload.action_id, {
        status: RuntimeStatus.ERROR,
        executionEvidence: payload.execution_evidence as ExecutionEvidence,
      });
    }
    getRuntimeStore().addLog({ level: 'WARN', message: `Verification failed: ${payload.details || payload.verification_state || 'unverified'}`, color: 'text-warning' });
  });

  // ── RECOVERY ─────────────────────────────────────────────────────
  on('RECOVERY_TRIGGERED', (event) => {
    const payload = event.payload as any;
    getRuntimeStore().incrementRecovery();
    getRuntimeStore().addLog({ level: 'WARN', message: `Recovery Triggered: ${payload.reason} (Depth: ${payload.depth})`, color: 'text-warning' });
  });

  on('RECOVERY_EXHAUSTED', (event) => {
    getRuntimeStore().addLog({ level: 'ERR', message: `Recovery Budget Exhausted`, color: 'text-danger' });
  });

  // ── TELEMETRY ────────────────────────────────────────────────────
  on('TELEMETRY_UPDATE', (event) => {
    const payload = event.payload as any;
    const telemetry: Record<string, unknown> = {};
    if (payload.determinism_score !== undefined) telemetry.determinismScore = payload.determinism_score;
    if (payload.recovery_budget !== undefined) telemetry.recoveryBudget = payload.recovery_budget;
    if (payload.vram_usage_text !== undefined) telemetry.vramUsage = payload.vram_usage_text;
    if (payload.active_app !== undefined) telemetry.activeApp = payload.active_app;
    if (payload.active_model !== undefined) telemetry.activeModel = payload.active_model;
    if (payload.cpu_percent !== undefined) telemetry.cpuPercent = payload.cpu_percent;
    if (payload.memory_percent !== undefined) telemetry.memoryPercent = payload.memory_percent;
    if (payload.uptime_seconds !== undefined) telemetry.uptimeSeconds = payload.uptime_seconds;
    if (payload.io_throughput !== undefined) telemetry.ioThroughput = payload.io_throughput;
    if (payload.websocket_clients !== undefined) telemetry.websocketClients = payload.websocket_clients;
    getRuntimeStore().setTelemetry(telemetry as any);
  });

  on('MODEL_SWITCH', (event) => {
    const payload = event.payload as any;
    getRuntimeStore().setTelemetry({ activeModel: payload.active_model });
    getRuntimeStore().addLog({ level: 'SYS', message: `Model Switch: ${payload.active_model}`, color: 'text-accent' });
  });

  on('MAINTENANCE_SCAN_COMPLETED', (event) => {
    const payload = event.payload as any;
    if (payload.report) {
      getRuntimeStore().setMaintenanceScan(payload.report as Record<string, unknown>);
      const report = payload.report as any;
      if (report.checks?.app_registry) {
        getRuntimeStore().setAppRegistry(report.checks.app_registry as AppRegistrySnapshot);
      }
      if (report.checks?.tool_registry?.registry) {
        getRuntimeStore().setToolRegistry(report.checks.tool_registry.registry as ToolRegistrySnapshot);
      }
      getRuntimeStore().addLog({ level: 'OK', message: 'Maintenance scan completed.', color: 'text-success' });
    }
  });

  on('STATE_CHANGE', (event) => {
    const payload = event.payload as any;
    const fromState = payload.from as RuntimeState | undefined;
    const newState = payload.to as RuntimeState;
    if (newState) {
      getRuntimeStore().applyBackendTransition(fromState, newState, { reason: payload.reason });
    }
  });

  // ── TASK ─────────────────────────────────────────────────────────
  on('TASK_FINISHED', (event) => {
    const payload = event.payload as any;
    getRuntimeStore().addLog({ level: payload.final_state === RuntimeState.FAILED ? 'ERR' : 'OK', message: `Task Pipeline Finished: ${payload.final_state || 'unknown'}`, color: payload.final_state === RuntimeState.FAILED ? 'text-danger' : 'text-success' });
  });

  // ── PLAN ─────────────────────────────────────────────────────────
  on('PLAN_CREATED', (event) => {
    const payload = event.payload as any;
    (payload.steps || []).forEach((step: any) => {
      getRuntimeStore().addStep({
        id: step.step_id,
        component: step.tool,
        status: RuntimeStatus.PENDING,
        label: step.tool,
        detail: step.description,
        timestamp: new Date(event.timestamp).toLocaleTimeString(),
      });
    });
  });
}

// ═══════════════════════════════════════════════════════════════════
// PUBLIC API
// ═══════════════════════════════════════════════════════════════════

export async function connectRuntime() {
  if (connectionState === 'connected' || connectionState === 'connecting') {
    return;
  }

  connectionState = 'connecting';
  useRuntimeStore.getState().setTelemetry({ connectionState });
  
  try {
    await eventSourcing.init();
  } catch (err) {
    console.error('[EVENT_SOURCING] Failed to initialize:', err);
  }

  registerEventHandlers();

  if (!socketLifecycleRegistered) {
    socketLifecycleRegistered = true;

  // ── Socket lifecycle ────────────────────────────────────────────
  socket.on('connect', () => {
    connectionState = 'connected';
    useRuntimeStore.getState().setTelemetry({ connectionState });
    reconnectAttempts = 0;
    cancelReconnect();
    startHeartbeat();
    console.log('[BRIDGE] Aegis Runtime Bridge Online.');

    // Handshake
    socket.emit('handshake', {
      protocol_version: PROTOCOL_VERSION,
      client_type: 'aegis-ui',
      timestamp: Date.now(),
      last_sequence_num: lastSequenceNum,
    });
  });

  socket.on('heartbeat_ack', (data: any) => {
    if (typeof data?.client_time === 'number') {
      useRuntimeStore.getState().setTelemetry({ wsRttMs: Date.now() - data.client_time });
    }
  });

  socket.on('disconnect', (reason) => {
    connectionState = 'disconnected';
    useRuntimeStore.getState().setTelemetry({ connectionState });
    stopHeartbeat();
    console.warn(`[BRIDGE] Disconnected: ${reason}`);

    if (reason !== 'io client disconnect') {
      scheduleReconnect();
    }
  });

  socket.on('connect_error', (err) => {
    console.error(`[BRIDGE] Connection error: ${err.message}`);
    useRuntimeStore.getState().setTelemetry({ connectionState: 'reconnecting' });
    if (connectionState !== 'reconnecting') {
      scheduleReconnect();
    }
  });

  // ── Main event ingestion ────────────────────────────────────────
  socket.onAny(async (eventName: string, data: unknown) => {
    // Skip internal socket.io events and heartbeat
    if (eventName.startsWith('__') || eventName === 'heartbeat_ack') return;

    // Validate against protocol
    const event = validateEvent(data);
    if (event) {
      lastServerTime = event.timestamp;
      await acceptRuntimeEvent(event);
    } else {
      quarantineProtocolViolation(eventName, data);
    }
  });

  }

  socket.connect();
}

export function disconnectRuntime() {
  cancelReconnect();
  stopHeartbeat();
  if (socket.connected) {
    socket.disconnect();
  }
  connectionState = 'disconnected';
  useRuntimeStore.getState().setTelemetry({ connectionState });
  console.log('[BRIDGE] Bridge terminated.');
}

export function getConnectionState(): ConnectionState {
  return connectionState;
}

export function sendCommand(text: string, mode: 'auto' | 'raw' = 'auto') {
  if (!socket.connected) {
    console.error('[BRIDGE] Cannot send command — not connected.');
    return;
  }

  const event = createEvent('COMMAND_RECEIVED', { text, mode }, {
    source: 'orchestrator',
    trace_id: crypto.randomUUID(),
  });

  socket.emit('command', event);
}

export function approveCommand(commandId: string) {
  if (socket.connected) {
    socket.emit('approve_command', { command_id: commandId, mode: 'auto' });
  }
}

export function rejectCommand(commandId: string) {
  if (socket.connected) {
    socket.emit('reject_command', { command_id: commandId });
  }
}

export function cancelCommand(commandId?: string) {
  if (socket.connected) {
    socket.emit('cancel_command', commandId ? { command_id: commandId } : {});
  }
}

export function runMaintenanceScan() {
  if (socket.connected) {
    socket.emit('maintenance_scan', { read_only: true });
  }
}

export function requestMaintenanceAction(proposalId: string) {
  if (socket.connected) {
    socket.emit('request_maintenance_action', { proposal_id: proposalId });
  }
}

// ─── PROTOCOL QUARANTINE ──────────────────────────────────────────
// Non-protocol socket payloads are quarantined. The UI must not infer runtime
// state from legacy/raw events.
function quarantineProtocolViolation(eventName: string, data: unknown) {
  console.warn(`[BRIDGE/PROTOCOL] Dropped non-protocol event: ${eventName}`, data);
  useRuntimeStore.getState().addLog({
    level: 'WARN',
    message: `Dropped non-protocol socket event: ${eventName}`,
    color: 'text-warning',
  });
}
