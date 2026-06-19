"use client";

import React from 'react';
import { Sidebar } from '@/features/sidebar/components/Sidebar';
import { Header } from '@/components/Header';
import { useUIStore } from '@/store/useUIStore';

export const AppShell: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const hydratePreferencesFromStorage = useUIStore((state) => state.hydratePreferencesFromStorage);

  React.useEffect(() => {
    hydratePreferencesFromStorage();
  }, [hydratePreferencesFromStorage]);

  return (
    <div className="flex h-dvh w-full overflow-hidden bg-[#050509] text-foreground selection:bg-secondary/30 bg-grid relative">
      <div className="pointer-events-none absolute inset-0 z-0 bg-[radial-gradient(circle_at_18%_14%,rgba(139,92,246,0.16),transparent_30%),radial-gradient(circle_at_88%_20%,rgba(6,182,212,0.11),transparent_30%),radial-gradient(circle_at_70%_82%,rgba(245,158,11,0.07),transparent_34%),linear-gradient(135deg,rgba(8,8,13,0.98),rgba(3,5,11,0.99))]" />
      <div className="pointer-events-none absolute inset-0 z-0 opacity-[0.055] bg-[repeating-linear-gradient(135deg,rgba(255,255,255,0.7)_0px,rgba(255,255,255,0.7)_1px,transparent_1px,transparent_8px)]" />
      <Sidebar />
      
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden relative z-10">
        <Header />
        
        <div className="flex-1 min-h-0 flex overflow-hidden">
          <div className="flex-1 min-h-0 min-w-0 flex flex-col">
            {children}
          </div>
        </div>
      </main>
    </div>
  );
};
