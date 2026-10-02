'use client';

import { useEffect, useMemo, useState } from 'react';
import { Search, SlidersHorizontal } from 'lucide-react';
import AppShell from '@/components/AppShell';
import RunCard from '@/components/RunCard';
import { fetchHistory, Task } from '@/lib/api';

export default function HistoryPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState('');
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { void fetchHistory(status || undefined).then(setTasks).catch(() => setError('Unable to load workflow history.')); }, [status]);
  const filtered = useMemo(() => tasks.filter((task) => task.prompt.toLowerCase().includes(query.toLowerCase())), [query, tasks]);
  return <AppShell><main className="mx-auto max-w-[1500px] px-5 py-10 sm:px-8"><div><p className="text-sm font-medium uppercase tracking-[0.18em] text-emerald-300">Your record</p><h1 className="mt-3 text-4xl font-semibold text-white">Workflow history</h1><p className="mt-3 text-sm leading-6 text-slate-400">Every run, output, and event stays available to inspect.</p></div><div className="mt-8 flex flex-col gap-3 sm:flex-row"><label className="relative flex-1"><Search size={16} className="absolute left-3 top-3.5 text-slate-500" aria-hidden="true" /><span className="sr-only">Search workflows</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search prompts" className="w-full border border-white/10 bg-[#111a23] py-3 pl-10 pr-3 text-sm text-white outline-none focus:border-emerald-300" /></label><label className="relative"><SlidersHorizontal size={15} className="absolute left-3 top-3.5 text-slate-500" aria-hidden="true" /><span className="sr-only">Filter status</span><select value={status} onChange={(event) => setStatus(event.target.value)} className="w-full appearance-none border border-white/10 bg-[#111a23] py-3 pl-9 pr-10 text-sm text-slate-300 outline-none focus:border-emerald-300 sm:w-44"><option value="">All statuses</option><option value="COMPLETED">Completed</option><option value="RUNNING">Running</option><option value="FAILED">Failed</option><option value="PENDING">Pending</option></select></label></div>{error ? <p role="alert" className="mt-8 border border-red-300/30 bg-red-300/10 p-4 text-sm text-red-200">{error}</p> : filtered.length === 0 ? <div className="mt-8 border border-dashed border-white/15 p-12 text-center text-sm text-slate-400">{query || status ? 'No workflows match these filters.' : 'No workflows yet. Start one from your dashboard.'}</div> : <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-3">{filtered.map((task) => <RunCard key={task.id} task={task} />)}</div>}</main></AppShell>;
}
