'use client';

import { useEffect, useRef, useState } from 'react';

type Props = { code: string; id: string; className?: string };

export function MermaidDiagram({ code, id, className = '' }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!code || !containerRef.current) return;
    setError(null);
    const el = containerRef.current;
    el.innerHTML = '';

    import('mermaid').then((mermaid) => {
      mermaid.default.initialize({
        startOnLoad: false,
        theme: 'dark',
        securityLevel: 'loose',
        flowchart: { useMaxWidth: true, htmlLabels: true },
        er: { useMaxWidth: true },
      });
      const uid = `mermaid-${id}-${Math.random().toString(36).slice(2, 9)}`;
      mermaid.default
        .render(uid, code)
        .then(({ svg }) => {
          el.innerHTML = svg;
        })
        .catch((err: Error) => {
          setError(err.message || 'Failed to render diagram');
        });
    }).catch(() => setError('Mermaid failed to load'));
  }, [code, id]);

  if (error) {
    return (
      <div className={`rounded border border-slate-600 bg-slate-900/50 p-4 text-red-400 text-sm ${className}`}>
        Diagram error: {error}
        <pre className="mt-2 text-xs text-slate-500 overflow-auto max-h-48">{code.slice(0, 500)}…</pre>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className={`mermaid-diagram rounded border border-slate-700 bg-slate-900/30 overflow-auto min-h-[200px] flex items-center justify-center ${className}`}
    />
  );
}
