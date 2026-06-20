"use client";

import { CircleDot, ShieldCheck } from 'lucide-react';

import { dictionaryFor } from '@/i18n';
import { useOperatorStore } from '@/store/useOperatorStore';
import { useUIStore } from '@/store/useUIStore';

import { OperatorProcessPanel } from './OperatorProcessPanel';
import { OperatorWorkspaceDrawer } from './OperatorWorkspaceDrawer';
import { formatRoute } from './OperatorRoutePreview';

export const OperatorContextPanel = () => {
  const language = useUIStore((state) => state.language);
  const t = dictionaryFor(language).operatorShell;
  const decision = useOperatorStore((state) => state.lastDecision);

  return (
    <div className="min-w-0 space-y-4">
      <section className="rounded-lg border border-[#33312e] bg-[#1d1d1c] p-4">
        <p className="text-xs leading-5 text-[#8f8b84]">{t.contextPanelCopy}</p>
        <div className="mt-4 space-y-2">
          <ContextRow label={t.currentRoute} value={decision ? formatRoute(decision.routeId, t) : t.routePreviewEmptyShort} />
          <ContextRow label={t.execution} value={t.nonePerformed} />
          <ContextRow label={t.memory} value={decision?.memoryActionProposed ? t.proposedOnly : t.noAutomaticWrite} />
          <ContextRow label={t.approval} value={decision?.approvalNeeded ? t.requiredBeforeAction : t.notGranted} />
        </div>
        <p className="mt-4 flex gap-2 border-t border-[#33312e] pt-4 text-[11px] leading-5 text-[#77736d]">
          <ShieldCheck size={13} className="mt-0.5 shrink-0 text-[#f4bf4f]" />
          {t.backendAuthorityCopy}
        </p>
      </section>

      <details className="rounded-lg border border-[#33312e] bg-[#1d1d1c]">
        <summary className="cursor-pointer px-4 py-3 text-xs font-semibold text-[#aaa69e]">{t.processTraceTitle}</summary>
        <div className="border-t border-[#33312e] p-3"><OperatorProcessPanel /></div>
      </details>

      <details className="rounded-lg border border-[#33312e] bg-[#1d1d1c]">
        <summary className="cursor-pointer px-4 py-3 text-xs font-semibold text-[#aaa69e]">{t.shortcutsTitle}</summary>
        <div className="border-t border-[#33312e] p-3"><OperatorWorkspaceDrawer /></div>
      </details>
    </div>
  );
};

const ContextRow = ({ label, value }: { label: string; value: string }) => (
  <div className="flex min-w-0 items-center justify-between gap-3 py-1.5">
    <span className="inline-flex min-w-0 items-center gap-2 text-xs text-[#817d76]">
      <CircleDot size={9} className="shrink-0 text-[#f4bf4f]" />
      <span className="truncate">{label}</span>
    </span>
    <span className="min-w-0 break-words text-right text-xs font-medium text-[#c9c5bc]">{value}</span>
  </div>
);
