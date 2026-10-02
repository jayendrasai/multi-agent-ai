import { config } from './config';

export interface User {
  id: string;
  username: string;
  email: string;
  display_name: string;
  onboarding_completed: boolean;
  created_at: string;
}

export interface Task {
  id: string;
  correlation_id: string;
  status: string;
  prompt: string;
  final_result: string | null;
  created_at: string;
  updated_at: string;
}

export interface TaskEvent {
  id: string;
  task_run_id: string;
  correlation_id: string;
  event_type: string;
  agent_name: string;
  payload: Record<string, unknown>;
  sequence_number: number;
  created_at: string;
}

export interface WorkflowNode {
  id: string;
  task_run_id: string;
  node_type: string;
  node_name: string;
  status: string;
  inputs: unknown;
  outputs: unknown;
  retry_count: number;
  execution_duration_ms: number | null;
  parent_node_id: string | null;
  edge_label: string | null;
  edge_type: string | null;
  position_x: number | null;
  position_y: number | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${config.apiBaseUrl}${path}`, {
    ...init,
    credentials: 'include',
    headers: {
      ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
      ...init?.headers,
    },
  });
  if (!response.ok) {
    let message = 'The request could not be completed.';
    try {
      const body = await response.json() as { detail?: string };
      if (typeof body.detail === 'string') message = body.detail;
    } catch {
      // Keep the generic message when the server does not return JSON.
    }
    throw new ApiError(message, response.status);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const register = (input: { name: string; email: string; username?: string; password: string }) =>
  request<User>('/api/v1/auth/register', { method: 'POST', body: JSON.stringify(input) });

export const login = (input: { identifier: string; password: string }) =>
  request<User>('/api/v1/auth/login', { method: 'POST', body: JSON.stringify(input) });

export const logout = () => request<void>('/api/v1/auth/logout', { method: 'POST' });

export const fetchCurrentUser = () => request<User>('/api/v1/auth/me');

export const createTask = (prompt: string) =>
  request<Task>('/api/v1/tasks', { method: 'POST', body: JSON.stringify({ prompt }) });

export const fetchTasks = () => request<Task[]>('/api/v1/tasks');

export const fetchHistory = (status?: string) =>
  request<Task[]>(`/api/v1/history${status ? `?status=${encodeURIComponent(status)}` : ''}`);

export const fetchTask = (taskId: string) => request<Task>(`/api/v1/tasks/${taskId}`);

export const fetchTaskEvents = (taskId: string) =>
  request<TaskEvent[]>(`/api/v1/tasks/${taskId}/events`);

export const fetchTaskNodes = (taskId: string) =>
  request<WorkflowNode[]>(`/api/v1/tasks/${taskId}/nodes`);

export const updateOnboarding = (input: { workflow_interest: string; team_size: string; experience_level: string }) =>
  request<User>('/api/v1/auth/onboarding', { method: 'PATCH', body: JSON.stringify(input) });
