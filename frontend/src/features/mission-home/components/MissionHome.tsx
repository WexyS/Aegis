"use client";

import React from 'react';
import {
  AlertTriangle,
  Brain,
  ChevronRight,
  CircleDot,
  Database,
  HelpCircle,
  Layers3,
  Loader2,
  LockKeyhole,
  Radio,
  Send,
  ShieldCheck,
  Sparkles,
  Wrench,
  Zap,
} from 'lucide-react';

import { StatusBadge } from '@/components/StatusBadge';
import { askAegis } from '@/lib/api';
import { useRuntimeStore } from '@/store/useRuntimeStore';
import { useUIStore } from '@/store/useUIStore';
import { AskResponse } from '@/types/ask';

const DEFAULT_MISSION_QUESTION = 'Aegis su an ne durumda?';

export const MissionHome = () => {
  const setActiveTab = useUIStore((state) => state.setActiveTab);
  const lastMaintenanceScan = useRuntimeStore((state) => state.lastMaintenanceScan);
  const pendingApprovals = useRuntimeStore((state) => state.pendingApprovals);
  const pendingClarifications = useRuntimeStore((state) => state.pendingClarifications);
  const connectionState = useRuntimeStore((state) => state.connectionState ?? 'disconnected');
  const runtimeIntegrity = useRuntimeStore((state) => state.runtimeIntegrity ?? 'unverified');
  const activeModel = useRuntimeStore((state) => state.activeModel ?? 'Unavailable');
  const [question, setQuestion] = React.useState(DEFAULT_MISSION_QUESTION);
  const [response, setResponse] = React.useState<AskResponse | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);

  const truth = React.useMemo(
    () => readRuntimeTruth(lastMaintenanceScan, pendingApprovals.length + pendingClarifications.length),
    [lastMaintenanceScan, pendingApprovals.length, pendingClarifications.length],
  );

  const submit = React.useCallback(async () => {
    const trimmed = question.trim();
    if (!trimmed || loading) return;
    setLoading(true);
    setError(null);
    try {
      const result = await askAegis({ question: trimmed, max_sources: 6 });
      setResponse(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Aegis Ask request failed.');
    } finally {
      setLoading(false);
    }
  }, [loading, question]);

  return (
    <div className="min-h-full overflow-y-auto custom-scrollbar">
      <div className="mx-auto flex w-full max-w-[94rem] flex-col gap-6 p-4 sm:p-5 lg:p-7 2xl:p-8">
        <section className="relative overflow-hidden rounded-lg border border-white/10 bg-white/[0.045] p-5 shadow-2xl shadow-black/20 lg:p-7">
          <div className="pointer-events-none absolute inset-x-10 top-0 h-px bg-gradient-to-r from-transparent via-accent/70 to-transparent" />
          <div className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-accent/10 blur-3xl" />
          <div className="pointer-events-none absolute bottom-0 left-1/3 h-48 w-72 rounded-full bg-secondary/10 blur-3xl" />

          <div className="relative z-10 grid gap-6 xl:grid-cols-[1.08fr_0.92fr] xl:items-stretch">
            <div className="flex min-w-0 flex-col justify-between gap-8">
              <div className="max-w-4xl">
                <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl lg:text-5xl">
                  Local-first Mission Control without fake green lights.
                </h1>
                <p className="mt-4 max-w-3xl text-sm leading-7 text-foreground/62 sm:text-[15px]">
                  Aegis explains current runtime truth, safe next steps, and capability boundaries while keeping execution, evidence, approvals, memory, plugins, tools, and agents behind backend-owned gates.
                </p>
              </div>

              <div className="rounded-lg border border-white/10 bg-black/25 p-3.5 shadow-xl shadow-black/15">
                <label htmlFor="mission-ask" className="mb-2 block text-[11px] font-semibold text-foreground/70">
                  Ask or plan with Aegis
                </label>
                <div className="grid gap-3 lg:grid-cols-[1fr_auto]">
                  <textarea
                    id="mission-ask"
                    value={question}
                    onChange={(event) => setQuestion(event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter' && !event.shiftKey) {
                        event.preventDefault();
                        void submit();
                      }
                    }}
                    rows={2}
                    className="min-h-[72px] resize-none rounded-md border border-white/10 bg-white/[0.035] px-3 py-3 text-sm leading-relaxed text-foreground/90 outline-none transition-colors placeholder:text-foreground/30 focus:border-accent/50"
                    placeholder="Ask about status, blockers, capabilities, or the next safe step."
                  />
                  <button
                    type="button"
                    onClick={() => void submit()}
                    disabled={!question.trim() || loading}
                    className="inline-flex min-h-[44px] items-center justify-center gap-2 rounded-md bg-accent px-4 py-2 text-[12px] font-bold uppercase tracking-wider text-background transition-colors hover:bg-accent-light disabled:cursor-not-allowed disabled:opacity-45"
                  >
                    {loading ? <Loader2 size={15} className="animate-spin" /> : <Send size={15} />}
                    Ask
                  </button>
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  <BoundaryPill label="read-only answer" />
                  <BoundaryPill label="no tool execution" />
                  <BoundaryPill label="no memory write" />
                  <BoundaryPill label="no verifier claim" />
                </div>
              </div>
            </div>

            <div className="grid gap-3">
              <RuntimeTruthCard truth={truth} runtimeIntegrity={runtimeIntegrity} connectionState={connectionState} />
              <NextStepCard response={response} error={error} onOpenAsk={() => setActiveTab('Ask')} />
            </div>
          </div>
        </section>

        <section className="grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
          <TrustStack
            truth={truth}
            runtimeIntegrity={runtimeIntegrity}
            activeModel={activeModel}
            connectionState={connectionState}
          />
          <CapabilityPreview onOpenCapabilities={() => setActiveTab('Capabilities')} onOpenAdvanced={() => setActiveTab('Advanced')} />
        </section>

        <section className="grid gap-4 lg:grid-cols-3">
          <MissionTile
            icon={<Brain size={17} />}
            title="Memory preview"
            status="consent-aware"
            detail="Memory is local and lifecycle-based. This home does not write memory or treat retrieval as authority."
            action="Open Memory"
            onClick={() => setActiveTab('Memory')}
          />
          <MissionTile
            icon={<Wrench size={17} />}
            title="Advanced diagnostics"
            status="visible on demand"
            detail="Raw evidence and replay debt stay inspectable, but no longer dominate the first screen."
            action="Open Advanced"
            onClick={() => setActiveTab('Advanced')}
          />
          <MissionTile
            icon={<Zap size={17} />}
            title="Work surface"
            status="governed"
            detail="Aegis Control, command review, approvals, and timelines stay accessible without becoming default clutter."
            action="Open Work"
            onClick={() => setActiveTab('Work')}
          />
        </section>
      </div>
    </div>
  );
};

