"use client";

import { useCallback } from "react";
import { useAuth } from "@/components/auth-provider";
import { PageHeader } from "@/components/page-header";
import { ErrorState, LoadingState } from "@/components/ui/state";
import { useApi } from "@/hooks/use-api";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";

export default function AuditPage() {
  const { can } = useAuth();
  if (!can("audit:read"))
    return <ErrorState message="Audit access is restricted." />;
  return <AuthorizedAuditPage />;
}

function AuthorizedAuditPage() {
  const loader = useCallback(() => api.auditLogs(), []);
  const { data, loading, error, reload } = useApi(loader);
  return (
    <>
      <PageHeader
        title="Audit Logs"
        description="A safe, append-only view of meaningful sales and access events."
      />
      {loading ? (
        <LoadingState label="Loading audit history" />
      ) : error ? (
        <ErrorState message={error} onRetry={reload} />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
          <table className="w-full min-w-[800px] text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                <th className="p-4">Event</th>
                <th className="p-4">Actor</th>
                <th className="p-4">Entity</th>
                <th className="p-4">Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data?.items.map((entry) => (
                <tr key={entry.id}>
                  <td className="p-4 font-semibold text-slate-800">
                    {entry.event_type.replaceAll("_", " ")}
                  </td>
                  <td className="p-4 text-slate-600">
                    {entry.actor?.full_name ?? "System"}
                  </td>
                  <td className="p-4 text-slate-600">
                    {entry.entity_type}
                    {entry.entity_id ? ` #${entry.entity_id}` : ""}
                  </td>
                  <td className="p-4 text-xs text-slate-500">
                    {formatDate(entry.created_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
