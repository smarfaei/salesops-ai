import { PageHeader } from "@/components/page-header";
import { PipelineBoard } from "@/features/pipeline/pipeline-board";
export default function PipelinePage() {
  return (
    <>
      <PageHeader
        title="Sales Pipeline"
        description="Move opportunities reliably; every stage change is recorded in the timeline."
      />
      <PipelineBoard />
    </>
  );
}