const RuntimeTruthCard = ({
  truth,
  runtimeIntegrity,
  connectionState,
}: {
  truth: RuntimeTruth;
  runtimeIntegrity: string;
  connectionState: string;
}) => (
  <section className="rounded-lg border border-warning/20 bg-warning/[0.045] p-4 shadow-xl shadow-black/15">
    <div className="flex items-start justify-between gap-3">
      <div>
        <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.18em] text-warning">
          <AlertTriangle size={14} />
          Runtime truth
        </div>
        <p className="mt-2 text-sm leading-relaxed text-foreground/72">
          Current blockers can be clear while raw evidence/replay debt remains visible.
        </p>
      </div>
      <StatusBadge label={truth.status} tone={truthTone(truth.status)} />
    </div>
    <div className="mt-4 grid grid-cols-2 gap-2">
      <TruthMetric label="current blockers" value={truth.currentBlockers} />
      <TruthMetric label="pending approvals" value={truth.pendingDecisions} />
      <TruthMetric label="raw evidence" value={truth.rawEvidence} tone={truthTone(truth.rawEvidence)} />
      <TruthMetric label="raw replay" value={truth.rawReplay} tone={truthTone(truth.rawReplay)} />
      <TruthMetric label="socket" value={connectionState} tone={connectionState === 'connected' ? 'info' : 'warning'} />
      <TruthMetric label="integrity" value={runtimeIntegrity} tone={truthTone(runtimeIntegrity)} />
    </div>
  </section>
);

const NextStepCard = ({
  response,
  error,
  onOpenAsk,
}: {
  response: AskResponse | null;
  error: string | null;
  onOpenAsk: () => void;
}) => {
  const nextStep = response?.recommended_next_steps?.[0]
    ?? 'Ask for a read-only explanation, then move only through explicit capability and approval gates.';
  return (
    <section className="rounded-lg border border-accent/20 bg-accent/[0.035] p-4 shadow-xl shadow-black/15">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.18em] text-accent">
            <Sparkles size={14} />
            Next safe step
          </div>
          <p className="mt-3 text-sm leading-7 text-foreground/78">{error ?? nextStep}</p>
        </div>
        <StatusBadge label={response?.intent ?? 'proposal'} tone={error ? 'warning' : 'info'} />
      </div>
      <button
        type="button"
        onClick={onOpenAsk}
        className="mt-4 inline-flex items-center gap-2 rounded-md border border-accent/30 bg-accent/10 px-3 py-2 text-[11px] font-bold uppercase tracking-wider text-accent transition-colors hover:border-accent/55 hover:bg-accent/15"
      >
        Open Ask
        <ChevronRight size={14} />
      </button>
    </section>
  );
};

