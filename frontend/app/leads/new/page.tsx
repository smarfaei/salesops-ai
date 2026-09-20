import { PageHeader } from "@/components/page-header";
import { LeadForm } from "@/features/leads/lead-form";
export default function NewLeadPage() {
  return (
    <>
      <PageHeader
        title="Create lead"
        description="The score and qualification are calculated automatically after save."
      />
      <LeadForm />
    </>
  );
}
