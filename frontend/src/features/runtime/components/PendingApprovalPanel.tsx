"use client";

import React, { useRef, useState } from 'react';
import { Ban, Check, ShieldAlert, Square, Wrench } from 'lucide-react';

import { EmptyState } from '@/components/EmptyState';
import { StatusBadge } from '@/components/StatusBadge';
import { resolveApprovalDecision, resolveClarificationDecision } from '@/lib/api';
import { cancelCommand, requestMaintenanceAction, runMaintenanceScan } from '@/lib/socket';
import { useRuntimeStore } from '@/store/useRuntimeStore';
import {
  ActionTimelineDiagnostics,
  CommandLifecycleDiagnostics,
  CommandRecord,
  EnvironmentDiagnostics,
  EvidenceAudit,
  MaintenanceActionProposal,
  MaintenanceFinding,
  NetworkPortsDiagnostics,
  ProcessResourcesDiagnostics,
  RuntimeHealth,
  RuntimeSnapshotDiagnostics,
  SystemResourcesDiagnostics,
  WebSocketDiagnostics,
} from '@/types/runtime';

export const PendingApprovalPanel = () => {
  const pendingApprovals = useRuntimeStore((state) => state.pendingApprovals);
  const pendingClarifications = useRuntimeStore((state) => state.pendingClarifications);
  const commandRecords = useRuntimeStore((state) => state.commandRecords);
  const activeCommand = useRuntimeStore((state) => state.activeCommand);
  const lastMaintenanceScan = useRuntimeStore((state) => state.lastMaintenanceScan);
  const resolvedDecisionRecords = commandRecords
    .filter((command) => hasResolutionMetadata(command))
    .slice(-4)
    .reverse();
  const runtimeHealth = getRuntimeHealth(lastMaintenanceScan);
  const commandLifecycle = getCommandLifecycle(lastMaintenanceScan);
  const runtimeSnapshot = getRuntimeSnapshot(lastMaintenanceScan);
  const websocket = getWebSocketDiagnostics(lastMaintenanceScan);
  const actionTimeline = getActionTimelineDiagnostics(lastMaintenanceScan);
  const systemResources = getSystemResources(lastMaintenanceScan);
  const processResources = getProcessResources(lastMaintenanceScan);
  const networkPorts = getNetworkPorts(lastMaintenanceScan);
  const environment = getEnvironmentDiagnostics(lastMaintenanceScan);
  const evidenceAudit = getEvidenceAudit(lastMaintenanceScan);
  const findings = getMaintenanceFindings(lastMaintenanceScan);
  const actionProposals = getMaintenanceActionProposals(lastMaintenanceScan);

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-[10px] font-bold uppercase tracking-[0.2em] text-accent flex items-center gap-2">
          <ShieldAlert size={12} /> Pending Decisions
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
        {pendingApprovals.length === 0 && pendingClarifications.length === 0 ? (
          <EmptyState title="No backend pending decisions" detail="Approval and clarification state is shown only from backend command records." icon={<ShieldAlert size={14} />} />
        ) : (
          <>
            {pendingApprovals.map((command) => (
              <ApprovalItem key={command.command_id} command={command} />
            ))}
            {pendingClarifications.map((command) => (
              <ClarificationItem key={command.command_id} command={command} />
            ))}
          </>
        )}
      </div>

      {resolvedDecisionRecords.length > 0 && (
        <div className="rounded-lg border border-white/10 bg-black/20 p-3 space-y-2">
          <div className="text-[9px] font-bold uppercase tracking-widest text-foreground/40">Recent Decision Results</div>
          {resolvedDecisionRecords.map((command) => (
            <ResolvedDecisionItem key={`${command.command_id}-${String(command.updated_at ?? command.status)}`} command={command} />
          ))}
        </div>
      )}

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
            <StatusBadge
              label={lastMaintenanceScan.read_only === true ? 'READ ONLY' : 'UNKNOWN MODE'}
              tone={lastMaintenanceScan.read_only === true ? 'info' : 'warning'}
            />
          </div>
          {runtimeHealth && <RuntimeHealthSummary health={runtimeHealth} />}
          {findings.length > 0 && <MaintenanceFindings findings={findings} />}
          {actionProposals.length > 0 && <MaintenanceActionProposals proposals={actionProposals} />}
          {(commandLifecycle || runtimeSnapshot || websocket || actionTimeline) && (
            <RuntimeTruthSummary
              commandLifecycle={commandLifecycle}
              runtimeSnapshot={runtimeSnapshot}
              websocket={websocket}
              actionTimeline={actionTimeline}
            />
          )}
          {(systemResources || processResources || networkPorts) && (
            <ResourceDiagnosticsSummary
              systemResources={systemResources}
              processResources={processResources}
              networkPorts={networkPorts}
            />
          )}
          {environment && <EnvironmentSummary diagnostics={environment} />}
          {evidenceAudit && <EvidenceAuditSummary audit={evidenceAudit} />}
        </div>
      )}
    </section>
  );
};

