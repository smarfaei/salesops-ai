import { PageHeader } from "@/components/page-header";
import { DashboardView } from "@/features/dashboard/dashboard-view";
export default function DashboardPage() {
  return (
    <>
      <PageHeader
        title="Executive Dashboard"
        description="A live view of qualification, pipeline value, and sales follow-through."
      />
      <DashboardView />
    </>
  );
}
