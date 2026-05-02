'use client';

import { useState, useEffect } from 'react';

type TableInfo = { table_name: string; row_count: number };
type LayerTables = { layer: string; tables: TableInfo[] };

const LAYER_BUSINESS_NAMES: Record<'bronze' | 'silver' | 'gold', { label: string; description: string }> = {
  bronze: { label: 'Raw', description: 'Landing / source data' },
  silver: { label: 'Curated', description: 'Validated & cleaned' },
  gold: { label: 'Analytics', description: 'Business marts & reporting' },
};

export default function DataLayersPage() {
  const [layer, setLayer] = useState<'bronze' | 'silver' | 'gold'>('bronze');
  const [data, setData] = useState<LayerTables | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sampleTable, setSampleTable] = useState<{ schema: string; table: string } | null>(null);
  const [sampleRows, setSampleRows] = useState<{ columns: string[]; rows: Record<string, unknown>[] } | null>(null);
  const [sampleLoading, setSampleLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetch(`/api/data-layers/tables?layer=${layer}`)
      .then((r) => r.json())
      .then((d) => {
        setData(d);
        setLoading(false);
      })
      .catch((e) => {
        setError(e.message);
        setLoading(false);
      });
  }, [layer]);

  useEffect(() => {
    if (!sampleTable) {
      setSampleRows(null);
      return;
    }
    setSampleLoading(true);
    fetch(`/api/data-layers/tables/${sampleTable.schema}/${sampleTable.table}/sample?limit=20`)
      .then((r) => r.json())
      .then((d) => {
        setSampleRows({ columns: d.columns || [], rows: d.rows || [] });
        setSampleLoading(false);
      })
      .catch(() => {
        setSampleRows(null);
        setSampleLoading(false);
      });
  }, [sampleTable?.schema, sampleTable?.table]);

  return (
    <div>
      <h1 className="mb-4 text-2xl font-bold text-white">Data layers</h1>
      <p className="text-slate-400 text-sm mb-6">
        Browse tables: <strong className="text-slate-300">Raw</strong> (landing), <strong className="text-slate-300">Curated</strong> (validated), <strong className="text-slate-300">Analytics</strong> (business marts).
      </p>

      <div className="flex gap-2 mb-6">
        {(['bronze', 'silver', 'gold'] as const).map((l) => (
          <button
            key={l}
            type="button"
            onClick={() => { setLayer(l); setSampleTable(null); }}
            className={`rounded px-4 py-2 font-medium ${
              layer === l
                ? 'bg-teal-600 text-white shadow-sm shadow-teal-900/40'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            {LAYER_BUSINESS_NAMES[l].label}
          </button>
        ))}
      </div>

      {error && <p className="text-red-400 text-sm mb-4">{error}</p>}
      {loading && <p className="text-slate-500 text-sm">Loading tables…</p>}

      {data && !loading && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <section className="rounded-lg border border-slate-700 bg-slate-900/50 p-4">
            <h2 className="mb-3 text-lg font-semibold text-white">{LAYER_BUSINESS_NAMES[layer].label} tables</h2>
            <p className="text-slate-500 text-xs mb-2">{LAYER_BUSINESS_NAMES[layer].description}</p>
            <ul className="space-y-2">
              {(data.tables || []).map((t) => (
                <li key={t.table_name} className="flex items-center justify-between gap-4 text-sm">
                  <span className="font-mono text-slate-300">{t.table_name}</span>
                  <span className="text-slate-500 tabular-nums">{t.row_count.toLocaleString()} rows</span>
                  <button
                    type="button"
                    onClick={() => setSampleTable({ schema: layer, table: t.table_name })}
                    className="text-teal-400 hover:text-teal-300 hover:underline"
                  >
                    Sample
                  </button>
                </li>
              ))}
              {(data.tables || []).length === 0 && (
                <li className="text-slate-500">No tables in this layer.</li>
              )}
            </ul>
          </section>

          <section className="rounded-lg border border-slate-700 bg-slate-900/50 p-4">
            <h2 className="text-lg font-semibold text-amber-400 mb-3">
              {sampleTable ? `${LAYER_BUSINESS_NAMES[sampleTable.schema as keyof typeof LAYER_BUSINESS_NAMES].label} · ${sampleTable.table}` : 'Sample data'}
            </h2>
            {!sampleTable && (
              <p className="text-slate-500 text-sm">Click &quot;Sample&quot; on a table to view rows.</p>
            )}
            {sampleTable && sampleLoading && <p className="text-slate-500 text-sm">Loading…</p>}
            {sampleTable && sampleRows && !sampleLoading && (
              <div className="overflow-x-auto">
                <table className="w-full text-sm border-collapse">
                  <thead>
                    <tr>
                      {(sampleRows.columns || []).map((c) => (
                        <th key={c} className="border-b border-slate-600 p-2 text-left font-mono text-teal-300">
                          {c}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {(sampleRows.rows || []).map((row, i) => (
                      <tr key={i} className="border-b border-slate-700/50">
                        {(sampleRows.columns || []).map((col) => (
                          <td key={col} className="p-2 text-slate-300 font-mono text-xs max-w-[200px] truncate">
                            {row[col] != null ? String(row[col]) : '—'}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
                <p className="text-slate-500 text-xs mt-2">Up to 20 rows.</p>
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
