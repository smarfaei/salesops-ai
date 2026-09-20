"use client";
import Link from "next/link";
import { Building2 } from "lucide-react";
import { useCallback, useState } from "react";
import { api } from "@/lib/api";
import { formatCurrency, stages } from "@/lib/utils";
import type { PipelineStage } from "@/types";
import { useApi } from "@/hooks/use-api";
import { StatusBadge } from "@/components/lead-badges";
import { Select } from "@/components/ui/form-controls";
import { ErrorState, LoadingState } from "@/components/ui/state";
import { useAuth } from "@/components/auth-provider";
const stageAccent: Record<PipelineStage, string> = {
  New: "border-t-slate-400",
  Qualified: "border-t-blue-500",
  Contacted: "border-t-cyan-500",
  Proposal: "border-t-violet-500",
  Won: "border-t-emerald-500",
  Lost: "border-t-stone-400",
};
export function PipelineBoard() {
  const { can } = useAuth();
  const loader = useCallback(
    () => api.leads({ page_size: 100, sort_by: "score", sort_order: "desc" }),
    [],
  );
  const { data, loading, error, reload } = useApi(loader);
  const [moving, setMoving] = useState<number | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const move = async (id: number, stage: PipelineStage) => {
    setMoving(id);
    setActionError(null);
    try {
      await api.updateStage(id, stage);
      await reload();
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Unable to move lead");
    } finally {
      setMoving(null);
    }
  };
  if (loading) return <LoadingState label="Loading pipeline" />;
  if (error || !data)
    return (
      <ErrorState
        message={error ?? "Pipeline is unavailable"}
        onRetry={reload}
      />
    );
  return (
    <div>
      {actionError && (
        <p
          role="alert"
          className="mb-4 rounded-lg bg-rose-50 p-3 text-sm text-rose-700"
        >
          {actionError}
        </p>
      )}
      <div className="overflow-x-auto pb-4">
        <div className="grid min-w-[1380px] grid-cols-6 gap-4">
          {stages.map((stage) => {
            const leads = data.items.filter((x) => x.pipeline_stage === stage);
            return (
              <section
                key={stage}
                className={`rounded-xl border-t-2 bg-slate-100/80 p-3 ${stageAccent[stage]}`}
              >
                <div className="mb-3 flex items-center justify-between">
                  <h2 className="text-sm font-bold text-slate-800">{stage}</h2>
                  <span className="rounded-full bg-white px-2 py-0.5 text-xs font-semibold text-slate-500">
                    {leads.length}
                  </span>
                </div>
                <div className="space-y-3">
                  {leads.map((lead) => (
                    <article
                      key={lead.id}
                      className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm transition-shadow hover:shadow-md"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <Link
                          href={`/leads/${lead.id}`}
                          className="font-bold text-slate-900 hover:text-blue-700"
                        >
                          {lead.name}
                        </Link>
                        <StatusBadge status={lead.status} />
                      </div>
                      <p className="mt-1 flex items-center gap-1 text-xs text-slate-500">
                        <Building2 className="size-3" />
                        {lead.company}
                      </p>
                      <div className="mt-4 flex items-end justify-between">
                        <div>
                          <p className="text-xs text-slate-400">Score</p>
                          <p className="font-bold">
                            {lead.score}
                            <span className="text-xs text-slate-400">/100</span>
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-xs text-slate-400">Budget</p>
                          <p className="text-sm font-semibold">
                            {formatCurrency(lead.budget)}
                          </p>
                        </div>
                      </div>
                      <Select
                        aria-label={`Move ${lead.name}`}
                        className="mt-4 w-full text-xs"
                        value={lead.pipeline_stage}
                        disabled={moving === lead.id || !can("pipeline:write")}
                        onChange={(e) =>
                          void move(lead.id, e.target.value as PipelineStage)
                        }
                      >
                        {stages.map((x) => (
                          <option key={x}>{x}</option>
                        ))}
                      </Select>
                    </article>
                  ))}
                  {!leads.length && (
                    <div className="rounded-xl border border-dashed border-slate-300 p-5 text-center text-xs text-slate-400">
                      No leads in this stage
                    </div>
                  )}
                </div>
              </section>
            );
          })}
        </div>
      </div>
    </div>
  );
}
