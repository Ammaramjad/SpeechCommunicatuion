"""Pricing endpoints."""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from mobility.api.v1.schemas import QuoteIn, SearchIn
from mobility.database import get_db
from mobility.services.pricing_service import calculate_quote, eligible_vehicle_types

router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.post("/quote")
def quote(body: QuoteIn, db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    try:
        return calculate_quote(db, body.model_dump())
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@router.post("/search")
def search(body: SearchIn, db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    classes = eligible_vehicle_types(db, body.pax, body.bags)
    results = []
    for vt in classes:
        try:
            q = calculate_quote(db, {**body.model_dump(), "class_id": vt.id})
            results.append({"class": q["class"], "price": q, "instant": True})
        except ValueError:
            continue
    return {"count": len(results), "results": results}
