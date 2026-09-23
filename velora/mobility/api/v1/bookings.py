"""Booking endpoints."""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from mobility.api.deps import get_current_user, require_permission, require_user
from mobility.api.v1.schemas import BookingCreateIn, OtpVerifyIn, TransitionIn
from mobility.database import get_db
from mobility.models.auth import User
from mobility.models.booking import Booking
from mobility.services.booking_service import (
    booking_to_dict,
    confirm_booking,
    create_booking,
    generate_boarding_otp,
    transition_booking,
    verify_boarding_otp,
)
from mobility.services.dispatch_service import assign_driver, create_dispatch
from mobility.services.flight_service import flight_to_dict, sync_flight
from mobility.services.payment_service import authorize_payment, capture_payment, create_payment_intent
from mobility.services.pricing_service import calculate_quote

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("")
def create(body: BookingCreateIn, db: Annotated[Session, Depends(get_db)], user: Annotated[User | None, Depends(get_current_user)]):
    try:
        booking = create_booking(db, body.model_dump(), customer_id=user.id if user else None)
        payment = create_payment_intent(db, booking, body.idempotency_key or None)
        authorize_payment(db, payment, user.id if user else None)
        confirm_booking(db, booking, user.id if user else None)
        if booking.track_flight and booking.flight_number:
            sync_flight(db, booking, booking.flight_number)
        create_dispatch(db, booking)
        assign_driver(db, booking)
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(400, str(exc))
    return booking_to_dict(db, booking)


@router.get("/{booking_id}")
def get_booking(booking_id: str, db: Annotated[Session, Depends(get_db)]):
    booking = db.get(Booking, booking_id)
    if not booking:
        by_ref = db.query(Booking).filter(Booking.reference == booking_id).first()
        booking = by_ref
    if not booking:
        raise HTTPException(404, "Booking not found")
    return booking_to_dict(db, booking)


@router.get("/share/{token}")
def share_booking(token: str, db: Annotated[Session, Depends(get_db)]):
    booking = db.query(Booking).filter(Booking.share_token == token).first()
    if not booking:
        raise HTTPException(404, "Trip not found")
    data = booking_to_dict(db, booking)
    data.pop("boarding_otp", None)
    return data


@router.post("/{booking_id}/transition")
def transition(
    booking_id: str,
    body: TransitionIn,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_permission("booking.modify"))],
):
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(404, "Booking not found")
    try:
        transition_booking(db, booking, body.status, user.id, "staff", body.reason)
        if body.status == "COMPLETED":
            from mobility.models.payment import Payment

            payment = db.query(Payment).filter(Payment.booking_id == booking.id).first()
            if payment:
                capture_payment(db, payment, actor_id=user.id)
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(400, str(exc))
    return booking_to_dict(db, booking)


@router.post("/{booking_id}/otp/generate")
def otp_generate(booking_id: str, db: Annotated[Session, Depends(get_db)], user: Annotated[User, Depends(require_user)]):
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(404, "Booking not found")
    otp = generate_boarding_otp(db, booking)
    db.commit()
    return {"expires_in_minutes": 10, "message": "OTP sent to driver app only"}


@router.post("/{booking_id}/otp/verify")
def otp_verify(booking_id: str, body: OtpVerifyIn, db: Annotated[Session, Depends(get_db)], user: Annotated[User, Depends(require_user)]):
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(404, "Booking not found")
    ok = verify_boarding_otp(db, booking, body.otp)
    if not ok:
        db.rollback()
        raise HTTPException(400, "Invalid or expired OTP")
    db.commit()
    return booking_to_dict(db, booking)
