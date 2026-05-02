import { NextResponse } from 'next/server';
import { backendApiBase } from '@/lib/backend-url';

export async function GET() {
  const ADMIN_TOKEN = process.env.ADMIN_RUN_TOKEN;
  if (!ADMIN_TOKEN) {
    return NextResponse.json(
      {
        error: 'Not configured',
        detail: 'Set ADMIN_RUN_TOKEN in repo root .env or apps/web/.env.local',
      },
      { status: 503 }
    );
  }
  try {
    const res = await fetch(`${backendApiBase()}/v1/admin/pipeline/status`, {
      headers: { 'X-Admin-Token': ADMIN_TOKEN },
      cache: 'no-store',
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      return NextResponse.json(data, { status: res.status });
    }
    return NextResponse.json(data);
  } catch (e) {
    const message = e instanceof Error ? e.message : 'Unknown error';
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
