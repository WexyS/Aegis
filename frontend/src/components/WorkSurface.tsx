"use client";

import React from 'react';
import { Clock3, MessageSquare, Rocket, ShieldCheck } from 'lucide-react';

import { ChatPanel } from '@/features/chat/components/ChatPanel';
import { MissionControlRCPanel } from '@/features/mission-control-rc/components/MissionControlRCPanel';
import { PendingApprovalPanel } from '@/features/runtime/components/PendingApprovalPanel';
import { ScientificTimeline } from '@/features/runtime/components/ScientificTimeline';
import { dictionaryFor } from '@/i18n';
import { useUIStore } from '@/store/useUIStore';

type WorkView = 'control' | 'command' | 'approvals' | 'timeline';

export const WorkSurface = () => {
  const [view, setView] = React.useState<WorkView>('control');
  const language = useUIStore((state) => state.language);
  const t = dictionaryFor(language);
  const views: Array<{ id: WorkView; label: string; detail: string; icon: React.ReactNode }> = [
    { id: 'control', label: t.work.views.control.label, detail: t.work.views.control.detail, icon: <Rocket size={15} /> },
    { id: 'command', label: t.work.views.command.label, detail: t.work.views.command.detail, icon: <MessageSquare size={15} /> },
    { id: 'approvals', label: t.work.views.approvals.label, detail: t.work.views.approvals.detail, icon: <ShieldCheck size={15} /> },
    { id: 'timeline', label: t.work.views.timeline.label, detail: t.work.views.timeline.detail, icon: <Clock3 size={15} /> },
  ];

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="shrink-0 border-b border-white/10 bg-white/[0.025] p-3 sm:p-4">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div className="min-w-0">
            <h1 className="text-xl font-semibold tracking-tight text-white">{t.work.title}</h1>
            <p className="mt-1 text-sm leading-relaxed text-foreground/52">
              {t.work.subtitle}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {views.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => setView(item.id)}
                className={`inline-flex items-center gap-2 rounded-md border px-3 py-2 text-left transition-colors ${view === item.id ? 'border-accent/40 bg-accent/10 text-accent' : 'border-white/10 bg-white/[0.03] text-foreground/55 hover:border-white/20 hover:text-white'}`}
              >
                {item.icon}
                <span className="hidden min-w-0 flex-col sm:flex">
                  <span className="text-[11px] font-semibold">{item.label}</span>
                  <span className="text-[9px] font-mono uppercase tracking-wider opacity-60">{item.detail}</span>
                </span>
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-hidden">
        {view === 'control' && (
          <div className="h-full min-h-0 overflow-y-auto pb-10 custom-scrollbar">
            <MissionControlRCPanel />
          </div>
        )}
        {view === 'command' && <ChatPanel />}
        {view === 'approvals' && (
          <div className="h-full overflow-y-auto p-4 pb-10 sm:p-5 sm:pb-10 lg:p-6 lg:pb-12 custom-scrollbar">
            <div className="mx-auto max-w-3xl">
              <PendingApprovalPanel />
            </div>
          </div>
        )}
        {view === 'timeline' && (
          <div className="h-full overflow-y-auto p-4 pb-10 sm:p-5 sm:pb-10 lg:p-6 lg:pb-12 custom-scrollbar">
            <div className="mx-auto max-w-4xl">
              <ScientificTimeline />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
