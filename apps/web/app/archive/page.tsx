import { fetchApi } from '@/lib/api';

export default async function ArchivePage() {
  const depot = await fetchApi<{ data: Array<{ report_date: string; depot_name: string; volume_litres: number | null }>; data_status: string }>('/v1/archive/truckout/depot', { per_page: '30' });
  const summary = await fetchApi<{ data: Array<{ report_date: string; product: string; total_days_sufficiency: number | null }>; data_status: string }>('/v1/archive/stock/summary', { per_page: '30' });

  return (
    <div>
      <h1 className="text-2xl font-bold text-amber-400 mb-4">Archived data</h1>
      <div className="banner-archived mb-6">
        <strong>Archived (last published 2023)</strong>
        <p className="text-sm mt-1">Daily Truckout and Stock Report feeds stopped at 2023. Shown for historical coverage.</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <section>
          <h2 className="text-lg font-semibold mb-2">Truckout by depot (sample)</h2>
          <p className="text-slate-400 text-sm mb-2">Status: {depot.data_status}</p>
          <table>
            <thead>
              <tr><th>Date</th><th>Depot</th><th>Volume (L)</th></tr>
            </thead>
            <tbody>
              {(depot.data || []).map((r, i) => (
                <tr key={i}><td>{r.report_date}</td><td>{r.depot_name}</td><td>{r.volume_litres != null ? r.volume_litres : '—'}</td></tr>
              ))}
            </tbody>
          </table>
          <span className="text-slate-500 text-sm mt-2 inline-block">Use API /v1/archive/truckout/depot for full data</span>
        </section>
        <section>
          <h2 className="text-lg font-semibold mb-2">Stock & days sufficiency summary (sample)</h2>
          <p className="text-slate-400 text-sm mb-2">Status: {summary.data_status}</p>
          <table>
            <thead>
              <tr><th>Date</th><th>Product</th><th>Days sufficiency</th></tr>
            </thead>
            <tbody>
              {(summary.data || []).map((r, i) => (
                <tr key={i}><td>{r.report_date}</td><td>{r.product}</td><td>{r.total_days_sufficiency != null ? r.total_days_sufficiency : '—'}</td></tr>
              ))}
            </tbody>
          </table>
          <span className="text-slate-500 text-sm mt-2 inline-block">Use API /v1/archive/stock/summary for full data</span>
        </section>
      </div>
    </div>
  );
}
