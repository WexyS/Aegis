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
  activeCommand: CommandRecord | null;
  lastMaintenanceScan: Record<string, unknown> | null;
  appRegistry: AppRegistrySnapshot | null;
  toolRegistry: ToolRegistrySnapshot | null;
  currentState: RuntimeState;
  isExecuting: boolean;
  recoveryDepth: number;
  maxRecoveryDepth: number;
  addStep: (step: RuntimeStep) => void;
  updateStep: (id: string, updates: Partial<RuntimeStep>) => void;
  addLog: (log: Omit<SystemLog, 'id' | 'timestamp'>) => void;
  setTelemetry: (data: Partial<TelemetryData>) => void;
  upsertCommand: (command: CommandRecord) => void;
  syncCommandSnapshot: (commands: any) => void;
  syncActionTimelineSnapshot: (timeline: unknown) => void;
  setMaintenanceScan: (report: Record<string, unknown> | null) => void;
  setAppRegistry: (registry: AppRegistrySnapshot | null) => void;
  setToolRegistry: (registry: ToolRegistrySnapshot | null) => void;
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

export const useRuntimeStore = create<RuntimeStoreState>((set, get) => ({
  steps: [],
  systemLogs: [],
  commandRecords: [],
  pendingApprovals: [],
  activeCommand: null,
  lastMaintenanceScan: null,
  appRegistry: null,
  toolRegistry: null,
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
      activeCommand: command.active ? command : records.find((item) => item.active) ?? null,
    };
  }),

  syncCommandSnapshot: (commands) => {
    if (!commands || typeof commands !== 'object') return;
    const records = Array.isArray(commands.records) ? commands.records as CommandRecord[] : [];
    const pending = Array.isArray(commands.pending_approvals) ? commands.pending_approvals as CommandRecord[] : [];
    const active = commands.active_command as CommandRecord | null | undefined;
    set({
      commandRecords: records,
      pendingApprovals: pending,
      activeCommand: active ?? null,
    });
  },

  syncActionTimelineSnapshot: (timeline) => {
    if (!Array.isArray(timeline)) return;
    const steps = timeline.map((item: ActionTimelineItem): RuntimeStep => {
      const status = Object.values(RuntimeStatus).includes(item.status as RuntimeStatus)
        ? item.status as RuntimeStatus
        : RuntimeStatus.PENDING;
      const eventTime = item.completed_at ?? item.started_at;
      const metrics = ((item.latency_ms !== null && item.latency_ms !== undefined) || item.execution_evidence)
        ? {
            latency_ms: item.latency_ms ?? undefined,
            retries: item.execution_evidence?.retry_count ?? 0,
            determinism: item.execution_evidence?.verification_state === 'verified' ? 1.0 : undefined,
          }
        : undefined;
      return {
        id: item.action_id,
        component: item.tool || 'executor',
        status,
        label: item.tool || 'executor',
        detail: item.target || `Executing ${item.tool || 'executor'}`,
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
