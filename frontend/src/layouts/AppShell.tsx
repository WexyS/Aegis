"use client";

import React from 'react';
import { Sidebar } from '@/features/sidebar/components/Sidebar';
import { RuntimeConsole } from '@/components/RuntimeConsole';
import { Header } from '@/components/Header';

export const AppShell: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-foreground selection:bg-accent/30 bg-grid relative">
      <div className="absolute inset-0 bg-background/80 pointer-events-none z-0" />
      <Sidebar />
      
      <main className="flex-1 flex flex-col min-w-0 relative z-10">
        <Header />
        
        <div className="flex-1 flex overflow-hidden">
          <div className="flex-1 flex flex-col">
            {children}
          </div>
        </div>

        <RuntimeConsole />
      </main>
    </div>
  );
};
