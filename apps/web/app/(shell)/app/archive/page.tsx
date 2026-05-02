import { fetchApi } from '@/lib/api';
import { AppEmptyState } from '@/app/components/AppEmptyState';

export const metadata = {
  title: 'Archive · Dashboard',
};

export default async function ArchivePage() {
  let depot: {
    data?: Array<{ report_date: string; depot_name: string; volume_litres: number | null }>;
    data_status?: string;
  } = {};
  let summary: {
    data?: Array<{ report_date: string; product: string; total_days_sufficiency: number | null }>;
    data_status?: string;
  } = {};

  try {
    depot = await fetchApi<typeof depot>('/v1/archive/truckout/depot', { per_page: '30' });
  } catch {
    depot = {};
  }
  try {
    summary = await fetchApi<typeof summary>('/v1/archive/stock/summary', { per_page: '30' });
  } catch {
    summary = {};
  }

  const depotRows = depot.data || [];
  const summaryRows = summary.data || [];
  const bothEmpty = depotRows.length === 0 && summaryRows.length === 0;

  return (
    <div>
      <h1 className="mb-2 text-2xl font-bold text-white">Archived data</h1>
      <p className="mb-6 text-slate-400">
        Historical Daily Truckout and Stock Report feeds where publication ended (often last visible around 2023).
      </p>

      <div className="mb-8 rounded-xl border border-slate-700/80 bg-slate-900/40 px-4 py-3 text-sm text-slate-400">
        <span className="font-medium text-slate-200">Archived coverage</span>
        <span className="mx-2 text-slate-600">·</span>
        Retained for longitudinal comparison and completeness reporting.
      </div>

      {bothEmpty && <AppEmptyState context="archived truckout and stock summaries" />}

      <div className="grid gap-8 md:grid-cols-2">
        <section>
          <h2 className="mb-3 text-lg font-semibold text-white">Truckout by depot</h2>
          <p className="mb-3 text-xs text-slate-500">Status: {depot.data_status ?? '—'}</p>
          {depotRows.length === 0 ? (
            <p className="text-sm text-slate-500">No depot rows loaded.</p>
          ) : (
            <div className="overflow-x-auto rounded-xl border border-slate-800">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700 text-left text-slate-500">
                    <th className="p-3 font-medium">Date</th>
                    <th className="p-3 font-medium">Depot</th>
                    <th className="p-3 font-medium">Volume (L)</th>
                  </tr>
                </thead>
                <tbody>
                  {depotRows.map((r, i) => (
                    <tr key={i} className="border-b border-slate-800/80">
                      <td className="p-3 text-slate-300">{r.report_date}</td>
                      <td className="p-3 text-slate-300">{r.depot_name}</td>
                      <td className="p-3 tabular-nums text-teal-100">
                        {r.volume_litres != null ? r.volume_litres : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section>
          <h2 className="mb-3 text-lg font-semibold text-white">Stock & days sufficiency summary</h2>
          <p className="mb-3 text-xs text-slate-500">Status: {summary.data_status ?? '—'}</p>
          {summaryRows.length === 0 ? (
            <p className="text-sm text-slate-500">No summary rows loaded.</p>
          ) : (
            <div className="overflow-x-auto rounded-xl border border-slate-800">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700 text-left text-slate-500">
                    <th className="p-3 font-medium">Date</th>
                    <th className="p-3 font-medium">Product</th>
                    <th className="p-3 font-medium">Days sufficiency</th>
                  </tr>
                </thead>
                <tbody>
                  {summaryRows.map((r, i) => (
                    <tr key={i} className="border-b border-slate-800/80">
                      <td className="p-3 text-slate-300">{r.report_date}</td>
                      <td className="p-3 text-slate-300">{r.product}</td>
                      <td className="p-3 tabular-nums text-teal-100">
                        {r.total_days_sufficiency != null ? r.total_days_sufficiency : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
