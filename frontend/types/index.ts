export type LeadStatus = "Hot" | "Warm" | "Cold";
export type PipelineStage =
  "New" | "Qualified" | "Contacted" | "Proposal" | "Won" | "Lost";
export type TaskStatus = "pending" | "completed" | "cancelled";
export type TaskPriority = "low" | "medium" | "high";
export type ActivityType =
  | "lead_created"
  | "lead_updated"
  | "stage_changed"
  | "call"
  | "email"
  | "meeting"
  | "note";

export interface Lead {
  id: number;
  name: string;
  company: string;
  employees: number;
  need: string;
  budget: number;
  score: number;
  status: LeadStatus;
  score_reasons: string[];
  pipeline_stage: PipelineStage;
  created_at: string;
  updated_at: string;
}
export interface LeadInput {
  name: string;
  company: string;
  employees: number;
  need: string;
  budget: number;
}
export interface LeadList {
  items: Lead[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}
export interface Activity {
  id: number;
  lead_id: number;
  type: ActivityType;
  description: string;
  metadata: Record<string, unknown> | null;
  created_at: string;
}
export interface SalesTask {
  id: number;
  lead_id: number;
  title: string;
  description: string | null;
  due_at: string;
  status: TaskStatus;
  priority: TaskPriority;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}
export interface TaskInput {
  title: string;
  description?: string | null;
  due_at: string;
  priority: TaskPriority;
}
export interface TaskList {
  items: SalesTask[];
  total: number;
}
export interface EvidenceSignal {
  signal: string;
  evidence: string;
}
export interface LeadIntelligence {
  id: number;
  lead_id: number;
  qualification_summary: string;
  buying_signals: EvidenceSignal[];
  risks: EvidenceSignal[];
  next_best_action: { action: string; reason: string; priority: TaskPriority };
  follow_up: { subject: string; message: string };
  generated_at: string;
  provider: string;
  model: string | null;
  provider_metadata: Record<string, unknown> | null;
}
export interface MetricItem {
  name: string;
  value: number;
}
export interface DashboardSummary {
  kpis: {
    total_leads: number;
    hot_leads: number;
    qualified_leads: number;
    open_pipeline_value: number;
    won_leads: number;
    pending_tasks: number;
  };
  lead_status_distribution: MetricItem[];
  pipeline_distribution: MetricItem[];
  score_distribution: MetricItem[];
  task_status_distribution: MetricItem[];
}
export interface ApiErrorBody {
  detail?: string | Array<{ loc: (string | number)[]; msg: string }>;
}
