"use client";

import React from 'react';
import { Activity, CheckCircle2, CircleDashed, ShieldAlert } from 'lucide-react';

import { StatusBadge } from '@/components/StatusBadge';
import { useRuntimeStore } from '@/store/useRuntimeStore';
import { RuntimeState } from '@/types/fsm';
import { RuntimeHealth, RuntimeSnapshotDiagnostics } from '@/types/runtime';

type OverviewStatus = {
  label: string;
  tone: 'success' | 'info' | 'warning' | 'danger' | 'unknown';
  reason: string;
};

export const SystemOverview = () => {
  const connectionState = useRuntimeStore((state) => state.connectionState ?? 'disconnected');
  const currentState = useRuntimeStore((state) => state.currentState);
  const pendingApprovals = useRuntimeStore((state) => state.pendingApprovals);
  const activeCommand = useRuntimeStore((state) => state.activeCommand);
  const lastMaintenanceScan = useRuntimeStore((state) => state.lastMaintenanceScan);
  const runtimeIntegrity = useRuntimeStore((state) => state.runtimeIntegrity ?? 'unverified');
  const lastSequenceNum = useRuntimeStore((state) => state.lastSequenceNum);
  const recoveryBudget = useRuntimeStore((state) => state.recoveryBudget);

  const runtimeHealth = getRuntimeHealth(lastMaintenanceScan);
  const runtimeSnapshot = getRuntimeSnapshot(lastMaintenanceScan);
  const overviewStatus = deriveOverviewStatus({
    connectionState,
    currentState,
    pendingCount: pendingApprovals.length,
    hasActiveCommand: Boolean(activeCommand),
    runtimeHealth,
    runtimeSnapshot,
  });

  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <h3 className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.2em] text-accent">
          <Activity size={12} /> System Overview
        </h3>
        <StatusBadge label={overviewStatus.label} tone={overviewStatus.tone} icon={statusIcon(overviewStatus.tone)} />
      </div>

      <div className="rounded-lg border border-white/10 bg-black/20 p-3.5">
        <div className="text-[10px] font-mono leading-relaxed text-foreground/45">
          {overviewStatus.reason}
        </div>
        <div className="mt-3 grid grid-cols-2 gap-2">
          <OverviewMetric label="FSM" value={currentState ?? 'unknown'} tone={stateTone(currentState)} />
          <OverviewMetric label="Socket" value={connectionState} tone={connectionState === 'connected' ? 'info' : 'unknown'} />
          <OverviewMetric label="Approvals" value={String(pendingApprovals.length)} tone={pendingApprovals.length > 0 ? 'warning' : 'info'} />
          <OverviewMetric label="Active" value={activeCommand ? 'yes' : 'no'} tone={activeCommand ? 'warning' : 'info'} />
          <OverviewMetric label="Integrity" value={runtimeIntegrity} tone={integrityTone(runtimeIntegrity)} />
          <OverviewMetric label="Sequence" value={lastSequenceNum === undefined ? 'Unavailable' : String(lastSequenceNum)} tone={lastSequenceNum === undefined ? 'unknown' : 'info'} />
          <OverviewMetric label="Runtime Scan" value={runtimeHealth?.status ?? 'Unavailable'} tone={healthTone(runtimeHealth?.status)} />
          <OverviewMetric label="Snapshot" value={snapshotLabel(runtimeSnapshot)} tone={snapshotTone(runtimeSnapshot)} />
          <OverviewMetric label="Recovery" value={typeof recoveryBudget === 'number' ? `${(recoveryBudget * 100).toFixed(0)}%` : 'Unavailable'} tone="info" />
        </div>
      </div>
    </section>
  );
};

const OverviewMetric = ({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone: 'success' | 'info' | 'warning' | 'danger' | 'unknown';
}) => (
  <div className="min-w-0 rounded-md border border-white/10 bg-white/[0.02] px-2 py-1.5">
    <div className="text-[8px] font-bold uppercase tracking-widest text-foreground/35">{label}</div>
    <div className={`mt-1 truncate text-[10px] font-mono ${textTone(tone)}`}>{value}</div>
  </div>
);

