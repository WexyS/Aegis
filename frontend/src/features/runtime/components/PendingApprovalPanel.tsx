"use client";

import React from 'react';
import { Ban, Check, ShieldAlert, Square, Wrench } from 'lucide-react';

import { approveCommand, cancelCommand, rejectCommand, runMaintenanceScan } from '@/lib/socket';
import { useRuntimeStore } from '@/store/useRuntimeStore';
import { CommandRecord, EnvironmentDiagnostics, EvidenceAudit } from '@/types/runtime';

export const PendingApprovalPanel = () => {
  const pendingApprovals = useRuntimeStore((state) => state.pendingApprovals);
  const activeCommand = useRuntimeStore((state) => state.activeCommand);
  const lastMaintenanceScan = useRuntimeStore((state) => state.lastMaintenanceScan);
  const environment = getEnvironmentDiagnostics(lastMaintenanceScan);
  const evidenceAudit = getEvidenceAudit(lastMaintenanceScan);

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-[10px] font-bold uppercase tracking-[0.2em] text-accent flex items-center gap-2">
          <ShieldAlert size={12} /> Pending Approval
        </h3>
        <button
          type="button"
          aria-label="Run read-only maintenance scan"
          onClick={runMaintenanceScan}
          className="p-1.5 rounded-md border border-white/10 bg-white/[0.03] text-foreground/55 hover:text-accent hover:border-accent/40 transition-colors"
          title="Run read-only maintenance scan"
        >
          <Wrench size={13} />
        </button>
      </div>

      <div className="space-y-3">
        {pendingApprovals.length === 0 ? (
          <div className="rounded-lg border border-white/10 bg-black/20 p-3 text-[11px] font-mono text-foreground/35">
            No backend pending approvals.
          </div>
        ) : (
          pendingApprovals.map((command) => (
            <ApprovalItem key={command.command_id} command={command} />
          ))
        )}
      </div>

      {activeCommand && (
        <div className="rounded-lg border border-warning/20 bg-warning/5 p-3 space-y-3">
          <div className="min-w-0">
            <div className="text-[9px] font-bold uppercase tracking-widest text-warning">Active Command</div>
            <div className="mt-1 truncate text-[12px] font-medium text-foreground/80">{activeCommand.text}</div>
          </div>
          <button
            type="button"
            onClick={() => cancelCommand(activeCommand.command_id)}
            className="w-full flex items-center justify-center gap-2 rounded-md border border-danger/30 bg-danger/10 px-3 py-2 text-[10px] font-bold uppercase tracking-widest text-danger hover:bg-danger/15 transition-colors"
          >
            <Square size={12} /> Cancel
          </button>
        </div>
      )}

      {lastMaintenanceScan && (
        <div className="rounded-lg border border-white/10 bg-black/20 p-3">
          <div className="text-[9px] font-bold uppercase tracking-widest text-foreground/40">Maintenance Scan</div>
          <div className="mt-2 flex items-center justify-between text-[10px] font-mono text-foreground/55">
            <span>{String(lastMaintenanceScan.scan_version ?? 'maintenance-scan/1')}</span>
            <span>{lastMaintenanceScan.read_only === true ? 'READ ONLY' : 'UNKNOWN'}</span>
          </div>
          {environment && <EnvironmentSummary diagnostics={environment} />}
          {evidenceAudit && <EvidenceAuditSummary audit={evidenceAudit} />}
        </div>
      )}
    </section>
  );
};

const EvidenceAuditSummary = ({ audit }: { audit: EvidenceAudit }) => {
  return (
    <div className="mt-3 border-t border-white/10 pt-3">
      <div className="flex items-center justify-between text-[9px] font-bold uppercase tracking-widest">
        <span className="text-foreground/40">Evidence</span>
        <span className={audit.status === 'ok' ? 'text-success' : 'text-warning'}>
          {audit.status}
        </span>
      </div>
      <div className="mt-2 grid grid-cols-2 gap-1.5">
        <AuditMetric label="actions" value={audit.action_count} />
        <AuditMetric label="backed" value={audit.evidence_backed_count} />
        <AuditMetric label="missing" value={audit.missing_evidence_count} tone={audit.missing_evidence_count > 0 ? 'warning' : 'success'} />
        <AuditMetric label="seq" value={audit.latest_sequence_num} />
      </div>
    </div>
  );
};

