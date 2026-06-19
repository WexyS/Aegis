"use client";

import React from 'react';
import {
  AlertTriangle,
  BrainCircuit,
  CheckCircle2,
  Loader2,
  PlugZap,
  RefreshCw,
  Send,
  ShieldCheck,
} from 'lucide-react';

import { StatusBadge } from '@/components/StatusBadge';
import { dictionaryFor, type Language } from '@/i18n';
import { completeModelGateway, fetchModelHubStatus, probeModelGateway } from '@/lib/api';
import { ModelGatewayCompletionResponse, ModelGatewayStatus, ModelHubStatus } from '@/types/modelHub';

import { ExternalProviderReadinessSection } from './ExternalProviderReadinessSection';
import { ExternalProviderBrokerBoundarySection } from './ExternalProviderBrokerBoundarySection';
import { LocalModelProfilesSection } from './LocalModelProfilesSection';
import { ModelHubFactRow as FactRow } from './ModelHubFactRow';

type LoadState = 'idle' | 'loading' | 'loaded' | 'error';

export const ModelHubPanel = ({ language }: { language: Language }) => {
  const t = dictionaryFor(language).modelHub;
  const [loadState, setLoadState] = React.useState<LoadState>('idle');
  const [status, setStatus] = React.useState<ModelHubStatus | null>(null);
  const [statusError, setStatusError] = React.useState<string | null>(null);
  const [probeResult, setProbeResult] = React.useState<ModelGatewayStatus | null>(null);
  const [probeLoading, setProbeLoading] = React.useState(false);
  const [proposal, setProposal] = React.useState<ModelGatewayCompletionResponse | null>(null);
  const [proposalLoading, setProposalLoading] = React.useState(false);
  const [proposalPrompt, setProposalPrompt] = React.useState(t.defaultPrompt);

  React.useEffect(() => {
    setProposalPrompt((current) => (current.trim() ? current : t.defaultPrompt));
  }, [t.defaultPrompt]);

  const refreshStatus = React.useCallback(async () => {
    setLoadState('loading');
    setStatusError(null);
    try {
      const result = await fetchModelHubStatus();
      setStatus(result);
      setLoadState('loaded');
    } catch (err) {
      setStatusError(err instanceof Error ? err.message : t.statusFailed);
      setLoadState('error');
    }
  }, [t.statusFailed]);

  React.useEffect(() => {
    let cancelled = false;
    setLoadState('loading');
    setStatusError(null);
    fetchModelHubStatus()
      .then((result) => {
        if (cancelled) return;
        setStatus(result);
        setLoadState('loaded');
      })
      .catch((err) => {
        if (cancelled) return;
        setStatusError(err instanceof Error ? err.message : t.statusFailed);
        setLoadState('error');
      });
    return () => {
      cancelled = true;
    };
  }, [t.statusFailed]);

  const runProbe = React.useCallback(async () => {
    if (probeLoading) return;
    setProbeLoading(true);
    setProbeResult(null);
    try {
      const result = await probeModelGateway();
      setProbeResult(result);
      await refreshStatus();
    } catch (err) {
      setProbeResult({
        status: 'error',
        provider: 'lm_studio',
        base_url: status?.lm_studio.base_url ?? '',
        host: status?.lm_studio.host ?? '',
        model: status?.lm_studio.model ?? null,
        model_configured: Boolean(status?.lm_studio.model_configured),
        enabled: Boolean(status?.lm_studio.enabled),
        timeout_seconds: 0,
        max_input_chars: 0,
        max_output_tokens: 0,
        health_result: 'not_probed',
        failure_reasons: [err instanceof Error ? err.message : t.probeFailed],
        warnings: [],
        limitations: [],
        unknowns: [],
        duration_ms: 0,
        provider_probe_performed: false,
        http_request_performed: false,
        model_call_performed: false,
        generation_performed: false,
        prompt_payload_sent: false,
        context_payload_sent: false,
        memory_write_performed: false,
        tool_call_performed: false,
        mcp_call_performed: false,
        shell_command_performed: false,
        file_mutation_performed: false,
        data_sent_external: false,
        authority: false,
        runtime_dispatch_allowed: false,
        execution_permission: 'not_granted_by_model_gateway',
        evidence: false,
        evidence_provided_by_model: false,
        verifier_success: false,
        approval_granted: false,
        permission_granted: false,
        capability_lease_granted: false,
        model_output_is_truth: false,
        model_output_is_evidence: false,
        model_output_is_verifier_success: false,
      });
    } finally {
      setProbeLoading(false);
    }
  }, [probeLoading, refreshStatus, status, t.probeFailed]);

  const runProposal = React.useCallback(async () => {
    const trimmed = proposalPrompt.trim();
    if (!trimmed || proposalLoading) return;
    setProposalLoading(true);
    setProposal(null);
    try {
      const result = await completeModelGateway({
        purpose: 'explanation',
        prompt: buildSafeProposalPrompt(trimmed, status, language),
        max_output_tokens: 320,
        temperature: 0.2,
      });
      setProposal(result);
    } catch (err) {
      setProposal({
        request_id: 'model-hub-ui-error',
        status: 'error',
        provider: 'lm_studio',
        base_url: status?.lm_studio.base_url ?? '',
        model: status?.lm_studio.model ?? null,
        purpose: 'explanation',
        output_text: '',
        usage: {},
        started_at: 0,
        completed_at: 0,
        duration_ms: 0,
        warnings: [],
        limitations: [],
        failure_reasons: [err instanceof Error ? err.message : t.proposalFailed],
        raw_error: err instanceof Error ? err.message : t.proposalFailed,
        schema_validation: 'not_validated',
        safety_validation: 'non_authority_envelope_applied',
        http_request_performed: false,
        model_call_performed: false,
        generation_performed: false,
        prompt_payload_sent: false,
        context_payload_sent: false,
        memory_write_performed: false,
        tool_call_performed: false,
        mcp_call_performed: false,
        shell_command_performed: false,
        file_mutation_performed: false,
        data_sent_external: false,
        transcript_persisted: false,
        journal_mutated: false,
        evidence_mutated: false,
        runtime_state_mutated: false,
        authority: false,
        runtime_dispatch_allowed: false,
        execution_permission: 'not_granted_by_model_gateway',
        evidence: false,
        evidence_provided_by_model: false,
        verifier_success: false,
        approval_granted: false,
        permission_granted: false,
        capability_lease_granted: false,
        model_output_is_truth: false,
        model_output_is_evidence: false,
        model_output_is_verifier_success: false,
      });
    } finally {
      setProposalLoading(false);
    }
  }, [language, proposalLoading, proposalPrompt, status, t.proposalFailed]);

  const gatewayStatus = status?.model_gateway.status ?? 'unknown';
  const lmStudio = status?.lm_studio;
  const integrationCount = status?.model_hub_integrations.length ?? 0;
  const modelName = lmStudio?.model || t.notConfigured;
  const configReasons = [...(lmStudio?.failure_reasons ?? []), ...(lmStudio?.warnings ?? [])];

  return (
    <section className="rounded-2xl border border-accent/20 bg-accent/[0.035] p-5 shadow-2xl shadow-black/20">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.2em] text-accent">
            <BrainCircuit size={15} />
            {t.eyebrow}
          </div>
          <h2 className="mt-2 text-xl font-semibold tracking-tight text-white">{t.title}</h2>
          <p className="mt-2 max-w-3xl text-sm leading-7 text-foreground/60">{t.subtitle}</p>
        </div>
        <div className="flex max-w-full flex-wrap gap-2 xl:justify-end">
          <StatusBadge label={t.localOnly} tone="info" icon={<ShieldCheck size={12} />} />
          <StatusBadge label={t.noCloudFallback} tone="unknown" />
          <StatusBadge label={statusLabel(gatewayStatus, t)} tone={statusTone(gatewayStatus)} />
        </div>
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-[1fr_1.1fr]">
        <div className="rounded-xl border border-white/10 bg-black/20 p-4">
          <div className="mb-3 flex items-center justify-between gap-3">
            <h3 className="text-sm font-semibold text-white">{t.connection}</h3>
            <button
              type="button"
              onClick={() => void refreshStatus()}
              disabled={loadState === 'loading'}
              className="inline-flex h-8 items-center gap-2 rounded-md border border-white/10 bg-white/[0.04] px-3 text-[11px] font-bold uppercase tracking-wider text-foreground/60 transition-colors hover:border-accent/30 hover:text-accent disabled:cursor-not-allowed disabled:opacity-45"
            >
              {loadState === 'loading' ? <Loader2 size={13} className="animate-spin" /> : <RefreshCw size={13} />}
              {t.refresh}
            </button>
          </div>
          {statusError && (
            <div className="mb-3 rounded-lg border border-danger/25 bg-danger/10 p-3 text-xs text-danger">
              {statusError}
            </div>
          )}
          <div className="grid gap-2">
            <FactRow label={t.provider} value={lmStudio?.provider ?? 'lm_studio'} />
            <FactRow label={t.baseUrl} value={lmStudio?.base_url ?? t.unknown} />
            <FactRow label={t.model} value={modelName} />
            <FactRow label={t.configState} value={lmStudio?.enabled ? t.enabled : t.disabled} />
            <FactRow label={t.modelHubRecords} value={String(integrationCount)} />
            <FactRow label={t.liveHealth} value={t.probeRequired} />
          </div>
          {configReasons.length > 0 && (
            <div className="mt-3 rounded-lg border border-warning/20 bg-warning/[0.045] p-3">
              <p className="text-[11px] font-bold uppercase tracking-wider text-warning">{t.reasonsAndWarnings}</p>
              <ul className="mt-2 space-y-1">
                {configReasons.map((reason, index) => (
                  <li key={`${reason}-${index}`} className="break-words text-xs leading-5 text-foreground/62">
                    {reason}
                  </li>
                ))}
              </ul>
            </div>
          )}
          <div className="mt-4 flex flex-wrap gap-2">
            <StatusBadge label={t.noMemoryWrite} tone="unknown" />
            <StatusBadge label={t.noExecution} tone="unknown" />
            <StatusBadge label={t.noExternalApi} tone="unknown" />
            <StatusBadge label={t.noEnvWrite} tone="unknown" />
          </div>
        </div>

        <div className="rounded-xl border border-white/10 bg-black/20 p-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div className="min-w-0">
              <h3 className="text-sm font-semibold text-white">{t.userTriggeredActions}</h3>
              <p className="mt-1 text-xs leading-6 text-foreground/52">{t.userTriggeredCopy}</p>
            </div>
            <button
              type="button"
              onClick={() => void runProbe()}
              disabled={probeLoading}
              className="inline-flex min-h-[38px] items-center justify-center gap-2 rounded-md border border-accent/30 bg-accent/10 px-3 text-[11px] font-bold uppercase tracking-wider text-accent transition-colors hover:bg-accent/15 disabled:cursor-not-allowed disabled:opacity-45"
            >
              {probeLoading ? <Loader2 size={14} className="animate-spin" /> : <PlugZap size={14} />}
              {t.probe}
            </button>
          </div>

          {probeResult && (
            <ResultBox
              title={t.lastProbe}
              status={probeResult.status}
              lines={[
                `${t.status}: ${statusLabel(probeResult.status, t)}`,
                `${t.httpRequest}: ${String(probeResult.http_request_performed)}`,
                `${t.modelCall}: ${String(probeResult.model_call_performed)}`,
                ...probeResult.failure_reasons.map((reason) => `${t.reason}: ${reason}`),
              ]}
            />
          )}

          <div className="mt-4 rounded-lg border border-white/10 bg-white/[0.025] p-3">
            <label className="text-xs font-semibold text-foreground/75">{t.proposalComposer}</label>
            <textarea
              value={proposalPrompt}
              onChange={(event) => setProposalPrompt(event.target.value)}
              rows={4}
              className="mt-2 min-h-[104px] w-full resize-none rounded-md border border-white/10 bg-black/25 p-3 text-sm leading-6 text-foreground/88 placeholder:text-foreground/30 focus:border-accent/45 focus:outline-none"
              placeholder={t.promptPlaceholder}
            />
            <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-xs leading-5 text-foreground/45">{t.safeContextCopy}</p>
              <button
                type="button"
                onClick={() => void runProposal()}
                disabled={proposalLoading || !proposalPrompt.trim()}
                className="inline-flex min-h-[38px] items-center justify-center gap-2 rounded-md bg-accent px-4 text-[11px] font-bold uppercase tracking-wider text-background transition-colors hover:bg-accent-light disabled:cursor-not-allowed disabled:opacity-45"
              >
                {proposalLoading ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
                {t.sendProposal}
              </button>
            </div>
          </div>

          {proposal && (
            <>
              <ResultBox
                title={t.lastProposal}
                status={proposal.status}
                lines={[
                  `${t.status}: ${statusLabel(proposal.status, t)}`,
                  `${t.modelCall}: ${String(proposal.model_call_performed)}`,
                  `${t.memoryWrite}: ${String(proposal.memory_write_performed)}`,
                  `${t.evidence}: ${String(proposal.evidence)}`,
                  ...proposal.failure_reasons.map((reason) => `${t.reason}: ${reason}`),
                ]}
                body={proposal.output_text}
              />
              <SafetyGrid
                title={t.proposalBoundary}
                safeLabel={t.flagFalse}
                riskLabel={t.needsReview}
                items={[
                  [t.outputNotAuthority, !proposal.authority && !proposal.model_output_is_truth],
                  [t.noVerifierSuccess, !proposal.verifier_success && !proposal.model_output_is_verifier_success],
                  [t.noApprovalGrant, !proposal.approval_granted && !proposal.permission_granted],
                  [t.noCapabilityLease, !proposal.capability_lease_granted],
                  [t.noToolOrMcp, !proposal.tool_call_performed && !proposal.mcp_call_performed],
                  [t.noFileOrShell, !proposal.file_mutation_performed && !proposal.shell_command_performed],
                ]}
              />
            </>
          )}
        </div>
      </div>

      <div className="mt-4 rounded-xl border border-warning/20 bg-warning/[0.04] p-4">
        <div className="flex min-w-0 items-start gap-3">
          <AlertTriangle size={17} className="mt-0.5 shrink-0 text-warning" />
          <p className="min-w-0 break-words text-xs leading-6 text-foreground/58">{t.boundaryCopy}</p>
        </div>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-[1.25fr_1fr]">
        <LocalModelProfilesSection status={status} t={t} modelName={modelName} />
        <ExternalProviderReadinessSection status={status} t={t} />
      </div>

      <div className="mt-4">
        <ExternalProviderBrokerBoundarySection status={status} t={t} />
      </div>
    </section>
  );
};

