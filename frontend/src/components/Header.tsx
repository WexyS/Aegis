"use client";

import React from 'react';
import { Maximize2, Minimize2, PanelRight, Settings, ShieldCheck, Square, X } from 'lucide-react';

import { dictionaryFor } from '@/i18n';
import { useUIStore } from '@/store/useUIStore';

export const Header = () => {
  const language = useUIStore((state) => state.language);
  const activeTab = useUIStore((state) => state.activeTab);
  const setActiveTab = useUIStore((state) => state.setActiveTab);
  const toggleInspector = useUIStore((state) => state.toggleInspector);
  const isInspectorOpen = useUIStore((state) => state.isInspectorOpen);
  const t = dictionaryFor(language);
  const [isElectron, setIsElectron] = React.useState(false);

  React.useEffect(() => {
    setIsElectron(Boolean(window.aegis?.isElectron && window.aegis.windowAction));
  }, []);

  const sendWindowAction = React.useCallback((action: 'minimize' | 'toggle-maximize' | 'toggle-fullscreen' | 'close') => {
    window.aegis?.windowAction?.(action);
  }, []);

  return (
    <header className="electron-drag-region relative z-40 flex h-14 shrink-0 items-center justify-between gap-3 border-b border-[#2b2a28] bg-[#151515] px-3 sm:px-4 lg:px-5">
      <div className="flex min-w-0 items-center gap-3">
        <h1 className="truncate text-sm font-semibold text-[#f4f1ea]">{surfaceLabel(activeTab, t.nav)}</h1>
        <span className="hidden items-center gap-1.5 text-xs text-[#8d8a84] sm:inline-flex">
          <ShieldCheck size={13} className="text-[#f4bf4f]" />
          {t.header.localFirstPreview}
        </span>
      </div>

      <div className="electron-no-drag flex shrink-0 items-center gap-1">
        {activeTab === 'Operator' && (
          <WindowButton
            id="operator-context-trigger"
            label={t.header.context}
            onClick={toggleInspector}
            ariaExpanded={isInspectorOpen}
            ariaControls="operator-context-drawer"
          >
            <PanelRight size={15} />
          </WindowButton>
        )}
        <WindowButton label={t.nav.settings} onClick={() => setActiveTab('Settings')}>
          <Settings size={15} />
        </WindowButton>
        {isElectron && (
          <>
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
          </>
        )}
      </div>
    </header>
  );
};

function surfaceLabel(activeTab: string, nav: ReturnType<typeof dictionaryFor>['nav']): string {
  const labels: Record<string, string> = {
    Operator: nav.operator,
    History: nav.history,
    Projects: nav.projects,
    Outputs: nav.outputs,
    Memory: nav.memory,
    Customize: nav.customize,
    Settings: nav.settings,
    Skills: nav.skills,
    Advanced: nav.advancedTools,
  };
  return labels[activeTab] ?? nav.operator;
}

const WindowButton = ({
  children,
  label,
  danger = false,
  onClick,
  id,
  ariaExpanded,
  ariaControls,
}: {
  children: React.ReactNode;
  label: string;
  danger?: boolean;
  onClick: () => void;
  id?: string;
  ariaExpanded?: boolean;
  ariaControls?: string;
}) => (
  <button
    id={id}
    type="button"
    aria-label={label}
    title={label}
    onClick={onClick}
    aria-expanded={ariaExpanded}
    aria-controls={ariaControls}
    className={`flex h-10 w-10 items-center justify-center rounded-md border transition-colors ${
      danger
        ? 'border-transparent text-[#9b9891] hover:bg-[#4c2020] hover:text-[#ffd6d6]'
        : 'border-transparent text-[#9b9891] hover:border-[#383632] hover:bg-[#232321] hover:text-[#f4f1ea]'
    }`}
  >
    {children}
  </button>
);
