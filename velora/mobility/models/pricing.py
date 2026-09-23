"""Pricing rules, addons, and cancellation policies."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from mobility.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PricingRule(Base):
    __tablename__ = "pricing_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
    rule_type: Mapped[str] = mapped_column(String(32))
    value: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(8), default="TWD")
    service_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    region_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Addon(Base):
    __tablename__ = "addons"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    price: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(8), default="TWD")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class CancellationPolicy(Base):
    __tablename__ = "cancellation_policies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    service_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    hours_before: Mapped[float] = mapped_column(Float)
    fee_type: Mapped[str] = mapped_column(String(16), default="percent")
    fee_value: Mapped[float] = mapped_column(Float, default=0)
    is_no_show: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
