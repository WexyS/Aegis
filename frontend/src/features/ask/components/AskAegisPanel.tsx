"use client";

import React from 'react';
import { AlertTriangle, CheckCircle2, HelpCircle, Loader2, Send, ShieldCheck } from 'lucide-react';

import { StatusBadge } from '@/components/StatusBadge';
import { askAegis } from '@/lib/api';
import { AskResponse } from '@/types/ask';

const DEFAULT_QUESTION = 'Aegis su an ne durumda?';

export const AskAegisPanel = () => {
  const [question, setQuestion] = React.useState(DEFAULT_QUESTION);
  const [includeMemory, setIncludeMemory] = React.useState(false);
  const [includeModelPolish, setIncludeModelPolish] = React.useState(false);
  const [includeAutopilot, setIncludeAutopilot] = React.useState(false);
  const [includeAgentProposal, setIncludeAgentProposal] = React.useState(false);
  const [response, setResponse] = React.useState<AskResponse | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);

  const submit = React.useCallback(async () => {
    const trimmed = question.trim();
    if (!trimmed || loading) return;
    setLoading(true);
    setError(null);
    try {
      const result = await askAegis({
        question: trimmed,
        include_memory: includeMemory,
        include_model_polish: includeModelPolish,
        include_autopilot: includeAutopilot,
        include_agent_proposal: includeAgentProposal,
        max_sources: 8,
      });
      setResponse(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Aegis Ask request failed.');
    } finally {
      setLoading(false);
    }
  }, [includeAgentProposal, includeAutopilot, includeMemory, includeModelPolish, loading, question]);

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      void submit();
    }
  };

  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden bg-transparent">
      <div className="border-b border-white/10 p-4 sm:p-5">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div className="min-w-0">
            <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.18em] text-accent">
              <HelpCircle size={14} />
              Ask Aegis
            </div>
            <h2 className="mt-2 text-xl font-semibold tracking-tight text-white">Read-only mission explanation</h2>
            <p className="mt-2 max-w-3xl text-[12px] leading-relaxed text-foreground/55">
              Ask about status, warnings, capabilities, skills, tools, model gateway state, and safe next steps. This panel does not execute commands or create authority.
            </p>
          </div>
          <StatusBadge label="read only" tone="info" icon={<ShieldCheck size={12} />} className="shrink-0" />
        </div>

        <div className="mt-4 rounded-lg border border-white/10 bg-black/20 p-3">
          <textarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            onKeyDown={handleKeyDown}
            rows={3}
            className="min-h-[84px] w-full resize-none rounded-md border border-white/10 bg-black/25 p-3 text-[13px] leading-relaxed text-foreground/90 placeholder:text-foreground/30 focus:border-accent/45 focus:outline-none"
            placeholder="Ask about Aegis status, warnings, skills, tools, model gateway, or the next safe step."
          />
          <div className="mt-3 flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
            <div className="flex flex-wrap gap-2">
              <AskOption label="Memory refs" checked={includeMemory} onChange={setIncludeMemory} />
              <AskOption label="Model polish" checked={includeModelPolish} onChange={setIncludeModelPolish} />
              <AskOption label="AutoPilot refs" checked={includeAutopilot} onChange={setIncludeAutopilot} />
              <AskOption label="Agent metadata" checked={includeAgentProposal} onChange={setIncludeAgentProposal} />
            </div>
            <button
              type="button"
              onClick={() => void submit()}
              disabled={!question.trim() || loading}
              className="inline-flex items-center justify-center gap-2 rounded-md bg-accent px-4 py-2 text-[12px] font-bold uppercase tracking-wider text-background transition-colors hover:bg-accent-light disabled:cursor-not-allowed disabled:opacity-45"
            >
              {loading ? <Loader2 size={15} className="animate-spin" /> : <Send size={15} />}
              Ask
            </button>
          </div>
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto p-4 sm:p-5 custom-scrollbar">
        {error && (
          <div className="mb-4 rounded-lg border border-danger/25 bg-danger/10 p-3 text-[12px] text-danger">
            {error}
          </div>
        )}

        {!response && !error && (
          <div className="rounded-lg border border-white/10 bg-white/[0.02] p-4 text-[12px] leading-relaxed text-foreground/55">
            Ask a read-only question to get a backend-owned explanation. Execution requests will be kept in a safe unsupported path.
          </div>
        )}

        {response && <AskResponseView response={response} />}
      </div>
    </div>
  );
};

