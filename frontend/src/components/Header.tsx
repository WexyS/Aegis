"use client";

import React from 'react';
import {
  Box,
  Compass,
  Maximize2,
  Minimize2,
  Monitor,
  ShieldCheck,
  Square,
  X,
} from 'lucide-react';

import { dictionaryFor } from '@/i18n';
import { useRuntimeStore } from '@/store/useRuntimeStore';
import { useUIStore } from '@/store/useUIStore';

export const Header = () => {
  const language = useUIStore((state) => state.language);
  const t = dictionaryFor(language);
  const pendingApprovals = useRuntimeStore((state) => state.pendingApprovals);
  const pendingClarifications = useRuntimeStore((state) => state.pendingClarifications);
  const [isElectron, setIsElectron] = React.useState(false);
  const pendingCount = pendingApprovals.length + pendingClarifications.length;

  React.useEffect(() => {
    setIsElectron(Boolean(window.aegis?.isElectron && window.aegis.windowAction));
  }, []);

  const sendWindowAction = React.useCallback((action: 'minimize' | 'toggle-maximize' | 'toggle-fullscreen' | 'close') => {
    window.aegis?.windowAction?.(action);
  }, []);

  return (
    <header className="electron-drag-region relative z-40 flex h-14 shrink-0 items-center justify-between gap-3 border-b border-white/10 bg-[#09090d]/[0.82] px-3 pl-4 backdrop-blur-2xl sm:px-4 lg:px-6">
      <div className="pointer-events-none absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-white/[0.12] to-transparent" />

      <div className="flex min-w-0 flex-1 items-center justify-center gap-2 lg:justify-start">
        <ControlChip icon={<ShieldCheck size={15} />} label={t.header.localMode} active />
        <ControlChip icon={<Compass size={15} />} label={t.header.autoModePreview} />
        <ControlChip icon={<Monitor size={15} />} label={t.header.externalApisOff} />
        <ControlChip icon={<Box size={15} />} label={t.header.modelBoundary} />
        <ControlChip
          icon={<ShieldCheck size={15} />}
          label={`${t.header.approvalGate}: ${pendingCount} ${t.header.pending}`}
          warning={pendingCount > 0}
        />
      </div>

      {isElectron && (
        <div className="electron-no-drag flex shrink-0 items-center gap-1">
          <WindowButton label={t.header.minimize} onClick={() => sendWindowAction('minimize')}>
            <Minimize2 size={15} />
          </WindowButton>
          <WindowButton label={t.header.maximize} onClick={() => sendWindowAction('toggle-maximize')}>
            <Square size={13} />
          </WindowButton>
          <WindowButton label={t.header.fullscreen} onClick={() => sendWindowAction('toggle-fullscreen')}>
            <Maximize2 size={15} />
          </WindowButton>
          <WindowButton label={t.header.close} danger onClick={() => sendWindowAction('close')}>
            <X size={16} />
          </WindowButton>
        </div>
      )}
    </header>
  );
};

const ControlChip = ({
  icon,
  label,
  active = false,
  warning = false,
}: {
  icon: React.ReactNode;
  label: string;
  active?: boolean;
  warning?: boolean;
}) => (
  <div
    className={`electron-no-drag hidden items-center gap-2 rounded-xl border px-3 py-1.5 text-[11px] font-semibold tracking-wide shadow-lg shadow-black/10 sm:inline-flex ${
      warning
        ? 'border-warning/25 bg-warning/10 text-warning'
        : active
          ? 'border-accent/25 bg-accent/10 text-accent'
          : 'border-white/10 bg-white/[0.035] text-foreground/55'
    }`}
  >
    <span className={active ? 'text-accent' : warning ? 'text-warning' : 'text-foreground/45'}>{icon}</span>
    <span className="truncate">{label}</span>
  </div>
);

const WindowButton = ({
  children,
  label,
  danger = false,
  onClick,
}: {
  children: React.ReactNode;
  label: string;
  danger?: boolean;
  onClick: () => void;
}) => (
  <button
    type="button"
    aria-label={label}
    title={label}
    onClick={onClick}
    className={`flex h-8 w-9 items-center justify-center rounded-md border transition-colors ${
      danger
        ? 'border-transparent text-foreground/55 hover:bg-danger/20 hover:text-danger'
        : 'border-transparent text-foreground/45 hover:border-white/10 hover:bg-white/[0.06] hover:text-white'
    }`}
  >
    {children}
  </button>
);
