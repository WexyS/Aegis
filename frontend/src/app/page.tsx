"use client";

import React from 'react';
import { AppShell } from '@/layouts/AppShell';
import { ChatPanel } from '@/features/chat/components/ChatPanel';
import { ScientificTimeline } from '@/features/runtime/components/ScientificTimeline';
import { useUIStore } from '@/store/useUIStore';
import { useRuntimeStore } from '@/store/useRuntimeStore';
import { Eye, ShieldAlert, Activity, Gauge } from 'lucide-react';
import { motion } from 'framer-motion';

import { AgentGraphPanel } from '@/features/runtime/components/AgentGraphPanel';
import { VisionLabPanel } from '@/features/runtime/components/VisionLabPanel';
import { RuntimeStatsPanel } from '@/features/runtime/components/RuntimeStatsPanel';
import { ChaosShieldPanel } from '@/features/runtime/components/ChaosShieldPanel';
import { PendingApprovalPanel } from '@/features/runtime/components/PendingApprovalPanel';
import { AppRegistryPanel } from '@/features/runtime/components/AppRegistryPanel';
import { ToolRegistryPanel } from '@/features/runtime/components/ToolRegistryPanel';

import { connectRuntime, disconnectRuntime } from '@/lib/socket';
import { getVisionStreamUrl } from '@/lib/api';

