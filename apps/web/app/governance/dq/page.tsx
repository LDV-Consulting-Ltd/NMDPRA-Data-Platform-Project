import { fetchApi } from '@/lib/api';

export default async function GovernanceDQPage() {
  const rules = await fetchApi<{ data: Array<{ rule_name: string; layer: string; table_name: string; rule_type: string; severity: string }> }>('/v1/governance/dq/rules', { per_page: '50' });
  const results = await fetchApi<{ data: Array<{ table_name: string; passed: boolean; failed_count: number; total_count: number; created_at: string }> }>('/v1/governance/dq/results', { per_page: '20' });

  return (
    <div>
      <h1 className="text-2xl font-bold text-amber-400 mb-4">Governance · Data quality</h1>
      <p className="text-slate-400 mb-6">DQ rules and latest results (pass rate, failures).</p>
      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-2">Latest DQ results</h2>
        <table>
          <thead>
            <tr><th>Table</th><th>Passed</th><th>Failed</th><th>Total</th><th>Created</th></tr>
          </thead>
          <tbody>
            {(results.data || []).map((r, i) => (
              <tr key={i}>
                <td>{r.table_name}</td><td>{r.passed ? 'Yes' : 'No'}</td><td>{r.failed_count}</td><td>{r.total_count}</td><td>{r.created_at || '—'}</td>
              </tr>
            ))}
            {(!results.data || results.data.length === 0) && <tr><td colSpan={5} className="text-slate-500">No results yet</td></tr>}
          </tbody>
        </table>
      </section>
      <section>
        <h2 className="text-lg font-semibold mb-2">DQ rules</h2>
        <table>
          <thead>
            <tr><th>Rule name</th><th>Layer</th><th>Table</th><th>Type</th><th>Severity</th></tr>
          </thead>
          <tbody>
            {(rules.data || []).map((r, i) => (
              <tr key={i}><td>{r.rule_name}</td><td>{r.layer}</td><td>{r.table_name}</td><td>{r.rule_type}</td><td>{r.severity}</td></tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
