import { NextRequest, NextResponse } from 'next/server';

const API_BASE = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
  const layer = request.nextUrl.searchParams.get('layer') || 'bronze';
  if (!['bronze', 'silver', 'gold'].includes(layer)) {
    return NextResponse.json({ error: 'layer must be bronze, silver, or gold' }, { status: 400 });
  }
  try {
    const res = await fetch(`${API_BASE}/v1/data-layers/tables?layer=${layer}`);
    const data = await res.json().catch(() => ({}));
    return NextResponse.json(data);
  } catch (e) {
    return NextResponse.json({ error: e instanceof Error ? e.message : 'Unknown' }, { status: 502 });
  }
}
