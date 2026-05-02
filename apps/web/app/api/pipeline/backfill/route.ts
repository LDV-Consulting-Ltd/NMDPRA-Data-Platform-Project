import { NextRequest, NextResponse } from 'next/server';
import { backendApiBase } from '@/lib/backend-url';

export async function POST(request: NextRequest) {
  const ADMIN_TOKEN = process.env.ADMIN_RUN_TOKEN;
  if (!ADMIN_TOKEN) {
    return NextResponse.json({ error: 'Not configured' }, { status: 503 });
  }
  let body: Record<string, unknown> = {};
  try {
    body = await request.json();
  } catch {
    body = {};
  }
  try {
    const res = await fetch(`${backendApiBase()}/v1/admin/pipeline/backfill`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Admin-Token': ADMIN_TOKEN,
      },
      body: JSON.stringify(body),
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
