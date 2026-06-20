"use client";

import type React from 'react';
import { FolderKanban, ListChecks, SearchCode } from 'lucide-react';

import { dictionaryFor } from '@/i18n';
import { useOperatorStore } from '@/store/useOperatorStore';
import { useUIStore } from '@/store/useUIStore';

import { Empty, TruthNote, WorkspacePage } from './HistorySurface';

export const ProjectsSurface = () => {
  const language = useUIStore((state) => state.language);
  const t = dictionaryFor(language).workspace;
  const setComposerText = useOperatorStore((state) => state.setComposerText);
  const setActiveTab = useUIStore((state) => state.setActiveTab);
  const openPrompt = (prompt: string) => {
    setComposerText(prompt);
    setActiveTab('Operator');
  };

  return (
    <WorkspacePage title={t.projectsTitle} description={t.projectsDescription}>
      <Empty icon={<FolderKanban size={24} />} title={t.projectsEmptyTitle} copy={t.projectsEmptyCopy} />
      <div className="grid gap-3 sm:grid-cols-2">
        <ProjectAction icon={<ListChecks size={18} />} title={t.projectPlanTitle} copy={t.projectPlanCopy} onClick={() => openPrompt(t.projectPlanPrompt)} />
        <ProjectAction icon={<SearchCode size={18} />} title={t.projectReviewTitle} copy={t.projectReviewCopy} onClick={() => openPrompt(t.projectReviewPrompt)} />
      </div>
      <TruthNote>{t.projectsTruthNote}</TruthNote>
    </WorkspacePage>
  );
};

const ProjectAction = ({ icon, title, copy, onClick }: { icon: React.ReactNode; title: string; copy: string; onClick: () => void }) => (
  <button type="button" onClick={onClick} className="min-h-24 rounded-lg border border-[#33312e] bg-[#1a1a19] p-4 text-left hover:border-[#5b5039] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[#f4bf4f]">
    <span className="text-[#f4bf4f]">{icon}</span>
    <span className="mt-3 block text-sm font-semibold text-[#ece9e2]">{title}</span>
    <span className="mt-1 block text-xs leading-5 text-[#817d76]">{copy}</span>
  </button>
);
