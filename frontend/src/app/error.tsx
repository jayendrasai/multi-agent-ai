'use client';

import { AlertTriangle, RefreshCw } from 'lucide-react';

export default function GlobalError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[#0b1117] p-6 text-slate-100">
      <section className="w-full max-w-lg border border-red-400/30 bg-[#111a23] p-8">
        <AlertTriangle className="text-red-300" size={28} aria-hidden="true" />
        <h1 className="mt-5 text-2xl font-semibold">Something interrupted the workflow view</h1>
        <p className="mt-3 text-sm leading-6 text-slate-400">The application protected the page from an internal error. Reload the view to reconnect to persisted workflow events.</p>
        <button onClick={reset} className="mt-6 inline-flex items-center gap-2 bg-emerald-300 px-4 py-2.5 text-sm font-semibold text-slate-950"><RefreshCw size={16} aria-hidden="true" /> Reload view</button>
      </section>
    </main>
  );
}
