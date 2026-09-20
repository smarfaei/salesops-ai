from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.lead import Lead


class LeadIntelligence(Base):
    __tablename__ = "lead_intelligence"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    qualification_summary: Mapped[str] = mapped_column(Text, nullable=False)
    buying_signals: Mapped[list[dict[str, str]]] = mapped_column(JSON, nullable=False)
    risks: Mapped[list[dict[str, str]]] = mapped_column(JSON, nullable=False)
    recommended_action: Mapped[str] = mapped_column(String(200), nullable=False)
    recommended_action_reason: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_action_priority: Mapped[str] = mapped_column(String(20), nullable=False)
    follow_up_subject: Mapped[str] = mapped_column(String(200), nullable=False)
    follow_up_message: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    provider_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    lead: Mapped["Lead"] = relationship(back_populates="intelligence")
