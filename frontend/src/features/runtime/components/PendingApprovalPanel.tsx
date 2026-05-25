"use client";

import React, { useRef, useState } from 'react';
import { Ban, Check, ShieldAlert, Square } from 'lucide-react';

import { EmptyState } from '@/components/EmptyState';
import { resolveApprovalDecision, resolveClarificationDecision } from '@/lib/api';
import { cancelCommand } from '@/lib/socket';
import { useRuntimeStore } from '@/store/useRuntimeStore';
import {
  CommandRecord,
  MaintenanceActionProposal,
} from '@/types/runtime';

export const PendingApprovalPanel = () => {
  const pendingApprovals = useRuntimeStore((state) => state.pendingApprovals);
  const pendingClarifications = useRuntimeStore((state) => state.pendingClarifications);
  const commandRecords = useRuntimeStore((state) => state.commandRecords);
  const activeCommand = useRuntimeStore((state) => state.activeCommand);
  const resolvedDecisionRecords = commandRecords
    .filter((command) => hasResolutionMetadata(command))
    .slice(-4)
    .reverse();

  return (
    <section className="space-y-4">
      <div className="flex items-center gap-3">
        <h3 className="text-[10px] font-bold uppercase tracking-[0.2em] text-accent flex items-center gap-2">
          <ShieldAlert size={12} /> Pending Decisions
        </h3>
      </div>

      <div className="space-y-3">
        {pendingApprovals.length === 0 && pendingClarifications.length === 0 ? (
          <EmptyState title="No backend pending decisions" detail="Approval and clarification state is shown only from backend command records." icon={<ShieldAlert size={14} />} />
        ) : (
          <>
            {pendingApprovals.map((command) => (
              <ApprovalItem key={command.command_id} command={command} />
            ))}
            {pendingClarifications.map((command) => (
              <ClarificationItem key={command.command_id} command={command} />
            ))}
          </>
        )}
      </div>

      {resolvedDecisionRecords.length > 0 && (
        <div className="rounded-lg border border-white/10 bg-black/20 p-3 space-y-2">
          <div className="text-[9px] font-bold uppercase tracking-widest text-foreground/40">Recent Decision Results</div>
          {resolvedDecisionRecords.map((command) => (
            <ResolvedDecisionItem key={`${command.command_id}-${String(command.updated_at ?? command.status)}`} command={command} />
          ))}
        </div>
      )}

      {activeCommand && (
        <div className="rounded-lg border border-warning/20 bg-warning/5 p-3 space-y-3">
          <div className="min-w-0">
            <div className="text-[9px] font-bold uppercase tracking-widest text-warning">Active Command</div>
            <div className="mt-1 truncate text-[12px] font-medium text-foreground/80">{activeCommand.text}</div>
          </div>
          <button
            type="button"
            onClick={() => cancelCommand(activeCommand.command_id)}
            className="w-full flex items-center justify-center gap-2 rounded-md border border-danger/30 bg-danger/10 px-3 py-2 text-[10px] font-bold uppercase tracking-widest text-danger hover:bg-danger/15 transition-colors"
          >
            <Square size={12} /> Cancel
          </button>
        </div>
      )}
    </section>
  );
};

