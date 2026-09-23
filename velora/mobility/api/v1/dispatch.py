"""Dispatch endpoints."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from mobility.api.deps import client_ip, require_permission, require_user
from mobility.api.v1.schemas import DispatchAssignIn, DispatchRespondIn
from mobility.database import get_db
from mobility.models.auth import User
from mobility.models.booking import Booking
from mobility.services.booking_service import booking_to_dict, transition_booking
from mobility.services.dispatch_service import assign_driver, driver_respond

router = APIRouter(prefix="/dispatch", tags=["dispatch"])


@router.post("/assign/{booking_id}")
def assign(
    booking_id: str,
    body: DispatchAssignIn,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_permission("dispatch.manual"))],
    ip: Annotated[str | None, Depends(client_ip)],
):
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(404, "Booking not found")
    try:
        result = assign_driver(db, booking, body.driver_id, user.id, user.email, manual=True)
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(400, str(exc))
    return {"booking": booking_to_dict(db, booking), **result}


@router.post("/respond/{booking_id}")
def respond(
    booking_id: str,
    body: DispatchRespondIn,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
):
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(404, "Booking not found")
    driver_id = booking.assigned_driver_id
    if not driver_id:
        raise HTTPException(400, "No driver assigned")
    try:
        result = driver_respond(db, booking, driver_id, body.accept)
        if body.accept:
            transition_booking(db, booking, "EN_ROUTE", driver_id, "driver", "accepted")
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(400, str(exc))
    return {"booking": booking_to_dict(db, booking), **result}