const RuntimeHealthSummary = ({ health }: { health: RuntimeHealth }) => {
  const statusTone = health.status === 'ok' ? 'text-success' : health.status === 'fail' ? 'text-danger' : 'text-warning';
  const attention = Array.isArray(health.attention) ? health.attention : [];
  const findingCount = numberish(health.finding_count);
  return (
    <div className="mt-3 border-t border-white/10 pt-3">
      <div className="flex items-center justify-between text-[9px] font-bold uppercase tracking-widest">
        <span className="text-foreground/40">Runtime Health</span>
        <span className={statusTone}>{health.status}</span>
      </div>
      <div className="mt-2 grid grid-cols-2 gap-1.5">
        {Object.entries(health.component_statuses || {}).slice(0, 12).map(([name, status]) => (
          <StatusMetric key={name} label={name} status={String(status)} />
        ))}
      </div>
      {attention.length > 0 && (
        <p className="mt-2 truncate text-[9px] font-mono text-warning/85">{attention.join(', ')}</p>
      )}
      {findingCount !== null && findingCount > 0 && (
        <p className="mt-2 text-[9px] font-mono text-foreground/45">{findingCount} backend findings</p>
      )}
      {typeof health.action_proposal_count === 'number' && health.action_proposal_count > 0 && (
        <p className="mt-1 text-[9px] font-mono text-foreground/45">{health.action_proposal_count} approval-gated proposals</p>
      )}
      {typeof health.pending_action_proposal_count === 'number' && health.pending_action_proposal_count > 0 && (
        <p className="mt-1 text-[9px] font-mono text-warning/80">{health.pending_action_proposal_count} proposals in approval lifecycle</p>
      )}
    </div>
  );
};

const MaintenanceFindings = ({ findings }: { findings: MaintenanceFinding[] }) => (
  <div className="mt-3 border-t border-white/10 pt-3">
    <div className="flex items-center justify-between text-[9px] font-bold uppercase tracking-widest">
      <span className="text-foreground/40">Findings</span>
      <span className="text-foreground/45">{findings.length}</span>
    </div>
    <div className="mt-2 space-y-1.5">
      {findings.slice(0, 3).map((finding) => (
        <div key={finding.finding_id} className="rounded-md border border-white/10 bg-white/[0.02] px-2 py-1.5">
          <div className="flex items-center justify-between gap-2 text-[9px] font-mono">
            <span className="truncate text-foreground/45">{finding.category}</span>
            <span className={findingSeverityTone(finding.severity)}>{finding.severity}</span>
          </div>
          <p className="mt-1 line-clamp-2 text-[9px] font-mono leading-relaxed text-foreground/65">{finding.reason}</p>
          <p className="mt-1 truncate text-[8px] font-mono text-foreground/35">{finding.source}</p>
        </div>
      ))}
    </div>
  </div>
);

const MaintenanceActionProposals = ({ proposals }: { proposals: MaintenanceActionProposal[] }) => (
  <div className="mt-3 border-t border-white/10 pt-3">
    <div className="flex items-center justify-between text-[9px] font-bold uppercase tracking-widest">
      <span className="text-foreground/40">Action Proposals</span>
      <span className="text-warning">{proposals.length}</span>
    </div>
    <div className="mt-2 space-y-1.5">
      {proposals.slice(0, 3).map((proposal) => (
        <div key={proposal.proposal_id} className="rounded-md border border-warning/20 bg-warning/[0.03] px-2 py-1.5">
          <div className="flex items-center justify-between gap-2 text-[9px] font-mono">
            <span className="truncate text-foreground/70">{proposal.title}</span>
            <span className="text-warning">{proposal.status}</span>
          </div>
          <p className="mt-1 line-clamp-2 text-[9px] font-mono leading-relaxed text-foreground/55">{proposal.reason}</p>
          <p className="mt-1 truncate text-[8px] font-mono text-foreground/35">{proposal.source}</p>
          <ProposalPreviewDetails proposal={proposal} />
          {proposal.lifecycle?.command_id && (
            <p className="mt-1 truncate text-[8px] font-mono text-foreground/35">
              {proposal.lifecycle.command_status} / {proposal.lifecycle.verification_state} / {proposal.lifecycle.command_id}
            </p>
          )}
          <button
            type="button"
            onClick={() => requestMaintenanceAction(proposal.proposal_id)}
            disabled={proposal.status !== 'proposed'}
            className="mt-2 w-full rounded-md border border-warning/30 bg-warning/10 px-2 py-1.5 text-[9px] font-bold uppercase tracking-widest text-warning hover:bg-warning/15 disabled:cursor-not-allowed disabled:border-white/10 disabled:bg-white/[0.02] disabled:text-foreground/35 transition-colors"
          >
            {proposal.status === 'proposed' ? 'Request Approval' : 'Lifecycle Active'}
          </button>
        </div>
      ))}
    </div>
  </div>
);

function findingSeverityTone(severity: string): string {
  if (severity === 'fail') return 'text-danger';
  if (severity === 'warning') return 'text-warning';
  return 'text-foreground/45';
}

function riskBorderStyle(risk: string): string {
  switch (risk) {
    case 'critical': return 'border-red-500/30 bg-red-500/5';
    case 'high': return 'border-orange-500/25 bg-orange-500/5';
    case 'medium': return 'border-amber-500/20 bg-amber-500/5';
    case 'low': return 'border-emerald-500/20 bg-emerald-500/5';
    default: return 'border-white/10 bg-white/[0.02]';
  }
}

function riskBadgeStyle(risk: string): string {
  switch (risk) {
    case 'critical': return 'bg-red-500/15 border-red-500/30 text-red-300';
    case 'high': return 'bg-orange-500/15 border-orange-500/30 text-orange-300';
    case 'medium': return 'bg-amber-500/15 border-amber-500/30 text-amber-300';
    case 'low': return 'bg-emerald-500/15 border-emerald-500/30 text-emerald-300';
    default: return 'bg-slate-500/10 border-slate-500/20 text-slate-300';
  }
}

