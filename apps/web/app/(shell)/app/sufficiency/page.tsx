import { fetchApi } from '@/lib/api';
import { AppEmptyState } from '@/app/components/AppEmptyState';

export const metadata = {
  title: 'Sufficiency · Dashboard',
};

export default async function SufficiencyPage() {
  let res: {
    data?: Array<{ period_month?: string; series_name: string; value: number }>;
    data_status?: string;
    last_updated?: string;
  } = {};

  try {
    res = await fetchApi<typeof res>('/v1/charts/series', { per_page: '100' });
  } catch {
    res = {};
  }

  const rows = res.data || [];
  const empty = rows.length === 0;

  return (
    <div>
      <h1 className="mb-2 text-2xl font-bold text-white">Stock & days sufficiency trends</h1>
      <p className="mb-6 text-slate-400">
        Series from published fact sheets (Inland / Marine / Total where available).
      </p>

      {empty ? (
        <AppEmptyState context="sufficiency series" />
      ) : (
        <>
          <div className="mb-6 rounded-lg border border-teal-900/40 bg-teal-950/20 px-4 py-3 text-sm text-teal-100/90">
            Status: {res.data_status ?? '—'} · Last updated: {res.last_updated || '—'}
          </div>
          <div className="overflow-x-auto rounded-xl border border-slate-800">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700 text-left text-slate-500">
                  <th className="p-3 font-medium">Period (month)</th>
                  <th className="p-3 font-medium">Series</th>
                  <th className="p-3 font-medium">Value</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r, i) => (
                  <tr key={i} className="border-b border-slate-800/80">
                    <td className="p-3 text-slate-300">{r.period_month || '—'}</td>
                    <td className="p-3 text-slate-300">{r.series_name}</td>
                    <td className="p-3 tabular-nums text-teal-100">{r.value}</td>
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
