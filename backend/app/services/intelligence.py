import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import Request
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.factory import create_ai_provider
from app.ai.providers.base import AIProvider, AIProviderError
from app.ai.providers.local import LocalAIProvider
from app.core.demo import get_request_settings
from app.core.enums import ActivityType, TaskStatus
from app.models.activity import Activity
from app.models.intelligence import LeadIntelligence
from app.models.lead import Lead
from app.models.task import SalesTask
from app.schemas.intelligence import (
    ActivityContext,
    FollowUpMessage,
    IntelligenceContext,
    LeadIntelligenceResponse,
    NextBestAction,
    SalesIntelligence,
    TaskContext,
)
from app.services.activity import create_activity

logger = logging.getLogger(__name__)


class IntelligenceUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class GenerationOutcome:
    content: SalesIntelligence
    provider: str
    model: str | None
    provider_metadata: dict | None


class SalesIntelligenceService:
    def __init__(
        self,
        provider: AIProvider,
        *,
        fallback_provider: AIProvider | None = None,
    ) -> None:
        self.provider = provider
        self.fallback_provider = fallback_provider

    def generate_for_lead(self, db: Session, lead: Lead) -> LeadIntelligence:
        context = self._build_context(db, lead)
        outcome = self._generate(context)
        record = db.scalar(select(LeadIntelligence).where(LeadIntelligence.lead_id == lead.id))
        is_first_generation = record is None
        if record is None:
            record = LeadIntelligence(lead_id=lead.id)
            db.add(record)

        record.qualification_summary = outcome.content.qualification_summary
        record.buying_signals = [item.model_dump() for item in outcome.content.buying_signals]
        record.risks = [item.model_dump() for item in outcome.content.risks]
        record.recommended_action = outcome.content.next_best_action.action
        record.recommended_action_reason = outcome.content.next_best_action.reason
        record.recommended_action_priority = outcome.content.next_best_action.priority.value
        record.follow_up_subject = outcome.content.follow_up.subject
        record.follow_up_message = outcome.content.follow_up.message
        record.provider = outcome.provider
        record.model = outcome.model
        record.provider_metadata = outcome.provider_metadata
        record.generated_at = context.generated_at
        db.flush()

        if is_first_generation:
            create_activity(
                db,
                lead_id=lead.id,
                activity_type=ActivityType.NOTE,
                description="Sales intelligence generated",
                metadata={"event": "sales_intelligence_generated", "provider": outcome.provider},
            )
        return record

    def _generate(self, context: IntelligenceContext) -> GenerationOutcome:
        try:
            content = self.provider.generate(context)
            return GenerationOutcome(content, self.provider.name, self.provider.model, None)
        except (AIProviderError, ValidationError, ValueError) as exc:
            logger.warning("AI provider %s failed: %s", self.provider.name, type(exc).__name__)
            if self.fallback_provider is None or self.fallback_provider.name == self.provider.name:
                raise IntelligenceUnavailable("Sales intelligence provider is unavailable") from exc
            try:
                content = self.fallback_provider.generate(context)
            except (AIProviderError, ValidationError, ValueError) as fallback_exc:
                logger.warning(
                    "Fallback AI provider %s failed: %s",
                    self.fallback_provider.name,
                    type(fallback_exc).__name__,
                )
                raise IntelligenceUnavailable("Sales intelligence provider is unavailable") from fallback_exc
            return GenerationOutcome(
                content,
                self.fallback_provider.name,
                self.fallback_provider.model,
                {"fallback_from": self.provider.name, "reason": type(exc).__name__},
            )

    @staticmethod
    def _build_context(db: Session, lead: Lead) -> IntelligenceContext:
        activities = list(
            db.scalars(
                select(Activity)
                .where(Activity.lead_id == lead.id)
                .order_by(Activity.created_at.desc(), Activity.id.desc())
                .limit(10)
            ).all()
        )
        tasks = list(
            db.scalars(
                select(SalesTask)
                .where(SalesTask.lead_id == lead.id, SalesTask.status == TaskStatus.PENDING)
                .order_by(SalesTask.due_at.asc(), SalesTask.id.asc())
            ).all()
        )
        generated_at = datetime.now(timezone.utc)
        return IntelligenceContext(
            lead_id=lead.id,
            name=lead.name,
            company=lead.company,
            employees=lead.employees,
            need=lead.need,
            budget=lead.budget,
            score=lead.score,
            qualification_status=lead.status,
            pipeline_stage=lead.pipeline_stage,
            recent_activities=[ActivityContext.model_validate(item, from_attributes=True) for item in activities],
            open_tasks=[TaskContext.model_validate(item, from_attributes=True) for item in tasks],
            generated_at=generated_at,
        )


def intelligence_to_response(record: LeadIntelligence) -> LeadIntelligenceResponse:
    return LeadIntelligenceResponse(
        id=record.id,
        lead_id=record.lead_id,
        qualification_summary=record.qualification_summary,
        buying_signals=record.buying_signals,
        risks=record.risks,
        next_best_action=NextBestAction(
            action=record.recommended_action,
            reason=record.recommended_action_reason,
            priority=record.recommended_action_priority,
        ),
        follow_up=FollowUpMessage(
            subject=record.follow_up_subject,
            message=record.follow_up_message,
        ),
        generated_at=record.generated_at,
        provider=record.provider,
        model=record.model,
        provider_metadata=record.provider_metadata,
    )


def get_sales_intelligence_service(request: Request) -> SalesIntelligenceService:
    settings = get_request_settings(request)
    provider = create_ai_provider(settings)
    fallback = LocalAIProvider() if settings.ai_allow_fallback and provider.name != "local" else None
    return SalesIntelligenceService(provider, fallback_provider=fallback)
