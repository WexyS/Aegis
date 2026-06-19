import { Cpu } from 'lucide-react';

import { StatusBadge } from '@/components/StatusBadge';
import type { dictionaryFor } from '@/i18n';
import type { ModelHubStatus } from '@/types/modelHub';

import { ModelHubFactRow } from './ModelHubFactRow';

type ModelHubText = ReturnType<typeof dictionaryFor>['modelHub'];

export const LocalModelProfilesSection = ({
  status,
  t,
  modelName,
}: {
  status: ModelHubStatus | null;
  t: ModelHubText;
  modelName: string;
}) => {
  const activeProfile = status?.active_model_profile_match;
  const recommendedProfileId = status?.recommended_default_profile_id;
  const defaultProfile = status?.local_model_profiles.find(
    (profile) => profile.profile_id === recommendedProfileId,
  );

  return (
    <div className="rounded-xl border border-white/10 bg-black/20 p-4">
      <div className="mb-3 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.18em] text-accent">
            <Cpu size={14} />
            {t.localProfiles}
          </div>
          <p className="mt-2 text-xs leading-6 text-foreground/52">{t.localProfilesCopy}</p>
        </div>
        <div className="flex max-w-full flex-wrap gap-2 sm:justify-end">
          <StatusBadge label={t.noAutoSwitch} tone="unknown" />
          <StatusBadge label={t.recommendationsOnly} tone="info" />
          <StatusBadge label={t.noEnvWrite} tone="unknown" />
          <StatusBadge label={t.probeRequired} tone="warning" />
        </div>
      </div>

      <div className="grid gap-2 lg:grid-cols-2">
        <ModelHubFactRow label={t.targetHardware} value={formatHardware(status)} />
        <ModelHubFactRow label={t.configuredModel} value={modelName} />
        <ModelHubFactRow label={t.matchedProfile} value={activeProfile?.matched_profile_label ?? t.unknown} />
        <ModelHubFactRow label={t.defaultProfile} value={defaultProfile?.preferred_model_id_hint ?? 'google/gemma-4-12b'} />
      </div>

      {activeProfile?.warnings?.length ? (
        <div className="mt-3 rounded-lg border border-warning/20 bg-warning/[0.045] p-3">
          <p className="text-[11px] font-bold uppercase tracking-wider text-warning">{t.activeProfileWarnings}</p>
          <ul className="mt-2 space-y-1">
            {activeProfile.warnings.map((warning, index) => (
              <li key={`${warning}-${index}`} className="break-words text-xs leading-5 text-foreground/62">
                {warning}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {(status?.local_model_profiles ?? []).map((profile) => (
          <div key={profile.profile_id} className="min-w-0 rounded-lg border border-white/10 bg-white/[0.025] p-3">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
              <div className="min-w-0">
                <h4 className="break-words text-sm font-semibold text-white">{profile.label}</h4>
                <p className="mt-1 break-words font-mono text-[11px] leading-5 text-foreground/48">
                  {profile.preferred_model_id_hint}
                </p>
              </div>
              <StatusBadge label={memoryPressureLabel(profile.memory_pressure, t)} tone={profileTone(profile.memory_pressure)} />
            </div>
            <p className="mt-2 break-words text-xs leading-5 text-foreground/56">{profile.purpose}</p>
            <div className="mt-3 flex flex-wrap gap-1.5">
              {profile.default_profile ? <StatusBadge label={t.defaultProfileBadge} tone="info" /> : null}
              {profile.manual_selection_required ? <StatusBadge label={t.manualSelection} tone="warning" /> : null}
              <StatusBadge
                label={profile.eligible_for_completion ? t.completionCandidate : t.notForCompletion}
                tone={profile.eligible_for_completion ? 'unknown' : 'warning'}
              />
              {profile.eligible_for_rerank ? <StatusBadge label={t.rerankOnly} tone="info" /> : null}
            </div>
            <div className="mt-3 grid gap-1 text-[11px] leading-5 text-foreground/48">
              <span>{t.inputChars}: {profile.recommended_max_input_chars}</span>
              <span>{t.outputTokens}: {profile.recommended_max_output_tokens}</span>
              <span>{t.timeoutSeconds}: {profile.recommended_timeout_seconds}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

function profileTone(memoryPressure: string): 'success' | 'info' | 'warning' | 'danger' | 'unknown' {
  if (memoryPressure === 'low') return 'success';
  if (memoryPressure === 'balanced') return 'info';
  if (memoryPressure === 'medium_high') return 'warning';
  if (memoryPressure === 'high') return 'danger';
  return 'unknown';
}

function memoryPressureLabel(memoryPressure: string, t: ModelHubText): string {
  if (memoryPressure === 'low') return t.memoryPressureLow;
  if (memoryPressure === 'balanced') return t.memoryPressureBalanced;
  if (memoryPressure === 'medium_high') return t.memoryPressureMediumHigh;
  if (memoryPressure === 'high') return t.memoryPressureHigh;
  return memoryPressure;
}

function formatHardware(status: ModelHubStatus | null): string {
  if (!status?.resource_guardrails) return 'RTX 4080 / 12GB VRAM / 32GB RAM';
  return `${status.resource_guardrails.gpu} / ${status.resource_guardrails.vram_gb_target}GB VRAM / ${status.resource_guardrails.system_ram_gb_target}GB RAM`;
}
