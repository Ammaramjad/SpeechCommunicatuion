"""Flight tracking models."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mobility.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Flight(Base):
    __tablename__ = "flights"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    booking_id: Mapped[str | None] = mapped_column(ForeignKey("bookings.id"), nullable=True, index=True)
    airline: Mapped[str | None] = mapped_column(String(64), nullable=True)
    flight_number: Mapped[str] = mapped_column(String(32), index=True)
    airport_code: Mapped[str | None] = mapped_column(String(8), nullable=True)
    scheduled_arrival: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    estimated_arrival: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_arrival: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="scheduled")
    provider: Mapped[str] = mapped_column(String(32), default="fallback")
    raw_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    events: Mapped[list["FlightEvent"]] = relationship(back_populates="flight", cascade="all, delete-orphan")


class FlightEvent(Base):
    __tablename__ = "flight_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    flight_id: Mapped[str] = mapped_column(ForeignKey("flights.id", ondelete="CASCADE"))
    event_type: Mapped[str] = mapped_column(String(32))
    previous_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    new_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    delay_minutes: Mapped[int | None] = mapped_column(nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    flight: Mapped[Flight] = relationship(back_populates="events")
