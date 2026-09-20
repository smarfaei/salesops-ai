from datetime import datetime, timezone

from app.ai.providers.base import AIProvider
from app.core.enums import PipelineStage, TaskPriority, TaskStatus
from app.schemas.intelligence import (
    EvidenceSignal,
    FollowUpMessage,
    IntelligenceContext,
    NextBestAction,
    SalesIntelligence,
)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class LocalAIProvider(AIProvider):
    name = "local"
    model = "deterministic-rules-v1"

    def generate(self, context: IntelligenceContext) -> SalesIntelligence:
        buying_signals = self._buying_signals(context)
        risks = self._risks(context)
        action = self._next_best_action(context)
        return SalesIntelligence(
            qualification_summary=self._summary(context),
            buying_signals=buying_signals,
            risks=risks,
            next_best_action=action,
            follow_up=self._follow_up(context, action),
        )

    @staticmethod
    def _summary(context: IntelligenceContext) -> str:
        return (
            f"{context.qualification_status} B2B lead for {context.company} with a score of "
            f"{context.score}/100, a ${context.budget:,} stated budget, and a "
            f"{context.pipeline_stage.value} pipeline position. The stated requirement is "
            f"{context.need.rstrip('.')} ."
        ).replace("  ", " ").replace(" .", ".")

    @staticmethod
    def _buying_signals(context: IntelligenceContext) -> list[EvidenceSignal]:
        signals: list[EvidenceSignal] = []
        if context.budget >= 5000:
            signals.append(EvidenceSignal(signal="High budget", evidence=f"Stated budget is ${context.budget:,}."))
        elif context.budget >= 2000:
            signals.append(EvidenceSignal(signal="Qualified budget", evidence=f"Stated budget is ${context.budget:,}."))
        if context.employees >= 100:
            signals.append(EvidenceSignal(signal="Large company", evidence=f"Company size is {context.employees} employees."))
        elif context.employees >= 20:
            signals.append(EvidenceSignal(signal="Established company", evidence=f"Company size is {context.employees} employees."))
        if "AI" in context.need.upper() or "AUTOMAT" in context.need.upper():
            signals.append(EvidenceSignal(signal="AI or automation requirement", evidence=context.need))
        if context.score >= 70:
            signals.append(EvidenceSignal(signal="High lead score", evidence=f"Qualification score is {context.score}/100."))
        if context.pipeline_stage in {PipelineStage.CONTACTED, PipelineStage.PROPOSAL, PipelineStage.WON}:
            signals.append(EvidenceSignal(signal="Advanced pipeline position", evidence=f"Current stage is {context.pipeline_stage.value}."))
        return signals

    @staticmethod
    def _risks(context: IntelligenceContext) -> list[EvidenceSignal]:
        risks: list[EvidenceSignal] = []
        if context.budget < 1000:
            risks.append(EvidenceSignal(signal="Low budget", evidence=f"Stated budget is ${context.budget:,}."))
        if context.employees < 5:
            risks.append(EvidenceSignal(signal="Very small company", evidence=f"Company size is {context.employees} employees."))
        if context.score < 40:
            risks.append(EvidenceSignal(signal="Low qualification score", evidence=f"Lead score is {context.score}/100."))
        if len(context.need.split()) < 4:
            risks.append(EvidenceSignal(signal="Requirement needs clarification", evidence=f"Current requirement is brief: {context.need}"))
        now = _as_utc(context.generated_at)
        overdue = [
            task for task in context.open_tasks
            if task.status == TaskStatus.PENDING.value and _as_utc(task.due_at) < now
        ]
        if overdue:
            risks.append(EvidenceSignal(signal="Overdue follow-up", evidence=f"{len(overdue)} pending task(s) are overdue."))
        manual_types = {"call", "email", "meeting", "note"}
        if not any(activity.type in manual_types for activity in context.recent_activities):
            risks.append(EvidenceSignal(signal="No recent sales activity", evidence="No recent call, email, meeting, or note is recorded."))
        return risks

    @staticmethod
    def _next_best_action(context: IntelligenceContext) -> NextBestAction:
        now = _as_utc(context.generated_at)
        overdue = [
            task for task in context.open_tasks
            if task.status == TaskStatus.PENDING.value and _as_utc(task.due_at) < now
        ]
        if overdue:
            return NextBestAction(
                action="Resolve overdue task",
                reason=f"{len(overdue)} pending follow-up task(s) are overdue and require attention.",
                priority=TaskPriority.HIGH,
            )
        if context.pipeline_stage == PipelineStage.PROPOSAL:
            return NextBestAction(action="Follow up on proposal", reason="The lead is in Proposal and has no overdue task blocking the follow-up.", priority=TaskPriority.HIGH)
        if context.pipeline_stage == PipelineStage.QUALIFIED:
            return NextBestAction(action="Schedule discovery call", reason=f"The lead is Qualified with a score of {context.score}/100.", priority=TaskPriority.HIGH if context.score >= 70 else TaskPriority.MEDIUM)
        if context.pipeline_stage == PipelineStage.CONTACTED:
            return NextBestAction(action="Send follow-up", reason="The lead has been contacted and the next response should be progressed.", priority=TaskPriority.MEDIUM)
        if context.pipeline_stage == PipelineStage.WON:
            return NextBestAction(action="Coordinate customer handoff", reason="The opportunity is Won and should move into delivery handoff.", priority=TaskPriority.MEDIUM)
        if context.pipeline_stage == PipelineStage.LOST:
            return NextBestAction(action="Nurture lead", reason="The opportunity is Lost; retain context for a future re-engagement.", priority=TaskPriority.LOW)
        if context.score >= 70:
            return NextBestAction(action="Contact immediately", reason=f"The lead is New with a high score of {context.score}/100.", priority=TaskPriority.HIGH)
        if context.score < 40:
            return NextBestAction(action="Nurture lead", reason=f"The lead score is {context.score}/100 and does not justify immediate sales effort.", priority=TaskPriority.LOW)
        return NextBestAction(action="Schedule discovery call", reason=f"A score of {context.score}/100 warrants further qualification.", priority=TaskPriority.MEDIUM)

    @staticmethod
    def _follow_up(context: IntelligenceContext, action: NextBestAction) -> FollowUpMessage:
        first_name = context.name.split()[0]
        subject = f"Next steps for {context.company}"
        message = (
            f"Hi {first_name},\n\n"
            f"Thank you for sharing your interest in {context.need.rstrip('.')}. "
            f"Based on our current conversation, the next useful step is to {action.action.lower()}. "
            "Please let me know a convenient time to continue.\n\n"
            "Best regards"
        )
        return FollowUpMessage(subject=subject, message=message)
