"use client";

import React from 'react';
import { Bot, Check, Copy } from 'lucide-react';

import { dictionaryFor } from '@/i18n';
import { useOperatorStore } from '@/store/useOperatorStore';
import { useUIStore } from '@/store/useUIStore';

export const OperatorResponseDraft = () => {
  const language = useUIStore((state) => state.language);
  const t = dictionaryFor(language).operatorShell;
  const artifacts = useOperatorStore((state) => state.artifacts);
  const selectedArtifactId = useOperatorStore((state) => state.selectedArtifactId);
  const selectedArtifact = artifacts.find((artifact) => artifact.id === selectedArtifactId) ?? artifacts[0] ?? null;
  const [copied, setCopied] = React.useState(false);

  const copyText = React.useMemo(() => {
    if (!selectedArtifact) return '';
    return [selectedArtifact.title, '', selectedArtifact.body, '', t.responseDraftSafetyFooter].filter(Boolean).join('\n');
  }, [selectedArtifact, t.responseDraftSafetyFooter]);

  const copyDraft = React.useCallback(async () => {
    if (!copyText || !navigator.clipboard) return;
    await navigator.clipboard.writeText(copyText);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1200);
  }, [copyText]);

  if (!selectedArtifact) return null;

  return (
    <article className="flex gap-3 sm:gap-4">
      <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-[#4a4333] bg-[#28241c] text-[#f4bf4f]">
        <Bot size={16} />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs font-semibold text-[#f4bf4f]">Aegis</p>
            <h2 className="mt-1 text-lg font-semibold text-[#f4f1ea]">{selectedArtifact.title}</h2>
          </div>
          <button type="button" onClick={() => void copyDraft()} className="flex h-10 items-center gap-2 rounded-md px-3 text-xs text-[#918d86] hover:bg-[#242321] hover:text-[#f4f1ea]" aria-label={t.copyDraft}>
            {copied ? <Check size={14} /> : <Copy size={14} />}
            <span className="hidden sm:inline">{copied ? t.copiedDraft : t.copyDraft}</span>
          </button>
        </div>
        {selectedArtifact.summary && <p className="mt-3 text-sm leading-6 text-[#aaa69e]">{selectedArtifact.summary}</p>}
        <pre className="mt-4 whitespace-pre-wrap break-words border-l border-[#3b3935] pl-4 font-sans text-sm leading-7 text-[#d1cdc4]">{selectedArtifact.body}</pre>
        <p className="mt-4 text-xs leading-5 text-[#77736d]">{t.responseDraftSafetyFooter}</p>
      </div>
    </article>
  );
};
