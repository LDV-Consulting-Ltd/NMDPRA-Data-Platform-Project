export function MetricCard({
  label,
  value,
  hint,
  accent = 'gold',
}: {
  label: string;
  value: React.ReactNode;
  hint?: string;
  accent?: 'gold' | 'teal';
}) {
  const accentClass =
    accent === 'teal'
      ? 'border-teal-500/30 bg-teal-950/40 text-teal-100'
      : 'border-amber-500/25 bg-amber-950/30 text-amber-50';
  return (
    <div className={`rounded-xl border px-4 py-4 shadow-inner ${accentClass}`}>
      <div className="text-[11px] font-medium uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-1 text-xl font-semibold tabular-nums sm:text-2xl">{value}</div>
      {hint && <div className="mt-2 text-xs text-slate-500">{hint}</div>}
    </div>
  );
}
