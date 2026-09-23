"""Fleet, vehicle, driver, and location models."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mobility.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(128))
    kind: Mapped[str] = mapped_column(String(32), default="landmark")
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Taipei")
    country_code: Mapped[str] = mapped_column(String(8), default="TW")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class VehicleType(Base):
    __tablename__ = "vehicle_types"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    example: Mapped[str | None] = mapped_column(String(255), nullable=True)
    seat_capacity: Mapped[int] = mapped_column(Integer)
    recommended_pax: Mapped[int] = mapped_column(Integer)
    max_pax: Mapped[int] = mapped_column(Integer)
    luggage_capacity: Mapped[int] = mapped_column(Integer)
    large_suitcases: Mapped[int] = mapped_column(Integer, default=2)
    small_luggage: Mapped[int] = mapped_column(Integer, default=2)
    child_seat: Mapped[bool] = mapped_column(Boolean, default=True)
    wheelchair: Mapped[bool] = mapped_column(Boolean, default=False)
    price_multiplier: Mapped[float] = mapped_column(Float, default=1.0)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    features_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    vehicle_type_id: Mapped[str] = mapped_column(ForeignKey("vehicle_types.id"))
    operator_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    brand: Mapped[str] = mapped_column(String(64))
    model: Mapped[str] = mapped_column(String(64))
    year: Mapped[int] = mapped_column(Integer)
    color: Mapped[str | None] = mapped_column(String(32), nullable=True)
    plate: Mapped[str] = mapped_column(String(32))
    fuel: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active")
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    vehicle_type: Mapped[VehicleType] = relationship()
    driver: Mapped["Driver | None"] = relationship(back_populates="vehicle", uselist=False)


class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    first_name: Mapped[str] = mapped_column(String(128))
    last_name: Mapped[str] = mapped_column(String(128))
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    license_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    license_expiry: Mapped[datetime | None] = mapped_column(nullable=True)
    approval_status: Mapped[str] = mapped_column(String(32), default="approved")
    suspension_status: Mapped[str] = mapped_column(String(32), default="active")
    online_status: Mapped[str] = mapped_column(String(32), default="offline")
    rating: Mapped[float] = mapped_column(Float, default=5.0)
    service_score: Mapped[float] = mapped_column(Float, default=5.0)
    vehicle_id: Mapped[str | None] = mapped_column(ForeignKey("vehicles.id"), nullable=True)
    operator_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    service_regions: Mapped[str | None] = mapped_column(Text, nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    rejection_count: Mapped[int] = mapped_column(Integer, default=0)
    trip_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    user: Mapped["User | None"] = relationship(back_populates="driver_profile")
    vehicle: Mapped[Vehicle | None] = relationship(back_populates="driver", foreign_keys=[vehicle_id])


from mobility.models.auth import User  # noqa: E402
