"use client";
import { useParams } from "next/navigation";
import { LeadDetail } from "@/features/leads/lead-detail";
export default function LeadDetailPage() {
  const params = useParams<{ id: string }>();
  return <LeadDetail leadId={Number(params.id)} />;
}
