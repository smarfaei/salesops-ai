"use client";
import { useCallback, useState } from "react";
import {
  BrainCircuit,
  CalendarDays,
  FileText,
  Mail,
  MessageSquare,
  Phone,
  Plus,
  RefreshCw,
  Users,
} from "lucide-react";
import { api } from "@/lib/api";
import { activityLabels, formatDate } from "@/lib/utils";
import type { ActivityType } from "@/types";
import { useApi } from "@/hooks/use-api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Select, Textarea } from "@/components/ui/form-controls";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/state";
import { useAuth } from "@/components/auth-provider";
const icons: Record<
  ActivityType,
  React.ComponentType<{ className?: string }>
> = {
  lead_created: Plus,
  lead_updated: RefreshCw,
  stage_changed: RefreshCw,
  call: Phone,
  email: Mail,
  meeting: Users,
  note: FileText,
};
export function ActivityTimeline({
  leadId,
  refreshKey = 0,
}: {
  leadId: number;
  refreshKey?: number;
}) {
  const { can } = useAuth();
  const loader = useCallback(() => {
    void refreshKey;
    return api.activities(leadId);
  }, [leadId, refreshKey]);
  const { data, loading, error, reload } = useApi(loader);
  const [open, setOpen] = useState(false);
  const [type, setType] = useState<"note" | "call" | "email" | "meeting">(
    "note",
  );
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const add = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!description.trim()) {
      setFormError("Add a short activity description.");
      return;
    }
    setSaving(true);
    try {
      await api.addActivity(leadId, { type, description });
      setDescription("");
      setOpen(false);
      await reload();
    } catch (e) {
      setFormError(e instanceof Error ? e.message : "Unable to add activity");
    } finally {
      setSaving(false);
    }
  };
  return (
    <Card>
      <CardHeader>
        <div>
          <h2 className="font-bold">Activity timeline</h2>
          <p className="mt-1 text-xs text-slate-500">
            Customer touchpoints and automatic system events
          </p>
        </div>
        {can("activity:write") && (
          <Button
            size="sm"
            variant="outline"
            onClick={() => setOpen((x) => !x)}
          >
            <MessageSquare className="size-4" />
            Add activity
          </Button>
        )}
      </CardHeader>
      <CardContent>
        {open && (
          <form
            onSubmit={add}
            className="mb-5 rounded-xl border border-slate-200 bg-slate-50 p-4"
          >
            <div className="grid gap-3 sm:grid-cols-[160px_1fr]">
              <Select
                value={type}
                onChange={(e) => setType(e.target.value as typeof type)}
              >
                <option value="note">Note</option>
                <option value="call">Call</option>
                <option value="email">Email</option>
                <option value="meeting">Meeting</option>
              </Select>
              <Textarea
                className="min-h-20"
                placeholder="What happened and what matters next?"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>
            {formError && (
              <p className="mt-2 text-xs text-rose-700">{formError}</p>
            )}
            <div className="mt-3 flex gap-2">
              <Button size="sm" disabled={saving}>
                {saving ? "Saving…" : "Save activity"}
              </Button>
              <Button
                size="sm"
                variant="ghost"
                type="button"
                onClick={() => setOpen(false)}
              >
                Cancel
              </Button>
            </div>
          </form>
        )}
        {loading ? (
          <LoadingState />
        ) : error ? (
          <ErrorState message={error} onRetry={reload} />
        ) : !data?.length ? (
          <EmptyState
            title="No activity yet"
            description="The timeline will capture lead and sales events."
          />
        ) : (
          <div className="space-y-0">
            {data.map((item, index) => {
              const intelligenceEvent =
                item.metadata?.event === "sales_intelligence_generated";
              const Icon = intelligenceEvent
                ? BrainCircuit
                : (icons[item.type] ?? CalendarDays);
              return (
                <div key={item.id} className="relative flex gap-3 pb-5">
                  <div className="relative z-10 flex size-8 shrink-0 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-500">
                    <Icon className="size-4" />
                  </div>
                  {index < data.length - 1 && (
                    <div className="absolute left-4 top-8 h-full w-px bg-slate-200" />
                  )}
                  <div className="pt-0.5">
                    <p className="text-xs font-bold uppercase tracking-wide text-slate-500">
                      {intelligenceEvent
                        ? "Sales intelligence generated"
                        : activityLabels[item.type]}
                    </p>
                    <p className="mt-1 text-sm text-slate-700">
                      {item.description}
                    </p>
                    <p className="mt-1 text-xs text-slate-400">
                      {formatDate(item.created_at)}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
