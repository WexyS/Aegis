import { create } from 'zustand';
import { ActionTimelineItem, AppRegistrySnapshot, CommandRecord, RuntimeStatus, RuntimeStep, TelemetryData, ToolRegistrySnapshot } from '@/types/runtime';
import { RuntimeState, VALID_TRANSITIONS } from '@/types/fsm';

export interface SystemLog {
  id: string;
  timestamp: string;
  level: 'SYS' | 'INFO' | 'OK' | 'EXEC' | 'TOOL' | 'DBUG' | 'WARN' | 'ERR';
  message: string;
  color?: string;
  duration?: string;
}

export interface RuntimeStoreState extends TelemetryData {
  steps: RuntimeStep[];
  systemLogs: SystemLog[];
  commandRecords: CommandRecord[];
  pendingApprovals: CommandRecord[];
  pendingClarifications: CommandRecord[];
  activeCommand: CommandRecord | null;
  lastMaintenanceScan: Record<string, unknown> | null;
  appRegistry: AppRegistrySnapshot | null;
  toolRegistry: ToolRegistrySnapshot | null;
  visionFeedEnabled: boolean;
  currentState: RuntimeState;
  isExecuting: boolean;
  recoveryDepth: number;
  maxRecoveryDepth: number;
  addStep: (step: RuntimeStep) => void;
  upsertStep: (step: RuntimeStep) => void;
  updateStep: (id: string, updates: Partial<RuntimeStep>) => void;
  addLog: (log: Omit<SystemLog, 'id' | 'timestamp'>) => void;
  setTelemetry: (data: Partial<TelemetryData>) => void;
  upsertCommand: (command: CommandRecord) => void;
  syncCommandSnapshot: (commands: any) => void;
  syncActionTimelineSnapshot: (timeline: unknown) => void;
  setMaintenanceScan: (report: Record<string, unknown> | null) => void;
  setAppRegistry: (registry: AppRegistrySnapshot | null) => void;
  setToolRegistry: (registry: ToolRegistrySnapshot | null) => void;
  setVisionFeedEnabled: (enabled: boolean) => void;
  transitionTo: (newState: RuntimeState, payload?: any) => void;
  applyBackendTransition: (fromState: RuntimeState | undefined, newState: RuntimeState, payload?: any) => void;
  syncBackendSnapshot: (newState: RuntimeState, payload?: any) => void;
  acquireLock: () => boolean;
  releaseLock: () => void;
  incrementRecovery: () => boolean; // Bounded complexity: check recovery budget
  clearSteps: () => void;
}

const RUNNING_STATES = new Set<RuntimeState>([
  RuntimeState.THINKING,
  RuntimeState.PLANNING,
  RuntimeState.EXECUTING,
  RuntimeState.VERIFYING,
  RuntimeState.RECOVERING,
]);

function isLegalTransition(fromState: RuntimeState, toState: RuntimeState): boolean {
  if (fromState === toState) return true;
  return VALID_TRANSITIONS.some(t =>
    (Array.isArray(t.from) ? t.from.includes(fromState) : t.from === fromState) &&
    (Array.isArray(t.to) ? t.to.includes(toState) : t.to === toState)
  );
}

function getStatePatch(newState: RuntimeState): Partial<RuntimeStoreState> {
  const patch: Partial<RuntimeStoreState> = {
    currentState: newState,
    isExecuting: RUNNING_STATES.has(newState),
  };

  if ([RuntimeState.COMPLETED, RuntimeState.IDLE, RuntimeState.FAILED].includes(newState)) {
    patch.recoveryDepth = 0;
    patch.recoveryBudget = 1.0;
  }

  return patch;
}

function stringValue(value: unknown): string | null {
  return typeof value === 'string' && value.trim().length > 0 ? value : null;
}

