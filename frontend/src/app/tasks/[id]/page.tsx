'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, CircleAlert, RefreshCw, Wifi, WifiOff } from 'lucide-react';
import { useParams } from 'next/navigation';
import EventLog from '@/components/EventLog';
import WorkflowGraph from '@/components/WorkflowGraph';
import AppShell from '@/components/AppShell';
import { fetchTask, fetchTaskEvents, fetchTaskNodes, Task, WorkflowNode } from '@/lib/api';
import { useAgentWebSocket } from '@/hooks/useAgentWebSocket';
import { AgentEvent, useEventStore } from '@/store';

const terminalStatuses = new Set(['COMPLETED', 'FAILED', 'PARTIAL_COMPLETED']);
const EMPTY_EVENTS: AgentEvent[] = [];

export default function TaskView() {
  const params = useParams();
  const taskId = params.id as string;
  const [task, setTask] = useState<Task | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [persistedNodes, setPersistedNodes] = useState<WorkflowNode[]>([]);
  const { isConnected, reconnectAttempt } = useAgentWebSocket(taskId);
  const events = useEventStore((state) => state.eventsByTask[taskId] ?? EMPTY_EVENTS);
  const addEvent = useEventStore((state) => state.addEvent);

  const loadTask = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const [nextTask, history, nodes] = await Promise.all([
        fetchTask(taskId),
        fetchTaskEvents(taskId),
        fetchTaskNodes(taskId),
      ]);
      setTask(nextTask);
      setPersistedNodes(nodes);
      history.forEach((event) => addEvent(taskId, { ...event, timestamp: event.created_at }));
      setError(null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Unable to load this workflow.');
    } finally {
      setIsRefreshing(false);
    }
  }, [addEvent, taskId]);

  useEffect(() => {
    const initialLoad = window.setTimeout(() => void loadTask(), 0);
    const poller = window.setInterval(() => void loadTask(), 2500);
    return () => {
      window.clearTimeout(initialLoad);
      window.clearInterval(poller);
    };
  }, [loadTask]);

  if (error && !task) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[#0b1117] p-6 text-slate-100">
        <section className="w-full max-w-lg border border-red-400/30 bg-[#111a23] p-8">
          <CircleAlert className="text-red-300" size={28} aria-hidden="true" />
          <h1 className="mt-5 text-2xl font-semibold">Workflow could not be loaded</h1>
          <p className="mt-3 text-sm leading-6 text-slate-400">{error}</p>
          <button onClick={() => void loadTask()} className="mt-6 inline-flex items-center gap-2 bg-emerald-300 px-4 py-2.5 text-sm font-semibold text-slate-950">
            <RefreshCw size={16} aria-hidden="true" /> Try again
          </button>
        </section>
      </main>
    );
  }

  if (!task) {
    return <main className="flex min-h-screen items-center justify-center bg-[#0b1117] text-sm text-slate-300" aria-busy="true">Loading workflow…</main>;
  }

  const isTerminal = terminalStatuses.has(task.status);
  const statusColor = task.status === 'FAILED' ? 'text-red-200 bg-red-400/15 border-red-400/30' : task.status === 'COMPLETED' ? 'text-emerald-200 bg-emerald-400/15 border-emerald-400/30' : 'text-amber-200 bg-amber-400/15 border-amber-400/30';

  return (
    <AppShell>
    <main className="flex h-screen flex-col bg-[#0b1117] text-slate-100">
      <header className="border-b border-white/10 bg-[#111a23] px-5 py-4 sm:px-8">
        <div className="mx-auto flex max-w-[1600px] items-center justify-between gap-6">
          <div className="min-w-0">
            <div className="mb-3 flex flex-wrap items-center gap-4 text-xs font-medium text-slate-400">
              <Link href="/dashboard" className="inline-flex items-center gap-1.5 transition hover:text-emerald-200">
                <ArrowLeft size={14} aria-hidden="true" /> Dashboard
              </Link>
              <span className="text-slate-600">|</span>
              <Link href="/history" className="inline-flex items-center gap-1.5 transition hover:text-emerald-200">
                History
              </Link>
            </div>
            <h1 className="truncate text-lg font-semibold text-white sm:text-xl">Workflow run</h1>
            <p className="mt-1 truncate text-sm text-slate-400" title={task.prompt}>{task.prompt}</p>
          </div>
          <div className="flex shrink-0 items-center gap-3">
            <div className="hidden items-center gap-2 text-xs text-slate-400 sm:flex" role="status">
              {isConnected ? <Wifi size={15} className="text-emerald-300" aria-hidden="true" /> : <WifiOff size={15} className="text-amber-300" aria-hidden="true" />}
              {isConnected ? 'Live events' : reconnectAttempt > 0 ? `Reconnecting (${reconnectAttempt})` : 'Connecting'}
            </div>
            <span className={`border px-3 py-1.5 text-xs font-semibold ${statusColor}`}>{task.status}</span>
          </div>
        </div>
      </header>

      <div className="mx-auto flex w-full max-w-[1600px] flex-1 min-h-0 flex-col gap-4 p-4 sm:p-6 lg:flex-row">
        <section className="flex min-h-[520px] flex-1 flex-col border border-white/10 bg-[#111a23] lg:min-h-0">
          <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
            <div>
              <h2 className="text-sm font-semibold text-white">Execution graph</h2>
              <p className="mt-1 text-xs text-slate-500">Agents and tools appear as they execute.</p>
            </div>
            <button onClick={() => void loadTask()} disabled={isRefreshing} className="inline-flex items-center gap-2 border border-white/10 px-3 py-2 text-xs text-slate-300 transition hover:border-emerald-300/60 hover:text-emerald-200 disabled:opacity-50">
              <RefreshCw size={14} className={isRefreshing ? 'animate-spin' : ''} aria-hidden="true" /> Refresh
            </button>
          </div>
          {!isConnected && !isTerminal && <div role="status" className="border-b border-amber-300/20 bg-amber-300/10 px-5 py-3 text-xs text-amber-100">Live connection unavailable. Persisted events will replay when it reconnects.</div>}
          {task.status === 'FAILED' && <div role="alert" className="border-b border-red-300/20 bg-red-300/10 px-5 py-3 text-xs text-red-100">This workflow failed safely. Review the event log for the failed node, then retry or resume from a checkpoint.</div>}
          <div className="relative min-h-0 flex-1 bg-[#0e161e]"><WorkflowGraph events={events} persistedNodes={persistedNodes} /></div>
        </section>

        <aside className="flex min-h-0 w-full flex-col border border-white/10 bg-[#111a23] lg:w-[390px]">
          <div className="border-b border-white/10 px-5 py-4"><h2 className="text-sm font-semibold text-white">Run activity</h2><p className="mt-1 text-xs text-slate-500">{events.length} persisted events</p></div>
          <div className="min-h-0 flex-1 overflow-y-auto p-4"><EventLog events={events} /></div>
          {task.final_result && <div className="flex min-h-0 flex-1 flex-col border-t border-white/10 bg-[#0e161e] p-5"><h2 className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-300">Final output</h2><div className="mt-3 min-h-0 flex-1 overflow-y-auto whitespace-pre-wrap text-sm leading-6 text-slate-200">{task.final_result}</div></div>}
        </aside>
      </div>
    </main>
    </AppShell>
  );
}
