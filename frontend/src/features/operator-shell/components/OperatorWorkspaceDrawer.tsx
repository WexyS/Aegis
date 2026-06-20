"use client";

import React from 'react';
import { Bot, BrainCircuit, Database, FolderKanban, Layers3, Settings2, TerminalSquare, Wrench } from 'lucide-react';

import { dictionaryFor } from '@/i18n';
import { useUIStore } from '@/store/useUIStore';

type WorkspaceShortcut = {
  label: string;
  detail: string;
  target: string;
  icon: React.ReactNode;
};

export const OperatorWorkspaceDrawer = () => {
  const language = useUIStore((state) => state.language);
  const setActiveTab = useUIStore((state) => state.setActiveTab);
  const t = dictionaryFor(language).operatorShell;

  const shortcuts: WorkspaceShortcut[] = [
    { label: t.openAskDetails, detail: t.workspaceAskDetail, target: 'History', icon: <Bot size={15} /> },
    { label: t.openWorkTools, detail: t.workspaceWorkDetail, target: 'Projects', icon: <TerminalSquare size={15} /> },
    { label: t.openOutputs, detail: t.workspaceOutputsDetail, target: 'Outputs', icon: <FolderKanban size={15} /> },
    { label: t.openMemoryTools, detail: t.workspaceMemoryDetail, target: 'Memory', icon: <Database size={15} /> },
    { label: t.openModelHub, detail: t.workspaceModelDetail, target: 'Settings', icon: <BrainCircuit size={15} /> },
    { label: t.openSkillsConnectors, detail: t.workspaceSkillsDetail, target: 'Skills', icon: <Wrench size={15} /> },
    { label: t.openAdvancedDiagnostics, detail: t.workspaceAdvancedDetail, target: 'Advanced', icon: <Layers3 size={15} /> },
    { label: t.openSettings, detail: t.workspaceSettingsDetail, target: 'Settings', icon: <Settings2 size={15} /> },
  ];

  return (
    <section>
      <div className="mb-3">
        <h2 className="text-sm font-semibold text-[#ece9e2]">{t.workspaceDrawerTitle}</h2>
        <p className="mt-1 text-xs leading-5 text-[#817d76]">{t.workspaceDrawerCopy}</p>
      </div>
      <div className="grid gap-2">
        {shortcuts.map((shortcut) => (
          <button
            key={shortcut.label}
            type="button"
            onClick={() => setActiveTab(shortcut.target)}
            className="flex min-h-11 items-start gap-3 rounded-md border border-[#33312e] bg-[#191918] px-3 py-2.5 text-left transition-colors hover:border-[#5b5039] hover:bg-[#22211f]"
          >
            <span className="mt-0.5 shrink-0 text-[#f4bf4f]">{shortcut.icon}</span>
            <span className="min-w-0">
              <span className="block text-xs font-semibold text-[#c9c5bc]">{shortcut.label}</span>
              <span className="mt-0.5 block break-words text-[11px] leading-5 text-[#77736d]">{shortcut.detail}</span>
            </span>
          </button>
        ))}
      </div>
    </section>
  );
};
