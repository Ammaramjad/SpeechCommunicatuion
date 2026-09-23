"""Flight tracking with provider abstraction and fallback."""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from mobility.config import get_settings
from mobility.models.booking import Booking
from mobility.models.flight import Flight, FlightEvent

settings = get_settings()


def _fallback_flight(code: str) -> dict[str, Any]:
    seed = int(hashlib.sha256(code.upper().encode()).hexdigest()[:8], 16)
    delay = seed % 45
    status_pool = ["scheduled", "delayed", "landed", "boarding"]
    status = status_pool[seed % len(status_pool)]
    now = datetime.now(timezone.utc)
    scheduled = now + timedelta(hours=2)
    estimated = scheduled + timedelta(minutes=delay)
    return {
        "airline": code[:2].upper(),
        "flight_number": code.upper(),
        "airport": "TPE",
        "scheduled_arrival": scheduled.isoformat(),
        "estimated_arrival": estimated.isoformat(),
        "actual_arrival": estimated.isoformat() if status == "landed" else None,
        "status": status,
        "delay_minutes": delay if status == "delayed" else 0,
        "provider": "fallback",
    }


def sync_flight(db: Session, booking: Booking | None, flight_number: str) -> Flight:
    data = _fallback_flight(flight_number)
    if settings.flight_api_key:
        data["provider"] = "external_stub"
    row = (
        db.query(Flight)
        .filter(Flight.flight_number == flight_number.upper(), Flight.booking_id == (booking.id if booking else None))
        .order_by(Flight.updated_at.desc())
        .first()
    )
    prev_status = row.status if row else None
    if not row:
        row = Flight(
            id=str(uuid.uuid4()),
            booking_id=booking.id if booking else None,
            airline=data["airline"],
            flight_number=data["flight_number"],
            airport_code=data["airport"],
            scheduled_arrival=datetime.fromisoformat(data["scheduled_arrival"]),
            estimated_arrival=datetime.fromisoformat(data["estimated_arrival"]),
            actual_arrival=datetime.fromisoformat(data["actual_arrival"]) if data.get("actual_arrival") else None,
            status=data["status"],
            provider=data["provider"],
            raw_json=json.dumps(data),
        )
        db.add(row)
    else:
        row.estimated_arrival = datetime.fromisoformat(data["estimated_arrival"])
        row.status = data["status"]
        row.raw_json = json.dumps(data)
        row.updated_at = datetime.now(timezone.utc)
    if prev_status != row.status:
        db.add(
            FlightEvent(
                id=str(uuid.uuid4()),
                flight_id=row.id,
                event_type="status_change",
                previous_status=prev_status,
                new_status=row.status,
                delay_minutes=data.get("delay_minutes"),
                metadata_json=json.dumps(data),
            )
        )
    db.flush()
    return row


def flight_to_dict(flight: Flight) -> dict[str, Any]:
    return {
        "id": flight.id,
        "airline": flight.airline,
        "flight_number": flight.flight_number,
        "airport": flight.airport_code,
        "scheduled_arrival": flight.scheduled_arrival.isoformat() if flight.scheduled_arrival else None,
        "estimated_arrival": flight.estimated_arrival.isoformat() if flight.estimated_arrival else None,
        "actual_arrival": flight.actual_arrival.isoformat() if flight.actual_arrival else None,
        "status": flight.status,
        "provider": flight.provider,
        "free_wait_minutes": settings.airport_free_wait_minutes,
    }
