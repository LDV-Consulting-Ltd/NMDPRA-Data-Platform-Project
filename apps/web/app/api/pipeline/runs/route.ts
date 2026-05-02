/**
 * Server-only route: lists pipeline runs via FastAPI with ADMIN_RUN_TOKEN.
 * Token is read from env on the server; never sent to the browser.
 */
import { NextRequest, NextResponse } from 'next/server';
import { backendApiBase } from '@/lib/backend-url';

export async function GET(request: NextRequest) {
  const ADMIN_TOKEN = process.env.ADMIN_RUN_TOKEN;
  if (!ADMIN_TOKEN) {
    return NextResponse.json(
      {
        error: 'Pipeline runs not configured (ADMIN_RUN_TOKEN missing)',
        detail: 'Set ADMIN_RUN_TOKEN in repo root .env or apps/web/.env.local',
      },
      { status: 503 }
    );
  }

  const limit = request.nextUrl.searchParams.get('limit') || '10';

  try {
    const res = await fetch(
      `${backendApiBase()}/v1/admin/pipeline/runs?limit=${limit}`,
      {
        headers: {
          'X-Admin-Token': ADMIN_TOKEN,
        },
      }
    );

    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      return NextResponse.json(
        { error: data.detail || data.message || 'Failed to fetch runs' },
        { status: res.status }
      );
    }

    return NextResponse.json(data);
  } catch (e) {
    const message = e instanceof Error ? e.message : 'Unknown error';
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
