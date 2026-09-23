"""Dispatch models."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mobility.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Dispatch(Base):
    __tablename__ = "dispatches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    booking_id: Mapped[str] = mapped_column(ForeignKey("bookings.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    assigned_driver_id: Mapped[str | None] = mapped_column(ForeignKey("drivers.id"), nullable=True)
    assigned_vehicle_id: Mapped[str | None] = mapped_column(ForeignKey("vehicles.id"), nullable=True)
    mode: Mapped[str] = mapped_column(String(32), default="auto")
    decision_log_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    attempts: Mapped[list["DispatchAttempt"]] = relationship(back_populates="dispatch", cascade="all, delete-orphan")


class DispatchAttempt(Base):
    __tablename__ = "dispatch_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    dispatch_id: Mapped[str] = mapped_column(ForeignKey("dispatches.id", ondelete="CASCADE"))
    driver_id: Mapped[str] = mapped_column(ForeignKey("drivers.id"))
    status: Mapped[str] = mapped_column(String(32), default="sent")
    rank_score: Mapped[int] = mapped_column(Integer, default=0)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    timeout_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    dispatch: Mapped[Dispatch] = relationship(back_populates="attempts")
