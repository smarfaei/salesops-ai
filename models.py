from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(100)
    )

    company: Mapped[str] = mapped_column(
        String(100)
    )

    employees: Mapped[int] = mapped_column(
        Integer
    )

    need: Mapped[str] = mapped_column(
        String(500)
    )

    budget: Mapped[int] = mapped_column(
        Integer
    )

    score: Mapped[int] = mapped_column(
        Integer
    )

    status: Mapped[str] = mapped_column(
        String(50)
    )