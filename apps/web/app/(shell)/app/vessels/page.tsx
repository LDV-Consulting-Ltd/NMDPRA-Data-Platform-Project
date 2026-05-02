import { fetchApi } from '@/lib/api';
import { AppEmptyState } from '@/app/components/AppEmptyState';

export const metadata = {
  title: 'Vessels · Dashboard',
};

export default async function VesselsPage() {
  let res: {
    data?: Array<{
      report_period: string;
      company: string;
      vessel_name: string;
      processing_days: number | null;
      processing_hours: number | null;
    }>;
    data_status?: string;
    last_updated?: string;
  } = {};

  try {
    res = await fetchApi<typeof res>('/v1/vessels/clearance', { per_page: '50' });
  } catch {
    res = {};
  }

  const rows = res.data || [];
  const empty = rows.length === 0;

  return (
    <div>
      <h1 className="mb-2 text-2xl font-bold text-white">Vessel clearance schedule</h1>
      <p className="mb-6 text-slate-400">
        Clearance timelines from published vessel schedule materials.
      </p>

      {empty ? (
        <AppEmptyState context="vessel clearance" />
      ) : (
        <>
          <div className="mb-6 rounded-lg border border-teal-900/40 bg-teal-950/20 px-4 py-3 text-sm text-teal-100/90">
            Status: {res.data_status ?? '—'} · Last updated: {res.last_updated || '—'} · Rows: {rows.length}
          </div>
          <div className="overflow-x-auto rounded-xl border border-slate-800">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700 text-left text-slate-500">
                  <th className="p-3 font-medium">Report period</th>
                  <th className="p-3 font-medium">Company</th>
                  <th className="p-3 font-medium">Vessel</th>
                  <th className="p-3 font-medium">Processing days</th>
                  <th className="p-3 font-medium">Processing hours</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r, i) => (
                  <tr key={i} className="border-b border-slate-800/80">
                    <td className="p-3 text-slate-300">{r.report_period}</td>
                    <td className="p-3 text-slate-300">{r.company || '—'}</td>
                    <td className="p-3 text-slate-300">{r.vessel_name || '—'}</td>
                    <td className="p-3 tabular-nums text-teal-100">
                      {r.processing_days != null ? r.processing_days : '—'}
                    </td>
                    <td className="p-3 tabular-nums text-teal-100">
                      {r.processing_hours != null ? r.processing_hours : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
