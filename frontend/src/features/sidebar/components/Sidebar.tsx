"use client";

import React from 'react';
import { 
  BrainCircuit,
  BriefcaseBusiness,
  Boxes,
  Database,
  HelpCircle,
  Layers3,
  Radar,
  Zap 
} from 'lucide-react';
import { useUIStore } from '@/store/useUIStore';

export const Sidebar = () => {
  const { activeTab, setActiveTab } = useUIStore();

  return (
    <aside className="w-14 sm:w-16 lg:w-64 shrink-0 flex flex-col border-r border-white/10 bg-background/90 backdrop-blur-xl z-50">
      <div className="h-16 px-3 sm:px-4 flex items-center justify-center lg:justify-start gap-3 border-b border-white/10">
        <div className="w-8 h-8 rounded-md bg-accent flex items-center justify-center shadow-lg shadow-cyan-950/30">
          <Zap className="text-background w-6 h-6 fill-current" />
        </div>
        <div className="hidden lg:flex flex-col">
          <span className="text-base font-bold tracking-tight text-white">Aegis</span>
          <span className="text-[9px] font-mono text-accent uppercase tracking-widest">Mission Control</span>
        </div>
      </div>

      <nav className="flex-1 px-2 sm:px-3 py-4 space-y-1 overflow-y-auto custom-scrollbar">
        <NavItem icon={<Radar size={18}/>} label="Mission" detail="Home" active={activeTab === 'Mission'} onClick={() => setActiveTab('Mission')} />
        <NavItem icon={<HelpCircle size={18}/>} label="Ask" detail="Read-only" active={activeTab === 'Ask'} onClick={() => setActiveTab('Ask')} />
        <NavItem icon={<BriefcaseBusiness size={18}/>} label="Work" detail="Plan & review" active={activeTab === 'Work'} onClick={() => setActiveTab('Work')} />
        <NavItem icon={<Database size={18}/>} label="Memory" detail="Consent" active={activeTab === 'Memory'} onClick={() => setActiveTab('Memory')} />
        <NavItem icon={<Boxes size={18}/>} label="Capabilities" detail="What exists" active={activeTab === 'Capabilities'} onClick={() => setActiveTab('Capabilities')} />
        <NavItem icon={<Layers3 size={18}/>} label="Advanced" detail="Diagnostics" active={activeTab === 'Advanced'} onClick={() => setActiveTab('Advanced')} />
      </nav>

      <div className="p-2 sm:p-3 border-t border-white/10">
        <div className="hidden rounded-lg border border-white/10 bg-white/[0.025] p-3 text-[10px] leading-relaxed text-foreground/45 lg:block">
          Backend truth remains authoritative. This shell does not create evidence, approvals, leases, or execution.
        </div>
        <NavItem icon={<BrainCircuit size={18}/>} label="Runtime truth" detail="No fake green" active={false} onClick={() => setActiveTab('Advanced')} className="lg:hidden" />
      </div>
    </aside>
  );
};

const NavItem = ({ icon, label, detail, active, onClick, className = '' }: any) => (
  <button
    type="button"
    aria-label={label}
    onClick={onClick}
    className={`w-full flex items-center justify-center lg:justify-start gap-3 p-2.5 rounded-md cursor-pointer transition-colors duration-150 group relative overflow-hidden ${active ? 'bg-accent/10 text-accent border border-accent/25 shadow-lg shadow-cyan-950/10' : 'text-foreground/45 hover:bg-white/[0.04] hover:text-white border border-transparent'} ${className}`}
  >
    <div className={`relative z-10 ${active ? 'text-accent' : 'text-foreground/50 group-hover:text-white'} transition-colors`}>
      {icon}
    </div>
    <span className="hidden lg:flex min-w-0 flex-col items-start relative z-10">
      <span className="text-[13px] font-medium tracking-wide">{label}</span>
      {detail && <span className="mt-0.5 max-w-full truncate text-[9px] font-mono uppercase tracking-wider text-foreground/30 group-hover:text-foreground/45">{detail}</span>}
    </span>
  </button>
);
