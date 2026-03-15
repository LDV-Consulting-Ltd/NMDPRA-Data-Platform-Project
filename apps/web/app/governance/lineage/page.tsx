import { fetchApi } from '@/lib/api';

export default async function GovernanceLineagePage() {
  const nodes = await fetchApi<{ data: Array<{ node_id: string; layer: string; object_name: string; object_type: string }> }>('/v1/governance/lineage/nodes');
  const edges = await fetchApi<{ data: Array<{ from_node_id: string; to_node_id: string; transform_name: string }> }>('/v1/governance/lineage/edges');

  return (
    <div>
      <h1 className="text-2xl font-bold text-amber-400 mb-4">Governance · Lineage</h1>
      <p className="text-slate-400 mb-6">Lineage nodes and edges (Bronze → Silver → Gold). Mermaid diagram in /docs/diagrams/lineage.mmd.</p>
      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-2">Nodes</h2>
        <table>
          <thead>
            <tr><th>Layer</th><th>Object name</th><th>Type</th></tr>
          </thead>
          <tbody>
            {(nodes.data || []).map((n) => (
              <tr key={n.node_id}><td>{n.layer}</td><td>{n.object_name}</td><td>{n.object_type}</td></tr>
            ))}
          </tbody>
        </table>
      </section>
      <section>
        <h2 className="text-lg font-semibold mb-2">Edges</h2>
        <table>
          <thead>
            <tr><th>From</th><th>To</th><th>Transform</th></tr>
          </thead>
          <tbody>
            {(edges.data || []).map((e, i) => (
              <tr key={i}><td>{e.from_node_id}</td><td>{e.to_node_id}</td><td>{e.transform_name || '—'}</td></tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
