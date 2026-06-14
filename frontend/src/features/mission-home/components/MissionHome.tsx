"use client";

import React from 'react';
import {
  AlertTriangle,
  Brain,
  CircleDot,
  Compass,
  Database,
  FileText,
  HelpCircle,
  Loader2,
  LockKeyhole,
  Send,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Wrench,
} from 'lucide-react';

import { ApprovalDrawer } from '@/components/ApprovalDrawer';
import { StatusBadge } from '@/components/StatusBadge';
import { dictionaryFor } from '@/i18n';
import { askAegis } from '@/lib/api';
import { useRuntimeStore } from '@/store/useRuntimeStore';
import { useUIStore } from '@/store/useUIStore';
import type { AskResponse } from '@/types/ask';

type ReasoningMode = 'deterministic' | 'local_model' | 'external_disabled';

const DEFAULT_MISSION_QUESTION = 'Aegis şu an ne durumda?';

export const MissionHome = () => {
  const language = useUIStore((state) => state.language);
  const density = useUIStore((state) => state.density);
  const setActiveTab = useUIStore((state) => state.setActiveTab);
  const t = dictionaryFor(language);
  const lastMaintenanceScan = useRuntimeStore((state) => state.lastMaintenanceScan);
  const pendingApprovals = useRuntimeStore((state) => state.pendingApprovals);
  const pendingClarifications = useRuntimeStore((state) => state.pendingClarifications);
  const connectionState = useRuntimeStore((state) => state.connectionState ?? 'disconnected');
  const runtimeIntegrity = useRuntimeStore((state) => state.runtimeIntegrity ?? 'unverified');
  const activeModel = useRuntimeStore((state) => state.activeModel ?? 'Unavailable');
  const pendingCount = pendingApprovals.length + pendingClarifications.length;
  const [question, setQuestion] = React.useState(DEFAULT_MISSION_QUESTION);
  const [reasoningMode, setReasoningMode] = React.useState<ReasoningMode>('deterministic');
  const [response, setResponse] = React.useState<AskResponse | null>(null);
  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);

  const truth = React.useMemo(
    () => readRuntimeTruth(lastMaintenanceScan, pendingCount),
    [lastMaintenanceScan, pendingCount],
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
      setError(err instanceof Error ? err.message : t.mission.askRequestFailed);
    } finally {
      setLoading(false);
    }
  }, [loading, question, t.mission.askRequestFailed]);

  const setSafePrompt = React.useCallback((prompt: string) => {
    setQuestion(prompt);
  }, []);

  return (
    <div className="relative h-full min-h-0 overflow-y-auto custom-scrollbar">
      <AmbientTrustHalo />
      <div className={`relative z-10 mx-auto grid w-full max-w-[112rem] gap-5 px-4 py-5 sm:px-6 lg:grid-cols-[minmax(0,1fr)_22rem] lg:px-8 ${density === 'compact' ? 'xl:gap-5' : 'xl:gap-7'}`}>
        <section className="min-w-0">
          <div className="mb-6 max-w-5xl">
            <h1 className="max-w-5xl text-4xl font-semibold leading-[1.05] tracking-tight text-white sm:text-5xl xl:text-6xl">
              {t.mission.heroTitle}
            </h1>
            <p className="mt-4 max-w-4xl text-base leading-8 text-foreground/58 sm:text-lg">
              {t.mission.heroSubtitle}
            </p>
          </div>

          <MissionComposer
            question={question}
            setQuestion={setQuestion}
            loading={loading}
            error={error}
            response={response}
            reasoningMode={reasoningMode}
            setReasoningMode={setReasoningMode}
            submit={submit}
            setSafePrompt={setSafePrompt}
          />

          <div className="mt-5 grid gap-5 xl:grid-cols-[0.82fr_1.18fr]">
            <TrustSummary truth={truth} runtimeIntegrity={runtimeIntegrity} activeModel={activeModel} connectionState={connectionState} />
            <CapabilityNexus />
          </div>
        </section>

        <ContextInspector
          truth={truth}
          pendingCount={pendingCount}
          onOpenAsk={() => setActiveTab('Ask')}
          onOpenApprovalDrawer={() => setDrawerOpen(true)}
        />
      </div>

      <ApprovalDrawer
        open={drawerOpen}
        pendingCount={pendingCount}
        onClose={() => setDrawerOpen(false)}
        onReviewDetails={() => {
          setDrawerOpen(false);
          setActiveTab('Work');
        }}
      />
    </div>
  );
};

