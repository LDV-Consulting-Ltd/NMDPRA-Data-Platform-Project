import { fetchApi } from '@/lib/api';
import Link from 'next/link';
import { PipelineStatusCard } from '@/app/components/PipelineStatusCard';

export default async function HomePage() {
  let coverage: { data?: Array<{ source_name: string; data_status: string; last_updated?: string }> } = {};
  let highlights: { data?: Array<{ month: string; metric_name: string; metric_value: number }> } = {};
  try {
    coverage = await fetchApi('/v1/coverage');
    highlights = await fetchApi('/v1/highlights?per_page=5');
  } catch (e) {
    // API may be down
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-amber-400 mb-4">Overview</h1>
      <div className="mb-6">
        <PipelineStatusCard />
      </div>
      <div className="banner-coverage mb-6">
        <strong>Coverage &amp; last updated</strong>
        <ul className="mt-2 space-y-1 text-sm">
          {(coverage.data || []).map((c) => (
            <li key={c.source_name}>
              {c.source_name}: {c.data_status} {c.last_updated ? ` · ${c.last_updated}` : ''}
            </li>
          ))}
          {(!coverage.data || coverage.data.length === 0) && <li>No coverage data yet. Run the pipeline.</li>}
        </ul>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <section>
          <h2 className="text-lg font-semibold mb-2">Quick links</h2>
          <ul className="space-y-2">
            <li><Link href="/prices" className="text-amber-400 hover:underline">Fuel prices by city</Link></li>
            <li><Link href="/sufficiency" className="text-amber-400 hover:underline">Stock & days sufficiency</Link></li>
            <li><Link href="/refineries" className="text-amber-400 hover:underline">Refinery status</Link></li>
            <li><Link href="/vessels" className="text-amber-400 hover:underline">Vessel clearance</Link></li>
            <li><Link href="/archive" className="text-amber-400 hover:underline">Archived (truckout, stock)</Link></li>
          </ul>
        </section>
        <section>
          <h2 className="text-lg font-semibold mb-2">Recent performance highlights</h2>
          <table>
            <thead>
              <tr><th>Month</th><th>Metric</th><th>Value</th></tr>
            </thead>
            <tbody>
              {(highlights.data || []).slice(0, 5).map((h, i) => (
                <tr key={i}><td>{h.month}</td><td>{h.metric_name}</td><td>{h.metric_value != null ? h.metric_value : '—'}</td></tr>
              ))}
              {(!highlights.data || highlights.data.length === 0) && (
                <tr><td colSpan={3} className="text-slate-500">No data</td></tr>
              )}
            </tbody>
          </table>
        </section>
      </div>
    </div>
  );
}
