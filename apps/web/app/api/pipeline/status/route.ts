/**
 * Fetches last pipeline run from DB (bronze.ingest_run) for Overview card.
 * No auth; used as fallback when Airflow runs list is empty or fails.
 */
import { NextResponse } from 'next/server';
import { backendApiBase } from '@/lib/backend-url';

export async function GET() {
  try {
    const res = await fetch(`${backendApiBase()}/v1/pipeline/status`);
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
