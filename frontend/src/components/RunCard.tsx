'use client';

import Link from 'next/link';
import { ArrowUpRight, CheckCircle2, CircleAlert, Clock3, LoaderCircle } from 'lucide-react';
import { Task } from '@/lib/api';

const statusIcon: Record<string, typeof CheckCircle2> = { COMPLETED: CheckCircle2, FAILED: CircleAlert, RUNNING: LoaderCircle, PENDING: Clock3 };

export default function RunCard({ task }: { task: Task }) {
  const Icon = statusIcon[task.status] ?? Clock3;
  const statusClass = task.status === 'COMPLETED' ? 'text-emerald-300' : task.status === 'FAILED' ? 'text-red-300' : 'text-amber-300';
  return <Link href={`/tasks/${task.id}`} className="group block border border-white/10 bg-[#111a23] p-5 transition hover:-translate-y-0.5 hover:border-emerald-300/40"><div className="flex items-start justify-between gap-4"><div className="flex min-w-0 items-center gap-2"><Icon size={16} className={`${statusClass} ${task.status === 'RUNNING' ? 'animate-spin' : ''}`} aria-hidden="true" /><span className={`text-xs font-semibold uppercase tracking-[0.14em] ${statusClass}`}>{task.status}</span></div><ArrowUpRight size={16} className="text-slate-500 transition group-hover:text-emerald-300" aria-hidden="true" /></div><p className="mt-4 line-clamp-2 text-sm leading-6 text-slate-200">{task.prompt}</p><p className="mt-5 text-xs text-slate-500">{new Date(task.created_at).toLocaleString()}</p>{task.final_result && <p className="mt-3 line-clamp-2 border-t border-white/10 pt-3 text-xs leading-5 text-slate-400">{task.final_result}</p>}</Link>;
}
