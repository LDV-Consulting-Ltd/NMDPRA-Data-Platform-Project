/**
 * Server-only: get a single DAG run (for progress / current task).
 */
import { NextRequest, NextResponse } from 'next/server';
import { backendApiBase } from '@/lib/backend-url';

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ dagRunId: string }> }
) {
  const { dagRunId } = await params;
  const ADMIN_TOKEN = process.env.ADMIN_RUN_TOKEN;
  if (!ADMIN_TOKEN) {
    return NextResponse.json(
      { error: 'Not configured (ADMIN_RUN_TOKEN missing)' },
      { status: 503 }
    );
  }

  try {
    const res = await fetch(
      `${backendApiBase()}/v1/admin/pipeline/runs/${encodeURIComponent(dagRunId)}`,
      {
        headers: { 'X-Admin-Token': ADMIN_TOKEN },
      }
    );
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      return NextResponse.json(
        { error: data.detail || data.message || 'Failed to fetch run' },
        { status: res.status }
      );
    }
    return NextResponse.json(data);
  } catch (e) {
    const message = e instanceof Error ? e.message : 'Unknown error';
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
