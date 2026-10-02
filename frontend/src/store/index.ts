import { create } from 'zustand';
import { Task, fetchTasks } from '@/lib/api';

interface TaskState {
  tasks: Task[];
  activeTaskId: string | null;
  isLoading: boolean;
  error: string | null;
  fetchTasks: () => Promise<void>;
  setActiveTask: (id: string) => void;
  addTask: (task: Task) => void;
}

export const useTaskStore = create<TaskState>((set) => ({
  tasks: [],
  activeTaskId: null,
  isLoading: false,
  error: null,
  fetchTasks: async () => {
    set({ isLoading: true, error: null });
    try {
      const tasks = await fetchTasks();
      set({ tasks, isLoading: false });
    } catch (error: unknown) {
      if (error instanceof Error) {
        set({ error: error.message, isLoading: false });
      } else {
        set({ error: 'An unknown error occurred', isLoading: false });
      }
    }
  },
  setActiveTask: (id) => set({ activeTaskId: id }),
  addTask: (task) => set((state) => ({ tasks: [task, ...state.tasks] })),
}));

export interface AgentEvent {
  id?: string;
  task_run_id?: string;
  correlation_id?: string;
  event_type: string;
  agent_name: string;
  payload: Record<string, unknown>;
  sequence_number: number;
  timestamp: string;
}

interface EventState {
  eventsByTask: Record<string, AgentEvent[]>;
  addEvent: (taskId: string, event: AgentEvent) => void;
  clearEvents: (taskId: string) => void;
}

export const useEventStore = create<EventState>((set) => ({
  eventsByTask: {},
  addEvent: (taskId, event) => set((state) => {
    const existingEvents = state.eventsByTask[taskId] || [];
    // Ensure we don't add duplicate sequences if replaying
    if (existingEvents.some(e => e.sequence_number === event.sequence_number)) {
      return state;
    }
    const updatedEvents = [...existingEvents, event].sort((a, b) => a.sequence_number - b.sequence_number);
    return {
      eventsByTask: {
        ...state.eventsByTask,
        [taskId]: updatedEvents
      }
    };
  }),
  clearEvents: (taskId) => set((state) => {
    const newEvents = { ...state.eventsByTask };
    delete newEvents[taskId];
    return { eventsByTask: newEvents };
  })
}));

interface GraphState {
  nodes: Record<string, unknown>[];
  edges: Record<string, unknown>[];
  setNodes: (nodes: Record<string, unknown>[]) => void;
  setEdges: (edges: Record<string, unknown>[]) => void;
}

export const useGraphStore = create<GraphState>((set) => ({
  nodes: [],
  edges: [],
  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),
}));