const MissionComposer = ({
  question,
  setQuestion,
  loading,
  error,
  response,
  reasoningMode,
  setReasoningMode,
  submit,
  setSafePrompt,
}: {
  question: string;
  setQuestion: (question: string) => void;
  loading: boolean;
  error: string | null;
  response: AskResponse | null;
  reasoningMode: ReasoningMode;
  setReasoningMode: (mode: ReasoningMode) => void;
  submit: () => Promise<void>;
  setSafePrompt: (prompt: string) => void;
}) => {
  const language = useUIStore((state) => state.language);
  const t = dictionaryFor(language);
  const prompt = t.mission;
  const modes: Array<{ value: ReasoningMode; label: string; detail: string }> = [
    { value: 'deterministic', label: prompt.deterministic, detail: prompt.modeNoModelCall },
    { value: 'local_model', label: prompt.localModel, detail: prompt.modeProposalOnly },
    { value: 'external_disabled', label: prompt.externalDisabled, detail: prompt.modeNoCloud },
  ];

  return (
    <section className="relative overflow-hidden rounded-2xl border border-white/[0.12] bg-white/[0.055] p-1 shadow-[0_30px_100px_rgba(0,0,0,0.45),0_0_72px_rgba(139,92,246,0.14)] backdrop-blur-2xl">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_18%_18%,rgba(139,92,246,0.17),transparent_32%),radial-gradient(circle_at_92%_26%,rgba(6,182,212,0.12),transparent_34%)]" />
      <div className="relative rounded-[0.9rem] border border-white/10 bg-[#121217]/[0.88]">
        <div className="flex flex-col gap-3 border-b border-white/10 px-5 py-4 xl:flex-row xl:items-center xl:justify-between">
          <div>
            <div className="flex items-center gap-2 text-[12px] font-semibold text-white">
              <Sparkles size={16} className="text-secondary-light" />
              {prompt.composerTitle}
            </div>
            <div className="mt-2 flex flex-wrap gap-2">
              <SafetyChip label={prompt.readOnly} tone="cyan" />
              <SafetyChip label={prompt.noToolExecution} tone="neutral" />
              <SafetyChip label={prompt.noMemoryWrite} tone="neutral" />
              <SafetyChip label={prompt.approvalGated} tone="amber" />
            </div>
          </div>

          <div className="min-w-0 rounded-xl border border-white/10 bg-black/20 p-1">
            <div className="mb-1 px-2 text-[9px] font-bold uppercase tracking-[0.18em] text-foreground/35">{prompt.reasoningMode}</div>
            <div className="flex flex-wrap gap-1">
              {modes.map((mode) => (
                <button
                  key={mode.value}
                  type="button"
                  onClick={() => setReasoningMode(mode.value)}
                  className={`rounded-lg border px-2.5 py-1.5 text-left transition-colors ${
                    reasoningMode === mode.value
                      ? 'border-secondary/35 bg-secondary/[0.16] text-white'
                      : 'border-transparent text-foreground/45 hover:bg-white/[0.045] hover:text-white'
                  }`}
                >
                  <span className="block text-[11px] font-semibold">{mode.label}</span>
                  <span className="block text-[8px] font-mono uppercase tracking-wider opacity-55">{mode.detail}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="p-5">
          <textarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                void submit();
              }
            }}
            rows={5}
            className="min-h-[11rem] w-full resize-none rounded-xl border border-white/[0.12] bg-black/[0.24] px-5 py-4 text-base leading-8 text-foreground/90 shadow-[inset_0_1px_0_rgba(255,255,255,0.05)] outline-none transition-colors placeholder:text-foreground/[0.32] focus:border-secondary/50 focus:shadow-[0_0_0_1px_rgba(139,92,246,0.18),0_0_42px_rgba(139,92,246,0.14)]"
            placeholder={prompt.composerPlaceholder}
          />

          <div className="mt-4 flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
            <div className="flex flex-wrap gap-2">
              <ComposerAction label={prompt.draftPlan} icon={<FileText size={15} />} onClick={() => setSafePrompt(prompt.draftPlanQuestion)} />
              <ComposerAction label={prompt.explainStatus} icon={<HelpCircle size={15} />} onClick={() => setSafePrompt(prompt.explainStatusQuestion)} />
              <ComposerAction label={prompt.exploreOptions} icon={<Compass size={15} />} onClick={() => setSafePrompt(prompt.exploreOptionsQuestion)} />
            </div>
            <button
              type="button"
              onClick={() => void submit()}
              disabled={!question.trim() || loading}
              className="inline-flex min-h-[46px] items-center justify-center gap-2 rounded-xl border border-secondary/40 bg-secondary px-6 py-2.5 text-sm font-semibold text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.25),0_0_34px_rgba(139,92,246,0.28)] transition-colors hover:bg-secondary-light disabled:cursor-not-allowed disabled:opacity-45"
            >
              {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
              {prompt.ask}
            </button>
          </div>

          {(response || error) && (
            <div className={`mt-4 rounded-xl border p-4 ${error ? 'border-danger/25 bg-danger/10' : 'border-accent/20 bg-accent/[0.045]'}`}>
              <div className="mb-2 flex items-center justify-between gap-3">
                <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-foreground/42">{prompt.latestReadOnlyAnswer}</div>
                {response && <StatusBadge label={response.intent} tone="info" />}
              </div>
              <p className={`text-sm leading-7 ${error ? 'text-danger' : 'text-foreground/70'}`}>{error ?? response?.answer}</p>
            </div>
          )}
        </div>
      </div>
    </section>
  );
};

