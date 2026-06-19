"use client";

import React from 'react';
import { Bot, BrainCircuit, Database, FileSearch, Settings2, ShieldCheck, TerminalSquare } from 'lucide-react';

import { dictionaryFor } from '@/i18n';
import { useOperatorStore } from '@/store/useOperatorStore';
import { useUIStore } from '@/store/useUIStore';

import { OperatorArtifactsPanel } from './OperatorArtifactsPanel';
import { OperatorComposer } from './OperatorComposer';
import { OperatorProcessPanel } from './OperatorProcessPanel';
import { OperatorQuickActions } from './OperatorQuickActions';
import { OperatorRoutePreview } from './OperatorRoutePreview';

export const UnifiedOperatorShell = () => {
  const language = useUIStore((state) => state.language);
  const setActiveTab = useUIStore((state) => state.setActiveTab);
  const t = dictionaryFor(language).operatorShell;
  const lastDecision = useOperatorStore((state) => state.lastDecision);

  const shortcuts = [
    { label: t.openAskDetails, icon: <Bot size={15} />, onClick: () => setActiveTab('Ask') },
    { label: t.openWorkTools, icon: <TerminalSquare size={15} />, onClick: () => setActiveTab('Work') },
    { label: t.openModelHub, icon: <BrainCircuit size={15} />, onClick: () => setActiveTab('Settings') },
    { label: t.openMemoryTools, icon: <Database size={15} />, onClick: () => setActiveTab('Memory') },
    { label: t.openAdvancedDiagnostics, icon: <Settings2 size={15} />, onClick: () => setActiveTab('Advanced') },
    { label: t.reviewApprovalPattern, icon: <ShieldCheck size={15} />, onClick: () => setActiveTab('Work') },
  ];

  return (
    <div className="operator-shell relative h-full min-h-0 overflow-y-auto bg-[#030611] pb-10 custom-scrollbar">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_8%,rgba(139,92,246,0.15),transparent_30%),radial-gradient(circle_at_82%_18%,rgba(6,182,212,0.13),transparent_34%),linear-gradient(135deg,rgba(6,8,17,0.96),rgba(3,6,14,0.98))]" />
      <div className="pointer-events-none absolute inset-0 opacity-[0.055] bg-[repeating-linear-gradient(135deg,rgba(255,255,255,0.7)_0px,rgba(255,255,255,0.7)_1px,transparent_1px,transparent_8px)]" />

      <div className="relative z-10 mx-auto grid w-full max-w-[92rem] gap-5 p-4 lg:grid-cols-[minmax(0,1fr)_25rem] lg:p-6">
        <main className="min-w-0 space-y-5">
          <section className="min-w-0 pt-4 lg:pt-8">
            <div className="mb-3 inline-flex items-center gap-2 rounded-md border border-accent/25 bg-accent/10 px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.22em] text-accent">
              <ShieldCheck size={14} />
              {t.eyebrow}
            </div>
            <h1 className="max-w-4xl text-3xl font-semibold leading-tight tracking-tight text-white sm:text-4xl lg:text-5xl">
              {t.heroTitle}
            </h1>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-foreground/62 sm:text-base">
              {t.heroSubtitle}
            </p>
          </section>

          <OperatorComposer />
          <OperatorQuickActions />
          <OperatorRoutePreview decision={lastDecision} />

          <section className="grid gap-3 sm:grid-cols-3">
            <BoundaryCard title={t.localFirstTitle} copy={t.localFirstCopy} />
            <BoundaryCard title={t.previewOnlyTitle} copy={t.previewOnlyCopy} />
            <BoundaryCard title={t.backendAuthorityTitle} copy={t.backendAuthorityCopy} />
          </section>

          <section className="rounded-lg border border-white/10 bg-black/20 p-4">
            <div className="flex items-start gap-3">
              <FileSearch size={17} className="mt-0.5 shrink-0 text-warning" />
              <p className="min-w-0 break-words text-xs leading-6 text-foreground/58">{t.traceBoundaryCopy}</p>
            </div>
          </section>
        </main>

        <aside className="min-w-0 space-y-4 lg:sticky lg:top-5 lg:self-start">
          <OperatorProcessPanel />
          <OperatorArtifactsPanel />
          <section className="rounded-lg border border-white/10 bg-white/[0.035] p-4">
            <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-foreground/42">{t.shortcutsTitle}</p>
            <div className="mt-3 grid gap-2">
              {shortcuts.map((shortcut) => (
                <button
                  key={shortcut.label}
                  type="button"
                  onClick={shortcut.onClick}
                  className="inline-flex min-h-[38px] items-center gap-2 rounded-md border border-white/10 bg-black/20 px-3 text-left text-xs font-semibold text-foreground/68 transition-colors hover:border-accent/30 hover:text-accent"
                >
                  {shortcut.icon}
                  <span className="min-w-0 break-words">{shortcut.label}</span>
                </button>
              ))}
            </div>
          </section>
        </aside>
      </div>
    </div>
  );
};

const BoundaryCard = ({ title, copy }: { title: string; copy: string }) => (
  <div className="rounded-lg border border-white/10 bg-white/[0.035] p-4">
    <h2 className="text-sm font-semibold text-white">{title}</h2>
    <p className="mt-2 text-xs leading-6 text-foreground/55">{copy}</p>
  </div>
);
