"""Dispatch engine 1.0."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from mobility.config import get_settings
from mobility.models.booking import Booking
from mobility.models.dispatch import Dispatch, DispatchAttempt
from mobility.models.fleet import Driver, Vehicle
from mobility.services.audit_service import log_action
from mobility.services.booking_service import transition_booking

settings = get_settings()


def _eligible_drivers(db: Session, booking: Booking) -> list[Driver]:
    q = db.query(Driver).filter(
        Driver.approval_status == "approved",
        Driver.suspension_status == "active",
        Driver.online_status == "online",
    )
    if booking.vehicle_type_id:
        q = q.join(Vehicle, Driver.vehicle_id == Vehicle.id).filter(
            Vehicle.status == "active",
            Vehicle.vehicle_type_id == booking.vehicle_type_id,
        )
    return q.order_by(Driver.rejection_count.asc(), Driver.trip_count.asc()).all()


def create_dispatch(db: Session, booking: Booking, mode: str = "auto") -> Dispatch:
    dispatch = Dispatch(
        id=str(uuid.uuid4()),
        booking_id=booking.id,
        status="pending",
        mode=mode,
    )
    db.add(dispatch)
    booking.dispatch_status = "pending"
    db.flush()
    return dispatch


def assign_driver(
    db: Session,
    booking: Booking,
    driver_id: str | None = None,
    actor_id: str | None = None,
    actor_email: str | None = None,
    manual: bool = False,
) -> dict[str, Any]:
    dispatch = db.query(Dispatch).filter(Dispatch.booking_id == booking.id).order_by(Dispatch.created_at.desc()).first()
    if not dispatch:
        dispatch = create_dispatch(db, booking, mode="manual" if manual else "auto")
    drivers = _eligible_drivers(db, booking)
    if driver_id:
        driver = db.get(Driver, driver_id)
        if not driver:
            raise ValueError("Driver not found")
    elif drivers:
        idx = booking.id.__hash__() % len(drivers)
        driver = drivers[idx]
    else:
        raise ValueError("No eligible drivers available")
    attempt = DispatchAttempt(
        id=str(uuid.uuid4()),
        dispatch_id=dispatch.id,
        driver_id=driver.id,
        status="sent",
        rank_score=100 - driver.rejection_count,
        timeout_at=datetime.now(timezone.utc) + timedelta(seconds=settings.dispatch_timeout_seconds),
    )
    dispatch.status = "assigned"
    dispatch.assigned_driver_id = driver.id
    dispatch.assigned_vehicle_id = driver.vehicle_id
    dispatch.decision_log_json = json.dumps({"driver_id": driver.id, "mode": dispatch.mode, "eligible": len(drivers)})
    booking.assigned_driver_id = driver.id
    booking.assigned_vehicle_id = driver.vehicle_id
    booking.dispatch_status = "assigned"
    transition_booking(db, booking, "ASSIGNED", actor_id or "system", "dispatcher" if manual else "system", "driver_assigned")
    db.add(attempt)
    if manual:
        log_action(
            db,
            actor_id=actor_id,
            actor_email=actor_email,
            action="dispatch.manual",
            entity_type="booking",
            entity_id=booking.id,
            after={"driver_id": driver.id},
        )
    db.flush()
    return {"dispatch_id": dispatch.id, "driver_id": driver.id, "attempt_id": attempt.id}


def driver_respond(db: Session, booking: Booking, driver_id: str, accept: bool) -> dict[str, Any]:
    dispatch = db.query(Dispatch).filter(Dispatch.booking_id == booking.id).order_by(Dispatch.created_at.desc()).first()
    if not dispatch or dispatch.assigned_driver_id != driver_id:
        raise ValueError("No active dispatch for driver")
    attempt = (
        db.query(DispatchAttempt)
        .filter(DispatchAttempt.dispatch_id == dispatch.id, DispatchAttempt.driver_id == driver_id)
        .order_by(DispatchAttempt.created_at.desc())
        .first()
    )
    if not attempt:
        raise ValueError("Dispatch attempt not found")
    driver = db.get(Driver, driver_id)
    if accept:
        attempt.status = "accepted"
        attempt.responded_at = datetime.now(timezone.utc)
        dispatch.status = "accepted"
        booking.dispatch_status = "accepted"
    else:
        attempt.status = "rejected"
        attempt.responded_at = datetime.now(timezone.utc)
        dispatch.status = "rejected"
        if driver:
            driver.rejection_count += 1
        booking.assigned_driver_id = None
        booking.assigned_vehicle_id = None
        booking.dispatch_status = "rejected"
        transition_booking(db, booking, "CONFIRMED", driver_id, "driver", "driver_rejected")
        assign_driver(db, booking, manual=False)
    db.flush()
    return {"accepted": accept, "status": dispatch.status}