function runtimeTruthLabel(runtimeSnapshot: RuntimeSnapshotDiagnostics | null): string {
  if (!runtimeSnapshot) return 'unknown';
  return runtimeSnapshot.sequence_aligned === false ? 'drift' : 'synced';
}

function runtimeTruthTone(runtimeSnapshot: RuntimeSnapshotDiagnostics | null): string {
  if (!runtimeSnapshot) return 'text-foreground/45';
  return runtimeSnapshot.sequence_aligned === false ? 'text-warning' : 'text-success';
}

const RuntimeTruthSummary = ({
  commandLifecycle,
  runtimeSnapshot,
  websocket,
  actionTimeline,
}: {
  commandLifecycle: CommandLifecycleDiagnostics | null;
  runtimeSnapshot: RuntimeSnapshotDiagnostics | null;
  websocket: WebSocketDiagnostics | null;
  actionTimeline: ActionTimelineDiagnostics | null;
}) => (
  <div className="mt-3 border-t border-white/10 pt-3">
    <div className="flex items-center justify-between text-[9px] font-bold uppercase tracking-widest">
      <span className="text-foreground/40">Runtime Truth</span>
      <span className={runtimeTruthTone(runtimeSnapshot)}>{runtimeTruthLabel(runtimeSnapshot)}</span>
    </div>
    <div className="mt-2 grid grid-cols-2 gap-1.5">
      {commandLifecycle && <AuditMetric label="pending" value={commandLifecycle.pending_count} tone={commandLifecycle.pending_count > 0 ? 'warning' : 'default'} />}
      {commandLifecycle && <AuditMetric label="active" value={commandLifecycle.active_count} tone={commandLifecycle.active_count > 0 ? 'warning' : 'default'} />}
      {websocket && typeof websocket.connected_clients === 'number' && <AuditMetric label="clients" value={websocket.connected_clients} />}
      {(websocket?.queue_depth !== null && websocket?.queue_depth !== undefined) ? (
        <AuditMetric label="queue" value={websocket.queue_depth} />
      ) : runtimeSnapshot ? (
        <AuditMetric label="queue" value={runtimeSnapshot.queue_depth} />
      ) : null}
      {actionTimeline && <AuditMetric label="actions" value={actionTimeline.action_count} />}
      {actionTimeline && <AuditMetric label="errors" value={actionTimeline.error_count} tone={actionTimeline.error_count > 0 ? 'warning' : 'default'} />}
    </div>
    {!runtimeSnapshot && (
      <p className="mt-2 text-[9px] font-mono text-foreground/35">Runtime snapshot diagnostics unavailable.</p>
    )}
  </div>
);

const ResourceDiagnosticsSummary = ({
  systemResources,
  processResources,
  networkPorts,
}: {
  systemResources: SystemResourcesDiagnostics | null;
  processResources: ProcessResourcesDiagnostics | null;
  networkPorts: NetworkPortsDiagnostics | null;
}) => {
  const cpuPercent = numberish(systemResources?.cpu_percent);
  const memoryPercent = numberish(systemResources?.memory?.percent);
  const diskPercent = numberish(systemResources?.disk?.percent);
  const uptimeSeconds = numberish(systemResources?.uptime_seconds);
  const processCount = numberish(processResources?.process_count);
  const skippedCount = numberish(processResources?.skipped_count);
  const ports = Array.isArray(networkPorts?.ports) ? networkPorts.ports : [];
  const listeningPorts = ports.filter((port) => port.status === 'listening');
  const topProcess = Array.isArray(processResources?.top_by_memory) ? processResources.top_by_memory[0] : undefined;
  const status = worstDiagnosticStatus(systemResources?.status, processResources?.status, networkPorts?.status);

  return (
    <div className="mt-3 border-t border-white/10 pt-3">
      <div className="flex items-center justify-between text-[9px] font-bold uppercase tracking-widest">
        <span className="text-foreground/40">Resources</span>
        <span className={statusTone(status)}>{status}</span>
      </div>
      <div className="mt-2 grid grid-cols-2 gap-1.5">
        {cpuPercent !== null && <ResourceMetric label="cpu" value={`${cpuPercent.toFixed(1)}%`} tone={cpuPercent >= 90 ? 'warning' : 'success'} />}
        {memoryPercent !== null && <ResourceMetric label="memory" value={`${memoryPercent.toFixed(1)}%`} tone={memoryPercent >= 90 ? 'warning' : 'success'} />}
        {diskPercent !== null && <ResourceMetric label="disk" value={`${diskPercent.toFixed(1)}%`} tone={diskPercent >= 90 ? 'warning' : 'success'} />}
        {uptimeSeconds !== null && <ResourceMetric label="uptime" value={formatDuration(uptimeSeconds)} />}
        {processCount !== null && <ResourceMetric label="processes" value={String(processCount)} />}
        {skippedCount !== null && <ResourceMetric label="skipped" value={String(skippedCount)} tone={skippedCount > 0 ? 'warning' : 'success'} />}
        {networkPorts && <ResourceMetric label="ports" value={`${listeningPorts.length}/${ports.length}`} tone={listeningPorts.length > 0 ? 'warning' : 'default'} />}
      </div>
      {topProcess && (
        <p className="mt-2 truncate text-[9px] font-mono text-foreground/45">
          top memory: {topProcess.name} / PID {topProcess.pid} / {formatBytes(topProcess.memory_rss_bytes)}
        </p>
      )}
      {listeningPorts.length > 0 && (
        <p className="mt-1 truncate text-[9px] font-mono text-foreground/45">
          listening: {listeningPorts.map((port) => `${port.port}:${port.listeners[0]?.process_name ?? port.listeners[0]?.pid ?? 'unknown'}`).join(', ')}
        </p>
      )}
    </div>
  );
};

