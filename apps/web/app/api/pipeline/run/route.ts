/**
 * Server-only route: triggers pipeline run via FastAPI with ADMIN_RUN_TOKEN.
 * Token is read from env on the server; never sent to the browser.
 */
import { NextResponse } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const ADMIN_TOKEN = process.env.ADMIN_RUN_TOKEN;

export async function POST() {
  if (!ADMIN_TOKEN) {
    return NextResponse.json(
      { error: 'Pipeline run not configured (ADMIN_RUN_TOKEN missing)' },
      { status: 503 }
    );
  }

  try {
    const res = await fetch(`${API_BASE}/v1/admin/pipeline/run`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Admin-Token': ADMIN_TOKEN,
      },
    });

    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      return NextResponse.json(
        { error: data.detail || data.message || 'Pipeline trigger failed' },
        { status: res.status }
      );
    }

    return NextResponse.json(data);
  } catch (e) {
    const message = e instanceof Error ? e.message : 'Unknown error';
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
