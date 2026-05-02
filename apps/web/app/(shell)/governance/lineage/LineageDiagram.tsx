'use client';

import { MermaidDiagram } from '@/app/components/MermaidDiagram';
import { LINEAGE_MMD } from '@/lib/diagrams';

export function LineageDiagram() {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
      <p className="mb-3 text-xs font-medium uppercase tracking-wide text-teal-400/80">
        Reference · Bronze → Silver → Gold
      </p>
      <MermaidDiagram code={LINEAGE_MMD} id="governance-lineage" className="min-h-[280px]" />
    </div>
  );
}
