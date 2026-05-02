import dynamic from 'next/dynamic';

const MetadataTabs = dynamic(() => import('./MetadataTabs').then((m) => ({ default: m.MetadataTabs })), {
  ssr: false,
  loading: () => <div className="rounded-lg border border-slate-700 bg-slate-900/50 p-8 text-slate-400 text-center">Loading diagrams…</div>,
});

export default function MetadataPage() {
  return (
    <div>
      <h1 className="mb-2 text-2xl font-bold text-white">Metadata</h1>
      <p className="mb-6 text-slate-400">
        Data lineage, data model, and data architecture. Use this tab to see how data flows and how the platform is structured.{' '}
        <a href="/governance/catalog" className="text-teal-400 hover:text-teal-300 hover:underline">
          Data dictionary
        </a>{' '}
        (tables, columns, descriptions) lives under Governance → Catalog.
      </p>
      <MetadataTabs />
    </div>
  );
}
