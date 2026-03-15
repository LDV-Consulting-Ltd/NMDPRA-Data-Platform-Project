import { fetchApi } from '@/lib/api';
import { PipelineStatusCard } from '@/app/components/PipelineStatusCard';

export default async function GovernanceCoveragePage() {
  const coverage = await fetchApi<{ data: Array<{ source_name: string; data_status: string; min_period: string; max_period: string; last_updated: string }> }>('/v1/coverage');
  const health = await fetchApi<{ data: { last_run_id: string; last_run_status: string; last_run_finished_at: string; failures_count: number } }>('/v1/governance/health/ingestion');

  return (
    <div>
      <h1 className="text-2xl font-bold text-amber-400 mb-4">Governance · Coverage</h1>
      <p className="text-slate-400 mb-6">Coverage per dataset, last updated, and ingestion health.</p>
      <div className="mb-8">
        <PipelineStatusCard />
      </div>
      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-2">Ingestion health</h2>
        <ul className="space-y-1 text-sm">
          <li>Last run ID: {health.data?.last_run_id || '—'}</li>
          <li>Last run status: {health.data?.last_run_status || '—'}</li>
          <li>Last run finished: {health.data?.last_run_finished_at || '—'}</li>
          <li>DQ failures (last run): {health.data?.failures_count ?? '—'}</li>
        </ul>
      </section>
      <section>
        <h2 className="text-lg font-semibold mb-2">Coverage by source</h2>
        <table>
          <thead>
            <tr><th>Source</th><th>Status</th><th>Min period</th><th>Max period</th><th>Last updated</th></tr>
          </thead>
          <tbody>
            {(coverage.data || []).map((c) => (
              <tr key={c.source_name}>
                <td>{c.source_name}</td><td>{c.data_status}</td><td>{c.min_period || '—'}</td><td>{c.max_period || '—'}</td><td>{c.last_updated || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
