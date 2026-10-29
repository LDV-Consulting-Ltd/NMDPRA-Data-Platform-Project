import { NextRequest, NextResponse } from 'next/server';
import { backendApiBase } from '@/lib/backend-url';

type Params = { params: Promise<{ schema: string; table: string }> };

export async function GET(request: NextRequest, { params }: Params) {
  const { schema, table } = await params;
  const limit = request.nextUrl.searchParams.get('limit') || '10';
  if (!['bronze', 'silver', 'gold'].includes(schema)) {
    return NextResponse.json({ error: 'Invalid schema' }, { status: 400 });
  }
  try {
    const res = await fetch(
      `${backendApiBase()}/v1/data-layers/tables/${schema}/${table}/sample?limit=${limit}`
    );
    const data = await res.json().catch(() => ({}));
    if (!res.ok) return NextResponse.json(data, { status: res.status });
    return NextResponse.json(data);
  } catch (e) {
    return NextResponse.json({ error: e instanceof Error ? e.message : 'Unknown' }, { status: 502 });
  }
}
