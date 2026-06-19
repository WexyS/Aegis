"use client";

import React from 'react';
import { ShieldCheck } from 'lucide-react';

import { dictionaryFor } from '@/i18n';
import { useOperatorStore } from '@/store/useOperatorStore';
import { useUIStore } from '@/store/useUIStore';

import { OperatorComposer } from './OperatorComposer';
import { OperatorContextPanel } from './OperatorContextPanel';
import { OperatorQuickActions } from './OperatorQuickActions';
import { OperatorResponseDraft } from './OperatorResponseDraft';
import { OperatorRoutePreview } from './OperatorRoutePreview';

export const UnifiedOperatorShell = () => {
  const language = useUIStore((state) => state.language);
  const t = dictionaryFor(language).operatorShell;
  const lastDecision = useOperatorStore((state) => state.lastDecision);

  return (
    <div className="operator-shell relative h-full min-h-0 overflow-y-auto bg-[#151516] pb-8 custom-scrollbar">
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(180deg,rgba(255,255,255,0.026),transparent_18%),linear-gradient(135deg,rgba(30,31,34,0.98),rgba(18,19,21,0.99))]" />
      <div className="pointer-events-none absolute inset-0 opacity-[0.04] bg-[repeating-linear-gradient(135deg,rgba(255,255,255,0.75)_0px,rgba(255,255,255,0.75)_1px,transparent_1px,transparent_9px)]" />

      <div className="relative z-10 mx-auto grid w-full max-w-[95rem] gap-5 p-4 xl:grid-cols-[minmax(0,1fr)_24rem] xl:p-6">
        <main className="min-w-0">
          <section className="mx-auto flex min-h-[calc(100dvh-8rem)] w-full max-w-5xl flex-col justify-center py-6">
            <div className="mb-5 inline-flex w-fit items-center gap-2 rounded-xl border border-white/10 bg-white/[0.045] px-3 py-1.5 text-xs font-semibold text-foreground/62">
              <ShieldCheck size={14} />
              {t.eyebrow}
            </div>
            <h1 className="max-w-4xl text-3xl font-semibold leading-tight text-white sm:text-4xl lg:text-5xl">
              {t.heroTitle}
            </h1>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-foreground/58 sm:text-base">
              {t.heroSubtitle}
            </p>

            <div className="mt-8 space-y-4">
              <OperatorComposer />
              <OperatorQuickActions />
            </div>
          </section>

          <div className="mx-auto w-full max-w-5xl space-y-4 pb-6">
            <OperatorResponseDraft />
            <OperatorRoutePreview decision={lastDecision} />
          </div>
        </main>

        <div className="min-w-0 xl:sticky xl:top-5 xl:self-start">
          <OperatorContextPanel />
        </div>
      </div>
    </div>
  );
};
