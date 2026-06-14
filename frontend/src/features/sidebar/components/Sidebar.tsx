"use client";

import React from 'react';
import {
  Box,
  BriefcaseBusiness,
  Database,
  HelpCircle,
  Layers3,
  Radar,
  Settings,
  Shield,
  SlidersHorizontal,
} from 'lucide-react';

import { dictionaryFor } from '@/i18n';
import { useUIStore } from '@/store/useUIStore';

const NAV_ITEMS = [
  { id: 'Mission', icon: <Radar size={19} />, labelKey: 'mission', detailKey: 'mission' },
  { id: 'Ask', icon: <HelpCircle size={19} />, labelKey: 'ask', detailKey: 'ask' },
  { id: 'Work', icon: <BriefcaseBusiness size={19} />, labelKey: 'work', detailKey: 'work' },
  { id: 'Memory', icon: <Database size={19} />, labelKey: 'memory', detailKey: 'memory' },
  { id: 'Capabilities', icon: <Box size={19} />, labelKey: 'capabilities', detailKey: 'capabilities' },
  { id: 'Advanced', icon: <Layers3 size={19} />, labelKey: 'advanced', detailKey: 'advanced' },
] as const;

export const Sidebar = () => {
  const activeTab = useUIStore((state) => state.activeTab);
  const setActiveTab = useUIStore((state) => state.setActiveTab);
  const language = useUIStore((state) => state.language);
  const t = dictionaryFor(language);

  return (
    <aside className="electron-drag-region relative z-50 flex w-16 shrink-0 flex-col border-r border-white/10 bg-[#08080d]/[0.88] backdrop-blur-2xl lg:w-72">
      <div className="flex h-20 items-center justify-center gap-3 border-b border-white/10 px-3 lg:justify-start lg:px-5">
        <AegisMark />
        <div className="hidden min-w-0 flex-col lg:flex">
          <span className="text-lg font-semibold tracking-[0.28em] text-white">AEGIS</span>
          <span className="mt-0.5 text-[10px] font-semibold uppercase tracking-[0.24em] text-accent/75">{t.navDetails.operatorSubtitle}</span>
        </div>
      </div>

      <nav className="electron-no-drag flex-1 space-y-2 overflow-y-auto px-2 py-5 custom-scrollbar lg:px-4">
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

      <div className="electron-no-drag space-y-3 border-t border-white/10 p-2 lg:p-4">
        <button
          type="button"
          onClick={() => setActiveTab('Settings')}
          className={`group flex w-full items-center justify-center gap-3 rounded-xl border p-2.5 text-left transition-colors lg:justify-start lg:p-3 ${
            activeTab === 'Settings'
              ? 'border-secondary/35 bg-secondary/[0.12] text-secondary-light shadow-[0_0_28px_rgba(139,92,246,0.18)]'
              : 'border-white/10 bg-white/[0.035] text-foreground/55 hover:border-white/20 hover:text-white'
          }`}
          aria-label={t.nav.settings}
        >
            <Settings size={18} />
          <span className="hidden min-w-0 flex-col lg:flex">
            <span className="text-[13px] font-semibold">{t.nav.settings}</span>
            <span className="text-[9px] font-mono uppercase tracking-wider opacity-55">{t.navDetails.settings}</span>
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
        <button
          type="button"
          onClick={() => setActiveTab('Advanced')}
          className="flex w-full items-center justify-center gap-3 rounded-xl border border-white/10 bg-white/[0.025] p-2.5 text-foreground/45 transition-colors hover:text-white lg:hidden"
          aria-label={t.nav.advanced}
        >
          <SlidersHorizontal size={18} />
        </button>
      </div>
    </aside>
  );
};

const AegisMark = () => (
  <div className="relative flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-secondary/25 bg-secondary/[0.12] shadow-[0_0_24px_rgba(139,92,246,0.24)]">
    <div className="absolute inset-1 rounded-lg bg-gradient-to-br from-secondary-light/40 via-secondary/20 to-accent/20 blur-[2px]" />
    <div className="relative h-6 w-6">
      <div className="absolute left-1 top-0 h-6 w-2.5 -rotate-[28deg] rounded-full bg-gradient-to-b from-secondary-light to-secondary" />
      <div className="absolute right-1 top-0 h-6 w-2.5 rotate-[28deg] rounded-full bg-gradient-to-b from-accent-light to-secondary" />
      <div className="absolute bottom-0 left-[7px] h-2.5 w-3 rounded-full bg-[#09090d]" />
    </div>
  </div>
);

const NavItem = ({
  icon,
  label,
  detail,
  active,
  onClick,
}: {
  icon: React.ReactNode;
  label: string;
  detail: string;
  active: boolean;
  onClick: () => void;
}) => (
  <button
    type="button"
    aria-label={label}
    onClick={onClick}
    className={`group relative flex w-full items-center justify-center gap-3 overflow-hidden rounded-xl border p-2.5 text-left transition-all lg:justify-start lg:p-3 ${
      active
        ? 'border-secondary/35 bg-white/[0.07] text-white shadow-[0_0_34px_rgba(139,92,246,0.18)]'
        : 'border-transparent text-foreground/48 hover:border-white/10 hover:bg-white/[0.035] hover:text-white'
    }`}
  >
    {active && <span className="absolute left-0 top-2 h-[calc(100%-1rem)] w-0.5 rounded-r-full bg-secondary-light shadow-[0_0_12px_rgba(167,139,250,0.9)]" />}
    <span className={`relative z-10 ${active ? 'text-secondary-light' : 'text-foreground/50 group-hover:text-white'}`}>
      {icon}
    </span>
    <span className="relative z-10 hidden min-w-0 flex-col lg:flex">
      <span className="text-[14px] font-semibold tracking-wide">{label}</span>
      <span className="mt-0.5 max-w-full truncate text-[9px] font-mono uppercase tracking-wider text-foreground/34 group-hover:text-foreground/50">
        {detail}
      </span>
    </span>
  </button>
);
