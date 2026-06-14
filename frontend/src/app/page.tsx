"use client";

import React from 'react';
import { AppShell } from '@/layouts/AppShell';
import { useUIStore } from '@/store/useUIStore';

import { AskAegisPanel } from '@/features/ask/components/AskAegisPanel';
import { AdvancedWorkspace } from '@/features/advanced/components/AdvancedWorkspace';
import { CapabilitiesPanel } from '@/features/capabilities/components/CapabilitiesPanel';
import { MemoryOverviewPanel } from '@/features/memory/components/MemoryOverviewPanel';
import { MissionHome } from '@/features/mission-home/components/MissionHome';
import { WorkSurface } from '@/components/WorkSurface';

import { connectRuntime, disconnectRuntime } from '@/lib/socket';

export default function AegisDashboard() {
  const { activeTab } = useUIStore();

  React.useEffect(() => {
    connectRuntime();
    return () => disconnectRuntime();
  }, []);

  return (
    <AppShell>
      <div className="relative z-10 flex-1 min-h-0 min-w-0 overflow-hidden">
        {activeTab === 'Mission' && <MissionHome />}
        {activeTab === 'Ask' && <AskAegisPanel />}
        {activeTab === 'Work' && <WorkSurface />}
        {activeTab === 'Memory' && <MemoryOverviewPanel />}
        {activeTab === 'Capabilities' && <CapabilitiesPanel />}
        {activeTab === 'Advanced' && <AdvancedWorkspace />}
      </div>
    </AppShell>
  );
}
