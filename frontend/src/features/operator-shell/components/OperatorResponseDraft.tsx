"use client";

import React from 'react';
import { Check, Copy, FileText, ShieldCheck } from 'lucide-react';

import { StatusBadge } from '@/components/StatusBadge';
import { dictionaryFor } from '@/i18n';
import { useOperatorStore } from '@/store/useOperatorStore';
import { useUIStore } from '@/store/useUIStore';

import { formatRoute } from './OperatorRoutePreview';

export const OperatorResponseDraft = () => {
  const language = useUIStore((state) => state.language);
  const t = dictionaryFor(language).operatorShell;
  const decision = useOperatorStore((state) => state.lastDecision);
  const artifacts = useOperatorStore((state) => state.artifacts);
  const selectedArtifactId = useOperatorStore((state) => state.selectedArtifactId);
  const selectedArtifact = artifacts.find((artifact) => artifact.id === selectedArtifactId) ?? artifacts[0] ?? null;
  const [copied, setCopied] = React.useState(false);

  const copyText = React.useMemo(() => {
    if (!selectedArtifact) return '';
    return [
      selectedArtifact.title ?? t.responseDraftTitle,
      '',
      selectedArtifact.summary ?? '',
      '',
      selectedArtifact.body ?? '',
      '',
      t.responseDraftSafetyFooter,
    ].filter(Boolean).join('\n');
  }, [selectedArtifact, t.responseDraftSafetyFooter, t.responseDraftTitle]);

  const copyDraft = React.useCallback(async () => {
    if (!copyText || typeof navigator === 'undefined' || !navigator.clipboard) return;
    try {
      await navigator.clipboard.writeText(copyText);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1400);
    } catch {
      setCopied(false);
    }
  }, [copyText]);

  return (
    <section className="rounded-2xl border border-white/10 bg-[#1f2024]/85 shadow-2xl shadow-black/20">
      <div className="flex flex-col gap-3 border-b border-white/10 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-2 text-sm font-semibold text-white">
            <FileText size={17} className="text-accent" />
            {t.responseDraftTitle}
          </div>
          <p className="mt-1 text-xs leading-5 text-foreground/50">{t.responseDraftCopy}</p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <StatusBadge label={t.previewOnly} tone="info" />
          <StatusBadge label={t.noCommandExecution} tone="unknown" />
          <StatusBadge label={t.noVerifierSuccess} tone="unknown" />
        </div>
      </div>

      {!selectedArtifact || !decision ? (
        <div className="px-5 py-10">
          <div className="mx-auto flex max-w-lg flex-col items-center text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-accent/25 bg-accent/10 text-accent">
              <ShieldCheck size={22} />
            </div>
            <h2 className="mt-4 text-xl font-semibold text-white">{t.responseDraftEmptyTitle}</h2>
            <p className="mt-2 text-sm leading-7 text-foreground/54">{t.responseDraftEmptyCopy}</p>
          </div>
        </div>
      ) : (
        <div className="grid gap-0 lg:grid-cols-[minmax(0,1fr)_16rem]">
          <div className="min-w-0 px-5 py-5">
            <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
              <div className="min-w-0">
                <p className="text-[11px] font-semibold text-foreground/45">{t.selectedArtifact}</p>
                <h2 className="mt-1 break-words text-xl font-semibold text-white">{selectedArtifact.title}</h2>
              </div>
              <button
                type="button"
                onClick={copyDraft}
                disabled={!copyText}
                className="inline-flex min-h-[34px] items-center justify-center gap-2 rounded-lg border border-white/10 bg-white/[0.06] px-3 text-xs font-semibold text-foreground/72 transition-colors hover:border-accent/30 hover:text-accent disabled:cursor-not-allowed disabled:opacity-40"
              >
                {copied ? <Check size={14} /> : <Copy size={14} />}
                {copied ? t.copiedDraft : t.copyDraft}
              </button>
            </div>

            <div className="rounded-xl border border-white/10 bg-black/20 p-4">
              <p className="text-[11px] font-semibold uppercase text-foreground/38">{t.draftSummary}</p>
              <p className="mt-2 text-sm leading-7 text-foreground/72">{selectedArtifact.summary}</p>
            </div>

            <div className="mt-4 rounded-xl border border-white/10 bg-black/25 p-4">
              <p className="text-[11px] font-semibold uppercase text-foreground/38">{t.draftBody}</p>
              <pre className="mt-3 whitespace-pre-wrap break-words font-sans text-sm leading-7 text-foreground/78">
                {selectedArtifact.body ?? t.noArtifactBody}
              </pre>
            </div>
          </div>

          <aside className="border-t border-white/10 bg-black/15 p-5 lg:border-l lg:border-t-0">
            <p className="text-[11px] font-semibold uppercase text-foreground/38">{t.routeSnapshot}</p>
            <dl className="mt-3 space-y-3 text-xs">
              <div>
                <dt className="text-foreground/42">{t.proposedRoute}</dt>
                <dd className="mt-1 break-words font-semibold text-foreground/78">{formatRoute(decision.routeId, t)}</dd>
              </div>
              <div>
                <dt className="text-foreground/42">{t.detectedIntent}</dt>
                <dd className="mt-1 break-words font-semibold text-foreground/78">{decision.primaryIntent}</dd>
              </div>
              <div>
                <dt className="text-foreground/42">{t.previewSource}</dt>
                <dd className="mt-1 font-semibold text-foreground/78">
                  {decision.previewSource === 'backend_contract' ? t.previewSourceBackend : t.previewSourceFallback}
                </dd>
              </div>
            </dl>
            <div className="mt-5 rounded-xl border border-warning/20 bg-warning/[0.06] p-3">
              <p className="text-[11px] font-semibold text-warning">{t.safetySnapshot}</p>
              <p className="mt-2 text-[11px] leading-5 text-foreground/58">{t.routePreviewSafetyCopy}</p>
            </div>
          </aside>
        </div>
      )}
    </section>
  );
};
