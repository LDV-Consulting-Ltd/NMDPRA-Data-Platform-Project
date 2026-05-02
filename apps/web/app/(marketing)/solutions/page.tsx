import { FeatureCard } from '@/app/components/marketing/FeatureCard';
import { CTASection } from '@/app/components/marketing/CTASection';

export const metadata = {
  title: 'Solutions · Downstream Regulatory Intelligence Platform',
};

export default function SolutionsPage() {
  return (
    <div className="space-y-20">
      <section>
        <h1 className="text-3xl font-bold text-white">Solutions</h1>
        <p className="mt-2 text-lg text-teal-400/90">A governed regulatory intelligence platform</p>
      </section>

      <section>
        <h2 className="text-2xl font-semibold text-white">Problem</h2>
        <h3 className="mt-4 text-xl text-slate-200">Downstream data is published, but not always usable.</h3>
        <ul className="mt-4 max-w-3xl list-inside list-disc space-y-2 text-slate-400">
          <li>Regulatory reports are often locked in PDFs and static tables.</li>
          <li>Analysts manually copy numbers into spreadsheets — slow and error-prone.</li>
          <li>Decision-makers cannot query trends consistently across months and cities.</li>
          <li>Data lineage and quality are hard to prove for audit and external disclosure.</li>
        </ul>
      </section>

      <section>
        <h2 className="text-2xl font-semibold text-white">Solution</h2>
        <p className="mt-4 max-w-3xl text-slate-400">
          LDV converts static reports into a <strong className="text-slate-200">governed intelligence layer</strong>.
          PDFs are discovered, downloaded, parsed, validated, modeled in Bronze / Silver / Gold, and exposed through APIs
          and dashboards. Gold provides the dimensional analytical layer for executive and operational views.
        </p>
      </section>

      <section>
        <h2 className="mb-8 text-2xl font-semibold text-white">Product capabilities</h2>
        <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          <FeatureCard title="Report discovery & ingestion">Automated discovery from official publication pages.</FeatureCard>
          <FeatureCard title="PDF table extraction">Structured extraction from multi-page regulatory PDFs.</FeatureCard>
          <FeatureCard title="Chart-under-table extraction">Capture chart-adjacent metrics where published.</FeatureCard>
          <FeatureCard title="Data quality & validation">Rules at landing with recorded outcomes.</FeatureCard>
          <FeatureCard title="Metadata & lineage APIs">Trace metrics back to source documents.</FeatureCard>
          <FeatureCard title="Gold dimensional model">Star-schema friendly facts and dimensions.</FeatureCard>
          <FeatureCard title="Dashboard & API access">Consumer-ready interfaces over governed data.</FeatureCard>
          <FeatureCard title="Archived feed monitoring">Historical feeds retained where still published.</FeatureCard>
        </div>
      </section>

      <section>
        <h2 className="mb-8 text-2xl font-semibold text-white">Business value</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[
            'Faster analysis cycles',
            'Better regulatory transparency',
            'Reduced manual reporting effort',
            'AI-ready structured datasets',
            'Improved decision support',
            'Reusable architecture for other regulators',
          ].map((t) => (
            <div
              key={t}
              className="rounded-xl border border-teal-900/40 bg-teal-950/20 px-4 py-4 text-sm text-teal-100/90"
            >
              {t}
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-8 text-2xl font-semibold text-white">Who it serves</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[
            'Regulators & policy teams',
            'Oil marketers',
            'Depot & logistics operators',
            'Financial institutions',
            'Energy researchers',
            'Public sector agencies',
          ].map((t) => (
            <div key={t} className="rounded-lg border border-slate-700 bg-slate-900/50 px-4 py-3 text-slate-300">
              {t}
            </div>
          ))}
        </div>
      </section>

      <CTASection />
    </div>
  );
}