const ResultBox = ({
  title,
  status,
  lines,
  body,
}: {
  title: string;
  status: string;
  lines: string[];
  body?: string;
}) => (
  <div className="mt-4 rounded-lg border border-white/10 bg-white/[0.025] p-3">
    <div className="mb-2 flex items-center justify-between gap-3">
      <h4 className="text-xs font-semibold text-white">{title}</h4>
      <StatusBadge label={status} tone={statusTone(status)} />
    </div>
    <div className="grid gap-1">
      {lines.map((line, index) => (
        <div key={`${line}-${index}`} className="flex min-w-0 items-start gap-2 text-[11px] text-foreground/50">
          <CheckCircle2 size={11} className="shrink-0 text-accent" />
          <span className="min-w-0 break-words">{line}</span>
        </div>
      ))}
    </div>
    {body && (
      <p className="mt-3 whitespace-pre-wrap rounded-md border border-accent/15 bg-accent/[0.035] p-3 text-sm leading-6 text-foreground/82">
        {body}
      </p>
    )}
  </div>
);

const SafetyGrid = ({
  title,
  safeLabel,
  riskLabel,
  items,
}: {
  title: string;
  safeLabel: string;
  riskLabel: string;
  items: Array<[string, boolean]>;
}) => (
  <div className="mt-3 rounded-lg border border-accent/15 bg-accent/[0.03] p-3">
    <p className="text-[11px] font-bold uppercase tracking-wider text-accent">{title}</p>
    <div className="mt-2 grid gap-2 sm:grid-cols-2">
      {items.map(([label, safe]) => (
        <div
          key={label}
          className="flex items-center justify-between gap-3 rounded-md border border-white/10 bg-black/20 px-2.5 py-1.5"
        >
          <span className="min-w-0 break-words text-[11px] text-foreground/58">{label}</span>
          <StatusBadge label={safe ? safeLabel : riskLabel} tone={safe ? 'unknown' : 'danger'} />
        </div>
      ))}
    </div>
  </div>
);