const TrustStack = ({
  truth,
  runtimeIntegrity,
  activeModel,
  connectionState,
}: {
  truth: RuntimeTruth;
  runtimeIntegrity: string;
  activeModel: string;
  connectionState: string;
}) => {
  const items = [
    { title: 'Runtime Health', state: truth.status, detail: 'Backend projection only', tone: truthTone(truth.status), icon: <Radio size={15} /> },
    { title: 'Approval', state: truth.pendingDecisions === '0' ? 'clear' : truth.pendingDecisions, detail: 'No auto-grant from UI', tone: truth.pendingDecisions === '0' ? 'success' as const : 'warning' as const, icon: <LockKeyhole size={15} /> },
    { title: 'Evidence', state: truth.rawEvidence, detail: 'Raw debt remains visible', tone: truthTone(truth.rawEvidence), icon: <ShieldCheck size={15} /> },
    { title: 'Memory', state: 'local lifecycle', detail: 'Consent and search, not authority', tone: 'info' as const, icon: <Database size={15} /> },
    { title: 'Model Gateway', state: activeModel || 'unavailable', detail: 'Proposal-only boundary', tone: activeModel && activeModel !== 'Unavailable' ? 'info' as const : 'unknown' as const, icon: <Brain size={15} /> },
    { title: 'Tools / Skills', state: 'metadata-only', detail: 'Catalog is not permission', tone: 'unknown' as const, icon: <Wrench size={15} /> },
    { title: 'Agents / Plugins', state: 'proposal-only', detail: 'No runtime execution from metadata', tone: 'unknown' as const, icon: <Layers3 size={15} /> },
    { title: 'Socket', state: connectionState, detail: 'Live UI transport only', tone: connectionState === 'connected' ? 'info' as const : 'warning' as const, icon: <CircleDot size={15} /> },
  ];

  return (
    <section className="rounded-lg border border-white/10 bg-white/[0.035] p-4 shadow-xl shadow-black/15">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-white">Trust stack</h2>
          <p className="mt-1 text-sm leading-relaxed text-foreground/52">Compact state cards. Unknown stays unknown; warning stays warning.</p>
        </div>
        <StatusBadge label={runtimeIntegrity} tone={truthTone(runtimeIntegrity)} />
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        {items.map((item) => (
          <div key={item.title} className="rounded-lg border border-white/10 bg-black/20 p-3.5">
            <div className="flex items-start justify-between gap-3">
              <div className="flex min-w-0 items-start gap-3">
                <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-white/10 bg-white/[0.035] text-accent">
                  {item.icon}
                </div>
                <div className="min-w-0">
                  <div className="text-sm font-semibold text-white">{item.title}</div>
                  <p className="mt-1 text-[11px] leading-relaxed text-foreground/45">{item.detail}</p>
                </div>
              </div>
              <StatusBadge label={item.state} tone={item.tone} className="max-w-[8rem] shrink-0" />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};

const CapabilityPreview = ({
  onOpenCapabilities,
  onOpenAdvanced,
}: {
  onOpenCapabilities: () => void;
  onOpenAdvanced: () => void;
}) => {
  const preview = [
    ['Aegis Ask', 'implemented read-only explanation'],
    ['Maintenance', 'implemented read-only diagnostics'],
    ['Memory OS', 'explicit lifecycle and search'],
    ['AutoPilot', 'read-only repo structure audit'],
    ['Model Gateway', 'local proposal-only boundary'],
    ['Skill Registry', 'metadata only, no execution'],
    ['Agent Runtime', 'proposal-only sessions'],
    ['Plugin/Manifest', 'readiness metadata only'],
    ['Computer Operator', 'governed partial runtime foundation'],
    ['Codex Supervisor', 'external/manual bridge review'],
  ];
  return (
    <section className="rounded-lg border border-white/10 bg-white/[0.035] p-4 shadow-xl shadow-black/15">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
        <div>
          <h2 className="text-lg font-semibold text-white">Capability preview</h2>
          <p className="mt-1 text-sm leading-relaxed text-foreground/52">What Aegis can discuss today, without pretending future capabilities are active.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button type="button" onClick={onOpenCapabilities} className="rounded-md border border-accent/30 bg-accent/10 px-3 py-2 text-[11px] font-bold uppercase tracking-wider text-accent hover:border-accent/55">
            Capabilities
          </button>
          <button type="button" onClick={onOpenAdvanced} className="rounded-md border border-white/10 bg-white/[0.035] px-3 py-2 text-[11px] font-bold uppercase tracking-wider text-foreground/60 hover:border-white/20 hover:text-white">
            Advanced
          </button>
        </div>
      </div>
      <div className="mt-4 grid gap-2 md:grid-cols-2">
        {preview.map(([name, state]) => (
          <div key={name} className="flex min-w-0 items-center justify-between gap-3 rounded-md border border-white/10 bg-black/20 px-3 py-2.5">
            <span className="truncate text-sm font-medium text-foreground/82">{name}</span>
            <span className="shrink-0 text-right text-[10px] font-mono text-foreground/42">{state}</span>
          </div>
        ))}
      </div>
    </section>
  );
};

const MissionTile = ({
  icon,
  title,
  status,
  detail,
  action,
  onClick,
}: {
  icon: React.ReactNode;
  title: string;
  status: string;
  detail: string;
  action: string;
  onClick: () => void;
}) => (
  <section className="rounded-lg border border-white/10 bg-white/[0.03] p-4 shadow-xl shadow-black/10">
    <div className="flex items-start justify-between gap-3">
      <div className="flex min-w-0 items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-accent/20 bg-accent/10 text-accent">
          {icon}
        </div>
        <div className="min-w-0">
          <h3 className="text-base font-semibold text-white">{title}</h3>
          <p className="mt-1 text-[11px] font-mono text-accent/80">{status}</p>
        </div>
      </div>
    </div>
    <p className="mt-4 text-sm leading-6 text-foreground/55">{detail}</p>
    <button
      type="button"
      onClick={onClick}
      className="mt-4 inline-flex items-center gap-2 text-[11px] font-bold uppercase tracking-wider text-accent transition-colors hover:text-accent-light"
    >
      {action}
      <ChevronRight size={14} />
    </button>
  </section>
);

const BoundaryPill = ({ label }: { label: string }) => (
  <span className="rounded-md border border-white/10 bg-white/[0.035] px-2.5 py-1 text-[10px] font-mono uppercase tracking-wider text-foreground/45">
    {label}
  </span>
);

const TruthMetric = ({
  label,
  value,
  tone = 'unknown',
}: {
  label: string;
  value: string;
  tone?: 'success' | 'info' | 'warning' | 'danger' | 'unknown';
}) => (
  <div className="rounded-md border border-white/10 bg-black/20 p-2.5">
    <div className="truncate text-[9px] font-bold uppercase tracking-wider text-foreground/35">{label}</div>
    <div className={`mt-1 truncate text-[12px] font-mono ${metricToneClass(tone)}`}>{value}</div>
  </div>
);

type RuntimeTruth = {
  status: string;
  currentBlockers: string;
  pendingDecisions: string;
  rawEvidence: string;
  rawReplay: string;
};

function readRuntimeTruth(report: Record<string, unknown> | null, pendingCount: number): RuntimeTruth {
  const summary = getRecord(report?.summary);
  const checks = getRecord(report?.checks);
  const closure = getRecord(checks?.foundation_closure_readiness);
  const evidence = getRecord(checks?.evidence_audit);
  const replay = getRecord(checks?.replay_diagnostics);
  const rawStatuses = getRecord(summary?.raw_component_statuses);
  return {
    status: stringValue(summary?.status) ?? stringValue(closure?.status) ?? 'unknown',
    currentBlockers: countValue(closure?.current_blocker_count),
    pendingDecisions: String(pendingCount),
    rawEvidence: stringValue(evidence?.status) ?? stringValue(rawStatuses?.evidence_audit) ?? 'unknown',
    rawReplay: stringValue(replay?.status) ?? stringValue(rawStatuses?.replay_diagnostics) ?? 'unknown',
  };
}

function getRecord(value: unknown): Record<string, unknown> | null {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : null;
}

function stringValue(value: unknown): string | null {
  return typeof value === 'string' && value.trim().length > 0 ? value : null;
}

function countValue(value: unknown): string {
  return typeof value === 'number' && Number.isFinite(value) ? String(value) : 'unknown';
}

function truthTone(value: string): 'success' | 'info' | 'warning' | 'danger' | 'unknown' {
  if (value === 'ok' || value === 'clear' || value === 'ready') return 'success';
  if (value === 'warning' || value === 'unverified' || value === 'resyncing') return 'warning';
  if (value === 'fail' || value === 'failed' || value === 'blocked') return 'danger';
  if (value === 'unknown' || value === 'Unavailable') return 'unknown';
  return 'info';
}

function metricToneClass(tone: 'success' | 'info' | 'warning' | 'danger' | 'unknown'): string {
  if (tone === 'success') return 'text-success';
  if (tone === 'info') return 'text-accent';
  if (tone === 'warning') return 'text-warning';
  if (tone === 'danger') return 'text-danger';
  return 'text-foreground/60';
}
