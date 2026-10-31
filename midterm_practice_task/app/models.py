from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class WantedCriminal(Base):
    __tablename__ = "wanted_criminals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nickname: Mapped[str] = mapped_column(String(255), nullable=False)
    reward: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    location_note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    difficulty: Mapped[int] = mapped_column(nullable=False)
    armed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_crew: Mapped[bool] = mapped_column(Boolean, nullable=False)
    escape_master: Mapped[bool] = mapped_column(Boolean, nullable=False)

    hunt_logs: Mapped[list["HuntLog"]] = relationship(back_populates="criminal")


class HuntLog(Base):
    __tablename__ = "hunt_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    criminal_id: Mapped[int] = mapped_column(ForeignKey("wanted_criminals.id"), nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    criminal: Mapped[WantedCriminal] = relationship(back_populates="hunt_logs")
