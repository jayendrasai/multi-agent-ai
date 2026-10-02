'use client';

import { FormEvent, useEffect, useState } from 'react';
import Link from 'next/link';
import { Activity, ArrowRight, Network, Search, ShieldCheck, Sparkles } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { createTask } from '@/lib/api';
import { useTaskStore } from '@/store';
import { useAuthStore } from '@/store/auth';

const examples = [
  'Compare the latest product announcements from two companies and summarize the differences.',
  'What is the weather in Bengaluru today, and what should I pack for an evening walk?',
  'Calculate 184 × 27, explain the result, and format it as a short Markdown note.',
];

const capabilities = [
  { icon: Network, title: 'Graph-native execution', text: 'Watch Planner, Router, Researcher, Analyst, Critic, Synthesizer, and Validator move through a live workflow graph.' },
  { icon: Activity, title: 'Real-time visibility', text: 'Every agent and tool transition is streamed to the run view with timestamps, status, retries, and outputs.' },
  { icon: ShieldCheck, title: 'Recoverable by design', text: 'Checkpoints, validation loops, structured errors, and persisted events keep a failed tool from taking down a run.' },
];

export default function Home() {
  const [prompt, setPrompt] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { addTask } = useTaskStore();
  const { user, loadCurrentUser } = useAuthStore();
  const router = useRouter();

  useEffect(() => { void loadCurrentUser(); }, [loadCurrentUser]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const value = prompt.trim();
    if (!value) return;

    setError(null);
    setIsSubmitting(true);
    try {
      if (!user) {
        window.sessionStorage.setItem('pending_workflow_prompt', value);
        router.push('/signup');
        return;
      }
      const task = await createTask(value);
      addTask(task);
      router.push(`/tasks/${task.id}`);
    } catch (submissionError) {
      setError(submissionError instanceof Error ? submissionError.message : 'Unable to start this workflow.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="min-h-screen bg-[#0b1117] text-slate-100">
      <div className="mx-auto max-w-7xl px-5 py-6 sm:px-8 lg:px-12">
        <header className="flex items-center justify-between border-b border-white/10 pb-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-400 text-slate-950">
              <Sparkles size={20} aria-hidden="true" />
            </div>
            <div>
              <p className="text-sm font-semibold tracking-wide text-white">Orchestrator</p>
              <p className="text-xs text-slate-400">Multi-agent workflow control plane</p>
            </div>
          </div>
          <div className="flex items-center gap-3 text-xs text-slate-400">
            <span className="h-2 w-2 rounded-full bg-emerald-400" aria-hidden="true" />
            <span className="hidden sm:inline">API and workers online</span>
            <Link href={user ? '/dashboard' : '/login'} className="border border-white/10 px-3 py-2 text-slate-300 transition hover:border-emerald-300/50 hover:text-emerald-200">{user ? 'Open workspace' : 'Sign in'}</Link>
          </div>
        </header>

        <section className="grid gap-12 py-16 lg:grid-cols-[1.05fr_0.95fr] lg:items-center lg:py-24">
          <div>
            <p className="mb-5 text-sm font-medium uppercase tracking-[0.2em] text-emerald-300">Design the work. Observe the work.</p>
            <h1 className="max-w-3xl text-4xl font-semibold leading-tight tracking-tight text-white sm:text-6xl">
              Turn a complex request into an accountable execution graph.
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-300">
              Give the platform a goal. Specialized agents plan, route, research, analyze, critique, synthesize, and validate it while you watch every transition.
            </p>

            <div className="mt-10 grid gap-4 sm:grid-cols-3">
              {capabilities.map(({ icon: Icon, title, text }) => (
                <div key={title} className="border-l border-emerald-400/60 pl-4">
                  <Icon className="mb-3 text-emerald-300" size={18} aria-hidden="true" />
                  <h2 className="text-sm font-semibold text-white">{title}</h2>
                  <p className="mt-2 text-sm leading-6 text-slate-400">{text}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="border border-white/10 bg-[#111a23] p-6 shadow-2xl shadow-black/20 sm:p-8">
            <div className="mb-7 flex items-start justify-between gap-4">
              <div>
                <p className="text-xs font-medium uppercase tracking-[0.18em] text-slate-400">New workflow</p>
                <h2 className="mt-2 text-2xl font-semibold text-white">What should the agents solve?</h2>
              </div>
              <Search className="mt-1 text-emerald-300" size={22} aria-hidden="true" />
            </div>
            <form onSubmit={handleSubmit}>
              <label htmlFor="workflow-prompt" className="mb-2 block text-sm font-medium text-slate-200">Task prompt</label>
              <textarea
                id="workflow-prompt"
                className="min-h-36 w-full resize-y border border-white/15 bg-[#0b1117] p-4 text-sm leading-6 text-white outline-none transition focus:border-emerald-300 focus:ring-2 focus:ring-emerald-300/20 disabled:cursor-not-allowed disabled:opacity-60"
                placeholder="Example: Research three options, compare the evidence, and recommend the best one."
                value={prompt}
                onChange={(event) => setPrompt(event.target.value)}
                disabled={isSubmitting}
                maxLength={10000}
              />
              <div className="mt-2 flex justify-between text-xs text-slate-500">
                <span>Use a clear goal and include useful constraints.</span>
                <span>{prompt.length}/10000</span>
              </div>
              {error && <p role="alert" className="mt-4 border border-red-400/40 bg-red-400/10 p-3 text-sm text-red-200">{error}</p>}
              <button
                type="submit"
                disabled={!prompt.trim() || isSubmitting}
                className="mt-6 flex w-full items-center justify-center gap-2 bg-emerald-300 px-5 py-3.5 text-sm font-semibold text-slate-950 transition hover:bg-emerald-200 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isSubmitting ? 'Starting workflow…' : user ? 'Start workflow' : 'Start building'}
                {!isSubmitting && <ArrowRight size={17} aria-hidden="true" />}
              </button>
            </form>

            <div className="mt-8 border-t border-white/10 pt-6">
              <p className="mb-3 text-xs font-medium uppercase tracking-[0.18em] text-slate-500">Try an example</p>
              <div className="space-y-2">
                {examples.map((example) => (
                  <button
                    key={example}
                    type="button"
                    onClick={() => setPrompt(example)}
                    className="block w-full text-left text-sm leading-6 text-slate-400 transition hover:text-emerald-200"
                  >
                    {example}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </section>

        <footer className="border-t border-white/10 py-6 text-xs text-slate-500">
          LangGraph orchestration · PostgreSQL checkpoints · Redis event transport · React Flow visualization
        </footer>
      </div>
    </main>
  );
}
