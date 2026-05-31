import {
  AppRegistrySnapshot,
  ApprovalHygieneDenyResponse,
  ApprovalHygienePreviewResponse,
  CommandRecord,
  ToolRegistrySnapshot,
} from '@/types/runtime';

export const API_URL = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_WS_URL || 'http://localhost:8400';

export function getVisionStreamUrl(): string {
  return new URL('/vision/stream', API_URL).toString();
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
  }
  return fallback;
}
