import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import type {
  ActivityType,
  LeadStatus,
  PipelineStage,
  TaskPriority,
  TaskStatus,
} from "@/types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
export const stages: PipelineStage[] = [
  "New",
  "Qualified",
  "Contacted",
  "Proposal",
  "Won",
  "Lost",
];
export const statusTone: Record<LeadStatus, string> = {
  Hot: "bg-rose-50 text-rose-700 ring-rose-200",
  Warm: "bg-amber-50 text-amber-700 ring-amber-200",
  Cold: "bg-sky-50 text-sky-700 ring-sky-200",
};
export const stageTone: Record<PipelineStage, string> = {
  New: "bg-slate-100 text-slate-700 ring-slate-200",
  Qualified: "bg-blue-50 text-blue-700 ring-blue-200",
  Contacted: "bg-cyan-50 text-cyan-700 ring-cyan-200",
  Proposal: "bg-violet-50 text-violet-700 ring-violet-200",
  Won: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  Lost: "bg-stone-100 text-stone-600 ring-stone-200",
};
export const taskTone: Record<TaskStatus | string, string> = {
  pending: "bg-blue-50 text-blue-700 ring-blue-200",
  completed: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  cancelled: "bg-slate-100 text-slate-600 ring-slate-200",
};
export const priorityTone: Record<TaskPriority, string> = {
  low: "text-slate-600",
  medium: "text-amber-700",
  high: "text-rose-700",
};
export const activityLabels: Record<ActivityType, string> = {
  lead_created: "Lead created",
  lead_updated: "Lead updated",
  stage_changed: "Stage changed",
  call: "Call",
  email: "Email",
  meeting: "Meeting",
  note: "Note",
};
export const formatCurrency = (value: number) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
export const formatDate = (value: string) =>
  new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value));
export const isOverdue = (due: string, status: TaskStatus) =>
  status === "pending" && new Date(due).getTime() < Date.now();
