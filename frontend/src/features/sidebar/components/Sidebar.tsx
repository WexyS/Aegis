"use client";

import React from 'react';
import { Archive, Bot, Database, FolderKanban, History, Plus, Settings, Shield, SlidersHorizontal, Sparkles } from 'lucide-react';

import { dictionaryFor } from '@/i18n';
import { useOperatorStore } from '@/store/useOperatorStore';
import { useUIStore } from '@/store/useUIStore';

const NAV_ITEMS = [
  { id: 'History', icon: <History size={18} />, labelKey: 'history', detailKey: 'history' },
  { id: 'Projects', icon: <FolderKanban size={18} />, labelKey: 'projects', detailKey: 'projects' },
  { id: 'Outputs', icon: <Archive size={18} />, labelKey: 'outputs', detailKey: 'outputs' },
  { id: 'Memory', icon: <Database size={18} />, labelKey: 'memory', detailKey: 'memory' },
  { id: 'Customize', icon: <Sparkles size={18} />, labelKey: 'customize', detailKey: 'customize' },
  { id: 'Settings', icon: <Settings size={18} />, labelKey: 'settings', detailKey: 'settings' },
] as const;

export const Sidebar = () => {
  const activeTab = useUIStore((state) => state.activeTab);
  const setActiveTab = useUIStore((state) => state.setActiveTab);
  const language = useUIStore((state) => state.language);
  const startNewTask = useOperatorStore((state) => state.startNewTask);
  const t = dictionaryFor(language);

  return (
    <aside className="electron-drag-region relative z-50 flex w-14 shrink-0 flex-col border-r border-[#2b2a28] bg-[#191919] lg:w-60">
      <div className="flex h-14 items-center justify-center gap-3 border-b border-[#2b2a28] px-2 lg:justify-start lg:px-4">
        <AegisMark />
        <div className="hidden min-w-0 flex-col lg:flex">
          <span className="text-base font-semibold text-[#f4f1ea]">Aegis</span>
          <span className="mt-0.5 text-[11px] text-[#85817a]">{t.navDetails.operatorSubtitle}</span>
        </div>
      </div>

      <nav className="electron-no-drag flex-1 space-y-1 overflow-y-auto px-2 py-4 custom-scrollbar lg:px-3">
        <NavItem
          icon={<Plus size={18} />}
          label={t.nav.newTask}
          detail={t.navDetails.newTask}
          active={activeTab === 'Operator'}
          primary
          onClick={() => {
            startNewTask();
            setActiveTab('Operator');
          }}
        />
        <div className="my-3 h-px bg-[#2b2a28]" />
        {NAV_ITEMS.map((item) => (
          <NavItem
            key={item.id}
            icon={item.icon}
            label={t.nav[item.labelKey]}
            detail={t.navDetails[item.detailKey]}
            active={activeTab === item.id}
            onClick={() => setActiveTab(item.id)}
          />
        ))}
      </nav>

      <div className="electron-no-drag space-y-2 border-t border-[#2b2a28] p-2 lg:p-3">
        <button
          type="button"
          onClick={() => setActiveTab('Advanced')}
          className={`group flex min-h-10 w-full items-center justify-center gap-3 rounded-lg border px-2.5 py-2 text-left transition-colors lg:justify-start ${
            activeTab === 'Advanced'
              ? 'border-[#4a4333] bg-[#2a261e] text-[#f4bf4f]'
              : 'border-transparent text-[#77736d] hover:border-[#34322f] hover:bg-[#222220] hover:text-[#e9e5dd]'
          }`}
          aria-label={t.nav.advancedTools}
        >
          <SlidersHorizontal size={18} />
          <span className="hidden min-w-0 flex-col lg:flex">
            <span className="text-[13px] font-semibold">{t.nav.advancedTools}</span>
            <span className="text-[10px] text-[#716d66]">{t.navDetails.advanced}</span>
          </span>
        </button>

        <div className="hidden rounded-lg border border-[#2f2e2b] bg-[#1d1d1c] p-3 lg:block">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-[#4a4333] bg-[#28241c] text-[#f4bf4f]">
              <Shield size={16} />
            </div>
            <div className="min-w-0">
              <div className="truncate text-sm font-semibold text-[#f4f1ea]">Aegis</div>
              <div className="mt-0.5 text-[11px] text-[#85817a]">{t.nav.localOperator}</div>
            </div>
            <span className="ml-auto h-2 w-2 rounded-full bg-[#f4bf4f]" />
          </div>
          <p className="mt-3 text-[11px] leading-relaxed text-[#77736d]">{t.navDetails.localOperatorCopy}</p>
        </div>
      </div>
    </aside>
  );
};

const AegisMark = () => (
  <div className="relative flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-[#4a4333] bg-[#28241c]">
    <Bot size={19} className="relative z-10 text-[#f4bf4f]" />
  </div>
);

const NavItem = ({ icon, label, detail, active, primary = false, onClick }: { icon: React.ReactNode; label: string; detail: string; active: boolean; primary?: boolean; onClick: () => void }) => (
  <button
    type="button"
    aria-label={label}
    onClick={onClick}
    className={`group relative flex min-h-10 w-full items-center justify-center gap-3 overflow-hidden rounded-lg border px-2.5 py-2 text-left transition-colors lg:justify-start ${
      active
        ? 'border-[#3a3834] bg-[#2a2927] text-[#f4f1ea]'
        : primary
          ? 'border-[#3a3834] bg-[#242321] text-[#dedad2] hover:border-[#5b5039] hover:text-[#f4bf4f]'
          : 'border-transparent text-[#918d86] hover:border-[#34322f] hover:bg-[#222220] hover:text-[#f4f1ea]'
    }`}
  >
    {active && <span className="absolute left-0 top-2 h-[calc(100%-1rem)] w-0.5 rounded-r-full bg-[#f4bf4f]" />}
    <span className={`relative z-10 ${active ? 'text-[#f4bf4f]' : 'text-[#8f8b84] group-hover:text-[#f4f1ea]'}`}>{icon}</span>
    <span className="relative z-10 hidden min-w-0 flex-col lg:flex">
      <span className="text-[14px] font-semibold">{label}</span>
      <span className="mt-0.5 max-w-full truncate text-[10px] text-[#6f6b65] group-hover:text-[#918d86]">{detail}</span>
    </span>
  </button>
);