const EvidenceAuditSummary = ({ audit }: { audit: EvidenceAudit }) => {
  const statusTone = audit.status === 'ok' ? 'text-success' : audit.status === 'fail' ? 'text-danger' : 'text-warning';
  const verifiedActionCount = numberish(audit.verified_action_count);
  const checkFailCount = numberish(audit.check_fail_count);
  const criticalFailureCount = numberish(audit.critical_failure_count);
  const criticalFailures = Array.isArray(audit.critical_failures) ? audit.critical_failures : [];
  return (
    <div className="mt-3 border-t border-white/10 pt-3">
      <div className="flex items-center justify-between text-[9px] font-bold uppercase tracking-widest">
        <span className="text-foreground/40">Evidence</span>
        <span className={statusTone}>{audit.status}</span>
      </div>
      <div className="mt-2 grid grid-cols-2 gap-1.5">
        <AuditMetric label="actions" value={audit.action_count} />
        <AuditMetric label="backed" value={audit.evidence_backed_count} />
        <AuditMetric label="missing" value={audit.missing_evidence_count} tone={audit.missing_evidence_count > 0 ? 'warning' : 'success'} />
        <AuditMetric label="verified" value={countLabel(verifiedActionCount)} tone={verifiedActionCount !== null && verifiedActionCount > 0 ? 'success' : 'default'} />
        <AuditMetric label="check fail" value={countLabel(checkFailCount)} tone={checkFailCount !== null && checkFailCount > 0 ? 'danger' : 'default'} />
        <AuditMetric label="critical" value={countLabel(criticalFailureCount)} tone={criticalFailureCount !== null && criticalFailureCount > 0 ? 'danger' : 'default'} />
      </div>
      {criticalFailures.length > 0 && (
        <div className="mt-2 space-y-1">
          {criticalFailures.slice(0, 2).map((failure, index) => (
            <p key={`${String(failure.action_id ?? index)}-${String(failure.check_name ?? index)}`} className="truncate text-[9px] font-mono text-danger/85">
              {String(failure.action ?? 'action')}:{String(failure.check_name ?? 'check')}
            </p>
          ))}
        </div>
      )}
    </div>
  );
};

const StatusMetric = ({ label, status }: { label: string; status: string }) => {
  const valueColor = status === 'ok' ? 'text-success' : status === 'fail' ? 'text-danger' : status === 'unknown' ? 'text-foreground/45' : 'text-warning';
  return (
    <div className="flex items-center justify-between rounded-md border border-white/10 bg-white/[0.02] px-2 py-1 text-[9px] font-mono">
      <span className="max-w-[88px] truncate text-foreground/45">{label}</span>
      <span className={valueColor}>{status}</span>
    </div>
  );
};

const AuditMetric = ({ label, value, tone = 'default' }: { label: string; value: number | string; tone?: 'default' | 'success' | 'warning' | 'danger' }) => {
  const valueColor = tone === 'success' ? 'text-success' : tone === 'warning' ? 'text-warning' : tone === 'danger' ? 'text-danger' : 'text-foreground/70';
  return (
    <div className="flex items-center justify-between rounded-md border border-white/10 bg-white/[0.02] px-2 py-1 text-[9px] font-mono">
      <span className="text-foreground/45">{label}</span>
      <span className={valueColor}>{value}</span>
    </div>
  );
};

const ResourceMetric = ({ label, value, tone = 'default' }: { label: string; value: string; tone?: 'default' | 'success' | 'warning' | 'danger' }) => {
  const valueColor = tone === 'success' ? 'text-success' : tone === 'warning' ? 'text-warning' : tone === 'danger' ? 'text-danger' : 'text-foreground/70';
  return (
    <div className="flex items-center justify-between rounded-md border border-white/10 bg-white/[0.02] px-2 py-1 text-[9px] font-mono">
      <span className="text-foreground/45">{label}</span>
      <span className={valueColor}>{value}</span>
    </div>
  );
};

