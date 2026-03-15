import { fetchApi } from '@/lib/api';

export default async function VesselsPage() {
  const res = await fetchApi<{
    data: Array<{ report_period: string; company: string; vessel_name: string; processing_days: number | null; processing_hours: number | null }>;
    data_status: string;
    last_updated: string;
  }>('/v1/vessels/clearance', { per_page: '50' });

  return (
    <div>
      <h1 className="text-2xl font-bold text-amber-400 mb-4">Vessel clearance schedule</h1>
      <div className="banner-coverage mb-4">
        Status: {res.data_status} · Last updated: {res.last_updated || '—'}
      </div>
      <table>
        <thead>
          <tr><th>Report period</th><th>Company</th><th>Vessel</th><th>Processing days</th><th>Processing hours</th></tr>
        </thead>
        <tbody>
          {(res.data || []).map((r, i) => (
            <tr key={i}>
              <td>{r.report_period}</td><td>{r.company || '—'}</td><td>{r.vessel_name || '—'}</td><td>{r.processing_days != null ? r.processing_days : '—'}</td><td>{r.processing_hours != null ? r.processing_hours : '—'}</td>
            </tr>
          ))}
          {(!res.data || res.data.length === 0) && <tr><td colSpan={5} className="text-slate-500">No data</td></tr>}
        </tbody>
      </table>
    </div>
  );
}
