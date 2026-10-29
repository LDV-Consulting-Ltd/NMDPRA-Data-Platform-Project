import { backendApiBase } from '@/lib/backend-url';

/**
 * Resolve API base for fetchApi.
 * - Server: prefer binding / Docker internal URL (API_URL).
 * - Browser: same-origin (empty base) when NEXT_PUBLIC_API_URL is unset so
 *   public rewrites (/v1/*, /health) hit the FastAPI service on this domain.
 */
function apiBase(): string {
  if (typeof window === 'undefined') {
    return backendApiBase();
  }
  const publicUrl = process.env.NEXT_PUBLIC_API_URL;
  if (publicUrl && publicUrl.trim()) {
    return publicUrl.replace(/\/$/, '');
  }
  return '';
}

export async function fetchApi<T>(path: string, params?: Record<string, string>): Promise<T> {
  const base = apiBase();
  let url: URL;
  if (base) {
    url = new URL(path, base.endsWith('/') ? base : `${base}/`);
  } else if (typeof window !== 'undefined') {
    url = new URL(path, window.location.origin);
  } else {
    // Server without binding / env: absolute path on same host is not available;
    // fall back to local FastAPI for non-Vercel runs.
    url = new URL(path, 'http://localhost:8000');
  }
  if (params) {
    Object.entries(params).forEach(([k, v]) => v && url.searchParams.set(k, v));
  }
  const res = await fetch(url.toString(), { next: { revalidate: 60 } });
  if (!res.ok) throw new Error(`API ${res.status}: ${path}`);
  return res.json();
}

export function coverageBanner(status: string, lastUpdated?: string) {
  return { data_status: status, last_updated: lastUpdated };
}
