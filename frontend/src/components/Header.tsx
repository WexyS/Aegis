"use client";

import React from 'react';
import { Activity, Cpu, Radio, ShieldCheck } from 'lucide-react';
import { StatusBadge } from '@/components/StatusBadge';
import { useUIStore } from '@/store/useUIStore';
import { useRuntimeStore } from '@/store/useRuntimeStore';

export const Header = () => {
  const activeTab = useUIStore((state) => state.activeTab);
  const {
    activeModel,
    connectionState = 'disconnected',
    currentState,
    lastSequenceNum,
    runtimeIntegrity = 'unverified',
  } = useRuntimeStore();
  const isConnected = connectionState === 'connected';
  const sequenceLabel = lastSequenceNum === undefined ? 'Unavailable' : lastSequenceNum;

  return (
    <header className="h-16 shrink-0 border-b border-white/10 flex items-center justify-between gap-3 px-3 sm:px-4 lg:px-6 bg-background/72 backdrop-blur-xl z-40">
      <div className="flex items-center gap-4 min-w-0">
        <div className="flex items-center gap-3 min-w-0">
          <div className="hidden h-8 w-8 shrink-0 items-center justify-center rounded-md border border-accent/25 bg-accent/10 text-accent sm:flex">
            <ShieldCheck size={15} />
          </div>
          <div className="min-w-0">
            <div className="truncate text-sm font-semibold text-white">{activeTab}</div>
            <div className="hidden text-[10px] font-mono uppercase tracking-wider text-foreground/35 sm:block">
              backend-owned truth, presentation-only UI
            </div>
          </div>
          <StatusBadge label={compactIntegrityLabel(runtimeIntegrity)} tone={integrityTone(runtimeIntegrity)} className="sm:hidden" />
        </div>
        <div className="hidden md:flex items-center gap-2 text-[10px] font-mono text-foreground/45">
          <Activity size={12} className="text-accent" />
          <span>FSM {currentState}</span>
          <span className="text-foreground/20">/</span>
          <span>SEQ {sequenceLabel}</span>
          <span className="text-foreground/20">/</span>
          <span>{runtimeIntegrity}</span>
        </div>
      </div>
      
      <div className="flex min-w-0 items-center justify-end gap-2 lg:gap-3">
        <div className="hidden md:flex items-center gap-2 rounded-md border border-white/10 bg-white/[0.03] px-3 py-1.5 text-[10px] font-mono">
          <span className={`h-2 w-2 rounded-full ${isConnected ? 'bg-success' : 'bg-warning'}`} />
          <span className="text-foreground/45">SOCKET</span>
          <span className="font-bold text-foreground/80">{connectionState.toUpperCase()}</span>
        </div>
        <StatusBadge label={runtimeIntegrity} tone={integrityTone(runtimeIntegrity)} className="hidden sm:inline-flex" />
        <div className="hidden min-w-0 items-center gap-2 rounded-md border border-white/10 bg-white/[0.03] px-2.5 py-1.5 text-[10px] font-mono sm:flex lg:px-3">
          <Cpu size={13} className="text-accent" />
          <span className="hidden lg:inline text-foreground/45">MODEL CONFIG</span>
          <span className="max-w-[120px] truncate font-bold text-foreground/80 xl:max-w-[180px]">{activeModel || 'Unavailable'}</span>
        </div>
        <div className="hidden lg:flex items-center gap-2 rounded-md border border-white/10 bg-white/[0.03] px-3 py-1.5 text-[10px] font-mono text-foreground/60">
          <Radio size={13} className="text-foreground/40" />
          backend authority
        </div>
      </div>
    </header>
  );
};

function integrityTone(integrity: string): 'info' | 'warning' | 'unknown' {
  if (integrity === 'unverified' || integrity === 'resyncing') return 'warning';
  if (integrity === 'session-reset') return 'unknown';
  return 'info';
}

function compactIntegrityLabel(integrity: string): string {
  if (integrity === 'unverified') return 'unver.';
  return integrity;
}
