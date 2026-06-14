"use client";

import React, { useEffect, useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { eventSourcing } from '@/features/runtime/services/EventSourcing';
import { getConnectionState } from '@/lib/socket';

export const DevOverlay = () => {
  if (process.env.NODE_ENV !== 'development' || process.env.NEXT_PUBLIC_AEGIS_SHOW_DEV_OVERLAY !== '1') {
    return null;
  }

  return <DevOverlayInner />;
};

const DevOverlayInner = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [metrics, setMetrics] = useState({
    fps: 0,
    renders: 0,
    heapMb: 0,
    eventThroughput: 0,
    queueSize: 0,
    connectionState: 'disconnected'
  });
  
  const renders = useRef(0);
  const lastEventCount = useRef(0);
  const frames = useRef(0);
  const lastFpsTime = useRef(performance.now());

  useEffect(() => {
    renders.current++;
    
    // FPS Loop
    let animationFrameId: number;
    const loop = () => {
      frames.current++;
      const now = performance.now();
      if (now - lastFpsTime.current >= 1000) {
        // Update FPS
        const currentFps = Math.round((frames.current * 1000) / (now - lastFpsTime.current));
        
        // Calculate other metrics
        const totalEvents = eventSourcing.getHistory().length;
        const throughput = totalEvents - lastEventCount.current;
        lastEventCount.current = totalEvents;
        
        let heapMb = 0;
        const mem = (performance as any).memory;
        if (mem) {
          heapMb = Math.round(mem.usedJSHeapSize / 1024 / 1024);
        }

        setMetrics({
          fps: currentFps,
          renders: renders.current,
          heapMb,
          eventThroughput: throughput,
          queueSize: eventSourcing.getPendingWriteCount(),
          connectionState: getConnectionState()
        });

        frames.current = 0;
        lastFpsTime.current = now;
      }
      animationFrameId = requestAnimationFrame(loop);
    };
    
    loop();
    return () => cancelAnimationFrame(animationFrameId);
  }, []);

  return (
    <div className="fixed top-4 right-4 z-[9999] font-mono text-[10px]">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="bg-red-500/20 border border-red-500/50 text-red-400 px-2 py-1 rounded shadow-[0_0_10px_rgba(239,68,68,0.2)] hover:bg-red-500/30 transition-colors backdrop-blur-sm"
      >
        DEV: RELIABILITY
      </button>
      
      {isOpen && (
        <motion.div 
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-2 bg-black/80 border border-red-500/30 p-3 rounded-lg shadow-2xl backdrop-blur-md w-64 space-y-2"
        >
          <div className="text-red-400 font-bold border-b border-red-500/30 pb-1 mb-2">AEGIS WATCHDOG</div>
          <MetricRow label="FPS" value={metrics.fps} warn={metrics.fps < 30} />
          <MetricRow label="React Renders" value={metrics.renders} />
          <MetricRow label="Heap Usage" value={`${metrics.heapMb} MB`} warn={metrics.heapMb > 500} />
          <MetricRow label="Events/sec" value={metrics.eventThroughput} />
          <MetricRow label="WAL Queue" value={metrics.queueSize} warn={metrics.queueSize > 100} />
          <MetricRow label="DB Latency" value="unmeasured" />
          <MetricRow label="WS State" value={metrics.connectionState} warn={metrics.connectionState !== 'connected'} />
        </motion.div>
      )}
    </div>
  );
};

const MetricRow = ({ label, value, warn }: { label: string, value: string | number, warn?: boolean }) => (
  <div className="flex justify-between items-center">
    <span className="text-zinc-500">{label}</span>
    <span className={`font-bold ${warn ? 'text-yellow-500 animate-pulse' : 'text-emerald-400'}`}>
      {value}
    </span>
  </div>
);
