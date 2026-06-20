"use client";

import { Bot, Boxes, Settings2, SlidersHorizontal } from 'lucide-react';

import { dictionaryFor } from '@/i18n';
import { useUIStore } from '@/store/useUIStore';

import { TruthNote, WorkspacePage } from './HistorySurface';

export const CustomizeSurface = () => {
  const language = useUIStore((state) => state.language);
  const t = dictionaryFor(language).workspace;
  const setActiveTab = useUIStore((state) => state.setActiveTab);
  const items = [
    { tab: 'Skills', icon: <Boxes size={20} />, title: t.customizeSkillsTitle, copy: t.customizeSkillsCopy },
    { tab: 'Settings', icon: <Bot size={20} />, title: t.customizeModelsTitle, copy: t.customizeModelsCopy },
    { tab: 'Memory', icon: <Settings2 size={20} />, title: t.customizeMemoryTitle, copy: t.customizeMemoryCopy },
    { tab: 'Advanced', icon: <SlidersHorizontal size={20} />, title: t.customizeAdvancedTitle, copy: t.customizeAdvancedCopy },
  ];

  return (
    <WorkspacePage title={t.customizeTitle} description={t.customizeDescription}>
      <div className="grid gap-3 sm:grid-cols-2">
        {items.map((item) => (
          <button key={item.tab} type="button" onClick={() => setActiveTab(item.tab)} className="min-h-32 rounded-lg border border-[#33312e] bg-[#1a1a19] p-5 text-left hover:border-[#5b5039] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[#f4bf4f]">
            <span className="text-[#f4bf4f]">{item.icon}</span>
            <span className="mt-4 block text-sm font-semibold text-[#ece9e2]">{item.title}</span>
            <span className="mt-2 block text-xs leading-5 text-[#817d76]">{item.copy}</span>
          </button>
        ))}
      </div>
      <TruthNote>{t.customizeTruthNote}</TruthNote>
    </WorkspacePage>
  );
};