const ApprovalItem = React.memo(({ command }: { command: CommandRecord }) => {
  const upsertCommand = useRuntimeStore((state) => state.upsertCommand);
  const addLog = useRuntimeStore((state) => state.addLog);
  const [resolving, setResolving] = useState<'grant' | 'deny' | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inFlightRef = useRef(false);
  const proposal = getMaintenanceProposalFromCommand(command);
  const resources = Array.isArray(proposal?.affected_resources) ? proposal.affected_resources : [];
  const evidenceRefs = Array.isArray(proposal?.evidence_refs) ? proposal.evidence_refs : [];
  const approvalId = getMetadataString(command, 'approval_id') || command.command_id;
  const resumeAllowed = command.metadata?.resume_allowed === true;
  const nonExecutable = command.metadata?.resume_allowed === false || isQuarantinedClickDecision(command);
  const isPending = command.status === 'pending_approval';
  const controlsDisabled = resolving !== null || !isPending;
  const resolve = async (decision: 'grant' | 'deny') => {
    if (inFlightRef.current || resolving !== null) return;
    if (!isPending) {
      setError(`Approval is no longer pending: ${command.status}`);
      return;
    }
    inFlightRef.current = true;
    setResolving(decision);
    setError(null);
    try {
      const updated = await resolveApprovalDecision(approvalId, decision);
      upsertCommand(updated);
      addLog({
        level: decision === 'grant' ? 'INFO' : 'WARN',
        message: decision === 'grant'
          ? `Approval grant recorded by backend: ${updated.status}`
          : `Approval denied: ${updated.reason || 'operator decision'}`,
        color: decision === 'grant' ? 'text-accent' : 'text-warning',
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Approval resolve failed';
      setError(message);
      addLog({ level: 'ERR', message: `Approval resolve failed: ${message}`, color: 'text-danger' });
    } finally {
      inFlightRef.current = false;
      setResolving(null);
    }
  };

  return (
    <div className={`rounded-lg border p-3 space-y-3 ${riskBorderStyle(command.risk_level)}`}>
      <div className="space-y-1">
        <div className="flex items-center justify-between gap-3">
          <span className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${riskBadgeStyle(command.risk_level)}`}>{command.risk_level} risk</span>
          <span className="text-[9px] font-mono text-foreground/35">{command.verification_state}</span>
        </div>
        <p className="text-[12px] font-medium leading-relaxed text-foreground/85">{command.text}</p>
        {command.reason && <p className="text-[10px] font-mono text-foreground/45">{command.reason}</p>}
        <div className="rounded-md border border-white/10 bg-black/15 px-2 py-1.5 text-[9px] font-mono leading-relaxed text-foreground/45">
          <div className="flex items-center justify-between gap-2">
            <span className="truncate">approval id: {approvalId}</span>
            <span className={resumeAllowed ? 'text-warning' : 'text-foreground/45'}>
              {resumeAllowed ? 'backend-gated state update' : 'state-only / non-executing'}
            </span>
          </div>
          {nonExecutable && (
            <p className="mt-1 text-warning/80">
              Grant records the decision only; quarantined or unresolved click actions are not executed by this control.
            </p>
          )}
          {!isPending && (
            <p className="mt-1 text-warning/80">
              This approval is no longer pending; controls are disabled until the backend snapshot changes.
            </p>
          )}
        </div>
        {proposal && (
          <div className="rounded-md border border-white/10 bg-black/15 px-2 py-1.5">
            <div className="flex items-center justify-between gap-2 text-[9px] font-mono">
              <span className="truncate text-foreground/55">{proposal.action}</span>
              <span className="text-warning">{proposal.status}</span>
            </div>
            <p className="mt-1 line-clamp-2 text-[9px] font-mono leading-relaxed text-foreground/60">{proposal.reason}</p>
            {resources.length > 0 && (
              <p className="mt-1 truncate text-[8px] font-mono text-foreground/35">
                {resources.map((resource) => String(resource.path ?? resource.type ?? 'resource')).join(', ')}
              </p>
            )}
            {evidenceRefs.length > 0 && (
              <p className="mt-1 truncate text-[8px] font-mono text-foreground/35">{evidenceRefs.join(', ')}</p>
            )}
            <ProposalPreviewDetails proposal={proposal} compact />
          </div>
        )}
        {error && (
          <p className="rounded-md border border-danger/30 bg-danger/10 px-2 py-1.5 text-[9px] font-mono text-danger">
            {error}
          </p>
        )}
      </div>
      <div className="grid grid-cols-2 gap-2">
        <button
          type="button"
          onClick={() => void resolve('grant')}
          disabled={controlsDisabled}
          aria-busy={resolving === 'grant'}
          className="flex items-center justify-center gap-2 rounded-md border border-success/30 bg-success/10 px-3 py-2 text-[10px] font-bold uppercase tracking-widest text-success hover:bg-success/15 disabled:cursor-not-allowed disabled:opacity-50 transition-colors"
        >
          <Check size={12} /> {resolving === 'grant' ? 'Resolving' : 'Grant'}
        </button>
        <button
          type="button"
          onClick={() => void resolve('deny')}
          disabled={controlsDisabled}
          aria-busy={resolving === 'deny'}
          className="flex items-center justify-center gap-2 rounded-md border border-white/10 bg-white/[0.03] px-3 py-2 text-[10px] font-bold uppercase tracking-widest text-foreground/55 hover:text-danger hover:border-danger/30 disabled:cursor-not-allowed disabled:opacity-50 transition-colors"
        >
          <Ban size={12} /> {resolving === 'deny' ? 'Resolving' : 'Deny'}
        </button>
      </div>
    </div>
  );
});

ApprovalItem.displayName = 'ApprovalItem';

const ClarificationItem = React.memo(({ command }: { command: CommandRecord }) => {
  const upsertCommand = useRuntimeStore((state) => state.upsertCommand);
  const addLog = useRuntimeStore((state) => state.addLog);
  const [answer, setAnswer] = useState('');
  const [resolving, setResolving] = useState<'submit' | 'cancel' | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inFlightRef = useRef(false);
  const clarificationId = getMetadataString(command, 'clarification_id') || command.command_id;
  const isPending = command.status === 'waiting_for_clarification';
  const hasAnswer = answer.trim().length > 0;

  const resolve = async (mode: 'submit' | 'cancel') => {
    if (inFlightRef.current || resolving !== null) return;
    if (!isPending) {
      setError(`Clarification is no longer pending: ${command.status}`);
      return;
    }
    if (mode === 'submit' && !hasAnswer) {
      setError('Enter a clarification response before resolving, or cancel the clarification.');
      return;
    }
    inFlightRef.current = true;
    setResolving(mode);
    setError(null);
    try {
      const updated = await resolveClarificationDecision(clarificationId, {
        answer: mode === 'submit' ? answer.trim() : undefined,
        cancelled: mode === 'cancel',
      });
      upsertCommand(updated);
      addLog({
        level: 'WARN',
        message: `Clarification ${mode === 'cancel' ? 'cancelled' : 'resolved'} without execution: ${updated.status}`,
        color: 'text-warning',
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Clarification resolve failed';
      setError(message);
      addLog({ level: 'ERR', message: `Clarification resolve failed: ${message}`, color: 'text-danger' });
    } finally {
      inFlightRef.current = false;
      setResolving(null);
    }
  };

  return (
    <div className={`rounded-lg border p-3 space-y-3 ${riskBorderStyle(command.risk_level)}`}>
      <div className="space-y-1">
        <div className="flex items-center justify-between gap-3">
          <span className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${riskBadgeStyle(command.risk_level)}`}>{command.risk_level} risk</span>
          <span className="text-[9px] font-mono text-warning">clarification</span>
        </div>
        <p className="text-[12px] font-medium leading-relaxed text-foreground/85">{command.text}</p>
        {command.reason && <p className="text-[10px] font-mono text-foreground/45">{command.reason}</p>}
        <div className="rounded-md border border-warning/20 bg-warning/[0.04] px-2 py-1.5 text-[9px] font-mono leading-relaxed text-warning/80">
          Clarification resolve is state-only in backend v1. Submitting an answer records the decision and does not reparse or execute the command.
        </div>
        {!isPending && (
          <p className="rounded-md border border-warning/20 bg-warning/[0.04] px-2 py-1.5 text-[9px] font-mono text-warning/80">
            This clarification is no longer pending; controls are disabled until the backend snapshot changes.
          </p>
        )}
        <textarea
          value={answer}
          onChange={(event) => setAnswer(event.target.value)}
          placeholder="Clarification response"
          disabled={resolving !== null || !isPending}
          className="min-h-[72px] w-full resize-y rounded-md border border-white/10 bg-black/20 px-2 py-2 text-[11px] text-foreground/80 outline-none placeholder:text-foreground/30 focus:border-accent/40"
        />
        {!hasAnswer && isPending && (
          <p className="text-[9px] font-mono text-foreground/40">
            Enter a response to resolve, or cancel the clarification without execution.
          </p>
        )}
        {error && (
          <p className="rounded-md border border-danger/30 bg-danger/10 px-2 py-1.5 text-[9px] font-mono text-danger">
            {error}
          </p>
        )}
      </div>
      <div className="grid grid-cols-2 gap-2">
        <button
          type="button"
          onClick={() => void resolve('submit')}
          disabled={resolving !== null || !isPending || !hasAnswer}
          aria-busy={resolving === 'submit'}
          className="flex items-center justify-center gap-2 rounded-md border border-warning/30 bg-warning/10 px-3 py-2 text-[10px] font-bold uppercase tracking-widest text-warning hover:bg-warning/15 disabled:cursor-not-allowed disabled:opacity-50 transition-colors"
        >
          <Check size={12} /> {resolving === 'submit' ? 'Resolving' : 'Submit'}
        </button>
        <button
          type="button"
          onClick={() => void resolve('cancel')}
          disabled={resolving !== null || !isPending}
          aria-busy={resolving === 'cancel'}
          className="flex items-center justify-center gap-2 rounded-md border border-white/10 bg-white/[0.03] px-3 py-2 text-[10px] font-bold uppercase tracking-widest text-foreground/55 hover:text-danger hover:border-danger/30 disabled:cursor-not-allowed disabled:opacity-50 transition-colors"
        >
          <Ban size={12} /> {resolving === 'cancel' ? 'Resolving' : 'Cancel'}
        </button>
      </div>
    </div>
  );
});

ClarificationItem.displayName = 'ClarificationItem';

const ResolvedDecisionItem = ({ command }: { command: CommandRecord }) => {
  const approvalStatus = getMetadataString(command, 'approval_resolution_status');
  const clarificationStatus = getMetadataString(command, 'clarification_resolution_status');
  const status = approvalStatus || clarificationStatus || command.status;
  const tone = command.status === 'rejected' || command.status === 'cancelled' || command.status === 'blocked' ? 'text-warning' : 'text-foreground/70';
  const mutationLabel = Object.prototype.hasOwnProperty.call(command.metadata ?? {}, 'mutation_performed')
    ? String(command.metadata?.mutation_performed)
    : 'Unavailable';

  return (
    <div className="rounded-md border border-white/10 bg-white/[0.02] px-2 py-1.5">
      <div className="flex items-center justify-between gap-2 text-[9px] font-mono">
        <span className="truncate text-foreground/55">{command.text}</span>
        <span className={tone}>{status}</span>
      </div>
      <p className="mt-1 truncate text-[8px] font-mono text-foreground/35">
        {command.status} / mutation={mutationLabel} / {command.command_id}
      </p>
    </div>
  );
};

const ProposalPreviewDetails = ({ proposal, compact = false }: { proposal: MaintenanceActionProposal; compact?: boolean }) => {
  const preview = getRecord(proposal.dry_run_preview);
  const resources = Array.isArray(proposal.affected_resources) ? proposal.affected_resources : [];
  const evidenceRefs = Array.isArray(proposal.evidence_refs) ? proposal.evidence_refs : [];
  const safetyGate = getRecord(proposal.safety_gate);
  const mutationIfApproved = getRecord(preview?.mutation_if_approved);
  const expectedOutcome = getRecord(proposal.expected_outcome);
  const preconditions = Array.isArray(preview?.preconditions) ? preview.preconditions : [];
  const target = String(preview?.target ?? mutationIfApproved?.path ?? resources[0]?.path ?? '');
  const operation = String(preview?.operation ?? mutationIfApproved?.operation ?? resources[0]?.operation ?? '');
  const previewVersion = typeof preview?.preview_version === 'string' ? preview.preview_version : null;
  const gateVersion = typeof safetyGate?.gate_version === 'string' ? safetyGate.gate_version : null;

  if (!preview && !resources.length && !safetyGate) return null;

  return (
    <div className={compact ? 'mt-2 space-y-1' : 'mt-2 rounded-md border border-white/10 bg-black/15 px-2 py-1.5 space-y-1'}>
      {previewVersion && (
        <div className="flex items-center justify-between gap-2 text-[8px] font-mono">
          <span className="text-foreground/35">dry-run preview</span>
          <span className="text-foreground/45">{previewVersion}</span>
        </div>
      )}
      {(operation || target) && (
        <p className="truncate text-[8px] font-mono text-foreground/45">
          {operation}{operation && target ? ' ' : ''}{target}
        </p>
      )}
      {resources.length > 0 && !compact && (
        <p className="truncate text-[8px] font-mono text-foreground/35">
          resources: {resources.map((resource) => formatResource(resource)).join(', ')}
        </p>
      )}
      {gateVersion && (
        <p className="truncate text-[8px] font-mono text-success/70">gate: {gateVersion}</p>
      )}
      {preconditions.length > 0 && !compact && (
        <p className="truncate text-[8px] font-mono text-foreground/35">
          preflight: {preconditions.map((check) => String(getRecord(check)?.check_name ?? 'check')).join(', ')}
        </p>
      )}
      {Object.keys(expectedOutcome || {}).length > 0 && !compact && (
        <p className="truncate text-[8px] font-mono text-foreground/35">
          expected: {Object.entries(expectedOutcome || {}).map(([key, value]) => `${key}=${String(value)}`).join(', ')}
        </p>
      )}
      {evidenceRefs.length > 0 && !compact && (
        <p className="truncate text-[8px] font-mono text-foreground/35">evidence: {evidenceRefs.join(', ')}</p>
      )}
    </div>
  );
};

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

function getCommandLifecycle(report: Record<string, unknown> | null): CommandLifecycleDiagnostics | null {
  const lifecycle = getCheck(report, 'command_lifecycle') as Partial<CommandLifecycleDiagnostics> | null;
  if (!lifecycle || lifecycle.scan_version !== 'command-lifecycle/1') return null;
  return lifecycle as CommandLifecycleDiagnostics;
}

function getRuntimeSnapshot(report: Record<string, unknown> | null): RuntimeSnapshotDiagnostics | null {
  const snapshot = getCheck(report, 'runtime_snapshot') as Partial<RuntimeSnapshotDiagnostics> | null;
  if (!snapshot || snapshot.scan_version !== 'runtime-snapshot/1') return null;
  return snapshot as RuntimeSnapshotDiagnostics;
}

function getWebSocketDiagnostics(report: Record<string, unknown> | null): WebSocketDiagnostics | null {
  const websocket = getCheck(report, 'websocket') as Partial<WebSocketDiagnostics> | null;
  if (!websocket || websocket.scan_version !== 'websocket-runtime/1') return null;
  return websocket as WebSocketDiagnostics;
}

function getActionTimelineDiagnostics(report: Record<string, unknown> | null): ActionTimelineDiagnostics | null {
  const timeline = getCheck(report, 'action_timeline') as Partial<ActionTimelineDiagnostics> | null;
  if (!timeline || timeline.scan_version !== 'action-timeline-health/1') return null;
  return timeline as ActionTimelineDiagnostics;
}

function getSystemResources(report: Record<string, unknown> | null): SystemResourcesDiagnostics | null {
  const resources = getCheck(report, 'system_resources') as Partial<SystemResourcesDiagnostics> | null;
  if (!resources || resources.scan_version !== 'system-resources/1') return null;
  return resources as SystemResourcesDiagnostics;
}

function getProcessResources(report: Record<string, unknown> | null): ProcessResourcesDiagnostics | null {
  const resources = getCheck(report, 'process_resources') as Partial<ProcessResourcesDiagnostics> | null;
  if (!resources || resources.scan_version !== 'process-resources/1') return null;
  return resources as ProcessResourcesDiagnostics;
}

function getNetworkPorts(report: Record<string, unknown> | null): NetworkPortsDiagnostics | null {
  const ports = getCheck(report, 'network_ports') as Partial<NetworkPortsDiagnostics> | null;
  if (!ports || ports.scan_version !== 'network-ports/1') return null;
  return ports as NetworkPortsDiagnostics;
}

const EnvironmentSummary = ({ diagnostics }: { diagnostics: EnvironmentDiagnostics }) => {
  const checks = ['python', 'git', 'node', 'npm', 'playwright']
    .map((name) => ({ name, status: String(diagnostics.checks?.[name]?.status ?? 'unknown') }));

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
    </div>
  );
};

