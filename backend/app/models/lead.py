from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import PipelineStage
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.activity import Activity
    from app.models.task import SalesTask


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    company: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    employees: Mapped[int] = mapped_column(Integer, nullable=False)
    need: Mapped[str] = mapped_column(String(500), nullable=False)
    budget: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    score_reasons: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    pipeline_stage: Mapped[PipelineStage] = mapped_column(
        Enum(
            PipelineStage,
            name="pipeline_stage",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
            values_callable=lambda enum: [item.value for item in enum],
        ),
        default=PipelineStage.NEW,
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    activities: Mapped[list["Activity"]] = relationship(
        back_populates="lead", cascade="all, delete-orphan", passive_deletes=True
    )
    tasks: Mapped[list["SalesTask"]] = relationship(
        back_populates="lead", cascade="all, delete-orphan", passive_deletes=True
    )
