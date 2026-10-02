import { AgentEvent } from '@/store';

interface Props {
  events: AgentEvent[];
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return '—';
  if (typeof value === 'string') return value;
  try { return JSON.stringify(value, null, 2) ?? String(value); } catch { return String(value); }
}

export default function EventLog({ events }: Props) {
  if (events.length === 0) return <div className="border border-dashed border-white/10 p-6 text-sm italic text-slate-500">No history events yet. They will appear as soon as the workflow begins.</div>;
  return <div className="space-y-3">{events.map((event) => { const output = event.payload.output; const input = event.payload.input; const error = event.payload.error ?? event.payload.message; return <article key={`${event.sequence_number}-${event.id ?? event.event_type}`} className="border border-white/10 bg-[#0e161e] p-4"><div className="flex items-start justify-between gap-3"><div><span className="text-[10px] font-semibold uppercase tracking-[0.16em] text-emerald-300">{event.agent_name}</span><p className="mt-1 text-sm font-medium text-slate-200">{event.event_type.replaceAll('_', ' ')}</p></div><time className="shrink-0 text-[11px] text-slate-500">{new Date(event.timestamp).toLocaleTimeString()}</time></div>{(input !== undefined || output !== undefined || error !== undefined) && <div className="mt-3 space-y-2 text-xs">{input !== undefined && <div><p className="font-semibold uppercase tracking-wider text-slate-600">Input</p><pre className="mt-1 max-h-20 overflow-auto whitespace-pre-wrap text-slate-400">{formatValue(input)}</pre></div>}{output !== undefined && <div className="border-l border-emerald-300/50 pl-3"><p className="font-semibold uppercase tracking-wider text-emerald-300">Output</p><pre className="mt-1 max-h-32 overflow-auto whitespace-pre-wrap text-emerald-100">{formatValue(output)}</pre></div>}{error !== undefined && <div className="border-l border-red-300/50 pl-3"><p className="font-semibold uppercase tracking-wider text-red-300">Error</p><pre className="mt-1 max-h-24 overflow-auto whitespace-pre-wrap text-red-100">{formatValue(error)}</pre></div>}</div>}</article>; })}</div>;
}