const ContextInspector = ({
  truth,
  pendingCount,
  onOpenAsk,
  onOpenApprovalDrawer,
}: {
  truth: RuntimeTruth;
  pendingCount: number;
  onOpenAsk: () => void;
  onOpenApprovalDrawer: () => void;
}) => {
  const language = useUIStore((state) => state.language);
  const t = dictionaryFor(language);

  return (
    <aside className="min-w-0 space-y-4 lg:sticky lg:top-5 lg:self-start">
      <section className="rounded-2xl border border-white/10 bg-white/[0.045] p-4 shadow-2xl shadow-black/25 backdrop-blur-2xl">
        <div className="flex items-center justify-between gap-3 border-b border-white/10 pb-3">
          <h2 className="text-[11px] font-bold uppercase tracking-[0.2em] text-foreground/45">{t.mission.contextInspector}</h2>
          <SlidersHorizontal size={15} className="text-foreground/35" />
        </div>
        <InspectorNote title={t.mission.nextSafeStep} copy={t.mission.nextSafeStepCopy} tone="cyan" icon={<ShieldCheck size={15} />} />
        <InspectorNote title={t.mission.runtimeNote} copy={runtimeNoteCopy(t, truth)} tone="amber" icon={<AlertTriangle size={15} />} />
        <InspectorNote title={t.mission.truthNote} copy={t.mission.truthNoteCopy} tone="neutral" icon={<HelpCircle size={15} />} />
        <div className="mt-4 grid gap-2">
          <button
            type="button"
            onClick={onOpenAsk}
            className="rounded-xl border border-white/10 bg-white/[0.045] px-4 py-3 text-sm font-semibold text-foreground/[0.78] transition-colors hover:border-accent/30 hover:text-accent"
          >
            {t.mission.openAsk}
          </button>
          <button
            type="button"
            onClick={onOpenApprovalDrawer}
            className={`rounded-xl border px-4 py-3 text-sm font-semibold transition-colors ${
              pendingCount > 0
                ? 'border-warning/30 bg-warning/10 text-warning hover:bg-warning/15'
                : 'border-white/10 bg-white/[0.035] text-foreground/52 hover:border-white/20 hover:text-white'
            }`}
          >
            {t.mission.openApprovalDrawer}
          </button>
        </div>
      </section>

      <section className="rounded-2xl border border-white/10 bg-white/[0.035] p-4 shadow-xl shadow-black/15">
        <h2 className="text-lg font-semibold text-white">{t.mission.runtimeTruth}</h2>
        <div className="mt-4 space-y-3">
          <RuntimeRow label={t.mission.health} value={formatTruthStatus(t, truth.status)} tone={truthTone(truth.status)} />
          <RuntimeRow label={t.mission.activeBlockers} value={truth.currentBlockers} />
          <RuntimeRow label={t.mission.pendingApprovals} value={truth.pendingDecisions} />
          <RuntimeRow label={t.mission.rawEvidence} value={formatTruthStatus(t, truth.rawEvidence)} tone={truthTone(truth.rawEvidence)} />
          <RuntimeRow label={t.mission.rawReplay} value={formatTruthStatus(t, truth.rawReplay)} tone={truthTone(truth.rawReplay)} />
        </div>
      </section>
    </aside>
  );
};

