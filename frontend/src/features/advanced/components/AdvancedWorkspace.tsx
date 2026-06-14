"use client";

import React from 'react';
import {
  Activity,
  Database,
  Eye,
  FlaskConical,
  GitBranch,
  LayoutDashboard,
  MonitorUp,
  ShieldAlert,
  Terminal,
  Wrench,
} from 'lucide-react';

import { RuntimeConsole } from '@/components/RuntimeConsole';
import { AgentGraphPanel } from '@/features/runtime/components/AgentGraphPanel';
import { AppRegistryPanel } from '@/features/runtime/components/AppRegistryPanel';
import { ChaosShieldPanel } from '@/features/runtime/components/ChaosShieldPanel';
import { MaintenanceScanPanel } from '@/features/runtime/components/MaintenanceScanPanel';
import { RuntimeStatsPanel } from '@/features/runtime/components/RuntimeStatsPanel';
import { ScientificTimeline } from '@/features/runtime/components/ScientificTimeline';
import { ToolRegistryPanel } from '@/features/runtime/components/ToolRegistryPanel';
import { VisionLabPanel } from '@/features/runtime/components/VisionLabPanel';
import { dictionaryFor } from '@/i18n';
import { useUIStore } from '@/store/useUIStore';

type AdvancedView =
  | 'maintenance'
  | 'runtime'
  | 'tools'
  | 'apps'
  | 'agent'
  | 'vision'
  | 'chaos'
  | 'timeline'
  | 'console';

export const AdvancedWorkspace = () => {
  const [view, setView] = React.useState<AdvancedView>('maintenance');
  const language = useUIStore((state) => state.language);
  const t = dictionaryFor(language);
  const views: Array<{ id: AdvancedView; label: string; detail: string; icon: React.ReactNode }> = [
    { id: 'maintenance', label: t.advanced.views.maintenance.label, detail: t.advanced.views.maintenance.detail, icon: <Wrench size={15} /> },
    { id: 'runtime', label: t.advanced.views.runtime.label, detail: t.advanced.views.runtime.detail, icon: <Activity size={15} /> },
    { id: 'tools', label: t.advanced.views.tools.label, detail: t.advanced.views.tools.detail, icon: <Database size={15} /> },
    { id: 'apps', label: t.advanced.views.apps.label, detail: t.advanced.views.apps.detail, icon: <MonitorUp size={15} /> },
    { id: 'agent', label: t.advanced.views.agent.label, detail: t.advanced.views.agent.detail, icon: <GitBranch size={15} /> },
    { id: 'vision', label: t.advanced.views.vision.label, detail: t.advanced.views.vision.detail, icon: <Eye size={15} /> },
    { id: 'chaos', label: t.advanced.views.chaos.label, detail: t.advanced.views.chaos.detail, icon: <ShieldAlert size={15} /> },
    { id: 'timeline', label: t.advanced.views.timeline.label, detail: t.advanced.views.timeline.detail, icon: <FlaskConical size={15} /> },
    { id: 'console', label: t.advanced.views.console.label, detail: t.advanced.views.console.detail, icon: <Terminal size={15} /> },
  ];

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="shrink-0 border-b border-white/10 bg-white/[0.025] p-3 sm:p-4">
        <div className="flex flex-col gap-4 2xl:flex-row 2xl:items-end 2xl:justify-between">
          <div className="min-w-0 max-w-4xl">
            <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.18em] text-accent">
              <LayoutDashboard size={15} />
              {t.advanced.eyebrow}
            </div>
            <h1 className="mt-2 text-xl font-semibold tracking-tight text-white">{t.advanced.title}</h1>
            <p className="mt-1 text-sm leading-relaxed text-foreground/52">
              {t.advanced.subtitle}
            </p>
          </div>
          <div className="flex max-w-full gap-2 overflow-x-auto pb-1 custom-scrollbar">
            {views.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => setView(item.id)}
                className={`flex min-w-[11rem] items-start gap-2 rounded-md border px-3 py-2 text-left transition-colors ${view === item.id ? 'border-accent/40 bg-accent/10 text-accent' : 'border-white/10 bg-white/[0.03] text-foreground/52 hover:border-white/20 hover:text-white'}`}
              >
                <span className="mt-0.5 shrink-0">{item.icon}</span>
                <span className="min-w-0">
                  <span className="block truncate text-[11px] font-semibold">{item.label}</span>
                  <span className="block truncate text-[9px] font-mono uppercase tracking-wider opacity-60">{item.detail}</span>
                </span>
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-hidden">
        {view === 'maintenance' && <AdvancedScroll><MaintenanceScanPanel /></AdvancedScroll>}
        {view === 'runtime' && <RuntimeStatsPanel />}
        {view === 'tools' && <ToolRegistryPanel />}
        {view === 'apps' && <AppRegistryPanel />}
        {view === 'agent' && <AgentGraphPanel />}
        {view === 'vision' && <VisionLabPanel />}
        {view === 'chaos' && <ChaosShieldPanel />}
        {view === 'timeline' && <AdvancedScroll><ScientificTimeline /></AdvancedScroll>}
        {view === 'console' && (
          <div className="flex h-full min-h-0 flex-col p-4 sm:p-5 lg:p-6">
            <RuntimeConsole />
          </div>
        )}
      </div>
    </div>
  );
};

const AdvancedScroll = ({ children }: { children: React.ReactNode }) => (
  <div className="h-full min-h-0 overflow-y-auto p-4 pb-10 sm:p-5 sm:pb-10 lg:p-6 lg:pb-12 custom-scrollbar">
    <div className="mx-auto max-w-5xl">{children}</div>
  </div>
);
