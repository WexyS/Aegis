"use client";

import React from 'react';
import { AlertTriangle, Save, X } from 'lucide-react';

import { dictionaryFor } from '@/i18n';
import { proposeMemory } from '@/lib/api';
import { useOperatorStore } from '@/store/useOperatorStore';
import { useUIStore } from '@/store/useUIStore';

import { detectSecretLikeMemoryContent } from '../memoryGuard';

type MemoryCandidateFormProps = {
  initialContent?: string;
  onCreated: () => void | Promise<void>;
  onCancel: () => void;
};

export const MemoryCandidateForm = ({ initialContent = '', onCreated, onCancel }: MemoryCandidateFormProps) => {
  const language = useUIStore((state) => state.language);
  const sessionRef = useOperatorStore((state) => state.currentSessionId);
  const t = dictionaryFor(language).memory;
  const [content, setContent] = React.useState(initialContent);
  const [summary, setSummary] = React.useState('');
  const [type, setType] = React.useState('task_session_memory');
  const [scope, setScope] = React.useState<'session' | 'project' | 'repository'>('session');
  const [sensitivity, setSensitivity] = React.useState<'public' | 'internal' | 'private' | 'sensitive'>('private');
  const [projectRef, setProjectRef] = React.useState('');
  const [repositoryRef, setRepositoryRef] = React.useState('');
  const [error, setError] = React.useState<string | null>(null);
  const [submitting, setSubmitting] = React.useState(false);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    const trimmed = content.trim();
    if (!trimmed) {
      setError(t.contentRequired);
      return;
    }
    const secretReason = detectSecretLikeMemoryContent(trimmed);
    if (secretReason) {
      setError(`${t.secretBlocked} ${secretReason}`);
      return;
    }
    if ((scope === 'project' || scope === 'repository') && !projectRef.trim()) {
      setError(t.projectRefRequired);
      return;
    }
    if (scope === 'repository' && !repositoryRef.trim()) {
      setError(t.repositoryRefRequired);
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      await proposeMemory({
        type,
        content: trimmed,
        summary: summary.trim() || undefined,
        scope,
        sensitivity,
        source_refs: [{ ref_id: sessionRef, ref_type: 'operator_explicit_candidate' }],
        session_ref: scope === 'session' ? sessionRef : undefined,
        project_ref: scope === 'project' || scope === 'repository' ? projectRef.trim() : undefined,
        repository_ref: scope === 'repository' ? repositoryRef.trim() : undefined,
        metadata: { source: 'operator_memory_candidate_form', explicit_user_action: true },
      });
      await onCreated();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : t.createFailed);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={(event) => void submit(event)} className="space-y-4 rounded-lg border border-[#3b3935] bg-[#191918] p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-[#f4f1ea]">{t.candidateFormTitle}</h3>
          <p className="mt-1 text-xs leading-5 text-[#8f8b84]">{t.candidateFormCopy}</p>
        </div>
        <button type="button" onClick={onCancel} className="flex h-10 w-10 items-center justify-center rounded-md text-[#8f8b84] hover:bg-[#292825] hover:text-white" aria-label={t.cancel}>
          <X size={16} />
        </button>
      </div>

      <label className="block text-xs font-medium text-[#bdb8ae]">
        {t.content}
        <textarea value={content} onChange={(event) => setContent(event.target.value)} rows={4} className="mt-2 w-full resize-y rounded-md border border-[#3b3935] bg-[#111] px-3 py-2 text-sm leading-6 text-[#eeeae2] outline-none focus:border-[#8b7b52]" />
      </label>
      <label className="block text-xs font-medium text-[#bdb8ae]">
        {t.summary}
        <input value={summary} onChange={(event) => setSummary(event.target.value)} className="mt-2 h-10 w-full rounded-md border border-[#3b3935] bg-[#111] px-3 text-sm text-[#eeeae2] outline-none focus:border-[#8b7b52]" />
      </label>

      <div className="grid gap-3 sm:grid-cols-3">
        <label className="text-xs font-medium text-[#bdb8ae]">
          {t.type}
          <select value={type} onChange={(event) => setType(event.target.value)} className="mt-2 h-10 w-full rounded-md border border-[#3b3935] bg-[#111] px-2 text-sm text-[#eeeae2]">
            <option value="task_session_memory">task_session_memory</option>
            <option value="project_preference">project_preference</option>
            <option value="repo_memory">repo_memory</option>
            <option value="temporary_scratch">temporary_scratch</option>
          </select>
        </label>
        <label className="text-xs font-medium text-[#bdb8ae]">
          {t.scope}
          <select value={scope} onChange={(event) => setScope(event.target.value as typeof scope)} className="mt-2 h-10 w-full rounded-md border border-[#3b3935] bg-[#111] px-2 text-sm text-[#eeeae2]">
            <option value="session">session</option>
            <option value="project">project</option>
            <option value="repository">repository</option>
          </select>
        </label>
        <label className="text-xs font-medium text-[#bdb8ae]">
          {t.sensitivity}
          <select value={sensitivity} onChange={(event) => setSensitivity(event.target.value as typeof sensitivity)} className="mt-2 h-10 w-full rounded-md border border-[#3b3935] bg-[#111] px-2 text-sm text-[#eeeae2]">
            <option value="public">public</option>
            <option value="internal">internal</option>
            <option value="private">private</option>
            <option value="sensitive">sensitive</option>
          </select>
        </label>
      </div>

      {(scope === 'project' || scope === 'repository') && (
        <label className="block text-xs font-medium text-[#bdb8ae]">
          {t.projectRef}
          <input value={projectRef} onChange={(event) => setProjectRef(event.target.value)} className="mt-2 h-10 w-full rounded-md border border-[#3b3935] bg-[#111] px-3 text-sm text-[#eeeae2]" />
        </label>
      )}
      {scope === 'repository' && (
        <label className="block text-xs font-medium text-[#bdb8ae]">
          {t.repositoryRef}
          <input value={repositoryRef} onChange={(event) => setRepositoryRef(event.target.value)} className="mt-2 h-10 w-full rounded-md border border-[#3b3935] bg-[#111] px-3 text-sm text-[#eeeae2]" />
        </label>
      )}

      {error && <div role="alert" className="flex items-start gap-2 rounded-md border border-red-500/25 bg-red-500/10 p-3 text-xs leading-5 text-red-200"><AlertTriangle size={15} className="mt-0.5 shrink-0" />{error}</div>}
      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-[#302f2c] pt-4">
        <p className="max-w-xl text-xs leading-5 text-[#77736d]">{t.candidateSafety}</p>
        <button type="submit" disabled={submitting} className="inline-flex h-10 items-center gap-2 rounded-md bg-[#f1ede4] px-4 text-xs font-semibold text-[#171715] hover:bg-white disabled:cursor-not-allowed disabled:opacity-50">
          <Save size={15} /> {submitting ? t.creating : t.createCandidate}
        </button>
      </div>
    </form>
  );
};