const AskOption = ({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}) => (
  <label className="inline-flex cursor-pointer items-center gap-2 rounded-md border border-white/10 bg-white/[0.03] px-2.5 py-1.5 text-[10px] font-bold uppercase tracking-wider text-foreground/55 transition-colors hover:border-accent/30 hover:text-accent">
    <input
      type="checkbox"
      checked={checked}
      onChange={(event) => onChange(event.target.checked)}
      className="h-3.5 w-3.5 accent-[var(--accent)]"
    />
    {label}
  </label>
);

const AskResponseView = ({ response }: { response: AskResponse }) => {
  const status = String(response.runtime_health_summary.status ?? 'unknown');
  return (
    <div className="space-y-4">
      <section className="rounded-lg border border-accent/20 bg-accent/[0.03] p-4">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-foreground/45">Answer</div>
            <p className="mt-2 text-[14px] leading-relaxed text-foreground/90">{response.answer}</p>
          </div>
          <div className="flex shrink-0 flex-wrap gap-2">
            <StatusBadge label={response.intent} tone="info" />
            <StatusBadge label={`health ${status}`} tone={statusTone(status)} />
          </div>
        </div>
      </section>

      <RuntimeHealthSummary response={response} />

      <div className="grid gap-4 xl:grid-cols-2">
        <ListSection title="Known" items={response.known} empty="No known facts returned." tone="info" />
        <ListSection title="Unknown" items={response.unknown} empty="No unknowns returned." tone="warning" />
        <ListSection title="Limitations" items={response.limitations} empty="No limitations returned." tone="warning" />
        <ListSection title="Recommended next steps" items={response.recommended_next_steps} empty="No next steps returned." tone="info" />
      </div>

      <section className="rounded-lg border border-white/10 bg-black/20 p-4">
        <div className="mb-3 flex items-center justify-between gap-3">
          <h3 className="text-[10px] font-bold uppercase tracking-[0.18em] text-foreground/45">Sources</h3>
          <StatusBadge label="not evidence" tone="unknown" />
        </div>
        <div className="grid gap-2 md:grid-cols-2">
          {response.source_refs.map((source) => (
            <div key={source.source_id} className="rounded-md border border-white/10 bg-white/[0.02] p-2.5">
              <div className="truncate text-[11px] font-semibold text-foreground/80">{source.label}</div>
              <div className="mt-1 text-[9px] font-mono uppercase tracking-wider text-foreground/35">
                {source.source_id} / authority {String(source.authority)} / evidence {String(source.evidence)}
              </div>
            </div>
          ))}
          {response.source_refs.length === 0 && (
            <div className="text-[12px] text-foreground/45">No backend source refs returned.</div>
          )}
        </div>
      </section>

      <SafetyFlags response={response} />
    </div>
  );
};

const RuntimeHealthSummary = ({ response }: { response: AskResponse }) => {
  const health = response.runtime_health_summary;
  const currentBlockers = String(health.current_blocker_count ?? 'unknown');
  const rawEvidence = String(health.raw_evidence_status ?? 'unknown');
  const activeEvidence = String(health.active_evidence_status ?? 'unknown');
  const rawReplay = String(health.raw_replay_status ?? 'unknown');
  const activeReplay = String(health.active_replay_status ?? 'unknown');
  return (
    <section className="rounded-lg border border-warning/20 bg-warning/[0.03] p-4">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-[10px] font-bold uppercase tracking-[0.18em] text-warning">Runtime truth</h3>
        <StatusBadge label="raw debt visible" tone="warning" icon={<AlertTriangle size={12} />} />
      </div>
      <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
        <TruthMetric label="current blockers" value={currentBlockers} />
        <TruthMetric label="raw evidence" value={rawEvidence} tone={statusTone(rawEvidence)} />
        <TruthMetric label="active evidence" value={activeEvidence} tone={statusTone(activeEvidence)} />
        <TruthMetric label="raw replay" value={rawReplay} tone={statusTone(rawReplay)} />
        <TruthMetric label="active replay" value={activeReplay} tone={statusTone(activeReplay)} />
        <TruthMetric label="historical evidence debt" value={String(health.historical_evidence_debt_count ?? 'unknown')} />
        <TruthMetric label="historical missing evidence" value={String(health.historical_missing_evidence_count ?? 'unknown')} />
        <TruthMetric label="pending decisions" value={String(health.pending_decision_count ?? 'unknown')} />
      </div>
      <p className="mt-3 text-[11px] leading-relaxed text-foreground/50">
        Current blockers can be clear while raw historical evidence/replay debt remains visible. This panel does not repair or suppress diagnostics.
      </p>
    </section>
  );
};

