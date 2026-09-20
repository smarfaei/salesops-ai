import type {
  Activity,
  AuditLogList,
  AuthResponse,
  DashboardSummary,
  Lead,
  LeadInput,
  LeadIntelligence,
  LeadList,
  PipelineStage,
  SalesTask,
  TaskInput,
  TaskList,
  User,
  UserList,
  UserRole,
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
let accessToken: string | null = null;

export const setAccessToken = (token: string | null) => {
  accessToken = token;
};

async function parseError(response: Response): Promise<string> {
  let message = `Request failed (${response.status})`;
  try {
    const body = await response.json();
    message =
      typeof body.error?.message === "string"
        ? body.error.message
        : typeof body.detail === "string"
          ? body.detail
          : body.detail?.map((e: { msg: string }) => e.msg).join(", ") ||
            message;
  } catch {}
  return message;
}

async function refreshAccessToken(): Promise<AuthResponse> {
  const response = await fetch(`${API_URL}/auth/refresh`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
  });
  if (!response.ok)
    throw new ApiError(await parseError(response), response.status);
  const body = (await response.json()) as AuthResponse;
  setAccessToken(body.access_token);
  return body;
}

async function request<T>(
  path: string,
  init?: RequestInit,
  retried = false,
): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...init?.headers,
    },
  });
  if (response.status === 401 && !retried && !path.startsWith("/auth/")) {
    try {
      await refreshAccessToken();
      return request<T>(path, init, true);
    } catch {
      setAccessToken(null);
    }
  }
  if (!response.ok) {
    throw new ApiError(await parseError(response), response.status);
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
  login: async (email: string, password: string) => {
    const result = await request<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setAccessToken(result.access_token);
    return result;
  },
  refresh: refreshAccessToken,
  me: () => request<User>("/auth/me"),
  logout: async () => {
    try {
      await request<void>("/auth/logout", { method: "POST" });
    } finally {
      setAccessToken(null);
    }
  },
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
  assignLead: (id: number, owner_user_id: number | null) =>
    request<Lead>(`/leads/${id}/owner`, {
      method: "PATCH",
      body: JSON.stringify({ owner_user_id }),
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
  users: () => request<UserList>("/users"),
  assignableUsers: () => request<User[]>("/users/assignable"),
  createUser: (data: {
    email: string;
    full_name: string;
    password: string;
    role: UserRole;
  }) => request<User>("/users", { method: "POST", body: JSON.stringify(data) }),
  updateUser: (
    id: number,
    data: { role?: UserRole; is_active?: boolean; full_name?: string },
  ) =>
    request<User>(`/users/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  auditLogs: () => request<AuditLogList>("/audit-logs"),
};
