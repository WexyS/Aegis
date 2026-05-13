import React from 'react';
import { ShieldAlert, Power, AlertTriangle, RefreshCcw, Activity } from 'lucide-react';
import { sendCommand } from '@/lib/socket';
import { useRuntimeStore } from '@/store/useRuntimeStore';

export const ChaosShieldPanel = () => {
  const connectionState = useRuntimeStore((state) => state.connectionState ?? 'disconnected');
  const isConnected = connectionState === 'connected';

  const handleEmergencyStop = () => {
    // A raw command to the backend to force idle
    sendCommand("/force_idle", "raw");
  };

  const handleResetMemory = () => {
    sendCommand("/reset_memory", "raw");
  };

  return (
    <div className="flex-1 p-5 lg:p-6 space-y-6 overflow-y-auto custom-scrollbar relative">
      <div className="flex items-center gap-4 border-b border-white/5 pb-6">
        <div className="p-3 bg-red-500/10 rounded-lg border border-red-500/30">
          <ShieldAlert className="text-red-500" size={24} />
        </div>
        <div>
          <h2 className="text-lg font-bold tracking-widest text-white uppercase">Chaos Shield</h2>
          <p className="text-xs text-foreground/40 font-mono">Execution Guardrails & Anomaly Management</p>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
        {/* Guardrail Policy */}
        <section className="glass-panel p-5 rounded-lg space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-[11px] font-bold text-accent tracking-widest uppercase">Global Policy</h3>
            <span className="px-3 py-1 rounded-md text-[9px] font-bold tracking-widest border bg-emerald-500/10 text-emerald-400 border-emerald-500/30">
              BACKEND AUTHORITY
            </span>
          </div>
          
          <div className="space-y-3">
            <div className="w-full text-left p-4 rounded-lg border bg-white/5 border-white/10">
              <div className="text-sm font-bold text-white mb-1">Runtime Guardrails</div>
              <div className="text-[10px] text-foreground/50">Policy state is emitted by backend guard events. Local UI overrides are disabled.</div>
            </div>
          </div>
        </section>

        {/* Emergency Controls */}
        <section className="glass-panel p-5 rounded-lg space-y-6">
          <h3 className="text-[11px] font-bold text-red-400 tracking-widest uppercase">System Override</h3>
          
          <div className="space-y-4">
            <button 
              onClick={handleEmergencyStop}
              disabled={!isConnected}
              className="w-full flex items-center justify-between p-4 rounded-lg bg-red-500/10 border border-red-500/30 hover:bg-red-500/20 transition-colors group disabled:cursor-not-allowed disabled:opacity-45"
            >
              <div className="flex items-center gap-3">
                <Power className="text-red-400 group-hover:scale-110 transition-transform" size={18} />
                <span className="text-sm font-bold text-red-100 uppercase tracking-wider">Emergency Halt</span>
              </div>
              <span className="text-[10px] text-red-500/50 font-mono">RAW CONTROL</span>
            </button>

            <button 
              onClick={handleResetMemory}
              disabled={!isConnected}
              className="w-full flex items-center justify-between p-4 rounded-lg bg-yellow-500/5 border border-yellow-500/20 hover:bg-yellow-500/10 transition-colors group disabled:cursor-not-allowed disabled:opacity-45"
            >
              <div className="flex items-center gap-3">
                <RefreshCcw className="text-yellow-400 group-hover:rotate-180 transition-transform duration-500" size={18} />
                <span className="text-sm font-bold text-yellow-100 uppercase tracking-wider">Flush Memory Buffers</span>
              </div>
              <span className="text-[10px] text-yellow-500/50 font-mono">RAW CONTROL</span>
            </button>
            
            <div className="p-4 rounded-lg bg-black/40 border border-white/10 flex gap-4 items-start">
              <AlertTriangle className="text-foreground/40 shrink-0 mt-0.5" size={14} />
              <p className="text-[10px] text-foreground/40 leading-relaxed">
                Emergency Halt sends a raw backend control command. The UI only changes state after the backend emits authoritative FSM events. Socket: {connectionState}.
              </p>
            </div>
          </div>
        </section>
      </div>

      {/* Watchdog Status */}
      <section className="glass-panel p-5 rounded-lg">
        <div className="flex items-center gap-3 mb-6">
          <Activity size={16} className="text-accent" />
          <h3 className="text-[11px] font-bold text-accent tracking-widest uppercase">Resource Watchdog</h3>
        </div>
        <div className="grid grid-cols-4 gap-4">
          <WatchdogStat label="Active Contexts" value="Unavailable" />
          <WatchdogStat label="Leaked Handles" value="Unavailable" />
          <WatchdogStat label="Forced Cleanups" value="Unavailable" />
          <WatchdogStat label="Avg Lifetime" value="Unavailable" />
        </div>
      </section>
    </div>
  );
};

const WatchdogStat = ({ label, value }: any) => (
  <div className="p-4 bg-black/20 rounded-lg border border-white/10 min-w-0">
    <div className="text-[9px] text-foreground/40 uppercase tracking-widest mb-2">{label}</div>
    <div className="flex items-baseline gap-2 min-w-0">
      <span className="truncate text-sm font-bold text-white">{value}</span>
    </div>
  </div>
);
