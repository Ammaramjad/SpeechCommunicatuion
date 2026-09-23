"""Canonical booking model and related entities."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mobility.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    reference: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    customer_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    service_type: Mapped[str] = mapped_column(String(32), default="airport")
    status: Mapped[str] = mapped_column(String(32), default="DRAFT", index=True)
    trip_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    pickup_location_id: Mapped[str] = mapped_column(ForeignKey("locations.id"))
    destination_location_id: Mapped[str] = mapped_column(ForeignKey("locations.id"))
    pickup_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Taipei")
    passenger_count: Mapped[int] = mapped_column(Integer, default=1)
    luggage_count: Mapped[int] = mapped_column(Integer, default=1)
    vehicle_type_id: Mapped[str | None] = mapped_column(ForeignKey("vehicle_types.id"), nullable=True)
    assigned_vehicle_id: Mapped[str | None] = mapped_column(ForeignKey("vehicles.id"), nullable=True)
    assigned_driver_id: Mapped[str | None] = mapped_column(ForeignKey("drivers.id"), nullable=True)
    flight_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    airline: Mapped[str | None] = mapped_column(String(64), nullable=True)
    track_flight: Mapped[bool] = mapped_column(Boolean, default=False)
    contact_first_name: Mapped[str] = mapped_column(String(128))
    contact_last_name: Mapped[str] = mapped_column(String(128))
    contact_email: Mapped[str] = mapped_column(String(255))
    contact_phone: Mapped[str] = mapped_column(String(32))
    special_requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    currency: Mapped[str] = mapped_column(String(8), default="TWD")
    total_amount: Mapped[int] = mapped_column(Integer, default=0)
    quote_id: Mapped[str | None] = mapped_column(ForeignKey("quotes.id"), nullable=True)
    payment_status: Mapped[str] = mapped_column(String(32), default="pending")
    dispatch_status: Mapped[str] = mapped_column(String(32), default="pending")
    creation_source: Mapped[str] = mapped_column(String(32), default="web")
    channel: Mapped[str] = mapped_column(String(32), default="velora")
    external_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    charter_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    roundtrip: Mapped[bool] = mapped_column(Boolean, default=False)
    boarding_otp: Mapped[str | None] = mapped_column(String(8), nullable=True)
    boarding_otp_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    boarding_otp_attempts: Mapped[int] = mapped_column(Integer, default=0)
    share_token: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    stops: Mapped[list["BookingStop"]] = relationship(back_populates="booking", cascade="all, delete-orphan")
    addons: Mapped[list["BookingAddon"]] = relationship(back_populates="booking", cascade="all, delete-orphan")
    passengers: Mapped[list["BookingPassenger"]] = relationship(back_populates="booking", cascade="all, delete-orphan")
    status_history: Mapped[list["BookingStatusHistory"]] = relationship(back_populates="booking", cascade="all, delete-orphan")
    quote: Mapped["Quote | None"] = relationship(back_populates="booking", uselist=False, foreign_keys="Quote.booking_id")


class BookingStop(Base):
    __tablename__ = "booking_stops"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    booking_id: Mapped[str] = mapped_column(ForeignKey("bookings.id", ondelete="CASCADE"))
    location_id: Mapped[str] = mapped_column(ForeignKey("locations.id"))
    sequence: Mapped[int] = mapped_column(Integer, default=0)

    booking: Mapped[Booking] = relationship(back_populates="stops")


class BookingAddon(Base):
    __tablename__ = "booking_addons"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    booking_id: Mapped[str] = mapped_column(ForeignKey("bookings.id", ondelete="CASCADE"))
    addon_id: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(128))
    amount: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(8), default="TWD")

    booking: Mapped[Booking] = relationship(back_populates="addons")


class BookingPassenger(Base):
    __tablename__ = "booking_passengers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    booking_id: Mapped[str] = mapped_column(ForeignKey("bookings.id", ondelete="CASCADE"))
    first_name: Mapped[str] = mapped_column(String(128))
    last_name: Mapped[str] = mapped_column(String(128))
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    booking: Mapped[Booking] = relationship(back_populates="passengers")


class BookingStatusHistory(Base):
    __tablename__ = "booking_status_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    booking_id: Mapped[str] = mapped_column(ForeignKey("bookings.id", ondelete="CASCADE"), index=True)
    previous_state: Mapped[str | None] = mapped_column(String(32), nullable=True)
    new_state: Mapped[str] = mapped_column(String(32))
    actor_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    actor_type: Mapped[str] = mapped_column(String(32), default="system")
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    booking: Mapped[Booking] = relationship(back_populates="status_history")


class Quote(Base):
    __tablename__ = "quotes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    booking_id: Mapped[str | None] = mapped_column(ForeignKey("bookings.id"), nullable=True)
    currency: Mapped[str] = mapped_column(String(8), default="TWD")
    distance_km: Mapped[float] = mapped_column(Float, default=0)
    duration_min: Mapped[int] = mapped_column(Integer, default=0)
    subtotal: Mapped[int] = mapped_column(Integer, default=0)
    total: Mapped[int] = mapped_column(Integer, default=0)
    twd_total: Mapped[int] = mapped_column(Integer, default=0)
    breakdown_json: Mapped[str] = mapped_column(Text)
    vehicle_type_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    promo_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    booking: Mapped[Booking | None] = relationship(back_populates="quote", foreign_keys=[booking_id])