export default function AegisDashboard() {
  const { activeTab } = useUIStore();
  const {
    determinismScore,
    recoveryBudget,
    activeApp,
    memoryPercent,
    wsRttMs,
    runtimeIntegrity = 'unverified',
    lastSequenceNum,
    currentState,
  } = useRuntimeStore();
  const memoryPressureLabel = memoryPercent === undefined ? 'Unavailable' : `${memoryPercent.toFixed(1)}%`;
  const memoryPressureWidth = memoryPercent === undefined ? 0 : Math.min(memoryPercent, 100);
  const sequenceLabel = lastSequenceNum === undefined ? 'Unavailable' : lastSequenceNum;
  const rttLabel = wsRttMs === undefined ? 'Unavailable' : `${wsRttMs}ms`;
  const determinismLabel = determinismScore === undefined ? 'Unavailable' : `${(determinismScore * 100).toFixed(1)}%`;
  const visionStreamUrl = getVisionStreamUrl();

  React.useEffect(() => {
    connectRuntime();
    return () => disconnectRuntime();
  }, []);

  return (
    <AppShell>
      <div className="flex-1 flex overflow-hidden p-4 lg:p-5 gap-5 relative z-10">
        {/* CENTER CONTENT */}
        <div className="flex-1 flex flex-col min-w-0 glass-panel rounded-lg overflow-hidden relative">
          {activeTab === 'chat' && <ChatPanel />}
          {activeTab === 'Agent Graph' && <AgentGraphPanel />}
          {activeTab === 'Vision Lab' && <VisionLabPanel />}
          {activeTab === 'Runtime Stats' && <RuntimeStatsPanel />}
          {activeTab === 'Chaos Shield' && <ChaosShieldPanel />}
          {activeTab === 'Applications' && <AppRegistryPanel />}
          {activeTab === 'Tools' && <ToolRegistryPanel />}
          {!['chat', 'Agent Graph', 'Vision Lab', 'Runtime Stats', 'Chaos Shield', 'Applications', 'Tools'].includes(activeTab) && (
            <div className="flex-1 flex items-center justify-center text-[11px] font-mono uppercase tracking-[0.16em] text-foreground/30">
              {activeTab} unavailable
            </div>
          )}
        </div>

        {/* SCIENTIFIC INSPECTOR (Right Panel) */}
        <aside className="hidden xl:flex w-96 flex-col space-y-6 overflow-y-auto custom-scrollbar pr-2">
          {/* SECTION: REAL-TIME METRICS */}
          <section className="space-y-4">
            <h3 className="text-[10px] font-bold uppercase tracking-[0.2em] text-accent flex items-center gap-2">
              <Activity size={12} /> System Telemetry
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <MetricCard 
                label="Determinism" 
                value={determinismLabel}
                context={runtimeIntegrity}
                icon={<Gauge size={14} className="text-accent" />}
              />
              <MetricCard 
                label="Recov. Budget" 
                value={`${(recoveryBudget * 100).toFixed(0)}%`} 
                context={currentState}
                icon={<ShieldAlert size={14} className="text-secondary" />}
              />
            </div>
            <div className="p-4 glass-card rounded-lg space-y-3 relative overflow-hidden group">
              <div className="flex justify-between items-center relative z-10">
                <span className="text-[10px] font-bold text-foreground/50 uppercase tracking-widest">Memory Pressure</span>
                <span className="text-[11px] font-mono font-bold text-accent">{memoryPressureLabel}</span>
              </div>
              <div className="h-1.5 w-full bg-black/40 rounded-full overflow-hidden relative z-10">
                <motion.div 
                  initial={{ width: 0 }}
                  animate={{ width: `${memoryPressureWidth}%` }}
                  transition={{ duration: 1, ease: "easeOut" }}
                  className="h-full bg-accent"
                />
              </div>
              <div className="flex justify-between text-[9px] font-mono text-foreground/35 relative z-10">
                <span>SEQ {sequenceLabel}</span>
                <span>{runtimeIntegrity.toUpperCase()} / RTT {rttLabel}</span>
              </div>
            </div>
          </section>

          <PendingApprovalPanel />

          {/* SECTION: SCIENTIFIC TIMELINE */}
          <ScientificTimeline />

          {/* SECTION: VISION CONTEXT */}
          <section className="space-y-4">
            <h3 className="text-[10px] font-bold uppercase tracking-[0.2em] text-accent flex items-center gap-2">
              <Eye size={12} /> Vision Context
            </h3>
            <div className="aspect-video rounded-lg bg-black/30 border border-white/10 flex flex-col items-center justify-center overflow-hidden relative group">
              <img 
                src={visionStreamUrl}
                alt="Live Vision Feed" 
                className="absolute inset-0 w-full h-full object-cover opacity-60 group-hover:opacity-100 transition-opacity duration-500 mix-blend-screen"
                onError={(e) => {
                  e.currentTarget.style.display = 'none';
                  const fallback = e.currentTarget.parentElement?.querySelector('.fallback');
                  if (fallback) fallback.classList.remove('hidden');
                }}
              />
              <div className="fallback hidden flex-col items-center justify-center z-10">
                <Eye className="text-foreground/15" size={24} />
                <div className="mt-3 text-[9px] font-mono text-foreground/30 uppercase tracking-widest">
                  Feed Offline
                </div>
              </div>
            </div>
            <div className="flex justify-between items-center px-2">
              <span className="text-[10px] font-mono text-foreground/50"><span className="text-foreground/30">Focus:</span> {activeApp}</span>
              <span className="text-[10px] font-mono text-foreground/40 font-bold">FOCUS FROM TELEMETRY</span>
            </div>
          </section>
        </aside>
      </div>
    </AppShell>
  );
}

type MetricCardProps = {
  label: string;
  value: string;
  context: string;
  icon: React.ReactNode;
};

const MetricCard = React.memo(({ label, value, context, icon }: MetricCardProps) => (
  <div className="p-4 glass-card rounded-lg space-y-2 hover:border-accent/30 transition-all cursor-default group relative overflow-hidden">
    <div className="flex items-center justify-between text-foreground/45 group-hover:text-foreground/80 transition-colors">
      {icon}
      <span className="max-w-[110px] truncate text-[9px] font-bold uppercase tracking-widest text-foreground/45">{context}</span>
    </div>
    <div className="relative z-10">
      <p className="text-[10px] font-bold text-foreground/50 uppercase tracking-widest">{label}</p>
      <p className="text-2xl font-bold text-white mt-1">{value}</p>
    </div>
  </div>
));

MetricCard.displayName = 'MetricCard';
