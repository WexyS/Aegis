"use client";

import React from 'react';
import { FileText, HelpCircle, MemoryStick, MonitorCog, Search, Wand2 } from 'lucide-react';

import { dictionaryFor } from '@/i18n';
import { useOperatorStore } from '@/store/useOperatorStore';
import { useUIStore } from '@/store/useUIStore';

export const OperatorQuickActions = () => {
  const language = useUIStore((state) => state.language);
  const t = dictionaryFor(language).operatorShell;
  const setComposerText = useOperatorStore((state) => state.setComposerText);
  const actions = [
    { label: t.quickInspectStatus, prompt: t.quickInspectStatusPrompt, icon: <HelpCircle size={14} /> },
    { label: t.quickDraftCodexPrompt, prompt: t.quickDraftCodexPromptPrompt, icon: <FileText size={14} /> },
    { label: t.quickAnalyzeUiIssue, prompt: t.quickAnalyzeUiIssuePrompt, icon: <MonitorCog size={14} /> },
    { label: t.quickPlanNextSprint, prompt: t.quickPlanNextSprintPrompt, icon: <Wand2 size={14} /> },
    { label: t.quickExplainModelHub, prompt: t.quickExplainModelHubPrompt, icon: <Search size={14} /> },
    { label: t.quickReviewMemoryPolicy, prompt: t.quickReviewMemoryPolicyPrompt, icon: <MemoryStick size={14} /> },
  ];

  return (
    <section>
      <div className="mb-2 flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-xs font-semibold text-foreground/58">{t.quickActionsTitle}</h2>
        <p className="text-[11px] text-foreground/42">{t.quickActionsCopy}</p>
      </div>
      <div className="flex flex-wrap gap-2">
        {actions.map((action) => (
          <button
            key={action.label}
            type="button"
            onClick={() => setComposerText(action.prompt)}
            className="inline-flex min-h-[34px] items-center gap-2 rounded-xl border border-white/10 bg-white/[0.04] px-3 text-left text-xs font-semibold text-foreground/62 transition-colors hover:border-accent/30 hover:bg-accent/[0.06] hover:text-accent"
          >
            {action.icon}
            <span className="min-w-0 break-words">{action.label}</span>
          </button>
        ))}
      </div>
    </section>
  );
};
