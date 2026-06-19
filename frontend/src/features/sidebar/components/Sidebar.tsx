"use client";

import React from 'react';
import {
  Archive,
  Bot,
  Database,
  FolderKanban,
  History,
  Plus,
  Settings,
  Shield,
  SlidersHorizontal,
  Wrench,
} from 'lucide-react';

import { dictionaryFor } from '@/i18n';
import { useUIStore } from '@/store/useUIStore';

const NAV_ITEMS = [
  { id: 'History', icon: <History size={19} />, labelKey: 'history', detailKey: 'history' },
  { id: 'Projects', icon: <FolderKanban size={19} />, labelKey: 'projects', detailKey: 'projects' },
  { id: 'Outputs', icon: <Archive size={19} />, labelKey: 'outputs', detailKey: 'outputs' },
  { id: 'Memory', icon: <Database size={19} />, labelKey: 'memory', detailKey: 'memory' },
  { id: 'Skills', icon: <Wrench size={19} />, labelKey: 'skills', detailKey: 'skills' },
] as const;

export const Sidebar = () => {
  const activeTab = useUIStore((state) => state.activeTab);
  const setActiveTab = useUIStore((state) => state.setActiveTab);
  const language = useUIStore((state) => state.language);
  const t = dictionaryFor(language);

  return (
    <aside className="electron-drag-region relative z-50 flex w-16 shrink-0 flex-col border-r border-white/10 bg-[#202123]/[0.96] backdrop-blur-2xl lg:w-72">
      <div className="flex h-16 items-center justify-center gap-3 border-b border-white/10 px-3 lg:justify-start lg:px-4">
        <AegisMark />
        <div className="hidden min-w-0 flex-col lg:flex">
          <span className="text-base font-semibold text-white">Aegis</span>
          <span className="mt-0.5 text-[11px] text-foreground/45">{t.navDetails.operatorSubtitle}</span>
        </div>
      </div>

      <nav className="electron-no-drag flex-1 space-y-1 overflow-y-auto px-2 py-4 custom-scrollbar lg:px-3">
        <NavItem
          icon={<Plus size={18} />}
          label={t.nav.newTask}
          detail={t.navDetails.newTask}
          active={activeTab === 'Operator'}
          onClick={() => setActiveTab('Operator')}
          primary
        />
        <div className="my-3 h-px bg-white/10" />
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

      <div className="electron-no-drag space-y-2 border-t border-white/10 p-2 lg:p-3">
        <button
          type="button"
          onClick={() => setActiveTab('Settings')}
          className={`group flex w-full items-center justify-center gap-3 rounded-xl border p-2.5 text-left transition-colors lg:justify-start lg:p-3 ${
            activeTab === 'Settings'
              ? 'border-accent/30 bg-accent/[0.1] text-accent'
              : 'border-white/10 bg-white/[0.035] text-foreground/55 hover:border-white/20 hover:text-white'
          }`}
          aria-label={t.nav.settings}
        >
          <Settings size={18} />
          <span className="hidden min-w-0 flex-col lg:flex">
            <span className="text-[13px] font-semibold">{t.nav.settings}</span>
            <span className="text-[10px] text-foreground/38">{t.navDetails.settings}</span>
          </span>
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('Advanced')}
          className={`group flex w-full items-center justify-center gap-3 rounded-xl border p-2.5 text-left transition-colors lg:justify-start lg:p-3 ${
            activeTab === 'Advanced'
              ? 'border-warning/30 bg-warning/[0.1] text-warning'
              : 'border-white/10 bg-white/[0.025] text-foreground/45 hover:border-white/20 hover:text-white'
          }`}
          aria-label={t.nav.advanced}
        >
          <SlidersHorizontal size={18} />
          <span className="hidden min-w-0 flex-col lg:flex">
            <span className="text-[13px] font-semibold">{t.nav.advanced}</span>
            <span className="text-[10px] text-foreground/38">{t.navDetails.advanced}</span>
          </span>
        </button>
        <div className="hidden rounded-xl border border-white/10 bg-white/[0.025] p-3 lg:block">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-accent/20 bg-accent/10 text-accent">
              <Shield size={16} />
            </div>
            <div className="min-w-0">
              <div className="truncate text-sm font-semibold text-white">Aegis</div>
              <div className="mt-0.5 text-[11px] text-foreground/45">{t.nav.localOperator}</div>
            </div>
            <span className="ml-auto h-2 w-2 rounded-full bg-accent shadow-[0_0_10px_rgba(6,182,212,0.65)]" />
          </div>
          <p className="mt-3 text-[11px] leading-relaxed text-foreground/42">
            {t.navDetails.localOperatorCopy}
          </p>
        </div>
      </div>
    </aside>
  );
};

const AegisMark = () => (
  <div className="relative flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-accent/20 bg-accent/[0.1] shadow-[0_0_22px_rgba(6,182,212,0.18)]">
    <Bot size={19} className="relative z-10 text-accent" />
  </div>
);

const NavItem = ({
  icon,
  label,
  detail,
  active,
  primary = false,
  onClick,
}: {
  icon: React.ReactNode;
  label: string;
  detail: string;
  active: boolean;
  primary?: boolean;
  onClick: () => void;
}) => (
  <button
    type="button"
    aria-label={label}
    onClick={onClick}
    className={`group relative flex w-full items-center justify-center gap-3 overflow-hidden rounded-xl border p-2.5 text-left transition-all lg:justify-start lg:p-3 ${
      active
        ? 'border-white/15 bg-white/[0.09] text-white'
        : primary
          ? 'border-white/10 bg-white/[0.05] text-foreground/68 hover:border-accent/25 hover:text-accent'
          : 'border-transparent text-foreground/52 hover:border-white/10 hover:bg-white/[0.035] hover:text-white'
    }`}
  >
    {active && <span className="absolute left-0 top-2 h-[calc(100%-1rem)] w-0.5 rounded-r-full bg-accent" />}
    <span className={`relative z-10 ${active ? 'text-accent' : 'text-foreground/52 group-hover:text-white'}`}>
      {icon}
    </span>
    <span className="relative z-10 hidden min-w-0 flex-col lg:flex">
      <span className="text-[14px] font-semibold">{label}</span>
      <span className="mt-0.5 max-w-full truncate text-[10px] text-foreground/36 group-hover:text-foreground/50">
        {detail}
      </span>
    </span>
  </button>
);
