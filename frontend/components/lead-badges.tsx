import { Badge } from "@/components/ui/badge";
import { stageTone, statusTone } from "@/lib/utils";
import type { LeadStatus, PipelineStage } from "@/types";
export const StatusBadge = ({ status }: { status: LeadStatus }) => (
  <Badge className={statusTone[status]}>{status}</Badge>
);
export const StageBadge = ({ stage }: { stage: PipelineStage }) => (
  <Badge className={stageTone[stage]}>{stage}</Badge>
);
