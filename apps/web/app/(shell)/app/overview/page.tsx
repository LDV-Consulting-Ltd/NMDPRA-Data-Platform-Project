import Link from 'next/link';
import { fetchApi } from '@/lib/api';
import { MetricCard } from '@/app/components/marketing/MetricCard';

export const metadata = {
  title: 'Overview · Dashboard',
};

export default async function AppOverviewPage() {
  let coverage: { data?: Array<{ source_name: string; data_status: string; last_updated?: string }> } = {};
  let highlights: { data?: Array<{ month: string; metric_name: string; metric_value: number }> } = {};
  try {
    const chunk = await Promise.all([
      fetchApi<typeof coverage>('/v1/coverage').catch(() => ({}) as typeof coverage),
      fetchApi<typeof highlights>('/v1/highlights?per_page=6').catch(() => ({}) as typeof highlights),
    ]);
    coverage = chunk[0];
    highlights = chunk[1];
  } catch {
    /* empty */
  }

  const hasData = (highlights.data?.length ?? 0) > 0 || (coverage.data?.some((c) => c.data_status !== 'no_data') ?? false);

  return (
    <div>
      <h1 className="text-2xl font-bold text-white">Operational overview</h1>
      <p className="mt-2 text-slate-400">
        Downstream intelligence across prices, sufficiency, refining, gas, and vessels.
      </p>

      {!hasData && (
        <div className="mt-6 rounded-xl border border-amber-900/40 bg-amber-950/20 px-4 py-4 text-sm text-amber-100/90">
          Data has not been loaded yet. An authorized operator can run the refresh from{' '}
          <Link href="/admin/pipeline" className="font-medium text-amber-400 underline hover:text-amber-300">
            Admin → Pipeline
          </Link>
          .
        </div>
      )}

      <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard label="Sources tracked" value={coverage.data?.length ?? '—'} accent="teal" />
        <MetricCard
          label="Highlights rows"
          value={highlights.data?.length ?? 0}
          hint="Performance metrics"
        />
        <MetricCard label="Dashboard" value="Live" hint="API-backed" accent="teal" />
        <MetricCard label="Governance" value="DQ · Lineage · Catalog" />
      </div>

      <div className="mt-10 grid gap-6 md:grid-cols-2">
        <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
          <h2 className="text-lg font-semibold text-white">Coverage</h2>
          <ul className="mt-3 space-y-2 text-sm text-slate-400">
            {(coverage.data || []).map((c) => (
              <li key={c.source_name} className="flex justify-between gap-2">
                <span>{c.source_name}</span>
                <span className="text-teal-400/90">{c.data_status}</span>
              </li>
            ))}
            {(!coverage.data || coverage.data.length === 0) && (
              <li className="text-slate-500">No coverage data yet.</li>
            )}
          </ul>
        </section>
        <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
          <h2 className="text-lg font-semibold text-white">Recent highlights</h2>
          <div className="mt-3 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700 text-left text-slate-500">
                  <th className="py-2">Month</th>
                  <th>Metric</th>
                  <th>Value</th>
                </tr>
              </thead>
              <tbody>
                {(highlights.data || []).slice(0, 6).map((h, i) => (
                  <tr key={i} className="border-b border-slate-800">
                    <td className="py-2 text-slate-300">{h.month}</td>
                    <td className="text-slate-300">{h.metric_name}</td>
                    <td className="tabular-nums text-teal-200">{h.metric_value ?? '—'}</td>
                  </tr>
                ))}
                {(!highlights.data || highlights.data.length === 0) && (
                  <tr>
                    <td colSpan={3} className="py-4 text-slate-500">
                      No rows yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      </div>

      <section className="mt-10">
        <h2 className="mb-4 text-lg font-semibold text-white">Navigate</h2>
        <div className="flex flex-wrap gap-3">
          {[
            ['/app/prices', 'Fuel prices'],
            ['/app/sufficiency', 'Sufficiency'],
            ['/app/refineries', 'Refineries'],
            ['/app/gas', 'Gas'],
            ['/app/vessels', 'Vessels'],
            ['/app/archive', 'Archive'],
          ].map(([href, label]) => (
            <Link
              key={href}
              href={href}
              className="rounded-lg border border-teal-800/50 bg-teal-950/30 px-4 py-2 text-sm font-medium text-teal-200 transition hover:border-teal-600 hover:bg-teal-950/50"
            >
              {label}
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
