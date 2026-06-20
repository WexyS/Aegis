"use client";

import React from 'react';
import { Check, Copy, FileText } from 'lucide-react';

import { dictionaryFor } from '@/i18n';
import { useOperatorStore } from '@/store/useOperatorStore';
import { useUIStore } from '@/store/useUIStore';

import { Empty, TruthNote, WorkspacePage } from './HistorySurface';

export const OutputsSurface = () => {
  const language = useUIStore((state) => state.language);
  const t = dictionaryFor(language).workspace;
  const artifacts = useOperatorStore((state) => state.artifacts);
  const selectedId = useOperatorStore((state) => state.selectedArtifactId);
  const selectArtifact = useOperatorStore((state) => state.selectArtifact);
  const selected = artifacts.find((item) => item.id === selectedId) ?? artifacts[0] ?? null;
  const [copied, setCopied] = React.useState(false);

  const copy = React.useCallback(async () => {
    if (!selected?.body || !navigator.clipboard) return;
    await navigator.clipboard.writeText(`${selected.title ?? ''}\n\n${selected.body}`.trim());
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1200);
  }, [selected]);

  return (
    <WorkspacePage title={t.outputsTitle} description={t.outputsDescription}>
      {!selected ? (
        <Empty icon={<FileText size={24} />} title={t.outputsEmptyTitle} copy={t.outputsEmptyCopy} />
      ) : (
        <div className="grid gap-5 lg:grid-cols-[15rem_minmax(0,1fr)]">
          <div className="space-y-1">
            {artifacts.map((artifact) => (
              <button key={artifact.id} type="button" onClick={() => selectArtifact(artifact.id)} className={`w-full rounded-md px-3 py-2.5 text-left text-sm ${artifact.id === selected.id ? 'bg-[#2a2927] text-[#f4f1ea]' : 'text-[#8f8b84] hover:bg-[#1d1d1c]'}`}>
                <span className="block truncate">{artifact.title}</span>
                <span className="mt-1 block text-[11px] text-[#716d66]">{t.previewOutput}</span>
              </button>
            ))}
          </div>
          <article className="min-w-0 rounded-lg border border-[#33312e] bg-[#191918]">
            <header className="flex items-center justify-between gap-3 border-b border-[#33312e] px-4 py-3">
              <h3 className="truncate text-sm font-semibold text-[#ece9e2]">{selected.title}</h3>
              <button type="button" onClick={() => void copy()} className="flex h-10 items-center gap-2 rounded-md px-3 text-xs text-[#aaa69e] hover:bg-[#292825] hover:text-[#f4f1ea]">
                {copied ? <Check size={14} /> : <Copy size={14} />}{copied ? t.copied : t.copy}
              </button>
            </header>
            <pre className="whitespace-pre-wrap break-words p-5 font-sans text-sm leading-7 text-[#c9c5bc]">{selected.body}</pre>
          </article>
        </div>
      )}
      <TruthNote>{t.outputsTruthNote}</TruthNote>
    </WorkspacePage>
  );
};
