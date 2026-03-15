import { fetchApi } from '@/lib/api';

export default async function GasPage() {
  const res = await fetchApi<{
    data: Array<{ month: string; category: string; item_name: string; metric_name: string; metric_value: number | string | null }>;
    data_status: string;
    last_updated: string;
  }>('/v1/gas/infra', { per_page: '100' });

  return (
    <div>
      <h1 className="text-2xl font-bold text-amber-400 mb-4">Gas & pipeline progress</h1>
      <div className="banner-coverage mb-4">
        Status: {res.data_status} · Last updated: {res.last_updated || '—'}
      </div>
      <table>
        <thead>
          <tr><th>Month</th><th>Category</th><th>Item</th><th>Metric</th><th>Value</th></tr>
        </thead>
        <tbody>
          {(res.data || []).map((r, i) => (
            <tr key={i}>
              <td>{r.month}</td><td>{r.category}</td><td>{r.item_name || '—'}</td><td>{r.metric_name}</td><td>{r.metric_value != null ? String(r.metric_value) : '—'}</td>
            </tr>
          ))}
          {(!res.data || res.data.length === 0) && <tr><td colSpan={5} className="text-slate-500">No data</td></tr>}
        </tbody>
      </table>
    </div>
  );
}
