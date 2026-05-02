import { fetchApi } from '@/lib/api';
import { AppEmptyState } from '@/app/components/AppEmptyState';

export const metadata = {
  title: 'Refineries · Dashboard',
};

export default async function RefineriesPage({
  searchParams,
}: {
  searchParams: Promise<{ month?: string }>;
}) {
  const { month } = await searchParams;
  const params: Record<string, string> = { per_page: '50' };
  if (month) params.month = month;

  let status: {
    data?: Array<{ month: string; refinery_name: string; utilization_pct: number | null; status: string }>;
    data_status?: string;
    last_updated?: string;
  } = {};
  let modular: {
    data?: Array<{ month: string; refinery_name: string; capacity_utilization_pct: number | null }>;
    last_updated?: string;
  } = {};

  try {
    status = await fetchApi<typeof status>('/v1/refineries/status', params);
  } catch {
    status = {};
  }
  try {
    modular = await fetchApi<typeof modular>('/v1/refineries/modular', params);
  } catch {
    modular = {};
  }

  const statusRows = status.data || [];
  const modularRows = modular.data || [];
  const empty = statusRows.length === 0 && modularRows.length === 0;

  return (
    <div>
      <h1 className="mb-2 text-2xl font-bold text-white">Refinery status & utilization</h1>
      <p className="mb-6 text-slate-400">
        Filter by month via <span className="font-mono text-slate-300">?month=YYYY-MM</span>.
      </p>

      {empty ? (
        <AppEmptyState context="refinery status" />
      ) : (
        <>
          <div className="mb-6 rounded-lg border border-teal-900/40 bg-teal-950/20 px-4 py-3 text-sm text-teal-100/90">
            Status: {status.data_status ?? '—'} · Last updated: {status.last_updated || '—'}
          </div>

          <section className="mb-10">
            <h2 className="mb-3 text-lg font-semibold text-white">Refinery status</h2>
            <div className="overflow-x-auto rounded-xl border border-slate-800">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700 text-left text-slate-500">
                    <th className="p-3 font-medium">Month</th>
                    <th className="p-3 font-medium">Refinery</th>
                    <th className="p-3 font-medium">Utilization %</th>
                    <th className="p-3 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {statusRows.map((r, i) => (
                    <tr key={i} className="border-b border-slate-800/80">
                      <td className="p-3 text-slate-300">{r.month}</td>
                      <td className="p-3 text-slate-300">{r.refinery_name}</td>
                      <td className="p-3 tabular-nums text-teal-100">
                        {r.utilization_pct != null ? r.utilization_pct : '—'}
                      </td>
                      <td className="p-3 text-slate-400">{r.status || '—'}</td>
                    </tr>
                  ))}
                  {statusRows.length === 0 && (
                    <tr>
                      <td colSpan={4} className="p-4 text-slate-500">
                        No status rows for this filter.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>

          <section>
            <h2 className="mb-3 text-lg font-semibold text-white">Modular refinery output</h2>
            <p className="mb-3 text-xs text-slate-500">Last updated: {modular.last_updated || '—'}</p>
            <div className="overflow-x-auto rounded-xl border border-slate-800">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700 text-left text-slate-500">
                    <th className="p-3 font-medium">Month</th>
                    <th className="p-3 font-medium">Refinery</th>
                    <th className="p-3 font-medium">Capacity utilization %</th>
                  </tr>
                </thead>
                <tbody>
                  {modularRows.map((r, i) => (
                    <tr key={i} className="border-b border-slate-800/80">
                      <td className="p-3 text-slate-300">{r.month}</td>
                      <td className="p-3 text-slate-300">{r.refinery_name}</td>
                      <td className="p-3 tabular-nums text-teal-100">
                        {r.capacity_utilization_pct != null ? r.capacity_utilization_pct : '—'}
                      </td>
                    </tr>
                  ))}
                  {modularRows.length === 0 && (
                    <tr>
                      <td colSpan={3} className="p-4 text-slate-500">
                        No modular output rows for this filter.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </div>
  );
}
