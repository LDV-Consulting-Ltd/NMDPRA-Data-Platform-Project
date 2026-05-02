import { fetchApi } from '@/lib/api';
import { AppEmptyState } from '@/app/components/AppEmptyState';

export const metadata = {
  title: 'Fuel prices · Dashboard',
};

export default async function PricesPage({
  searchParams,
}: {
  searchParams: Promise<{ month?: string }>;
}) {
  const { month } = await searchParams;
  const params: Record<string, string> = { per_page: '100' };
  if (month) params.month = month;

  let res: {
    data?: Array<{ month: string; city: string; avg_price: number | null; unit: string }>;
    meta?: { total: number };
    data_status?: string;
    last_updated?: string;
  } = {};

  try {
    res = await fetchApi<typeof res>('/v1/prices/fuel', params);
  } catch {
    res = { data: [], data_status: 'unavailable', last_updated: undefined };
  }

  const rows = res.data || [];
  const empty = rows.length === 0;

  return (
    <div>
      <h1 className="mb-2 text-2xl font-bold text-white">Fuel prices by city</h1>
      <p className="mb-6 text-slate-400">
        Average pump prices by reporting month and city. Append <span className="font-mono text-slate-300">?month=YYYY-MM</span>{' '}
        to filter.
      </p>

      {empty ? (
        <AppEmptyState context="fuel prices" />
      ) : (
        <>
          <div className="mb-6 rounded-lg border border-teal-900/40 bg-teal-950/20 px-4 py-3 text-sm text-teal-100/90">
            Status: {res.data_status ?? '—'} · Last updated: {res.last_updated || '—'} · Rows: {rows.length}
          </div>
          <div className="overflow-x-auto rounded-xl border border-slate-800">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700 text-left text-slate-500">
                  <th className="p-3 font-medium">Month</th>
                  <th className="p-3 font-medium">City</th>
                  <th className="p-3 font-medium">Avg price</th>
                  <th className="p-3 font-medium">Unit</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r, i) => (
                  <tr key={i} className="border-b border-slate-800/80">
                    <td className="p-3 text-slate-300">{r.month}</td>
                    <td className="p-3 text-slate-300">{r.city}</td>
                    <td className="p-3 tabular-nums text-teal-100">
                      {r.avg_price != null ? r.avg_price : '—'}
                    </td>
                    <td className="p-3 text-slate-400">{r.unit || 'NGN/L'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
