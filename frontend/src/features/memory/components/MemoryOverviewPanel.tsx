"use client";

import React from 'react';
import { Archive, CheckCircle2, Database, Eye, Inbox, Search, ShieldAlert, Trash2, XCircle } from 'lucide-react';

import { StatusBadge } from '@/components/StatusBadge';
import { useUIStore } from '@/store/useUIStore';

const PRINCIPLES = [
  {
    title: 'No silent long-term writes',
    detail: 'Persistent memory needs explicit lifecycle state and user intent.',
    icon: <ShieldAlert size={16} />,
  },
  {
    title: 'Candidate review first',
    detail: 'Memory Inbox is the intended product direction for batching useful candidates.',
    icon: <Inbox size={16} />,
  },
  {
    title: 'Search is context',
    detail: 'Memory retrieval can help explain, but it is never runtime truth or permission.',
    icon: <Search size={16} />,
  },
  {
    title: 'Delete and forget remain first-class',
    detail: 'User control must include approve, reject, forget, delete, and auditability.',
    icon: <Trash2 size={16} />,
  },
];

const LIFECYCLE = [
  ['proposed', 'candidate only', 'warning'],
  ['active', 'approved memory', 'success'],
  ['rejected', 'not used', 'danger'],
  ['deleted', 'retired locally', 'unknown'],
] as const;

export const MemoryOverviewPanel = () => {
  const setActiveTab = useUIStore((state) => state.setActiveTab);

  return (
    <div className="min-h-full overflow-y-auto custom-scrollbar">
      <div className="mx-auto flex w-full max-w-[90rem] flex-col gap-5 p-4 sm:p-5 lg:p-7 2xl:p-8">
        <section className="rounded-lg border border-white/10 bg-white/[0.04] p-5 shadow-2xl shadow-black/15 lg:p-6">
          <div className="flex flex-col justify-between gap-5 xl:flex-row xl:items-end">
            <div className="max-w-4xl">
              <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.18em] text-accent">
                <Database size={15} />
                Memory OS
              </div>
              <h1 className="mt-3 text-3xl font-semibold tracking-tight text-white lg:text-4xl">Memory that asks before it becomes durable.</h1>
              <p className="mt-3 text-sm leading-7 text-foreground/60">
                Aegis has a local memory lifecycle foundation. The product direction is a Memory Inbox that batches useful candidates without silently persisting private or sensitive content.
              </p>
            </div>
            <button
              type="button"
              onClick={() => setActiveTab('Work')}
              className="inline-flex items-center justify-center rounded-md border border-accent/30 bg-accent/10 px-4 py-2 text-[12px] font-bold uppercase tracking-wider text-accent transition-colors hover:border-accent/55 hover:bg-accent/15"
            >
              Open current Memory tools
            </button>
          </div>
        </section>

        <section className="grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
          <div className="rounded-lg border border-white/10 bg-white/[0.032] p-4 shadow-xl shadow-black/10">
            <div className="mb-4 flex items-start justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold text-white">Lifecycle states</h2>
                <p className="mt-1 text-sm leading-relaxed text-foreground/52">Current foundation supports explicit states. The UI must not turn candidates into authority.</p>
              </div>
              <StatusBadge label="local" tone="info" />
            </div>
            <div className="space-y-2">
              {LIFECYCLE.map(([state, detail, tone]) => (
                <div key={state} className="flex items-center justify-between gap-3 rounded-md border border-white/10 bg-black/20 px-3 py-2.5">
                  <div className="flex min-w-0 items-center gap-3">
                    <LifecycleIcon state={state} />
                    <div className="min-w-0">
                      <div className="text-sm font-medium text-white">{state}</div>
                      <div className="text-[11px] text-foreground/42">{detail}</div>
                    </div>
                  </div>
                  <StatusBadge label={state} tone={tone} />
                </div>
              ))}
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            {PRINCIPLES.map((principle) => (
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
              <h2 className="text-sm font-semibold text-white">Memory truth boundary</h2>
              <p className="mt-2 text-sm leading-6 text-foreground/58">
                This screen does not write memory, does not infer private facts, and does not claim automatic long-term Memory OS intelligence. Current manual propose/approve/reject/search workflows remain accessible from Work.
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
