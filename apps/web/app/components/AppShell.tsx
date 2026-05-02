import Image from 'next/image';
import Link from 'next/link';

const nav = [
  { href: '/app/overview', label: 'Overview' },
  { href: '/app/prices', label: 'Prices' },
  { href: '/app/sufficiency', label: 'Sufficiency' },
  { href: '/app/refineries', label: 'Refineries' },
  { href: '/app/gas', label: 'Gas' },
  { href: '/app/vessels', label: 'Vessels' },
  { href: '/app/archive', label: 'Archive' },
  { href: '/app/data-layers', label: 'Data layers' },
  { href: '/app/metadata', label: 'Metadata' },
] as const;

const gov = [
  { href: '/governance/coverage', label: 'Coverage' },
  { href: '/governance/dq', label: 'DQ' },
  { href: '/governance/lineage', label: 'Lineage' },
  { href: '/governance/catalog', label: 'Catalog' },
] as const;

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-[#070d18]">
      <header className="sticky top-0 z-40 border-b border-teal-900/30 bg-[#0a1628]/95 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-3 lg:flex-row lg:items-center lg:justify-between lg:px-6">
          <div className="flex flex-wrap items-center gap-3">
            <Link href="/" className="flex items-center">
              <Image
                src="/branding/petrosight-product.png"
                alt="PetroSight — Downstream Intelligence Platform"
                width={220}
                height={72}
                className="h-8 w-auto max-w-[min(52vw,13rem)] object-contain object-left sm:h-9 sm:max-w-[15rem]"
              />
            </Link>
          </div>
          <nav className="flex flex-wrap items-center gap-x-1 gap-y-2 text-xs sm:text-sm">
            {nav.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="rounded-md px-2 py-1.5 text-slate-400 transition hover:bg-white/5 hover:text-teal-200"
              >
                {item.label}
              </Link>
            ))}
            <span className="px-1 text-slate-600">|</span>
            {gov.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="rounded-md px-2 py-1.5 text-slate-500 transition hover:bg-teal-950/40 hover:text-teal-300"
              >
                {item.label}
              </Link>
            ))}
            <span className="px-1 text-slate-600">|</span>
            <Link
              href="/admin/pipeline"
              className="rounded-md px-2 py-1.5 font-medium text-amber-400/90 hover:bg-amber-950/30 hover:text-amber-300"
            >
              Pipeline
            </Link>
            <Link href="/" className="ml-1 rounded-md px-2 py-1.5 text-slate-500 hover:text-white">
              Platform
            </Link>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-8 lg:px-6">{children}</main>
    </div>
  );
}
