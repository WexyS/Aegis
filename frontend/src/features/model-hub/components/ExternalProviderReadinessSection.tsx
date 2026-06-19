import { CloudOff, KeyRound } from 'lucide-react';

import { StatusBadge } from '@/components/StatusBadge';
import type { dictionaryFor } from '@/i18n';
import type { ModelHubStatus } from '@/types/modelHub';

type ModelHubText = ReturnType<typeof dictionaryFor>['modelHub'];

export const ExternalProviderReadinessSection = ({
  status,
  t,
}: {
  status: ModelHubStatus | null;
  t: ModelHubText;
}) => (
  <div className="rounded-xl border border-white/10 bg-black/20 p-4">
    <div className="mb-3 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
      <div className="min-w-0">
        <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.18em] text-accent">
          <CloudOff size={14} />
          {t.externalReadiness}
        </div>
        <p className="mt-2 text-xs leading-6 text-foreground/52">{t.externalReadinessCopy}</p>
      </div>
      <StatusBadge label={t.cloudDisabled} tone="warning" />
    </div>

    <div className="grid gap-2">
      {(status?.external_provider_readiness ?? []).map((provider) => (
        <div key={provider.provider_id} className="min-w-0 rounded-lg border border-white/10 bg-white/[0.025] p-3">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex min-w-0 items-center gap-2">
              <KeyRound size={14} className="shrink-0 text-foreground/45" />
              <span className="min-w-0 break-words text-sm font-semibold text-white">{provider.label}</span>
            </div>
            <StatusBadge
              label={provider.api_key_present ? t.keyPresentCallsDisabled : t.keyMissing}
              tone={provider.api_key_present ? 'warning' : 'unknown'}
            />
          </div>
          <div className="mt-2 flex flex-wrap gap-1.5">
            <StatusBadge label={t.cloudDisabled} tone="warning" />
            <StatusBadge label={t.keyNotAuthorization} tone="warning" />
            <StatusBadge label={t.autoFallbackDisabled} tone="unknown" />
            <StatusBadge label={t.manualOptIn} tone="info" />
            <StatusBadge label={t.promptPreview} tone="info" />
            {provider.cost_warning_required ? <StatusBadge label={t.costWarningRequired} tone="warning" /> : null}
            {provider.privacy_warning_required ? <StatusBadge label={t.privacyWarningRequired} tone="warning" /> : null}
          </div>
          <p className="mt-2 max-w-full overflow-x-auto whitespace-nowrap font-mono text-[11px] leading-5 text-foreground/48">
            {provider.expected_env_vars.join(' / ')}
          </p>
        </div>
      ))}
    </div>

    <div className="mt-3 rounded-lg border border-warning/20 bg-warning/[0.04] p-3">
      <p className="text-xs leading-6 text-foreground/58">
        {status?.cloud_fallback_policy?.automatic_cloud_fallback_allowed === false
          ? t.cloudPolicyCopy
          : t.cloudPolicyUnknown}
      </p>
    </div>
  </div>
);