function buildSafeProposalPrompt(question: string, status: ModelHubStatus | null, language: Language): string {
  const familyCounts = status?.orchestrator_readiness.family_counts ?? {};
  const familySummary = Object.entries(familyCounts)
    .map(([family, count]) => `${family}:${count}`)
    .join(', ');
  const modes = status?.mode_policy_summary.modes
    .map((mode) => `${mode.mode}:execution=${String(mode.mode_allows_execution_now)}`)
    .join(', ');
  const modelHubRecords = status?.model_hub_integrations
    .map((record) => `${record.integration_id}:${record.default_execution_status}`)
    .join(', ');

  return [
    'Aegis local Model Hub proposal request.',
    `Language: ${language}.`,
    'Use only this small safe metadata summary.',
    'Do not claim truth, evidence, verifier success, approval, permission, tool execution, memory write, or runtime health.',
    'Do not ask for cloud fallback. Do not mention secrets, logs, raw journals, raw evidence, or repo content.',
    `LM Studio status: ${status?.lm_studio.status ?? 'unknown'}.`,
    `LM Studio model configured: ${String(status?.lm_studio.model_configured ?? false)}.`,
    `Integration families: ${familySummary || 'unknown'}.`,
    `Model Hub records: ${modelHubRecords || 'unknown'}.`,
    `Mode execution grants: ${modes || 'unknown'}.`,
    `Operator question: ${question}`,
  ].join('\n');
}

function statusLabel(status: string, t: ReturnType<typeof dictionaryFor>['modelHub']): string {
  if (status === 'configured_metadata_only' || status === 'configured') return t.configured;
  if (status === 'ready' || status === 'completed') return t.ready;
  if (status === 'disabled') return t.disabled;
  if (status === 'misconfigured') return t.misconfigured;
  if (status === 'blocked') return t.blocked;
  if (status === 'unavailable') return t.unavailable;
  if (status === 'timeout') return t.timeout;
  if (status === 'error') return t.error;
  return t.unknown;
}

function statusTone(status: string): 'success' | 'info' | 'warning' | 'danger' | 'unknown' {
  if (status === 'ready' || status === 'completed') return 'success';
  if (status === 'configured' || status === 'configured_metadata_only') return 'info';
  if (status === 'disabled' || status === 'misconfigured' || status === 'blocked') return 'warning';
  if (status === 'unavailable' || status === 'timeout' || status === 'error') return 'danger';
  return 'unknown';
}