function getEnvironmentDiagnostics(report: Record<string, unknown> | null): EnvironmentDiagnostics | null {
  const environment = getCheck(report, 'environment');
  if (!environment) return null;
  const diagnostic = environment as Partial<EnvironmentDiagnostics>;
  if (diagnostic.scan_version !== 'environment-diagnostics/1') return null;
  return diagnostic as EnvironmentDiagnostics;
}

function getEvidenceAudit(report: Record<string, unknown> | null): EvidenceAudit | null {
  const evidence = getCheck(report, 'evidence_audit');
  if (!evidence) return null;
  const audit = evidence as Partial<EvidenceAudit>;
  if (audit.scan_version !== 'evidence-audit/1' && audit.scan_version !== 'evidence-audit/2') return null;
  return audit as EvidenceAudit;
}

function getMaintenanceFindings(report: Record<string, unknown> | null): MaintenanceFinding[] {
  const findings = report?.findings;
  if (!Array.isArray(findings)) return [];
  return findings.filter((finding): finding is MaintenanceFinding => (
    Boolean(finding)
    && typeof finding === 'object'
    && typeof (finding as Partial<MaintenanceFinding>).finding_id === 'string'
    && typeof (finding as Partial<MaintenanceFinding>).category === 'string'
    && typeof (finding as Partial<MaintenanceFinding>).severity === 'string'
    && typeof (finding as Partial<MaintenanceFinding>).source === 'string'
    && typeof (finding as Partial<MaintenanceFinding>).reason === 'string'
    && typeof (finding as Partial<MaintenanceFinding>).recommendation === 'string'
    && (finding as Partial<MaintenanceFinding>).read_only === true
  ));
}

