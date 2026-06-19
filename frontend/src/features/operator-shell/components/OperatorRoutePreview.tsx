"use client";

import React from 'react';
import { ChevronDown, GitBranch, LockKeyhole, ShieldAlert } from 'lucide-react';

import { StatusBadge } from '@/components/StatusBadge';
import { dictionaryFor } from '@/i18n';
import { useUIStore } from '@/store/useUIStore';
import type { OperatorDecisionPreview, OperatorIntent, OperatorRouteId } from '@/types/operator';

export const OperatorRoutePreview = ({ decision }: { decision: OperatorDecisionPreview | null }) => {
  const language = useUIStore((state) => state.language);
  const t = dictionaryFor(language).operatorShell;

  if (!decision) {
    return (
      <section className="rounded-2xl border border-white/10 bg-white/[0.035] p-4">
        <div className="flex items-start gap-3">
          <GitBranch size={17} className="mt-0.5 shrink-0 text-accent" />
          <div className="min-w-0">
            <h2 className="text-sm font-semibold text-white">{t.routePreviewTitle}</h2>
            <p className="mt-2 text-xs leading-6 text-foreground/55">{t.routePreviewEmpty}</p>
          </div>
        </div>
      </section>
    );
  }

  return (
    <details className="group rounded-2xl border border-white/10 bg-white/[0.035] p-4">
      <summary className="flex cursor-pointer list-none flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-2 text-xs font-semibold text-accent">
            <GitBranch size={15} />
            {t.autoDecisionTitle}
          </div>
          <h2 className="mt-1 break-words text-base font-semibold text-white">{formatRoute(decision.routeId, t)}</h2>
          <p className="mt-1 line-clamp-2 break-words text-xs leading-5 text-foreground/52">{decision.request}</p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <StatusBadge
            label={decision.previewSource === 'backend_contract' ? t.previewSourceBackend : t.previewSourceFallback}
            tone={decision.previewSource === 'backend_contract' ? 'success' : 'warning'}
          />
          <ChevronDown size={16} className="text-foreground/45 transition-transform group-open:rotate-180" />
        </div>
      </summary>

      <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <PreviewCell label={t.detectedIntent} value={decision.intents.map((intent) => formatIntent(intent, t)).join(' + ')} />
        <PreviewCell label={t.proposedRoute} value={formatRoute(decision.routeId, t)} />
        <PreviewCell label={t.localModelCandidate} value={decision.modelCandidates.map((item) => `${item.profileId}: ${item.modelHint}`).join(' / ')} />
        <PreviewCell label={t.outputArtifact} value={t.artifactPreviewOnly} />
      </div>

      <div className="mt-3 flex max-w-full items-start gap-2 rounded-xl border border-white/10 bg-black/20 p-3">
        <LockKeyhole size={13} className="mt-0.5 shrink-0 text-accent" />
        <p className="text-[11px] leading-5 text-foreground/55">
          {decision.previewSource === 'backend_contract'
            ? t.previewSourceBackendCopy
            : `${t.previewSourceFallbackCopy}${decision.backendPreviewError ? ` ${decision.backendPreviewError}` : ''}`}
        </p>
      </div>

      <div className="mt-3 grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
        <BoundaryFlag label={t.cloud} value={decision.cloudNeeded ? t.approvalRequired : t.notUsed} />
        <BoundaryFlag label={t.memory} value={decision.memoryActionProposed ? t.proposedOnly : t.noAutomaticWrite} />
        <BoundaryFlag label={t.vision} value={decision.visionBoundaryRequired ? t.boundaryRequired : t.notNeeded} />
        <BoundaryFlag label={t.webResearch} value={decision.researchBoundaryRequired ? t.externalBoundaryRequired : t.notNeeded} />
        <BoundaryFlag label={t.execution} value={t.nonePerformed} />
        <BoundaryFlag label={t.approval} value={decision.approvalNeeded ? t.requiredBeforeAction : t.notGranted} />
        <BoundaryFlag label={t.evidence} value={t.notCreated} />
        <BoundaryFlag label={t.verifier} value={t.notCreated} />
      </div>

      <div className="mt-3 flex items-start gap-2 rounded-xl border border-warning/20 bg-warning/[0.05] p-3">
        <ShieldAlert size={15} className="mt-0.5 shrink-0 text-warning" />
        <p className="text-xs leading-6 text-foreground/60">{t.routePreviewSafetyCopy}</p>
      </div>
    </details>
  );
};

const PreviewCell = ({ label, value }: { label: string; value: string }) => (
  <div className="min-w-0 rounded-xl border border-white/10 bg-black/20 p-3">
    <div className="text-[10px] font-semibold text-foreground/38">{label}</div>
    <div className="mt-2 break-words text-xs font-semibold leading-5 text-foreground/78" title={value}>{value}</div>
  </div>
);

const BoundaryFlag = ({ label, value }: { label: string; value: string }) => (
  <div className="flex min-w-0 items-center justify-between gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2">
    <span className="text-xs text-foreground/50">{label}</span>
    <span className="min-w-0 break-words text-right text-xs font-semibold text-foreground/78">{value}</span>
  </div>
);

export function formatIntent(intent: OperatorIntent, t: ReturnType<typeof dictionaryFor>['operatorShell']): string {
  const labels: Record<OperatorIntent, string> = {
    ask_status: t.intentAskStatus,
    safe_plan: t.intentSafePlan,
    code_prompt: t.intentCodePrompt,
    memory_action: t.intentMemoryAction,
    model_hub: t.intentModelHub,
    vision_review: t.intentVisionReview,
    web_research: t.intentWebResearch,
    command_preview: t.intentCommandPreview,
    approval_review: t.intentApprovalReview,
    unknown: t.intentUnknown,
  };
  return labels[intent];
}

export function formatRoute(route: OperatorRouteId, t: ReturnType<typeof dictionaryFor>['operatorShell']): string {
  const labels: Record<OperatorRouteId, string> = {
    status_explainer: t.routeStatusExplainer,
    safe_plan_builder: t.routeSafePlanBuilder,
    code_prompt_builder: t.routeCodePromptBuilder,
    memory_policy_preview: t.routeMemoryPolicyPreview,
    model_hub_review: t.routeModelHubReview,
    vision_review_plan: t.routeVisionReviewPlan,
    vision_to_code_prompt: t.routeVisionToCodePrompt,
    research_plan: t.routeResearchPlan,
    command_approval_preview: t.routeCommandApprovalPreview,
    approval_review: t.routeApprovalReview,
  };
  return labels[route];
}
