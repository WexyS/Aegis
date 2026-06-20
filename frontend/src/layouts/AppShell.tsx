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
    <div className="relative flex h-dvh w-full overflow-hidden bg-[#111111] text-[#ece9e2] selection:bg-[#f4bf4f]/25">
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
