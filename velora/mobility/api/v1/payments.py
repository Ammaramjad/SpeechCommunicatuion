"""Payment endpoints."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from mobility.api.deps import require_permission
from mobility.api.v1.schemas import PaymentIntentIn, RefundIn
from mobility.database import get_db
from mobility.models.auth import User
from mobility.models.booking import Booking
from mobility.models.payment import Payment
from mobility.services.booking_service import transition_booking
from mobility.services.payment_service import capture_payment, create_payment_intent, refund_payment

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/intent/{booking_id}")
def payment_intent(
    booking_id: str,
    body: PaymentIntentIn,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_permission("booking.create"))],
):
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(404, "Booking not found")
    payment = create_payment_intent(db, booking, body.idempotency_key or None)
    db.commit()
    return {"payment_id": payment.id, "status": payment.status, "amount": payment.amount, "currency": payment.currency}


@router.post("/capture/{payment_id}")
def payment_capture(payment_id: str, db: Annotated[Session, Depends(get_db)], user: Annotated[User, Depends(require_permission("booking.modify"))]):
    payment = db.get(Payment, payment_id)
    if not payment:
        raise HTTPException(404, "Payment not found")
    capture_payment(db, payment, actor_id=user.id)
    db.commit()
    return {"payment_id": payment.id, "status": payment.status, "captured_amount": payment.captured_amount}


@router.post("/refund/{payment_id}")
def payment_refund(
    payment_id: str,
    body: RefundIn,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_permission("payment.refund"))],
):
    payment = db.get(Payment, payment_id)
    if not payment:
        raise HTTPException(404, "Payment not found")
    amount = body.amount or (payment.captured_amount - payment.refunded_amount)
    refund = refund_payment(db, payment, amount, body.reason, user.id, user.email)
    booking = db.get(Booking, payment.booking_id)
    if booking:
        transition_booking(db, booking, "REFUNDED", user.id, "finance", body.reason)
    db.commit()
    return {"refund_id": refund.id, "amount": refund.amount, "status": refund.status}
