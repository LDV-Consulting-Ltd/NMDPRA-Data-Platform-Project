'use client';

import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { SeedDemoButton } from '@/app/components/SeedDemoButton';

type Health = {
  api_ready?: boolean;
  db_ready?: boolean;
  airflow_ready?: boolean;
  scheduler_ready?: boolean;
  last_successful_run_finished_at?: string | null;
};

type AdminStatus = {
  latest_run_id?: string | null;
  status?: string;
  triggered_by?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
  current_task?: string | null;
  message?: string | null;
  data_ready?: boolean;
  ingested_file_count?: number;
};

type DbRun = {
  run_id: string;
  triggered_by?: string | null;
  started_at: string | null;
  finished_at: string | null;
  status: string | null;
  notes?: string | null;
};

const AF_UI = typeof window !== 'undefined' ? 'http://localhost:8080' : '';
/** Same-origin when unset so public /v1 rewrites reach FastAPI on Vercel. */
const PUB_API = (process.env.NEXT_PUBLIC_API_URL || '').replace(/\/$/, '');

export function AdminPipelinePanel() {
  const [health, setHealth] = useState<Health | null>(null);
  const [status, setStatus] = useState<AdminStatus | null>(null);
  const [runs, setRuns] = useState<DbRun[]>([]);
  const [afRuns, setAfRuns] = useState<unknown[]>([]);
  const [dqFails, setDqFails] = useState<number | null>(null);
  const [running, setRunning] = useState(false);
  const [queuedLabel, setQueuedLabel] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pollActive, setPollActive] = useState(false);

  const loadHealth = useCallback(async () => {
    try {
      const res = await fetch('/api/pipeline/health', { cache: 'no-store' });
      const j = await res.json().catch(() => ({}));
      if (res.ok) setHealth(j);
    } catch {
      setHealth(null);
    }
  }, []);

  const loadDq = useCallback(async () => {
    if (!PUB_API) return;
    try {
      const res = await fetch(`${PUB_API}/v1/governance/health/ingestion`, { cache: 'no-store' });
      const j = await res.json().catch(() => ({}));
      const n = j?.data?.failures_count;
      if (typeof n === 'number') setDqFails(n);
    } catch {
      setDqFails(null);
    }
  }, []);

  const loadStatus = useCallback(async () => {
    try {
      const res = await fetch('/api/pipeline/admin-status', { cache: 'no-store' });
      const j = await res.json().catch(() => ({}));
      if (res.ok) setStatus(j);
    } catch {
      setStatus(null);
    }
  }, []);

  const loadHistory = useCallback(async () => {
    try {
      const res = await fetch('/api/pipeline/history?limit=30', { cache: 'no-store' });
      const j = await res.json().catch(() => ({}));
      if (res.ok && Array.isArray(j.runs)) setRuns(j.runs);
    } catch {
      setRuns([]);
    }
  }, []);

  const loadAfRuns = useCallback(async () => {
    try {
      const res = await fetch('/api/pipeline/runs?limit=15', { cache: 'no-store' });
      const j = await res.json().catch(() => ({}));
      if (res.ok && Array.isArray(j.runs)) setAfRuns(j.runs);
    } catch {
      setAfRuns([]);
    }
  }, []);

  useEffect(() => {
    loadHealth();
    loadDq();
    loadStatus();
    loadHistory();
    loadAfRuns();
  }, [loadHealth, loadDq, loadStatus, loadHistory, loadAfRuns]);

  useEffect(() => {
    if (!pollActive) return;
    const id = setInterval(() => {
      loadStatus();
      loadHistory();
      loadAfRuns();
      loadDq();
    }, 5000);
    return () => clearInterval(id);
  }, [pollActive, loadStatus, loadHistory, loadAfRuns, loadDq]);

  useEffect(() => {
    if (status?.status === 'running' || queuedLabel) {
      setPollActive(true);
    }
    if (status?.status === 'success' || status?.status === 'failed') {
      setQueuedLabel(false);
      if (status.status === 'success') {
        setPollActive(false);
        if (typeof window !== 'undefined') window.dispatchEvent(new Event('nmdpra-data-refresh'));
      }
      if (status.status === 'failed') {
        setPollActive(false);
      }
    }
  }, [status?.status, queuedLabel]);

  const runPipeline = async () => {
    setRunning(true);
    setError(null);
    setQueuedLabel(true);
    setPollActive(true);
    try {
      const res = await fetch('/api/pipeline/run', { method: 'POST' });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = data?.detail;
        const msg =
          typeof detail === 'object' && detail?.message
            ? String(detail.message)
            : typeof detail === 'string'
              ? detail
              : data?.error || 'Trigger failed';
        setError(msg);
        setQueuedLabel(false);
        setPollActive(false);
        return;
      }
      setTimeout(() => loadStatus(), 2000);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Request failed');
      setQueuedLabel(false);
      setPollActive(false);
    } finally {
      setRunning(false);
    }
  };

  const uiStatus = queuedLabel
    ? 'Queued'
    : status?.status === 'running'
      ? 'Running'
      : status?.status === 'success'
        ? 'Success'
        : status?.status === 'failed'
          ? 'Failed'
          : status?.status || '—';

  const formatWAT = (iso: string | null | undefined): string => {
    if (iso == null || iso === '') return '—';
    const normalized = String(iso).trim().replace(' ', 'T');
    const d = new Date(normalized);
    if (Number.isNaN(d.getTime())) return '—';
    return d.toLocaleString('en-NG', {
      timeZone: 'Africa/Lagos',
      dateStyle: 'short',
      timeStyle: 'short',
    });
  };

  return (
    <div className="space-y-8">
      <section className="rounded-xl border border-slate-700 bg-slate-900/50 p-5">
        <h2 className="mb-3 text-lg font-semibold text-teal-400">Pipeline & engine health</h2>
        {health ? (
          <ul className="space-y-1 text-sm text-slate-300">
            <li>API: {health.api_ready ? 'ready' : 'not ready'}</li>
            <li>Database: {health.db_ready ? 'ready' : 'not ready'}</li>
            <li>Ingestion engine: {health.airflow_ready ? 'ready' : 'not ready'}</li>
            <li>Scheduler signal: {health.scheduler_ready ? 'ok' : 'unknown / warming up'}</li>
            <li>
              Last successful refresh:{' '}
              {health.last_successful_run_finished_at ? formatWAT(health.last_successful_run_finished_at) : '—'}
            </li>
            {dqFails !== null && <li className="text-teal-200/90">DQ checks failing (last run): {dqFails}</li>}
          </ul>
        ) : (
          <p className="text-sm text-slate-500">Could not load health.</p>
        )}
      </section>

      <section className="rounded-xl border border-slate-700 bg-slate-900/50 p-5">
        <h2 className="mb-3 text-lg font-semibold text-teal-400">Run pipeline</h2>
        <p className="mb-3 text-sm text-slate-400">
          Trigger end-to-end ingestion from public sources through validated warehouse tables (authorized operators).
        </p>
        <div className="mb-3 flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={runPipeline}
            disabled={running || queuedLabel || status?.status === 'running'}
            className="rounded-lg bg-gradient-to-r from-amber-500 to-amber-600 px-4 py-2 font-medium text-slate-950 shadow-md hover:from-amber-400 disabled:opacity-50"
          >
            {running ? 'Starting…' : 'Run now'}
          </button>
          <button
            type="button"
            onClick={() => {
              loadHealth();
              loadStatus();
              loadHistory();
              loadAfRuns();
              loadDq();
            }}
            className="rounded-lg border border-slate-600 px-4 py-2 text-sm text-slate-300 hover:bg-slate-800"
          >
            Refresh
          </button>
          <span className="text-slate-300">
            Status: <strong className="text-amber-300">{uiStatus}</strong>
          </span>
        </div>
        {status?.current_task && (
          <p className="mb-2 text-sm text-slate-400">Current step: {status.current_task}</p>
        )}
        {error && <p className="text-sm text-red-400">{error}</p>}
        <p className="mt-2 text-xs text-slate-500">
          Advanced logs (internal):{' '}
          <a href={AF_UI || 'http://localhost:8080'} target="_blank" rel="noopener noreferrer" className="text-teal-400 hover:underline">
            operations console (8080)
          </a>
        </p>
      </section>

      <section className="rounded-xl border border-slate-700 bg-slate-900/50 p-5">
        <h2 className="mb-3 text-lg font-semibold text-teal-400">Run history</h2>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-slate-600">
                <th className="py-2 pr-4 text-left text-slate-500">Run</th>
                <th className="py-2 pr-4 text-left text-slate-500">Started</th>
                <th className="py-2 pr-4 text-left text-slate-500">Finished</th>
                <th className="py-2 pr-4 text-left text-slate-500">Outcome</th>
              </tr>
            </thead>
            <tbody>
              {runs.length === 0 && (
                <tr>
                  <td colSpan={4} className="py-4 text-slate-500">
                    No runs recorded yet.
                  </td>
                </tr>
              )}
              {runs.map((r) => (
                <tr key={r.run_id} className="border-b border-slate-700/50">
                  <td className="py-2 pr-4 font-mono text-xs text-slate-400">{(r.run_id || '').slice(0, 8)}…</td>
                  <td className="py-2 pr-4 text-slate-300">{formatWAT(r.started_at)}</td>
                  <td className="py-2 pr-4 text-slate-300">{formatWAT(r.finished_at)}</td>
                  <td className="py-2 pr-4 text-slate-300">{r.status ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="rounded-xl border border-slate-700 bg-slate-900/50 p-5">
        <h2 className="mb-2 text-lg font-semibold text-teal-400">Engine run identifiers</h2>
        <p className="mb-2 text-xs text-slate-500">Technical identifiers for support.</p>
        <pre className="max-h-48 overflow-x-auto rounded bg-slate-950 p-3 text-xs text-slate-400">
          {JSON.stringify(afRuns.slice(0, 5), null, 2)}
        </pre>
      </section>

      <section className="rounded-xl border border-slate-600 bg-slate-800/50 p-5">
        <h2 className="mb-2 text-lg font-semibold text-slate-300">Demo dataset</h2>
        <p className="mb-3 text-sm text-slate-400">Load sample rows when live sources are unavailable.</p>
        <SeedDemoButton />
      </section>

      <section className="rounded-xl border border-slate-700 bg-slate-900/50 p-5">
        <h2 className="mb-3 text-lg font-semibold text-teal-400">Historical reprocessing</h2>
        <BackfillForm />
      </section>
    </div>
  );
}

function BackfillForm() {
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMsg(null);
    try {
      const res = await fetch('/api/pipeline/backfill', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source: 'oilgasdata' }),
      });
      const data = await res.json().catch(() => ({}));
      setMsg(res.ok ? JSON.stringify(data) : data.detail || data.error || 'Failed');
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={submit} className="flex flex-wrap items-end gap-3">
      <button
        type="submit"
        disabled={loading}
        className="rounded-lg border border-slate-600 px-4 py-2 text-sm text-slate-200 hover:bg-slate-800 disabled:opacity-50"
      >
        {loading ? 'Running…' : 'Run full reprocessing'}
      </button>
      {msg && <span className="max-w-xl truncate font-mono text-xs text-slate-400">{msg}</span>}
    </form>
  );
}
