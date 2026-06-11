"use client";

import React from 'react';
import {
  AlertTriangle,
  Brain,
  Check,
  ChevronRight,
  Clock3,
  Database,
  FileSearch,
  Layers3,
  Play,
  RefreshCw,
  Search,
  ShieldCheck,
  Trash2,
  Users,
  X,
} from 'lucide-react';

import { EmptyState } from '@/components/EmptyState';
import { StatusBadge } from '@/components/StatusBadge';
import {
  approveMemory,
  deleteMemory,
  fetchAutoPilotReport,
  fetchAutoPilotReports,
  fetchSocietySession,
  fetchSocietySessions,
  listMemories,
  proposeMemory,
  rejectMemory,
  runAutoPilotAudit,
  runSocietySession,
  searchMemories,
} from '@/lib/api';
import {
  AutoPilotReport,
  MemoryCandidateProposal,
  MemoryItem,
  SocietyProposal,
  SocietySession,
} from '@/types/rc';

const DEFAULT_ROOT_PATH = 'C:\\Users\\nemes\\Desktop\\Aegis';
const DEFAULT_PROJECT_REF = 'project:aegis';
const DEFAULT_REPOSITORY_REF = 'repository:aegis';
const DEFAULT_SESSION_REF = 'session:hackathon-rc';

