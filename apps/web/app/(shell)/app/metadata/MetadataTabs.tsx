'use client';

import { useState } from 'react';
import { MermaidDiagram } from '@/app/components/MermaidDiagram';
import { DATA_ARCHITECTURE_MMD, LINEAGE_MMD, DATA_MODEL_MMD } from '@/lib/diagrams';

const TABS = [
  { id: 'architecture', label: 'Data architecture', code: DATA_ARCHITECTURE_MMD },
  { id: 'lineage', label: 'Data lineage', code: LINEAGE_MMD },
  { id: 'model', label: 'Data model (gold)', code: DATA_MODEL_MMD },
] as const;

export function MetadataTabs() {
  const [active, setActive] = useState<(typeof TABS)[number]['id']>('architecture');
  const current = TABS.find((t) => t.id === active) ?? TABS[0];

  return (
    <section className="rounded-lg border border-slate-700 bg-slate-900/50 overflow-hidden">
      <div className="flex border-b border-slate-700">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActive(tab.id)}
            className={`px-4 py-3 text-sm font-medium transition-colors ${
              active === tab.id
                ? 'border-b-2 border-teal-500 bg-teal-950/40 text-teal-200'
                : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="p-4">
        {active === 'architecture' && (
          <p className="text-slate-500 text-sm mb-3">
            High-level flow: NMDPRA sources → automated ingestion and validation → PostgreSQL schemas (bronze, silver, gold, meta) → APIs → dashboard.
          </p>
        )}
        {active === 'lineage' && (
          <p className="text-slate-500 text-sm mb-3">
            Table-level lineage: Bronze (source-shaped) → Silver (normalized dims + facts) → Gold (star schemas with dim_report).
          </p>
        )}
        {active === 'model' && (
          <p className="text-slate-500 text-sm mb-3">
            Gold layer star schema: dimensions (date, product, location, facility, report) and fact tables linked by foreign keys.
          </p>
        )}
        <MermaidDiagram id={current.id} code={current.code} className="w-full" />
      </div>
    </section>
  );
}
