import { fetchApi } from '@/lib/api';
import { AppEmptyState } from '@/app/components/AppEmptyState';
import { LineageDiagram } from './LineageDiagram';

export const metadata = {
  title: 'Lineage · Governance',
};

export default async function GovernanceLineagePage() {
  let nodes: {
    data?: Array<{ node_id: string; layer: string; object_name: string; object_type: string }>;
  } = {};
  let edges: {
    data?: Array<{ from_node_id: string; to_node_id: string; transform_name: string }>;
  } = {};

  try {
    nodes = await fetchApi<typeof nodes>('/v1/governance/lineage/nodes');
  } catch {
    nodes = {};
  }
  try {
    edges = await fetchApi<typeof edges>('/v1/governance/lineage/edges');
  } catch {
    edges = {};
  }

  const nodeRows = nodes.data || [];
  const edgeRows = edges.data || [];
  const registryEmpty = nodeRows.length === 0 && edgeRows.length === 0;

  return (
    <div className="space-y-10">
      <div>
        <h1 className="mb-2 text-2xl font-bold text-white">Governance · Lineage</h1>
        <p className="max-w-3xl text-slate-400">
          Logical lineage from landing tables through Silver to Gold. The diagram below reflects the platform reference
          model; the tables list API-backed nodes and edges when metadata is published.
        </p>
      </div>

      <LineageDiagram />

      {registryEmpty ? (
        <AppEmptyState context="lineage nodes and edges" />
      ) : (
        <>
          <section>
            <h2 className="mb-4 text-lg font-semibold text-white">Nodes</h2>
            <div className="overflow-x-auto rounded-xl border border-slate-800">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700 text-left text-slate-500">
                    <th className="p-3 font-medium">Layer</th>
                    <th className="p-3 font-medium">Object name</th>
                    <th className="p-3 font-medium">Type</th>
                  </tr>
                </thead>
                <tbody>
                  {nodeRows.map((n) => (
                    <tr key={n.node_id} className="border-b border-slate-800/80">
                      <td className="p-3 text-teal-200/90">{n.layer}</td>
                      <td className="p-3 font-mono text-xs text-slate-300">{n.object_name}</td>
                      <td className="p-3 text-slate-400">{n.object_type}</td>
                    </tr>
                  ))}
                  {nodeRows.length === 0 && (
                    <tr>
                      <td colSpan={3} className="p-4 text-slate-500">
                        No lineage nodes returned.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>

          <section>
            <h2 className="mb-4 text-lg font-semibold text-white">Edges</h2>
            <div className="overflow-x-auto rounded-xl border border-slate-800">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700 text-left text-slate-500">
                    <th className="p-3 font-medium">From</th>
                    <th className="p-3 font-medium">To</th>
                    <th className="p-3 font-medium">Transform</th>
                  </tr>
                </thead>
                <tbody>
                  {edgeRows.map((e, i) => (
                    <tr key={i} className="border-b border-slate-800/80">
                      <td className="p-3 font-mono text-xs text-slate-400">{e.from_node_id}</td>
                      <td className="p-3 font-mono text-xs text-slate-400">{e.to_node_id}</td>
                      <td className="p-3 text-slate-300">{e.transform_name || '—'}</td>
                    </tr>
                  ))}
                  {edgeRows.length === 0 && (
                    <tr>
                      <td colSpan={3} className="p-4 text-slate-500">
                        No lineage edges returned.
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
