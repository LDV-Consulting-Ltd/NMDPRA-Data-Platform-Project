import { fetchApi } from '@/lib/api';

export default async function SufficiencyPage() {
  const res = await fetchApi<{
    data: Array<{ period_month?: string; series_name: string; value: number }>;
    data_status: string;
    last_updated: string;
  }>('/v1/charts/series', { per_page: '100' });

  return (
    <div>
      <h1 className="text-2xl font-bold text-amber-400 mb-4">Stock & days sufficiency trends</h1>
      <div className="banner-coverage mb-4">
        Status: {res.data_status} · Last updated: {res.last_updated || '—'}
      </div>
      <p className="text-slate-400 mb-4">Chart data (Inland / Marine / Total) from fact sheets.</p>
      <table>
        <thead>
          <tr><th>Period (month)</th><th>Series</th><th>Value</th></tr>
        </thead>
        <tbody>
          {(res.data || []).map((r, i) => (
            <tr key={i}>
              <td>{r.period_month || '—'}</td><td>{r.series_name}</td><td>{r.value}</td>
            </tr>
          ))}
          {(!res.data || res.data.length === 0) && <tr><td colSpan={3} className="text-slate-500">No data</td></tr>}
        </tbody>
      </table>
    </div>
  );
}
