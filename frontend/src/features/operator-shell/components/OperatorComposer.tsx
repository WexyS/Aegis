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
    <section className="rounded-lg border border-white/10 bg-white/[0.055] p-2 shadow-2xl shadow-black/25">
      <div className="rounded-md border border-white/10 bg-[#10131d]/90 p-4">
        <div className="mb-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2 text-sm font-semibold text-white">
            <ShieldCheck size={16} className="text-accent" />
            {t.composerTitle}
          </div>
          <div className="flex flex-wrap gap-2 sm:justify-end">
            <ModeChip label={t.modeAuto} />
            <ModeChip label={t.permissionSafePreview} />
            <ModeChip label={t.modelAuto} />
            <ModeChip label={t.sourceLocalFirst} />
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
          rows={6}
          className="min-h-[12rem] w-full resize-none rounded-md border border-white/10 bg-black/25 px-4 py-3 text-base leading-8 text-foreground/90 outline-none transition-colors placeholder:text-foreground/32 focus:border-accent/45"
          placeholder={t.composerPlaceholder}
        />

        <div className="mt-3 flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
          <div className="flex flex-wrap gap-2">
            <PlaceholderButton label={t.attachmentPlaceholder} icon={<Paperclip size={14} />} />
            <PlaceholderButton label={t.microphonePlaceholder} icon={<Mic size={14} />} />
            <ModeChip label={t.cloudApprovalRequired} tone="warning" />
            <ModeChip label={t.memoryAutoPolicyPreview} />
            <ModeChip label={t.researchWhenNeeded} />
            <ModeChip label={t.visionBoundaryRequired} tone="warning" />
          </div>
          <button
            type="button"
            onClick={() => { void submitPreviewRequest(); }}
            disabled={!composerText.trim()}
            className="inline-flex min-h-[44px] items-center justify-center gap-2 rounded-md bg-accent px-5 text-sm font-semibold text-background transition-colors hover:bg-accent-light disabled:cursor-not-allowed disabled:opacity-45"
          >
            <SendHorizontal size={16} />
            {t.previewRoute}
          </button>
        </div>
      </div>
    </section>
  );
};

const ModeChip = ({ label, tone = 'info' }: { label: string; tone?: 'info' | 'warning' }) => (
  <span className={`inline-flex max-w-full items-center rounded-md border px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide ${
    tone === 'warning'
      ? 'border-warning/25 bg-warning/10 text-warning'
      : 'border-accent/25 bg-accent/10 text-accent'
  }`}>
    <span className="truncate">{label}</span>
  </span>
);

const PlaceholderButton = ({ label, icon }: { label: string; icon: React.ReactNode }) => (
  <button
    type="button"
    title={label}
    className="inline-flex min-h-[30px] items-center gap-2 rounded-md border border-white/10 bg-white/[0.035] px-2.5 text-[10px] font-bold uppercase tracking-wide text-foreground/45"
  >
    {icon}
    {label}
  </button>
);
