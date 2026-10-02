'use client';

import { useMemo, useState } from 'react';
import { Background, Controls, Edge, MarkerType, MiniMap, Node, ReactFlow } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { WorkflowNode } from '@/lib/api';
import { AgentEvent } from '@/store';

interface Props {
  events: AgentEvent[];
  persistedNodes: WorkflowNode[];
}

interface GraphRecord {
  id: string;
  name: string;
  type: string;
  status: string;
  inputs: unknown;
  outputs: unknown;
  retries: number;
  duration: number | null;
  startedAt: string | null;
  completedAt: string | null;
  parentId: string | null;
  events: AgentEvent[];
}

const agentColors: Record<string, string> = {
  planner: '#2563eb',
  router: '#d97706',
  'task router': '#d97706',
  researcher: '#059669',
  analyst: '#7c3aed',
  critic: '#dc2626',
  synthesizer: '#0891b2',
  validator: '#db2777',
};

const lanePositions: Record<string, { x: number; y: number }> = {
  planner: { x: 40, y: 150 },
  router: { x: 280, y: 150 },
  'task router': { x: 280, y: 150 },
  researcher: { x: 530, y: 65 },
  analyst: { x: 530, y: 240 },
  critic: { x: 800, y: 150 },
  synthesizer: { x: 1065, y: 150 },
  validator: { x: 1330, y: 150 },
};

const statusStyles: Record<string, { border: string; background: string; text: string }> = {
  RUNNING: { border: '#fbbf24', background: 'rgba(251,191,36,.12)', text: '#fef3c7' },
  COMPLETED: { border: '#34d399', background: 'rgba(52,211,153,.12)', text: '#d1fae5' },
  FAILED: { border: '#f87171', background: 'rgba(248,113,113,.12)', text: '#fee2e2' },
  RETRYING: { border: '#fb923c', background: 'rgba(251,146,60,.12)', text: '#ffedd5' },
  PENDING: { border: '#64748b', background: 'rgba(100,116,139,.12)', text: '#cbd5e1' },
};

function eventStatus(events: AgentEvent[], current: string): string {
  const latest = events[events.length - 1]?.event_type;
  if (!latest) return current;
  if (latest === 'NODE_FAILED') return 'FAILED';
  if (latest === 'NODE_RETRYING') return 'RETRYING';
  if (latest === 'NODE_COMPLETED') return 'COMPLETED';
  if (latest === 'NODE_STARTED') return 'RUNNING';
  return current;
}