const ListSection = ({
  title,
  items,
  empty,
  tone,
}: {
  title: string;
  items: string[];
  empty: string;
  tone: 'info' | 'warning';
}) => (
  <section className="rounded-lg border border-white/10 bg-black/20 p-4">
    <div className="mb-3 flex items-center justify-between gap-3">
      <h3 className="text-[10px] font-bold uppercase tracking-[0.18em] text-foreground/45">{title}</h3>
      <StatusBadge label={String(items.length)} tone={tone} />
    </div>
    {items.length > 0 ? (
      <ul className="space-y-2">
        {items.map((item) => (
          <li key={item} className="text-[12px] leading-relaxed text-foreground/70">
            {item}
          </li>
        ))}
      </ul>
    ) : (
      <p className="text-[12px] text-foreground/40">{empty}</p>
    )}
  </section>
);

const SafetyFlags = ({ response }: { response: AskResponse }) => {
  const flags = [
    ['execution', response.execution_performed],
    ['memory write', response.memory_written],
    ['evidence', response.evidence_created],
    ['verifier success', response.verifier_success],
    ['approval', response.approval_granted],
    ['capability lease', response.capability_lease_granted],
    ['tool execution', response.tool_execution_performed],
    ['plugin execution', response.plugin_execution_performed],
    ['agent execution', response.agent_execution_performed],
  ];
  const nonAuthority = Object.entries(response.non_authority_flags);
  return (
    <section className="rounded-lg border border-white/10 bg-black/20 p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <h3 className="text-[10px] font-bold uppercase tracking-[0.18em] text-foreground/45">Safety / non-authority flags</h3>
        <StatusBadge label={response.execution_permission} tone="unknown" />
      </div>
      <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-3">
        {flags.map(([label, value]) => (
          <TruthMetric key={String(label)} label={String(label)} value={String(value)} tone={value === true ? 'danger' : 'info'} />
        ))}
      </div>
      {nonAuthority.length > 0 && (
        <div className="mt-3 grid gap-2 md:grid-cols-2">
          {nonAuthority.map(([label, value]) => (
            <div key={label} className="flex items-center gap-2 text-[10px] font-mono text-foreground/45">
              <CheckCircle2 size={12} className={value ? 'text-warning' : 'text-accent'} />
              <span className="truncate">{label}: {String(value)}</span>
            </div>
          ))}
        </div>
      )}
    </section>
  );
};

const TruthMetric = ({
  label,
  value,
  tone = 'unknown',
}: {
  label: string;
  value: string;
  tone?: 'success' | 'info' | 'warning' | 'danger' | 'unknown';
}) => (
  <div className="rounded-md border border-white/10 bg-white/[0.02] p-2.5">
    <div className="truncate text-[9px] font-bold uppercase tracking-wider text-foreground/35">{label}</div>
    <div className={`mt-1 truncate text-[12px] font-mono ${metricToneClass(tone)}`}>{value}</div>
  </div>
);

function statusTone(status: string): 'success' | 'info' | 'warning' | 'danger' | 'unknown' {
  if (status === 'ok' || status === 'ready') return 'success';
  if (status === 'warning') return 'warning';
  if (status === 'fail' || status === 'failed' || status === 'blocked') return 'danger';
  if (status === 'unknown') return 'unknown';
  return 'info';
}

function metricToneClass(tone: 'success' | 'info' | 'warning' | 'danger' | 'unknown'): string {
  if (tone === 'success') return 'text-success';
  if (tone === 'info') return 'text-accent';
  if (tone === 'warning') return 'text-warning';
  if (tone === 'danger') return 'text-danger';
  return 'text-foreground/60';
}
