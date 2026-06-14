"use client";

import React from 'react';
import { Database, Eye, Globe2, Moon, Radio, Settings2, ShieldCheck } from 'lucide-react';

import { dictionaryFor } from '@/i18n';
import type { Language } from '@/i18n';
import { StatusBadge } from '@/components/StatusBadge';
import { useUIStore } from '@/store/useUIStore';

export const SettingsPanel = () => {
  const language = useUIStore((state) => state.language);
  const density = useUIStore((state) => state.density);
  const setLanguage = useUIStore((state) => state.setLanguage);
  const setDensity = useUIStore((state) => state.setDensity);
  const t = dictionaryFor(language);

  return (
    <div className="h-full min-h-0 overflow-y-auto custom-scrollbar">
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-5 p-5 lg:p-8">
        <section className="rounded-2xl border border-white/10 bg-white/[0.04] p-5 shadow-2xl shadow-black/25">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.2em] text-secondary-light">
                <Settings2 size={15} />
                {t.settings.title}
              </div>
              <p className="mt-3 max-w-3xl text-sm leading-7 text-foreground/58">{t.settings.subtitle}</p>
            </div>
            <StatusBadge label={t.settings.persistedLocally} tone="unknown" className="shrink-0" />
          </div>
        </section>

        <div className="grid gap-5 lg:grid-cols-2">
          <SettingsCard icon={<Globe2 size={18} />} title={t.settings.language}>
            <SegmentedControl
              value={language}
              options={[
                { value: 'en', label: t.settings.english },
                { value: 'tr', label: t.settings.turkish },
              ]}
              onChange={(value) => setLanguage(value as Language)}
            />
          </SettingsCard>

          <SettingsCard icon={<Moon size={18} />} title={t.settings.appearance}>
            <div className="grid gap-2 sm:grid-cols-3">
              <StaticOption label={t.settings.dark} active />
              <button
                type="button"
                onClick={() => setDensity('comfortable')}
                className={optionClass(density === 'comfortable')}
              >
                {t.settings.comfortable}
              </button>
              <button
                type="button"
                onClick={() => setDensity('compact')}
                className={optionClass(density === 'compact')}
              >
                {t.settings.compact}
              </button>
            </div>
          </SettingsCard>

          <SettingsCard icon={<ShieldCheck size={18} />} title={t.settings.privacy}>
            <TruthRows
              rows={[
                [t.settings.externalApisOff, t.truth.externalOff],
                [t.settings.localMemory, t.truth.localLifecycle],
                [t.settings.dataPreview, t.truth.approvalRequired],
              ]}
            />
          </SettingsCard>

          <SettingsCard icon={<Radio size={18} />} title={t.settings.modelBoundaries}>
            <TruthRows
              rows={[
                [t.settings.localModelBoundary, t.truth.proposalOnly],
                [t.settings.externalProvidersDisabled, t.truth.externalOff],
                [t.settings.advancedDiagnostics, t.truth.readOnly],
              ]}
            />
          </SettingsCard>
        </div>

        <section className="rounded-2xl border border-warning/20 bg-warning/[0.04] p-5">
          <div className="flex items-start gap-3">
            <Database size={18} className="mt-1 shrink-0 text-warning" />
            <p className="text-sm leading-7 text-foreground/62">
              {language === 'tr'
                ? 'Bu ayarlar yalnızca arayüz davranışını etkiler. Hafızaya yazma, model çağırma, harici API kullanma veya onay verme yetkisi oluşturmaz.'
                : 'These settings only affect the interface. They do not write memory, call models, use external APIs, or grant approval authority.'}
            </p>
          </div>
        </section>
      </div>
    </div>
  );
};

const SettingsCard = ({
  icon,
  title,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  children: React.ReactNode;
}) => (
  <section className="rounded-2xl border border-white/10 bg-white/[0.035] p-5 shadow-xl shadow-black/15">
    <div className="mb-4 flex items-center gap-3">
      <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-secondary/25 bg-secondary/[0.10] text-secondary-light">
        {icon}
      </div>
      <h2 className="text-lg font-semibold text-white">{title}</h2>
    </div>
    {children}
  </section>
);

const SegmentedControl = ({
  value,
  options,
  onChange,
}: {
  value: string;
  options: Array<{ value: string; label: string }>;
  onChange: (value: string) => void;
}) => (
  <div className="grid gap-2 sm:grid-cols-2">
    {options.map((option) => (
      <button
        key={option.value}
        type="button"
        onClick={() => onChange(option.value)}
        className={optionClass(value === option.value)}
      >
        {option.label}
      </button>
    ))}
  </div>
);

const StaticOption = ({ label, active = false }: { label: string; active?: boolean }) => (
  <div className={optionClass(active)}>
    <Eye size={14} />
    {label}
  </div>
);

const TruthRows = ({ rows }: { rows: Array<[string, string]> }) => (
  <div className="space-y-2">
    {rows.map(([label, value]) => (
      <div key={label} className="flex items-center justify-between gap-3 rounded-xl border border-white/10 bg-black/20 px-3 py-2.5">
        <span className="text-sm text-foreground/70">{label}</span>
        <StatusBadge label={value} tone="unknown" className="shrink-0" />
      </div>
    ))}
  </div>
);

function optionClass(active: boolean): string {
  return `inline-flex min-h-[44px] items-center justify-center gap-2 rounded-xl border px-3 py-2 text-sm font-semibold transition-colors ${
    active
      ? 'border-secondary/35 bg-secondary/[0.16] text-white shadow-[0_0_22px_rgba(139,92,246,0.18)]'
      : 'border-white/10 bg-white/[0.035] text-foreground/55 hover:border-white/20 hover:text-white'
  }`;
}
