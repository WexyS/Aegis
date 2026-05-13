import React, { useState } from 'react';
import { Eye, Focus, ScanLine, Maximize, Play, Square } from 'lucide-react';
import { useRuntimeStore } from '@/store/useRuntimeStore';

export const VisionLabPanel = () => {
  const [isScanning, setIsScanning] = useState(true);
  const [feedFailed, setFeedFailed] = useState(false);
  const { activeApp } = useRuntimeStore();

  const toggleFeed = () => {
    setIsScanning((value) => {
      const next = !value;
      if (next) setFeedFailed(false);
      return next;
    });
  };

  return (
    <div className="flex-1 p-5 lg:p-6 space-y-6 overflow-y-auto custom-scrollbar relative flex flex-col">
      <div className="flex items-center gap-4 border-b border-white/5 pb-6">
        <div className="p-3 bg-emerald-500/10 rounded-lg border border-emerald-500/30">
          <Eye className="text-emerald-400" size={24} />
        </div>
        <div className="flex-1">
          <h2 className="text-lg font-bold tracking-widest text-white uppercase">Vision Lab</h2>
          <p className="text-xs text-foreground/40 font-mono">Semantic Screen Analysis & Anchors</p>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={toggleFeed}
            className={`p-2 rounded-md border flex items-center gap-2 transition-colors ${isScanning ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-300' : 'bg-white/5 border-white/10 text-foreground/50 hover:bg-white/10'}`}
          >
            {isScanning ? <Square size={14} className="fill-current" /> : <Play size={14} className="fill-current" />}
            <span className="text-[10px] font-bold uppercase tracking-widest">{isScanning ? 'Stop Feed' : 'Start Feed'}</span>
          </button>
        </div>
      </div>

      <div className="flex-1 grid grid-cols-1 xl:grid-cols-3 gap-5">
        {/* Main Viewport */}
        <div className="xl:col-span-2 glass-panel rounded-lg border border-white/10 relative overflow-hidden flex flex-col min-h-[420px]">
          <div className="p-4 border-b border-white/5 flex items-center justify-between bg-black/20">
            <div className="flex items-center gap-2 text-[10px] font-mono text-emerald-400">
              <span className="relative flex h-2 w-2">
                <span className={`animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75 ${!isScanning && 'hidden'}`}></span>
                <span className={`relative inline-flex rounded-full h-2 w-2 ${isScanning ? 'bg-emerald-500' : 'bg-foreground/20'}`}></span>
              </span>
              {isScanning ? 'LIVE DESKTOP FEED' : 'FEED OFFLINE'}
            </div>
            <Maximize size={14} className="text-foreground/40 hover:text-white cursor-pointer transition-colors" />
          </div>
          
          <div className="flex-1 bg-black/60 relative flex items-center justify-center overflow-hidden">
            {isScanning && !feedFailed ? (
              <>
                <img 
                  src="http://127.0.0.1:8400/vision/stream" 
                  alt="Live Vision Feed" 
                  className="absolute inset-0 w-full h-full object-contain"
                  onError={() => setFeedFailed(true)}
                />
                <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none mix-blend-overlay" />
              </>
            ) : isScanning && feedFailed ? (
              <div className="flex flex-col items-center justify-center">
                <Eye size={48} className="text-emerald-500/20 mb-4" />
                <div className="text-foreground/40 text-xs font-mono uppercase tracking-widest">Feed Offline</div>
              </div>
            ) : (
              <div className="text-foreground/20 text-xs font-mono">NO SIGNAL</div>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <section className="glass-panel p-5 rounded-lg">
            <h3 className="text-[11px] font-bold text-foreground/50 tracking-widest uppercase flex items-center gap-2 mb-4">
              <Focus size={14} /> Detected Anchors
            </h3>
            <div className="space-y-2">
              <AnchorItem label={activeApp || "Unknown"} type="Telemetry" />
              <AnchorItem label="Vision verification not run" type="Unavailable" />
            </div>
          </section>

          <section className="glass-panel p-5 rounded-lg">
            <h3 className="text-[11px] font-bold text-foreground/50 tracking-widest uppercase flex items-center gap-2 mb-4">
              <ScanLine size={14} /> Semantic Context
            </h3>
            <p className="text-[11px] leading-relaxed text-foreground/70 font-mono">
              Validator output will appear here after a backend verification event.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
};

const AnchorItem = ({ label, type }: any) => (
  <div className="p-2.5 rounded-md bg-black/40 border border-white/10 flex items-center justify-between">
    <span className="text-[10px] font-bold text-emerald-400">{label}</span>
    <span className="text-[9px] font-mono text-foreground/40 uppercase">{type}</span>
  </div>
);
