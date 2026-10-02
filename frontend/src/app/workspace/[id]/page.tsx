'use client';

import { FormEvent, useEffect, useState } from 'react';
import { ArrowRight, Bot, CircleAlert, Database, Search, Wrench } from 'lucide-react';
import { useParams, useRouter } from 'next/navigation';
import AppShell from '@/components/AppShell';
import { ApiError, createTask } from '@/lib/api';

const agents = ['Planner', 'Task Router', 'Researcher', 'Analyst', 'Critic', 'Synthesizer', 'Validator'];

export default function WorkspacePage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [prompt, setPrompt] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { if (id !== 'new') router.replace(`/tasks/${id}`); }, [id, router]);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!prompt.trim()) return;
    setIsSubmitting(true); setError(null);
    try { const task = await createTask(prompt.trim()); router.push(`/tasks/${task.id}`); }
    catch (submissionError) { setError(submissionError instanceof ApiError ? submissionError.message : 'Unable to start workflow.'); setIsSubmitting(false); }
  };

  return <AppShell><main className="mx-auto flex min-h-[calc(100vh-74px)] max-w-[1600px] flex-col px-4 py-4 sm:px-6"><div className="flex items-center justify-between border border-white/10 bg-[#111a23] px-5 py-4"><div><p className="text-xs uppercase tracking-[0.18em] text-emerald-300">Workspace / New</p><h1 className="mt-1 text-lg font-semibold text-white">Untitled workflow</h1></div><span className="text-xs text-slate-500">Manual trigger · autosave ready</span></div><div className="grid flex-1 gap-4 py-4 lg:grid-cols-[220px_1fr_280px]"><aside className="border border-white/10 bg-[#111a23] p-4"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Agents</p><div className="mt-4 space-y-2">{agents.map((agent) => <div key={agent} className="flex items-center gap-3 border border-white/5 bg-[#0e161e] px-3 py-3 text-sm text-slate-300"><Bot size={15} className="text-emerald-300" aria-hidden="true" />{agent}</div>)}</div><p className="mt-8 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Tools</p><div className="mt-4 space-y-2"><div className="flex items-center gap-3 px-3 py-2 text-sm text-slate-400"><Search size={15} aria-hidden="true" /> Web search</div><div className="flex items-center gap-3 px-3 py-2 text-sm text-slate-400"><Wrench size={15} aria-hidden="true" /> Calculator</div><div className="flex items-center gap-3 px-3 py-2 text-sm text-slate-400"><Database size={15} aria-hidden="true" /> Memory</div></div></aside><section className="relative flex min-h-[560px] flex-col overflow-hidden border border-white/10 bg-[#0e161e] p-8"><div className="pointer-events-none absolute inset-0 opacity-30" style={{ backgroundImage: 'linear-gradient(rgba(148,163,184,.12) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,.12) 1px, transparent 1px)', backgroundSize: '32px 32px' }} /><div className="relative m-auto w-full max-w-2xl border border-emerald-300/30 bg-[#111a23] p-7 shadow-2xl"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-300">Start node</p><h2 className="mt-3 text-2xl font-semibold text-white">What should your agents solve?</h2><p className="mt-2 text-sm leading-6 text-slate-400">The platform will plan, route, execute, critique, synthesize, and validate this request.</p><form onSubmit={submit} className="mt-6"><textarea value={prompt} onChange={(event) => setPrompt(event.target.value)} placeholder="Research a topic, compare options, analyze data, or calculate a result…" className="min-h-36 w-full resize-y border border-white/10 bg-[#0b1117] p-4 text-sm leading-6 text-white outline-none focus:border-emerald-300" maxLength={10000} />{error && <p role="alert" className="mt-3 flex gap-2 text-sm text-red-200"><CircleAlert size={16} className="mt-0.5 shrink-0" aria-hidden="true" />{error}</p>}<button disabled={!prompt.trim() || isSubmitting} className="mt-5 inline-flex items-center gap-2 bg-emerald-300 px-5 py-3 text-sm font-semibold text-slate-950 disabled:opacity-50">{isSubmitting ? 'Starting…' : 'Run workflow'}{!isSubmitting && <ArrowRight size={16} aria-hidden="true" />}</button></form></div></section><aside className="border border-white/10 bg-[#111a23] p-5"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Inspector</p><div className="mt-5 border border-dashed border-white/10 p-4 text-sm leading-6 text-slate-500">Select a node after the run starts to inspect inputs, outputs, retries, and timing.</div></aside></div></main></AppShell>;
}
