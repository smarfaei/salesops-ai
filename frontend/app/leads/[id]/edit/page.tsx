"use client";
import { useCallback } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { useApi } from "@/hooks/use-api";
import { PageHeader } from "@/components/page-header";
import { ErrorState, LoadingState } from "@/components/ui/state";
import { LeadForm } from "@/features/leads/lead-form";
export default function EditLeadPage() {
  const params = useParams<{ id: string }>();
  const id = Number(params.id);
  const loader = useCallback(() => api.lead(id), [id]);
  const { data, loading, error, reload } = useApi(loader);
  if (loading) return <LoadingState label="Loading lead" />;
  if (error || !data)
    return <ErrorState message={error ?? "Lead not found"} onRetry={reload} />;
  return (
    <>
      <PageHeader
        title={`Edit ${data.name}`}
        description="Changes recalculate the explainable lead score."
      />
      <LeadForm lead={data} />
    </>
  );
}
