import Image from 'next/image';
import Link from 'next/link';

const COMPANY_URL = 'https://www.ldvconsultingltd.ng/';
const CONSULT_URL = 'https://www.ldvconsultingltd.ng/contact-us';

export function MarketingHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-teal-900/40 bg-[#0a1628]/95 backdrop-blur-md shadow-[0_1px_0_rgba(45,212,191,0.06)]">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-y-3 px-4 py-3 lg:px-6">
        <Link href="/" className="flex min-w-0 shrink items-center">
          <Image
            src="/branding/landing-dual-brand.png"
            alt="LDV Consulting and PetroSight — Downstream Intelligence Platform"
            width={520}
            height={96}
            className="h-9 w-auto max-w-[min(92vw,520px)] object-contain object-left sm:h-10"
            priority
          />
        </Link>

        <nav className="flex flex-wrap items-center justify-end gap-x-1 gap-y-2 text-sm">
          <NavLink href="/">Platform</NavLink>
          <NavLink href="/solutions">Solutions</NavLink>
          <NavLink href="/resources">Resources</NavLink>
          <ExternalNavLink href={COMPANY_URL}>Company</ExternalNavLink>
          <ExternalNavLink href={CONSULT_URL}>Consult</ExternalNavLink>
          <span className="mx-1 hidden h-4 w-px bg-slate-700 sm:inline" aria-hidden />
          <span
            className="cursor-default px-2 py-1.5 text-xs text-slate-500 sm:text-sm"
            title="Enterprise access — contact LDV"
          >
            Sign in
          </span>
          <a
            href={CONSULT_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-md border border-teal-500/40 px-3 py-1.5 text-xs font-medium text-teal-300 transition hover:border-teal-400 hover:bg-teal-950/50 sm:text-sm"
          >
            Request access
          </a>
          <Link
            href="/demo"
            className="rounded-md bg-gradient-to-r from-amber-500 to-amber-600 px-3 py-1.5 text-xs font-semibold text-slate-950 shadow-md shadow-amber-900/30 transition hover:from-amber-400 hover:to-amber-500 sm:text-sm"
          >
            Open Demo
          </Link>
        </nav>
      </div>
    </header>
  );
}

function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      className="rounded-md px-2 py-1.5 text-slate-300 transition hover:bg-white/5 hover:text-white"
    >
      {children}
    </Link>
  );
}

function ExternalNavLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="rounded-md px-2 py-1.5 text-slate-300 transition hover:bg-white/5 hover:text-teal-200"
    >
      {children}
    </a>
  );
}
