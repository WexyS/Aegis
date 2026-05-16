"use client";

import React from 'react';
import { Activity, Cpu, Radio } from 'lucide-react';
import { useRuntimeStore } from '@/store/useRuntimeStore';

export const Header = () => {
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
    <header className="h-14 border-b border-white/10 flex items-center justify-between px-5 bg-background/85 backdrop-blur-md z-40">
      <div className="flex items-center gap-4 min-w-0">
        <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.12em] text-foreground/85">
          <Activity size={14} className="text-accent" />
          <span>Aegis Runtime</span>
        </div>
        <div className="hidden md:flex items-center gap-2 text-[10px] font-mono text-foreground/45">
          <span>FSM {currentState}</span>
          <span className="text-foreground/20">/</span>
          <span>SEQ {sequenceLabel}</span>
          <span className="text-foreground/20">/</span>
          <span>{runtimeIntegrity}</span>
        </div>
      </div>
      
      <div className="flex items-center gap-3">
        <div className="hidden md:flex items-center gap-2 rounded-md border border-white/10 bg-white/[0.03] px-3 py-1.5 text-[10px] font-mono">
          <span className={`h-2 w-2 rounded-full ${isConnected ? 'bg-success' : 'bg-warning'}`} />
          <span className="text-foreground/45">SOCKET</span>
          <span className="font-bold text-foreground/80">{connectionState.toUpperCase()}</span>
        </div>
        <div className="flex items-center gap-2 rounded-md border border-white/10 bg-white/[0.03] px-3 py-1.5 text-[10px] font-mono">
          <Cpu size={13} className="text-accent" />
          <span className="hidden sm:inline text-foreground/45">MODEL</span>
          <span className="max-w-[180px] truncate font-bold text-foreground/80">{activeModel || 'Unavailable'}</span>
        </div>
        <div className="hidden lg:flex items-center gap-2 rounded-md border border-white/10 bg-white/[0.03] px-3 py-1.5 text-[10px] font-mono text-foreground/60">
          <Radio size={13} className="text-foreground/40" />
          backend authority
        </div>
      </div>
    </header>
  );
};
