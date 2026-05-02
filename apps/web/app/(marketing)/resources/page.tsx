import { ResourceCard } from '@/app/components/marketing/ResourceCard';

export const metadata = {
  title: 'Resources · Downstream Regulatory Intelligence Platform',
};

const RESOURCES = [
  {
    title: 'Oil & Gas Data',
    url: 'https://www.nmdpra.gov.ng/OilGasData',
    description:
      'Monthly NMDPRA fact sheets with downstream petroleum performance highlights, prices, stock sufficiency, refinery status, and gas/infrastructure indicators.',
    badge: 'Active',
  },
  {
    title: 'Vessel Schedule',
    url: 'https://www.nmdpra.gov.ng/VesselSchedule',
    description:
      'Vessel clearance schedule reports for submission dates, clearance dates, processing timelines, and remarks.',
    badge: 'Active',
  },
  {
    title: 'Daily Truckout',
    url: 'https://www.nmdpra.gov.ng/DailyTruckout',
    description: 'Daily PMS truckout by depot and state. Treat as archived if latest available data remains in 2023.',
    badge: 'Archived',
  },
  {
    title: 'Daily Gas',
    url: 'https://www.nmdpra.gov.ng/DailyGas',
    description: 'Daily gas report source page for gas-related downstream regulatory reporting.',
    badge: 'Source Link',
  },
  {
    title: 'Stock Report',
    url: 'https://www.nmdpra.gov.ng/StockReport',
    description:
      'Petroleum products stock and days sufficiency reports. Treat as archived if latest available data remains in 2023.',
    badge: 'Archived',
  },
];

export default function ResourcesPage() {
  return (
    <div className="space-y-12">
      <div>
        <h1 className="text-3xl font-bold text-white">Resources</h1>
        <p className="mt-2 max-w-3xl text-slate-400">
          Official NMDPRA publication pages that feed the platform’s discovery and ingestion process.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {RESOURCES.map((r) => (
          <ResourceCard key={r.title} title={r.title} description={r.description} url={r.url} badge={r.badge} />
        ))}
      </div>

      <section className="rounded-2xl border border-slate-800 bg-slate-900/50 px-6 py-8">
        <h2 className="text-xl font-semibold text-white">How the platform uses these resources</h2>
        <ol className="mt-4 list-inside list-decimal space-y-2 text-slate-400">
          <li>
            <strong className="text-slate-300">Discovery</strong> — detect new and updated PDFs from official pages.
          </li>
          <li>
            <strong className="text-slate-300">Download</strong> — retrieve files with hash-based change detection.
          </li>
          <li>
            <strong className="text-slate-300">Parsing</strong> — extract tables, metrics, and chart-adjacent values.
          </li>
          <li>
            <strong className="text-slate-300">Data quality</strong> — validate and record checks at landing.
          </li>
          <li>
            <strong className="text-slate-300">Modeling</strong> — Bronze → Silver → Gold dimensional structures.
          </li>
          <li>
            <strong className="text-slate-300">Publishing</strong> — APIs and dashboards over governed datasets.
          </li>
        </ol>
      </section>
    </div>
  );
}
