"use client";

import React from 'react';
import { AlertTriangle, CheckCircle2, Info, ShieldCheck, X } from 'lucide-react';

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

        <div className="min-h-0 flex-1 space-y-5 overflow-y-auto px-6 py-6 custom-scrollbar">
          <section className="relative overflow-hidden rounded-xl border border-secondary/20 bg-secondary/[0.08] p-4">
            <div className="absolute inset-y-0 left-0 w-1 bg-secondary shadow-[0_0_12px_rgba(139,92,246,0.85)]" />
            <div className="flex items-start gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-secondary/25 bg-secondary/15 text-secondary-light">
                <ShieldCheck size={18} />
              </div>
              <div>
                <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-foreground/38">{t.approval.action}</div>
                <p className="mt-1 text-base font-semibold text-white">{t.approval.sampleAction}</p>
              </div>
            </div>
          </section>

          <div className="grid gap-4 sm:grid-cols-2">
            <DetailBlock title={t.approval.whyNeeded} copy={t.approval.sampleWhy} />
            <DetailBlock title={t.approval.scope} copy={t.approval.sampleScope} />
            <DetailBlock title={t.approval.risk} copy={t.approval.sampleRisk} accent />
          </div>

          <section className="grid gap-4 lg:grid-cols-2">
            <ImpactList
              title={t.approval.willHappen}
              tone="positive"
              items={[t.approval.happenOne, t.approval.happenTwo]}
            />
            <ImpactList
              title={t.approval.willNotHappen}
              tone="neutral"
              items={[t.approval.notOne, t.approval.notTwo, t.approval.notThree, t.approval.notFour]}
            />
          </section>

          <section className="rounded-xl border border-white/10 bg-white/[0.035] p-4">
            <div className="flex items-start gap-3">
              <Info size={17} className="mt-0.5 shrink-0 text-foreground/45" />
              <div>
                <h3 className="text-[10px] font-bold uppercase tracking-[0.18em] text-foreground/45">{t.approval.evidenceExpectation}</h3>
                <p className="mt-2 text-sm leading-6 text-foreground/58">{t.approval.auditCopy}</p>
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
            {t.approval.reviewDetails}
          </button>
          <div className="flex gap-3">
            <button
              type="button"
              disabled={!hasLivePending}
              className="rounded-lg border border-danger/25 bg-danger/10 px-5 py-2.5 text-sm font-semibold text-danger transition-colors disabled:cursor-not-allowed disabled:opacity-45"
            >
              {t.approval.reject}
            </button>
            <button
              type="button"
              disabled={!hasLivePending}
              className="rounded-lg border border-secondary/35 bg-secondary px-6 py-2.5 text-sm font-semibold text-white shadow-[0_0_28px_rgba(139,92,246,0.28)] transition-colors disabled:cursor-not-allowed disabled:opacity-45"
            >
              {t.approval.approve}
            </button>
          </div>
        </div>
      </aside>
    </div>
  );
};

const DetailBlock = ({ title, copy, accent = false }: { title: string; copy: string; accent?: boolean }) => (
  <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
    <h3 className="text-[10px] font-bold uppercase tracking-[0.18em] text-foreground/38">{title}</h3>
    <p className={`mt-2 text-sm leading-6 ${accent ? 'text-accent' : 'text-foreground/62'}`}>{copy}</p>
  </div>
);

const ImpactList = ({
  title,
  items,
  tone,
}: {
  title: string;
  items: string[];
  tone: 'positive' | 'neutral';
}) => (
  <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
    <h3 className="text-[10px] font-bold uppercase tracking-[0.18em] text-foreground/38">{title}</h3>
    <ul className="mt-3 space-y-2">
      {items.map((item) => (
        <li key={item} className="flex items-start gap-2 text-sm leading-6 text-foreground/62">
          {tone === 'positive'
            ? <CheckCircle2 size={15} className="mt-1 shrink-0 text-secondary-light" />
            : <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-foreground/35" />}
          <span>{item}</span>
        </li>
      ))}
    </ul>
  </div>
);