const ApprovalItem = React.memo(({ command }: { command: CommandRecord }) => {
  const upsertCommand = useRuntimeStore((state) => state.upsertCommand);
  const addLog = useRuntimeStore((state) => state.addLog);
  const [resolving, setResolving] = useState<'grant' | 'deny' | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inFlightRef = useRef(false);
  const proposal = getMaintenanceProposalFromCommand(command);
  const resources = Array.isArray(proposal?.affected_resources) ? proposal.affected_resources : [];
  const evidenceRefs = Array.isArray(proposal?.evidence_refs) ? proposal.evidence_refs : [];
  const approvalId = getMetadataString(command, 'approval_id') || command.command_id;
  const resumeAllowed = command.metadata?.resume_allowed === true;
  const nonExecutable = command.metadata?.resume_allowed === false || isQuarantinedClickDecision(command);
  const isPending = command.status === 'pending_approval';
  const controlsDisabled = resolving !== null || !isPending;

  const resolve = async (decision: 'grant' | 'deny') => {
    if (inFlightRef.current || resolving !== null) return;
    if (!isPending) {
      setError(`Approval is no longer pending: ${command.status}`);
      return;
    }
    inFlightRef.current = true;
    setResolving(decision);
    setError(null);
    try {
      const updated = await resolveApprovalDecision(approvalId, decision);
      upsertCommand(updated);
      addLog({
        level: decision === 'grant' ? 'INFO' : 'WARN',
        message: decision === 'grant'
          ? `Approval grant recorded by backend: ${updated.status}`
          : `Approval denied: ${updated.reason || 'operator decision'}`,
        color: decision === 'grant' ? 'text-accent' : 'text-warning',
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Approval resolve failed';
      setError(message);
      addLog({ level: 'ERR', message: `Approval resolve failed: ${message}`, color: 'text-danger' });
    } finally {
      inFlightRef.current = false;
      setResolving(null);
    }
  };

  return (
    <div className={`rounded-lg border p-3 space-y-3 ${riskBorderStyle(command.risk_level)}`}>
      <div className="space-y-1">
        <div className="flex items-center justify-between gap-3">
          <span className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${riskBadgeStyle(command.risk_level)}`}>{command.risk_level} risk</span>
          <span className="text-[9px] font-mono text-foreground/35">{command.verification_state}</span>
        </div>
        <p className="text-[12px] font-medium leading-relaxed text-foreground/85">{command.text}</p>
        {command.reason && <p className="text-[10px] font-mono text-foreground/45">{command.reason}</p>}
        <div className="rounded-md border border-white/10 bg-black/15 px-2 py-1.5 text-[9px] font-mono leading-relaxed text-foreground/45">
          <div className="flex items-center justify-between gap-2">
            <span className="truncate">approval id: {approvalId}</span>
            <span className={resumeAllowed ? 'text-warning' : 'text-foreground/45'}>
              {resumeAllowed ? 'backend-gated state update' : 'state-only / non-executing'}
            </span>
          </div>
          {nonExecutable && (
            <p className="mt-1 text-warning/80">
              Grant records the decision only; quarantined or unresolved click actions are not executed by this control.
            </p>
          )}
          {!isPending && (
            <p className="mt-1 text-warning/80">
              This approval is no longer pending; controls are disabled until the backend snapshot changes.
            </p>
          )}
        </div>
        {proposal && (
          <div className="rounded-md border border-white/10 bg-black/15 px-2 py-1.5">
            <div className="flex items-center justify-between gap-2 text-[9px] font-mono">
              <span className="truncate text-foreground/55">{proposal.action}</span>
              <span className="text-warning">{proposal.status}</span>
            </div>
            <p className="mt-1 line-clamp-2 text-[9px] font-mono leading-relaxed text-foreground/60">{proposal.reason}</p>
            {resources.length > 0 && (
              <p className="mt-1 truncate text-[8px] font-mono text-foreground/35">
                {resources.map((resource) => String(resource.path ?? resource.type ?? 'resource')).join(', ')}
              </p>
            )}
            {evidenceRefs.length > 0 && (
              <p className="mt-1 truncate text-[8px] font-mono text-foreground/35">{evidenceRefs.join(', ')}</p>
            )}
            <ProposalPreviewDetails proposal={proposal} compact />
          </div>
        )}
        {error && (
          <p className="rounded-md border border-danger/30 bg-danger/10 px-2 py-1.5 text-[9px] font-mono text-danger">
            {error}
          </p>
        )}
      </div>
      <div className="grid grid-cols-2 gap-2">
        <button
          type="button"
          onClick={() => void resolve('grant')}
          disabled={controlsDisabled}
          aria-busy={resolving === 'grant'}
          className="flex items-center justify-center gap-2 rounded-md border border-success/30 bg-success/10 px-3 py-2 text-[10px] font-bold uppercase tracking-widest text-success hover:bg-success/15 disabled:cursor-not-allowed disabled:opacity-50 transition-colors"
        >
          <Check size={12} /> {resolving === 'grant' ? 'Resolving' : 'Grant'}
        </button>
        <button
          type="button"
          onClick={() => void resolve('deny')}
          disabled={controlsDisabled}
          aria-busy={resolving === 'deny'}
          className="flex items-center justify-center gap-2 rounded-md border border-white/10 bg-white/[0.03] px-3 py-2 text-[10px] font-bold uppercase tracking-widest text-foreground/55 hover:text-danger hover:border-danger/30 disabled:cursor-not-allowed disabled:opacity-50 transition-colors"
        >
          <Ban size={12} /> {resolving === 'deny' ? 'Resolving' : 'Deny'}
        </button>
      </div>
    </div>
  );
});

ApprovalItem.displayName = 'ApprovalItem';

const ClarificationItem = React.memo(({ command }: { command: CommandRecord }) => {
  const upsertCommand = useRuntimeStore((state) => state.upsertCommand);
  const addLog = useRuntimeStore((state) => state.addLog);
  const [answer, setAnswer] = useState('');
  const [resolving, setResolving] = useState<'submit' | 'cancel' | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inFlightRef = useRef(false);
  const clarificationId = getMetadataString(command, 'clarification_id') || command.command_id;
  const isPending = command.status === 'waiting_for_clarification';
  const hasAnswer = answer.trim().length > 0;

  const resolve = async (mode: 'submit' | 'cancel') => {
    if (inFlightRef.current || resolving !== null) return;
    if (!isPending) {
      setError(`Clarification is no longer pending: ${command.status}`);
      return;
    }
    if (mode === 'submit' && !hasAnswer) {
      setError('Enter a clarification response before resolving, or cancel the clarification.');
      return;
    }
    inFlightRef.current = true;
    setResolving(mode);
    setError(null);
    try {
      const updated = await resolveClarificationDecision(clarificationId, {
        answer: mode === 'submit' ? answer.trim() : undefined,
        cancelled: mode === 'cancel',
      });
      upsertCommand(updated);
      addLog({
        level: 'WARN',
        message: `Clarification ${mode === 'cancel' ? 'cancelled' : 'resolved'} without execution: ${updated.status}`,
        color: 'text-warning',
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Clarification resolve failed';
      setError(message);
      addLog({ level: 'ERR', message: `Clarification resolve failed: ${message}`, color: 'text-danger' });
    } finally {
      inFlightRef.current = false;
      setResolving(null);
    }
  };

  return (
    <div className={`rounded-lg border p-3 space-y-3 ${riskBorderStyle(command.risk_level)}`}>
      <div className="space-y-1">
        <div className="flex items-center justify-between gap-3">
          <span className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${riskBadgeStyle(command.risk_level)}`}>{command.risk_level} risk</span>
          <span className="text-[9px] font-mono text-warning">clarification</span>
        </div>
        <p className="text-[12px] font-medium leading-relaxed text-foreground/85">{command.text}</p>
        {command.reason && <p className="text-[10px] font-mono text-foreground/45">{command.reason}</p>}
        <div className="rounded-md border border-warning/20 bg-warning/[0.04] px-2 py-1.5 text-[9px] font-mono leading-relaxed text-warning/80">
          Clarification resolve is state-only in backend v1. Submitting an answer records the decision and does not reparse or execute the command.
        </div>
        {!isPending && (
          <p className="rounded-md border border-warning/20 bg-warning/[0.04] px-2 py-1.5 text-[9px] font-mono text-warning/80">
            This clarification is no longer pending; controls are disabled until the backend snapshot changes.
          </p>
        )}
        <textarea
          value={answer}
          onChange={(event) => setAnswer(event.target.value)}
          placeholder="Clarification response"
          disabled={resolving !== null || !isPending}
          className="min-h-[72px] w-full resize-y rounded-md border border-white/10 bg-black/20 px-2 py-2 text-[11px] text-foreground/80 outline-none placeholder:text-foreground/30 focus:border-accent/40"
        />
        {!hasAnswer && isPending && (
          <p className="text-[9px] font-mono text-foreground/40">
            Enter a response to resolve, or cancel the clarification without execution.
          </p>
        )}
        {error && (
          <p className="rounded-md border border-danger/30 bg-danger/10 px-2 py-1.5 text-[9px] font-mono text-danger">
            {error}
          </p>
        )}
      </div>
      <div className="grid grid-cols-2 gap-2">
        <button
          type="button"
          onClick={() => void resolve('submit')}
          disabled={resolving !== null || !isPending || !hasAnswer}
          aria-busy={resolving === 'submit'}
          className="flex items-center justify-center gap-2 rounded-md border border-warning/30 bg-warning/10 px-3 py-2 text-[10px] font-bold uppercase tracking-widest text-warning hover:bg-warning/15 disabled:cursor-not-allowed disabled:opacity-50 transition-colors"
        >
          <Check size={12} /> {resolving === 'submit' ? 'Resolving' : 'Submit'}
        </button>
        <button
          type="button"
          onClick={() => void resolve('cancel')}
          disabled={resolving !== null || !isPending}
          aria-busy={resolving === 'cancel'}
          className="flex items-center justify-center gap-2 rounded-md border border-white/10 bg-white/[0.03] px-3 py-2 text-[10px] font-bold uppercase tracking-widest text-foreground/55 hover:text-danger hover:border-danger/30 disabled:cursor-not-allowed disabled:opacity-50 transition-colors"
        >
          <Ban size={12} /> {resolving === 'cancel' ? 'Resolving' : 'Cancel'}
        </button>
      </div>
    </div>
  );
});

ClarificationItem.displayName = 'ClarificationItem';

const ResolvedDecisionItem = ({ command }: { command: CommandRecord }) => {
  const approvalStatus = getMetadataString(command, 'approval_resolution_status');
  const clarificationStatus = getMetadataString(command, 'clarification_resolution_status');
  const status = approvalStatus || clarificationStatus || command.status;
  const tone = command.status === 'rejected' || command.status === 'cancelled' || command.status === 'blocked' ? 'text-warning' : 'text-foreground/70';
  const mutationLabel = Object.prototype.hasOwnProperty.call(command.metadata ?? {}, 'mutation_performed')
    ? String(command.metadata?.mutation_performed)
    : 'Unavailable';

  return (
    <div className="rounded-md border border-white/10 bg-white/[0.02] px-2 py-1.5">
      <div className="flex items-center justify-between gap-2 text-[9px] font-mono">
        <span className="truncate text-foreground/55">{command.text}</span>
        <span className={tone}>{status}</span>
      </div>
      <p className="mt-1 truncate text-[8px] font-mono text-foreground/35">
        {command.status} / mutation={mutationLabel} / {command.command_id}
      </p>
    </div>
  );
};

const ProposalPreviewDetails = ({ proposal, compact = false }: { proposal: MaintenanceActionProposal; compact?: boolean }) => {
  const preview = getRecord(proposal.dry_run_preview);
  const resources = Array.isArray(proposal.affected_resources) ? proposal.affected_resources : [];
  const evidenceRefs = Array.isArray(proposal.evidence_refs) ? proposal.evidence_refs : [];
  const safetyGate = getRecord(proposal.safety_gate);
  const mutationIfApproved = getRecord(preview?.mutation_if_approved);
  const expectedOutcome = getRecord(proposal.expected_outcome);
  const preconditions = Array.isArray(preview?.preconditions) ? preview.preconditions : [];
  const target = String(preview?.target ?? mutationIfApproved?.path ?? resources[0]?.path ?? '');
  const operation = String(preview?.operation ?? mutationIfApproved?.operation ?? resources[0]?.operation ?? '');
  const previewVersion = typeof preview?.preview_version === 'string' ? preview.preview_version : null;
  const gateVersion = typeof safetyGate?.gate_version === 'string' ? safetyGate.gate_version : null;

  if (!preview && !resources.length && !safetyGate) return null;

  return (
    <div className={compact ? 'mt-2 space-y-1' : 'mt-2 rounded-md border border-white/10 bg-black/15 px-2 py-1.5 space-y-1'}>
      {previewVersion && (
        <div className="flex items-center justify-between gap-2 text-[8px] font-mono">
          <span className="text-foreground/35">dry-run preview</span>
          <span className="text-foreground/45">{previewVersion}</span>
        </div>
      )}
      {(operation || target) && (
        <p className="truncate text-[8px] font-mono text-foreground/45">
          {operation}{operation && target ? ' ' : ''}{target}
        </p>
      )}
      {resources.length > 0 && !compact && (
        <p className="truncate text-[8px] font-mono text-foreground/35">
          resources: {resources.map((resource) => formatResource(resource)).join(', ')}
        </p>
      )}
      {gateVersion && (
        <p className="truncate text-[8px] font-mono text-success/70">gate: {gateVersion}</p>
      )}
      {preconditions.length > 0 && !compact && (
        <p className="truncate text-[8px] font-mono text-foreground/35">
          preflight: {preconditions.map((check) => String(getRecord(check)?.check_name ?? 'check')).join(', ')}
        </p>
      )}
      {Object.keys(expectedOutcome || {}).length > 0 && !compact && (
        <p className="truncate text-[8px] font-mono text-foreground/35">
          expected: {Object.entries(expectedOutcome || {}).map(([key, value]) => `${key}=${String(value)}`).join(', ')}
        </p>
      )}
      {evidenceRefs.length > 0 && !compact && (
        <p className="truncate text-[8px] font-mono text-foreground/35">evidence: {evidenceRefs.join(', ')}</p>
      )}
    </div>
  );
};

function riskBorderStyle(risk: string): string {
  switch (risk) {
    case 'critical': return 'border-red-500/30 bg-red-500/5';
    case 'high': return 'border-orange-500/25 bg-orange-500/5';
    case 'medium': return 'border-amber-500/20 bg-amber-500/5';
    case 'low': return 'border-emerald-500/20 bg-emerald-500/5';
    default: return 'border-white/10 bg-white/[0.02]';
  }
}

function riskBadgeStyle(risk: string): string {
  switch (risk) {
    case 'critical': return 'bg-red-500/15 border-red-500/30 text-red-300';
    case 'high': return 'bg-orange-500/15 border-orange-500/30 text-orange-300';
    case 'medium': return 'bg-amber-500/15 border-amber-500/30 text-amber-300';
    case 'low': return 'bg-emerald-500/15 border-emerald-500/20 text-emerald-300';
    default: return 'bg-slate-500/10 border-slate-500/20 text-slate-300';
  }
}

function getMaintenanceProposalFromCommand(command: CommandRecord): MaintenanceActionProposal | null {
  const metadata = command.metadata;
  if (!metadata || metadata.kind !== 'maintenance_action') return null;
  const proposal = metadata.proposal;
  if (!proposal || typeof proposal !== 'object') return null;
  const candidate = proposal as Partial<MaintenanceActionProposal>;
  if (
    typeof candidate.proposal_id !== 'string'
    || typeof candidate.action !== 'string'
    || typeof candidate.title !== 'string'
    || typeof candidate.reason !== 'string'
    || typeof candidate.status !== 'string'
  ) {
    return null;
  }
  return candidate as MaintenanceActionProposal;
}

function getMetadataString(command: CommandRecord, key: string): string | null {
  const value = command.metadata?.[key];
  return typeof value === 'string' && value.length > 0 ? value : null;
}

function hasResolutionMetadata(command: CommandRecord): boolean {
  return Boolean(
    getMetadataString(command, 'approval_resolution_status')
    || getMetadataString(command, 'clarification_resolution_status')
  );
}

function isQuarantinedClickDecision(command: CommandRecord): boolean {
  const policyRule = getMetadataString(command, 'policy_rule') || '';
  const decisionStatus = getMetadataString(command, 'decision_status') || '';
  return (
    policyRule.includes('generic_click.quarantined')
    || policyRule.includes('target_resolution_missing')
    || (decisionStatus.length > 0 && command.text.toLowerCase().includes('click'))
  );
}

function getRecord(value: unknown): Record<string, unknown> | null {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : null;
}

function formatResource(resource: Record<string, unknown>): string {
  const operation = typeof resource.operation === 'string' ? resource.operation : null;
  const path = typeof resource.path === 'string' ? resource.path : null;
  const type = typeof resource.type === 'string' ? resource.type : 'resource';
  if (operation && path) return `${operation}:${path}`;
  return path ?? type;
}
