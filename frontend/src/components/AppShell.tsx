'use client';

import { ReactNode, useEffect } from 'react';
import Link from 'next/link';
import { History, LayoutDashboard, LogOut, Sparkles } from 'lucide-react';
import { usePathname, useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth';

export default function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isLoading, loadCurrentUser, signOut } = useAuthStore();

  useEffect(() => {
    void loadCurrentUser();
  }, [loadCurrentUser]);

  useEffect(() => {
    if (!isLoading && !user) router.replace('/login');
    if (!isLoading && user && !user.onboarding_completed && pathname !== '/welcome') {
      router.replace('/welcome');
    }
  }, [isLoading, pathname, router, user]);

  if (isLoading || !user || (!user.onboarding_completed && pathname !== '/welcome')) {
    return <main className="flex min-h-screen items-center justify-center bg-[#0b1117] text-sm text-slate-400">Loading workspace…</main>;
  }

  return (
    <div className="min-h-screen bg-[#0b1117] text-slate-100">
      <header className="border-b border-white/10 bg-[#111a23]">
        <div className="mx-auto flex max-w-[1600px] items-center justify-between gap-6 px-5 py-4 sm:px-8">
          <Link href="/dashboard" className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-300 text-slate-950"><Sparkles size={18} aria-hidden="true" /></span>
            <span><span className="block text-sm font-semibold text-white">Orchestrator</span><span className="block text-xs text-slate-500">AI workspace</span></span>
          </Link>
          <nav className="flex items-center gap-1 text-sm" aria-label="Main navigation">
            <Link href="/dashboard" className="inline-flex items-center gap-2 px-3 py-2 text-slate-300 transition hover:bg-white/5 hover:text-white"><LayoutDashboard size={15} aria-hidden="true" /> Dashboard</Link>
            <Link href="/history" className="inline-flex items-center gap-2 px-3 py-2 text-slate-300 transition hover:bg-white/5 hover:text-white"><History size={15} aria-hidden="true" /> History</Link>
          </nav>
          <div className="flex items-center gap-3">
            <span className="hidden text-sm text-slate-400 sm:block">{user.display_name}</span>
            <button type="button" onClick={() => void signOut().then(() => router.replace('/'))} className="inline-flex items-center gap-2 border border-white/10 px-3 py-2 text-xs text-slate-300 transition hover:border-red-300/40 hover:text-red-200"><LogOut size={14} aria-hidden="true" /> Sign out</button>
          </div>
        </div>
      </header>
      {children}
    </div>
  );
}
