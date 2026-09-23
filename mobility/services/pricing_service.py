"""Rule-based pricing engine 1.0."""
from __future__ import annotations

import json
import math
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from catalog import EXTRAS, FIXED_ROUTES, FX, PROMOS, PRICING, SYMBOL
from mobility.models.fleet import Location, VehicleType
from mobility.models.pricing import Addon, PricingRule
from mobility.models.booking import Quote


def _rule_map(db: Session) -> dict[str, float]:
    rows = db.query(PricingRule).filter(PricingRule.is_active.is_(True)).all()
    if rows:
        return {r.code: r.value for r in rows}
    return {
        "base": PRICING["base"],
        "per_km": PRICING["per_km"],
        "per_min": PRICING["per_min"],
        "min_fare": PRICING["min_fare"],
        "airport": PRICING["airport"],
        "night": PRICING["night"],
        "stop": PRICING["stop"],
        "service_fee": PRICING["service_fee"],
        "hourly_base": 880,
    }


def _hav(a: Location, b: Location) -> float:
    r = 6371
    p1, p2 = math.radians(a.lat), math.radians(b.lat)
    dphi = math.radians(b.lat - a.lat)
    dlmb = math.radians(b.lng - a.lng)
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(min(1, math.sqrt(h)))


def _road_km(a: Location, b: Location) -> float:
    return round(_hav(a, b) * 1.35, 1)


def _night(when: datetime) -> bool:
    h = when.hour
    return h >= 22 or h < 6


def _convert(twd: int, currency: str) -> int:
    if currency == "TWD":
        return twd
    return max(1, round(twd * FX.get(currency, 1.0)))


def capacity_check(db: Session, vehicle_type_id: str, pax: int, bags: int) -> dict[str, Any]:
    vt = db.get(VehicleType, vehicle_type_id)
    if not vt:
        return {"ok": False, "reason": "unknown_vehicle_type"}
    if pax > vt.max_pax or bags > vt.luggage_capacity + 1:
        upgrade = (
            db.query(VehicleType)
            .filter(VehicleType.is_active.is_(True), VehicleType.max_pax >= pax, VehicleType.luggage_capacity >= bags)
            .order_by(VehicleType.price_multiplier.asc())
            .first()
        )
        return {
            "ok": False,
            "reason": "capacity_exceeded",
            "recommended_upgrade": upgrade.id if upgrade else None,
            "message": f"Passengers/luggage exceed {vt.name} capacity",
        }
    return {"ok": True, "vehicle_type": vt.id}


def eligible_vehicle_types(db: Session, pax: int, bags: int) -> list[VehicleType]:
    return (
        db.query(VehicleType)
        .filter(
            VehicleType.is_active.is_(True),
            VehicleType.max_pax >= pax,
            VehicleType.luggage_capacity + 1 >= bags,
        )
        .order_by(VehicleType.price_multiplier.asc())
        .all()
    )


def calculate_quote(db: Session, payload: dict[str, Any]) -> dict[str, Any]:
    rules = _rule_map(db)
    pickup = db.get(Location, payload["pickup_id"])
    dest = db.get(Location, payload["dest_id"])
    if not pickup or not dest:
        raise ValueError("Unknown location")
    stop_ids = payload.get("stops") or []
    stops = [db.get(Location, sid) for sid in stop_ids]
    if any(s is None for s in stops):
        raise ValueError("Unknown stop location")
    pts = [pickup, *stops, dest]
    km = sum(_road_km(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
    mins = max(12, int(km / 0.55))
    vt = db.get(VehicleType, payload.get("class_id") or "standard")
    if not vt:
        raise ValueError("Unknown vehicle class")
    cap = capacity_check(db, vt.id, int(payload.get("pax", 1)), int(payload.get("bags", 1)))
    if not cap["ok"]:
        raise ValueError(cap.get("message", "Capacity exceeded"))
    pair = (pickup.id, dest.id)
    reverse = (dest.id, pickup.id)
    fixed = FIXED_ROUTES.get(pair) or FIXED_ROUTES.get(reverse)
    service = payload.get("service") or "airport"
    if service == "hourly":
        hours = int(payload.get("hours") or 4)
        base = int(rules["hourly_base"] * hours * vt.price_multiplier)
        mins = hours * 60
        km = round(hours * 28, 1)
    else:
        base = fixed if fixed and not stops else max(
            int(rules["min_fare"]),
            int(rules["base"] + km * rules["per_km"] + mins * rules["per_min"]),
        )
        base = int(base * vt.price_multiplier)
    when_raw = payload.get("when") or datetime.now(timezone.utc).isoformat()
    when = datetime.fromisoformat(when_raw.replace("Z", "+00:00"))
    airport_fee = int(rules["airport"]) if pickup.kind == "airport" or dest.kind == "airport" else 0
    night_fee = int(base * rules["night"]) if _night(when) else 0
    stop_fee = int(rules["stop"]) * len(stops)
    extras_fee = 0
    extra_rows = []
    addon_ids = payload.get("extras") or []
    for eid in addon_ids:
        addon = db.get(Addon, eid)
        if addon:
            extras_fee += addon.price
            extra_rows.append({"id": addon.id, "name": addon.name, "price": addon.price})
        else:
            ex = next((e for e in EXTRAS if e["id"] == eid), None)
            if ex:
                extras_fee += ex["price"]
                extra_rows.append(ex)
    sub = base + airport_fee + night_fee + stop_fee + extras_fee
    if payload.get("roundtrip"):
        sub *= 2
        base *= 2
        airport_fee *= 2
        night_fee *= 2
        stop_fee *= 2
        extras_fee *= 2
    service_fee = int(sub * rules["service_fee"])
    discount = 0
    promo = PROMOS.get((payload.get("promo") or "").upper())
    if promo and sub >= promo["min"]:
        discount = promo["value"] if promo["type"] == "flat" else int(sub * promo["value"] / 100)
        if promo["type"] == "flat" and payload.get("roundtrip"):
            discount *= 2
    total = max(0, sub + service_fee - discount)
    curr = payload.get("currency") or "TWD"
    breakdown = {
        "base": _convert(base, curr),
        "airport": _convert(airport_fee, curr),
        "night": _convert(night_fee, curr),
        "stops": _convert(stop_fee, curr),
        "extras": _convert(extras_fee, curr),
        "service_fee": _convert(service_fee, curr),
        "discount": _convert(discount, curr),
        "total": _convert(total, curr),
    }
    quote = Quote(
        id=str(uuid.uuid4()),
        currency=curr,
        distance_km=km,
        duration_min=mins,
        subtotal=sub,
        total=total,
        twd_total=total,
        breakdown_json=json.dumps(breakdown),
        vehicle_type_id=vt.id,
        promo_code=(payload.get("promo") or "").upper() or None,
    )
    db.add(quote)
    db.flush()
    return {
        "quote_id": quote.id,
        "currency": curr,
        "symbol": SYMBOL.get(curr, curr),
        "km": km,
        "mins": mins,
        "breakdown": breakdown,
        "twd_total": total,
        "extras": extra_rows,
        "class": {
            "id": vt.id,
            "name": vt.name,
            "pax": vt.max_pax,
            "bags": vt.luggage_capacity,
            "mult": vt.price_multiplier,
            "img": vt.image_url,
        },
        "capacity": cap,
    }