function numberValue(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

function timelineStatus(item: ActionTimelineItem): RuntimeStatus {
  const status = String(item.status || '').toLowerCase();
  if (Object.values(RuntimeStatus).includes(status as RuntimeStatus)) {
    return status as RuntimeStatus;
  }
  if (['blocked', 'failed', 'error', 'rejected', 'cancelled', 'approval_denied'].includes(status)) {
    return RuntimeStatus.ERROR;
  }
  return RuntimeStatus.PENDING;
}

function timelineStepId(item: ActionTimelineItem, index: number): string {
  const kind = stringValue(item.kind);
  const candidates = [
    item.action_id,
    item.timeline_id,
    item.approval_id,
    item.clarification_id,
    item.blocked_id,
    item.sequence_num === null || item.sequence_num === undefined ? null : `seq-${item.sequence_num}`,
    item.command_id && kind ? `${item.command_id}-${kind}` : item.command_id,
  ];
  const raw = candidates.map(stringValue).find(Boolean);
  if (raw) return kind && !raw.startsWith(`${kind}:`) ? `${kind}:${raw}` : raw;
  return `timeline-fallback-${index}`;
}

function timelineComponent(item: ActionTimelineItem): string {
  if (item.not_executed || item.kind || item.terminal_non_executed) {
    return 'guard';
  }
  return stringValue(item.tool) || 'executor';
}

function timelineLabel(item: ActionTimelineItem): string {
  if (item.kind) return item.kind.replace(/_/g, ' ');
  return stringValue(item.tool) || 'executor';
}

function timelineDetail(item: ActionTimelineItem, status: RuntimeStatus): string {
  const target = stringValue(item.target);
  if (target) return target;

  const reason = stringValue(item.reason);
  const kind = stringValue(item.kind);
  const state = String(item.status || item.command_status || item.decision || '').toLowerCase();
  if (item.not_executed || item.terminal_non_executed || kind) {
    if (kind === 'approval_requested') return reason || 'Approval requested; execution is paused.';
    if (kind === 'approval_resolved') {
      if (state.includes('denied') || state.includes('rejected')) return reason || 'Approval denied; command was not executed.';
      if (state.includes('granted')) return reason || 'Approval granted; waiting for backend policy-gated resume.';
      return reason || 'Approval resolved as lifecycle state; execution is not implied.';
    }
    if (kind === 'clarification_requested') return reason || 'Clarification requested; execution is paused.';
    if (kind === 'clarification_resolved') return reason || 'Clarification resolved as state-only; command was not executed.';
    if (kind === 'blocked_by_policy') return reason || 'Blocked by policy; command was not executed.';
    return reason || 'Lifecycle state recorded without execution.';
  }

  const tool = stringValue(item.tool) || 'executor';
  if (status === RuntimeStatus.ACTIVE) return `Executing ${tool}`;
  if (status === RuntimeStatus.SUCCESS) return `${tool} completed`;
  if (status === RuntimeStatus.ERROR) return `${tool} failed or unverified`;
  return `${tool} pending`;
}

export const useRuntimeStore = create<RuntimeStoreState>((set, get) => ({
  steps: [],
  systemLogs: [],
  commandRecords: [],
  pendingApprovals: [],
  pendingClarifications: [],
  activeCommand: null,
  lastMaintenanceScan: null,
  appRegistry: null,
  toolRegistry: null,
  visionFeedEnabled: false,
  currentState: RuntimeState.IDLE,
  isExecuting: false,
  recoveryDepth: 0,
  maxRecoveryDepth: 5, // Governance: Hard limit on self-healing loops
  determinismScore: undefined,
  recoveryBudget: 1.0,
  vramUsage: 'Unavailable',
  activeApp: 'None',
  activeModel: 'Unavailable',
  connectionState: 'disconnected',
  cpuPercent: undefined,
  memoryPercent: undefined,
  uptimeSeconds: undefined,
  ioThroughput: undefined,
  websocketClients: undefined,
  eventThroughput: undefined,
  wsRttMs: undefined,
  lastSequenceNum: undefined,
  runtimeIntegrity: 'unverified',

  acquireLock: () => {
    if (get().isExecuting) {
      console.warn('[DETERMINISM] Concurrent Action Blocked: Mutex Active.');
      return false;
    }
    set({ isExecuting: true });
    return true;
  },

  releaseLock: () => set({ isExecuting: false }),

  incrementRecovery: () => {
    const nextDepth = get().recoveryDepth + 1;
    if (nextDepth > get().maxRecoveryDepth) {
      console.error('[GOVERNANCE] Recovery Budget Exhausted. Escalating to Critical Failure.');
      get().transitionTo(RuntimeState.FAILED, { reason: 'Recovery depth limit reached' });
      return false;
    }
    set({ recoveryDepth: nextDepth, recoveryBudget: 1 - (nextDepth / get().maxRecoveryDepth) });
    return true;
  },

  addStep: (step) => set((state) => ({ steps: [...state.steps, step] })),

  upsertStep: (step) => set((state) => {
    const existing = state.steps.find((item) => item.id === step.id);
    if (!existing) return { steps: [...state.steps, step] };
    return {
      steps: state.steps.map((item) => item.id === step.id ? { ...item, ...step } : item),
    };
  }),
  
  updateStep: (id, updates) => set((state) => ({
    steps: state.steps.map(s => s.id === id ? { ...s, ...updates } : s)
  })),

  addLog: (log) => set((state) => {
    const newLog = {
      ...log,
      id: crypto.randomUUID(),
      timestamp: new Date().toLocaleTimeString('en-US', { hour12: false, hour: 'numeric', minute: 'numeric', second: 'numeric', fractionalSecondDigits: 1 }),
    };
    // Keep max 100 logs
    const newLogs = [...state.systemLogs, newLog];
    if (newLogs.length > 100) newLogs.shift();
    return { systemLogs: newLogs };
  }),

  setTelemetry: (data) => set((state) => ({ ...state, ...data })),

  upsertCommand: (command) => set((state) => {
    const records = [...state.commandRecords.filter((item) => item.command_id !== command.command_id), command].slice(-50);
    return {
      commandRecords: records,
      pendingApprovals: records.filter((item) => item.status === 'pending_approval'),
      pendingClarifications: records.filter((item) => item.status === 'waiting_for_clarification'),
      activeCommand: command.active ? command : records.find((item) => item.active) ?? null,
    };
  }),

  syncCommandSnapshot: (commands) => {
    if (!commands || typeof commands !== 'object') return;
    const records = Array.isArray(commands.records) ? commands.records as CommandRecord[] : [];
    const pending = Array.isArray(commands.pending_approvals) ? commands.pending_approvals as CommandRecord[] : [];
    const pendingClarifications = Array.isArray(commands.pending_clarifications) ? commands.pending_clarifications as CommandRecord[] : [];
    const active = commands.active_command as CommandRecord | null | undefined;
    set({
      commandRecords: records,
      pendingApprovals: pending,
      pendingClarifications,
      activeCommand: active ?? null,
    });
  },

  syncActionTimelineSnapshot: (timeline) => {
    if (!Array.isArray(timeline)) return;
    const steps = timeline.map((item: ActionTimelineItem, index): RuntimeStep => {
      const status = timelineStatus(item);
      const eventTime = numberValue(item.completed_at) ?? numberValue(item.started_at) ?? numberValue(item.timestamp);
      const metrics = ((item.latency_ms !== null && item.latency_ms !== undefined) || item.execution_evidence)
        ? {
            latency_ms: item.latency_ms ?? undefined,
            retries: item.execution_evidence?.retry_count ?? 0,
            determinism: item.execution_evidence?.verification_state === 'verified' ? 1.0 : undefined,
          }
        : undefined;
      return {
        id: timelineStepId(item, index),
        component: timelineComponent(item),
        status,
        label: timelineLabel(item),
        detail: timelineDetail(item, status),
        timestamp: typeof eventTime === 'number' ? new Date(eventTime).toLocaleTimeString() : '',
        executionEvidence: item.execution_evidence ?? undefined,
        metrics,
      };
    });
    set({ steps });
  },

  setMaintenanceScan: (report) => set({ lastMaintenanceScan: report }),
  setAppRegistry: (registry) => set({ appRegistry: registry }),
  setToolRegistry: (registry) => set({ toolRegistry: registry }),
  setVisionFeedEnabled: () => set({ visionFeedEnabled: false }),

  transitionTo: (newState, payload = {}) => {
    const { currentState } = get();
    
    // Strict Transition Locking
    if (!isLegalTransition(currentState, newState)) {
      console.warn(`[FSM] Forbidden Transition: ${currentState} -> ${newState}`);
      return;
    }

    set(getStatePatch(newState));
  },

  applyBackendTransition: (fromState, newState, payload = {}) => {
    const { currentState } = get();
    const authoritativeFrom = fromState ?? currentState;

    if (!isLegalTransition(authoritativeFrom, newState)) {
      const reason = payload.reason ? ` (${payload.reason})` : '';
      console.error(`[FSM] Backend emitted illegal transition: ${authoritativeFrom} -> ${newState}${reason}`);
      get().addLog({
        level: 'ERR',
        message: `Backend FSM breach: ${authoritativeFrom} -> ${newState}`,
        color: 'text-danger',
      });
      return;
    } else if (currentState !== authoritativeFrom && currentState !== newState) {
      console.warn(`[FSM] Projection resync: local ${currentState}, backend ${authoritativeFrom} -> ${newState}`);
      get().addLog({
        level: 'WARN',
        message: `FSM projection resynced: local ${currentState}, backend ${authoritativeFrom}`,
        color: 'text-warning',
      });
    }

    set(getStatePatch(newState));
  },

  syncBackendSnapshot: (newState) => {
    const { currentState } = get();
    if (currentState !== newState) {
      get().addLog({
        level: 'SYS',
        message: `Runtime snapshot state: ${newState}`,
        color: 'text-accent',
      });
    }
    set(getStatePatch(newState));
  },

  clearSteps: () => set({ steps: [] }),
}));
