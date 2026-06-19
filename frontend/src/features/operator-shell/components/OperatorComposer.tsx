"use client";

import React from 'react';
import { Mic, Paperclip, SendHorizontal, ShieldCheck } from 'lucide-react';

import { dictionaryFor } from '@/i18n';
import { useOperatorStore } from '@/store/useOperatorStore';
import { useUIStore } from '@/store/useUIStore';

export const OperatorComposer = () => {
  const language = useUIStore((state) => state.language);
  const t = dictionaryFor(language).operatorShell;
  const composerText = useOperatorStore((state) => state.composerText);
  const setComposerText = useOperatorStore((state) => state.setComposerText);
  const submitPreviewRequest = useOperatorStore((state) => state.submitPreviewRequest);

  return (
    <section className="rounded-3xl border border-white/10 bg-[#2a2b2f]/90 p-4 shadow-2xl shadow-black/25">
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-center gap-2 text-sm font-semibold text-white">
          <ShieldCheck size={16} className="shrink-0 text-accent" />
          <span className="truncate">{t.composerTitle}</span>
        </div>
        <div className="hidden shrink-0 flex-wrap gap-2 md:flex">
          <ModeChip label={t.modeAuto} />
          <ModeChip label={t.permissionSafePreview} />
          <ModeChip label={t.modelAuto} />
        </div>
      </div>

      <textarea
        value={composerText}
        onChange={(event) => setComposerText(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            void submitPreviewRequest();
          }
        }}
        rows={4}
        className="mt-4 min-h-[9.5rem] w-full resize-none rounded-2xl border border-white/10 bg-[#202126]/95 px-4 py-3 text-base leading-8 text-foreground/90 outline-none transition-colors placeholder:text-foreground/36 focus:border-accent/45"
        placeholder={t.composerPlaceholder}
      />

      <div className="mt-3 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-wrap gap-2">
          <PlaceholderButton label={t.attachmentPlaceholder} icon={<Paperclip size={14} />} />
          <PlaceholderButton label={t.microphonePlaceholder} icon={<Mic size={14} />} />
          <ModeChip label={t.sourceLocalFirst} />
          <ModeChip label={t.cloudApprovalRequired} tone="warning" />
          <ModeChip label={t.noMemoryWrite} />
          <ModeChip label={t.noCommandExecution} />
        </div>
        <button
          type="button"
          onClick={() => { void submitPreviewRequest(); }}
          disabled={!composerText.trim()}
          className="inline-flex min-h-[42px] items-center justify-center gap-2 rounded-xl bg-accent px-5 text-sm font-semibold text-background transition-colors hover:bg-accent-light disabled:cursor-not-allowed disabled:opacity-45"
        >
          <SendHorizontal size={16} />
          {t.previewRoute}
        </button>
      </div>
    </section>
  );
};

const ModeChip = ({ label, tone = 'info' }: { label: string; tone?: 'info' | 'warning' }) => (
  <span className={`inline-flex max-w-full items-center rounded-lg border px-2.5 py-1 text-[11px] font-semibold ${
    tone === 'warning'
      ? 'border-warning/25 bg-warning/10 text-warning'
      : 'border-white/10 bg-white/[0.055] text-foreground/62'
  }`}>
    <span className="truncate">{label}</span>
  </span>
);

const PlaceholderButton = ({ label, icon }: { label: string; icon: React.ReactNode }) => (
  <button
    type="button"
    title={label}
    className="inline-flex min-h-[30px] items-center gap-2 rounded-lg border border-white/10 bg-white/[0.045] px-2.5 text-[11px] font-semibold text-foreground/50"
  >
    {icon}
    {label}
  </button>
);
