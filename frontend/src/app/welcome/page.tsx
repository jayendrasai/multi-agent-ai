'use client';

import { FormEvent, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth';

const interests = ['Research Agent', 'Coding Assistant', 'Customer Support', 'Sales Agent', 'Custom'];

export default function WelcomePage() {
  const router = useRouter();
  const { user, isLoading, loadCurrentUser, completeOnboarding } = useAuthStore();
  const [form, setForm] = useState({ workflow_interest: interests[0], team_size: 'Just me', experience_level: 'Exploring' });
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { void loadCurrentUser(); }, [loadCurrentUser]);
  useEffect(() => { if (!isLoading && !user) router.replace('/login'); }, [isLoading, router, user]);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      await completeOnboarding(form);
      router.replace('/dashboard');
    } catch {
      setError('We could not save your preferences. Please try again.');
    }
  };

  if (isLoading || !user) return <main className="flex min-h-screen items-center justify-center bg-[#0b1117] text-sm text-slate-400">Preparing your workspace…</main>;
  return <main className="flex min-h-screen items-center justify-center bg-[#0b1117] px-5 py-12 text-slate-100"><section className="w-full max-w-2xl border border-white/10 bg-[#111a23] p-7 sm:p-10"><p className="text-sm font-semibold text-emerald-300">Welcome, {user.display_name}</p><h1 className="mt-3 text-3xl font-semibold text-white">Shape your first workspace</h1><p className="mt-3 max-w-xl text-sm leading-6 text-slate-400">These answers personalize your starting point. You can change direction later.</p><form onSubmit={submit} className="mt-8 space-y-7"><fieldset><legend className="text-sm font-medium text-slate-200">What are you building?</legend><div className="mt-3 grid gap-2 sm:grid-cols-2">{interests.map((interest) => <label key={interest} className={`cursor-pointer border p-3 text-sm ${form.workflow_interest === interest ? 'border-emerald-300 bg-emerald-300/10 text-emerald-100' : 'border-white/10 text-slate-400'}`}><input type="radio" className="sr-only" name="interest" checked={form.workflow_interest === interest} onChange={() => setForm({ ...form, workflow_interest: interest })} />{interest}</label>)}</div></fieldset><label className="block text-sm text-slate-300">Team size<select value={form.team_size} onChange={(event) => setForm({ ...form, team_size: event.target.value })} className="mt-2 w-full border border-white/15 bg-[#0b1117] px-3 py-3 text-white"><option>Just me</option><option>2–10</option><option>11–50</option><option>51+</option></select></label><label className="block text-sm text-slate-300">Experience level<select value={form.experience_level} onChange={(event) => setForm({ ...form, experience_level: event.target.value })} className="mt-2 w-full border border-white/15 bg-[#0b1117] px-3 py-3 text-white"><option>Exploring</option><option>Building workflows</option><option>Production operator</option></select></label>{error && <p role="alert" className="text-sm text-red-200">{error}</p>}<button className="bg-emerald-300 px-5 py-3 text-sm font-semibold text-slate-950">Continue to workspace</button></form></section></main>;
}
