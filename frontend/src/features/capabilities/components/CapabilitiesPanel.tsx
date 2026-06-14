"use client";

import React from 'react';
import {
  Bot,
  BrainCircuit,
  Boxes,
  CheckCircle2,
  Database,
  FileSearch,
  Globe2,
  HelpCircle,
  Layers3,
  LockKeyhole,
  MonitorCog,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Wrench,
} from 'lucide-react';

import { StatusBadge } from '@/components/StatusBadge';
import { dictionaryFor } from '@/i18n';
import { useUIStore } from '@/store/useUIStore';

type CapabilityState =
  | 'implemented'
  | 'read-only'
  | 'proposal-only'
  | 'metadata-only'
  | 'approval-gated'
  | 'future-gated'
  | 'blocked/unsupported';

type Capability = {
  name: string;
  state: CapabilityState;
  stateLabel: string;
  detail: string;
  icon: React.ReactNode;
};

export const CapabilitiesPanel = () => {
  const language = useUIStore((state) => state.language);
  const t = dictionaryFor(language);
  const c = t.capabilities;
  const state = c.states;
  const capabilities: Capability[] = [
    { name: c.items.ask.name, state: 'implemented', stateLabel: state.implemented, detail: c.items.ask.detail, icon: <HelpCircle size={17} /> },
    { name: c.items.maintenance.name, state: 'read-only', stateLabel: state.readOnly, detail: c.items.maintenance.detail, icon: <ShieldCheck size={17} /> },
    { name: c.items.memory.name, state: 'implemented', stateLabel: state.implemented, detail: c.items.memory.detail, icon: <Database size={17} /> },
    { name: c.items.autopilot.name, state: 'read-only', stateLabel: state.readOnly, detail: c.items.autopilot.detail, icon: <FileSearch size={17} /> },
    { name: c.items.modelGateway.name, state: 'proposal-only', stateLabel: state.proposalOnly, detail: c.items.modelGateway.detail, icon: <BrainCircuit size={17} /> },
    { name: c.items.skillRegistry.name, state: 'metadata-only', stateLabel: state.metadataOnly, detail: c.items.skillRegistry.detail, icon: <Wrench size={17} /> },
    { name: c.items.agentRuntime.name, state: 'proposal-only', stateLabel: state.proposalOnly, detail: c.items.agentRuntime.detail, icon: <Bot size={17} /> },
    { name: c.items.pluginLifecycle.name, state: 'metadata-only', stateLabel: state.metadataOnly, detail: c.items.pluginLifecycle.detail, icon: <Layers3 size={17} /> },
    { name: c.items.computerOperator.name, state: 'approval-gated', stateLabel: state.approvalGated, detail: c.items.computerOperator.detail, icon: <MonitorCog size={17} /> },
    { name: c.items.codexSupervisor.name, state: 'future-gated', stateLabel: state.futureGated, detail: c.items.codexSupervisor.detail, icon: <CheckCircle2 size={17} /> },
    { name: c.items.verticalPacks.name, state: 'future-gated', stateLabel: state.futureGated, detail: c.items.verticalPacks.detail, icon: <Boxes size={17} /> },
    { name: c.items.modelCouncil.name, state: 'future-gated', stateLabel: state.futureGated, detail: c.items.modelCouncil.detail, icon: <Sparkles size={17} /> },
    { name: c.items.externalBroker.name, state: 'future-gated', stateLabel: state.futureGated, detail: c.items.externalBroker.detail, icon: <Globe2 size={17} /> },
    { name: c.items.robustnessLab.name, state: 'future-gated', stateLabel: state.futureGated, detail: c.items.robustnessLab.detail, icon: <ShieldAlert size={17} /> },
  ];

  return (
  <div className="h-full min-h-0 overflow-y-auto custom-scrollbar">
    <div className="mx-auto flex w-full max-w-[94rem] flex-col gap-5 p-4 pb-10 sm:p-5 sm:pb-10 lg:p-7 lg:pb-12 2xl:p-8 2xl:pb-12">
      <section className="rounded-lg border border-white/10 bg-white/[0.04] p-5 shadow-2xl shadow-black/15 lg:p-6">
        <div className="flex flex-col justify-between gap-4 xl:flex-row xl:items-end">
          <div className="max-w-4xl">
            <h1 className="text-3xl font-semibold tracking-tight text-white lg:text-4xl">{c.title}</h1>
            <p className="mt-3 text-sm leading-7 text-foreground/60">
              {c.subtitle}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <StatusBadge label={c.metadataNotPermission} tone="warning" />
            <StatusBadge label={c.frontendNotAuthority} tone="unknown" />
          </div>
        </div>
      </section>

      <div className="grid gap-4 md:grid-cols-2 2xl:grid-cols-3">
        {capabilities.map((capability) => (
          <CapabilityCard key={capability.name} capability={capability} />
        ))}
      </div>

      <section className="rounded-lg border border-warning/20 bg-warning/[0.035] p-4">
        <div className="flex items-start gap-3">
          <LockKeyhole size={17} className="mt-0.5 text-warning" />
          <div>
            <h2 className="text-sm font-semibold text-white">{c.boundaryTitle}</h2>
            <p className="mt-2 text-sm leading-6 text-foreground/58">
              {c.boundaryCopy}
            </p>
          </div>
        </div>
      </section>
    </div>
  </div>
  );
};

const CapabilityCard = ({ capability }: { capability: Capability }) => (
  <section className="rounded-lg border border-white/10 bg-white/[0.032] p-4 shadow-xl shadow-black/10">
    <div className="flex items-start justify-between gap-3">
      <div className="flex min-w-0 items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-accent/20 bg-accent/10 text-accent">
          {capability.icon}
        </div>
        <div className="min-w-0">
          <h2 className="text-base font-semibold text-white">{capability.name}</h2>
          <p className="mt-2 text-sm leading-6 text-foreground/58">{capability.detail}</p>
        </div>
      </div>
      <StatusBadge label={capability.stateLabel} tone={stateTone(capability.state)} className="max-w-[8rem] shrink-0" />
    </div>
  </section>
);

function stateTone(state: CapabilityState): 'success' | 'info' | 'warning' | 'danger' | 'unknown' {
  if (state === 'implemented') return 'success';
  if (state === 'read-only' || state === 'proposal-only') return 'info';
  if (state === 'approval-gated' || state === 'future-gated') return 'warning';
  if (state === 'blocked/unsupported') return 'danger';
  return 'unknown';
}
