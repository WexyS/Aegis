import { AppRegistrySnapshot, ToolRegistrySnapshot } from '@/types/runtime';

const API_URL = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_WS_URL || 'http://localhost:8400';

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
