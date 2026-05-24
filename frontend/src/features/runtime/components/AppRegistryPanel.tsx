"use client";

import React from 'react';
import { Database, MonitorUp, RefreshCw, Search } from 'lucide-react';

import { fetchAppRegistry } from '@/lib/api';
import { useRuntimeStore } from '@/store/useRuntimeStore';
import { AppRegistryEntry, AppRegistrySnapshot } from '@/types/runtime';

const SOURCE_LABELS: Record<string, string> = {
  configured: 'Configured',
  start_menu: 'Start Menu',
  program_files: 'Program Files',
  steam: 'Steam',
  epic: 'Epic',
};

export const AppRegistryPanel = () => {
  const appRegistry = useRuntimeStore((state) => state.appRegistry);
  const setAppRegistry = useRuntimeStore((state) => state.setAppRegistry);
  const [query, setQuery] = React.useState('');
  const [isRefreshing, setIsRefreshing] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const loadRegistry = React.useCallback(async (refresh: boolean) => {
    setIsRefreshing(true);
    setError(null);
    try {
      const registry = await fetchAppRegistry(refresh);
      setAppRegistry(registry);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'App registry unavailable');
    } finally {
      setIsRefreshing(false);
    }
  }, [setAppRegistry]);

  React.useEffect(() => {
    if (!appRegistry) {
      void loadRegistry(false);
    }
  }, [appRegistry, loadRegistry]);

  const entries = React.useMemo(() => filterEntries(appRegistry, query), [appRegistry, query]);
  const sourceCounts = React.useMemo(() => countBySource(appRegistry?.entries ?? []), [appRegistry]);

  return (
    <div className="flex-1 p-5 lg:p-6 space-y-5 overflow-y-auto custom-scrollbar">
      <div className="flex flex-col gap-4 border-b border-white/5 pb-5 xl:flex-row xl:items-center xl:justify-between">
        <div className="flex items-center gap-4 min-w-0">
          <div className="p-3 bg-cyan-500/10 rounded-lg border border-cyan-500/30">
            <Database className="text-cyan-300" size={24} />
          </div>
          <div className="min-w-0">
            <h2 className="text-lg font-bold tracking-widest text-white uppercase">Application Registry</h2>
            <p className="text-xs text-foreground/40 font-mono truncate">
              {appRegistry ? `${appRegistry.entry_count} entries / ${appRegistry.scan_version}` : 'Backend registry unavailable'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="relative min-w-0">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-foreground/35" />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              className="h-9 w-full min-w-0 rounded-md border border-white/10 bg-black/20 pl-9 pr-3 text-[12px] text-foreground/80 outline-none focus:border-accent/50 xl:w-64"
              placeholder="Filter apps"
            />
          </div>
          <button
            type="button"
            onClick={() => void loadRegistry(true)}
            disabled={isRefreshing}
            className="flex h-9 items-center justify-center gap-2 rounded-md border border-white/10 bg-white/[0.03] px-3 text-[10px] font-bold uppercase tracking-widest text-foreground/60 transition-colors hover:border-accent/40 hover:text-accent disabled:cursor-not-allowed disabled:opacity-50"
          >
            <RefreshCw size={13} className={isRefreshing ? 'animate-spin' : ''} />
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-danger/30 bg-danger/10 px-4 py-3 text-[12px] font-mono text-danger">
          {error}
        </div>
      )}

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Stat label="Configured" value={appRegistry ? appRegistry.configured_count : 'Unavailable'} />
        <Stat label="Discovered" value={appRegistry ? appRegistry.discovered_count : 'Unavailable'} />
        <Stat label="Visible" value={appRegistry ? entries.length : 'Unavailable'} />
        <Stat label="Read Only" value={appRegistry ? (appRegistry.read_only === false ? 'No' : 'Yes') : 'Unavailable'} />
      </div>

      <div className="flex flex-wrap gap-2">
        {Object.entries(sourceCounts).map(([source, count]) => (
          <span key={source} className="rounded-md border border-white/10 bg-white/[0.03] px-2.5 py-1 text-[10px] font-mono text-foreground/50">
            {SOURCE_LABELS[source] ?? source}: {count}
          </span>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-3 2xl:grid-cols-2">
        {entries.map((entry) => (
          <AppEntryCard key={`${entry.source}-${entry.app_id}`} entry={entry} />
        ))}
      </div>

      {appRegistry && entries.length === 0 && (
        <div className="rounded-lg border border-white/10 bg-black/20 p-5 text-[12px] font-mono text-foreground/35">
          No backend registry entries match this filter.
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

const AppEntryCard = ({ entry }: { entry: AppRegistryEntry }) => (
  <div className="rounded-lg border border-white/10 bg-white/[0.03] p-4 transition-colors hover:border-accent/25">
    <div className="flex items-start justify-between gap-3">
      <div className="min-w-0">
        <div className="truncate text-sm font-semibold text-white">{entry.display_name}</div>
        <div className="mt-1 truncate text-[10px] font-mono text-foreground/40">{entry.app_id}</div>
      </div>
      <MonitorUp size={16} className="shrink-0 text-accent/70" />
    </div>
    <div className="mt-4 flex flex-wrap gap-2">
      <Pill>{SOURCE_LABELS[entry.source] ?? entry.source}</Pill>
      <Pill>{entry.launch_target_type}</Pill>
      {entry.process_name && <Pill>{entry.process_name}</Pill>}
    </div>
  </div>
);

const Pill = ({ children }: { children: React.ReactNode }) => (
  <span className="rounded-md border border-white/10 bg-black/20 px-2 py-1 text-[9px] font-mono uppercase tracking-wider text-foreground/45">
    {children}
  </span>
);

function filterEntries(snapshot: AppRegistrySnapshot | null, query: string): AppRegistryEntry[] {
  const entries = snapshot?.entries ?? [];
  const normalized = query.trim().toLowerCase();
  if (!normalized) return entries;
  return entries.filter((entry) => {
    const haystack = [
      entry.app_id,
      entry.display_name,
      entry.source,
      entry.launch_target_type,
      entry.process_name ?? '',
      ...(entry.aliases ?? []),
    ].join(' ').toLowerCase();
    return haystack.includes(normalized);
  });
}

function countBySource(entries: AppRegistryEntry[]): Record<string, number> {
  return entries.reduce<Record<string, number>>((acc, entry) => {
    acc[entry.source] = (acc[entry.source] ?? 0) + 1;
    return acc;
  }, {});
}
