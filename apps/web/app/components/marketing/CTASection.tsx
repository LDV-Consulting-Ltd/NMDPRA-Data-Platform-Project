import Link from 'next/link';

const CONSULT_URL = 'https://www.ldvconsultingltd.ng/contact-us';

export function CTASection() {
  return (
    <section className="rounded-2xl border border-teal-800/40 bg-gradient-to-br from-slate-900 via-[#0a1628] to-teal-950/40 px-6 py-12 text-center shadow-xl">
      <h2 className="text-2xl font-semibold text-white sm:text-3xl">
        Need this intelligence layer for your organization?
      </h2>
      <p className="mx-auto mt-4 max-w-2xl text-slate-400">
        LDV Consulting helps energy and operational organizations convert fragmented reports, PDFs, and spreadsheets into
        governed data products.
      </p>
      <div className="mt-8 flex flex-wrap justify-center gap-4">
        <a
          href={CONSULT_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="rounded-lg bg-gradient-to-r from-amber-500 to-amber-600 px-6 py-3 font-semibold text-slate-950 shadow-lg shadow-amber-900/25 transition hover:from-amber-400 hover:to-amber-500"
        >
          Consult LDV
        </a>
        <Link
          href="/demo"
          className="rounded-lg border border-teal-500/50 px-6 py-3 font-semibold text-teal-200 transition hover:bg-teal-950/50"
        >
          Open Demo
        </Link>
      </div>
    </section>
  );
}
