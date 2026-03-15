import { fetchApi } from '@/lib/api';

export default async function RefineriesPage({
  searchParams,
}: {
  searchParams: Promise<{ month?: string }>;
}) {
  const { month } = await searchParams;
  const q = month ? { month } : {};
  const status = await fetchApi<{ data: Array<{ month: string; refinery_name: string; utilization_pct: number | null; status: string }>; data_status: string; last_updated: string }>('/v1/refineries/status', { ...q, per_page: '50' });
  const modular = await fetchApi<{ data: Array<{ month: string; refinery_name: string; capacity_utilization_pct: number | null }>; last_updated: string }>('/v1/refineries/modular', { ...q, per_page: '50' });

  return (
    <div>
      <h1 className="text-2xl font-bold text-amber-400 mb-4">Refinery status & utilization</h1>
      <div className="banner-coverage mb-4">
        Status: {status.data_status} · Last updated: {status.last_updated || '—'}
      </div>
      <h2 className="text-lg font-semibold mt-6 mb-2">Refinery status</h2>
      <table>
        <thead>
          <tr><th>Month</th><th>Refinery</th><th>Utilization %</th><th>Status</th></tr>
        </thead>
        <tbody>
          {(status.data || []).map((r, i) => (
            <tr key={i}><td>{r.month}</td><td>{r.refinery_name}</td><td>{r.utilization_pct != null ? r.utilization_pct : '—'}</td><td>{r.status || '—'}</td></tr>
          ))}
        </tbody>
      </table>
      <h2 className="text-lg font-semibold mt-6 mb-2">Modular refinery output</h2>
      <table>
        <thead>
          <tr><th>Month</th><th>Refinery</th><th>Capacity utilization %</th></tr>
        </thead>
        <tbody>
          {(modular.data || []).map((r, i) => (
            <tr key={i}><td>{r.month}</td><td>{r.refinery_name}</td><td>{r.capacity_utilization_pct != null ? r.capacity_utilization_pct : '—'}</td></tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
