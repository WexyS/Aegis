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
  detail: string;
  icon: React.ReactNode;
};

const CAPABILITIES: Capability[] = [
  {
    name: 'Aegis Ask',
    state: 'implemented',
    detail: 'Read-only explanation and safe next-step planning through the backend Ask API.',
    icon: <HelpCircle size={17} />,
  },
  {
    name: 'Maintenance Scan',
    state: 'read-only',
    detail: 'Backend diagnostics preserve raw versus active evidence and replay status without mutation.',
    icon: <ShieldCheck size={17} />,
  },
  {
    name: 'Memory OS',
    state: 'implemented',
    detail: 'Local lifecycle/search surfaces exist; no silent long-term memory write from this shell.',
    icon: <Database size={17} />,
  },
  {
    name: 'AutoPilot',
    state: 'read-only',
    detail: 'Repo structure audit is bounded read-only analysis. AutoPilot reports are not evidence.',
    icon: <FileSearch size={17} />,
  },
  {
    name: 'Model Gateway',
    state: 'proposal-only',
    detail: 'Local provider boundary exists. Model output is never truth, evidence, approval, or verifier success.',
    icon: <BrainCircuit size={17} />,
  },
  {
    name: 'Skill Registry',
    state: 'metadata-only',
    detail: 'Static catalog and proposal metadata. Registry entries do not grant skill execution permission.',
    icon: <Wrench size={17} />,
  },
  {
    name: 'Agent Runtime',
    state: 'proposal-only',
    detail: 'Bounded agent sessions are proposals only. No tool, model, MCP, shell, or memory authority.',
    icon: <Bot size={17} />,
  },
  {
    name: 'Plugin / Manifest / Lifecycle',
    state: 'metadata-only',
    detail: 'Readiness contracts only. No plugin loading, dynamic import, marketplace action, or execution.',
    icon: <Layers3 size={17} />,
  },
  {
    name: 'Computer Operator',
    state: 'approval-gated',
    detail: 'Governed command runtime foundation exists. Broad autonomous computer control is not implemented.',
    icon: <MonitorCog size={17} />,
  },
  {
    name: 'Codex Supervisor',
    state: 'future-gated',
    detail: 'Read-only bridge and manual review docs exist. In-product review board is not implemented.',
    icon: <CheckCircle2 size={17} />,
  },
  {
    name: 'Vertical Skill Packs',
    state: 'future-gated',
    detail: 'Product direction only until capability, policy, approval, and execution gates are implemented.',
    icon: <Boxes size={17} />,
  },
  {
    name: 'Future Model Council',
    state: 'future-gated',
    detail: 'Roadmap framing only. No model racing, external router, provider keys, or cloud fallback added.',
    icon: <Sparkles size={17} />,
  },
  {
    name: 'Future External API Broker',
    state: 'future-gated',
    detail: 'Would require explicit provider enablement, purpose, redaction preview, cost/privacy gates, and no hidden execution.',
    icon: <Globe2 size={17} />,
  },
  {
    name: 'Future Robustness Lab',
    state: 'future-gated',
    detail: 'Defensive testing concept only. No jailbreak, bypass, anti-refusal, or prompt-obfuscation behavior.',
    icon: <ShieldAlert size={17} />,
  },
];

export const CapabilitiesPanel = () => (
  <div className="min-h-full overflow-y-auto custom-scrollbar">
    <div className="mx-auto flex w-full max-w-[94rem] flex-col gap-5 p-4 sm:p-5 lg:p-7 2xl:p-8">
      <section className="rounded-lg border border-white/10 bg-white/[0.04] p-5 shadow-2xl shadow-black/15 lg:p-6">
        <div className="flex flex-col justify-between gap-4 xl:flex-row xl:items-end">
          <div className="max-w-4xl">
            <h1 className="text-3xl font-semibold tracking-tight text-white lg:text-4xl">Capability map</h1>
            <p className="mt-3 text-sm leading-7 text-foreground/60">
              A user-facing inventory of what Aegis can do now, what is read-only or proposal-only, and what remains future-gated. This page is product explanation, not runtime permission.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <StatusBadge label="metadata is not permission" tone="warning" />
            <StatusBadge label="frontend is not authority" tone="unknown" />
          </div>
        </div>
      </section>

      <div className="grid gap-4 md:grid-cols-2 2xl:grid-cols-3">
        {CAPABILITIES.map((capability) => (
          <CapabilityCard key={capability.name} capability={capability} />
        ))}
      </div>

      <section className="rounded-lg border border-warning/20 bg-warning/[0.035] p-4">
        <div className="flex items-start gap-3">
          <LockKeyhole size={17} className="mt-0.5 text-warning" />
          <div>
            <h2 className="text-sm font-semibold text-white">Capability boundary</h2>
            <p className="mt-2 text-sm leading-6 text-foreground/58">
              Implemented, listed, proposed, or configured does not mean approved, executed, verified, or safe. Future execution still requires backend policy, explicit scope, approval where needed, evidence expectations, and verifier checks.
            </p>
          </div>
        </div>
      </section>
    </div>
  </div>
);

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
      <StatusBadge label={capability.state} tone={stateTone(capability.state)} className="max-w-[8rem] shrink-0" />
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
