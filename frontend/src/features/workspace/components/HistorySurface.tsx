"use client";

import type React from 'react';
import { Clock3, History } from 'lucide-react';

import { dictionaryFor } from '@/i18n';
import { useOperatorStore } from '@/store/useOperatorStore';
import { useUIStore } from '@/store/useUIStore';

export const HistorySurface = () => {
  const language = useUIStore((state) => state.language);
  const t = dictionaryFor(language).workspace;
  const history = useOperatorStore((state) => state.sessionHistory);
  const selectArtifact = useOperatorStore((state) => state.selectArtifact);
  const setActiveTab = useUIStore((state) => state.setActiveTab);

  return (
    <WorkspacePage title={t.historyTitle} description={t.historyDescription}>
      {!history.length ? (
        <Empty icon={<History size={24} />} title={t.historyEmptyTitle} copy={t.historyEmptyCopy} />
      ) : (
        <div className="divide-y divide-[#302f2c] border-y border-[#302f2c]">
          {history.map((item) => (
            <button
              type="button"
              key={item.id}
              onClick={() => {
                selectArtifact(item.artifactId);
                setActiveTab('Outputs');
              }}
              className="flex min-h-16 w-full items-center gap-4 px-1 py-3 text-left hover:bg-[#191918] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[#f4bf4f]"
            >
              <Clock3 size={16} className="shrink-0 text-[#8b877f]" />
              <span className="min-w-0 flex-1">
                <span className="block truncate text-sm font-medium text-[#ece9e2]">{item.request}</span>
                <span className="mt-1 block truncate text-xs text-[#817d76]">{item.artifactTitle}</span>
              </span>
              <time className="shrink-0 text-xs text-[#817d76]">
                {new Intl.DateTimeFormat(language === 'tr' ? 'tr-TR' : 'en-US', { hour: '2-digit', minute: '2-digit' }).format(new Date(item.createdAt))}
              </time>
            </button>
          ))}
        </div>
      )}
      <TruthNote>{t.sessionOnlyNote}</TruthNote>
    </WorkspacePage>
  );
};

export const WorkspacePage = ({ title, description, children }: { title: string; description: string; children: React.ReactNode }) => (
  <div className="h-full overflow-y-auto bg-[#131313] px-5 py-8 custom-scrollbar sm:px-8 lg:px-12">
    <div className="mx-auto w-full max-w-5xl">
      <h2 className="text-2xl font-semibold text-[#f4f1ea]">{title}</h2>
      <p className="mt-2 max-w-2xl text-sm leading-6 text-[#8f8b84]">{description}</p>
      <div className="mt-8">{children}</div>
    </div>
  </div>
);

export const Empty = ({ icon, title, copy }: { icon: React.ReactNode; title: string; copy: string }) => (
  <div className="flex min-h-72 flex-col items-center justify-center text-center">
    <div className="flex h-12 w-12 items-center justify-center rounded-lg border border-[#3a3834] bg-[#1d1d1c] text-[#f4bf4f]">{icon}</div>
    <h3 className="mt-4 text-lg font-semibold text-[#ece9e2]">{title}</h3>
    <p className="mt-2 max-w-md text-sm leading-6 text-[#85817a]">{copy}</p>
  </div>
);

export const TruthNote = ({ children }: { children: React.ReactNode }) => (
  <p className="mt-6 border-l-2 border-[#5b5039] pl-3 text-xs leading-5 text-[#77736d]">{children}</p>
);
