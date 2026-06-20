"use client";

import React from 'react';
import { AlertTriangle, Check, Copy, Cpu, Loader2 } from 'lucide-react';

import { dictionaryFor } from '@/i18n';
import { useOperatorStore } from '@/store/useOperatorStore';
import { useUIStore } from '@/store/useUIStore';

export const OperatorLocalProposalPanel = () => {
  const language = useUIStore((state) => state.language);
  const setActiveTab = useUIStore((state) => state.setActiveTab);
  const t = dictionaryFor(language).operatorShell;
  const decision = useOperatorStore((state) => state.lastDecision);
  const modelPreference = useOperatorStore((state) => state.modelPreference);
  const planningDetail = useOperatorStore((state) => state.planningDetail);
  const status = useOperatorStore((state) => state.localProposalStatus);
  const proposal = useOperatorStore((state) => state.localProposal);
  const error = useOperatorStore((state) => state.localProposalError);
  const generate = useOperatorStore((state) => state.generateLocalProposal);
  const [copied, setCopied] = React.useState(false);

  if (!decision) return null;
  const boundaryBlocked = modelPreference === 'external_provider' || modelPreference === 'vision_review';
  const preferenceLabel = t[`modelPreference_${modelPreference}`];

  const copyProposal = async () => {
    if (!proposal?.outputText || !navigator.clipboard) return;
    await navigator.clipboard.writeText(proposal.outputText);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1200);
  };

  return (
    <section className="mt-7 border-t border-[#302f2c] pt-6" aria-labelledby="local-proposal-title">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
        <div className="max-w-2xl">
          <div className="flex items-center gap-2 text-xs font-semibold text-[#f4bf4f]"><Cpu size={15} />{t.localProposal}</div>
          <h2 id="local-proposal-title" className="mt-2 text-base font-semibold text-[#f4f1ea]">{t.localProposalTitle}</h2>
          <p className="mt-2 text-sm leading-6 text-[#8f8b84]">{t.localProposalCopy}</p>
        </div>
        <button
          type="button"
          onClick={() => void generate()}
          disabled={status === 'loading' || boundaryBlocked}
          className="inline-flex h-10 shrink-0 items-center justify-center gap-2 rounded-md border border-[#665b3f] bg-[#28241c] px-4 text-xs font-semibold text-[#f4d27d] hover:bg-[#312b20] disabled:cursor-not-allowed disabled:opacity-45"
        >
          {status === 'loading' ? <Loader2 size={15} className="animate-spin" /> : <Cpu size={15} />}
          {status === 'loading' ? t.generatingLocalDraft : t.generateLocalDraft}
        </button>
      </div>

      <details className="mt-4 rounded-md border border-[#302f2c] bg-[#181817] px-4 py-3 text-xs text-[#9d9991]">
        <summary className="cursor-pointer font-medium text-[#c8c3ba]">{t.proposalInput}</summary>
        <dl className="mt-3 grid gap-2 sm:grid-cols-[9rem_1fr]">
          <dt>{t.proposalRequest}</dt><dd className="break-words text-[#ddd8cf]">{decision.request}</dd>
          <dt>{t.proposalRoute}</dt><dd className="text-[#ddd8cf]">{decision.routeId}</dd>
          <dt>{t.proposalIntent}</dt><dd className="text-[#ddd8cf]">{decision.primaryIntent}</dd>
          <dt>{t.proposalCandidate}</dt><dd className="text-[#ddd8cf]">{preferenceLabel}</dd>
          <dt>{t.proposalDetail}</dt><dd className="text-[#ddd8cf]">{t[`planningDetail_${planningDetail}`]}</dd>
        </dl>
        <p className="mt-3 border-t border-[#302f2c] pt-3 leading-5">{t.proposalInputBoundary}</p>
      </details>

      {boundaryBlocked && (
        <div className="mt-4 flex items-start gap-2 rounded-md border border-amber-500/20 bg-amber-500/[0.06] p-3 text-xs leading-5 text-amber-100">
          <AlertTriangle size={15} className="mt-0.5 shrink-0" />
          <span>{modelPreference === 'external_provider' ? t.externalProposalBlocked : t.visionProposalBlocked} <button type="button" className="underline underline-offset-2" onClick={() => setActiveTab('Settings')}>{t.openModelSettings}</button></span>
        </div>
      )}
      {status === 'failed' && error && <div role="alert" className="mt-4 flex items-start gap-2 rounded-md border border-red-500/25 bg-red-500/10 p-3 text-xs leading-5 text-red-200"><AlertTriangle size={15} className="mt-0.5 shrink-0" />{error}</div>}

      {status === 'completed' && proposal && (
        <article className="mt-5 rounded-lg border border-[#4a4333] bg-[#1b1916] p-4 sm:p-5">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-semibold text-[#f4bf4f]">{t.localProposal}</p>
              <p className="mt-1 text-xs text-[#8f8b84]">{proposal.model ?? t.configuredLocalModel} · {proposal.backendStatus}</p>
            </div>
            <button type="button" onClick={() => void copyProposal()} className="inline-flex h-10 items-center gap-2 rounded-md px-3 text-xs text-[#a8a39a] hover:bg-[#292825] hover:text-white">
              {copied ? <Check size={14} /> : <Copy size={14} />}{copied ? t.copiedDraft : t.copyDraft}
            </button>
          </div>
          <pre className="mt-4 whitespace-pre-wrap break-words font-sans text-sm leading-7 text-[#ddd8cf]">{proposal.outputText}</pre>
          <div className="mt-4 flex flex-wrap gap-2 border-t border-[#34312b] pt-4 text-[11px] text-[#aaa49a]">
            {[t.unverifiedModelOutput, t.notEvidence, t.notExecution, t.notApproval, t.notVerifierSuccess].map((label) => <span key={label} className="rounded-sm border border-[#4a4333] bg-black/15 px-2 py-1">{label}</span>)}
          </div>
          {(proposal.warnings.length > 0 || proposal.limitations.length > 0) && <p className="mt-3 text-xs leading-5 text-[#918b81]">{[...proposal.warnings, ...proposal.limitations].join(' · ')}</p>}
        </article>
      )}
    </section>
  );
};
