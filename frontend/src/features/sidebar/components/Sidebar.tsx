"use client";

import React from 'react';
import { 
  MessageSquare, 
  HelpCircle,
  Activity, 
  Database,
  Rocket,
  LayoutDashboard, 
  Eye, 
  ShieldAlert, 
  Settings, 
  Wrench,
  Zap 
} from 'lucide-react';
import { useUIStore } from '@/store/useUIStore';

export const Sidebar = () => {
  const { activeTab, setActiveTab } = useUIStore();

  return (
    <aside className="w-14 sm:w-16 lg:w-60 shrink-0 flex flex-col border-r border-white/10 bg-background/95 z-50">
      <div className="h-14 px-3 sm:px-4 flex items-center justify-center lg:justify-start gap-3 border-b border-white/10">
        <div className="w-8 h-8 rounded-md bg-accent flex items-center justify-center">
          <Zap className="text-background w-6 h-6 fill-current" />
        </div>
        <div className="hidden lg:flex flex-col">
          <span className="text-base font-bold tracking-tight text-white uppercase">AEGIS</span>
          <span className="text-[9px] font-mono text-accent uppercase tracking-widest">Runtime Core</span>
        </div>
      </div>

      <nav className="flex-1 px-2 sm:px-3 py-4 space-y-1 overflow-y-auto custom-scrollbar">
        <NavItem icon={<MessageSquare size={18}/>} label="Mission Control" active={activeTab === 'chat'} onClick={() => setActiveTab('chat')} />
        <NavItem icon={<HelpCircle size={18}/>} label="Ask Aegis" active={activeTab === 'Ask Aegis'} onClick={() => setActiveTab('Ask Aegis')} />
        <NavItem icon={<Rocket size={18}/>} label="Aegis Control" active={activeTab === 'Aegis Control'} onClick={() => setActiveTab('Aegis Control')} />
        <NavItem icon={<Activity size={18}/>} label="Runtime Stats" active={activeTab === 'Runtime Stats'} onClick={() => setActiveTab('Runtime Stats')} />
        <NavItem icon={<Database size={18}/>} label="Applications" active={activeTab === 'Applications'} onClick={() => setActiveTab('Applications')} />
        <NavItem icon={<Wrench size={18}/>} label="Tools" active={activeTab === 'Tools'} onClick={() => setActiveTab('Tools')} />
        <NavItem icon={<LayoutDashboard size={18}/>} label="Agent Graph" active={activeTab === 'Agent Graph'} onClick={() => setActiveTab('Agent Graph')} />
        <NavItem icon={<Eye size={18}/>} label="Vision Lab" active={activeTab === 'Vision Lab'} onClick={() => setActiveTab('Vision Lab')} />
        <NavItem icon={<ShieldAlert size={18}/>} label="Chaos Shield" active={activeTab === 'Chaos Shield'} onClick={() => setActiveTab('Chaos Shield')} />
      </nav>

      <div className="p-2 sm:p-3 border-t border-white/10">
        <NavItem icon={<Settings size={18}/>} label="Settings" active={activeTab === 'settings'} onClick={() => setActiveTab('settings')} />
      </div>
    </aside>
  );
};

const NavItem = ({ icon, label, active, onClick }: any) => (
  <button
    type="button"
    aria-label={label}
    onClick={onClick}
    className={`w-full flex items-center justify-center lg:justify-start gap-3 p-2.5 rounded-md cursor-pointer transition-colors duration-150 group relative overflow-hidden ${active ? 'bg-accent/10 text-accent border border-accent/20' : 'text-foreground/45 hover:bg-white/[0.04] hover:text-white border border-transparent'}`}
  >
    <div className={`relative z-10 ${active ? 'text-accent' : 'text-foreground/50 group-hover:text-white'} transition-colors`}>
      {icon}
    </div>
    <span className="hidden lg:block relative z-10 text-[13px] font-medium tracking-wide">{label}</span>
  </button>
);