function getMaintenanceActionProposals(report: Record<string, unknown> | null): MaintenanceActionProposal[] {
  const proposals = report?.action_proposals;
  if (!Array.isArray(proposals)) return [];
  return proposals.filter((proposal): proposal is MaintenanceActionProposal => (
    Boolean(proposal)
    && typeof proposal === 'object'
    && typeof (proposal as Partial<MaintenanceActionProposal>).proposal_version === 'string'
    && typeof (proposal as Partial<MaintenanceActionProposal>).proposal_id === 'string'
    && typeof (proposal as Partial<MaintenanceActionProposal>).action === 'string'
    && typeof (proposal as Partial<MaintenanceActionProposal>).title === 'string'
    && typeof (proposal as Partial<MaintenanceActionProposal>).reason === 'string'
    && typeof (proposal as Partial<MaintenanceActionProposal>).source === 'string'
    && typeof (proposal as Partial<MaintenanceActionProposal>).risk_level === 'string'
    && (proposal as Partial<MaintenanceActionProposal>).requires_approval === true
    && typeof (proposal as Partial<MaintenanceActionProposal>).approval_text === 'string'
    && (proposal as Partial<MaintenanceActionProposal>).read_only === true
    && typeof (proposal as Partial<MaintenanceActionProposal>).status === 'string'
  ));
}

