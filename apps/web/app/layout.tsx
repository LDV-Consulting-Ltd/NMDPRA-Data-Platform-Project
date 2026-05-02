import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Downstream Regulatory Intelligence Platform',
  description:
    'National downstream regulatory intelligence — governed data products from NMDPRA public sources.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-[#070d18] font-sans antialiased text-slate-100">{children}</body>
    </html>
  );
}
