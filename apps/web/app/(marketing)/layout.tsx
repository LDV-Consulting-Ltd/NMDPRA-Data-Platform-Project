import { MarketingHeader } from '@/app/components/marketing/MarketingHeader';

export default function MarketingLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-[#070d18]">
      <MarketingHeader />
      <main className="mx-auto max-w-7xl px-4 py-12 lg:px-6">{children}</main>
    </div>
  );
}
