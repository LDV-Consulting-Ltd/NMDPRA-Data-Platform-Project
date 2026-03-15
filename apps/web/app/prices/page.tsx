import { fetchApi } from '@/lib/api';

export default async function PricesPage({
  searchParams,
}: {
  searchParams: Promise<{ month?: string }>;
}) {
  const { month } = await searchParams;
  const q = month ? { month } : {};
  const res = await fetchApi<{
    data: Array<{ month: string; city: string; avg_price: number | null; unit: string }>;
    meta: { total: number };
    data_status: string;
    last_updated: string;
  }>('/v1/prices/fuel', { ...q, per_page: '100' });

  return (
    <div>
      <h1 className="text-2xl font-bold text-amber-400 mb-4">Fuel prices by city</h1>
      <div className="banner-coverage mb-4">
        Status: {res.data_status} · Last updated: {res.last_updated || '—'}
      </div>
      <p className="text-slate-400 mb-4">Filter by month (e.g. ?month=2024-01) and download CSV from table.</p>
      <table>
        <thead>
          <tr><th>Month</th><th>City</th><th>Avg price</th><th>Unit</th></tr>
        </thead>
        <tbody>
          {(res.data || []).map((r, i) => (
            <tr key={i}>
              <td>{r.month}</td><td>{r.city}</td><td>{r.avg_price != null ? r.avg_price : '—'}</td><td>{r.unit || 'NGN/L'}</td>
            </tr>
          ))}
          {(!res.data || res.data.length === 0) && <tr><td colSpan={4} className="text-slate-500">No data</td></tr>}
        </tbody>
      </table>
    </div>
  );
}
