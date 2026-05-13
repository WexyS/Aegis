"use client";

import React from 'react';
import { useRuntimeStore } from '@/store/useRuntimeStore';
import { motion } from 'framer-motion';
import { ExecutionEvidence, RuntimeComponent, RuntimeStatus } from '@/types/runtime';

export const ScientificTimeline = () => {
  const { steps } = useRuntimeStore();

  return (
    <div className="space-y-4 p-4 glass-card rounded-lg relative overflow-hidden flex flex-col min-h-[280px]">
      <div className="flex justify-between items-center relative z-10">
        <h3 className="text-[10px] font-bold uppercase tracking-[0.2em] text-accent">Execution Timeline</h3>
        <span className="text-[9px] font-mono text-foreground/40">{steps.length} steps</span>
      </div>
      <div className="relative space-y-4 pt-2 flex-1 overflow-y-auto custom-scrollbar pr-2">
        {/* Connection Line */}
        <div className="absolute left-[7px] top-4 bottom-4 w-px bg-white/10" />
        
        {steps.slice(-20).map((step) => (
          <TimelineItem key={step.id} step={step} />
        ))}
      </div>
    </div>
  );
};

const TimelineItem = React.memo(({ step }: { step: any }) => {
  const statusColors = {
    [RuntimeStatus.SUCCESS]: 'bg-success',
    [RuntimeStatus.ACTIVE]: 'bg-accent',
    [RuntimeStatus.ERROR]: 'bg-danger',
    [RuntimeStatus.PENDING]: 'bg-surface-secondary',
  };

  return (
    <motion.div 
      initial={{ opacity: 0, x: -15 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.16 }}
      className="flex items-start gap-5 relative z-10 group"
    >
      <div className={`mt-2 w-4 h-4 rounded-full border-2 border-background flex items-center justify-center bg-surface relative z-10`}>
        <div className={`w-2 h-2 rounded-full ${statusColors[step.status as RuntimeStatus]}`} />
      </div>
      <div className="flex-1 bg-black/20 hover:bg-black/35 p-3 rounded-md border border-white/10 hover:border-accent/30 transition-colors duration-150 relative overflow-hidden">
        <div className="flex justify-between items-center mb-1.5 relative z-10">
          <span className="text-[11px] font-bold text-white uppercase tracking-wider">{step.component}</span>
          <span className="text-[9px] font-mono text-foreground/40">{step.timestamp}</span>
        </div>
        <p className="text-[13px] text-foreground/70 leading-relaxed font-medium relative z-10">{step.detail}</p>
        
        {step.metrics && (
          <div className="mt-3 flex gap-4 border-t border-white/10 pt-3 relative z-10">
            <Metric label="DET" value={step.metrics.determinism} />
            <Metric label="LAT" value={`${step.metrics.latency_ms}ms`} />
          </div>
        )}
        {step.executionEvidence && <EvidenceSummary evidence={step.executionEvidence} />}
      </div>
    </motion.div>
  );
});

const EvidenceSummary = ({ evidence }: { evidence: ExecutionEvidence }) => {
  const isVerified = evidence.verification_state === 'verified';
  const pidText = evidence.pids?.length ? `PID ${evidence.pids.slice(0, 2).join(', ')}` : 'no pid';
  const windowTitle = typeof evidence.window?.title === 'string' ? evidence.window.title : '';

  return (
    <div className="mt-3 rounded-md border border-white/10 bg-white/[0.02] p-2 relative z-10">
      <div className="flex items-center justify-between gap-2">
        <span className={`text-[9px] font-bold uppercase tracking-widest ${isVerified ? 'text-success' : 'text-warning'}`}>
          {evidence.verification_state}
        </span>
        <span className="text-[9px] font-mono text-foreground/40">{evidence.method}</span>
      </div>
      <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-[9px] font-mono text-foreground/45">
        {evidence.process_name && <span>{evidence.process_name}</span>}
        <span>{pidText}</span>
        {evidence.retry_count > 0 && <span>Retries {evidence.retry_count}</span>}
        {evidence.fallback_chain?.length > 0 && <span>Fallback {evidence.fallback_chain.length}</span>}
        {windowTitle && <span className="truncate max-w-full">{windowTitle}</span>}
      </div>
      {evidence.warnings?.[0] && (
        <p className="mt-1 text-[9px] font-mono leading-relaxed text-warning/80">{evidence.warnings[0]}</p>
      )}
    </div>
  );
};

const Metric = ({ label, value }: any) => (
  <div className="flex items-center gap-2">
    <span className="text-[9px] font-bold text-foreground/40">{label}:</span>
    <span className="text-[10px] font-mono font-bold text-accent">{value}</span>
  </div>
);
