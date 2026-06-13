import {
  AutoPilotReport,
  AutoPilotReportListResponse,
  MemoryOperationResponse,
  SocietySession,
  SocietySessionListResponse,
} from '@/types/rc';
import { AskRequest, AskResponse } from '@/types/ask';
import {
  AppRegistrySnapshot,
  ApprovalHygieneDenyResponse,
  ApprovalHygienePreviewResponse,
  CommandRecord,
  LocalProviderProbeProjection,
  RepoAuditDryRunProjection,
  ToolRegistrySnapshot,
} from '@/types/runtime';

export const API_URL = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_WS_URL || 'http://localhost:8400';

export function getVisionStreamUrl(): string {
  return new URL('/vision/stream', API_URL).toString();
}

export async function askAegis(payload: AskRequest): Promise<AskResponse> {
  const url = new URL('/ask', API_URL);
  const response = await fetch(url.toString(), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    cache: 'no-store',
    body: JSON.stringify(payload),
  });
  const body = await parseJsonBody<AskResponse | { detail?: unknown }>(response);
  if (!response.ok) {
    throw new Error(resolveErrorDetail(body, `Aegis Ask failed: ${response.status}`));
  }
  if (!body || !('answer' in body)) {
    throw new Error('Aegis Ask returned no answer.');
  }
  return body as AskResponse;
}

export async function fetchAppRegistry(refresh = false): Promise<AppRegistrySnapshot> {
  const url = new URL('/apps/registry', API_URL);
  if (refresh) {
    url.searchParams.set('refresh', 'true');
  }

  const response = await fetch(url.toString(), { cache: 'no-store' });
  if (!response.ok) {
    throw new Error(`App registry request failed: ${response.status}`);
  }
  return response.json() as Promise<AppRegistrySnapshot>;
}

export async function fetchToolRegistry(): Promise<ToolRegistrySnapshot> {
  const url = new URL('/tools/registry', API_URL);
  const response = await fetch(url.toString(), { cache: 'no-store' });
  if (!response.ok) {
    throw new Error(`Tool registry request failed: ${response.status}`);
  }
  return response.json() as Promise<ToolRegistrySnapshot>;
}

export async function fetchRepoAuditDryRunProjection(): Promise<RepoAuditDryRunProjection> {
  const url = new URL('/maintenance/repo-audit/dry-run-projection', API_URL);
  const response = await fetch(url.toString(), { cache: 'no-store' });
  if (!response.ok) {
    throw new Error(`Repo audit dry-run projection request failed: ${response.status}`);
  }
  return response.json() as Promise<RepoAuditDryRunProjection>;
}

export async function fetchLocalProviderProbeProjection(): Promise<LocalProviderProbeProjection> {
  const url = new URL('/maintenance/local-provider/probe-projection', API_URL);
  const response = await fetch(url.toString(), { cache: 'no-store' });
  if (!response.ok) {
    throw new Error(`Local provider probe projection request failed: ${response.status}`);
  }
  return response.json() as Promise<LocalProviderProbeProjection>;
}

export async function runAutoPilotAudit(payload: {
  root_path: string;
  task_id?: string;
}): Promise<AutoPilotReport> {
  const url = new URL('/autopilot/run', API_URL);
  const response = await fetch(url.toString(), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    cache: 'no-store',
    body: JSON.stringify({
      task_id: payload.task_id ?? 'repo_structure_audit',
      root_path: payload.root_path,
    }),
  });
  const body = await parseJsonBody<AutoPilotReport | { detail?: unknown }>(response);
  if (!response.ok) {
    throw new Error(resolveErrorDetail(body, `AutoPilot audit failed: ${response.status}`));
  }
  if (!body || !('report_id' in body)) {
    throw new Error('AutoPilot audit returned no report.');
  }
  return body as AutoPilotReport;
}

export async function fetchAutoPilotReports(): Promise<AutoPilotReportListResponse> {
  const url = new URL('/autopilot/reports', API_URL);
  const response = await fetch(url.toString(), { cache: 'no-store' });
  const body = await parseJsonBody<AutoPilotReportListResponse | { detail?: unknown }>(response);
  if (!response.ok) {
    throw new Error(resolveErrorDetail(body, `AutoPilot reports request failed: ${response.status}`));
  }
  return body as AutoPilotReportListResponse;
}

export async function fetchAutoPilotReport(reportId: string): Promise<AutoPilotReport> {
  const url = new URL(`/autopilot/reports/${encodeURIComponent(reportId)}`, API_URL);
  const response = await fetch(url.toString(), { cache: 'no-store' });
  const body = await parseJsonBody<AutoPilotReport | { detail?: unknown }>(response);
  if (!response.ok) {
    throw new Error(resolveErrorDetail(body, `AutoPilot report request failed: ${response.status}`));
  }
  return body as AutoPilotReport;
}

