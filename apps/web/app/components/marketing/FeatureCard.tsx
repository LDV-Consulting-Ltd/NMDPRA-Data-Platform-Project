export function FeatureCard({
  title,
  children,
  icon,
}: {
  title: string;
  children: React.ReactNode;
  icon?: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-slate-700/80 bg-gradient-to-b from-slate-900/90 to-slate-950/90 p-5 shadow-lg shadow-black/20 transition hover:border-teal-700/50">
      <div className="mb-3 flex items-start gap-3">
        {icon && <div className="text-teal-400">{icon}</div>}
        <h3 className="font-semibold text-slate-100">{title}</h3>
      </div>
      <div className="text-sm leading-relaxed text-slate-400">{children}</div>
    </div>
  );
}
