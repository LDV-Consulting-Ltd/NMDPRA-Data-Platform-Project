import { CoverageBadge } from '@/app/components/marketing/CoverageBadge';

export function ResourceCard({
  title,
  description,
  url,
  badge,
}: {
  title: string;
  description: string;
  url: string;
  badge: string;
}) {
  return (
    <div className="flex h-full flex-col rounded-xl border border-slate-700/80 bg-slate-900/60 p-5 shadow-md">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h3 className="font-semibold text-slate-100">{title}</h3>
        <CoverageBadge status={badge} />
      </div>
      <p className="mb-4 flex-1 text-sm leading-relaxed text-slate-400">{description}</p>
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex w-fit items-center rounded-md bg-slate-800 px-3 py-2 text-sm font-medium text-teal-300 ring-1 ring-teal-700/40 transition hover:bg-slate-700 hover:ring-teal-500/50"
      >
        Open source
      </a>
    </div>
  );
}
