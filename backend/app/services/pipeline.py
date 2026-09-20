from sqlalchemy.orm import Session

from app.core.enums import ActivityType, PipelineStage
from app.models.lead import Lead
from app.services.activity import create_activity


def transition_stage(db: Session, lead: Lead, target: PipelineStage) -> bool:
    previous = lead.pipeline_stage
    if previous == target:
        return False
    lead.pipeline_stage = target
    create_activity(
        db,
        lead_id=lead.id,
        activity_type=ActivityType.STAGE_CHANGED,
        description=f"Pipeline stage changed from {previous.value} to {target.value}",
        metadata={"from": previous.value, "to": target.value},
    )
    return True
