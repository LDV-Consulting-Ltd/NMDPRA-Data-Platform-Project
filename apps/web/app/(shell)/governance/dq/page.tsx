import { fetchApi } from '@/lib/api';
import { AppEmptyState } from '@/app/components/AppEmptyState';

export const metadata = {
  title: 'Data quality · Governance',
};

export default async function GovernanceDQPage() {
  let rules: {
    data?: Array<{ rule_name: string; layer: string; table_name: string; rule_type: string; severity: string }>;
  } = {};
  let results: {
    data?: Array<{
      table_name: string;
      passed: boolean;
      failed_count: number;
      total_count: number;
      created_at: string;
    }>;
  } = {};

  try {
    rules = await fetchApi<typeof rules>('/v1/governance/dq/rules', { per_page: '50' });
  } catch {
    rules = {};
  }
  try {
    results = await fetchApi<typeof results>('/v1/governance/dq/results', { per_page: '20' });
  } catch {
    results = {};
  }

  const ruleRows = rules.data || [];
  const resultRows = results.data || [];
  const empty = ruleRows.length === 0 && resultRows.length === 0;

  return (
    <div>
      <h1 className="mb-2 text-2xl font-bold text-white">Governance · Data quality</h1>
      <p className="mb-8 max-w-3xl text-slate-400">
        Registered DQ rules and latest evaluation outcomes. Operational remediation sits outside this view.
      </p>

      {empty ? (
        <AppEmptyState context="DQ rules and results" />
      ) : (
        <>
          <section className="mb-10">
            <h2 className="mb-4 text-lg font-semibold text-white">Latest DQ results</h2>
            <div className="overflow-x-auto rounded-xl border border-slate-800">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700 text-left text-slate-500">
                    <th className="p-3 font-medium">Table</th>
                    <th className="p-3 font-medium">Passed</th>
                    <th className="p-3 font-medium">Failed</th>
                    <th className="p-3 font-medium">Total</th>
                    <th className="p-3 font-medium">Created</th>
                  </tr>
                </thead>
                <tbody>
                  {resultRows.map((r, i) => (
                    <tr key={i} className="border-b border-slate-800/80">
                      <td className="p-3 font-mono text-xs text-slate-300">{r.table_name}</td>
                      <td className="p-3 text-teal-300">{r.passed ? 'Yes' : 'No'}</td>
                      <td className="p-3 tabular-nums text-slate-300">{r.failed_count}</td>
                      <td className="p-3 tabular-nums text-slate-300">{r.total_count}</td>
                      <td className="p-3 text-slate-400">{r.created_at || '—'}</td>
                    </tr>
                  ))}
                  {resultRows.length === 0 && (
                    <tr>
                      <td colSpan={5} className="p-4 text-slate-500">
                        No result rows yet.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>

          <section>
            <h2 className="mb-4 text-lg font-semibold text-white">DQ rules</h2>
            <div className="overflow-x-auto rounded-xl border border-slate-800">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700 text-left text-slate-500">
                    <th className="p-3 font-medium">Rule name</th>
                    <th className="p-3 font-medium">Layer</th>
                    <th className="p-3 font-medium">Table</th>
                    <th className="p-3 font-medium">Type</th>
                    <th className="p-3 font-medium">Severity</th>
                  </tr>
                </thead>
                <tbody>
                  {ruleRows.map((r, i) => (
                    <tr key={i} className="border-b border-slate-800/80">
                      <td className="p-3 text-slate-300">{r.rule_name}</td>
                      <td className="p-3 text-slate-400">{r.layer}</td>
                      <td className="p-3 font-mono text-xs text-slate-400">{r.table_name}</td>
                      <td className="p-3 text-slate-400">{r.rule_type}</td>
                      <td className="p-3">
                        <span
                          className={
                            r.severity?.toLowerCase() === 'error'
                              ? 'text-red-300'
                              : r.severity?.toLowerCase() === 'warn'
                                ? 'text-amber-200'
                                : 'text-slate-300'
                          }
                        >
                          {r.severity}
                        </span>
                      </td>
                    </tr>
                  ))}
                  {ruleRows.length === 0 && (
                    <tr>
                      <td colSpan={5} className="p-4 text-slate-500">
                        No rules registered yet.
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
