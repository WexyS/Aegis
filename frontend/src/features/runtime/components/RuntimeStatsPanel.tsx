import React from 'react';
import { BarChart3, HardDrive, Cpu, MemoryStick, Clock, Radio } from 'lucide-react';
import { useRuntimeStore } from '@/store/useRuntimeStore';
import { motion } from 'framer-motion';

export const RuntimeStatsPanel = () => {
  const { determinismScore, recoveryBudget, cpuPercent, memoryPercent, uptimeSeconds, ioThroughput, eventThroughput, websocketClients, wsRttMs } = useRuntimeStore();

  const formatPercent = (value?: number) => value === undefined ? 'Unavailable' : `${value.toFixed(1)}%`;
  const formatCount = (value?: number) => value === undefined ? 'Unavailable' : `${value}`;
  const formatUptime = (seconds?: number) => {
    if (seconds === undefined) return 'Unavailable';
    const h = Math.floor(seconds / 3600).toString().padStart(2, '0');
    const m = Math.floor((seconds % 3600) / 60).toString().padStart(2, '0');
    const s = Math.floor(seconds % 60).toString().padStart(2, '0');
    return `${h}:${m}:${s}`;
  };

  const metrics = [
    { label: "Memory Pressure", value: formatPercent(memoryPercent), icon: <MemoryStick size={16} />, color: "text-blue-300", bg: "bg-blue-500/10", border: "border-blue-500/25" },
    { label: "CPU Load", value: formatPercent(cpuPercent), icon: <Cpu size={16} />, color: "text-emerald-300", bg: "bg-emerald-500/10", border: "border-emerald-500/25" },
    { label: "Storage I/O", value: ioThroughput ?? 'Unavailable', icon: <HardDrive size={16} />, color: "text-violet-300", bg: "bg-violet-500/10", border: "border-violet-500/25" },
    { label: "Uptime", value: formatUptime(uptimeSeconds), icon: <Clock size={16} />, color: "text-accent", bg: "bg-accent/10", border: "border-accent/25" },
    { label: "WS Clients", value: formatCount(websocketClients), icon: <Radio size={16} />, color: "text-cyan-300", bg: "bg-cyan-500/10", border: "border-cyan-500/25" },
  ];
  const rttValue = wsRttMs === undefined ? undefined : Math.min(wsRttMs, 1000) / 10;
  const throughputValue = eventThroughput ?? 0;

  return (
    <div className="flex-1 p-5 lg:p-6 space-y-6 overflow-y-auto custom-scrollbar relative">
      <div className="flex items-center gap-4 border-b border-white/5 pb-6">
        <div className="p-3 bg-blue-500/10 rounded-lg border border-blue-500/30">
          <BarChart3 className="text-blue-400" size={24} />
        </div>
        <div>
          <h2 className="text-lg font-bold tracking-widest text-white uppercase">Runtime Stats</h2>
          <p className="text-xs text-foreground/40 font-mono">Performance & Infrastructure Metrics</p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-4">
        {metrics.map((m, i) => (
          <div key={i} className={`p-4 rounded-lg border ${m.border} ${m.bg} flex flex-col gap-3 min-w-0`}>
            <div className={`flex items-center gap-2 ${m.color}`}>
              {m.icon}
              <span className="text-[10px] font-bold uppercase tracking-widest">{m.label}</span>
            </div>
            <div className="text-2xl font-bold text-white">{m.value}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 2xl:grid-cols-2 gap-4">
        <section className="glass-panel p-5 rounded-lg space-y-6">
          <h3 className="text-[11px] font-bold text-foreground/50 tracking-widest uppercase">System Stability</h3>
          <div className="space-y-4">
            <ProgressBar label="Determinism Score" value={determinismScore === undefined ? undefined : determinismScore * 100} color="bg-success" />
            <ProgressBar label="Recovery Budget" value={recoveryBudget * 100} color="bg-secondary" />
            <ProgressBar label="WebSocket RTT" value={rttValue} color="bg-accent" displayValue={wsRttMs === undefined ? 'Unavailable' : `${wsRttMs}ms`} />
          </div>
        </section>

        <section className="glass-panel p-5 rounded-lg space-y-4 flex flex-col">
          <h3 className="text-[11px] font-bold text-foreground/50 tracking-widest uppercase">Event Throughput</h3>
          <div className="flex-1 flex flex-col justify-center gap-3 pt-4">
            <div className="text-5xl font-bold text-white tracking-tight">{eventThroughput === undefined ? 'Unavailable' : eventThroughput}</div>
            <div className="text-[10px] uppercase tracking-widest text-foreground/40">backend events / sec</div>
            <div className="h-2 bg-black/40 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${Math.min(throughputValue, 100)}%` }}
                className="h-full bg-accent"
              />
            </div>
          </div>
          <div className="flex justify-between text-[9px] font-mono text-foreground/30 border-t border-white/5 pt-2">
            <span>-60s</span>
            <span>Now</span>
          </div>
        </section>
      </div>
    </div>
  );
};

const ProgressBar = ({ label, value, color, displayValue }: { label: string; value?: number; color: string; displayValue?: string }) => (
  <div>
    <div className="flex justify-between text-[10px] font-bold uppercase tracking-widest mb-2 text-foreground/60">
      <span>{label}</span>
      <span className="text-white">{displayValue ?? (value === undefined ? 'Unavailable' : `${value.toFixed(1)}%`)}</span>
    </div>
    <div className="h-1.5 bg-black/40 rounded-full overflow-hidden">
      <motion.div 
        initial={{ width: 0 }}
        animate={{ width: `${value === undefined ? 0 : Math.min(Math.max(value, 0), 100)}%` }}
        className={`h-full ${color}`}
      />
    </div>
  </div>
);
