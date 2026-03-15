'use client';

import { useState, useEffect, useCallback } from 'react';

type DagRun = {
  dag_run_id?: string;
  run_id?: string;
  execution_date?: string;
  state?: 'running' | 'success' | 'failed' | 'queued';
  start_date?: string;
  end_date?: string;
  conf?: { triggered_by?: string };
};

export function PipelineStatusCard() {
  const [runs, setRuns] = useState<DagRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchRuns = useCallback(async () => {
    try {
      const res = await fetch('/api/pipeline/runs?limit=5');
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || 'Failed to load runs');
        return;
      }
      const list = data.runs?.dag_runs ?? data.runs ?? [];
      setRuns(Array.isArray(list) ? list : []);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Request failed');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRuns();
    const interval = setInterval(fetchRuns, 15000);
    return () => clearInterval(interval);
  }, [fetchRuns]);

  const hasRunning = runs.some((r) => r.state === 'running' || r.state === 'queued');
  useEffect(() => {
    if (!hasRunning) return;
    const poll = setInterval(fetchRuns, 5000);
    return () => clearInterval(poll);
  }, [hasRunning, fetchRuns]);

  const runNow = async () => {
    setRunning(true);
    setError(null);
    try {
      const res = await fetch('/api/pipeline/run', { method: 'POST' });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || 'Trigger failed');
        return;
      }
      await fetchRuns();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Request failed');
    } finally {
      setRunning(false);
    }
  };

  const last = runs[0];
  const statusLabel =
    last?.state === 'running' || last?.state === 'queued'
      ? 'Running'
      : last?.state === 'success'
        ? 'Success'
        : last?.state === 'failed'
          ? 'Failed'
          : '—';

  return (
    <section className="rounded-lg border border-slate-700 bg-slate-900/50 p-4">
      <h2 className="text-lg font-semibold text-amber-400 mb-3">Pipeline status</h2>
      {loading && !runs.length ? (
        <p className="text-slate-400 text-sm">Loading…</p>
      ) : (
        <>
          <div className="flex flex-wrap items-center gap-4 mb-3">
            <div>
              <span className="text-slate-500 text-sm">Last run</span>
              <p className="text-slate-200">
                {last?.execution_date
                  ? new Date(last.execution_date).toLocaleString()
                  : last?.start_date
                    ? new Date(last.start_date).toLocaleString()
                    : '—'}
              </p>
            </div>
            <div>
              <span className="text-slate-500 text-sm">Status</span>
              <p className="text-slate-200">
                <span
                  className={
                    statusLabel === 'Running'
                      ? 'text-amber-400'
                      : statusLabel === 'Success'
                        ? 'text-emerald-400'
                        : statusLabel === 'Failed'
                          ? 'text-red-400'
                          : ''
                  }
                >
                  {statusLabel}
                </span>
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={runNow}
              disabled={running || hasRunning}
              className="px-4 py-2 rounded bg-amber-500 text-slate-900 font-medium hover:bg-amber-400 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {running ? 'Triggering…' : hasRunning ? 'Run in progress…' : 'Run now'}
            </button>
            <button
              type="button"
              onClick={() => { setLoading(true); fetchRuns(); }}
              className="px-4 py-2 rounded border border-slate-600 text-slate-300 text-sm hover:bg-slate-800"
            >
              Refresh
            </button>
          </div>
          {error && (
            <p className="mt-2 text-sm text-red-400">{error}</p>
          )}
        </>
      )}
    </section>
  );
}
