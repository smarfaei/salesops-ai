"use client";
import Link from "next/link";
import { Building2, Calendar, Edit3, Users } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { formatCurrency, formatDate, stages } from "@/lib/utils";
import type { PipelineStage, User } from "@/types";
import { useApi } from "@/hooks/use-api";
import { StatusBadge, StageBadge } from "@/components/lead-badges";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Select } from "@/components/ui/form-controls";
import { ErrorState, LoadingState } from "@/components/ui/state";
import { IntelligencePanel } from "@/features/intelligence/intelligence-panel";
import { ActivityTimeline } from "@/features/activities/activity-timeline";
import { TaskCenter } from "@/features/tasks/task-center";
import { DEMO_MODE } from "@/lib/config";
import { useAuth } from "@/components/auth-provider";
export function LeadDetail({ leadId }: { leadId: number }) {
  const { can } = useAuth();
  const loader = useCallback(() => api.lead(leadId), [leadId]);
  const { data: lead, loading, error, reload } = useApi(loader);
  const [updating, setUpdating] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [owners, setOwners] = useState<User[]>([]);
  useEffect(() => {
    if (can("lead:assign"))
      void api
        .assignableUsers()
        .then(setOwners)
        .catch(() => setOwners([]));
  }, [can]);
  const changeStage = async (stage: PipelineStage) => {
    if (!lead || stage === lead.pipeline_stage) return;
    setUpdating(true);
    setActionError(null);
    try {
      await api.updateStage(lead.id, stage);
      await reload();
      setRefreshKey((x) => x + 1);
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Unable to update stage");
    } finally {
      setUpdating(false);
    }
  };
  const changeOwner = async (ownerUserId: string) => {
    if (!lead) return;
    setUpdating(true);
    setActionError(null);
    try {
      await api.assignLead(lead.id, ownerUserId ? Number(ownerUserId) : null);
      await reload();
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Unable to assign lead");
    } finally {
      setUpdating(false);
    }
  };
  if (loading) return <LoadingState label="Loading CRM record" />;
  if (error || !lead)
    return <ErrorState message={error ?? "Lead not found"} onRetry={reload} />;
  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 rounded-xl border border-slate-200 bg-white p-5 sm:flex-row sm:items-center">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight">{lead.name}</h1>
            <StatusBadge status={lead.status} />
            <StageBadge stage={lead.pipeline_stage} />
          </div>
          <p className="mt-1 flex items-center gap-2 text-sm text-slate-500">
            <Building2 className="size-4" />
            {lead.company}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Select
            aria-label="Pipeline stage"
            value={lead.pipeline_stage}
            disabled={updating || !can("pipeline:write")}
            onChange={(e) => void changeStage(e.target.value as PipelineStage)}
          >
            {stages.map((x) => (
              <option key={x}>{x}</option>
            ))}
          </Select>
          {!DEMO_MODE && can("lead:edit") && (
            <Link href={`/leads/${lead.id}/edit`}>
              <Button variant="outline">
                <Edit3 className="size-4" />
                Edit lead
              </Button>
            </Link>
          )}
        </div>
      </div>
      {actionError && (
        <p
          role="alert"
          className="rounded-lg bg-rose-50 p-3 text-sm text-rose-700"
        >
          {actionError}
        </p>
      )}
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.6fr)_minmax(340px,0.8fr)]">
        <div className="space-y-6">
          <IntelligencePanel
            leadId={lead.id}
            onGenerated={() => setRefreshKey((x) => x + 1)}
          />
          <ActivityTimeline leadId={lead.id} refreshKey={refreshKey} />
        </div>
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <h2 className="font-bold">Lead information</h2>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="grid grid-cols-2 gap-4">
                <Metric label="Score" value={`${lead.score}/100`} />
                <Metric label="Budget" value={formatCurrency(lead.budget)} />
                <Metric
                  label="Company size"
                  value={`${lead.employees.toLocaleString()} people`}
                />
                <Metric label="Stage" value={lead.pipeline_stage} />
              </div>
              <div>
                <p className="text-xs font-bold uppercase tracking-wide text-slate-500">
                  Owner
                </p>
                {can("lead:assign") ? (
                  <Select
                    className="mt-2 w-full"
                    aria-label="Lead owner"
                    value={lead.owner_user_id ?? ""}
                    disabled={updating}
                    onChange={(event) => void changeOwner(event.target.value)}
                  >
                    <option value="">Unassigned</option>
                    {owners.map((owner) => (
                      <option key={owner.id} value={owner.id}>
                        {owner.full_name}
                      </option>
                    ))}
                  </Select>
                ) : (
                  <p className="mt-2 text-sm font-medium text-slate-800">
                    {lead.owner?.full_name ?? "Unassigned"}
                  </p>
                )}
              </div>
              <div>
                <p className="text-xs font-bold uppercase tracking-wide text-slate-500">
                  Business need
                </p>
                <p className="mt-2 text-sm leading-6 text-slate-700">
                  {lead.need}
                </p>
              </div>
              <div>
                <p className="text-xs font-bold uppercase tracking-wide text-slate-500">
                  Why this score
                </p>
                <ul className="mt-2 space-y-2">
                  {lead.score_reasons.map((x) => (
                    <li key={x} className="flex gap-2 text-sm text-slate-600">
                      <span className="mt-2 size-1.5 shrink-0 rounded-full bg-blue-500" />
                      {x}
                    </li>
                  ))}
                </ul>
              </div>
              <div className="grid gap-2 border-t border-slate-100 pt-4 text-xs text-slate-500">
                <span className="flex items-center gap-2">
                  <Calendar className="size-3.5" />
                  Created {formatDate(lead.created_at)}
                </span>
                <span className="flex items-center gap-2">
                  <Users className="size-3.5" />
                  Updated {formatDate(lead.updated_at)}
                </span>
              </div>
            </CardContent>
          </Card>
          <TaskCenter leadId={lead.id} compact />
        </div>
      </div>
    </div>
  );
}
function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-slate-50 p-3">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="mt-1 font-bold text-slate-900">{value}</p>
    </div>
  );
}
