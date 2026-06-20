"use client";

import React from 'react';
import { Paperclip, SendHorizontal, ShieldCheck } from 'lucide-react';

import { dictionaryFor } from '@/i18n';
import { useOperatorStore } from '@/store/useOperatorStore';
import { useUIStore } from '@/store/useUIStore';
import type { OperatorModelPreference, OperatorPlanningDetail } from '@/types/operator';

export const OperatorComposer = ({ compact = false }: { compact?: boolean }) => {
  const language = useUIStore((state) => state.language);
  const t = dictionaryFor(language).operatorShell;
  const composerText = useOperatorStore((state) => state.composerText);
  const setComposerText = useOperatorStore((state) => state.setComposerText);
  const submitPreviewRequest = useOperatorStore((state) => state.submitPreviewRequest);
  const modelPreference = useOperatorStore((state) => state.modelPreference);
  const setModelPreference = useOperatorStore((state) => state.setModelPreference);
  const planningDetail = useOperatorStore((state) => state.planningDetail);
  const setPlanningDetail = useOperatorStore((state) => state.setPlanningDetail);
  const lastDecision = useOperatorStore((state) => state.lastDecision);
  const [routeAnnouncement, setRouteAnnouncement] = React.useState('');

  React.useEffect(() => {
    if (lastDecision) setRouteAnnouncement(t.routePreviewCompleted);
  }, [lastDecision, t.routePreviewCompleted]);

  const submitRoutePreview = React.useCallback(async () => {
    if (!composerText.trim()) return;
    setRouteAnnouncement(t.routePreviewStarted);
    const decision = await submitPreviewRequest();
    setRouteAnnouncement(decision ? t.routePreviewCompleted : t.routePreviewUnavailable);
  }, [composerText, submitPreviewRequest, t.routePreviewCompleted, t.routePreviewStarted, t.routePreviewUnavailable]);

  return (
    <section className="rounded-xl border border-[#3a3834] bg-[#242321] shadow-[0_18px_48px_rgba(0,0,0,0.22)]">
      <textarea
        value={composerText}
        onChange={(event) => setComposerText(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            void submitRoutePreview();
          }
        }}
        rows={compact ? 2 : 4}
        className={`w-full resize-none bg-transparent px-4 pt-4 text-[15px] leading-7 text-[#ece9e2] outline-none placeholder:text-[#77736d] ${compact ? 'min-h-20' : 'min-h-32'}`}
        placeholder={t.composerPlaceholder}
        aria-label={t.composerTitle}
      />

      <div className="flex flex-col gap-3 border-t border-[#34322f] px-3 py-3 md:flex-row md:items-center md:justify-between">
        <div className="flex min-w-0 flex-wrap items-center gap-2">
          <button type="button" disabled title={t.attachmentUnavailable} aria-label={t.attachmentUnavailable} className={`${compact ? 'hidden' : 'flex'} h-10 w-10 cursor-not-allowed items-center justify-center rounded-md text-[#716d66]`}>
            <Paperclip size={17} />
          </button>
          <label className="sr-only" htmlFor="operator-model-preference">{t.modelPreferenceLabel}</label>
          <select
            id="operator-model-preference"
            value={modelPreference}
            onChange={(event) => setModelPreference(event.target.value as OperatorModelPreference)}
            className="h-10 max-w-[14rem] rounded-md border border-[#3b3935] bg-[#1d1d1c] px-3 text-xs text-[#c9c5bc] outline-none focus:border-[#7a683d]"
          >
            <option value="auto">{t.modelPreferenceAuto}</option>
            <option value="fast_summary">{t.modelPreferenceFast}</option>
            <option value="balanced_draft">{t.modelPreferenceBalanced}</option>
            <option value="code_review">{t.modelPreferenceCode}</option>
            <option value="reasoning_plan">{t.modelPreferenceReasoning}</option>
            <option value="vision_review">{t.modelPreferenceVision}</option>
            <option value="external_provider" disabled>{t.modelPreferenceExternal}</option>
          </select>
          <label className="sr-only" htmlFor="operator-planning-detail">{t.planningDetailLabel}</label>
          <select
            id="operator-planning-detail"
            value={planningDetail}
            onChange={(event) => setPlanningDetail(event.target.value as OperatorPlanningDetail)}
            className="h-10 rounded-md border border-[#3b3935] bg-[#1d1d1c] px-3 text-xs text-[#c9c5bc] outline-none focus:border-[#7a683d]"
          >
            <option value="concise">{t.planningConcise}</option>
            <option value="balanced">{t.planningBalanced}</option>
            <option value="deep">{t.planningDeep}</option>
          </select>
          <span className={`${compact ? 'hidden sm:inline-flex' : 'inline-flex'} h-10 items-center gap-1.5 px-2 text-[11px] text-[#77736d]`}>
            <ShieldCheck size={13} className="text-[#f4bf4f]" />
            {t.safePreviewNoAction}
          </span>
        </div>
        <button
          type="button"
          onClick={() => { void submitRoutePreview(); }}
          disabled={!composerText.trim()}
          className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-[#f4bf4f] px-4 text-sm font-semibold text-[#18150f] hover:bg-[#ffd475] disabled:cursor-not-allowed disabled:opacity-35"
        >
          <SendHorizontal size={15} />
          {t.previewRoute}
        </button>
      </div>
      <p className="sr-only" role="status" aria-live="polite" aria-atomic="true">{routeAnnouncement}</p>
    </section>
  );
};
