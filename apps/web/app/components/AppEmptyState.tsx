import Link from 'next/link';

export function AppEmptyState({ context }: { context?: string }) {
  return (
    <div className="rounded-xl border border-amber-900/40 bg-amber-950/20 px-4 py-4 text-sm text-amber-100/90">
      <p>
        Data has not been loaded yet{context ? ` for ${context}` : ''}. An authorized operator can run the refresh from{' '}
        <Link href="/admin/pipeline" className="font-medium text-amber-400 underline hover:text-amber-300">
          Admin → Pipeline
        </Link>
        .
      </p>
    </div>
  );
}