export const MissionControlRCPanel = () => {
  const [rootPath, setRootPath] = React.useState(DEFAULT_ROOT_PATH);
  const [projectRef, setProjectRef] = React.useState(DEFAULT_PROJECT_REF);
  const [repositoryRef, setRepositoryRef] = React.useState(DEFAULT_REPOSITORY_REF);
  const [sessionRef, setSessionRef] = React.useState(DEFAULT_SESSION_REF);
  const [reports, setReports] = React.useState<AutoPilotReport[]>([]);
  const [selectedReport, setSelectedReport] = React.useState<AutoPilotReport | null>(null);
  const [memories, setMemories] = React.useState<MemoryItem[]>([]);
  const [memorySearch, setMemorySearch] = React.useState('');
  const [manualMemory, setManualMemory] = React.useState('');
  const [manualScope, setManualScope] = React.useState('session');
  const [manualSensitivity, setManualSensitivity] = React.useState('private');
  const [sessions, setSessions] = React.useState<SocietySession[]>([]);
  const [selectedSession, setSelectedSession] = React.useState<SocietySession | null>(null);
  const [loading, setLoading] = React.useState<Record<string, boolean>>({});
  const [error, setError] = React.useState<string | null>(null);
  const [notice, setNotice] = React.useState<string | null>(null);
  const activeMemoryCount = React.useMemo(
    () => memories.filter((memory) => memory.status === 'active').length,
    [memories],
  );

  const setBusy = React.useCallback((key: string, value: boolean) => {
    setLoading((current) => ({ ...current, [key]: value }));
  }, []);

  const refreshReports = React.useCallback(async () => {
    const response = await fetchAutoPilotReports();
    setReports(response.reports ?? []);
    if (!selectedReport && response.reports?.[0]) {
      setSelectedReport(response.reports[0]);
    }
  }, [selectedReport]);

  const refreshMemories = React.useCallback(async () => {
    const response = memorySearch.trim()
      ? await searchMemories({ keyword: memorySearch.trim(), include_sensitive: true })
      : await listMemories({ include_deleted: true });
    setMemories(response.memories ?? []);
  }, [memorySearch]);

  const refreshSessions = React.useCallback(async () => {
    const response = await fetchSocietySessions();
    setSessions(response.sessions ?? []);
    if (!selectedSession && response.sessions?.[0]) {
      setSelectedSession(response.sessions[0]);
    }
  }, [selectedSession]);

  React.useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const [reportList, memoryList, sessionList] = await Promise.all([
          fetchAutoPilotReports(),
          listMemories({ include_deleted: true }),
          fetchSocietySessions(),
        ]);
        if (cancelled) return;
        setReports(reportList.reports ?? []);
        setMemories(memoryList.memories ?? []);
        setSessions(sessionList.sessions ?? []);
        setSelectedReport(reportList.reports?.[0] ?? null);
        setSelectedSession(sessionList.sessions?.[0] ?? null);
      } catch (err) {
        if (!cancelled) setError(errorMessage(err));
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const runAudit = async () => {
    setError(null);
    setNotice(null);
    setBusy('audit', true);
    try {
      const report = await runAutoPilotAudit({ root_path: rootPath });
      setSelectedReport(report);
      setReports((current) => [report, ...current.filter((item) => item.report_id !== report.report_id)]);
      setNotice('AutoPilot read-only audit completed from backend response.');
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy('audit', false);
    }
  };

  const reloadReport = async (reportId: string) => {
    setError(null);
    setBusy(`report:${reportId}`, true);
    try {
      const report = await fetchAutoPilotReport(reportId);
      setSelectedReport(report);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(`report:${reportId}`, false);
    }
  };

  const proposeManualMemory = async () => {
    if (!manualMemory.trim()) return;
    await proposeMemoryFromPayload({
      type: manualScope === 'repository' ? 'repo_memory' : manualScope === 'project' ? 'project_preference' : 'task_session_memory',
      content: manualMemory.trim(),
      summary: 'Manual Hackathon RC memory proposal',
      scope: manualScope,
      sensitivity: manualSensitivity,
      source_refs: [{ ref_id: 'mission-control-rc-ui', ref_type: 'explicit_user_action' }],
      metadata: { source: 'mission_control_rc_manual_memory' },
    });
    setManualMemory('');
  };

  const proposeCandidateMemory = async (candidate: MemoryCandidateProposal, index: number) => {
    await proposeMemoryFromPayload({
      type: candidate.type ?? 'repo_memory',
      content: candidate.content ?? 'AutoPilot memory candidate',
      summary: candidate.rationale ?? 'AutoPilot memory candidate proposal',
      scope: normalizeScope(candidate.scope_suggestion),
      sensitivity: normalizeSensitivity(candidate.sensitivity_suggestion),
      source_refs: [{
        ref_id: candidate.source_ref ?? selectedReport?.report_id ?? `autopilot-candidate-${index}`,
        ref_type: 'autopilot_memory_candidate',
      }],
      metadata: {
        autopilot_report_id: selectedReport?.report_id,
        candidate_status: candidate.status,
        persisted_before_user_action: candidate.persisted === true,
      },
    });
  };

  const proposeMemoryFromPayload = async (basePayload: Record<string, unknown>) => {
    setError(null);
    setNotice(null);
    setBusy('memory', true);
    const scope = String(basePayload.scope ?? 'session');
    try {
      await proposeMemory({
        ...basePayload,
        project_ref: scope === 'project' || scope === 'repository' ? projectRef : undefined,
        repository_ref: scope === 'repository' ? repositoryRef : undefined,
        session_ref: scope === 'session' ? sessionRef : undefined,
      });
      setNotice('Memory proposal created. It is not active until explicitly approved.');
      await refreshMemories();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy('memory', false);
    }
  };

  const transitionMemory = async (memoryId: string, action: 'approve' | 'reject' | 'delete') => {
    setError(null);
    setNotice(null);
    setBusy(`memory:${memoryId}:${action}`, true);
    try {
      if (action === 'approve') await approveMemory(memoryId);
      if (action === 'reject') await rejectMemory(memoryId, 'Rejected from Mission Control RC UI');
      if (action === 'delete') await deleteMemory(memoryId);
      setNotice(`Memory ${action} completed from backend response.`);
      await refreshMemories();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(`memory:${memoryId}:${action}`, false);
    }
  };

  const runSociety = async () => {
    if (!selectedReport?.report_id) {
      setError('Select an AutoPilot report before running Society.');
      return;
    }
    setError(null);
    setNotice(null);
    setBusy('society', true);
    try {
      const session = await runSocietySession({
        autopilot_report_id: selectedReport.report_id,
        memory_ids: memories.filter((item) => item.status === 'active').map((item) => item.id),
        society_name: 'hackathon_rc_review_society',
      });
      setSelectedSession(session);
      setSessions((current) => [session, ...current.filter((item) => item.session_id !== session.session_id)]);
      setNotice('Deterministic Society Session completed from backend response.');
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy('society', false);
    }
  };

  const reloadSession = async (sessionId: string) => {
    setError(null);
    setBusy(`session:${sessionId}`, true);
    try {
      setSelectedSession(await fetchSocietySession(sessionId));
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(`session:${sessionId}`, false);
    }
  };

  return (
    <div className="rc-workspace relative flex-1 min-h-0 overflow-y-auto custom-scrollbar bg-[#030611]">
      <div className="rc-ambient-layer pointer-events-none absolute inset-0" aria-hidden="true" />
      <div className="rc-grid-layer pointer-events-none absolute inset-0" aria-hidden="true" />
      <div className="relative z-10 mx-auto flex w-full max-w-[92rem] flex-col gap-5 p-4 lg:p-6">
        <Hero
          report={selectedReport}
          session={selectedSession}
          activeMemoryCount={activeMemoryCount}
        />

        {(error || notice) && (
          <SignalBanner tone={error ? 'danger' : 'success'} message={error ?? notice ?? ''} />
        )}

        <GoldenPath report={selectedReport} memories={memories} session={selectedSession} />
        <LimitationsStrip />

        <div className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
          <div className="space-y-5">
            <AutoPilotPanel
              rootPath={rootPath}
              setRootPath={setRootPath}
              reports={reports}
              selectedReport={selectedReport}
              loading={loading}
              onRun={runAudit}
              onRefreshReports={refreshReports}
              onSelectReport={reloadReport}
            />
            <ReportSurface report={selectedReport} onProposeCandidate={proposeCandidateMemory} memoryBusy={loading.memory === true} />
          </div>

          <div className="space-y-5">
            <MemoryPanel
              memories={memories}
              search={memorySearch}
              setSearch={setMemorySearch}
              manualMemory={manualMemory}
              setManualMemory={setManualMemory}
              manualScope={manualScope}
              setManualScope={setManualScope}
              manualSensitivity={manualSensitivity}
              setManualSensitivity={setManualSensitivity}
              projectRef={projectRef}
              setProjectRef={setProjectRef}
              repositoryRef={repositoryRef}
              setRepositoryRef={setRepositoryRef}
              sessionRef={sessionRef}
              setSessionRef={setSessionRef}
              loading={loading}
              onRefresh={refreshMemories}
              onProposeManual={proposeManualMemory}
              onTransition={transitionMemory}
            />
            <SocietyPanel
              selectedReport={selectedReport}
              sessions={sessions}
              selectedSession={selectedSession}
              loading={loading}
              onRun={runSociety}
              onRefresh={refreshSessions}
              onSelectSession={reloadSession}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

const Hero = ({
  report,
  session,
  activeMemoryCount,
}: {
  report: AutoPilotReport | null;
  session: SocietySession | null;
  activeMemoryCount: number;
}) => (
  <section className="rc-hero relative overflow-hidden rounded-lg border border-white/10 bg-white/[0.04] p-5 shadow-2xl shadow-cyan-950/20 lg:p-6">
    <div className="pointer-events-none absolute inset-x-8 top-0 h-px bg-gradient-to-r from-transparent via-cyan-300/80 to-transparent" />
    <div className="pointer-events-none absolute right-8 top-8 h-28 w-28 rounded-full border border-cyan-300/15 bg-cyan-300/5 blur-[1px]" />
    <div className="relative z-10 flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
      <div className="min-w-0 max-w-4xl">
        <div className="inline-flex items-center gap-2 rounded-md border border-accent/25 bg-accent/10 px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.22em] text-accent shadow-lg shadow-cyan-950/20">
          <ShieldCheck size={14} />
          Hackathon RC Mission Control
        </div>
        <h1 className="mt-4 max-w-4xl text-3xl font-bold tracking-tight text-white lg:text-4xl">
          Judge-facing control surface for the bounded RC path
        </h1>
        <p className="mt-3 max-w-3xl text-sm leading-7 text-foreground/[0.62]">
          Run the real read-only AutoPilot audit, promote selected findings through explicit Memory actions, then render a deterministic Society Session without model, MCP, shell, network, or autonomous execution claims.
        </p>
        <div className="mt-5 flex flex-wrap gap-2">
          <TrustPill label="backend APIs only" />
          <TrustPill label="no fake evidence" />
          <TrustPill label="proposal-only society" />
          <TrustPill label="explicit memory actions" />
        </div>
      </div>
      <div className="grid gap-3 sm:grid-cols-3 lg:w-[30rem]">
        <HeroMetric label="report" value={report?.status ?? 'none'} tone={toneForStatus(report?.status)} />
        <HeroMetric label="active memory" value={String(activeMemoryCount)} tone={activeMemoryCount > 0 ? 'success' : 'unknown'} />
        <HeroMetric label="society" value={session?.status ?? 'none'} tone={toneForStatus(session?.status)} />
      </div>
    </div>
  </section>
);

const HeroMetric = ({ label, value, tone }: { label: string; value: string; tone: StatusToneName }) => (
  <div className="rc-glass-card rounded-lg border border-white/10 bg-black/30 p-3.5">
    <div className="flex items-center justify-between gap-2">
      <div className="text-[9px] font-bold uppercase tracking-widest text-foreground/[0.38]">{label}</div>
      <span className={`h-1.5 w-1.5 rounded-full ${toneDot(tone)}`} />
    </div>
    <div className={`mt-3 truncate text-base font-bold ${toneText(tone)}`}>{formatLabel(value)}</div>
  </div>
);

const TrustPill = ({ label }: { label: string }) => (
  <span className="rounded-md border border-white/10 bg-black/25 px-2.5 py-1 text-[10px] font-mono uppercase tracking-[0.14em] text-foreground/[0.48]">
    {label}
  </span>
);

const GoldenPath = ({
  report,
  memories,
  session,
}: {
  report: AutoPilotReport | null;
  memories: MemoryItem[];
  session: SocietySession | null;
}) => {
  const proposed = memories.some((item) => item.status === 'proposed' || item.status === 'active');
  const steps = [
    { label: 'AutoPilot audit', done: Boolean(report), detail: report?.status ?? 'waiting' },
    { label: 'Candidate review', done: Boolean(report?.memory_candidate_proposals?.length), detail: `${report?.memory_candidate_proposals?.length ?? 0} candidates` },
    { label: 'Explicit Memory action', done: proposed, detail: proposed ? 'memory API used' : 'not yet' },
    { label: 'Society Session', done: Boolean(session), detail: session?.status ?? 'waiting' },
    { label: 'Report timeline', done: Boolean(session?.timeline?.length), detail: `${session?.timeline?.length ?? 0} events` },
  ];
  return (
    <section className="rounded-lg border border-white/10 bg-black/20 p-3 shadow-xl shadow-black/15">
      <div className="mb-3 flex flex-col justify-between gap-2 px-1 sm:flex-row sm:items-center">
        <div>
          <div className="text-[10px] font-bold uppercase tracking-[0.24em] text-accent">Golden Path</div>
          <div className="mt-1 text-[11px] font-mono text-foreground/[0.36]">Every step is driven by backend response or explicit user action.</div>
        </div>
        <StatusBadge label={`${steps.filter((step) => step.done).length}/${steps.length} completed`} tone={steps.every((step) => step.done) ? 'success' : 'info'} />
      </div>
      <div className="grid gap-2 lg:grid-cols-5">
      {steps.map((step, index) => (
        <div key={step.label} className={`rc-step-card relative overflow-hidden rounded-lg border p-3 ${step.done ? 'border-accent/25 bg-accent/[0.075]' : 'border-white/10 bg-white/[0.025]'}`}>
          <div className="flex items-center justify-between gap-2">
            <span className="text-[10px] font-bold uppercase tracking-widest text-foreground/[0.42]">Step {index + 1}</span>
            <span className={`flex h-6 w-6 items-center justify-center rounded-md border ${step.done ? 'border-success/30 bg-success/10 text-success' : 'border-white/10 bg-black/25 text-foreground/30'}`}>
              {step.done ? <Check size={14} /> : <Clock3 size={14} />}
            </span>
          </div>
          <div className="mt-3 text-sm font-semibold text-white">{step.label}</div>
          <div className="mt-1 truncate text-[10px] font-mono text-foreground/40">{step.detail}</div>
          {step.done && <div className="absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-success/60 to-transparent" />}
        </div>
      ))}
      </div>
    </section>
  );
};

const LimitationsStrip = () => (
  <section className="grid gap-2 md:grid-cols-4">
    {[
      'AutoPilot reports are process-local/in-memory only.',
      'Society is deterministic and bounded, not live autonomous multi-agent.',
      'Verifier-lite is not full verification and reports are not evidence.',
      'Memory is local SQLite; retrieval is not authority or permission.',
    ].map((item) => (
      <div key={item} className="rounded-lg border border-warning/20 bg-warning/[0.045] px-3 py-2.5 text-[10px] font-mono leading-relaxed text-warning/85 shadow-lg shadow-black/10">
        {item}
      </div>
    ))}
  </section>
);

const AutoPilotPanel = ({
  rootPath,
  setRootPath,
  reports,
  selectedReport,
  loading,
  onRun,
  onRefreshReports,
  onSelectReport,
}: {
  rootPath: string;
  setRootPath: (value: string) => void;
  reports: AutoPilotReport[];
  selectedReport: AutoPilotReport | null;
  loading: Record<string, boolean>;
  onRun: () => void;
  onRefreshReports: () => void;
  onSelectReport: (reportId: string) => void;
}) => (
  <SectionFrame icon={<FileSearch size={15} />} title="AutoPilot read-only audit" subtitle="Real backend scan, metadata-only report, no shell/network/model/MCP" accent="cyan">
    {loading.audit === true && <InlineLoading label="Backend read-only audit request is in flight" />}
    <div className="grid gap-3 lg:grid-cols-[1fr_auto_auto]">
      <label className="min-w-0">
        <span className="text-[10px] font-bold uppercase tracking-widest text-foreground/35">Local root path</span>
        <input
          value={rootPath}
          onChange={(event) => setRootPath(event.target.value)}
          className="mt-1 w-full rounded-md border border-white/10 bg-black/30 px-3 py-2 text-[12px] font-mono text-foreground/80 outline-none transition-colors focus:border-accent/50"
        />
      </label>
      <IconButton label={loading.audit ? 'Running' : 'Run audit'} icon={<Play size={14} />} onClick={onRun} disabled={loading.audit === true} />
      <IconButton label="Refresh" icon={<RefreshCw size={14} />} onClick={onRefreshReports} />
    </div>

    <div className="mt-4 flex flex-wrap gap-2">
      {reports.length === 0 ? (
        <EmptyState title="No AutoPilot reports loaded" detail="Run a read-only audit or refresh if backend restarted." icon={<FileSearch size={14} />} />
      ) : reports.map((report) => (
        <button
          key={report.report_id}
          type="button"
          onClick={() => onSelectReport(report.report_id)}
          className={`max-w-full rounded-md border px-3 py-2 text-left shadow-lg shadow-black/10 transition-colors ${selectedReport?.report_id === report.report_id ? 'border-accent/[0.45] bg-accent/[0.12]' : 'border-white/10 bg-white/[0.035] hover:border-white/20 hover:bg-white/[0.055]'}`}
        >
          <div className="flex items-center gap-2">
            <StatusBadge label={report.status} tone={toneForStatus(report.status)} />
            <span className="truncate text-[11px] font-mono text-foreground/55">{shortId(report.report_id)}</span>
          </div>
          <div className="mt-1 max-w-[22rem] truncate text-[10px] text-foreground/35">{report.root_path}</div>
        </button>
      ))}
    </div>
  </SectionFrame>
);

const ReportSurface = ({
  report,
  onProposeCandidate,
  memoryBusy,
}: {
  report: AutoPilotReport | null;
  onProposeCandidate: (candidate: MemoryCandidateProposal, index: number) => void;
  memoryBusy: boolean;
}) => {
  if (!report) {
    return (
      <SectionFrame icon={<Layers3 size={15} />} title="AutoPilot report" subtitle="No report selected" accent="violet">
        <EmptyState title="Select or run an AutoPilot report" detail="The UI does not invent report data. Process-local backend reports may disappear after restart." />
      </SectionFrame>
    );
  }
  const inventory = report.source_inventory ?? {};
  const candidates = report.memory_candidate_proposals ?? [];
  return (
    <SectionFrame icon={<Layers3 size={15} />} title="AutoPilot report" subtitle="Report, not evidence. Verifier-lite, not full verification." accent="violet">
      <div className="grid gap-3 lg:grid-cols-4">
        <Metric label="status" value={formatLabel(report.status)} tone={toneForStatus(report.status)} />
        <Metric label="included files" value={String(inventory.included_file_count ?? 0)} />
        <Metric label="dirs" value={String(inventory.total_dirs ?? 0)} />
        <Metric label="verifier-lite" value={formatLabel(report.verifier_lite?.state ?? 'unknown')} tone={toneForStatus(report.verifier_lite?.state)} />
      </div>
      <BoundaryNotice>
        AutoPilot report is a backend read-only audit output. It is not evidence, not full verifier success, and not autonomous execution.
      </BoundaryNotice>
      <div className="mt-4 grid gap-3 lg:grid-cols-2">
        <DataBlock title="Key files" items={inventory.key_files ?? []} />
        <DataBlock title="Docs / tests" items={[...(inventory.docs_paths ?? []), ...(inventory.tests_paths ?? [])]} />
        <DataBlock title="Frontend indicators" items={inventory.frontend_indicators ?? []} />
        <DataBlock title="Backend indicators" items={inventory.backend_indicators ?? []} />
      </div>
      <div className="mt-4 grid gap-3 lg:grid-cols-2">
        <ListBlock title="Risk markers" items={(report.risk_markers ?? []).map((item) => `${item.severity ?? 'info'}: ${item.id ?? item.message ?? 'marker'}`)} />
        <ListBlock title="Limitations" items={report.limitations ?? []} />
      </div>
      <div className="mt-4">
        <Subhead title="Memory candidate proposals" detail="Explicit user action required. Candidate is not active memory." />
        {candidates.length === 0 ? (
          <EmptyState title="No memory candidates" detail="AutoPilot did not return candidate memory proposals." />
        ) : (
          <div className="grid gap-2">
            {candidates.map((candidate, index) => (
              <div key={`${candidate.source_ref ?? 'candidate'}-${index}`} className="rc-glass-card rounded-lg border border-white/10 bg-black/20 p-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <StatusBadge label={candidate.status ?? 'candidate only'} tone="info" />
                      <span className="text-[10px] font-mono text-foreground/35">{candidate.scope_suggestion ?? 'scope unknown'} / {candidate.sensitivity_suggestion ?? 'sensitivity unknown'}</span>
                    </div>
                    <p className="mt-2 text-[12px] leading-relaxed text-foreground/70">{candidate.content}</p>
                    <p className="mt-1 text-[10px] font-mono text-foreground/35">{candidate.rationale}</p>
                  </div>
                  <IconButton label="Propose" icon={<Database size={14} />} onClick={() => onProposeCandidate(candidate, index)} disabled={memoryBusy} />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </SectionFrame>
  );
};

const MemoryPanel = ({
  memories,
  search,
  setSearch,
  manualMemory,
  setManualMemory,
  manualScope,
  setManualScope,
  manualSensitivity,
  setManualSensitivity,
  projectRef,
  setProjectRef,
  repositoryRef,
  setRepositoryRef,
  sessionRef,
  setSessionRef,
  loading,
  onRefresh,
  onProposeManual,
  onTransition,
}: {
  memories: MemoryItem[];
  search: string;
  setSearch: (value: string) => void;
  manualMemory: string;
  setManualMemory: (value: string) => void;
  manualScope: string;
  setManualScope: (value: string) => void;
  manualSensitivity: string;
  setManualSensitivity: (value: string) => void;
  projectRef: string;
  setProjectRef: (value: string) => void;
  repositoryRef: string;
  setRepositoryRef: (value: string) => void;
  sessionRef: string;
  setSessionRef: (value: string) => void;
  loading: Record<string, boolean>;
  onRefresh: () => void;
  onProposeManual: () => void;
  onTransition: (memoryId: string, action: 'approve' | 'reject' | 'delete') => void;
}) => (
  <SectionFrame icon={<Database size={15} />} title="Memory OS" subtitle="Explicit API actions only. Retrieval is not authority." accent="emerald">
    {loading.memory === true && <InlineLoading label="Memory API action pending explicit backend response" />}
    <div className="grid gap-2 sm:grid-cols-3">
      <SmallInput label="project_ref" value={projectRef} onChange={setProjectRef} />
      <SmallInput label="repository_ref" value={repositoryRef} onChange={setRepositoryRef} />
      <SmallInput label="session_ref" value={sessionRef} onChange={setSessionRef} />
    </div>
    <div className="mt-3 grid gap-2 sm:grid-cols-[1fr_auto]">
      <input
        value={search}
        onChange={(event) => setSearch(event.target.value)}
        placeholder="Search memory keyword"
        className="rounded-md border border-white/10 bg-black/30 px-3 py-2 text-[12px] text-foreground/80 outline-none focus:border-accent/50"
      />
      <IconButton label="Search/List" icon={<Search size={14} />} onClick={onRefresh} />
    </div>
    <div className="mt-3 grid gap-2">
      <textarea
        value={manualMemory}
        onChange={(event) => setManualMemory(event.target.value)}
        placeholder="Manual memory proposal. It will remain proposed until approved."
        className="min-h-[5rem] rounded-md border border-white/10 bg-black/30 px-3 py-2 text-[12px] leading-relaxed text-foreground/80 outline-none focus:border-accent/50"
      />
      <div className="grid gap-2 sm:grid-cols-[1fr_1fr_auto]">
        <Select label="scope" value={manualScope} onChange={setManualScope} options={['session', 'project', 'repository']} />
        <Select label="sensitivity" value={manualSensitivity} onChange={setManualSensitivity} options={['public', 'internal', 'private', 'sensitive']} />
        <IconButton label="Propose" icon={<Brain size={14} />} onClick={onProposeManual} disabled={loading.memory === true || !manualMemory.trim()} />
      </div>
    </div>
    <BoundaryNotice>
      Candidate memory is not active memory. Active memory is not authority and does not grant permission.
    </BoundaryNotice>
    <div className="mt-3 space-y-2">
      {memories.length === 0 ? (
        <EmptyState title="No memories returned" detail="Use explicit propose actions or refresh after backend restart." />
      ) : memories.map((memory) => (
        <div key={memory.id} className="rc-glass-card rounded-lg border border-white/10 bg-black/20 p-3">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <StatusBadge label={memory.status} tone={toneForMemoryStatus(memory.status)} />
                <StatusBadge label={memory.scope} tone="unknown" />
                <StatusBadge label={memory.sensitivity} tone={memory.sensitivity === 'sensitive' ? 'warning' : 'info'} />
              </div>
              <p className="mt-2 text-[12px] leading-relaxed text-foreground/70">{memory.content}</p>
              <p className="mt-1 truncate text-[10px] font-mono text-foreground/35">{memory.id}</p>
            </div>
            <div className="flex shrink-0 flex-col gap-1.5">
              <TinyAction label="Approve" icon={<Check size={12} />} onClick={() => onTransition(memory.id, 'approve')} disabled={memory.status !== 'proposed'} />
              <TinyAction label="Reject" icon={<X size={12} />} onClick={() => onTransition(memory.id, 'reject')} disabled={memory.status !== 'proposed'} />
              <TinyAction label="Delete" icon={<Trash2 size={12} />} onClick={() => onTransition(memory.id, 'delete')} disabled={!['proposed', 'active'].includes(memory.status)} />
            </div>
          </div>
        </div>
      ))}
    </div>
  </SectionFrame>
);

const SocietyPanel = ({
  selectedReport,
  sessions,
  selectedSession,
  loading,
  onRun,
  onRefresh,
  onSelectSession,
}: {
  selectedReport: AutoPilotReport | null;
  sessions: SocietySession[];
  selectedSession: SocietySession | null;
  loading: Record<string, boolean>;
  onRun: () => void;
  onRefresh: () => void;
  onSelectSession: (sessionId: string) => void;
}) => (
  <SectionFrame icon={<Users size={15} />} title="Deterministic Society Session" subtitle="Bounded role proposals, not live autonomous multi-agent" accent="violet">
    {loading.society === true && <InlineLoading label="Deterministic Society Session request is in flight" />}
    <div className="flex flex-wrap items-center gap-2">
      <IconButton label={loading.society ? 'Running' : 'Run from report'} icon={<Play size={14} />} onClick={onRun} disabled={!selectedReport || loading.society === true} />
      <IconButton label="Refresh" icon={<RefreshCw size={14} />} onClick={onRefresh} />
      <span className="min-w-0 truncate text-[10px] font-mono text-foreground/40">
        report: {selectedReport?.report_id ? shortId(selectedReport.report_id) : 'none selected'}
      </span>
    </div>
    <BoundaryNotice>
      Society is deterministic and bounded. Role proposals are not truth, evidence, verifier success, approval, or tool permission.
    </BoundaryNotice>
    <div className="mt-3 flex flex-wrap gap-2">
      {sessions.map((session) => (
        <button
          key={session.session_id}
          type="button"
          onClick={() => onSelectSession(session.session_id)}
          className={`rounded-md border px-3 py-2 text-left shadow-lg shadow-black/10 transition-colors ${selectedSession?.session_id === session.session_id ? 'border-secondary/[0.45] bg-secondary/10' : 'border-white/10 bg-white/[0.035] hover:border-white/20 hover:bg-white/[0.055]'}`}
        >
          <div className="flex items-center gap-2">
            <StatusBadge label={session.status} tone={toneForStatus(session.status)} />
            <span className="text-[11px] font-mono text-foreground/50">{shortId(session.session_id)}</span>
          </div>
        </button>
      ))}
    </div>
    {!selectedSession ? (
      <EmptyState title="No Society session selected" detail="Run a deterministic session from a selected AutoPilot report." icon={<Users size={14} />} className="mt-3" />
    ) : (
      <SocietySessionView session={selectedSession} />
    )}
  </SectionFrame>
);

const SocietySessionView = ({ session }: { session: SocietySession }) => (
  <div className="mt-4 space-y-4">
    <div className="rc-glass-card rounded-lg border border-white/10 bg-black/20 p-4">
      <div className="flex items-center justify-between gap-3">
        <div className="min-w-0">
          <div className="text-sm font-semibold text-white">{session.society_name ?? 'hackathon_rc_review_society'}</div>
          <div className="mt-1 truncate text-[10px] font-mono text-foreground/35">{session.session_id}</div>
        </div>
        <StatusBadge label={session.mode ?? 'deterministic'} tone="info" />
      </div>
      {session.final_summary && <p className="mt-3 text-[12px] leading-relaxed text-foreground/65">{session.final_summary}</p>}
    </div>
    <Subhead title="Role proposals" detail="All role outputs are bounded proposals." />
    <div className="grid gap-2">
      {(session.proposals ?? []).map((proposal) => <ProposalCard key={`${proposal.role}-${proposal.proposal_type}`} proposal={proposal} />)}
    </div>
    <Subhead title="Timeline" detail="Backend-owned session timeline, not journal/evidence events." />
    <div className="relative space-y-2">
      <div className="absolute bottom-3 left-3 top-3 w-px bg-gradient-to-b from-accent/50 via-secondary/25 to-transparent" aria-hidden="true" />
      {(session.timeline ?? []).map((event) => (
        <div key={`${event.sequence}-${event.event}`} className="relative flex items-start gap-3 rounded-lg border border-white/10 bg-black/20 p-3 shadow-lg shadow-black/10">
          <div className="relative z-10 flex h-6 w-6 shrink-0 items-center justify-center rounded-md border border-accent/25 bg-accent/10 text-[10px] font-bold text-accent">{event.sequence}</div>
          <div className="min-w-0">
            <div className="text-[11px] font-semibold text-white">{formatLabel(event.event)}</div>
            <div className="mt-1 text-[10px] font-mono text-foreground/40">{event.summary}</div>
          </div>
        </div>
      ))}
    </div>
  </div>
);

const ProposalCard = ({ proposal }: { proposal: SocietyProposal }) => (
  <div className="rc-glass-card rounded-lg border border-white/10 bg-black/20 p-3">
    <div className="flex items-start justify-between gap-3">
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <StatusBadge label={proposal.role} tone="info" />
          <StatusBadge label={formatLabel(proposal.proposal_type)} tone="unknown" />
        </div>
        <h4 className="mt-2 text-sm font-semibold text-white">{proposal.title}</h4>
        <p className="mt-1 text-[12px] leading-relaxed text-foreground/65">{proposal.summary}</p>
      </div>
      <StatusBadge label={proposal.authority === false ? 'no authority' : 'unknown'} tone={proposal.authority === false ? 'success' : 'warning'} />
    </div>
    <div className="mt-3 grid gap-2 md:grid-cols-2">
      <DataBlock title="Inputs used" items={proposal.inputs_used ?? []} />
      <DataBlock title="Limitations" items={proposal.limitations ?? []} />
    </div>
  </div>
);

const SectionFrame = ({
  icon,
  title,
  subtitle,
  children,
  accent = 'cyan',
}: {
  icon: React.ReactNode;
  title: string;
  subtitle: string;
  children: React.ReactNode;
  accent?: 'cyan' | 'violet' | 'emerald';
}) => (
  <section className={`rc-section rc-section-${accent} rounded-lg border border-white/10 bg-white/[0.045] p-4 shadow-xl shadow-black/15`}>
    <div className="mb-4 flex items-start justify-between gap-3">
      <div className="min-w-0">
        <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.2em] text-accent">
          {icon}
          {title}
        </div>
        <p className="mt-1 text-[11px] font-mono leading-relaxed text-foreground/40">{subtitle}</p>
      </div>
    </div>
    {children}
  </section>
);

const Subhead = ({ title, detail }: { title: string; detail: string }) => (
  <div className="mb-2 flex items-center justify-between gap-3 border-b border-white/10 pb-2">
    <h3 className="text-[10px] font-bold uppercase tracking-[0.18em] text-foreground/45">{title}</h3>
    <span className="text-right text-[9px] font-mono text-foreground/30">{detail}</span>
  </div>
);

const Metric = ({ label, value, tone = 'unknown' }: { label: string; value: string; tone?: StatusToneName }) => (
  <div className="rc-glass-card rounded-lg border border-white/10 bg-black/20 p-3">
    <div className="text-[9px] font-bold uppercase tracking-widest text-foreground/35">{label}</div>
    <div className={`mt-2 truncate text-sm font-semibold ${toneText(tone)}`}>{value}</div>
  </div>
);

const DataBlock = ({ title, items }: { title: string; items: string[] }) => (
  <div className="rounded-lg border border-white/10 bg-black/[0.18] p-3">
    <div className="text-[9px] font-bold uppercase tracking-widest text-foreground/35">{title}</div>
    {items.length === 0 ? (
      <div className="mt-2 text-[10px] font-mono text-foreground/25">none returned</div>
    ) : (
      <div className="mt-2 flex flex-wrap gap-1.5">
        {items.slice(0, 12).map((item) => (
          <span key={item} className="max-w-full truncate rounded-md border border-white/10 bg-white/[0.035] px-2 py-1 text-[10px] font-mono text-foreground/55">{item}</span>
        ))}
      </div>
    )}
  </div>
);

const ListBlock = ({ title, items }: { title: string; items: string[] }) => (
  <div className="rounded-lg border border-white/10 bg-black/[0.18] p-3">
    <div className="text-[9px] font-bold uppercase tracking-widest text-foreground/35">{title}</div>
    {items.length === 0 ? (
      <div className="mt-2 text-[10px] font-mono text-foreground/25">none returned</div>
    ) : (
      <ul className="mt-2 space-y-1.5">
        {items.slice(0, 8).map((item) => <li key={item} className="text-[10px] font-mono leading-relaxed text-foreground/50">{item}</li>)}
      </ul>
    )}
  </div>
);

const BoundaryNotice = ({ children }: { children: React.ReactNode }) => (
  <p className="mt-3 rounded-md border border-accent/[0.18] bg-accent/[0.045] px-3 py-2 text-[10px] font-mono leading-relaxed text-accent/[0.82]">
    {children}
  </p>
);

const SignalBanner = ({ tone, message }: { tone: 'success' | 'danger'; message: string }) => (
  <div className={`rounded-lg border px-4 py-3 text-[12px] font-mono shadow-xl shadow-black/15 ${tone === 'danger' ? 'border-danger/35 bg-danger/10 text-danger' : 'border-success/30 bg-success/10 text-success'}`}>
    <div className="flex items-start gap-3">
      <span className={`mt-1 h-2 w-2 shrink-0 rounded-full ${tone === 'danger' ? 'bg-danger' : 'bg-success'}`} />
      <span className="leading-relaxed">{message}</span>
    </div>
  </div>
);

const InlineLoading = ({ label }: { label: string }) => (
  <div className="mb-4 overflow-hidden rounded-lg border border-accent/20 bg-accent/[0.045]">
    <div className="rc-loading-bar h-1 w-full bg-accent/40" />
    <div className="px-3 py-2 text-[10px] font-mono uppercase tracking-[0.14em] text-accent/85">{label}</div>
  </div>
);

const IconButton = ({ label, icon, onClick, disabled = false }: { label: string; icon: React.ReactNode; onClick: () => void; disabled?: boolean }) => (
  <button
    type="button"
    onClick={onClick}
    disabled={disabled}
    className="inline-flex items-center justify-center gap-2 rounded-md border border-accent/30 bg-accent/10 px-3 py-2 text-[11px] font-bold uppercase tracking-wider text-accent shadow-lg shadow-cyan-950/10 transition-colors hover:border-accent/60 hover:bg-accent/15 disabled:cursor-not-allowed disabled:opacity-45"
  >
    {icon}
    {label}
  </button>
);

const TinyAction = ({ label, icon, onClick, disabled }: { label: string; icon: React.ReactNode; onClick: () => void; disabled: boolean }) => (
  <button
    type="button"
    onClick={onClick}
    disabled={disabled}
    title={label}
    className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-white/10 bg-white/[0.03] text-foreground/55 transition-colors hover:border-accent/40 hover:text-accent disabled:cursor-not-allowed disabled:opacity-25"
  >
    {icon}
  </button>
);

const SmallInput = ({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) => (
  <label className="min-w-0">
    <span className="text-[9px] font-bold uppercase tracking-widest text-foreground/35">{label}</span>
    <input
      value={value}
      onChange={(event) => onChange(event.target.value)}
      className="mt-1 w-full rounded-md border border-white/10 bg-black/25 px-2 py-1.5 text-[10px] font-mono text-foreground/70 outline-none focus:border-accent/50"
    />
  </label>
);

const Select = ({ label, value, onChange, options }: { label: string; value: string; onChange: (value: string) => void; options: string[] }) => (
  <label>
    <span className="text-[9px] font-bold uppercase tracking-widest text-foreground/35">{label}</span>
    <select
      value={value}
      onChange={(event) => onChange(event.target.value)}
      className="mt-1 w-full rounded-md border border-white/10 bg-black/30 px-2 py-2 text-[11px] text-foreground/75 outline-none focus:border-accent/50"
    >
      {options.map((option) => <option key={option} value={option}>{option}</option>)}
    </select>
  </label>
);

type StatusToneName = 'success' | 'info' | 'warning' | 'danger' | 'unknown';

function normalizeScope(value: string | undefined): string {
  if (value === 'project' || value === 'repository' || value === 'session') return value;
  return 'session';
}

function normalizeSensitivity(value: string | undefined): string {
  if (value === 'public' || value === 'internal' || value === 'private' || value === 'sensitive') return value;
  return 'private';
}

function toneForStatus(status: string | undefined): StatusToneName {
  if (!status) return 'unknown';
  if (['completed', 'active', 'pass', 'success', 'ready'].includes(status)) return 'success';
  if (['failed', 'error', 'fail', 'deleted'].includes(status)) return 'danger';
  if (['degraded', 'warning', 'proposed', 'rejected', 'input_missing'].includes(status)) return 'warning';
  return 'info';
}

function toneForMemoryStatus(status: string): StatusToneName {
  if (status === 'active') return 'success';
  if (status === 'proposed') return 'warning';
  if (status === 'deleted' || status === 'rejected') return 'danger';
  return 'unknown';
}

function toneText(tone: StatusToneName): string {
  if (tone === 'success') return 'text-success';
  if (tone === 'warning') return 'text-warning';
  if (tone === 'danger') return 'text-danger';
  if (tone === 'info') return 'text-accent';
  return 'text-foreground/45';
}

function toneDot(tone: StatusToneName): string {
  if (tone === 'success') return 'bg-success shadow-[0_0_12px_rgba(16,185,129,0.55)]';
  if (tone === 'warning') return 'bg-warning shadow-[0_0_12px_rgba(245,158,11,0.5)]';
  if (tone === 'danger') return 'bg-danger shadow-[0_0_12px_rgba(244,63,94,0.5)]';
  if (tone === 'info') return 'bg-accent shadow-[0_0_12px_rgba(6,182,212,0.55)]';
  return 'bg-white/25';
}

function formatLabel(value: string): string {
  return value.replace(/_/g, ' ');
}

function shortId(value: string): string {
  if (value.length <= 18) return value;
  return `${value.slice(0, 10)}...${value.slice(-6)}`;
}

function errorMessage(error: unknown): string {
  if (error instanceof Error) return error.message;
  return 'Unknown error';
}
