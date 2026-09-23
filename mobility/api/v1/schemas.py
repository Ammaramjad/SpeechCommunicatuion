"""Pydantic schemas for API v1."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, EmailStr, Field


class AuthRegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=4)
    name: str
    phone: str = ""


class AuthLoginIn(BaseModel):
    email: EmailStr
    password: str


class QuoteIn(BaseModel):
    service: str = "airport"
    pickup_id: str
    dest_id: str
    when: str = ""
    pax: int = 2
    bags: int = 2
    hours: int = 4
    roundtrip: bool = False
    currency: str = "TWD"
    class_id: str = "standard"
    promo: str = ""
    extras: list[str] = Field(default_factory=list)
    stops: list[str] = Field(default_factory=list)


class SearchIn(QuoteIn):
    pass


class BookingCreateIn(QuoteIn):
    first: str
    last: str
    email: EmailStr
    phone: str
    flight: str = ""
    airline: str = ""
    track_flight: bool = False
    notes: str = ""
    channel: str = "web"
    payment_method: str = "card"
    idempotency_key: str = ""


class TransitionIn(BaseModel):
    status: str
    reason: str = ""


class PaymentIntentIn(BaseModel):
    idempotency_key: str = ""


class DispatchAssignIn(BaseModel):
    driver_id: str | None = None


class DispatchRespondIn(BaseModel):
    accept: bool = True


class OtpVerifyIn(BaseModel):
    otp: str


class RefundIn(BaseModel):
    amount: int | None = None
    reason: str = "customer_request"


class FlightManualIn(BaseModel):
    status: str
    estimated_arrival: str | None = None
    note: str = ""
