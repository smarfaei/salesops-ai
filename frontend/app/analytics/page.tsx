import { PageHeader } from "@/components/page-header";
import { DashboardView } from "@/features/dashboard/dashboard-view";
export default function AnalyticsPage() {
  return (
    <>
      <PageHeader
        title="Analytics"
        description="Portfolio and workload distribution from real backend data."
      />
      <DashboardView analytics />
    </>
  );
}
