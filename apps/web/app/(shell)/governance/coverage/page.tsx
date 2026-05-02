import { fetchApi } from '@/lib/api';
import { GovernanceSummaryCard } from '@/app/components/GovernanceSummaryCard';
import { CoverageBadge } from '@/app/components/marketing/CoverageBadge';

export const metadata = {
  title: 'Coverage · Governance',
};

export default async function GovernanceCoveragePage() {
  let coverage: {
    data?: Array<{
      source_name: string;
      data_status: string;
      min_period: string;
      max_period: string;
      last_updated: string;
    }>;
  } = {};
  let health: {
    data?: {
      last_run_id: string;
      last_run_status: string;
      last_run_finished_at: string;
      failures_count: number;
      data_ready?: boolean;
      ingested_file_count?: number;
      has_successful_run?: boolean;
    };
  } = {};
  try {
    coverage = await fetchApi('/v1/coverage');
    health = await fetchApi('/v1/governance/health/ingestion');
  } catch {
    /* API unavailable */
  }

  const h = health.data;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Governance · Coverage</h1>
        <p className="mt-2 max-w-3xl text-slate-400">
          Dataset coverage, publication ranges, and a concise view of ingestion freshness. Full pipeline controls live
          under <span className="text-slate-300">Admin → Pipeline</span>.
        </p>
      </div>

      <GovernanceSummaryCard
        title="Latest successful ingestion"
        subtitle="Summarized health — not a substitute for operational run history."
      >
        <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <dt className="text-xs uppercase tracking-wide text-slate-500">Data ready</dt>
            <dd className="mt-1 font-medium text-teal-200">{h?.data_ready === true ? 'Yes' : 'No'}</dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wide text-slate-500">Files ingested</dt>
            <dd className="mt-1 font-medium text-slate-200">{h?.ingested_file_count ?? '—'}</dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wide text-slate-500">Last run outcome</dt>
            <dd className="mt-1 font-medium text-slate-200">{h?.last_run_status || '—'}</dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wide text-slate-500">Finished at</dt>
            <dd className="mt-1 text-sm text-slate-300">{h?.last_run_finished_at || '—'}</dd>
          </div>
        </dl>
        <p className="mt-4 text-xs text-slate-500">
          Run identifier: <span className="font-mono text-slate-400">{h?.last_run_id || '—'}</span> · DQ failures last
          run: <span className="text-slate-300">{h?.failures_count ?? '—'}</span>
        </p>
      </GovernanceSummaryCard>

      <section>
        <h2 className="mb-4 text-lg font-semibold text-white">Coverage by source</h2>
        <div className="grid gap-4 md:grid-cols-2">
          {(coverage.data || []).map((c) => (
            <div
              key={c.source_name}
              className="flex flex-col rounded-xl border border-slate-800 bg-slate-900/40 p-5"
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <h3 className="font-semibold text-slate-100">{c.source_name}</h3>
                <CoverageBadge
                  status={
                    c.data_status === 'no_data'
                      ? 'Pending'
                      : c.data_status.charAt(0).toUpperCase() + c.data_status.slice(1)
                  }
                />
              </div>
              <dl className="mt-4 grid gap-2 text-sm">
                <div className="flex justify-between gap-4">
                  <dt className="text-slate-500">Period range</dt>
                  <dd className="text-right text-slate-300">
                    {c.min_period || '—'} → {c.max_period || '—'}
                  </dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-slate-500">Last updated</dt>
                  <dd className="text-right text-teal-200/90">{c.last_updated || '—'}</dd>
                </div>
              </dl>
            </div>
          ))}
          {(!coverage.data || coverage.data.length === 0) && (
            <p className="text-slate-500 md:col-span-2">No coverage rows returned yet.</p>
          )}
        </div>
      </section>
    </div>
  );
}
