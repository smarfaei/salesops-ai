import Link from "next/link";
import type { Lead } from "@/types";

export function LeadSummary({ lead }: { lead: Lead }) {
  return (
    <div>
      <Link href={`/leads/${lead.id}`}>{lead.name}</Link>
      <p className="mt-1 max-w-48 truncate text-xs text-slate-500">
        {lead.need}
      </p>
    </div>
  );
}
