'use client';

import { useEffect, useState, useCallback } from 'react';

type StatusPayload = {
  status?: string;
  data_ready?: boolean;
  message?: string | null;
};

export function DataReadinessBanner() {
  const [data, setData] = useState<StatusPayload | null>(null);

  const load = useCallback(async () => {
    try {
      const res = await fetch('/api/pipeline/status', { cache: 'no-store' });
      const j = await res.json().catch(() => ({}));
      if (res.ok) setData(j);
      else setData(null);
    } catch {
      setData(null);
    }
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, 15000);
    return () => clearInterval(t);
  }, [load]);

  if (!data || data.data_ready === true) return null;

  const status = data.status || 'unknown';
  let tone = 'border-amber-500/40 bg-amber-500/10 text-amber-100';
  let text =
    data.message ||
    'Data is being prepared. The platform is running ingestion and modeling in the background.';

  if (status === 'running') {
    tone = 'border-sky-500/40 bg-sky-500/10 text-sky-100';
    text =
      'Refresh in a moment. The latest data refresh is still running.';
  }
  if (status === 'failed') {
    tone = 'border-red-500/40 bg-red-950/40 text-red-100';
    text = 'Latest refresh did not complete successfully. An administrator has been notified.';
  }

  return (
    <div className={`rounded-lg border px-4 py-3 mb-6 text-sm ${tone}`} role="status">
      {text}
    </div>
  );
}
