'use client';

import { FormEvent, useState } from 'react';
import Link from 'next/link';
import { ArrowRight, CircleAlert, Sparkles } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { ApiError } from '@/lib/api';
import { useAuthStore } from '@/store/auth';

export default function SignupPage() {
  const [form, setForm] = useState({ name: '', email: '', username: '', password: '' });
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const router = useRouter();
  const signUp = useAuthStore((state) => state.signUp);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await signUp({ ...form, username: form.username || undefined });
      router.replace('/welcome');
    } catch (submissionError) {
      setError(submissionError instanceof ApiError ? submissionError.message : 'Unable to create your account. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return <main className="flex min-h-screen items-center justify-center bg-[#0b1117] px-5 py-12 text-slate-100"><section className="w-full max-w-md border border-white/10 bg-[#111a23] p-7 sm:p-9"><Link href="/" className="flex items-center gap-3 text-sm font-semibold text-white"><span className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-300 text-slate-950"><Sparkles size={18} aria-hidden="true" /></span> Orchestrator</Link><h1 className="mt-10 text-3xl font-semibold text-white">Build your workspace</h1><p className="mt-2 text-sm leading-6 text-slate-400">Create an account to save every run, output, and event.</p><form onSubmit={submit} className="mt-8 space-y-4"><label className="block text-sm text-slate-300">Name<input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required className="mt-2 w-full border border-white/15 bg-[#0b1117] px-3 py-3 text-white outline-none focus:border-emerald-300" autoComplete="name" /></label><label className="block text-sm text-slate-300">Email<input type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} required className="mt-2 w-full border border-white/15 bg-[#0b1117] px-3 py-3 text-white outline-none focus:border-emerald-300" autoComplete="email" /></label><label className="block text-sm text-slate-300">Username <span className="text-slate-500">(optional)</span><input value={form.username} onChange={(event) => setForm({ ...form, username: event.target.value })} minLength={3} className="mt-2 w-full border border-white/15 bg-[#0b1117] px-3 py-3 text-white outline-none focus:border-emerald-300" autoComplete="username" /></label><label className="block text-sm text-slate-300">Password<input type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} minLength={10} required className="mt-2 w-full border border-white/15 bg-[#0b1117] px-3 py-3 text-white outline-none focus:border-emerald-300" autoComplete="new-password" /></label>{error && <p role="alert" className="flex gap-2 border border-red-400/30 bg-red-400/10 p-3 text-sm text-red-200"><CircleAlert size={17} className="mt-0.5 shrink-0" aria-hidden="true" />{error}</p>}<button disabled={isSubmitting} className="flex w-full items-center justify-center gap-2 bg-emerald-300 px-4 py-3 text-sm font-semibold text-slate-950 disabled:opacity-50">{isSubmitting ? 'Creating workspace…' : 'Create account'}{!isSubmitting && <ArrowRight size={16} aria-hidden="true" />}</button></form><p className="mt-7 text-center text-sm text-slate-500">Already have an account? <Link href="/login" className="text-emerald-300 hover:text-emerald-200">Sign in</Link></p></section></main>;
}
