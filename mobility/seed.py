"""Seed database with roles, catalog data, and demo users."""
from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from catalog import CLASSES, DRIVERS, EXTRAS, LOCATIONS, PRICING, VEHICLES
from mobility.auth import hash_password
from mobility.models.auth import Permission, Role, User
from mobility.models.fleet import Driver, Location, Vehicle, VehicleType
from mobility.models.pricing import Addon, CancellationPolicy, PricingRule
from mobility.permissions import PERMISSIONS, ROLE_PERMISSIONS


def seed_if_empty(db: Session) -> None:
    if db.query(Role).count() > 0:
        return
    perm_rows = {}
    for code, name in PERMISSIONS:
        p = Permission(id=str(uuid.uuid4()), code=code, name=name)
        db.add(p)
        perm_rows[code] = p
    role_rows = {}
    for code, perm_codes in ROLE_PERMISSIONS.items():
        role = Role(id=str(uuid.uuid4()), code=code, name=code.replace("_", " ").title())
        role.permissions = [perm_rows[c] for c in perm_codes if c in perm_rows]
        db.add(role)
        role_rows[code] = role
    for loc in LOCATIONS:
        db.add(
            Location(
                id=loc["id"],
                name=loc["name"],
                city=loc["city"],
                kind=loc["kind"],
                lat=loc["lat"],
                lng=loc["lng"],
            )
        )
    for cl in CLASSES:
        db.add(
            VehicleType(
                id=cl["id"],
                name=cl["name"],
                example=cl.get("example"),
                seat_capacity=cl["pax"],
                recommended_pax=max(1, cl["pax"] - 1),
                max_pax=cl["pax"],
                luggage_capacity=cl["bags"],
                large_suitcases=cl["bags"],
                child_seat=cl.get("child", True),
                wheelchair=cl.get("wheelchair", False),
                price_multiplier=cl["mult"],
                image_url=cl.get("img"),
            )
        )
    for v in VEHICLES:
        db.add(
            Vehicle(
                id=v["id"],
                vehicle_type_id=v["class_id"],
                operator_id=v.get("operator_id"),
                brand=v["brand"],
                model=v["model"],
                year=v["year"],
                color=v.get("color"),
                plate=v["plate"],
                fuel=v.get("fuel"),
                status=v.get("status", "active"),
            )
        )
    for d in DRIVERS:
        db.add(
            Driver(
                id=d["id"],
                first_name=d["first"],
                last_name=d["last"],
                photo_url=d.get("photo"),
                rating=d.get("rating", 5.0),
                vehicle_id=d.get("vehicle_id"),
                operator_id=d.get("operator_id"),
                online_status=d.get("status", "offline"),
                lat=d.get("lat"),
                lng=d.get("lng"),
                approval_status="approved",
            )
        )
    for ex in EXTRAS:
        db.add(Addon(id=ex["id"], name=ex["name"], price=ex["price"]))
    pricing_rules = [
        ("base", "Base fare", "fixed", PRICING["base"]),
        ("per_km", "Per km", "distance", PRICING["per_km"]),
        ("per_min", "Per minute", "time", PRICING["per_min"]),
        ("min_fare", "Minimum fare", "fixed", PRICING["min_fare"]),
        ("airport", "Airport surcharge", "surcharge", PRICING["airport"]),
        ("night", "Night surcharge rate", "multiplier", PRICING["night"]),
        ("stop", "Extra stop", "fixed", PRICING["stop"]),
        ("service_fee", "Service fee rate", "multiplier", PRICING["service_fee"]),
        ("hourly_base", "Hourly base", "fixed", 880),
    ]
    for code, name, rtype, value in pricing_rules:
        db.add(PricingRule(id=str(uuid.uuid4()), code=code, name=name, rule_type=rtype, value=value))
    db.add(CancellationPolicy(id=str(uuid.uuid4()), name=">24h full refund", hours_before=24, fee_type="percent", fee_value=0))
    db.add(CancellationPolicy(id=str(uuid.uuid4()), name="12-24h partial", hours_before=12, fee_type="percent", fee_value=50))
    db.add(CancellationPolicy(id=str(uuid.uuid4()), name="No-show", hours_before=0, fee_type="percent", fee_value=100, is_no_show=True))
    demos = [
        ("emma@velora.demo", "Emma Chen", "CUSTOMER"),
        ("driver@velora.demo", "Wei Lin", "DRIVER"),
        ("admin@velora.demo", "Aurel Ops", "ADMIN"),
        ("dispatch@velora.demo", "Mina Dispatch", "DISPATCHER"),
    ]
    for email, name, role_code in demos:
        user = User(
            id=str(uuid.uuid4()),
            email=email,
            password_hash=hash_password("demo"),
            name=name,
            phone="+886910000111" if "driver" in email else None,
        )
        if role_code in role_rows:
            user.roles.append(role_rows[role_code])
        db.add(user)
        if role_code == "DRIVER":
            driver = db.get(Driver, "d01")
            if driver:
                driver.user_id = user.id
    db.commit()
