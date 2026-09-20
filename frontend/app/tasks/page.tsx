import { PageHeader } from "@/components/page-header";
import { TaskCenter } from "@/features/tasks/task-center";
export default function TasksPage() {
  return (
    <>
      <PageHeader
        title="Task Center"
        description="Prioritize the sales follow-ups that need attention."
      />
      <TaskCenter />
    </>
  );
}
