"""Payment provider abstraction."""
from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy.orm import Session

from mobility.config import get_settings
from mobility.models.booking import Booking
from mobility.models.payment import Payment, PaymentTransaction, Refund
from mobility.services.audit_service import log_action
from mobility.state_machine import can_transition

settings = get_settings()


def create_payment_intent(db: Session, booking: Booking, idempotency_key: str | None = None) -> Payment:
    existing = None
    if idempotency_key:
        existing = db.query(Payment).filter(Payment.idempotency_key == idempotency_key).first()
    if existing:
        return existing
    payment = Payment(
        id=str(uuid.uuid4()),
        booking_id=booking.id,
        provider="stripe" if settings.stripe_secret_key else "internal",
        status="pending",
        currency=booking.currency,
        amount=booking.total_amount,
        idempotency_key=idempotency_key or str(uuid.uuid4()),
    )
    db.add(payment)
    db.flush()
    return payment


def authorize_payment(db: Session, payment: Payment, actor_id: str | None = None) -> Payment:
    if not can_transition(payment.status, "authorized", {"pending": {"authorized", "failed"}}):
        raise ValueError(f"Cannot authorize payment in status {payment.status}")
    payment.status = "authorized"
    payment.authorized_amount = payment.amount
    txn = PaymentTransaction(
        id=str(uuid.uuid4()),
        payment_id=payment.id,
        type="authorize",
        status="succeeded",
        amount=payment.amount,
        currency=payment.currency,
        provider_ref=f"auth_{payment.id[:8]}",
        idempotency_key=f"auth-{payment.id}",
    )
    db.add(txn)
    db.flush()
    return payment


def capture_payment(db: Session, payment: Payment, amount: int | None = None, actor_id: str | None = None) -> Payment:
    if payment.status != "authorized":
        raise ValueError("Payment must be authorized before capture")
    cap = amount or payment.authorized_amount
    payment.status = "captured"
    payment.captured_amount = cap
    txn = PaymentTransaction(
        id=str(uuid.uuid4()),
        payment_id=payment.id,
        type="capture",
        status="succeeded",
        amount=cap,
        currency=payment.currency,
        provider_ref=f"cap_{payment.id[:8]}",
        idempotency_key=f"cap-{payment.id}",
    )
    db.add(txn)
    booking = db.get(Booking, payment.booking_id)
    if booking:
        booking.payment_status = "captured"
    db.flush()
    return payment


def refund_payment(
    db: Session,
    payment: Payment,
    amount: int,
    reason: str,
    actor_id: str | None = None,
    actor_email: str | None = None,
    fee_amount: int = 0,
) -> Refund:
    if payment.captured_amount - payment.refunded_amount < amount:
        raise ValueError("Refund exceeds captured amount")
    refund = Refund(
        id=str(uuid.uuid4()),
        payment_id=payment.id,
        booking_id=payment.booking_id,
        amount=amount,
        currency=payment.currency,
        status="completed",
        reason=reason,
        fee_amount=fee_amount,
        actor_id=actor_id,
    )
    payment.refunded_amount += amount
    payment.status = "refunded" if payment.refunded_amount >= payment.captured_amount else "partially_refunded"
    txn = PaymentTransaction(
        id=str(uuid.uuid4()),
        payment_id=payment.id,
        type="refund",
        status="succeeded",
        amount=amount,
        currency=payment.currency,
        provider_ref=f"ref_{refund.id[:8]}",
        idempotency_key=f"ref-{refund.id}",
    )
    db.add(refund)
    db.add(txn)
    log_action(
        db,
        actor_id=actor_id,
        actor_email=actor_email,
        action="payment.refund",
        entity_type="payment",
        entity_id=payment.id,
        after={"amount": amount, "reason": reason},
    )
    db.flush()
    return refund
