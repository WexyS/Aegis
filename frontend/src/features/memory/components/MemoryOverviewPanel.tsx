"use client";

import React from 'react';
import { Archive, CheckCircle2, Database, Eye, Inbox, Search, ShieldAlert, Trash2, XCircle } from 'lucide-react';

import { StatusBadge } from '@/components/StatusBadge';
import { dictionaryFor } from '@/i18n';
import { useUIStore } from '@/store/useUIStore';

export const MemoryOverviewPanel = () => {
  const setActiveTab = useUIStore((state) => state.setActiveTab);
  const language = useUIStore((state) => state.language);
  const t = dictionaryFor(language);
  const m = t.memory;
  const principles = [
    { title: m.principles.noSilentWrites.title, detail: m.principles.noSilentWrites.detail, icon: <ShieldAlert size={16} /> },
    { title: m.principles.candidateReview.title, detail: m.principles.candidateReview.detail, icon: <Inbox size={16} /> },
    { title: m.principles.searchContext.title, detail: m.principles.searchContext.detail, icon: <Search size={16} /> },
    { title: m.principles.deleteForget.title, detail: m.principles.deleteForget.detail, icon: <Trash2 size={16} /> },
  ];
  const lifecycle = [
    { state: 'proposed', stateLabel: m.states.proposed, detail: m.states.candidateOnly, tone: 'warning' },
    { state: 'active', stateLabel: m.states.active, detail: m.states.approvedMemory, tone: 'success' },
    { state: 'rejected', stateLabel: m.states.rejected, detail: m.states.notUsed, tone: 'danger' },
    { state: 'deleted', stateLabel: m.states.deleted, detail: m.states.retiredLocally, tone: 'unknown' },
  ] as const;

  return (
    <div className="h-full min-h-0 overflow-y-auto custom-scrollbar">
      <div className="mx-auto flex w-full max-w-[90rem] flex-col gap-5 p-4 pb-10 sm:p-5 sm:pb-10 lg:p-7 lg:pb-12 2xl:p-8 2xl:pb-12">
        <section className="rounded-lg border border-white/10 bg-white/[0.04] p-5 shadow-2xl shadow-black/15 lg:p-6">
          <div className="flex flex-col justify-between gap-5 xl:flex-row xl:items-end">
            <div className="max-w-4xl">
              <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.18em] text-accent">
                <Database size={15} />
                {m.eyebrow}
              </div>
              <h1 className="mt-3 text-3xl font-semibold tracking-tight text-white lg:text-4xl">{m.title}</h1>
              <p className="mt-3 text-sm leading-7 text-foreground/60">
                {m.subtitle}
              </p>
            </div>
            <button
              type="button"
              onClick={() => setActiveTab('Work')}
              className="inline-flex items-center justify-center rounded-md border border-accent/30 bg-accent/10 px-4 py-2 text-[12px] font-bold uppercase tracking-wider text-accent transition-colors hover:border-accent/55 hover:bg-accent/15"
            >
              {m.openTools}
            </button>
          </div>
        </section>

        <section className="grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
          <div className="rounded-lg border border-white/10 bg-white/[0.032] p-4 shadow-xl shadow-black/10">
            <div className="mb-4 flex items-start justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold text-white">{m.lifecycleTitle}</h2>
                <p className="mt-1 text-sm leading-relaxed text-foreground/52">{m.lifecycleSubtitle}</p>
              </div>
              <StatusBadge label={m.local} tone="info" />
            </div>
            <div className="space-y-2">
              {lifecycle.map(({ state, stateLabel, detail, tone }) => (
                <div key={state} className="flex items-center justify-between gap-3 rounded-md border border-white/10 bg-black/20 px-3 py-2.5">
                  <div className="flex min-w-0 items-center gap-3">
                    <LifecycleIcon state={state} />
                    <div className="min-w-0">
                      <div className="text-sm font-medium text-white">{stateLabel}</div>
                      <div className="text-[11px] text-foreground/42">{detail}</div>
                    </div>
                  </div>
                  <StatusBadge label={stateLabel} tone={tone} />
                </div>
              ))}
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            {principles.map((principle) => (
              <section key={principle.title} className="rounded-lg border border-white/10 bg-white/[0.032] p-4 shadow-xl shadow-black/10">
                <div className="flex items-start gap-3">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-accent/20 bg-accent/10 text-accent">
                    {principle.icon}
                  </div>
                  <div className="min-w-0">
                    <h2 className="text-sm font-semibold text-white">{principle.title}</h2>
                    <p className="mt-2 text-sm leading-6 text-foreground/56">{principle.detail}</p>
                  </div>
                </div>
              </section>
            ))}
          </div>
        </section>

        <section className="rounded-lg border border-warning/20 bg-warning/[0.035] p-4">
          <div className="flex items-start gap-3">
            <Eye size={17} className="mt-0.5 text-warning" />
          <div>
              <h2 className="text-sm font-semibold text-white">{m.boundaryTitle}</h2>
              <p className="mt-2 text-sm leading-6 text-foreground/58">
                {m.boundaryCopy}
              </p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

const LifecycleIcon = ({ state }: { state: string }) => {
  if (state === 'active') return <CheckCircle2 size={16} className="text-success" />;
  if (state === 'rejected') return <XCircle size={16} className="text-danger" />;
  if (state === 'deleted') return <Archive size={16} className="text-foreground/40" />;
  return <Inbox size={16} className="text-warning" />;
};