function getMaintenanceProposalFromCommand(command: CommandRecord): MaintenanceActionProposal | null {
  const metadata = command.metadata;
  if (!metadata || metadata.kind !== 'maintenance_action') return null;
  const proposal = metadata.proposal;
  if (!proposal || typeof proposal !== 'object') return null;
  const candidate = proposal as Partial<MaintenanceActionProposal>;
  if (
    typeof candidate.proposal_id !== 'string'
    || typeof candidate.action !== 'string'
    || typeof candidate.title !== 'string'
    || typeof candidate.reason !== 'string'
    || typeof candidate.status !== 'string'
  ) {
    return null;
  }
  return candidate as MaintenanceActionProposal;
}

function getMetadataString(command: CommandRecord, key: string): string | null {
  const value = command.metadata?.[key];
  return typeof value === 'string' && value.length > 0 ? value : null;
}

function hasResolutionMetadata(command: CommandRecord): boolean {
  return Boolean(
    getMetadataString(command, 'approval_resolution_status')
    || getMetadataString(command, 'clarification_resolution_status')
  );
}

function isQuarantinedClickDecision(command: CommandRecord): boolean {
  const policyRule = getMetadataString(command, 'policy_rule') || '';
  const decisionStatus = getMetadataString(command, 'decision_status') || '';
  return (
    policyRule.includes('generic_click.quarantined')
    || policyRule.includes('target_resolution_missing')
    || (decisionStatus.length > 0 && command.text.toLowerCase().includes('click'))
  );
}

function getRecord(value: unknown): Record<string, unknown> | null {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : null;
}

function formatResource(resource: Record<string, unknown>): string {
  const operation = typeof resource.operation === 'string' ? resource.operation : null;
  const path = typeof resource.path === 'string' ? resource.path : null;
  const type = typeof resource.type === 'string' ? resource.type : 'resource';
  if (operation && path) return `${operation}:${path}`;
  return path ?? type;
}

function numberish(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

function countLabel(value: number | null): string {
  return value === null ? 'Unavailable' : String(value);
}

function formatBytes(value: number): string {
  if (value >= 1024 * 1024 * 1024) return `${(value / (1024 * 1024 * 1024)).toFixed(1)}GB`;
  if (value >= 1024 * 1024) return `${(value / (1024 * 1024)).toFixed(1)}MB`;
  if (value >= 1024) return `${(value / 1024).toFixed(1)}KB`;
  return `${value}B`;
}

function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  if (hours >= 24) return `${Math.floor(hours / 24)}d`;
  if (hours > 0) return `${hours}h`;
  return `${Math.floor(seconds / 60)}m`;
}

function worstDiagnosticStatus(...statuses: Array<string | null | undefined>): string {
  const rank: Record<string, number> = { ok: 0, unknown: 1, warning: 2, fail: 3 };
  return statuses
    .filter((status): status is string => typeof status === 'string' && status.length > 0)
    .sort((a, b) => (rank[b] ?? 1) - (rank[a] ?? 1))[0] ?? 'unknown';
}

function statusTone(status: string): string {
  if (status === 'ok') return 'text-success';
  if (status === 'fail') return 'text-danger';
  if (status === 'warning') return 'text-warning';
  return 'text-foreground/45';
}
