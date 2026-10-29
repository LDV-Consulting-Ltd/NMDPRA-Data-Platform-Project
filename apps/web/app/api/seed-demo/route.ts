/**
 * Seed demo data into bronze (Prices, Sufficiency, Refineries, etc.). Uses ADMIN_RUN_TOKEN server-side.
 */
import { NextResponse } from 'next/server';
import { backendApiBase } from '@/lib/backend-url';

const ADMIN_TOKEN = process.env.ADMIN_RUN_TOKEN;

export async function POST() {
  if (!ADMIN_TOKEN) {
    return NextResponse.json(
      { error: 'Seed demo not configured (ADMIN_RUN_TOKEN missing)' },
      { status: 503 }
    );
  }
  try {
    const res = await fetch(`${backendApiBase()}/v1/admin/seed-demo`, {
      method: 'POST',
      headers: { 'X-Admin-Token': ADMIN_TOKEN },
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      return NextResponse.json(data, { status: res.status });
    }
    return NextResponse.json(data);
  } catch (e) {
    return NextResponse.json(
      { error: e instanceof Error ? e.message : 'Unknown error' },
      { status: 502 }
    );
  }
}