export async function proposeMemory(payload: Record<string, unknown>): Promise<MemoryOperationResponse> {
  const url = new URL('/memory/propose', API_URL);
  const response = await fetch(url.toString(), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    cache: 'no-store',
    body: JSON.stringify(payload),
  });
  const body = await parseJsonBody<MemoryOperationResponse | { detail?: unknown }>(response);
  if (!response.ok) {
    throw new Error(resolveErrorDetail(body, `Memory propose failed: ${response.status}`));
  }
  return body as MemoryOperationResponse;
}

export async function approveMemory(memoryId: string): Promise<MemoryOperationResponse> {
  const url = new URL(`/memory/${encodeURIComponent(memoryId)}/approve`, API_URL);
  const response = await fetch(url.toString(), { method: 'POST', cache: 'no-store' });
  const body = await parseJsonBody<MemoryOperationResponse | { detail?: unknown }>(response);
  if (!response.ok) {
    throw new Error(resolveErrorDetail(body, `Memory approve failed: ${response.status}`));
  }
  return body as MemoryOperationResponse;
}

export async function rejectMemory(memoryId: string, reason: string): Promise<MemoryOperationResponse> {
  const url = new URL(`/memory/${encodeURIComponent(memoryId)}/reject`, API_URL);
  const response = await fetch(url.toString(), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    cache: 'no-store',
    body: JSON.stringify({ reason }),
  });
  const body = await parseJsonBody<MemoryOperationResponse | { detail?: unknown }>(response);
  if (!response.ok) {
    throw new Error(resolveErrorDetail(body, `Memory reject failed: ${response.status}`));
  }
  return body as MemoryOperationResponse;
}

export async function deleteMemory(memoryId: string): Promise<MemoryOperationResponse> {
  const url = new URL(`/memory/${encodeURIComponent(memoryId)}`, API_URL);
  const response = await fetch(url.toString(), { method: 'DELETE', cache: 'no-store' });
  const body = await parseJsonBody<MemoryOperationResponse | { detail?: unknown }>(response);
  if (!response.ok) {
    throw new Error(resolveErrorDetail(body, `Memory delete failed: ${response.status}`));
  }
  return body as MemoryOperationResponse;
}

export async function listMemories(params: {
  status?: string;
  scope?: string;
  sensitivity?: string;
  project_ref?: string;
  repository_ref?: string;
  session_ref?: string;
  include_deleted?: boolean;
} = {}): Promise<MemoryOperationResponse> {
  const url = new URL('/memory', API_URL);
  appendDefinedParams(url, params);
  const response = await fetch(url.toString(), { cache: 'no-store' });
  const body = await parseJsonBody<MemoryOperationResponse | { detail?: unknown }>(response);
  if (!response.ok) {
    throw new Error(resolveErrorDetail(body, `Memory list failed: ${response.status}`));
  }
  return body as MemoryOperationResponse;
}

export async function searchMemories(params: {
  keyword?: string;
  scope?: string;
  sensitivity?: string;
  project_ref?: string;
  repository_ref?: string;
  session_ref?: string;
  include_sensitive?: boolean;
} = {}): Promise<MemoryOperationResponse> {
  const url = new URL('/memory/search', API_URL);
  appendDefinedParams(url, params);
  const response = await fetch(url.toString(), { cache: 'no-store' });
  const body = await parseJsonBody<MemoryOperationResponse | { detail?: unknown }>(response);
  if (!response.ok) {
    throw new Error(resolveErrorDetail(body, `Memory search failed: ${response.status}`));
  }
  return body as MemoryOperationResponse;
}

export async function runSocietySession(payload: {
  autopilot_report_id?: string;
  memory_ids?: string[];
  society_name?: string;
}): Promise<SocietySession> {
  const url = new URL('/society/run', API_URL);
  const response = await fetch(url.toString(), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    cache: 'no-store',
    body: JSON.stringify(payload),
  });
  const body = await parseJsonBody<SocietySession | { detail?: unknown }>(response);
  if (!response.ok) {
    throw new Error(resolveErrorDetail(body, `Society session failed: ${response.status}`));
  }
  return body as SocietySession;
}

export async function fetchSocietySessions(): Promise<SocietySessionListResponse> {
  const url = new URL('/society/sessions', API_URL);
  const response = await fetch(url.toString(), { cache: 'no-store' });
  const body = await parseJsonBody<SocietySessionListResponse | { detail?: unknown }>(response);
  if (!response.ok) {
    throw new Error(resolveErrorDetail(body, `Society sessions request failed: ${response.status}`));
  }
  return body as SocietySessionListResponse;
}