function deriveOverviewStatus({
  connectionState,
  currentState,
  pendingCount,
  hasActiveCommand,
  runtimeHealth,
  runtimeSnapshot,
}: {
  connectionState: string;
  currentState: RuntimeState;
  pendingCount: number;
  hasActiveCommand: boolean;
  runtimeHealth: RuntimeHealth | null;
  runtimeSnapshot: RuntimeSnapshotDiagnostics | null;
}): OverviewStatus {
  if (currentState === RuntimeState.FAILED || runtimeHealth?.status === 'fail') {
    return { label: 'risk', tone: 'danger', reason: 'Backend state or maintenance health reports a failed condition.' };
  }
  if (pendingCount > 0 || hasActiveCommand || currentState === RuntimeState.RECOVERING || runtimeHealth?.status === 'warning') {
    return { label: 'attention', tone: 'warning', reason: 'Runtime has pending, active, recovering, or warning state that needs operator attention.' };
  }
  if (connectionState !== 'connected') {
    return { label: 'unknown', tone: 'unknown', reason: 'Backend connection is not established; runtime health cannot be inferred.' };
  }
  if (!runtimeHealth || !runtimeSnapshot) {
    return { label: 'unknown', tone: 'unknown', reason: 'No complete backend maintenance diagnostics are available yet.' };
  }
  if (runtimeSnapshot.sequence_aligned === false) {
    return { label: 'attention', tone: 'warning', reason: 'Runtime snapshot reports journal/snapshot sequence drift.' };
  }
  if (currentState === RuntimeState.IDLE) {
    return { label: 'idle', tone: 'info', reason: 'Runtime is idle. This is neutral, not proof of whole-system health.' };
  }
  if (runtimeHealth.status === 'ok' && runtimeSnapshot.status === 'ok') {
    return { label: 'ok', tone: 'success', reason: 'Backend maintenance diagnostics explicitly report ok status.' };
  }
  return { label: 'unknown', tone: 'unknown', reason: 'No explicit backend ok signal is available.' };
}

function statusIcon(tone: OverviewStatus['tone']): React.ReactNode {
  if (tone === 'success') return <CheckCircle2 size={11} />;
  if (tone === 'danger' || tone === 'warning') return <ShieldAlert size={11} />;
  if (tone === 'info') return <Activity size={11} />;
  return <CircleDashed size={11} />;
}

function stateTone(state: RuntimeState): OverviewStatus['tone'] {
  if (state === RuntimeState.FAILED) return 'danger';
  if ([RuntimeState.THINKING, RuntimeState.PLANNING, RuntimeState.EXECUTING, RuntimeState.VERIFYING, RuntimeState.RECOVERING].includes(state)) return 'warning';
  return 'info';
}

function integrityTone(integrity: string): OverviewStatus['tone'] {
  if (integrity === 'unverified' || integrity === 'resyncing') return 'warning';
  if (integrity === 'session-reset') return 'unknown';
  return 'info';
}

function healthTone(status?: string): OverviewStatus['tone'] {
  if (status === 'ok') return 'success';
  if (status === 'fail') return 'danger';
  if (status === 'warning') return 'warning';
  return 'unknown';
}

function snapshotTone(snapshot: RuntimeSnapshotDiagnostics | null): OverviewStatus['tone'] {
  if (!snapshot) return 'unknown';
  if (snapshot.sequence_aligned === false || snapshot.status === 'warning') return 'warning';
  if (snapshot.status === 'fail') return 'danger';
  if (snapshot.status === 'ok') return 'success';
  return 'unknown';
}

function snapshotLabel(snapshot: RuntimeSnapshotDiagnostics | null): string {
  if (!snapshot) return 'Unavailable';
  if (snapshot.sequence_aligned === false) return 'drift';
  return snapshot.status ?? 'unknown';
}

function textTone(tone: OverviewStatus['tone']): string {
  if (tone === 'success') return 'text-success';
  if (tone === 'warning') return 'text-warning';
  if (tone === 'danger') return 'text-danger';
  if (tone === 'info') return 'text-accent';
  return 'text-foreground/45';
}

function getCheck(report: Record<string, unknown> | null, name: string): Record<string, unknown> | null {
  const checks = report?.checks;
  if (!checks || typeof checks !== 'object') return null;
  const check = (checks as Record<string, unknown>)[name];
  if (!check || typeof check !== 'object') return null;
  return check as Record<string, unknown>;
}

function getRuntimeHealth(report: Record<string, unknown> | null): RuntimeHealth | null {
  const summary = report?.summary;
  const health = (summary && typeof summary === 'object' ? summary : getCheck(report, 'runtime_health')) as Partial<RuntimeHealth> | null;
  if (!health || health.scan_version !== 'runtime-health/1') return null;
  return health as RuntimeHealth;
}

function getRuntimeSnapshot(report: Record<string, unknown> | null): RuntimeSnapshotDiagnostics | null {
  const snapshot = getCheck(report, 'runtime_snapshot') as Partial<RuntimeSnapshotDiagnostics> | null;
  if (!snapshot || snapshot.scan_version !== 'runtime-snapshot/1') return null;
  return snapshot as RuntimeSnapshotDiagnostics;
}
