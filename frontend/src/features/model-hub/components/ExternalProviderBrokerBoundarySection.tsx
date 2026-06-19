"use client";

import React from 'react';
import { CloudOff, Eye, KeyRound, Loader2, ShieldAlert } from 'lucide-react';

import { StatusBadge } from '@/components/StatusBadge';
import type { dictionaryFor } from '@/i18n';
import { previewExternalProviderBroker } from '@/lib/api';
import type {
  ExternalProviderPromptPreviewResponse,
  ExternalProviderSetupGuidance,
  ModelHubStatus,
} from '@/types/modelHub';

type ModelHubText = ReturnType<typeof dictionaryFor>['modelHub'];

const DEFAULT_PURPOSE = 'explanation';
const DEFAULT_PROMPT = 'Explain the current Aegis Model Hub external provider boundary without calling any provider.';

export const ExternalProviderBrokerBoundarySection = ({
  status,
  t,
}: {
  status: ModelHubStatus | null;
  t: ModelHubText;
}) => {
  const boundary = status?.external_provider_broker_boundary;
  const guidance = React.useMemo(
    () => boundary?.provider_setup_guidance ?? [],
    [boundary],
  );
  const [providerId, setProviderId] = React.useState(guidance[0]?.provider_id ?? 'openrouter');
  const [modelId, setModelId] = React.useState('');
  const [purpose, setPurpose] = React.useState(DEFAULT_PURPOSE);
  const [prompt, setPrompt] = React.useState(DEFAULT_PROMPT);
  const [acknowledgements, setAcknowledgements] = React.useState<Record<string, boolean>>({});
  const [preview, setPreview] = React.useState<ExternalProviderPromptPreviewResponse | null>(null);
  const [previewLoading, setPreviewLoading] = React.useState(false);
  const [previewError, setPreviewError] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (!guidance.length) return;
    if (!guidance.some((item) => item.provider_id === providerId)) {
      setProviderId(guidance[0].provider_id);
    }
  }, [guidance, providerId]);

  const requiredAcknowledgements = boundary?.required_operator_acknowledgements ?? [];
  const selectedProvider = guidance.find((item) => item.provider_id === providerId);

  const runPreview = React.useCallback(async () => {
    if (previewLoading) return;
    setPreviewLoading(true);
    setPreviewError(null);
    setPreview(null);
    try {
      const result = await previewExternalProviderBroker({
        provider_id: providerId,
        model_id: modelId.trim() || undefined,
        purpose,
        prompt,
        operator_acknowledgements: Object.entries(acknowledgements)
          .filter(([, checked]) => checked)
          .map(([item]) => item),
      });
      setPreview(result);
    } catch (err) {
      setPreviewError(err instanceof Error ? err.message : t.previewFailed);
    } finally {
      setPreviewLoading(false);
    }
  }, [acknowledgements, modelId, previewLoading, prompt, providerId, purpose, t.previewFailed]);

  return (
    <div className="rounded-xl border border-white/10 bg-black/20 p-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.18em] text-accent">
            <ShieldAlert size={14} />
            {t.externalBrokerBoundary}
          </div>
          <p className="mt-2 max-w-3xl text-xs leading-6 text-foreground/52">{t.externalBrokerBoundaryCopy}</p>
        </div>
        <div className="flex max-w-full flex-wrap gap-2 lg:justify-end">
          <StatusBadge label={t.brokerPreviewOnly} tone="info" />
          <StatusBadge label={t.cloudDisabled} tone="warning" />
          <StatusBadge label={t.keyInputDisabled} tone="unknown" />
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <StatusBadge label={t.keyNotAuthorization} tone="warning" />
        <StatusBadge label={t.autoFallbackDisabled} tone="unknown" />
        <StatusBadge label={t.noCloudFallback} tone="warning" />
        <StatusBadge label={t.manualOptIn} tone="info" />
        <StatusBadge label={t.promptPreview} tone="info" />
        <StatusBadge label={t.costWarningRequired} tone="warning" />
        <StatusBadge label={t.privacyWarningRequired} tone="warning" />
        <StatusBadge label={t.redactionReviewRequired} tone="warning" />
        <StatusBadge label={t.providerOutputProposalOnly} tone="info" />
      </div>

      <div className="mt-4 grid gap-3 xl:grid-cols-[0.9fr_1.1fr]">
        <div className="space-y-3">
          <div className="rounded-lg border border-white/10 bg-white/[0.025] p-3">
            <div className="mb-2 flex items-center gap-2 text-xs font-semibold text-white">
              <KeyRound size={14} className="text-foreground/45" />
              {t.providerSetup}
            </div>
            <div className="grid gap-2">
              {guidance.map((provider) => (
                <ProviderSetupCard key={provider.provider_id} provider={provider} t={t} />
              ))}
            </div>
          </div>

          <div className="rounded-lg border border-warning/20 bg-warning/[0.04] p-3">
            <div className="flex items-start gap-2">
              <CloudOff size={14} className="mt-0.5 shrink-0 text-warning" />
              <p className="text-xs leading-6 text-foreground/58">
                {boundary?.limitations?.join(' / ') || t.cloudPolicyCopy}
              </p>
            </div>
          </div>
        </div>

        <div className="rounded-lg border border-accent/15 bg-accent/[0.025] p-3">
          <div className="mb-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div className="min-w-0">
              <div className="flex items-center gap-2 text-xs font-semibold text-white">
                <Eye size={14} className="text-accent" />
                {t.providerPromptPreview}
              </div>
              <p className="mt-1 text-[11px] leading-5 text-foreground/48">
                {t.maxPromptChars}: {boundary?.max_prompt_chars ?? 4000}
              </p>
            </div>
            <StatusBadge label={t.noExternalApi} tone="warning" />
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            <label className="text-xs font-semibold text-foreground/70">
              {t.providerSelect}
              <select
                value={providerId}
                onChange={(event) => setProviderId(event.target.value)}
                className="mt-1 h-9 w-full rounded-md border border-white/10 bg-black/25 px-2 text-sm text-foreground/88 focus:border-accent/45 focus:outline-none"
              >
                {guidance.map((provider) => (
                  <option key={provider.provider_id} value={provider.provider_id}>
                    {provider.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="text-xs font-semibold text-foreground/70">
              {t.previewPurpose}
              <select
                value={purpose}
                onChange={(event) => setPurpose(event.target.value)}
                className="mt-1 h-9 w-full rounded-md border border-white/10 bg-black/25 px-2 text-sm text-foreground/88 focus:border-accent/45 focus:outline-none"
              >
                {(boundary?.allowed_preview_purposes ?? [DEFAULT_PURPOSE]).map((item) => (
                  <option key={item} value={item}>
                    {formatToken(item)}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <label className="mt-3 block text-xs font-semibold text-foreground/70">
            {t.modelIdOptional}
            <input
              value={modelId}
              onChange={(event) => setModelId(event.target.value)}
              className="mt-1 h-9 w-full rounded-md border border-white/10 bg-black/25 px-2 text-sm text-foreground/88 placeholder:text-foreground/30 focus:border-accent/45 focus:outline-none"
              placeholder={selectedProvider?.model_placeholder ?? '<future-model-id>'}
            />
          </label>

          <label className="mt-3 block text-xs font-semibold text-foreground/70">
            {t.previewPrompt}
            <textarea
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              rows={5}
              className="mt-1 min-h-[120px] w-full resize-y rounded-md border border-white/10 bg-black/25 p-3 text-sm leading-6 text-foreground/88 placeholder:text-foreground/30 focus:border-accent/45 focus:outline-none"
              placeholder={t.previewPromptPlaceholder}
            />
          </label>

          <div className="mt-3 rounded-md border border-white/10 bg-black/20 p-3">
            <p className="text-[11px] font-bold uppercase tracking-wider text-foreground/55">
              {t.operatorAcknowledgements}
            </p>
            <div className="mt-2 grid gap-1.5 sm:grid-cols-2">
              {requiredAcknowledgements.map((item) => (
                <label key={item} className="flex items-center gap-2 text-[11px] text-foreground/58">
                  <input
                    type="checkbox"
                    checked={Boolean(acknowledgements[item])}
                    onChange={(event) => setAcknowledgements((current) => ({
                      ...current,
                      [item]: event.target.checked,
                    }))}
                    className="h-3.5 w-3.5 accent-accent"
                  />
                  <span className="min-w-0 break-words">{formatToken(item)}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="mt-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-[11px] leading-5 text-foreground/45">{t.operatorEnvOnly}</p>
            <button
              type="button"
              onClick={() => void runPreview()}
              disabled={previewLoading || !prompt.trim()}
              className="inline-flex min-h-[38px] items-center justify-center gap-2 rounded-md border border-accent/35 bg-accent/10 px-4 text-[11px] font-bold uppercase tracking-wider text-accent transition-colors hover:bg-accent/15 disabled:cursor-not-allowed disabled:opacity-45"
            >
              {previewLoading ? <Loader2 size={14} className="animate-spin" /> : <Eye size={14} />}
              {t.dryRunPreview}
            </button>
          </div>

          {previewError && (
            <div className="mt-3 rounded-lg border border-danger/25 bg-danger/10 p-3 text-xs text-danger">
              {previewError}
            </div>
          )}

          {preview && <PreviewResult preview={preview} t={t} />}
        </div>
      </div>
    </div>
  );
};

const ProviderSetupCard = ({
  provider,
  t,
}: {
  provider: ExternalProviderSetupGuidance;
  t: ModelHubText;
}) => (
  <div className="rounded-md border border-white/10 bg-black/20 p-2.5">
    <div className="mb-2 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
      <span className="min-w-0 break-words text-xs font-semibold text-white">{provider.label}</span>
      <StatusBadge
        label={provider.api_key_present ? t.keyPresentCallsDisabled : t.keyMissing}
        tone={provider.api_key_present ? 'warning' : 'unknown'}
      />
    </div>
    <p className="min-w-0 text-[11px] leading-5 text-foreground/50">
      <span>{t.apiKeyPlaceholder}: </span>
      <span className="break-words font-mono">{provider.api_key_placeholder}</span>
    </p>
    <p className="min-w-0 text-[11px] leading-5 text-foreground/50">
      <span>{t.modelPlaceholder}: </span>
      <span className="break-words font-mono">{provider.model_placeholder}</span>
    </p>
  </div>
);

const PreviewResult = ({
  preview,
  t,
}: {
  preview: ExternalProviderPromptPreviewResponse;
  t: ModelHubText;
}) => (
  <div className="mt-4 rounded-lg border border-white/10 bg-white/[0.025] p-3">
    <div className="mb-2 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
      <h4 className="text-xs font-semibold text-white">{t.previewResult}</h4>
      <StatusBadge label={preview.status} tone="warning" />
    </div>
    <div className="grid gap-2 text-[11px] leading-5 text-foreground/52">
      <PreviewList title={t.blockedReasons} items={preview.blocked_reasons} t={t} />
      <PreviewList title={t.riskMarkers} items={preview.heuristic_prompt_risk_markers} t={t} />
      <PreviewList title={t.missingAcknowledgements} items={preview.missing_acknowledgements} t={t} />
      <PreviewList title={t.futureRequirements} items={preview.future_requirements} t={t} />
    </div>
    <div className="mt-3 rounded-md border border-accent/15 bg-black/20 p-3">
      <p className="mb-2 text-[11px] font-bold uppercase tracking-wider text-accent">{t.promptPreviewText}</p>
      <pre className="max-h-48 overflow-auto whitespace-pre-wrap break-words text-xs leading-5 text-foreground/70">
        {preview.prompt_preview || t.none}
      </pre>
    </div>
    <div className="mt-3 flex flex-wrap gap-2">
      <StatusBadge label={`${t.wouldCallProvider}: ${String(preview.would_call_provider)}`} tone="warning" />
      <StatusBadge label={`${t.cloudCall}: ${String(preview.cloud_call_performed)}`} tone="warning" />
      <StatusBadge label={`${t.dataExternal}: ${String(preview.data_sent_external)}`} tone="warning" />
      <StatusBadge label={`${t.keyValueExposed}: ${String(preview.provider_key_value_exposed)}`} tone="warning" />
    </div>
  </div>
);

const PreviewList = ({
  title,
  items,
  t,
}: {
  title: string;
  items: string[];
  t: ModelHubText;
}) => (
  <div>
    <span className="font-semibold text-foreground/70">{title}: </span>
    <span className="break-words">{items.length ? items.map(formatToken).join(', ') : t.none}</span>
  </div>
);

function formatToken(value: string): string {
  return value.replace(/_/g, ' ');
}
