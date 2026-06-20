"use client";

import { FileText, HelpCircle, MemoryStick, MonitorCog, Search, Wand2 } from 'lucide-react';

import { dictionaryFor } from '@/i18n';
import { useOperatorStore } from '@/store/useOperatorStore';
import { useUIStore } from '@/store/useUIStore';

export const OperatorQuickActions = () => {
  const language = useUIStore((state) => state.language);
  const t = dictionaryFor(language).operatorShell;
  const setComposerText = useOperatorStore((state) => state.setComposerText);
  const actions = [
    { label: t.quickInspectStatus, prompt: t.quickInspectStatusPrompt, icon: <HelpCircle size={17} /> },
    { label: t.quickDraftCodexPrompt, prompt: t.quickDraftCodexPromptPrompt, icon: <FileText size={17} /> },
    { label: t.quickAnalyzeUiIssue, prompt: t.quickAnalyzeUiIssuePrompt, icon: <MonitorCog size={17} /> },
    { label: t.quickPlanNextSprint, prompt: t.quickPlanNextSprintPrompt, icon: <Wand2 size={17} /> },
    { label: t.quickExplainModelHub, prompt: t.quickExplainModelHubPrompt, icon: <Search size={17} /> },
    { label: t.quickReviewMemoryPolicy, prompt: t.quickReviewMemoryPolicyPrompt, icon: <MemoryStick size={17} /> },
  ];

  return (
    <section className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3" aria-label={t.quickActionsTitle}>
      {actions.map((action) => (
        <button
          key={action.label}
          type="button"
          onClick={() => setComposerText(action.prompt)}
          className="flex min-h-16 items-center gap-3 rounded-lg border border-[#302f2c] bg-[#181817] px-4 text-left text-sm text-[#aaa69e] hover:border-[#4b463b] hover:bg-[#1d1c1a] hover:text-[#ece9e2] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[#f4bf4f]"
        >
          <span className="shrink-0 text-[#f4bf4f]">{action.icon}</span>
          <span className="min-w-0 leading-5">{action.label}</span>
        </button>
      ))}
    </section>
  );
};
