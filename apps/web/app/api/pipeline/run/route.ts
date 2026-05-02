/**
 * Server-only route: triggers pipeline run via FastAPI with ADMIN_RUN_TOKEN.
 * Token is read from env on the server; never sent to the browser.
 */
import { NextResponse } from 'next/server';
import { backendApiBase } from '@/lib/backend-url';

export async function POST() {
  const ADMIN_TOKEN = process.env.ADMIN_RUN_TOKEN;
  if (!ADMIN_TOKEN) {
    return NextResponse.json(
      { error: 'Pipeline run not configured (ADMIN_RUN_TOKEN missing)' },
      { status: 503 }
    );
  }

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 25000);
    const res = await fetch(`${backendApiBase()}/v1/admin/pipeline/run`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Admin-Token': ADMIN_TOKEN,
      },
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const detail = data?.detail;
      let msg =
        typeof detail === 'string'
          ? detail
          : typeof detail === 'object' && detail !== null && 'message' in detail
            ? String((detail as { message?: string }).message)
            : data.message || 'Pipeline trigger failed';
      if (res.status === 503 && typeof detail === 'object' && detail?.message) {
        msg = String(detail.message);
      }
      return NextResponse.json({ error: msg, detail: data.detail }, { status: res.status });
    }

    return NextResponse.json(data);
  } catch (e) {
    const err = e instanceof Error ? e : new Error('Unknown error');
    const message = err.name === 'AbortError' ? 'API request timed out. Is the API container running?' : err.message;
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
