"use client";

import React from 'react';
import { Check, Copy, FileText } from 'lucide-react';

import { StatusBadge } from '@/components/StatusBadge';
import { dictionaryFor } from '@/i18n';
import { useOperatorStore } from '@/store/useOperatorStore';
import { useUIStore } from '@/store/useUIStore';
import type { OperatorArtifact, OperatorArtifactType } from '@/types/operator';

export const OperatorArtifactsPanel = () => {
  const language = useUIStore((state) => state.language);
  const t = dictionaryFor(language).operatorShell;
  const artifacts = useOperatorStore((state) => state.artifacts);
  const selectedArtifactId = useOperatorStore((state) => state.selectedArtifactId);
  const selectArtifact = useOperatorStore((state) => state.selectArtifact);
  const selected = artifacts.find((item) => item.id === selectedArtifactId) ?? artifacts[0] ?? null;
  const [copied, setCopied] = React.useState(false);

  const copySelected = React.useCallback(async () => {
    if (!selected?.body || typeof navigator === 'undefined' || !navigator.clipboard) return;
    try {
      await navigator.clipboard.writeText(selected.body);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1400);
    } catch {
      setCopied(false);
    }
  }, [selected?.body]);

  return (
    <section className="rounded-2xl border border-white/10 bg-white/[0.045] p-4 shadow-xl shadow-black/15">
      <div className="mb-3 flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-accent">{t.artifactsTitle}</p>
          <p className="mt-2 text-xs leading-5 text-foreground/50">{t.artifactsCopy}</p>
        </div>
        <StatusBadge label={t.previewOnly} tone="info" />
      </div>

      {artifacts.length === 0 ? (
        <div className="rounded-md border border-white/10 bg-black/20 p-4">
          <p className="text-sm font-semibold text-white">{t.noArtifactsTitle}</p>
          <p className="mt-2 text-xs leading-6 text-foreground/50">{t.noArtifactsCopy}</p>
        </div>
      ) : (
        <div className="grid gap-2">
          {artifacts.map((artifact) => (
            <button
              key={artifact.id}
              type="button"
              onClick={() => selectArtifact(artifact.id)}
              className={`rounded-md border p-3 text-left transition-colors ${
                selected?.id === artifact.id
                  ? 'border-accent/30 bg-accent/[0.08]'
                  : 'border-white/10 bg-black/20 hover:border-white/20'
              }`}
            >
              <div className="flex items-center gap-2">
                <FileText size={14} className="shrink-0 text-accent" />
                <span className="min-w-0 break-words text-xs font-semibold text-white">{artifact.title ?? artifactTitle(artifact.type, t)}</span>
              </div>
              <p className="mt-2 line-clamp-2 text-[11px] leading-5 text-foreground/50">{artifact.request}</p>
            </button>
          ))}
        </div>
      )}

      {selected && (
        <div className="mt-3 rounded-xl border border-white/10 bg-black/20 p-3">
          <div className="mb-2 flex items-center justify-between gap-2">
            <span className="text-xs font-semibold text-white">{selected.title ?? artifactTitle(selected.type, t)}</span>
            <button
              type="button"
              onClick={copySelected}
              disabled={!selected.body}
              className="inline-flex h-7 items-center gap-1.5 rounded-lg border border-white/10 bg-white/[0.04] px-2 text-[11px] font-semibold text-foreground/58 hover:border-accent/30 hover:text-accent disabled:cursor-not-allowed disabled:opacity-40"
            >
              {copied ? <Check size={12} /> : <Copy size={12} />}
              {copied ? t.copiedDraft : t.copyDraft}
            </button>
          </div>
          <p className="text-[11px] leading-5 text-foreground/54">{selected.summary ?? artifactSummary(selected, t)}</p>
          {selected.body && (
            <pre className="mt-3 max-h-56 overflow-y-auto whitespace-pre-wrap break-words rounded-lg border border-white/10 bg-[#111217] p-3 font-sans text-[11px] leading-5 text-foreground/62 custom-scrollbar">
              {selected.body}
            </pre>
          )}
          <div className="mt-3 flex flex-wrap gap-1.5">
            {selected.safetyFlags.map((flag) => (
              <StatusBadge key={flag} label={formatFlag(flag, t)} tone="unknown" />
            ))}
          </div>
        </div>
      )}
    </section>
  );
};

function artifactTitle(type: OperatorArtifactType, t: ReturnType<typeof dictionaryFor>['operatorShell']): string {
  const labels: Record<OperatorArtifactType, string> = {
    safe_plan_draft: t.artifactSafePlanDraft,
    codex_prompt_draft: t.artifactCodexPromptDraft,
    ui_review_plan: t.artifactUiReviewPlan,
    research_plan: t.artifactResearchPlan,
    memory_action_preview: t.artifactMemoryActionPreview,
    model_routing_summary: t.artifactModelRoutingSummary,
    command_approval_preview: t.artifactCommandApprovalPreview,
  };
  return labels[type];
}

function artifactSummary(artifact: OperatorArtifact, t: ReturnType<typeof dictionaryFor>['operatorShell']): string {
  const labels: Record<OperatorArtifactType, string> = {
    safe_plan_draft: t.artifactSafePlanSummary,
    codex_prompt_draft: t.artifactCodexPromptSummary,
    ui_review_plan: t.artifactUiReviewSummary,
    research_plan: t.artifactResearchPlanSummary,
    memory_action_preview: t.artifactMemoryActionSummary,
    model_routing_summary: t.artifactModelRoutingSummaryCopy,
    command_approval_preview: t.artifactCommandApprovalSummary,
  };
  return `${labels[artifact.type]} ${t.artifactRequestPrefix}: "${artifact.request}"`;
}

function formatFlag(flag: string, t: ReturnType<typeof dictionaryFor>['operatorShell']): string {
  const labels: Record<string, string> = {
    no_command_execution: t.noCommandExecution,
    no_model_call: t.noModelCall,
    no_cloud_call: t.noCloudCall,
    no_external_provider_call: t.noExternalProviderCall,
    no_kimi_moonshot_call: t.noKimiMoonshotCall,
    no_image_upload: t.noImageUpload,
    no_video_upload: t.noVideoUpload,
    no_memory_write: t.noMemoryWrite,
    no_tool_call: t.noToolCall,
    no_evidence: t.noEvidence,
    no_verifier_success: t.noVerifierSuccess,
    no_approval_or_permission_grant: t.noApprovalOrPermission,
  };
  return labels[flag] ?? flag;
}
