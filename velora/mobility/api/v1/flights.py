"""Flight endpoints."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from mobility.api.deps import require_permission
from mobility.api.v1.schemas import FlightManualIn
from mobility.database import get_db
from mobility.models.auth import User
from mobility.models.booking import Booking
from mobility.models.flight import Flight
from mobility.services.audit_service import log_action
from mobility.services.flight_service import flight_to_dict, sync_flight

router = APIRouter(prefix="/flights", tags=["flights"])


@router.get("/{flight_number}")
def get_flight(flight_number: str, db: Annotated[Session, Depends(get_db)]):
    row = sync_flight(db, None, flight_number)
    db.commit()
    return flight_to_dict(row)


@router.post("/sync/{booking_id}")
def sync_booking_flight(booking_id: str, db: Annotated[Session, Depends(get_db)]):
    booking = db.get(Booking, booking_id)
    if not booking or not booking.flight_number:
        raise HTTPException(404, "Booking or flight not found")
    row = sync_flight(db, booking, booking.flight_number)
    db.commit()
    return flight_to_dict(row)


@router.post("/{flight_id}/manual")
def manual_update(
    flight_id: str,
    body: FlightManualIn,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_permission("booking.modify"))],
):
    row = db.get(Flight, flight_id)
    if not row:
        raise HTTPException(404, "Flight not found")
    before = flight_to_dict(row)
    row.status = body.status
    if body.estimated_arrival:
        row.estimated_arrival = datetime.fromisoformat(body.estimated_arrival.replace("Z", "+00:00"))
    row.updated_at = datetime.now(timezone.utc)
    log_action(
        db,
        actor_id=user.id,
        actor_email=user.email,
        action="flight.manual_update",
        entity_type="flight",
        entity_id=flight_id,
        before=before,
        after=flight_to_dict(row),
        metadata={"note": body.note},
    )
    db.commit()
    return flight_to_dict(row)
