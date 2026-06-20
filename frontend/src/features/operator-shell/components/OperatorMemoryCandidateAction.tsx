"use client";

import React from 'react';
import { Brain } from 'lucide-react';

import { MemoryCandidateForm } from '@/features/workspace/components/MemoryCandidateForm';
import { dictionaryFor } from '@/i18n';
import { useOperatorStore } from '@/store/useOperatorStore';
import { useUIStore } from '@/store/useUIStore';

export const OperatorMemoryCandidateAction = () => {
  const language = useUIStore((state) => state.language);
  const setActiveTab = useUIStore((state) => state.setActiveTab);
  const t = dictionaryFor(language).memory;
  const decision = useOperatorStore((state) => state.lastDecision);
  const [open, setOpen] = React.useState(false);
  const [created, setCreated] = React.useState(false);

  if (!decision?.intents.includes('memory_action')) return null;

  return (
    <section className="mt-7 border-t border-[#302f2c] pt-6">
      {!open ? (
        <div className="flex flex-col justify-between gap-4 rounded-lg border border-[#34322f] bg-[#181817] p-4 sm:flex-row sm:items-center">
          <div>
            <h2 className="flex items-center gap-2 text-sm font-semibold text-[#f4f1ea]"><Brain size={16} className="text-[#f4bf4f]" />{t.operatorCandidateTitle}</h2>
            <p className="mt-1 text-xs leading-5 text-[#8f8b84]">{t.operatorCandidateCopy}</p>
          </div>
          <button type="button" onClick={() => { setCreated(false); setOpen(true); }} className="h-10 shrink-0 rounded-md border border-[#665b3f] bg-[#28241c] px-4 text-xs font-semibold text-[#f4d27d] hover:bg-[#312b20]">{t.createMemoryCandidate}</button>
        </div>
      ) : (
        <MemoryCandidateForm
          initialContent={decision.request}
          onCancel={() => setOpen(false)}
          onCreated={() => { setCreated(true); setOpen(false); }}
        />
      )}
      {created && <div role="status" className="mt-3 flex items-center justify-between gap-3 rounded-md border border-emerald-500/20 bg-emerald-500/[0.06] p-3 text-xs text-emerald-100"><span>{t.candidateCreated}</span><button type="button" className="underline underline-offset-2" onClick={() => setActiveTab('Memory')}>{t.openMemoryInbox}</button></div>}
    </section>
  );
};
