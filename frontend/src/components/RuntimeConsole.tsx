"use client";

import React, { useEffect, useRef } from 'react';
import { Terminal as TerminalIcon, ShieldCheck, AlertTriangle, Activity } from 'lucide-react';

import { StatusBadge } from '@/components/StatusBadge';
import { useRuntimeStore } from '@/store/useRuntimeStore';

export const RuntimeConsole = () => {
  const { systemLogs, currentState, runtimeIntegrity = 'unverified' } = useRuntimeStore();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [systemLogs.length]);

  return (
    <div className="h-56 border-t border-white/10 bg-background/95 backdrop-blur-2xl flex flex-col relative z-20">
      <div className="h-9 border-b border-white/10 flex items-center justify-between px-5 bg-surface-secondary/60">
        <div className="flex items-center gap-3">
          <TerminalIcon size={14} className="text-accent" />
          <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-foreground/80">Runtime Daemon</span>
        </div>
        <div className="flex items-center gap-5 text-[10px] font-mono text-foreground/40">
          <StatusBadge
            label={runtimeIntegrity}
            tone={integrityTone(runtimeIntegrity)}
            icon={integrityTone(runtimeIntegrity) === 'warning' ? <AlertTriangle size={10} /> : <ShieldCheck size={10} />}
          />
          <StatusBadge label={currentState ?? 'unknown'} tone={stateTone(currentState)} icon={<AlertTriangle size={10} />} />
        </div>
      </div>
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 font-mono text-[11px] space-y-1 custom-scrollbar bg-[#010308] shadow-inner">
        <div className="space-y-1">
          {systemLogs.length === 0 ? (
            <div className="text-foreground/30 py-4 px-2 italic">Awaiting telemetry...</div>
          ) : (
            systemLogs.map(log => (
              <LogLine 
                key={log.id} 
                time={log.timestamp} 
                level={log.level} 
                msg={log.message} 
                color={log.color} 
                duration={log.duration} 
              />
            ))
          )}
        </div>
      </div>
    </div>
  );
};

const LogLine = ({ time, level, msg, color = "text-foreground/50", duration, badge }: any) => (
  <div className="flex gap-4 hover:bg-white/[0.03] px-2 py-1 rounded transition-colors items-start">
    <span className="text-foreground/30 opacity-70 w-20 shrink-0">[{time}]</span>
    <span className={`font-bold w-12 shrink-0 ${color}`}>{level}</span>
    <div className="flex-1 flex flex-col gap-1">
      <span className="text-foreground/80 tracking-wide leading-relaxed">{msg}</span>
      {badge && (
        <span className="inline-flex items-center gap-1 text-[9px] px-1.5 py-0.5 rounded bg-accent/10 border border-accent/20 text-accent-light w-max">
          <Activity size={8} /> {badge}
        </span>
      )}
    </div>
    {duration && <span className="text-foreground/30 opacity-70 text-[9px]">{duration}</span>}
  </div>
);

function integrityTone(integrity: string): 'info' | 'warning' | 'unknown' {
  if (integrity === 'unverified' || integrity === 'resyncing') return 'warning';
  if (integrity === 'session-reset') return 'unknown';
  return 'info';
}

function stateTone(state: string | undefined): 'info' | 'warning' | 'danger' | 'unknown' {
  if (!state) return 'unknown';
  if (state === 'FAILED') return 'danger';
  if (state === 'IDLE' || state === 'COMPLETED') return 'info';
  return 'warning';
}
