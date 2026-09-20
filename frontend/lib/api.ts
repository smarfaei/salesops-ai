import type {
  Activity,
  DashboardSummary,
  Lead,
  LeadInput,
  LeadIntelligence,
  LeadList,
  PipelineStage,
  SalesTask,
  TaskInput,
  TaskList,
} from "@/types";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      message =
        typeof body.detail === "string"
          ? body.detail
          : body.detail?.map((e: { msg: string }) => e.msg).join(", ") ||
            message;
    } catch {}
    throw new ApiError(message, response.status);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
const query = (values: Record<string, string | number | undefined>) => {
  const p = new URLSearchParams();
  Object.entries(values).forEach(([k, v]) => {
    if (v !== undefined && v !== "") p.set(k, String(v));
  });
  return p.size ? `?${p}` : "";
};

export const api = {
  dashboard: () => request<DashboardSummary>("/dashboard/summary"),
  leads: (params: Record<string, string | number | undefined> = {}) =>
    request<LeadList>(`/leads${query(params)}`),
  lead: (id: number) => request<Lead>(`/leads/${id}`),
  createLead: (data: LeadInput) =>
    request<Lead>("/leads", { method: "POST", body: JSON.stringify(data) }),
  updateLead: (id: number, data: Partial<LeadInput>) =>
    request<Lead>(`/leads/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  updateStage: (id: number, stage: PipelineStage) =>
    request<Lead>(`/leads/${id}/stage`, {
      method: "PATCH",
      body: JSON.stringify({ stage }),
    }),
  activities: (id: number) => request<Activity[]>(`/leads/${id}/activities`),
  addActivity: (
    id: number,
    data: { type: "note" | "call" | "email" | "meeting"; description: string },
  ) =>
    request<Activity>(`/leads/${id}/activities`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  tasks: (params: Record<string, string | undefined> = {}) =>
    request<TaskList>(`/tasks${query(params)}`),
  leadTasks: (id: number) => request<TaskList>(`/leads/${id}/tasks`),
  createTask: (id: number, data: TaskInput) =>
    request<SalesTask>(`/leads/${id}/tasks`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  updateTask: (id: number, data: Partial<TaskInput>) =>
    request<SalesTask>(`/tasks/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  completeTask: (id: number) =>
    request<SalesTask>(`/tasks/${id}/complete`, { method: "POST" }),
  cancelTask: (id: number) =>
    request<SalesTask>(`/tasks/${id}/cancel`, { method: "POST" }),
  deleteTask: (id: number) =>
    request<void>(`/tasks/${id}`, { method: "DELETE" }),
  intelligence: (id: number) =>
    request<LeadIntelligence>(`/leads/${id}/intelligence`),
  generateIntelligence: (id: number) =>
    request<LeadIntelligence>(`/leads/${id}/intelligence`, { method: "POST" }),
};
