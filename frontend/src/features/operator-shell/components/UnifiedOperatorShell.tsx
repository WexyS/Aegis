"use client";

import React from 'react';
import { Bot, X } from 'lucide-react';

import { dictionaryFor } from '@/i18n';
import { useOperatorStore } from '@/store/useOperatorStore';
import { useUIStore } from '@/store/useUIStore';

import { OperatorComposer } from './OperatorComposer';
import { OperatorContextPanel } from './OperatorContextPanel';
import { OperatorLocalProposalPanel } from './OperatorLocalProposalPanel';
import { OperatorMemoryCandidateAction } from './OperatorMemoryCandidateAction';
import { OperatorQuickActions } from './OperatorQuickActions';
import { OperatorResponseDraft } from './OperatorResponseDraft';
import { OperatorRoutePreview } from './OperatorRoutePreview';

export const UnifiedOperatorShell = () => {
  const language = useUIStore((state) => state.language);
  const t = dictionaryFor(language).operatorShell;
  const lastDecision = useOperatorStore((state) => state.lastDecision);
  const isInspectorOpen = useUIStore((state) => state.isInspectorOpen);
  const setInspectorOpen = useUIStore((state) => state.setInspectorOpen);
  const drawerRef = React.useRef<HTMLElement>(null);
  const closeButtonRef = React.useRef<HTMLButtonElement>(null);
  const wasInspectorOpen = React.useRef(false);

  React.useEffect(() => {
    if (!isInspectorOpen) {
      if (wasInspectorOpen.current) {
        window.requestAnimationFrame(() => document.getElementById('operator-context-trigger')?.focus());
      }
      wasInspectorOpen.current = false;
      return;
    }

    wasInspectorOpen.current = true;
    window.requestAnimationFrame(() => closeButtonRef.current?.focus());

    const handleDialogKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        setInspectorOpen(false);
        return;
      }
      if (event.key !== 'Tab' || !drawerRef.current) return;

      const focusable = Array.from(drawerRef.current.querySelectorAll<HTMLElement>(
        'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), summary, [tabindex]:not([tabindex="-1"])',
      )).filter((element) => {
        const closedDetails = element.closest('details:not([open])');
        return element.getClientRects().length > 0
          && !element.closest('[aria-hidden="true"]')
          && (!closedDetails || element.tagName === 'SUMMARY');
      });
      if (!focusable.length) {
        event.preventDefault();
        drawerRef.current.focus();
        return;
      }
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener('keydown', handleDialogKeyDown);
    return () => document.removeEventListener('keydown', handleDialogKeyDown);
  }, [isInspectorOpen, setInspectorOpen]);

  return (
    <div className="operator-shell relative flex h-full min-h-0 bg-[#131313]">
      <main className="min-w-0 flex-1 overflow-y-auto custom-scrollbar">
        {!lastDecision ? (
          <div className="mx-auto flex min-h-full w-full max-w-4xl flex-col justify-center px-5 py-10 sm:px-8">
            <div className="mb-8 text-center">
              <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-lg border border-[#4a4333] bg-[#28241c] text-[#f4bf4f]">
                <Bot size={21} />
              </div>
              <h2 className="mt-5 text-3xl font-semibold text-[#f4f1ea]">{t.heroTitle}</h2>
              <p className="mx-auto mt-3 max-w-xl text-sm leading-6 text-[#8f8b84]">{t.heroSubtitle}</p>
            </div>
            <OperatorComposer />
            <div className="mt-4"><OperatorQuickActions /></div>
          </div>
        ) : (
          <div className="mx-auto flex min-h-full w-full max-w-4xl flex-col px-4 pt-6 sm:px-7 sm:pt-8">
            <div className="flex-1 pb-36">
              <div className="mb-6 flex justify-end">
                <div className="max-w-[88%] rounded-xl rounded-br-sm bg-[#292825] px-4 py-3 text-sm leading-6 text-[#e3dfd7]">
                  {lastDecision.request}
                </div>
              </div>
              <OperatorResponseDraft />
              <OperatorLocalProposalPanel />
              <OperatorMemoryCandidateAction />
              <div className="mt-4"><OperatorRoutePreview decision={lastDecision} /></div>
            </div>
            <div className="sticky bottom-0 z-20 -mx-4 bg-[linear-gradient(180deg,transparent,#131313_18%)] px-4 pb-4 pt-8 sm:-mx-7 sm:px-7 sm:pb-6">
              <OperatorComposer compact />
            </div>
          </div>
        )}
      </main>

      {isInspectorOpen && (
        <div className="absolute inset-0 z-50 flex justify-end">
          <button type="button" tabIndex={-1} className="absolute inset-0 bg-black/55" aria-label={t.closeContext} onClick={() => setInspectorOpen(false)} />
          <aside
            id="operator-context-drawer"
            ref={drawerRef}
            role="dialog"
            aria-modal="true"
            aria-labelledby="operator-context-title"
            tabIndex={-1}
            className="relative z-10 h-full w-[min(92vw,24rem)] overflow-y-auto border-l border-[#34322f] bg-[#181817] p-4 shadow-2xl custom-scrollbar"
          >
            <div className="mb-4 flex items-center justify-between">
              <h2 id="operator-context-title" className="text-sm font-semibold text-[#ece9e2]">{t.contextPanelTitle}</h2>
              <button ref={closeButtonRef} type="button" onClick={() => setInspectorOpen(false)} className="flex h-10 w-10 items-center justify-center rounded-md text-[#8f8b84] hover:bg-[#292825] hover:text-[#f4f1ea]" aria-label={t.closeContext}>
                <X size={17} />
              </button>
            </div>
            <OperatorContextPanel />
          </aside>
        </div>
      )}
    </div>
  );
};
