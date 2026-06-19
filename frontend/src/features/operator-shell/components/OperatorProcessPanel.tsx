"use client";

import React from 'react';
import { CheckCircle2, CircleDashed, Clock3, XCircle } from 'lucide-react';

import { StatusBadge } from '@/components/StatusBadge';
import { dictionaryFor } from '@/i18n';
import { useOperatorStore } from '@/store/useOperatorStore';
import { useUIStore } from '@/store/useUIStore';
import type { OperatorDecisionPreview, OperatorTraceItem, OperatorTraceStep } from '@/types/operator';

import { formatRoute } from './OperatorRoutePreview';

export const OperatorProcessPanel = () => {
  const language = useUIStore((state) => state.language);
  const t = dictionaryFor(language).operatorShell;
  const traceItems = useOperatorStore((state) => state.traceItems);
  const decision = useOperatorStore((state) => state.lastDecision);
  const items = traceItems.length ? traceItems : emptyTrace();

  return (
    <section className="rounded-2xl border border-white/10 bg-white/[0.045] p-4 shadow-xl shadow-black/15">
      <div className="mb-3 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-accent">{t.processTraceTitle}</p>
          <p className="mt-2 text-xs leading-5 text-foreground/50">{t.processTraceCopy}</p>
        </div>
        <StatusBadge label={t.metadataOnly} tone="unknown" />
      </div>
      <div className="space-y-2">
        {items.map((item) => (
          <TraceRow key={item.id} item={item} decision={decision} />
        ))}
      </div>
      <p className="mt-3 rounded-md border border-white/10 bg-black/20 p-3 text-[11px] leading-5 text-foreground/50">
        {t.processTraceSafetyCopy}
      </p>
    </section>
  );
};

const TraceRow = ({ item, decision }: { item: OperatorTraceItem; decision: OperatorDecisionPreview | null }) => {
  const language = useUIStore((state) => state.language);
  const t = dictionaryFor(language).operatorShell;
  return (
    <div className="flex min-w-0 items-start gap-3 rounded-md border border-white/10 bg-black/20 p-3">
      <span className="mt-0.5 shrink-0">{traceIcon(item.status)}</span>
      <div className="min-w-0 flex-1">
        <div className="flex items-center justify-between gap-2">
          <span className="text-xs font-semibold text-white">{traceLabel(item.step, t)}</span>
          <StatusBadge label={traceStatusLabel(item.status, t)} tone={traceTone(item.status)} />
        </div>
        <p className="mt-1 break-words text-[11px] leading-5 text-foreground/50">{item.detail ?? traceDetail(item.step, decision, t)}</p>
      </div>
    </div>
  );
};

function emptyTrace(): OperatorTraceItem[] {
  return [
    { id: 'waiting-request', step: 'request_received', status: 'waiting' },
    { id: 'waiting-intent', step: 'intent_preview_generated', status: 'waiting' },
    { id: 'waiting-artifact', step: 'artifact_draft_created', status: 'waiting' },
  ];
}

function traceIcon(status: OperatorTraceItem['status']): React.ReactNode {
  if (status === 'done') return <CheckCircle2 size={15} className="text-success" />;
  if (status === 'blocked') return <XCircle size={15} className="text-warning" />;
  if (status === 'info') return <CircleDashed size={15} className="text-accent" />;
  return <Clock3 size={15} className="text-foreground/42" />;
}

function traceTone(status: OperatorTraceItem['status']): 'success' | 'info' | 'warning' | 'danger' | 'unknown' {
  if (status === 'done') return 'success';
  if (status === 'blocked') return 'warning';
  if (status === 'info') return 'info';
  return 'unknown';
}

function traceStatusLabel(status: OperatorTraceItem['status'], t: ReturnType<typeof dictionaryFor>['operatorShell']): string {
  if (status === 'done') return t.traceDone;
  if (status === 'blocked') return t.traceBlocked;
  if (status === 'info') return t.traceInfo;
  return t.traceWaiting;
}

function traceLabel(step: OperatorTraceStep, t: ReturnType<typeof dictionaryFor>['operatorShell']): string {
  const labels: Record<OperatorTraceStep, string> = {
    request_received: t.traceRequestReceived,
    intent_preview_generated: t.traceIntentPreviewGenerated,
    route_selected: t.traceRouteSelected,
    model_candidate_selected: t.traceModelCandidateSelected,
    permission_boundary_evaluated: t.tracePermissionBoundaryEvaluated,
    cloud_boundary_evaluated: t.traceCloudBoundaryEvaluated,
    memory_policy_evaluated: t.traceMemoryPolicyEvaluated,
    artifact_draft_created: t.traceArtifactDraftCreated,
    blocked_actions_not_performed: t.traceBlockedActions,
  };
  return labels[step];
}

function traceDetail(
  step: OperatorTraceStep,
  decision: OperatorDecisionPreview | null,
  t: ReturnType<typeof dictionaryFor>['operatorShell'],
): string {
  if (!decision) return t.traceWaitingDetail;
  if (step === 'route_selected') return `${t.proposedRoute}: ${formatRoute(decision.routeId, t)}`;
  if (step === 'model_candidate_selected') {
    return decision.modelCandidates.map((item) => `${item.profileId}: ${item.modelHint}`).join(' / ');
  }
  if (step === 'permission_boundary_evaluated') {
    return decision.approvalNeeded ? t.tracePermissionBlockedDetail : t.tracePermissionSafeDetail;
  }
  if (step === 'cloud_boundary_evaluated') {
    return decision.researchBoundaryRequired ? t.traceCloudBlockedDetail : t.traceCloudSafeDetail;
  }
  if (step === 'memory_policy_evaluated') {
    return decision.memoryActionProposed ? t.traceMemoryProposedDetail : t.traceMemorySafeDetail;
  }
  if (step === 'artifact_draft_created') return t.traceArtifactDetail;
  if (step === 'blocked_actions_not_performed') return t.traceNoActionsDetail;
  if (step === 'intent_preview_generated') return t.traceIntentDetail;
  return t.traceRequestDetail;
}
