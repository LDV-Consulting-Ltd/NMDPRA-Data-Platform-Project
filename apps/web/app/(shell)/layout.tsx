import { AppShell } from '@/app/components/AppShell';
import { ConditionalDataBanner } from '@/app/components/ConditionalDataBanner';

/** Dashboard / governance load live API data — avoid failing static generation when the API is offline. */
export const dynamic = 'force-dynamic';

export default function ShellLayout({ children }: { children: React.ReactNode }) {
  return (
    <AppShell>
      <ConditionalDataBanner />
      {children}
    </AppShell>
  );
}
