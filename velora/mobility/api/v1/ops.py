"""Operations console endpoints."""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from mobility.api.deps import require_permission
from mobility.database import get_db
from mobility.models.auth import User
from mobility.models.booking import Booking
from mobility.models.fleet import Driver
from mobility.models.payment import Payment
from mobility.services.booking_service import booking_to_dict

router = APIRouter(prefix="/ops", tags=["ops"])


@router.get("/dashboard")
def dashboard(db: Annotated[Session, Depends(get_db)], user: Annotated[User, Depends(require_permission("analytics.view"))]) -> dict[str, Any]:
    bookings = db.query(Booking).all()
    statuses = {}
    for b in bookings:
        statuses[b.status] = statuses.get(b.status, 0) + 1
    online_drivers = db.query(Driver).filter(Driver.online_status == "online").count()
    unassigned = db.query(Booking).filter(Booking.status == "CONFIRMED", Booking.assigned_driver_id.is_(None)).count()
    return {
        "total_bookings": len(bookings),
        "by_status": statuses,
        "online_drivers": online_drivers,
        "unassigned": unassigned,
        "gmv_twd": sum(b.total_amount for b in bookings if b.status not in ("CANCELLED", "FAILED")),
    }


@router.get("/bookings")
def list_bookings(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_permission("booking.view"))],
    status: str | None = None,
    limit: int = Query(50, le=200),
):
    q = db.query(Booking).order_by(Booking.created_at.desc())
    if status:
        q = q.filter(Booking.status == status)
    rows = q.limit(limit).all()
    return [booking_to_dict(db, b) for b in rows]
