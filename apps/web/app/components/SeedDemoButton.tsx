'use client';

import { useState } from 'react';

export function SeedDemoButton() {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const handleSeed = async () => {
    setLoading(true);
    setMessage(null);
    try {
      const res = await fetch('/api/seed-demo', { method: 'POST' });
      const data = await res.json().catch(() => ({}));
      if (res.ok) {
        setMessage('Demo data loaded. Refresh Prices, Sufficiency, Refineries, Gas, Vessels, Archive.');
      } else {
        setMessage(data.error || data.detail || 'Seed failed');
      }
    } catch (e) {
      setMessage(e instanceof Error ? e.message : 'Request failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rounded-lg border border-slate-600 bg-slate-800/50 p-4 mb-6">
      <p className="text-sm text-slate-400 mb-3">
        Insert <strong>sample demo data</strong> for demonstrations when live sources are not yet populated.
      </p>
      <button
        type="button"
        onClick={handleSeed}
        disabled={loading}
        className="px-4 py-2 rounded bg-slate-600 text-slate-200 text-sm font-medium hover:bg-slate-500 disabled:opacity-50"
      >
        {loading ? 'Loading…' : 'Load demo data'}
      </button>
      {message && (
        <p className={`mt-2 text-sm ${message.startsWith('Demo') ? 'text-emerald-400' : 'text-red-400'}`}>
          {message}
        </p>
      )}
    </div>
  );
}
