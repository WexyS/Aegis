"use client";

import React from 'react';
import { AlertTriangle, Archive, Check, Database, Inbox, Loader2, Plus, RefreshCw, ShieldCheck, Trash2, X } from 'lucide-react';

import { StatusBadge } from '@/components/StatusBadge';
import { MemoryCandidateForm } from '@/features/workspace/components/MemoryCandidateForm';
import { dictionaryFor } from '@/i18n';
import { approveMemory, deleteMemory, listMemories, rejectMemory } from '@/lib/api';
import { useUIStore } from '@/store/useUIStore';
import type { MemoryItem, StatusTone } from '@/types/rc';

const STATUS_ORDER = ['proposed', 'active', 'rejected', 'deleted'] as const;

export const MemoryOverviewPanel = () => {
  const language = useUIStore((state) => state.language);
  const t = dictionaryFor(language).memory;
  const [memories, setMemories] = React.useState<MemoryItem[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [busyId, setBusyId] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [notice, setNotice] = React.useState<string | null>(null);
  const [showDeleted, setShowDeleted] = React.useState(false);
  const [showCreate, setShowCreate] = React.useState(false);
  const [deleteConfirmation, setDeleteConfirmation] = React.useState<string | null>(null);

  const refresh = React.useCallback(async (includeDeleted: boolean) => {
    setLoading(true);
    setError(null);
    try {
      const response = await listMemories({ include_deleted: includeDeleted });
      setMemories(response.memories ?? []);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : t.loadFailed);
    } finally {
      setLoading(false);
    }
  }, [t.loadFailed]);

  React.useEffect(() => {
    void refresh(false);
  }, [refresh]);

  const toggleDeleted = async (checked: boolean) => {
    setShowDeleted(checked);
    await refresh(checked);
  };

  const transition = async (memory: MemoryItem, action: 'approve' | 'reject' | 'delete') => {
    setBusyId(memory.id);
    setError(null);
    setNotice(null);
    try {
      if (action === 'approve') await approveMemory(memory.id);
      if (action === 'reject') await rejectMemory(memory.id, 'Rejected explicitly from Memory Inbox');
      if (action === 'delete') await deleteMemory(memory.id);
      setDeleteConfirmation(null);
      setNotice(t.actionCompleted.replace('{action}', t.actions[action]));
      await refresh(showDeleted);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : t.actionFailed);
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="h-full min-h-0 overflow-y-auto bg-[#131313] custom-scrollbar">
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-5 p-4 pb-12 sm:p-6 lg:p-8">
        <header className="flex flex-col justify-between gap-4 border-b border-[#302f2c] pb-6 sm:flex-row sm:items-end">
          <div className="max-w-3xl">
            <div className="flex items-center gap-2 text-xs font-semibold text-[#f4bf4f]"><Database size={15} />{t.eyebrow}</div>
            <h1 className="mt-3 text-3xl font-semibold text-[#f4f1ea]">{t.inboxTitle}</h1>
            <p className="mt-2 text-sm leading-6 text-[#8f8b84]">{t.inboxSubtitle}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button type="button" onClick={() => void refresh(showDeleted)} className="inline-flex h-10 items-center gap-2 rounded-md px-3 text-xs text-[#aaa59c] hover:bg-[#242321] hover:text-white"><RefreshCw size={15} className={loading ? 'animate-spin' : ''} />{t.refresh}</button>
            <button type="button" onClick={() => setShowCreate((value) => !value)} className="inline-flex h-10 items-center gap-2 rounded-md bg-[#f1ede4] px-4 text-xs font-semibold text-[#171715] hover:bg-white"><Plus size={15} />{t.createCandidate}</button>
          </div>
        </header>

        <div className="flex flex-col justify-between gap-3 rounded-md border border-[#34322f] bg-[#181817] p-3 text-xs text-[#aaa59c] sm:flex-row sm:items-center">
          <span className="flex items-start gap-2 leading-5"><ShieldCheck size={15} className="mt-0.5 shrink-0 text-[#f4bf4f]" />{t.activeBoundary}</span>
          <label className="flex shrink-0 cursor-pointer items-center gap-2">
            <input type="checkbox" checked={showDeleted} onChange={(event) => void toggleDeleted(event.target.checked)} />
            {t.showDeleted}
          </label>
        </div>

        {showCreate && <MemoryCandidateForm onCancel={() => setShowCreate(false)} onCreated={async () => { setShowCreate(false); setNotice(t.candidateCreated); await refresh(showDeleted); }} />}
        {error && <div role="alert" className="flex items-start gap-2 rounded-md border border-red-500/25 bg-red-500/10 p-3 text-xs leading-5 text-red-200"><AlertTriangle size={15} className="mt-0.5 shrink-0" />{error}</div>}
        {notice && <div role="status" className="rounded-md border border-emerald-500/20 bg-emerald-500/[0.06] p-3 text-xs text-emerald-100">{notice}</div>}

        {loading && memories.length === 0 ? (
          <div role="status" aria-live="polite" className="flex min-h-48 items-center justify-center gap-2 text-sm text-[#8f8b84]"><Loader2 size={17} className="animate-spin" />{t.loading}</div>
        ) : memories.length === 0 ? (
          <div role="status" className="flex min-h-52 flex-col items-center justify-center border border-dashed border-[#34322f] px-5 text-center">
            <Inbox size={24} className="text-[#77736d]" />
            <h2 className="mt-4 text-base font-semibold text-[#e7e2d9]">{t.emptyTitle}</h2>
            <p className="mt-2 max-w-md text-sm leading-6 text-[#77736d]">{t.emptyCopy}</p>
          </div>
        ) : (
          <div className="space-y-7">
            {STATUS_ORDER.map((status) => {
              const items = memories.filter((memory) => memory.status === status);
              if (items.length === 0 || (status === 'deleted' && !showDeleted)) return null;
              return (
                <section key={status} aria-labelledby={`memory-${status}`}>
                  <div className="mb-3 flex items-center gap-2">
                    <MemoryStatusIcon status={status} />
                    <h2 id={`memory-${status}`} className="text-sm font-semibold capitalize text-[#e7e2d9]">{t.states[status]}</h2>
                    <span className="text-xs text-[#77736d]">{items.length}</span>
                  </div>
                  <div className="space-y-3">
                    {items.map((memory) => (
                      <MemoryInboxItem
                        key={memory.id}
                        memory={memory}
                        language={language}
                        busy={busyId === memory.id}
                        confirmDelete={deleteConfirmation === memory.id}
                        onApprove={() => void transition(memory, 'approve')}
                        onReject={() => void transition(memory, 'reject')}
                        onDelete={() => setDeleteConfirmation(memory.id)}
                        onCancelDelete={() => setDeleteConfirmation(null)}
                        onConfirmDelete={() => void transition(memory, 'delete')}
                      />
                    ))}
                  </div>
                </section>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

const MemoryInboxItem = ({ memory, language, busy, confirmDelete, onApprove, onReject, onDelete, onCancelDelete, onConfirmDelete }: {
  memory: MemoryItem;
  language: 'en' | 'tr';
  busy: boolean;
  confirmDelete: boolean;
  onApprove: () => void;
  onReject: () => void;
  onDelete: () => void;
  onCancelDelete: () => void;
  onConfirmDelete: () => void;
}) => {
  const t = dictionaryFor(language).memory;
  const refs = (memory.source_refs ?? []).map((ref) => String(ref.ref_id ?? ref.ref ?? '')).filter(Boolean);
  const deleteButtonRef = React.useRef<HTMLButtonElement>(null);
  const cancelDeleteButtonRef = React.useRef<HTMLButtonElement>(null);
  const accessibleName = memory.content_summary || memory.id;

  React.useEffect(() => {
    if (confirmDelete) cancelDeleteButtonRef.current?.focus();
  }, [confirmDelete]);

  const cancelDelete = () => {
    onCancelDelete();
    window.requestAnimationFrame(() => deleteButtonRef.current?.focus());
  };

  return (
    <article className="rounded-lg border border-[#34322f] bg-[#181817] p-4">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge label={memory.status} tone={toneForStatus(memory.status)} />
            <span className="text-[11px] text-[#77736d]">{memory.type} · {memory.scope} · {memory.sensitivity}</span>
          </div>
          <h3 className="mt-3 break-words text-sm font-semibold text-[#eeeae2]">{memory.content_summary || t.noSummary}</h3>
          <p className="mt-2 max-h-28 overflow-y-auto whitespace-pre-wrap break-words text-sm leading-6 text-[#aaa59c] custom-scrollbar">{memory.content}</p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-1">
          {memory.status === 'proposed' && <>
            <button type="button" disabled={busy} onClick={onApprove} aria-label={t.approveCandidateLabel.replace('{candidate}', accessibleName)} className="flex h-10 items-center gap-2 rounded-md px-3 text-xs text-emerald-200 hover:bg-emerald-500/10"><Check size={14} />{t.actions.approve}</button>
            <button type="button" disabled={busy} onClick={onReject} aria-label={t.rejectCandidateLabel.replace('{candidate}', accessibleName)} className="flex h-10 items-center gap-2 rounded-md px-3 text-xs text-amber-200 hover:bg-amber-500/10"><X size={14} />{t.actions.reject}</button>
          </>}
          {memory.status !== 'deleted' && <button ref={deleteButtonRef} type="button" disabled={busy} onClick={onDelete} aria-label={t.deleteCandidateLabel.replace('{candidate}', accessibleName)} className="flex h-10 items-center gap-2 rounded-md px-3 text-xs text-red-200 hover:bg-red-500/10"><Trash2 size={14} />{t.actions.delete}</button>}
        </div>
      </div>
      <dl className="mt-4 grid gap-2 border-t border-[#302f2c] pt-3 text-[11px] text-[#77736d] sm:grid-cols-2">
        <div><dt className="inline">ID: </dt><dd className="inline break-all text-[#9e9990]">{memory.id}</dd></div>
        <div><dt className="inline">{t.updated}: </dt><dd className="inline text-[#9e9990]">{formatTimestamp(memory.updated_at, language)}</dd></div>
        <div className="sm:col-span-2"><dt className="inline">{t.sourceRefs}: </dt><dd className="inline break-all text-[#9e9990]">{refs.length ? refs.join(', ') : t.noSourceRefs}</dd></div>
      </dl>
      {confirmDelete && <div role="group" aria-label={t.deleteConfirmationLabel.replace('{candidate}', accessibleName)} className="mt-4 flex flex-col justify-between gap-3 rounded-md border border-red-500/25 bg-red-500/[0.06] p-3 text-xs text-red-100 sm:flex-row sm:items-center"><span>{t.deleteConfirm}</span><div className="flex gap-2"><button ref={cancelDeleteButtonRef} type="button" onClick={cancelDelete} className="h-9 rounded-md px-3 hover:bg-white/5">{t.cancel}</button><button type="button" onClick={onConfirmDelete} className="h-9 rounded-md bg-red-500/20 px-3 font-semibold hover:bg-red-500/30">{t.confirmDelete}</button></div></div>}
    </article>
  );
};

function formatTimestamp(value: number | undefined, language: 'en' | 'tr'): string {
  if (!value) return 'unknown';
  return new Intl.DateTimeFormat(language === 'tr' ? 'tr-TR' : 'en-US', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value * 1000));
}

function toneForStatus(status: string): StatusTone {
  if (status === 'active') return 'success';
  if (status === 'proposed') return 'warning';
  if (status === 'rejected') return 'danger';
  return 'unknown';
}

const MemoryStatusIcon = ({ status }: { status: string }) => {
  if (status === 'active') return <ShieldCheck size={16} className="text-emerald-300" />;
  if (status === 'rejected') return <X size={16} className="text-red-300" />;
  if (status === 'deleted') return <Archive size={16} className="text-[#77736d]" />;
  return <Inbox size={16} className="text-[#f4bf4f]" />;
};
