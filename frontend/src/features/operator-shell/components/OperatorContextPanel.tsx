"use client";

import React from 'react';
import { Boxes, CircleDot, ShieldCheck } from 'lucide-react';

import { StatusBadge } from '@/components/StatusBadge';
import { dictionaryFor } from '@/i18n';
import { useOperatorStore } from '@/store/useOperatorStore';
import { useUIStore } from '@/store/useUIStore';

import { OperatorArtifactsPanel } from './OperatorArtifactsPanel';
import { OperatorProcessPanel } from './OperatorProcessPanel';
import { OperatorWorkspaceDrawer } from './OperatorWorkspaceDrawer';
import { formatRoute } from './OperatorRoutePreview';

export const OperatorContextPanel = () => {
  const language = useUIStore((state) => state.language);
  const t = dictionaryFor(language).operatorShell;
  const decision = useOperatorStore((state) => state.lastDecision);

  return (
    <aside className="min-w-0 space-y-4">
      <section className="rounded-2xl border border-white/10 bg-[#1b1d22]/80 p-4 shadow-xl shadow-black/15">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2 text-sm font-semibold text-white">
              <Boxes size={17} className="text-accent" />
              {t.contextPanelTitle}
            </div>
            <p className="mt-1 text-xs leading-5 text-foreground/50">{t.contextPanelCopy}</p>
          </div>
          <StatusBadge label={t.metadataOnly} tone="unknown" />
        </div>

        <div className="mt-4 grid gap-2">
          <ContextRow label={t.currentRoute} value={decision ? formatRoute(decision.routeId, t) : t.routePreviewEmptyShort} />
          <ContextRow label={t.execution} value={t.nonePerformed} />
          <ContextRow label={t.memory} value={decision?.memoryActionProposed ? t.proposedOnly : t.noAutomaticWrite} />
          <ContextRow label={t.approval} value={decision?.approvalNeeded ? t.requiredBeforeAction : t.notGranted} />
        </div>

        <div className="mt-4 rounded-xl border border-accent/20 bg-accent/[0.06] p-3">
          <div className="flex items-center gap-2 text-xs font-semibold text-accent">
            <ShieldCheck size={14} />
            {t.backendAuthorityTitle}
          </div>
          <p className="mt-2 text-[11px] leading-5 text-foreground/55">{t.backendAuthorityCopy}</p>
        </div>
      </section>

      <OperatorProcessPanel />
      <OperatorArtifactsPanel />
      <OperatorWorkspaceDrawer />
    </aside>
  );
};

const ContextRow = ({ label, value }: { label: string; value: string }) => (
  <div className="flex min-w-0 items-center justify-between gap-3 rounded-xl border border-white/10 bg-black/20 px-3 py-2">
    <span className="inline-flex min-w-0 items-center gap-2 text-xs text-foreground/50">
      <CircleDot size={10} className="shrink-0 text-accent" />
      <span className="truncate">{label}</span>
    </span>
    <span className="min-w-0 break-words text-right text-xs font-semibold text-foreground/78">{value}</span>
  </div>
);
