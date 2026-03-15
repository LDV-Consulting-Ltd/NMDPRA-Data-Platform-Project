import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'NMDPRA Data Product',
  description: 'NMDPRA Data Platform Dashboard',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-950 text-slate-100 font-sans antialiased">
        <header className="border-b border-slate-700 bg-slate-900/80 sticky top-0 z-10">
          <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
            <a href="/" className="text-lg font-semibold text-amber-400">NMDPRA Data Product</a>
            <nav className="flex gap-6">
              <a href="/" className="text-slate-300 hover:text-white">Overview</a>
              <a href="/prices" className="text-slate-300 hover:text-white">Prices</a>
              <a href="/sufficiency" className="text-slate-300 hover:text-white">Sufficiency</a>
              <a href="/refineries" className="text-slate-300 hover:text-white">Refineries</a>
              <a href="/gas" className="text-slate-300 hover:text-white">Gas</a>
              <a href="/vessels" className="text-slate-300 hover:text-white">Vessels</a>
              <a href="/archive" className="text-slate-300 hover:text-white">Archive</a>
              <span className="text-slate-500">|</span>
              <a href="/governance/coverage" className="text-slate-400 hover:text-white">Governance</a>
            </nav>
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-4 py-8">{children}</main>
      </body>
    </html>
  );
}
