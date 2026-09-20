import Link from "next/link";
import { Plus } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { LeadTable } from "@/features/leads/lead-table";
import { DEMO_MODE } from "@/lib/config";
export default function LeadsPage() {
  return (
    <>
      <PageHeader
        title="Leads"
        description="Search, qualify, and move real opportunities forward."
        action={
          !DEMO_MODE && (
            <Link href="/leads/new">
              <Button>
                <Plus className="size-4" />
                New lead
              </Button>
            </Link>
          )
        }
      />
      <LeadTable />
    </>
  );
}
