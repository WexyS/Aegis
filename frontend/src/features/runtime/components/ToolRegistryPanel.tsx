"use client";

import React from 'react';
import { RefreshCw, ShieldCheck, Wrench } from 'lucide-react';

import { fetchToolRegistry } from '@/lib/api';
import { useRuntimeStore } from '@/store/useRuntimeStore';
import { ToolSpec } from '@/types/runtime';

const RISK_STYLE: Record<string, string> = {
  none: 'border-white/10 text-foreground/45',
  low: 'border-emerald-500/25 text-emerald-300',
  medium: 'border-amber-500/25 text-amber-300',
  high: 'border-orange-500/25 text-orange-300',
  critical: 'border-red-500/30 text-red-300',
};

export const ToolRegistryPanel = () => {
  const toolRegistry = useRuntimeStore((state) => state.toolRegistry);
  const setToolRegistry = useRuntimeStore((state) => state.setToolRegistry);
  const [category, setCategory] = React.useState('all');
  const [isRefreshing, setIsRefreshing] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const loadRegistry = React.useCallback(async () => {
    setIsRefreshing(true);
    setError(null);
    try {
      setToolRegistry(await fetchToolRegistry());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Tool registry unavailable');
    } finally {
      setIsRefreshing(false);
    }
  }, [setToolRegistry]);

  React.useEffect(() => {
    if (!toolRegistry) void loadRegistry();
  }, [toolRegistry, loadRegistry]);

  const categories = React.useMemo(() => {
    const names = new Set((toolRegistry?.tools ?? []).map((tool) => tool.category));
    return ['all', ...Array.from(names).sort()];
  }, [toolRegistry]);

  const tools = React.useMemo(() => {
    const source = toolRegistry?.tools ?? [];
    return category === 'all' ? source : source.filter((tool) => tool.category === category);
  }, [category, toolRegistry]);

  return (
    <div className="flex-1 p-5 lg:p-6 space-y-5 overflow-y-auto custom-scrollbar">
      <div className="flex flex-col gap-4 border-b border-white/5 pb-5 xl:flex-row xl:items-center xl:justify-between">
        <div className="flex items-center gap-4 min-w-0">
          <div className="p-3 bg-emerald-500/10 rounded-lg border border-emerald-500/30">
            <Wrench className="text-emerald-300" size={24} />
          </div>
          <div className="min-w-0">
            <h2 className="text-lg font-bold tracking-widest text-white uppercase">Tool Registry</h2>
            <p className="text-xs text-foreground/40 font-mono truncate">
              {toolRegistry ? `${toolRegistry.registered_count} tools / ${toolRegistry.scan_version}` : 'Backend registry unavailable'}
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => void loadRegistry()}
          disabled={isRefreshing}
          className="flex h-9 items-center justify-center gap-2 rounded-md border border-white/10 bg-white/[0.03] px-3 text-[10px] font-bold uppercase tracking-widest text-foreground/60 transition-colors hover:border-accent/40 hover:text-accent disabled:cursor-not-allowed disabled:opacity-50"
        >
          <RefreshCw size={13} className={isRefreshing ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="rounded-lg border border-danger/30 bg-danger/10 px-4 py-3 text-[12px] font-mono text-danger">
          {error}
        </div>
      )}

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Stat label="Registered" value={toolRegistry ? toolRegistry.registered_count : 'Unavailable'} />
        <Stat label="Configured" value={toolRegistry ? toolRegistry.configured_count : 'Unavailable'} />
        <Stat label="Specs" value={toolRegistry ? toolRegistry.spec_count : 'Unavailable'} />
        <Stat label="Drift" value={toolRegistry?.status ?? 'Unavailable'} />
      </div>

      <div className="flex flex-wrap gap-2">
        {categories.map((item) => (
          <button
            key={item}
            type="button"
            onClick={() => setCategory(item)}
            className={`rounded-md border px-3 py-1.5 text-[10px] font-mono uppercase tracking-wider transition-colors ${category === item ? 'border-accent/50 bg-accent/10 text-accent' : 'border-white/10 bg-white/[0.03] text-foreground/45 hover:text-white'}`}
          >
            {item}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-3 2xl:grid-cols-2">
        {tools.map((tool) => (
          <ToolCard key={tool.name} tool={tool} />
        ))}
      </div>

      {toolRegistry && tools.length === 0 && (
        <div className="rounded-lg border border-white/10 bg-black/20 p-5 text-[12px] font-mono text-foreground/35">
          No backend tool registry entries match this filter.
        </div>
      )}
    </div>
  );
};

const Stat = ({ label, value }: { label: string; value: number | string }) => (
  <div className="rounded-lg border border-white/10 bg-black/20 p-3">
    <div className="text-[9px] font-bold uppercase tracking-widest text-foreground/40">{label}</div>
    <div className="mt-2 text-xl font-bold text-white">{value}</div>
  </div>
);

const ToolCard = ({ tool }: { tool: ToolSpec }) => {
  const executionPolicy = tool.risk === 'critical'
    ? 'blocked'
    : tool.requires_approval
      ? 'approval'
      : 'auto';

  return (
    <div className="rounded-lg border border-white/10 bg-white/[0.03] p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="truncate text-sm font-semibold text-white">{tool.name}</div>
          <div className="mt-1 truncate text-[10px] font-mono text-foreground/40">{tool.category} / {tool.evidence_policy}</div>
        </div>
        <ShieldCheck size={16} className="shrink-0 text-accent/70" />
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <Pill className={RISK_STYLE[tool.risk] ?? RISK_STYLE.none}>{tool.risk}</Pill>
        <Pill className={tool.risk === 'critical' ? RISK_STYLE.critical : undefined}>{executionPolicy}</Pill>
        <Pill>{tool.side_effecting ? 'side effect' : 'read only'}</Pill>
        {tool.cancellation_supported && <Pill>cancel</Pill>}
        {tool.dry_run_supported && <Pill>dry run</Pill>}
        <Pill>{tool.timeout_seconds}s</Pill>
      </div>
    </div>
  );
};

const Pill = ({ children, className = 'border-white/10 text-foreground/45' }: { children: React.ReactNode; className?: string }) => (
  <span className={`rounded-md border bg-black/20 px-2 py-1 text-[9px] font-mono uppercase tracking-wider ${className}`}>
    {children}
  </span>
);
