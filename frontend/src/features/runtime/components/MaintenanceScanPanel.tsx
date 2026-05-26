"use client";

import { Wrench } from 'lucide-react';

import { EmptyState } from '@/components/EmptyState';
import { StatusBadge } from '@/components/StatusBadge';
import { requestMaintenanceAction, runMaintenanceScan } from '@/lib/socket';
import { useRuntimeStore } from '@/store/useRuntimeStore';
import {
  ActionTimelineDiagnostics,
  AppDiscoveryDiagnostics,
  AppDiscoveryEntry,
  CommandLifecycleDiagnostics,
  EnvironmentDiagnostics,
  EvidenceAudit,
  MaintenanceActionProposal,
  MaintenanceFinding,
  NetworkPortsDiagnostics,
  PendingDecisionHygieneDiagnostics,
  ProcessResourcesDiagnostics,
  RuntimeHealth,
  RuntimeSnapshotDiagnostics,
  SystemResourcesDiagnostics,
  WebSocketDiagnostics,
} from '@/types/runtime';

export const MaintenanceScanPanel = () => {
  const lastMaintenanceScan = useRuntimeStore((state) => state.lastMaintenanceScan);
  const runtimeHealth = getRuntimeHealth(lastMaintenanceScan);
  const commandLifecycle = getCommandLifecycle(lastMaintenanceScan);
  const pendingDecisionHygiene = getPendingDecisionHygiene(lastMaintenanceScan);
  const runtimeSnapshot = getRuntimeSnapshot(lastMaintenanceScan);
  const websocket = getWebSocketDiagnostics(lastMaintenanceScan);
  const actionTimeline = getActionTimelineDiagnostics(lastMaintenanceScan);
  const systemResources = getSystemResources(lastMaintenanceScan);
  const processResources = getProcessResources(lastMaintenanceScan);
  const networkPorts = getNetworkPorts(lastMaintenanceScan);
  const appDiscovery = getAppDiscoveryDiagnostics(lastMaintenanceScan);
  const environment = getEnvironmentDiagnostics(lastMaintenanceScan);
  const evidenceAudit = getEvidenceAudit(lastMaintenanceScan);
  const findings = getMaintenanceFindings(lastMaintenanceScan);
  const actionProposals = getMaintenanceActionProposals(lastMaintenanceScan);

  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-[10px] font-bold uppercase tracking-[0.2em] text-accent flex items-center gap-2">
          <Wrench size={12} /> Maintenance Scan
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

      {!lastMaintenanceScan ? (
        <EmptyState title="No maintenance scan loaded" detail="Read-only diagnostics appear after the backend publishes a maintenance scan." icon={<Wrench size={14} />} />
      ) : (
        <div className="rounded-lg border border-white/10 bg-black/20 p-3">
          <div className="flex items-center justify-between text-[10px] font-mono text-foreground/55">
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
          <PendingDecisionHygieneSummary diagnostics={pendingDecisionHygiene} />
          <AppDiscoverySummary diagnostics={appDiscovery} />
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
      {commandLifecycle && <StatusMetric label="commands" status={commandLifecycle.status} />}
      {runtimeSnapshot && <StatusMetric label="snapshot" status={runtimeSnapshot.status} />}
      {websocket && <StatusMetric label="websocket" status={websocket.status} />}
      {actionTimeline && <StatusMetric label="timeline" status={actionTimeline.status} />}
    </div>
    {commandLifecycle && (
      <p className="mt-2 truncate text-[9px] font-mono text-foreground/45">
        active {commandLifecycle.active_count} / pending {commandLifecycle.pending_count} / records {commandLifecycle.record_count}
      </p>
    )}
  </div>
);

const PendingDecisionHygieneSummary = ({ diagnostics }: { diagnostics: PendingDecisionHygieneDiagnostics | null }) => {
  const currentSessionCount = numberish(diagnostics?.current_session_pending_count);
  const restoredCount = numberish(diagnostics?.restored_unresolved_count);
  const staleRestoredCount = numberish(diagnostics?.stale_restored_unresolved_count);
  const unknownAgeCount = numberish(diagnostics?.unknown_age_count);
  const approvalCount = numberish(diagnostics?.approval_count);
  const clarificationCount = numberish(diagnostics?.clarification_count);
  const resumableCount = numberish(diagnostics?.resumable_count);
  const stateOnlyCount = numberish(diagnostics?.state_only_count);
  const nonExecutingCount = numberish(diagnostics?.non_executing_count);
  const topCommands = Array.isArray(diagnostics?.top_command_texts) ? diagnostics.top_command_texts : [];
  const sources = diagnostics?.source_distribution && typeof diagnostics.source_distribution === 'object'
    ? Object.entries(diagnostics.source_distribution).filter(([, value]) => typeof value === 'number')
    : [];

  return (
    <div className="mt-3 border-t border-white/10 pt-3">
      <div className="flex items-center justify-between text-[9px] font-bold uppercase tracking-widest">
        <span className="text-foreground/40">Pending Decision Hygiene</span>
        <span className={diagnostics ? statusTone(diagnostics.status) : 'text-foreground/45'}>
          {diagnostics?.status ?? 'unavailable'}
        </span>
      </div>
      {!diagnostics ? (
        <p className="mt-2 text-[9px] font-mono text-foreground/35">
          Pending decision hygiene diagnostics unavailable from this backend scan.
        </p>
      ) : (
        <>
          <div className="mt-2 grid grid-cols-2 gap-1.5">
            <AuditMetric label="current" value={countLabel(currentSessionCount)} />
            <AuditMetric label="restored" value={countLabel(restoredCount)} tone={(restoredCount ?? 0) > 0 ? 'warning' : 'default'} />
            <AuditMetric label="stale restored" value={countLabel(staleRestoredCount)} tone={(staleRestoredCount ?? 0) > 0 ? 'warning' : 'default'} />
            <AuditMetric label="unknown age" value={countLabel(unknownAgeCount)} tone={(unknownAgeCount ?? 0) > 0 ? 'warning' : 'default'} />
            <AuditMetric label="approvals" value={countLabel(approvalCount)} />
            <AuditMetric label="clarifications" value={countLabel(clarificationCount)} />
            <AuditMetric label="resumable" value={countLabel(resumableCount)} tone={(resumableCount ?? 0) > 0 ? 'warning' : 'default'} />
            <AuditMetric label="state-only" value={countLabel(stateOnlyCount)} />
            <AuditMetric label="non-executing" value={countLabel(nonExecutingCount)} />
          </div>
          <p className="mt-2 text-[9px] font-mono text-foreground/45">
            {diagnostics.mutation_performed === false ? 'Read-only; no mutation performed.' : 'Mutation status unknown.'}
          </p>
          {diagnostics.recommendation && (
            <p className="mt-1 line-clamp-2 text-[9px] font-mono leading-relaxed text-warning/80">
              {diagnostics.recommendation}
            </p>
          )}
          {resumableCount !== null && resumableCount > 0 && (
            <p className="mt-1 text-[9px] font-mono text-warning/75">
              Resumable means backend-gated if granted; it is not a recommendation.
            </p>
          )}
          {topCommands.length > 0 && (
            <div className="mt-2 space-y-1">
              {topCommands.slice(0, 3).map((item) => (
                <div key={item.value} className="flex items-center justify-between gap-2 rounded-md border border-white/10 bg-white/[0.02] px-2 py-1 text-[9px] font-mono">
                  <span className="truncate text-foreground/55">{item.value}</span>
                  <span className="text-warning">{item.count}</span>
                </div>
              ))}
            </div>
          )}
          {sources.length > 0 && (
            <p className="mt-2 truncate text-[9px] font-mono text-foreground/35">
              sources: {sources.map(([source, value]) => `${source}=${value}`).join(', ')}
            </p>
          )}
          {diagnostics.safety?.approval_grant_exposed === false && (
            <p className="mt-1 text-[9px] font-mono text-foreground/35">
              Hygiene display exposes no approval grant action.
            </p>
          )}
        </>
      )}
    </div>
  );
};

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

const AppDiscoverySummary = ({ diagnostics }: { diagnostics: AppDiscoveryDiagnostics | null }) => {
  const entries = diagnostics?.entries ?? [];
  const visibleEntries = orderAppDiscoveryEntries(entries).slice(0, 4);
  const ambiguousCount = entries.filter((entry) => appDiscoveryState(entry) === 'ambiguous').length;
  const missingPathCount = entries.filter((entry) => hasMissingExecutablePath(entry)).length;
  const windowOnlyCount = entries.filter((entry) => isWindowOnlyAppDiscovery(entry)).length;
  const possibleCount = entries.filter((entry) => entry.deterministic_verification_possible === true).length;

  return (
    <div className="mt-3 border-t border-white/10 pt-3">
      <div className="flex items-center justify-between text-[9px] font-bold uppercase tracking-widest">
        <span className="text-foreground/40">App Discovery</span>
        <StatusBadge
          label={diagnostics?.read_only === true ? 'READ ONLY' : 'UNAVAILABLE'}
          tone={diagnostics?.read_only === true ? 'info' : 'unknown'}
        />
      </div>
      {!diagnostics ? (
        <p className="mt-2 text-[9px] font-mono text-foreground/35">App discovery diagnostics unavailable.</p>
      ) : (
        <>
          <div className="mt-2 grid grid-cols-2 gap-1.5">
            <AuditMetric label="entries" value={entries.length} />
            <AuditMetric label="verify possible" value={possibleCount} tone="default" />
            <AuditMetric label="ambiguous" value={ambiguousCount} tone={ambiguousCount > 0 ? 'warning' : 'default'} />
            <AuditMetric label="missing path" value={missingPathCount} tone={missingPathCount > 0 ? 'warning' : 'default'} />
            <AuditMetric label="window-only" value={windowOnlyCount} tone={windowOnlyCount > 0 ? 'warning' : 'default'} />
            <AuditMetric label="actions" value={diagnostics.actions_performed.length} tone={diagnostics.actions_performed.length > 0 ? 'danger' : 'default'} />
          </div>
          <p className="mt-2 text-[9px] font-mono text-foreground/40">Discovery only; not launch proof.</p>
          <div className="mt-2 space-y-1.5">
            {visibleEntries.length > 0 ? (
              visibleEntries.map((entry) => (
                <AppDiscoveryEntryRow key={entry.app_id} entry={entry} />
              ))
            ) : (
              <p className="rounded-md border border-white/10 bg-white/[0.02] px-2 py-1.5 text-[9px] font-mono text-foreground/35">
                No configured app discovery entries were reported.
              </p>
            )}
          </div>
          {Array.isArray(diagnostics.observation_errors) && diagnostics.observation_errors.length > 0 && (
            <p className="mt-2 line-clamp-2 text-[9px] font-mono text-warning/80">
              observation: {diagnostics.observation_errors.join(', ')}
            </p>
          )}
        </>
      )}
    </div>
  );
};

const AppDiscoveryEntryRow = ({ entry }: { entry: AppDiscoveryEntry }) => {
  const state = appDiscoveryState(entry);
  const blockers = Array.isArray(entry.verification_blockers) ? entry.verification_blockers : [];
  const processCandidates = Array.isArray(entry.process_name_candidates) ? entry.process_name_candidates : [];
  const aliases = Array.isArray(entry.aliases) ? entry.aliases : [];
  const matchingWindowCount = numberish(entry.matching_window_count) ?? 0;
  const pidMatchedWindowCount = numberish(entry.pid_matched_window_count) ?? 0;
  const pathLabel = executablePathLabel(entry);
  const processLabel = entry.process_alive === true
    ? `running ${formatPidList(entry.running_processes)}`
    : entry.process_alive === false
      ? 'process not observed'
      : 'process unknown';
  const windowLabel = matchingWindowCount > 0
    ? `${matchingWindowCount} window${matchingWindowCount === 1 ? '' : 's'} / ${pidMatchedWindowCount} pid matched`
    : 'no matching window';

  return (
    <div className={`rounded-md border px-2 py-1.5 ${appDiscoveryBorder(state)}`}>
      <div className="flex items-center justify-between gap-2 text-[9px] font-mono">
        <span className="truncate text-foreground/70">{entry.display_name ?? entry.app_id}</span>
        <StatusBadge label={appDiscoveryLabel(entry)} tone={appDiscoveryBadgeTone(state)} />
      </div>
      <div className="mt-1 grid grid-cols-1 gap-1 text-[8px] font-mono text-foreground/45">
        <div className="flex items-center justify-between gap-2">
          <span className="truncate">path</span>
          <span className={pathLabel.tone}>{pathLabel.label}</span>
        </div>
        <div className="flex items-center justify-between gap-2">
          <span className="truncate">process</span>
          <span className={entry.process_alive === true ? 'text-foreground/65' : 'text-warning/80'}>{processLabel}</span>
        </div>
        <div className="flex items-center justify-between gap-2">
          <span className="truncate">window</span>
          <span className={isWindowOnlyAppDiscovery(entry) ? 'text-warning/80' : 'text-foreground/55'}>{windowLabel}</span>
        </div>
      </div>
      {processCandidates.length > 0 && (
        <p className="mt-1 truncate text-[8px] font-mono text-foreground/35">process: {processCandidates.join(', ')}</p>
      )}
      {aliases.length > 0 && (
        <p className="mt-1 truncate text-[8px] font-mono text-foreground/35">aliases: {aliases.slice(0, 4).join(', ')}</p>
      )}
      {blockers.length > 0 && (
        <p className="mt-1 line-clamp-2 text-[8px] font-mono text-warning/80">blocked: {blockers.join(', ')}</p>
      )}
    </div>
  );
};

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

const ProposalPreviewDetails = ({ proposal }: { proposal: MaintenanceActionProposal }) => {
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
    <div className="mt-2 rounded-md border border-white/10 bg-black/15 px-2 py-1.5 space-y-1">
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
      {resources.length > 0 && (
        <p className="truncate text-[8px] font-mono text-foreground/35">
          resources: {resources.map((resource) => formatResource(resource)).join(', ')}
        </p>
      )}
      {gateVersion && (
        <p className="truncate text-[8px] font-mono text-success/70">gate: {gateVersion}</p>
      )}
      {preconditions.length > 0 && (
        <p className="truncate text-[8px] font-mono text-foreground/35">
          preflight: {preconditions.map((check) => String(getRecord(check)?.check_name ?? 'check')).join(', ')}
        </p>
      )}
      {Object.keys(expectedOutcome || {}).length > 0 && (
        <p className="truncate text-[8px] font-mono text-foreground/35">
          expected: {Object.entries(expectedOutcome || {}).map(([key, value]) => `${key}=${String(value)}`).join(', ')}
        </p>
      )}
      {evidenceRefs.length > 0 && (
        <p className="truncate text-[8px] font-mono text-foreground/35">evidence: {evidenceRefs.join(', ')}</p>
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

function getPendingDecisionHygiene(report: Record<string, unknown> | null): PendingDecisionHygieneDiagnostics | null {
  const hygiene = getCheck(report, 'pending_decision_hygiene') as Partial<PendingDecisionHygieneDiagnostics> | null;
  if (!hygiene || hygiene.scan_version !== 'pending-decision-hygiene/1' || hygiene.read_only !== true) return null;
  return hygiene as PendingDecisionHygieneDiagnostics;
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

function getAppDiscoveryDiagnostics(report: Record<string, unknown> | null): AppDiscoveryDiagnostics | null {
  const discovery = getCheck(report, 'app_discovery') as Partial<AppDiscoveryDiagnostics> | null;
  if (!discovery || discovery.scan_version !== 'app-discovery-smoke/1' || discovery.read_only !== true) return null;
  if (!Array.isArray(discovery.entries) || !Array.isArray(discovery.actions_performed)) return null;
  return discovery as AppDiscoveryDiagnostics;
}

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

function findingSeverityTone(severity: string): string {
  if (severity === 'fail') return 'text-danger';
  if (severity === 'warning') return 'text-warning';
  return 'text-foreground/45';
}

function runtimeTruthLabel(runtimeSnapshot: RuntimeSnapshotDiagnostics | null): string {
  if (!runtimeSnapshot) return 'unknown';
  return runtimeSnapshot.sequence_aligned === false ? 'drift' : runtimeSnapshot.status;
}

function runtimeTruthTone(runtimeSnapshot: RuntimeSnapshotDiagnostics | null): string {
  const label = runtimeTruthLabel(runtimeSnapshot);
  if (label === 'ok') return 'text-success';
  if (label === 'fail') return 'text-danger';
  return 'text-warning';
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
  return value === null ? 'n/a' : String(value);
}

function appDiscoveryState(entry: AppDiscoveryEntry): 'possible' | 'ambiguous' | 'missing' | 'window-only' | 'unknown' {
  if (entry.ambiguity_status === 'ambiguous' || (entry.ambiguous_title_windows?.length ?? 0) > 0) return 'ambiguous';
  if (hasMissingExecutablePath(entry)) return 'missing';
  if (isWindowOnlyAppDiscovery(entry)) return 'window-only';
  if (entry.deterministic_verification_possible === true) return 'possible';
  return 'unknown';
}

function appDiscoveryLabel(entry: AppDiscoveryEntry): string {
  const state = appDiscoveryState(entry);
  if (state === 'possible') return 'verifiable';
  if (state === 'ambiguous') return 'ambiguous';
  if (state === 'missing') return 'unavailable';
  if (state === 'window-only') return 'unverified';
  return 'unknown';
}

function appDiscoveryBadgeTone(state: ReturnType<typeof appDiscoveryState>): 'info' | 'warning' | 'unknown' {
  if (state === 'possible') return 'info';
  if (state === 'unknown') return 'unknown';
  return 'warning';
}

function appDiscoveryBorder(state: ReturnType<typeof appDiscoveryState>): string {
  if (state === 'possible') return 'border-accent/20 bg-accent/[0.03]';
  if (state === 'unknown') return 'border-white/10 bg-white/[0.02]';
  return 'border-warning/20 bg-warning/[0.03]';
}

function hasMissingExecutablePath(entry: AppDiscoveryEntry): boolean {
  const candidates = Array.isArray(entry.executable_candidates) ? entry.executable_candidates : [];
  if (candidates.length === 0) return entry.known === false;
  return candidates.some((candidate) => candidate.path_exists === false || candidate.resolved_read_only === false);
}

function isWindowOnlyAppDiscovery(entry: AppDiscoveryEntry): boolean {
  const matchingWindowCount = numberish(entry.matching_window_count) ?? 0;
  const pidMatchedWindowCount = numberish(entry.pid_matched_window_count) ?? 0;
  return matchingWindowCount > 0 && pidMatchedWindowCount === 0;
}

function executablePathLabel(entry: AppDiscoveryEntry): { label: string; tone: string } {
  const candidates = Array.isArray(entry.executable_candidates) ? entry.executable_candidates : [];
  if (candidates.length === 0) return { label: entry.known ? 'unavailable' : 'unknown app', tone: 'text-warning/80' };
  if (candidates.some((candidate) => candidate.path_exists === false || candidate.resolved_read_only === false)) {
    return { label: 'missing', tone: 'text-warning/80' };
  }
  if (candidates.some((candidate) => candidate.path_exists === true || candidate.resolved_read_only === true)) {
    return { label: 'present', tone: 'text-foreground/60' };
  }
  return { label: 'unknown', tone: 'text-foreground/45' };
}

function formatPidList(processes: AppDiscoveryEntry['running_processes']): string {
  const pids = (processes ?? []).flatMap((process) => process.pids).filter((pid) => Number.isFinite(pid));
  if (pids.length === 0) return 'pid unknown';
  return `PID ${pids.slice(0, 3).join(', ')}`;
}

function orderAppDiscoveryEntries(entries: AppDiscoveryEntry[]): AppDiscoveryEntry[] {
  return [...entries].sort((left, right) => {
    const leftAntigravity = left.app_id.includes('antigravity') ? 0 : 1;
    const rightAntigravity = right.app_id.includes('antigravity') ? 0 : 1;
    if (leftAntigravity !== rightAntigravity) return leftAntigravity - rightAntigravity;
    return appDiscoveryStateRank(appDiscoveryState(left)) - appDiscoveryStateRank(appDiscoveryState(right));
  });
}

function appDiscoveryStateRank(state: ReturnType<typeof appDiscoveryState>): number {
  if (state === 'ambiguous') return 0;
  if (state === 'missing') return 1;
  if (state === 'window-only') return 2;
  if (state === 'unknown') return 3;
  return 4;
}

function formatBytes(value: number): string {
  if (value >= 1024 * 1024 * 1024) return `${(value / 1024 / 1024 / 1024).toFixed(1)}GB`;
  if (value >= 1024 * 1024) return `${(value / 1024 / 1024).toFixed(1)}MB`;
  if (value >= 1024) return `${(value / 1024).toFixed(1)}KB`;
  return `${value}B`;
}

function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

function worstDiagnosticStatus(...statuses: Array<string | null | undefined>): string {
  const normalized = statuses.filter(Boolean).map((status) => String(status));
  if (normalized.includes('fail')) return 'fail';
  if (normalized.includes('warning')) return 'warning';
  if (normalized.includes('ok')) return 'ok';
  return 'unknown';
}

function statusTone(status: string): string {
  if (status === 'ok') return 'text-success';
  if (status === 'fail') return 'text-danger';
  if (status === 'unknown') return 'text-foreground/45';
  return 'text-warning';
}
