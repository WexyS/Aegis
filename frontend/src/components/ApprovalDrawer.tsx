"use client";

import React from 'react';
import { AlertTriangle, Info, X } from 'lucide-react';

import { dictionaryFor } from '@/i18n';
import { useUIStore } from '@/store/useUIStore';

type ApprovalDrawerProps = {
  open: boolean;
  pendingCount: number;
  onClose: () => void;
  onReviewDetails: () => void;
};

export const ApprovalDrawer = ({
  open,
  pendingCount,
  onClose,
  onReviewDetails,
}: ApprovalDrawerProps) => {
  const language = useUIStore((state) => state.language);
  const t = dictionaryFor(language);

  if (!open) return null;

  const hasLivePending = pendingCount > 0;

  return (
    <div className="fixed inset-0 z-[80] flex justify-end bg-black/45 backdrop-blur-sm" role="dialog" aria-modal="true" aria-label={t.approval.drawerTitle}>
      <button type="button" className="absolute inset-0 cursor-default" aria-label={t.approval.close} onClick={onClose} />
      <aside className="relative flex h-full w-full max-w-[36rem] flex-col border-l border-white/10 bg-[#111018]/95 shadow-2xl shadow-black/45">
        <div className="h-1 bg-white/[0.035]">
          <div className={`h-full ${hasLivePending ? 'w-1/2 bg-warning shadow-[0_0_16px_rgba(245,158,11,0.8)]' : 'w-1/5 bg-secondary shadow-[0_0_16px_rgba(139,92,246,0.75)]'}`} />
        </div>

        <div className="flex items-center justify-between gap-3 border-b border-white/10 bg-black/20 px-5 py-4">
          <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.18em] text-warning">
            <AlertTriangle size={15} />
            {t.approval.indicator}: {pendingCount} {t.header.pending}
          </div>
          <button type="button" onClick={onClose} className="rounded-md p-2 text-foreground/45 transition-colors hover:bg-white/[0.06] hover:text-white" aria-label={t.approval.close}>
            <X size={18} />
          </button>
        </div>

        <div className="border-b border-white/10 px-6 py-6">
          <h2 className="text-2xl font-semibold tracking-tight text-white">{hasLivePending ? t.approval.drawerTitle : t.approval.emptyTitle}</h2>
          <p className="mt-2 max-w-md text-sm leading-7 text-foreground/58">
            {hasLivePending ? t.approval.drawerSubtitle : t.approval.emptyCopy}
          </p>
        </div>

        <div className="min-h-0 flex-1 space-y-5 overflow-y-auto px-6 py-6 pb-10 custom-scrollbar">
          <section className={`rounded-xl border p-4 ${hasLivePending ? 'border-warning/20 bg-warning/[0.07]' : 'border-secondary/20 bg-secondary/[0.07]'}`}>
            <div className="flex items-start gap-3">
              <Info size={18} className={`mt-0.5 shrink-0 ${hasLivePending ? 'text-warning' : 'text-secondary-light'}`} />
              <div>
                <h3 className="text-sm font-semibold text-white">
                  {hasLivePending ? t.approval.pendingDetailsUnavailableTitle : t.approval.emptyTitle}
                </h3>
                <p className="mt-2 text-sm leading-6 text-foreground/62">
                  {hasLivePending ? t.approval.pendingDetailsUnavailableCopy : t.approval.emptyCopy}
                </p>
              </div>
            </div>
          </section>
        </div>

        <div className="flex flex-col gap-3 border-t border-white/10 bg-black/25 p-5 sm:flex-row sm:items-center sm:justify-between">
          <button
            type="button"
            onClick={onReviewDetails}
            className="rounded-lg border border-white/10 bg-white/[0.04] px-4 py-2.5 text-sm font-semibold text-foreground/[0.65] transition-colors hover:border-white/20 hover:text-white"
          >
            {t.approval.openWorkApprovals}
          </button>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-white/10 bg-white/[0.035] px-5 py-2.5 text-sm font-semibold text-foreground/65 transition-colors hover:border-white/20 hover:text-white"
          >
            {t.approval.close}
          </button>
        </div>
      </aside>
    </div>
  );
};