const TrustSummary = ({
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
  const language = useUIStore((state) => state.language);
  const t = dictionaryFor(language);
  const items = [
    { title: t.mission.runtimeAndEvidence, tags: [formatTruthStatus(t, truth.status), t.truth.readOnly, t.truth.metadataOnly], icon: <ShieldCheck size={16} />, tone: 'amber' },
    { title: t.mission.approvalGates, tags: [truth.pendingDecisions === '0' ? t.mission.zeroPending : truth.pendingDecisions, t.truth.approvalRequired], icon: <LockKeyhole size={16} />, tone: 'violet' },
    { title: t.nav.memory, tags: [t.truth.localLifecycle, t.truth.readOnly], icon: <Database size={16} />, tone: 'cyan' },
    { title: t.mission.models, tags: [activeModel === 'Unavailable' ? t.truth.notWired : t.truth.proposalOnly, t.truth.proposalOnly], icon: <Brain size={16} />, tone: 'amber' },
    { title: t.mission.toolsAgents, tags: [t.truth.metadataOnly, t.truth.proposalOnly], icon: <Wrench size={16} />, tone: 'cyan' },
    { title: t.mission.socket, tags: [connectionState, runtimeIntegrity], icon: <CircleDot size={16} />, tone: 'neutral' },
  ];

  return (
    <section className="rounded-2xl border border-white/10 bg-white/[0.04] p-4 shadow-xl shadow-black/20">
      <h2 className="text-lg font-semibold text-white">{t.mission.trustStack}</h2>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        {items.map((item) => (
          <div key={item.title} className="rounded-xl border border-white/10 bg-black/[0.18] p-4">
            <div className="flex items-center gap-3">
              <span className={`flex h-9 w-9 items-center justify-center rounded-lg border ${toneBorder(item.tone)} ${toneText(item.tone)}`}>
                {item.icon}
              </span>
              <h3 className="text-base font-semibold text-white">{item.title}</h3>
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              {item.tags.map((tag) => (
                <span key={tag} className={`rounded-lg border px-2.5 py-1 text-[11px] font-semibold ${toneChip(item.tone)}`}>
                  {tag}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
      <p className="mt-4 text-sm leading-7 text-foreground/45">{t.mission.memoryConsentCopy}</p>
    </section>
  );
};

const CapabilityNexus = () => {
  const language = useUIStore((state) => state.language);
  const t = dictionaryFor(language);
  const nodes = [
    [t.mission.askNode, t.mission.askNodeState],
    [t.mission.maintenanceNode, t.mission.maintenanceNodeState],
    [t.nav.memory, t.mission.memoryNodeState],
    [t.mission.modelGatewayNode, t.truth.proposalOnly],
    [t.mission.skillRegistryNode, t.truth.metadataOnly],
    [t.mission.agentRuntimeNode, t.truth.proposalOnly],
    [t.mission.pluginManifestNode, t.mission.pluginManifestNodeState],
    [t.mission.modelCouncilNode, t.truth.future],
  ];

  return (
    <section className="relative overflow-hidden rounded-2xl border border-white/10 bg-white/[0.035] p-4 shadow-xl shadow-black/20">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_62%_42%,rgba(6,182,212,0.12),transparent_24%),radial-gradient(circle_at_72%_70%,rgba(139,92,246,0.16),transparent_30%)]" />
      <div className="relative z-10 flex flex-col gap-5 xl:flex-row xl:items-center">
        <div className="relative mx-auto flex h-56 w-56 shrink-0 items-center justify-center">
          <div className="absolute inset-0 rounded-full border border-secondary/20" />
          <div className="absolute inset-6 rounded-full border border-accent/20" />
          <div className="absolute inset-12 rounded-full border border-white/10 bg-black/[0.18]" />
          <div className="absolute h-24 w-24 rounded-full bg-secondary/22 blur-2xl" />
          <div className="relative rounded-2xl border border-secondary/30 bg-secondary/[0.14] px-4 py-3 text-center text-sm font-semibold text-white shadow-[0_0_44px_rgba(139,92,246,0.28)]">
            {t.mission.capabilityNexus}
          </div>
        </div>
        <div className="grid min-w-0 flex-1 gap-2 sm:grid-cols-2">
          {nodes.map(([name, state], index) => (
            <div key={name} className="flex items-center gap-3 rounded-xl border border-white/10 bg-black/[0.18] px-3 py-2.5">
              <span className={`h-2.5 w-2.5 shrink-0 rounded-full ${index < 3 ? 'bg-accent shadow-[0_0_10px_rgba(6,182,212,0.8)]' : index < 7 ? 'bg-secondary-light shadow-[0_0_10px_rgba(167,139,250,0.75)]' : 'bg-foreground/35'}`} />
              <div className="min-w-0">
                <div className="truncate text-sm font-semibold text-white">{name}</div>
                <div className="truncate text-[10px] font-mono text-foreground/42">{state}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

const AmbientTrustHalo = () => (
  <div className="pointer-events-none absolute inset-0 overflow-hidden">
    <div className="absolute left-[12%] top-[28%] h-px w-[74%] bg-gradient-to-r from-transparent via-accent/[0.32] to-transparent" />
    <div className="absolute right-[8%] top-[42%] h-64 w-[62rem] -rotate-6 rounded-full border border-accent/10 opacity-70" />
    <div className="absolute right-[-7%] top-[34%] h-72 w-[58rem] -rotate-6 rounded-full border border-secondary/[0.12] opacity-80" />
    <div className="absolute bottom-[-10rem] right-[12%] h-72 w-72 rounded-full bg-accent/10 blur-3xl" />
  </div>
);

const ComposerAction = ({ label, icon, onClick }: { label: string; icon: React.ReactNode; onClick: () => void }) => (
  <button
    type="button"
    onClick={onClick}
    className="inline-flex min-h-[42px] items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/[0.04] px-4 py-2 text-sm font-semibold text-foreground/70 transition-colors hover:border-white/20 hover:text-white"
  >
    {icon}
    {label}
  </button>
);

const SafetyChip = ({ label, tone }: { label: string; tone: 'cyan' | 'amber' | 'neutral' }) => (
  <span className={`rounded-lg border px-2.5 py-1 text-[11px] font-semibold ${toneChip(tone)}`}>
    {label}
  </span>
);

const InspectorNote = ({
  title,
  copy,
  tone,
  icon,
}: {
  title: string;
  copy: string;
  tone: 'cyan' | 'amber' | 'neutral';
  icon: React.ReactNode;
}) => (
  <div className={`mt-4 rounded-xl border p-4 ${toneBorder(tone)} bg-black/20`}>
    <div className={`flex items-center gap-2 text-[12px] font-bold uppercase tracking-[0.16em] ${toneText(tone)}`}>
      {icon}
      {title}
    </div>
    <p className="mt-3 text-sm leading-7 text-foreground/66">{copy}</p>
  </div>
);

const RuntimeRow = ({
  label,
  value,
  tone = 'unknown',
}: {
  label: string;
  value: string;
  tone?: 'success' | 'info' | 'warning' | 'danger' | 'unknown';
}) => (
  <div className="flex items-center justify-between gap-3 rounded-xl border border-white/10 bg-black/[0.18] px-3 py-2.5">
    <span className="text-sm text-foreground/55">{label}</span>
    <span className={`text-sm font-semibold ${metricToneClass(tone)}`}>{value}</span>
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

function runtimeNoteCopy(t: ReturnType<typeof dictionaryFor>, truth: RuntimeTruth): string {
  const status = formatTruthStatus(t, truth.status);
  return `${status} - ${t.mission.rawEvidence}: ${formatTruthStatus(t, truth.rawEvidence)} / ${t.mission.rawReplay}: ${formatTruthStatus(t, truth.rawReplay)}`;
}

function formatTruthStatus(t: ReturnType<typeof dictionaryFor>, value: string): string {
  const normalized = value.toLowerCase();
  if (normalized === 'unknown' || normalized === 'unavailable') return t.truth.unknown;
  if (normalized === 'warning' || normalized === 'unverified' || normalized === 'resyncing') return t.truth.warning;
  if (normalized === 'fail' || normalized === 'failed') return 'Fail';
  if (normalized === 'ok' || normalized === 'ready' || normalized === 'clear') return 'OK';
  return value;
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
  const normalized = value.toLowerCase();
  if (normalized === 'ok' || normalized === 'clear' || normalized === 'ready') return 'success';
  if (normalized === 'warning' || normalized === 'unverified' || normalized === 'resyncing') return 'warning';
  if (normalized === 'fail' || normalized === 'failed' || normalized === 'blocked') return 'danger';
  if (normalized === 'unknown' || normalized === 'unavailable') return 'unknown';
  return 'info';
}

function metricToneClass(tone: 'success' | 'info' | 'warning' | 'danger' | 'unknown'): string {
  if (tone === 'success') return 'text-success';
  if (tone === 'info') return 'text-accent';
  if (tone === 'warning') return 'text-warning';
  if (tone === 'danger') return 'text-danger';
  return 'text-foreground/60';
}

function toneText(tone: string): string {
  if (tone === 'cyan') return 'text-accent';
  if (tone === 'amber') return 'text-warning';
  if (tone === 'violet') return 'text-secondary-light';
  return 'text-foreground/48';
}

function toneBorder(tone: string): string {
  if (tone === 'cyan') return 'border-accent/25';
  if (tone === 'amber') return 'border-warning/25';
  if (tone === 'violet') return 'border-secondary/25';
  return 'border-white/10';
}

function toneChip(tone: string): string {
  if (tone === 'cyan') return 'border-accent/25 bg-accent/10 text-accent';
  if (tone === 'amber') return 'border-warning/25 bg-warning/10 text-warning';
  if (tone === 'violet') return 'border-secondary/25 bg-secondary/[0.12] text-secondary-light';
  return 'border-white/10 bg-white/[0.04] text-foreground/55';
}
