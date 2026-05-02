/**
 * Pipeline run history from DB (bronze.ingest_run). No auth.
 */
import { NextRequest, NextResponse } from 'next/server';
import { backendApiBase } from '@/lib/backend-url';

export async function GET(request: NextRequest) {
  const limit = request.nextUrl.searchParams.get('limit') || '50';
  try {
    const res = await fetch(`${backendApiBase()}/v1/pipeline/history?limit=${limit}`, {
      cache: 'no-store',
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) return NextResponse.json(data, { status: res.status });
    return NextResponse.json(data);
  } catch (e) {
    return NextResponse.json(
      { error: e instanceof Error ? e.message : 'Unknown error' },
      { status: 502 }
    );
  }
}
