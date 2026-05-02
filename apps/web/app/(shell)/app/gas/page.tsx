import { fetchApi } from '@/lib/api';
import { AppEmptyState } from '@/app/components/AppEmptyState';

export const metadata = {
  title: 'Gas · Dashboard',
};

export default async function GasPage() {
  let res: {
    data?: Array<{
      month: string;
      category: string;
      item_name: string;
      metric_name: string;
      metric_value: number | string | null;
    }>;
    data_status?: string;
    last_updated?: string;
  } = {};

  try {
    res = await fetchApi<typeof res>('/v1/gas/infra', { per_page: '100' });
  } catch {
    res = {};
  }

  const rows = res.data || [];
  const empty = rows.length === 0;

  return (
    <div>
      <h1 className="mb-2 text-2xl font-bold text-white">Gas & pipeline progress</h1>
      <p className="mb-6 text-slate-400">
        Infrastructure and pipeline metrics from published downstream gas reporting.
      </p>

      {empty ? (
        <AppEmptyState context="gas & pipeline metrics" />
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
                  <th className="p-3 font-medium">Category</th>
                  <th className="p-3 font-medium">Item</th>
                  <th className="p-3 font-medium">Metric</th>
                  <th className="p-3 font-medium">Value</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r, i) => (
                  <tr key={i} className="border-b border-slate-800/80">
                    <td className="p-3 text-slate-300">{r.month}</td>
                    <td className="p-3 text-slate-300">{r.category}</td>
                    <td className="p-3 text-slate-300">{r.item_name || '—'}</td>
                    <td className="p-3 text-slate-400">{r.metric_name}</td>
                    <td className="p-3 tabular-nums text-teal-100">
                      {r.metric_value != null ? String(r.metric_value) : '—'}
                    </td>
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
