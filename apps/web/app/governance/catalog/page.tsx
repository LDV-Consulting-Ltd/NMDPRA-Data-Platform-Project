import { fetchApi } from '@/lib/api';

export default async function GovernanceCatalogPage({
  searchParams,
}: {
  searchParams: Promise<{ search?: string; object_type?: string }>;
}) {
  const { search, object_type } = await searchParams;
  const params: Record<string, string> = { per_page: '50' };
  if (search) params.search = search;
  if (object_type) params.object_type = object_type;
  const res = await fetchApi<{
    data: Array<{ object_type: string; object_name: string; description: string | null; data_type: string | null; tags: string[] | null }>;
  }>('/v1/governance/metadata/dictionary', params);

  return (
    <div>
      <h1 className="text-2xl font-bold text-amber-400 mb-4">Governance · Data dictionary</h1>
      <p className="text-slate-400 mb-6">Browse metadata catalog (tables, columns, endpoints). Filter via ?search= &amp; object_type=.</p>
      <table>
        <thead>
          <tr><th>Object type</th><th>Object name</th><th>Description</th><th>Data type</th><th>Tags</th></tr>
        </thead>
        <tbody>
          {(res.data || []).map((r, i) => (
            <tr key={i}>
              <td>{r.object_type}</td><td>{r.object_name}</td><td>{r.description || '—'}</td><td>{r.data_type || '—'}</td><td>{r.tags?.join(', ') || '—'}</td>
            </tr>
          ))}
          {(!res.data || res.data.length === 0) && <tr><td colSpan={5} className="text-slate-500">No dictionary entries yet</td></tr>}
        </tbody>
      </table>
    </div>
  );
}