export async function fetchSocietySession(sessionId: string): Promise<SocietySession> {
  const url = new URL(`/society/sessions/${encodeURIComponent(sessionId)}`, API_URL);
  const response = await fetch(url.toString(), { cache: 'no-store' });
  const body = await parseJsonBody<SocietySession | { detail?: unknown }>(response);
  if (!response.ok) {
    throw new Error(resolveErrorDetail(body, `Society session request failed: ${response.status}`));
  }
  return body as SocietySession;
}

type CommandEnvelope = {
  command?: CommandRecord;
};

export async function resolveApprovalDecision(
  approvalId: string,
  decision: 'grant' | 'deny',
  reason?: string,
): Promise<CommandRecord> {
  const url = new URL(`/command/approvals/${encodeURIComponent(approvalId)}/resolve`, API_URL);
  const response = await fetch(url.toString(), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    cache: 'no-store',
    body: JSON.stringify({ decision, reason }),
  });
  const body = await parseJsonBody<CommandEnvelope | { detail?: unknown }>(response);
  if (!response.ok) {
    throw new Error(resolveErrorDetail(body, `Approval resolve failed: ${response.status}`));
  }
  if (!body || !('command' in body) || !body.command) {
    throw new Error('Approval resolve returned no command record.');
  }
  return body.command;
}

export async function resolveClarificationDecision(
  clarificationId: string,
  payload: { answer?: string; cancelled?: boolean; reason?: string },
): Promise<CommandRecord> {
  const url = new URL(`/command/clarifications/${encodeURIComponent(clarificationId)}/resolve`, API_URL);
  const response = await fetch(url.toString(), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    cache: 'no-store',
    body: JSON.stringify(payload),
  });
  const body = await parseJsonBody<CommandEnvelope | { detail?: unknown }>(response);
  if (!response.ok) {
    throw new Error(resolveErrorDetail(body, `Clarification resolve failed: ${response.status}`));
  }
  if (!body || !('command' in body) || !body.command) {
    throw new Error('Clarification resolve returned no command record.');
  }
  return body.command;
}

export async function previewRestoredApprovalHygiene(
  approvalIds: string[],
): Promise<ApprovalHygienePreviewResponse> {
  const url = new URL('/command/approvals/hygiene/preview', API_URL);
  const response = await fetch(url.toString(), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    cache: 'no-store',
    body: JSON.stringify({
      approval_ids: approvalIds,
      restored_only: true,
      include_current_session: false,
    }),
  });
  const body = await parseJsonBody<ApprovalHygienePreviewResponse | { detail?: unknown }>(response);
  if (!response.ok) {
    throw new Error(resolveErrorDetail(body, `Approval hygiene preview failed: ${response.status}`));
  }
  if (!body || !('items' in body)) {
    throw new Error('Approval hygiene preview returned no items.');
  }
  return body;
}

export async function denySelectedRestoredApprovals(payload: {
  approvalIds: string[];
  confirmationPhrase: string;
  reason: string;
  idempotencyKey?: string;
}): Promise<ApprovalHygieneDenyResponse> {
  const url = new URL('/command/approvals/hygiene/deny-selected', API_URL);
  const response = await fetch(url.toString(), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    cache: 'no-store',
    body: JSON.stringify({
      approval_ids: payload.approvalIds,
      restored_only: true,
      include_current_session: false,
      confirmation_phrase: payload.confirmationPhrase,
      reason: payload.reason,
      idempotency_key: payload.idempotencyKey,
    }),
  });
  const body = await parseJsonBody<ApprovalHygieneDenyResponse | { detail?: unknown }>(response);
  if (!response.ok) {
    throw new Error(resolveErrorDetail(body, `Approval hygiene deny failed: ${response.status}`));
  }
  if (!body || !('results' in body) || !('failures' in body)) {
    throw new Error('Approval hygiene deny returned no result details.');
  }
  return body;
}

async function parseJsonBody<T>(response: Response): Promise<T | null> {
  try {
    return await response.json() as T;
  } catch {
    return null;
  }
}

function resolveErrorDetail(body: unknown, fallback: string): string {
  if (body && typeof body === 'object' && 'detail' in body) {
    const detail = (body as { detail?: unknown }).detail;
    if (typeof detail === 'string' && detail.trim()) return detail;
    if (detail && typeof detail === 'object') {
      const record = detail as Record<string, unknown>;
      const reasons = Array.isArray(record.failure_reasons) ? record.failure_reasons.join(', ') : null;
      const status = typeof record.status === 'string' ? record.status : null;
      if (status && reasons) return `${status}: ${reasons}`;
      if (status) return status;
      try {
        return JSON.stringify(detail);
      } catch {
        return fallback;
      }
    }
  }
  return fallback;
}

function appendDefinedParams(url: URL, params: Record<string, unknown>): void {
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return;
    url.searchParams.set(key, String(value));
  });
}
