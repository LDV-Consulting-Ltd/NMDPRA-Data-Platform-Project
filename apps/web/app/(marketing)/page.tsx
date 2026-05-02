import Link from 'next/link';
import { fetchApi } from '@/lib/api';
import { MetricCard } from '@/app/components/marketing/MetricCard';
import { FeatureCard } from '@/app/components/marketing/FeatureCard';
import { CoverageBadge } from '@/app/components/marketing/CoverageBadge';
import { CTASection } from '@/app/components/marketing/CTASection';

const CONSULT = 'https://www.ldvconsultingltd.ng/contact-us';

export default async function PlatformLandingPage() {
  let coverage: { data?: Array<{ source_name: string; data_status: string; last_updated?: string }> } = {};
  let highlights: { data?: Array<{ month: string; metric_name: string; metric_value: number }> } = {};
  let prices: {
    data?: Array<{ month: string; city: string; avg_price: number | null }>;
    last_updated?: string;
  } = {};
  let sufficiencySeries: { data?: Array<{ series_name: string; value: number }> } = {};
  try {
    const chunk = await Promise.all([
      fetchApi<typeof coverage>('/v1/coverage').catch(() => ({}) as typeof coverage),
      fetchApi<typeof highlights>('/v1/highlights?per_page=8').catch(() => ({}) as typeof highlights),
      fetchApi<typeof prices>('/v1/prices/fuel', { per_page: '200' }).catch(() => ({}) as typeof prices),
      fetchApi<typeof sufficiencySeries>('/v1/charts/series', { per_page: '50' }).catch(
        () => ({}) as typeof sufficiencySeries
      ),
    ]);
    coverage = chunk[0];
    highlights = chunk[1];
    prices = chunk[2];
    sufficiencySeries = chunk[3];
  } catch {
    /* graceful empty */
  }

  const pmsSuf = sufficiencySeries.data?.find(
    (s) => s.series_name?.toLowerCase().includes('total') || s.series_name?.toLowerCase().includes('sufficiency')
  );
  const priceVals = (prices.data || []).map((r) => r.avg_price).filter((x): x is number => x != null);
  const minP = priceVals.length ? Math.min(...priceVals) : null;
  const maxP = priceVals.length ? Math.max(...priceVals) : null;

  const feeds =
    coverage.data?.map((c) => ({
      name: c.source_name,
      status: c.data_status === 'no_data' ? 'Pending' : c.data_status,
      updated: c.last_updated,
    })) ?? [];

  return (
    <>
      <section className="relative overflow-hidden rounded-2xl border border-teal-900/40 bg-gradient-to-br from-[#0a1628] via-[#0d2137] to-[#051018] px-6 py-14 shadow-2xl shadow-black/40 lg:px-12 lg:py-16">
        <div className="pointer-events-none absolute -right-20 -top-20 h-64 w-64 rounded-full bg-teal-500/10 blur-3xl" />
        <div className="relative grid gap-10 lg:grid-cols-2 lg:items-center">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-teal-400/90">
              National downstream regulatory intelligence
            </p>
            <h1 className="mt-3 text-3xl font-bold tracking-tight text-white sm:text-4xl lg:text-5xl">
              Downstream Regulatory Intelligence Platform
            </h1>
            <p className="mt-4 max-w-xl text-lg leading-relaxed text-slate-400">
              Transform fragmented downstream petroleum regulatory reports into structured data, governed APIs, and
              decision-ready intelligence.
            </p>
            <div className="mt-8 flex flex-wrap gap-4">
              <Link
                href="/demo"
                className="rounded-lg bg-gradient-to-r from-amber-500 to-amber-600 px-6 py-3 font-semibold text-slate-950 shadow-lg shadow-amber-900/30 transition hover:from-amber-400"
              >
                Open Demo
              </Link>
              <a
                href={CONSULT}
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-lg border border-teal-500/50 px-6 py-3 font-semibold text-teal-200 transition hover:bg-teal-950/40"
              >
                Consult LDV
              </a>
            </div>
          </div>
          <div className="rounded-xl border border-slate-700/80 bg-slate-950/60 p-5 shadow-xl backdrop-blur-sm">
            <p className="mb-4 text-center text-xs font-medium uppercase tracking-wide text-teal-400/80">
              Executive snapshot
            </p>
            <div className="grid grid-cols-2 gap-3">
              <MetricCard
                label="PMS days sufficiency signal"
                value={pmsSuf?.value != null ? `${pmsSuf.value.toLocaleString()}` : '—'}
                hint={pmsSuf ? 'From chart series' : 'Awaiting data'}
                accent="teal"
              />
              <MetricCard
                label="Fuel price spread (sample)"
                value={minP != null && maxP != null ? `${minP} – ${maxP}` : '—'}
                hint={priceVals.length ? 'NGN/L across cities' : 'Awaiting data'}
              />
              <MetricCard label="Refinery utilization" value="—" hint="Published fact sheets" accent="teal" />
              <MetricCard label="Vessel clearance activity" value="—" hint="Schedule feeds" />
              <MetricCard
                label="Active feeds"
                value={feeds.filter((f) => f.status !== 'Pending' && f.status !== 'no_data').length}
                hint={`${feeds.length} sources monitored`}
                accent="teal"
              />
            </div>
          </div>
        </div>
      </section>

      <section className="mt-20">
        <h2 className="text-center text-2xl font-semibold text-white">Executive intelligence snapshot</h2>
        <p className="mx-auto mt-2 max-w-2xl text-center text-slate-400">
          Regulatory PDFs are not the final product — they are the source material. LDV converts static reports into a
          governed intelligence layer.
        </p>
        <div className="mt-10 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <MetricCard
            label="Latest sufficiency signal"
            value={pmsSuf?.value ?? '—'}
            accent="teal"
          />
          <MetricCard label="Fuel price range (NGN/L)" value={minP != null ? `${minP} – ${maxP ?? '—'}` : '—'} />
          <MetricCard label="Active / archived feeds" value={`${feeds.length} sources`} hint="Coverage overview below" />
          <MetricCard label="Performance highlights" value={(highlights.data || []).length ? 'Live' : '—'} accent="teal" />
          <MetricCard label="Coverage rows" value={feeds.length} hint="Per-source freshness in Governance" />
          <MetricCard label="Traceability" value="Bronze → Gold" hint="Every metric maps to source PDFs" accent="teal" />
        </div>
      </section>

      <section className="mt-24">
        <h2 className="text-center text-2xl font-semibold text-white">From PDF reports to data product</h2>
        <div className="mx-auto mt-10 max-w-4xl">
          <div className="flex flex-wrap items-center justify-center gap-3 text-sm text-slate-400">
            {['Source PDFs', 'Bronze extraction', 'Silver normalization', 'Gold dimensional intelligence', 'APIs & dashboard'].map(
              (step, i, arr) => (
                <span key={step} className="flex items-center gap-3">
                  <span className="rounded-full bg-teal-950/80 px-4 py-2 font-medium text-teal-200 ring-1 ring-teal-700/40">
                    {step}
                  </span>
                  {i < arr.length - 1 && <span className="text-teal-600">→</span>}
                </span>
              )
            )}
          </div>
          <p className="mt-8 text-center text-slate-500">
            Gold dimensional models power business-facing dashboards and APIs — queryable, comparable, and audit-ready.
          </p>
        </div>
      </section>

      <section className="mt-24">
        <h2 className="mb-10 text-center text-2xl font-semibold text-white">What the platform monitors</h2>
        <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          <FeatureCard title="Fuel price intelligence">City-level indicative pricing from published fact sheets.</FeatureCard>
          <FeatureCard title="Stock & days sufficiency">Days-cover signals across inland, marine, and total pathways.</FeatureCard>
          <FeatureCard title="Refinery status & utilization">Throughput and operational posture where published.</FeatureCard>
          <FeatureCard title="Vessel clearance performance">Submission-to-clearance timelines and remarks.</FeatureCard>
          <FeatureCard title="Truckout & distribution archive">Historical truck movement where datasets remain available.</FeatureCard>
          <FeatureCard title="Gas & infrastructure signals">Where disclosed on Oil & Gas publications.</FeatureCard>
        </div>
      </section>

      <section className="mt-24 rounded-2xl border border-slate-800 bg-slate-900/40 px-6 py-12">
        <h2 className="text-center text-2xl font-semibold text-white">Governance by design</h2>
        <p className="mx-auto mt-3 max-w-2xl text-center text-slate-400">
          Every number should be traceable from a dashboard metric back to the source report.
        </p>
        <ul className="mx-auto mt-8 max-w-2xl list-inside list-disc space-y-2 text-slate-300">
          <li>Data quality checks at ingestion</li>
          <li>Metadata catalog and searchable dictionary</li>
          <li>Lineage from source PDF through Bronze, Silver, and Gold</li>
          <li>Audit-ready APIs for downstream consumers</li>
        </ul>
      </section>

      <section className="mt-24">
        <h2 className="mb-8 text-center text-2xl font-semibold text-white">Data coverage</h2>
        <div className="mx-auto grid max-w-4xl gap-4 md:grid-cols-2">
          <CoverageRow name="OilGasData" badge="Active" />
          <CoverageRow name="VesselSchedule" badge="Active" />
          <CoverageRow name="DailyTruckout" badge="Archived · last 2023" />
          <CoverageRow name="StockReport" badge="Archived · last 2023" />
          <CoverageRow name="DailyGas" badge="Source link" />
        </div>
      </section>

      <section className="mt-24">
        <CTASection />
      </section>
    </>
  );
}

function CoverageRow({ name, badge }: { name: string; badge: string }) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-slate-700/80 bg-slate-900/60 px-4 py-3">
      <span className="font-medium text-slate-200">{name}</span>
      <CoverageBadge status={badge} />
    </div>
  );
}
