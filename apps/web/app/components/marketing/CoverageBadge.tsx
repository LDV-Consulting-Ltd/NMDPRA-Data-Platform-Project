export function CoverageBadge({ status }: { status: string }) {
  const s = status.toLowerCase();
  const active = s === 'active' || s === 'ok' || s.indexOf('data') >= 0;
  const archived = s.indexOf('archive') >= 0 || s === 'paused';
  const cls = archived
    ? 'border-slate-600 bg-slate-800/80 text-slate-400'
    : active
      ? 'border-teal-500/40 bg-teal-950/50 text-teal-200'
      : 'border-amber-500/40 bg-amber-950/40 text-amber-200';
  return (
    <span className={`inline-flex rounded-full border px-2.5 py-0.5 text-xs font-medium ${cls}`}>{status}</span>
  );
}
