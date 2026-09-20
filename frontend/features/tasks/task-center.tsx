"use client";
import Link from "next/link";
import { Check, CircleX, Clock3, Pencil, Plus, Trash2 } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { formatDate, isOverdue, priorityTone, taskTone } from "@/lib/utils";
import type { Lead, SalesTask, TaskInput } from "@/types";
import { useApi } from "@/hooks/use-api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input, Label, Select, Textarea } from "@/components/ui/form-controls";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/state";
type View = "pending" | "upcoming" | "overdue" | "completed" | "cancelled";
export function TaskCenter({
  leadId,
  compact = false,
}: {
  leadId?: number;
  compact?: boolean;
}) {
  const [view, setView] = useState<View>("pending");
  const loader = useCallback(
    () =>
      leadId
        ? api.leadTasks(leadId)
        : api.tasks(
            view === "overdue" || view === "upcoming"
              ? { timing: view }
              : { status: view },
          ),
    [leadId, view],
  );
  const { data, loading, error, reload } = useApi(loader);
  const [leads, setLeads] = useState<Lead[]>([]);
  useEffect(() => {
    if (!leadId)
      void api
        .leads({ page_size: 100 })
        .then((x) => setLeads(x.items))
        .catch(() => setLeads([]));
  }, [leadId]);
  const names = useMemo(
    () => Object.fromEntries(leads.map((x) => [x.id, x])),
    [leads],
  );
  const visible = leadId
    ? data?.items.filter((t) =>
        view === "overdue"
          ? isOverdue(t.due_at, t.status)
          : view === "upcoming"
            ? t.status === "pending" && !isOverdue(t.due_at, t.status)
            : t.status === view,
      )
    : data?.items;
  const [editing, setEditing] = useState<SalesTask | null | "new">(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [defaultDue, setDefaultDue] = useState("");
  const beginCreate = () => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    setDefaultDue(tomorrow.toISOString());
    setEditing("new");
  };
  const mutate = async (action: () => Promise<unknown>) => {
    setActionError(null);
    try {
      await action();
      await reload();
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Task action failed");
    }
  };
  return (
    <Card>
      <CardHeader>
        <div>
          <h2 className="font-bold">{leadId ? "Lead tasks" : "Task Center"}</h2>
          <p className="mt-1 text-xs text-slate-500">
            Follow-ups that keep the pipeline moving
          </p>
        </div>
        {leadId && (
          <Button size="sm" onClick={beginCreate}>
            <Plus className="size-4" />
            Create task
          </Button>
        )}
      </CardHeader>
      <CardContent>
        <div className="mb-4 flex flex-wrap gap-2">
          {(
            [
              "pending",
              "upcoming",
              "overdue",
              "completed",
              "cancelled",
            ] as View[]
          ).map((x) => (
            <Button
              key={x}
              size="sm"
              variant={view === x ? "default" : "outline"}
              onClick={() => setView(x)}
              className="capitalize"
            >
              {x}
            </Button>
          ))}
        </div>
        {editing && (leadId || editing !== "new") && (
          <TaskForm
            leadId={leadId ?? (editing === "new" ? 0 : editing.lead_id)}
            task={editing === "new" ? undefined : editing}
            defaultDue={defaultDue}
            onDone={async () => {
              setEditing(null);
              await reload();
            }}
            onCancel={() => setEditing(null)}
          />
        )}{" "}
        {actionError && (
          <p
            role="alert"
            className="mb-4 rounded-lg bg-rose-50 p-3 text-sm text-rose-700"
          >
            {actionError}
          </p>
        )}
        {loading ? (
          <LoadingState label="Loading tasks" />
        ) : error ? (
          <ErrorState message={error} onRetry={reload} />
        ) : !visible?.length ? (
          <EmptyState
            title={`No ${view} tasks`}
            description={
              leadId
                ? "Create a focused next step for this lead."
                : "Tasks matching this view will appear here."
            }
          />
        ) : (
          <div className="divide-y divide-slate-100">
            {visible.map((task) => (
              <div
                key={task.id}
                className="flex flex-col gap-3 py-4 first:pt-0 sm:flex-row sm:items-center"
              >
                <div
                  className={`flex size-9 shrink-0 items-center justify-center rounded-lg ${isOverdue(task.due_at, task.status) ? "bg-amber-50 text-amber-700" : "bg-slate-100 text-slate-500"}`}
                >
                  <Clock3 className="size-4" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="font-semibold text-slate-900">{task.title}</p>
                    <Badge className={taskTone[task.status]}>
                      {task.status}
                    </Badge>
                    <span
                      className={`text-xs font-bold uppercase ${priorityTone[task.priority]}`}
                    >
                      {task.priority}
                    </span>
                  </div>
                  {!leadId && names[task.lead_id] && (
                    <Link
                      href={`/leads/${task.lead_id}`}
                      className="mt-1 inline-block text-xs font-medium text-blue-700 hover:underline"
                    >
                      {names[task.lead_id].name} · {names[task.lead_id].company}
                    </Link>
                  )}
                  <p
                    className={`mt-1 text-xs ${isOverdue(task.due_at, task.status) ? "font-semibold text-amber-700" : "text-slate-500"}`}
                  >
                    {isOverdue(task.due_at, task.status)
                      ? "Overdue · "
                      : "Due · "}
                    {formatDate(task.due_at)}
                  </p>
                </div>
                <div className="flex gap-1">
                  {task.status === "pending" && (
                    <>
                      <Button
                        aria-label="Complete task"
                        title="Complete"
                        variant="ghost"
                        size="icon"
                        onClick={() => mutate(() => api.completeTask(task.id))}
                      >
                        <Check className="size-4" />
                      </Button>
                      <Button
                        aria-label="Cancel task"
                        title="Cancel"
                        variant="ghost"
                        size="icon"
                        onClick={() => mutate(() => api.cancelTask(task.id))}
                      >
                        <CircleX className="size-4" />
                      </Button>
                      <Button
                        aria-label="Edit task"
                        title="Edit"
                        variant="ghost"
                        size="icon"
                        onClick={() => setEditing(task)}
                      >
                        <Pencil className="size-4" />
                      </Button>
                    </>
                  )}
                  <Button
                    aria-label="Delete task"
                    title="Delete"
                    variant="ghost"
                    size="icon"
                    className="text-rose-600"
                    onClick={() => {
                      if (confirm("Delete this task?"))
                        void mutate(() => api.deleteTask(task.id));
                    }}
                  >
                    <Trash2 className="size-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
        {compact && visible && visible.length > 4 && (
          <p className="mt-3 text-xs text-slate-500">
            Showing all {visible.length} matching tasks.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
function TaskForm({
  leadId,
  task,
  defaultDue,
  onDone,
  onCancel,
}: {
  leadId: number;
  task?: SalesTask;
  defaultDue: string;
  onDone: () => void;
  onCancel: () => void;
}) {
  const local = (iso?: string) => {
    const d = new Date(iso ?? "");
    const z = new Date(d.getTime() - d.getTimezoneOffset() * 60000);
    return z.toISOString().slice(0, 16);
  };
  const [title, setTitle] = useState(task?.title ?? "");
  const [description, setDescription] = useState(task?.description ?? "");
  const [due, setDue] = useState(local(task?.due_at ?? defaultDue));
  const [priority, setPriority] = useState<TaskInput["priority"]>(
    task?.priority ?? "medium",
  );
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const dueValue = String(
      new FormData(e.currentTarget as HTMLFormElement).get("due_at") ?? "",
    );
    if (!title.trim()) {
      setError("Task title is required.");
      return;
    }
    if (!dueValue || Number.isNaN(new Date(dueValue).getTime())) {
      setError("Choose a valid due date and time.");
      return;
    }
    setSaving(true);
    try {
      const payload = {
        title,
        description: description || null,
        due_at: new Date(dueValue).toISOString(),
        priority,
      };
      if (task) await api.updateTask(task.id, payload);
      else await api.createTask(leadId, payload);
      onDone();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to save task");
    } finally {
      setSaving(false);
    }
  };
  return (
    <form
      onSubmit={submit}
      className="mb-5 rounded-xl border border-blue-100 bg-blue-50/40 p-4"
    >
      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <Label htmlFor="task-title">Task title</Label>
          <Input
            id="task-title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Follow up with decision maker"
          />
        </div>
        <div>
          <Label htmlFor="task-due">Due date and time</Label>
          <Input
            id="task-due"
            name="due_at"
            type="datetime-local"
            value={due}
            onChange={(e) => setDue(e.target.value)}
          />
        </div>
        <div>
          <Label htmlFor="task-priority">Priority</Label>
          <Select
            id="task-priority"
            className="w-full"
            value={priority}
            onChange={(e) =>
              setPriority(e.target.value as TaskInput["priority"])
            }
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </Select>
        </div>
        <div>
          <Label htmlFor="task-description">Description</Label>
          <Textarea
            id="task-description"
            className="min-h-10"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>
      </div>
      {error && <p className="mt-2 text-xs text-rose-700">{error}</p>}
      <div className="mt-3 flex gap-2">
        <Button size="sm" disabled={saving}>
          {saving ? "Saving…" : task ? "Save changes" : "Create task"}
        </Button>
        <Button type="button" size="sm" variant="ghost" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </form>
  );
}
