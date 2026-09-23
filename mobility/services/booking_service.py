"""Booking lifecycle service."""
from __future__ import annotations

import json
import random
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from mobility.config import get_settings
from mobility.models.booking import (
    Booking,
    BookingAddon,
    BookingPassenger,
    BookingStatusHistory,
    BookingStop,
    Quote,
)
from mobility.services.audit_service import log_action
from mobility.services.pricing_service import calculate_quote, capacity_check
from mobility.state_machine import assert_booking_transition

settings = get_settings()


def _ref() -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "MB-" + "".join(random.choice(alphabet) for _ in range(8))


def _share_token() -> str:
    return secrets.token_urlsafe(24)


def _record_status(db: Session, booking: Booking, new_state: str, actor_id: str | None, actor_type: str, reason: str | None = None, metadata: dict | None = None) -> None:
    prev = booking.status
    assert_booking_transition(prev, new_state)
    booking.status = new_state
    booking.updated_at = datetime.now(timezone.utc)
    db.add(
        BookingStatusHistory(
            id=str(uuid.uuid4()),
            booking_id=booking.id,
            previous_state=prev,
            new_state=new_state,
            actor_id=actor_id,
            actor_type=actor_type,
            reason=reason,
            metadata_json=json.dumps(metadata) if metadata else None,
        )
    )


def create_booking(db: Session, payload: dict[str, Any], customer_id: str | None = None) -> Booking:
    cap = capacity_check(db, payload["class_id"], int(payload.get("pax", 1)), int(payload.get("bags", 1)))
    if not cap["ok"]:
        raise ValueError(cap.get("message", "Capacity exceeded"))
    quote_data = calculate_quote(db, payload)
    quote = db.get(Quote, quote_data["quote_id"])
    when_raw = payload["when"]
    pickup_at = datetime.fromisoformat(when_raw.replace("Z", "+00:00"))
    booking = Booking(
        id=str(uuid.uuid4()),
        reference=_ref(),
        customer_id=customer_id,
        service_type=payload.get("service") or "airport",
        status="DRAFT",
        pickup_location_id=payload["pickup_id"],
        destination_location_id=payload["dest_id"],
        pickup_at=pickup_at,
        timezone=payload.get("timezone") or settings.default_timezone,
        passenger_count=int(payload.get("pax", 1)),
        luggage_count=int(payload.get("bags", 1)),
        vehicle_type_id=payload["class_id"],
        flight_number=payload.get("flight") or None,
        airline=payload.get("airline") or None,
        track_flight=bool(payload.get("track_flight")),
        contact_first_name=payload["first"],
        contact_last_name=payload["last"],
        contact_email=payload["email"],
        contact_phone=payload["phone"],
        special_requirements=payload.get("notes") or None,
        currency=payload.get("currency") or settings.default_currency,
        total_amount=quote_data["twd_total"],
        quote_id=quote.id,
        creation_source=payload.get("channel") or "web",
        channel=payload.get("channel") or "velora",
        charter_hours=int(payload.get("hours") or 0) or None,
        roundtrip=bool(payload.get("roundtrip")),
        share_token=_share_token(),
    )
    db.add(booking)
    if quote:
        quote.booking_id = booking.id
    for idx, sid in enumerate(payload.get("stops") or []):
        db.add(BookingStop(id=str(uuid.uuid4()), booking_id=booking.id, location_id=sid, sequence=idx))
    for ex in quote_data.get("extras") or []:
        db.add(
            BookingAddon(
                id=str(uuid.uuid4()),
                booking_id=booking.id,
                addon_id=ex["id"],
                name=ex["name"],
                amount=ex["price"],
                currency=booking.currency,
            )
        )
    db.add(
        BookingPassenger(
            id=str(uuid.uuid4()),
            booking_id=booking.id,
            first_name=payload["first"],
            last_name=payload["last"],
            phone=payload.get("phone"),
            is_primary=True,
        )
    )
    db.add(
        BookingStatusHistory(
            id=str(uuid.uuid4()),
            booking_id=booking.id,
            previous_state=None,
            new_state="DRAFT",
            actor_id=customer_id,
            actor_type="customer",
            reason="created",
        )
    )
    db.flush()
    return booking


def confirm_booking(db: Session, booking: Booking, actor_id: str | None = None) -> Booking:
    _record_status(db, booking, "CONFIRMED", actor_id, "system", "payment_authorized")
    booking.payment_status = "authorized"
    db.flush()
    return booking


def transition_booking(db: Session, booking: Booking, new_state: str, actor_id: str | None, actor_type: str, reason: str | None = None) -> Booking:
    _record_status(db, booking, new_state, actor_id, actor_type, reason)
    db.flush()
    return booking


def generate_boarding_otp(db: Session, booking: Booking) -> str:
    otp = f"{random.randint(1000, 9999)}"
    booking.boarding_otp = otp
    booking.boarding_otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.otp_expire_minutes)
    booking.boarding_otp_attempts = 0
    db.flush()
    return otp


def verify_boarding_otp(db: Session, booking: Booking, otp: str) -> bool:
    if not booking.boarding_otp or not booking.boarding_otp_expires_at:
        return False
    if datetime.now(timezone.utc) > booking.boarding_otp_expires_at:
        return False
    booking.boarding_otp_attempts += 1
    if booking.boarding_otp_attempts > settings.otp_max_attempts:
        booking.boarding_otp = None
        db.flush()
        return False
    ok = booking.boarding_otp == otp
    if ok:
        booking.boarding_otp = None
        transition_booking(db, booking, "IN_PROGRESS", booking.assigned_driver_id, "driver", "otp_verified")
    db.flush()
    return ok


def booking_to_dict(db: Session, booking: Booking) -> dict[str, Any]:
    quote = db.get(Quote, booking.quote_id) if booking.quote_id else None
    return {
        "id": booking.id,
        "reference": booking.reference,
        "status": booking.status,
        "trip_status": booking.trip_status,
        "service_type": booking.service_type,
        "pickup_id": booking.pickup_location_id,
        "dest_id": booking.destination_location_id,
        "when": booking.pickup_at.isoformat(),
        "timezone": booking.timezone,
        "pax": booking.passenger_count,
        "bags": booking.luggage_count,
        "class_id": booking.vehicle_type_id,
        "driver_id": booking.assigned_driver_id,
        "vehicle_id": booking.assigned_vehicle_id,
        "flight": booking.flight_number,
        "track_flight": booking.track_flight,
        "first": booking.contact_first_name,
        "last": booking.contact_last_name,
        "email": booking.contact_email,
        "phone": booking.contact_phone,
        "notes": booking.special_requirements,
        "currency": booking.currency,
        "total_amount": booking.total_amount,
        "payment_status": booking.payment_status,
        "dispatch_status": booking.dispatch_status,
        "share_token": booking.share_token,
        "quote": {
            "breakdown": json.loads(quote.breakdown_json) if quote else {},
            "twd_total": quote.twd_total if quote else booking.total_amount,
        },
        "created_at": booking.created_at.isoformat() if booking.created_at else None,
    }