const AuditMetric = ({ label, value, tone = 'default' }: { label: string; value: number; tone?: 'default' | 'success' | 'warning' }) => {
  const valueColor = tone === 'success' ? 'text-success' : tone === 'warning' ? 'text-warning' : 'text-foreground/70';
  return (
    <div className="flex items-center justify-between rounded-md border border-white/10 bg-white/[0.02] px-2 py-1 text-[9px] font-mono">
      <span className="text-foreground/45">{label}</span>
      <span className={valueColor}>{value}</span>
    </div>
  );
};

const ApprovalItem = React.memo(({ command }: { command: CommandRecord }) => (
  <div className="rounded-lg border border-warning/25 bg-warning/5 p-3 space-y-3">
    <div className="space-y-1">
      <div className="flex items-center justify-between gap-3">
        <span className="text-[9px] font-bold uppercase tracking-widest text-warning">{command.risk_level} risk</span>
        <span className="text-[9px] font-mono text-foreground/35">{command.verification_state}</span>
      </div>
      <p className="text-[12px] font-medium leading-relaxed text-foreground/85">{command.text}</p>
      {command.reason && <p className="text-[10px] font-mono text-foreground/45">{command.reason}</p>}
    </div>
    <div className="grid grid-cols-2 gap-2">
      <button
        type="button"
        onClick={() => approveCommand(command.command_id)}
        className="flex items-center justify-center gap-2 rounded-md border border-success/30 bg-success/10 px-3 py-2 text-[10px] font-bold uppercase tracking-widest text-success hover:bg-success/15 transition-colors"
      >
        <Check size={12} /> Approve
      </button>
      <button
        type="button"
        onClick={() => rejectCommand(command.command_id)}
        className="flex items-center justify-center gap-2 rounded-md border border-white/10 bg-white/[0.03] px-3 py-2 text-[10px] font-bold uppercase tracking-widest text-foreground/55 hover:text-danger hover:border-danger/30 transition-colors"
      >
        <Ban size={12} /> Reject
      </button>
    </div>
  </div>
));

ApprovalItem.displayName = 'ApprovalItem';

const EnvironmentSummary = ({ diagnostics }: { diagnostics: EnvironmentDiagnostics }) => {
  const checks = ['python', 'git', 'node', 'npm', 'playwright']
    .map((name) => ({ name, status: String(diagnostics.checks?.[name]?.status ?? 'unknown') }));
  const recommendations = Array.isArray(diagnostics.recommendations) ? diagnostics.recommendations.slice(0, 2) : [];

  return (
    <div className="mt-3 border-t border-white/10 pt-3">
      <div className="flex items-center justify-between text-[9px] font-bold uppercase tracking-widest">
        <span className="text-foreground/40">Environment</span>
        <span className={diagnostics.overall_status === 'ok' ? 'text-success' : 'text-warning'}>
          {diagnostics.overall_status}
        </span>
      </div>
      <div className="mt-2 grid grid-cols-2 gap-1.5">
        {checks.map((check) => (
          <div key={check.name} className="flex items-center justify-between rounded-md border border-white/10 bg-white/[0.02] px-2 py-1 text-[9px] font-mono">
            <span className="text-foreground/45">{check.name}</span>
            <span className={check.status === 'ok' ? 'text-success' : 'text-warning'}>{check.status}</span>
          </div>
        ))}
      </div>
      {recommendations.length > 0 && (
        <div className="mt-2 space-y-1">
          {recommendations.map((item) => (
            <p key={item} className="text-[9px] font-mono leading-relaxed text-warning/85">{item}</p>
          ))}
        </div>
      )}
    </div>
  );
};

function getEnvironmentDiagnostics(report: Record<string, unknown> | null): EnvironmentDiagnostics | null {
  const checks = report?.checks;
  if (!checks || typeof checks !== 'object') return null;
  const environment = (checks as Record<string, unknown>).environment;
  if (!environment || typeof environment !== 'object') return null;
  const diagnostic = environment as Partial<EnvironmentDiagnostics>;
  if (diagnostic.scan_version !== 'environment-diagnostics/1') return null;
  return diagnostic as EnvironmentDiagnostics;
}

function getEvidenceAudit(report: Record<string, unknown> | null): EvidenceAudit | null {
  const checks = report?.checks;
  if (!checks || typeof checks !== 'object') return null;
  const evidence = (checks as Record<string, unknown>).evidence_audit;
  if (!evidence || typeof evidence !== 'object') return null;
  const audit = evidence as Partial<EvidenceAudit>;
  if (audit.scan_version !== 'evidence-audit/1') return null;
  return audit as EvidenceAudit;
}
