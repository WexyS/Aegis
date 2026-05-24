import React from 'react';
import { Network, Cpu, Database, Activity, GitBranch, ShieldCheck, AlertTriangle, RotateCcw, CheckCircle2 } from 'lucide-react';
import { EmptyState } from '@/components/EmptyState';
import { StatusBadge } from '@/components/StatusBadge';
import { useRuntimeStore } from '@/store/useRuntimeStore';
import { RuntimeState } from '@/types/fsm';

export const AgentGraphPanel = () => {
  const { currentState, steps } = useRuntimeStore();
  const latestSteps = steps.slice(-12);
  const states = [
    { label: RuntimeState.IDLE, icon: <Cpu size={16} />, hint: 'ready' },
    { label: RuntimeState.THINKING, icon: <Activity size={16} />, hint: 'intent' },
    { label: RuntimeState.PLANNING, icon: <GitBranch size={16} />, hint: 'plan' },
    { label: RuntimeState.EXECUTING, icon: <Database size={16} />, hint: 'tool' },
    { label: RuntimeState.VERIFYING, icon: <ShieldCheck size={16} />, hint: 'proof' },
    { label: RuntimeState.RECOVERING, icon: <RotateCcw size={16} />, hint: 'repair' },
    { label: RuntimeState.COMPLETED, icon: <CheckCircle2 size={16} />, hint: 'done' },
    { label: RuntimeState.FAILED, icon: <AlertTriangle size={16} />, hint: 'halt' },
  ];

  return (
    <div className="flex-1 p-5 lg:p-6 space-y-6 overflow-y-auto custom-scrollbar relative flex flex-col">
      <div className="flex items-center gap-4 border-b border-white/5 pb-6">
        <div className="p-3 bg-violet-500/10 rounded-lg border border-violet-500/30">
          <Network className="text-violet-300" size={24} />
        </div>
        <div>
          <h2 className="text-lg font-bold tracking-widest text-white uppercase">Agent Graph</h2>
          <p className="text-xs text-foreground/40 font-mono">Topological Plan & State Visualization</p>
        </div>
      </div>

      <div className="flex-1 glass-panel rounded-lg border border-white/10 relative overflow-hidden flex flex-col p-5">
        <div className="flex items-center justify-between mb-8">
          <h3 className="text-[11px] font-bold text-foreground/50 tracking-widest uppercase flex items-center gap-2">
            <GitBranch size={14} /> FSM Topology
          </h3>
          <StatusBadge label={`CURRENT: ${currentState ?? 'unknown'}`} tone={currentState === RuntimeState.FAILED ? 'danger' : currentState === RuntimeState.IDLE ? 'info' : 'warning'} />
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {states.map((state) => (
            <GraphNode
              key={state.label}
              label={state.label}
              hint={state.hint}
              icon={state.icon}
              active={currentState === state.label}
            />
          ))}
        </div>

        <div className="mt-6 p-4 bg-black/35 rounded-lg border border-white/10">
          <div className="text-[10px] font-mono text-foreground/40 mb-2 uppercase">Execution Trace Projection</div>
          <div className="space-y-2">
            {latestSteps.length === 0 ? (
              <EmptyState title="No backend steps recorded" detail="Execution trace appears only after backend action timeline events or snapshots arrive." />
            ) : (
              latestSteps.map(step => (
                <div key={step.id} className="flex items-center justify-between text-[11px]">
                  <span className="truncate pr-4 text-white font-medium">{step.label}</span>
                  <span className={`font-mono ${step.status === 'success' ? 'text-emerald-400' : step.status === 'error' ? 'text-red-400' : step.status === 'active' ? 'text-accent' : 'text-foreground/45'}`}>{step.status.toUpperCase()}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

const GraphNode = ({ label, hint, icon, active }: any) => (
  <div
    className={`min-h-24 rounded-lg flex flex-col items-start justify-between gap-4 border p-4 transition-colors ${active ? 'bg-violet-500/15 border-violet-400/60 text-violet-200' : 'bg-black/35 border-white/10 text-foreground/45'}`}
  >
    <div className="flex w-full items-center justify-between">
      {icon}
      <span className="text-[9px] font-mono uppercase tracking-widest text-foreground/35">{hint}</span>
    </div>
    <span className="text-[11px] font-bold tracking-widest">{label}</span>
  </div>
);
