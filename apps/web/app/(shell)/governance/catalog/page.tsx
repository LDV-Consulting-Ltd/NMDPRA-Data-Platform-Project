import { fetchApi } from '@/lib/api';
import { AppEmptyState } from '@/app/components/AppEmptyState';

export const metadata = {
  title: 'Catalog · Governance',
};

export default async function GovernanceCatalogPage({
  searchParams,
}: {
  searchParams: Promise<{ search?: string; object_type?: string }>;
}) {
  const { search, object_type } = await searchParams;
  const params: Record<string, string> = { per_page: '50' };
  if (search) params.search = search;
  if (object_type) params.object_type = object_type;

  let res: {
    data?: Array<{
      object_type: string;
      object_name: string;
      description: string | null;
      data_type: string | null;
      tags: string[] | null;
    }>;
  } = {};

  try {
    res = await fetchApi<typeof res>('/v1/governance/metadata/dictionary', params);
  } catch {
    res = {};
  }

  const rows = res.data || [];
  const empty = rows.length === 0;

  return (
    <div>
      <h1 className="mb-2 text-2xl font-bold text-white">Governance · Data dictionary</h1>
      <p className="mb-6 max-w-3xl text-slate-400">
        Searchable catalog of tables, columns, and related objects. Use query parameters{' '}
        <span className="font-mono text-slate-300">search</span> and{' '}
        <span className="font-mono text-slate-300">object_type</span> to narrow results.
      </p>

      {empty ? (
        <AppEmptyState context="metadata dictionary" />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-800">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-700 text-left text-slate-500">
                <th className="p-3 font-medium">Object type</th>
                <th className="p-3 font-medium">Object name</th>
                <th className="p-3 font-medium">Description</th>
                <th className="p-3 font-medium">Data type</th>
                <th className="p-3 font-medium">Tags</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={i} className="border-b border-slate-800/80">
                  <td className="p-3 text-teal-200/80">{r.object_type}</td>
                  <td className="p-3 font-mono text-xs text-slate-300">{r.object_name}</td>
                  <td className="p-3 text-slate-400">{r.description || '—'}</td>
                  <td className="p-3 text-slate-500">{r.data_type || '—'}</td>
                  <td className="p-3 text-slate-500">{r.tags?.join(', ') || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
