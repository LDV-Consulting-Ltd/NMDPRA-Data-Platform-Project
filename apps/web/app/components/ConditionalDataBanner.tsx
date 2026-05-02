'use client';

import { usePathname } from 'next/navigation';
import { DataReadinessBanner } from '@/app/components/DataReadinessBanner';

/** Only on operational shell routes — not marketing landing, solutions, or resources. */
export function ConditionalDataBanner() {
  const pathname = usePathname();
  if (!pathname) return null;
  const shell = pathname.startsWith('/app') || pathname.startsWith('/governance');
  if (!shell) return null;
  return <DataReadinessBanner />;
}