function displayName(name: string): string {
  return name.replace(/_/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return '—';
  if (typeof value === 'string') return value;
  try { return JSON.stringify(value, null, 2) ?? String(value); } catch { return String(value); }
}

export default function WorkflowGraph({ events, persistedNodes }: Props) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const { nodes, edges, records } = useMemo(() => {
    const eventsByNode = new Map<string, AgentEvent[]>();
    events.forEach((event) => {
      const nodeId = event.payload.node_id;
      if (typeof nodeId !== 'string') return;
      eventsByNode.set(nodeId, [...(eventsByNode.get(nodeId) ?? []), event]);
    });

    const baseRecords = persistedNodes.map((node) => {
      const nodeEvents = eventsByNode.get(node.id) ?? [];
      return {
        id: node.id,
        name: node.node_name,
        type: node.node_type,
        status: eventStatus(nodeEvents, node.status),
        inputs: node.inputs,
        outputs: node.outputs,
        retries: node.retry_count,
        duration: node.execution_duration_ms,
        startedAt: node.started_at,
        completedAt: node.completed_at,
        parentId: node.parent_node_id,
        events: nodeEvents,
      } satisfies GraphRecord;
    });

    const knownIds = new Set(baseRecords.map((record) => record.id));
    eventsByNode.forEach((nodeEvents, id) => {
      if (knownIds.has(id)) return;
      const latest = nodeEvents[nodeEvents.length - 1];
      baseRecords.push({
        id,
        name: typeof latest.payload.node_name === 'string' ? latest.payload.node_name : latest.agent_name,
        type: typeof latest.payload.node_type === 'string' ? latest.payload.node_type : 'agent',
        status: eventStatus(nodeEvents, 'PENDING'),
        inputs: latest.payload.input,
        outputs: latest.payload.output,
        retries: typeof latest.payload.retries === 'number' ? latest.payload.retries : 0,
        duration: typeof latest.payload.duration_ms === 'number' ? latest.payload.duration_ms : null,
        startedAt: null,
        completedAt: null,
        parentId: null,
        events: nodeEvents,
      });
    });

    const occurrences = new Map<string, number>();
    const graphNodes: Node[] = baseRecords.map((record) => {
      const key = record.name.toLowerCase();
      const occurrence = occurrences.get(key) ?? 0;
      occurrences.set(key, occurrence + 1);
      const lane = lanePositions[key] ?? { x: 40 + (occurrence % 4) * 250, y: 420 };
      const color = agentColors[key] ?? '#475569';
      const status = statusStyles[record.status] ?? statusStyles.PENDING;
      return {
        id: record.id,
        position: { x: lane.x + occurrence * 24, y: lane.y + occurrence * 100 },
        data: { label: <div className="min-w-[172px] text-left"><div className="text-[10px] uppercase tracking-[0.16em] opacity-70">{record.type}</div><div className="mt-1 text-sm font-semibold">{displayName(record.name)}</div><div className="mt-2 text-[11px] font-medium uppercase tracking-wider" style={{ color: status.text }}>{record.status}</div>{record.outputs !== null && record.outputs !== undefined && <div className="mt-2 text-[10px] text-emerald-200/80">Output available</div>}</div> },
        style: { background: `linear-gradient(145deg, ${color}, #111a23 90%)`, border: `1px solid ${status.border}`, boxShadow: record.status === 'RUNNING' ? `0 0 24px ${status.border}55` : '0 12px 30px rgba(0,0,0,.25)', borderRadius: 12, color: '#f8fafc', padding: 14, width: 205 },
      };
    });

    const ordered = [...baseRecords].sort((a, b) => (a.startedAt ?? '').localeCompare(b.startedAt ?? '') || a.id.localeCompare(b.id));
    const graphEdges: Edge[] = [];
    ordered.forEach((record, index) => {
      const next = record.parentId ? null : ordered[index + 1];
      const target = record.parentId ? baseRecords.find((candidate) => candidate.id === record.parentId) : next;
      if (!target) return;
      graphEdges.push({ id: `transition-${record.id}-${target.id}`, source: record.id, target: target.id, animated: target.status === 'RUNNING', style: { stroke: target.status === 'FAILED' ? '#f87171' : '#64748b', strokeWidth: 2 }, markerEnd: { type: MarkerType.ArrowClosed, color: target.status === 'FAILED' ? '#f87171' : '#64748b' } });
    });
    return { nodes: graphNodes, edges: graphEdges, records: baseRecords };
  }, [events, persistedNodes]);

  const selected = records.find((record) => record.id === selectedId);
  return <div className="absolute inset-0 min-h-[520px]"><ReactFlow colorMode="dark" nodes={nodes.map((node) => ({ ...node, selected: node.id === selectedId }))} edges={edges} fitView fitViewOptions={{ padding: 0.2 }} snapToGrid snapGrid={[16, 16]} onNodeClick={(_, node) => setSelectedId(node.id)} onPaneClick={() => setSelectedId(null)}><Background color="#475569" gap={24} /><Controls className="opacity-80 hover:opacity-100" /><MiniMap nodeColor={(node) => agentColors[String(node.data?.label ?? '').toLowerCase()] ?? '#475569'} className="!bg-[#0b1117]" maskColor="rgba(11, 17, 23, 0.7)" /></ReactFlow>{selected && <aside className="absolute right-4 top-4 z-10 max-h-[calc(100%-2rem)] w-[min(360px,calc(100%-2rem))] overflow-y-auto border border-white/10 bg-[#111a23]/95 p-5 shadow-2xl backdrop-blur"><div className="flex items-start justify-between gap-3"><div><p className="text-[10px] uppercase tracking-[0.16em] text-emerald-300">{selected.type}</p><h3 className="mt-1 font-semibold text-white">{displayName(selected.name)}</h3></div><button type="button" onClick={() => setSelectedId(null)} className="text-xs text-slate-500 hover:text-white">Close</button></div><dl className="mt-5 grid grid-cols-2 gap-3 text-xs"><div><dt className="text-slate-500">Status</dt><dd className="mt-1 text-slate-200">{selected.status}</dd></div><div><dt className="text-slate-500">Duration</dt><dd className="mt-1 text-slate-200">{selected.duration === null ? '—' : `${selected.duration} ms`}</dd></div><div><dt className="text-slate-500">Retries</dt><dd className="mt-1 text-slate-200">{selected.retries}</dd></div><div><dt className="text-slate-500">Node ID</dt><dd className="mt-1 truncate text-slate-200" title={selected.id}>{selected.id.slice(0, 8)}…</dd></div></dl><div className="mt-5 space-y-4 text-xs"><div><p className="font-semibold uppercase tracking-wider text-slate-500">Input</p><pre className="mt-2 max-h-32 overflow-auto whitespace-pre-wrap border border-white/10 bg-[#0b1117] p-3 text-slate-300">{formatValue(selected.inputs)}</pre></div><div><p className="font-semibold uppercase tracking-wider text-emerald-300">Output</p><pre className="mt-2 max-h-48 overflow-auto whitespace-pre-wrap border border-emerald-300/20 bg-emerald-300/5 p-3 text-emerald-100">{formatValue(selected.outputs)}</pre></div>{selected.events.length > 0 && <div><p className="font-semibold uppercase tracking-wider text-slate-500">Event count</p><p className="mt-2 text-slate-300">{selected.events.length} persisted events</p></div>}</div></aside>}{nodes.length === 0 && <div className="pointer-events-none absolute inset-0 flex items-center justify-center"><p className="border border-white/10 bg-[#111a23] px-5 py-4 text-sm text-slate-400">Waiting for the first agent node…</p></div>}</div>;
}
