"use client";
import Link from "next/link";
import {
  ArrowDownUp,
  ChevronLeft,
  ChevronRight,
  Plus,
  Search,
} from "lucide-react";
import { useCallback, useState } from "react";
import { api } from "@/lib/api";
import { formatCurrency, formatDate, stages } from "@/lib/utils";
import { useApi } from "@/hooks/use-api";
import { StatusBadge, StageBadge } from "@/components/lead-badges";
import { Button } from "@/components/ui/button";
import { Input, Select } from "@/components/ui/form-controls";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/state";
import { LeadSummary } from "./lead-summary";
import { DEMO_MODE } from "@/lib/config";
import { useAuth } from "@/components/auth-provider";
export function LeadTable() {
  const { can } = useAuth();
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [stage, setStage] = useState("");
  const [minScore, setMinScore] = useState("");
  const [page, setPage] = useState(1);
  const [sort, setSort] = useState("updated_at");
  const [order, setOrder] = useState("desc");
  const loader = useCallback(
    () =>
      api.leads({
        page,
        page_size: 10,
        search: search || undefined,
        status: status || undefined,
        pipeline_stage: stage || undefined,
        min_score: minScore || undefined,
        sort_by: sort,
        sort_order: order,
      }),
    [page, search, status, stage, minScore, sort, order],
  );
  const { data, loading, error, reload } = useApi(loader);
  const toggleSort = (field: string) => {
    if (sort === field) setOrder(order === "asc" ? "desc" : "asc");
    else {
      setSort(field);
      setOrder("asc");
    }
    setPage(1);
  };
  return (
    <div className="space-y-4">
      <div className="grid gap-3 rounded-xl border border-slate-200 bg-white p-4 sm:grid-cols-2 xl:grid-cols-5">
        <div className="relative sm:col-span-2">
          <Search className="absolute left-3 top-3 size-4 text-slate-400" />
          <Input
            className="pl-9"
            placeholder="Search name, company, or need…"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
          />
        </div>
        <Select
          value={status}
          onChange={(e) => {
            setStatus(e.target.value);
            setPage(1);
          }}
        >
          <option value="">All temperatures</option>
          <option>Hot</option>
          <option>Warm</option>
          <option>Cold</option>
        </Select>
        <Select
          value={stage}
          onChange={(e) => {
            setStage(e.target.value);
            setPage(1);
          }}
        >
          <option value="">All stages</option>
          {stages.map((x) => (
            <option key={x}>{x}</option>
          ))}
        </Select>
        <Select
          value={minScore}
          onChange={(e) => {
            setMinScore(e.target.value);
            setPage(1);
          }}
        >
          <option value="">Any score</option>
          <option value="70">70+ Hot</option>
          <option value="40">40+ Qualified</option>
        </Select>
      </div>
      {loading ? (
        <LoadingState label="Loading leads" />
      ) : error ? (
        <ErrorState message={error} onRetry={reload} />
      ) : !data?.items.length ? (
        <EmptyState
          title="No leads found"
          description="Adjust the filters or create a lead to begin qualification."
          action={
            !DEMO_MODE &&
            can("lead:create") && (
              <Link href="/leads/new">
                <Button>
                  <Plus className="size-4" />
                  New lead
                </Button>
              </Link>
            )
          }
        />
      ) : (
        <>
          <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[1050px] text-left text-sm">
                <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                  <tr>
                    <Th onClick={() => toggleSort("name")}>Lead</Th>
                    <Th onClick={() => toggleSort("company")}>Company</Th>
                    <Th onClick={() => toggleSort("budget")}>Budget</Th>
                    <Th onClick={() => toggleSort("company_size")}>
                      Company size
                    </Th>
                    <Th onClick={() => toggleSort("score")}>Score</Th>
                    <Th>Temperature</Th>
                    <Th>Pipeline</Th>
                    <Th>Owner</Th>
                    <Th onClick={() => toggleSort("updated_at")}>Updated</Th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {data.items.map((lead) => (
                    <tr key={lead.id} className="hover:bg-slate-50">
                      <td className="p-4">
                        <LeadSummary lead={lead} />
                      </td>
                      <td className="p-4 text-slate-700">{lead.company}</td>
                      <td className="p-4 font-medium">
                        {formatCurrency(lead.budget)}
                      </td>
                      <td className="p-4 text-slate-600">
                        {lead.employees.toLocaleString()} employees
                      </td>
                      <td className="p-4">
                        <span className="font-bold text-slate-900">
                          {lead.score}
                        </span>
                        <span className="text-slate-400">/100</span>
                      </td>
                      <td className="p-4">
                        <StatusBadge status={lead.status} />
                      </td>
                      <td className="p-4">
                        <StageBadge stage={lead.pipeline_stage} />
                      </td>
                      <td className="p-4 text-xs text-slate-600">
                        {lead.owner?.full_name ?? "Unassigned"}
                      </td>
                      <td className="p-4 text-xs text-slate-500">
                        {formatDate(lead.updated_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-500">
              {data.total} leads · Page {data.page} of {Math.max(data.pages, 1)}
            </p>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="icon"
                aria-label="Previous page"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
              >
                <ChevronLeft className="size-4" />
              </Button>
              <Button
                variant="outline"
                size="icon"
                aria-label="Next page"
                disabled={page >= data.pages}
                onClick={() => setPage((p) => p + 1)}
              >
                <ChevronRight className="size-4" />
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
function Th({
  children,
  onClick,
}: {
  children: React.ReactNode;
  onClick?: () => void;
}) {
  return (
    <th className="p-4 font-semibold">
      <button
        className="flex items-center gap-1"
        onClick={onClick}
        disabled={!onClick}
      >
        {children}
        {onClick && <ArrowDownUp className="size-3" />}
      </button>
    </th>
  );
}
