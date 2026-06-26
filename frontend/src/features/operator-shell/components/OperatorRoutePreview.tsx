"use client";

import { ChevronDown, GitBranch, ShieldCheck } from 'lucide-react';

import { dictionaryFor } from '@/i18n';
import { useOperatorStore } from '@/store/useOperatorStore';
import { useUIStore } from '@/store/useUIStore';
import type {
  OperatorCapabilityClassification,
  OperatorDecisionPreview,
  OperatorIntent,
  OperatorRouteId,
} from '@/types/operator';

export const OperatorRoutePreview = ({ decision }: { decision: OperatorDecisionPreview | null }) => {
  const language = useUIStore((state) => state.language);
  const t = dictionaryFor(language).operatorShell;
  const modelPreference = useOperatorStore((state) => state.modelPreference);
  const planningDetail = useOperatorStore((state) => state.planningDetail);
  if (!decision) return null;

  return (
    <details className="group rounded-lg border border-[#302f2c] bg-[#181817]">
      <summary className="flex min-h-12 cursor-pointer list-none items-center justify-between gap-3 px-4 py-3">
        <span className="flex min-w-0 items-center gap-2 text-xs text-[#918d86]">
          <GitBranch size={14} className="shrink-0 text-[#f4bf4f]" />
          <span className="truncate">{t.routePreviewTitle}: {formatRoute(decision.routeId, t)}</span>
        </span>
        <span className="flex shrink-0 items-center gap-2 text-[11px] text-[#716d66]">
          {decision.previewSource === 'backend_contract' ? t.previewSourceBackend : t.previewSourceFallback}
          <ChevronDown size={15} className="transition-transform group-open:rotate-180" />
        </span>
      </summary>
      <div className="border-t border-[#302f2c] px-4 py-4">
        <dl className="grid gap-4 text-xs sm:grid-cols-2">
          <PreviewCell label={t.detectedIntent} value={decision.intents.map((intent) => formatIntent(intent, t)).join(' + ')} />
          <PreviewCell label={t.proposedRoute} value={formatRoute(decision.routeId, t)} />
          <PreviewCell label={t.modelPreferenceLabel} value={t[`modelPreference_${modelPreference}`]} />
          <PreviewCell label={t.planningDetailLabel} value={t[`planningDetail_${planningDetail}`]} />
        </dl>
        <section
          aria-labelledby="operator-capability-assessment-heading"
          className="mt-4 border-t border-[#302f2c] pt-4"
        >
          <h3
            id="operator-capability-assessment-heading"
            className="flex items-center gap-2 text-xs font-semibold text-[#c9c5bc]"
          >
            <ShieldCheck size={14} aria-hidden="true" className="shrink-0 text-[#f4bf4f]" />
            {t.capabilityAssessmentTitle}
          </h3>
          {decision.capabilityAssessment ? (
            <div className="mt-2 space-y-2 text-[11px] leading-5 text-[#918d86]">
              <p>
                <span className="font-medium text-[#d7b469]">
                  {formatCapabilityClassification(decision.capabilityAssessment.classification, t)}
                </span>
                {' - '}{decision.capabilityAssessment.rationale}
              </p>
              <p>
                <span className="font-medium text-[#c9c5bc]">{t.capabilityAssessmentBoundaryLabel}: </span>
                {decision.capabilityAssessment.boundary}
              </p>
              <p className="text-[#77736d]">{t.capabilityAssessmentPreviewCopy}</p>
            </div>
          ) : (
            <p className="mt-2 text-[11px] leading-5 text-[#77736d]">
              {t.capabilityAssessmentUnavailable}
            </p>
          )}
        </section>
        <p className="mt-4 flex items-start gap-2 text-[11px] leading-5 text-[#77736d]">
          <ShieldCheck size={13} className="mt-0.5 shrink-0 text-[#f4bf4f]" />
          {t.routePreviewSafetyCopy}
        </p>
      </div>
    </details>
  );
};

const PreviewCell = ({ label, value }: { label: string; value: string }) => (
  <div className="min-w-0">
    <dt className="text-[#716d66]">{label}</dt>
    <dd className="mt-1 break-words font-medium leading-5 text-[#c9c5bc]">{value}</dd>
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

function formatCapabilityClassification(
  classification: OperatorCapabilityClassification,
  t: ReturnType<typeof dictionaryFor>['operatorShell'],
): string {
  const labels: Record<OperatorCapabilityClassification, string> = {
    observe_only: t.capabilityObserveOnly,
    explain_only: t.capabilityExplainOnly,
    proposal_only: t.capabilityProposalOnly,
    approval_required: t.capabilityApprovalRequired,
    execution_unavailable: t.capabilityExecutionUnavailable,
    provider_unavailable: t.capabilityProviderUnavailable,
    unsupported_or_ambiguous: t.capabilityUnsupportedOrAmbiguous,
  };
  return labels[classification];
}
