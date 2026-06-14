"use client";

import React from 'react';
import { Sidebar } from '@/features/sidebar/components/Sidebar';
import { Header } from '@/components/Header';

export const AppShell: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="flex h-dvh w-full overflow-hidden bg-background text-foreground selection:bg-accent/30 bg-grid relative">
      <div className="pointer-events-none absolute inset-0 z-0 bg-[radial-gradient(circle_at_20%_12%,rgba(6,182,212,0.14),transparent_28%),radial-gradient(circle_at_82%_0%,rgba(139,92,246,0.13),transparent_30%),linear-gradient(135deg,rgba(5,8,20,0.96),rgba(3,6,17,0.98))]" />
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
