#!/usr/bin/env python3
"""VELORA — private-car marketplace API (demo, no card storage)."""
from __future__ import annotations

import hashlib
import json
import math
import random
import secrets
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import FileResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from catalog import (
    CLASSES,
    DRIVERS,
    EXTRAS,
    FAQ,
    FEATURE_FLAGS,
    FIXED_ROUTES,
    FLEET_OS_URL,
    FX,
    HELP,
    LOCATIONS,
    OPERATORS,
    POPULAR,
    PRICING,
    PROMOS,
    REVIEWS,
    SYMBOL,
    VEHICLES,
)

ROOT = Path(__file__).resolve().parent
STORE = ROOT / "data" / "store.json"
STORE.parent.mkdir(exist_ok=True)
LOCK = threading.Lock()

app = FastAPI(title="VELORA API")
app.mount("/assets", StaticFiles(directory=ROOT / "assets"), name="assets")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def loc(lid: str) -> dict[str, Any]:
    for x in LOCATIONS:
        if x["id"] == lid:
            return x
    raise HTTPException(404, "Unknown location")


def klass(cid: str) -> dict[str, Any]:
    for x in CLASSES:
        if x["id"] == cid:
            return x
    raise HTTPException(404, "Unknown class")


def operator(oid: str) -> dict[str, Any]:
    for x in OPERATORS:
        if x["id"] == oid:
            return x
    raise HTTPException(404, "Unknown operator")


def hav(a: dict[str, Any], b: dict[str, Any]) -> float:
    r = 6371
    p1, p2 = math.radians(a["lat"]), math.radians(b["lat"])
    dphi = math.radians(b["lat"] - a["lat"])
    dlmb = math.radians(b["lng"] - a["lng"])
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(min(1, math.sqrt(h)))


def road_km(a: dict[str, Any], b: dict[str, Any]) -> float:
    return round(hav(a, b) * 1.35, 1)


def ref() -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "VR-" + "".join(random.choice(alphabet) for _ in range(6))


def empty_store() -> dict[str, Any]:
    users = [
        {"id": "u-emma", "email": "emma@velora.demo", "name": "Emma Chen", "role": "customer", "password": hash_pw("demo"), "phone": "+886910000111"},
        {"id": "u-driver", "email": "driver@velora.demo", "name": "Wei Lin", "role": "driver", "password": hash_pw("demo"), "driver_id": "d01"},
        {"id": "u-admin", "email": "admin@velora.demo", "name": "Aurel Ops", "role": "admin", "password": hash_pw("demo")},
        {"id": "u-disp", "email": "dispatch@velora.demo", "name": "Mina Dispatch", "role": "dispatcher", "password": hash_pw("demo")},
    ]
    return {
        "users": users,
        "sessions": {},
        "bookings": [],
        "wishlist": [],
        "tickets": [],
        "events": [],
        "notifications": [],
        "audit": [],
        "saved": [],
        "drivers": [dict(d) for d in DRIVERS],
        "vehicles": [dict(v) for v in VEHICLES],
    }


def hash_pw(pw: str) -> str:
    return hashlib.sha256(("velora:" + pw).encode()).hexdigest()


def load() -> dict[str, Any]:
    with LOCK:
        if not STORE.exists():
            data = empty_store()
            STORE.write_text(json.dumps(data, ensure_ascii=False, indent=2))
            return data
        return json.loads(STORE.read_text())


def save(data: dict[str, Any]) -> None:
    with LOCK:
        tmp = STORE.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        tmp.replace(STORE)


def user_from(authorization: Optional[str]) -> Optional[dict[str, Any]]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    data = load()
    uid = data["sessions"].get(token)
    if not uid:
        return None
    return next((u for u in data["users"] if u["id"] == uid), None)


def require_role(authorization: Optional[str], roles: set[str]) -> dict[str, Any]:
    u = user_from(authorization)
    if not u or u["role"] not in roles:
        raise HTTPException(401, "Unauthorized")
    return u


def convert(twd: int, currency: str) -> int:
    return max(1, round(twd * FX.get(currency, 1.0))) if currency != "TWD" else twd


def night(when: str) -> bool:
    try:
        h = int(when[11:13]) if "T" in when else int(when.split(":")[0])
        return h >= 22 or h < 6
    except Exception:
        return False


def price_quote(body: dict[str, Any]) -> dict[str, Any]:
    pickup = loc(body["pickup_id"])
    dest = loc(body["dest_id"])
    stops = [loc(s) for s in body.get("stops") or []]
    pts = [pickup, *stops, dest]
    km = sum(road_km(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
    mins = max(12, int(km / 0.55))
    cl = klass(body.get("class_id") or "standard")
    pair = (body["pickup_id"], body["dest_id"])
    reverse = (body["dest_id"], body["pickup_id"])
    fixed = FIXED_ROUTES.get(pair) or FIXED_ROUTES.get(reverse)
    base = fixed if fixed and not stops else max(PRICING["min_fare"], int(PRICING["base"] + km * PRICING["per_km"] + mins * PRICING["per_min"]))
    base = int(base * cl["mult"])
    if body.get("service") == "hourly":
        hours = int(body.get("hours") or 4)
        base = int(880 * hours * cl["mult"])
        mins = hours * 60
        km = round(hours * 28, 1)
    airport_fee = PRICING["airport"] if pickup["kind"] == "airport" or dest["kind"] == "airport" else 0
    night_fee = int(base * PRICING["night"]) if night(body.get("when") or "") else 0
    stop_fee = PRICING["stop"] * len(stops)
    extras_fee = 0
    extra_rows = []
    for eid in body.get("extras") or []:
        ex = next((e for e in EXTRAS if e["id"] == eid), None)
        if ex:
            extras_fee += ex["price"]
            extra_rows.append(ex)
    sub = base + airport_fee + night_fee + stop_fee + extras_fee
    service_fee = int(sub * PRICING["service_fee"])
    discount = 0
    promo = PROMOS.get((body.get("promo") or "").upper())
    if promo and sub >= promo["min"]:
        discount = promo["value"] if promo["type"] == "flat" else int(sub * promo["value"] / 100)
    total = max(0, sub + service_fee - discount)
    if body.get("roundtrip"):
        total *= 2
        base *= 2
    curr = body.get("currency") or "TWD"
    return {
        "currency": curr,
        "symbol": SYMBOL[curr],
        "km": km,
        "mins": mins,
        "breakdown": {
            "base": convert(base, curr),
            "airport": convert(airport_fee, curr),
            "night": convert(night_fee, curr),
            "stops": convert(stop_fee, curr),
            "extras": convert(extras_fee, curr),
            "service_fee": convert(service_fee, curr),
            "discount": convert(discount, curr),
            "tolls": "estimated_included",
            "parking": "separate",
            "total": convert(total, curr),
        },
        "twd_total": total,
        "extras": extra_rows,
        "class": cl,
    }


class SearchIn(BaseModel):
    service: str = "airport"
    mode: str = "pickup"
    pickup_id: str
    dest_id: str
    when: str = ""
    pax: int = 2
    bags: int = 2
    hours: int = 4
    roundtrip: bool = False
    currency: str = "TWD"
    extras: list[str] = Field(default_factory=list)
    stops: list[str] = Field(default_factory=list)


class QuoteIn(SearchIn):
    class_id: str = "standard"
    promo: str = ""


class BookIn(QuoteIn):
    first: str
    last: str
    email: str
    phone: str
    flight: str = ""
    airline: str = ""
    track_flight: bool = False
    meet: bool = False
    notes: str = ""
    for_someone: bool = False
    passenger_name: str = ""
    payment: str = "card"
    guest: bool = True
    terms: bool = True
    line_id: str = ""
    whatsapp: str = ""


class AuthIn(BaseModel):
    email: str
    password: str = "demo"
    name: str = ""


class StatusIn(BaseModel):
    status: str
    note: str = ""


class AssignIn(BaseModel):
    driver_id: str


class TicketIn(BaseModel):
    category: str
    message: str
    booking_id: str = ""


class EventIn(BaseModel):
    name: str
    meta: dict[str, Any] = Field(default_factory=dict)


class PromoIn(BaseModel):
    code: str
    class_id: str = "standard"
    pickup_id: str = "tpe"
    dest_id: str = "taipei-101"
    when: str = "2026-09-16T10:00"
    currency: str = "TWD"


@app.get("/api/meta")
def meta() -> dict[str, Any]:
    return {
        "brand": "VELORA",
        "fleet_os": FLEET_OS_URL,
        "flags": FEATURE_FLAGS,
        "languages": ["en", "zh-TW", "zh-CN", "ja", "ko", "ar"],
        "currencies": list(FX.keys()),
        "symbols": SYMBOL,
        "services": ["airport", "p2p", "hourly"],
        "roles": ["super_admin", "admin", "dispatcher", "support", "finance", "operator", "driver", "customer"],
    }


@app.get("/api/locations")
def locations(q: str = "") -> list[dict[str, Any]]:
    ql = q.lower().strip()
    rows = LOCATIONS
    if ql:
        rows = [x for x in rows if ql in x["name"].lower() or ql in x["city"].lower() or ql in x["id"]]
    return rows[:20]


@app.get("/api/catalog")
def catalog() -> dict[str, Any]:
    return {
        "classes": CLASSES,
        "operators": OPERATORS,
        "locations": LOCATIONS,
        "popular": POPULAR,
        "extras": EXTRAS,
        "reviews": REVIEWS,
        "faq": FAQ,
        "help": HELP,
        "promos": list(PROMOS.keys()),
        "fleet_os": FLEET_OS_URL,
    }


@app.post("/api/search")
def search(body: SearchIn) -> dict[str, Any]:
    pickup, dest = loc(body.pickup_id), loc(body.dest_id)
    results = []
    for cl in CLASSES:
        vehicles = [v for v in VEHICLES if v["class_id"] == cl["id"] and v["status"] == "active"]
        if not vehicles:
            continue
        if body.pax > cl["pax"] or body.bags > cl["bags"] + 1:
            continue
        q = price_quote({**body.model_dump(), "class_id": cl["id"]})
        veh = vehicles[0]
        op = operator(veh["operator_id"])
        results.append({
            "class": cl,
            "vehicle": veh,
            "operator": op,
            "instant": cl["id"] not in {"minibus"},
            "free_cancel": True,
            "duration": q["mins"],
            "distance": q["km"],
            "price": q,
            "popular": cl["id"] in {"standard", "business", "mpv"},
        })
    return {"pickup": pickup, "dest": dest, "count": len(results), "results": results}


@app.post("/api/quote")
def quote(body: QuoteIn) -> dict[str, Any]:
    return price_quote(body.model_dump())


@app.post("/api/promo/check")
def promo_check(body: PromoIn) -> dict[str, Any]:
    p = PROMOS.get(body.code.upper())
    if not p:
        raise HTTPException(404, "Invalid code")
    q = price_quote(body.model_dump() | {"promo": body.code})
    return {"promo": p, "quote": q}


@app.get("/api/flights/{code}")
def flight(code: str) -> dict[str, Any]:
    delay = abs(hash(code.upper()) % 40)
    return {
        "code": code.upper(),
        "status": "delayed" if delay > 12 else "on_time",
        "delay_min": delay if delay > 12 else 0,
        "eta": "local+delay",
        "tracked": True,
    }


@app.post("/api/auth/register")
def register(body: AuthIn) -> dict[str, Any]:
    data = load()
    if any(u["email"] == body.email.lower() for u in data["users"]):
        raise HTTPException(400, "Email exists")
    user = {
        "id": "u-" + uuid.uuid4().hex[:8],
        "email": body.email.lower(),
        "name": body.name or body.email.split("@")[0],
        "role": "customer",
        "password": hash_pw(body.password or "demo"),
        "phone": "",
    }
    data["users"].append(user)
    token = secrets.token_hex(16)
    data["sessions"][token] = user["id"]
    save(data)
    return {"token": token, "user": {k: user[k] for k in ("id", "email", "name", "role")}}


@app.post("/api/auth/login")
def login(body: AuthIn) -> dict[str, Any]:
    data = load()
    user = next((u for u in data["users"] if u["email"] == body.email.lower() and u["password"] == hash_pw(body.password or "demo")), None)
    if not user:
        raise HTTPException(401, "Invalid credentials")
    token = secrets.token_hex(16)
    data["sessions"][token] = user["id"]
    save(data)
    return {"token": token, "user": {k: user[k] for k in ("id", "email", "name", "role") if k in user}}


@app.post("/api/bookings")
def create_booking(body: BookIn, authorization: Optional[str] = Header(None)) -> dict[str, Any]:
    if not body.terms:
        raise HTTPException(400, "Terms required")
    data = load()
    q = price_quote(body.model_dump())
    user = user_from(authorization)
    bid = ref()
    otp = f"{random.randint(1000, 9999)}"
    booking = {
        **body.model_dump(),
        "id": bid,
        "public_id": bid,
        "otp": otp,
        "status": "payment_confirmed",
        "payment_status": "paid",
        "driver_id": None,
        "quote": q,
        "created_at": now_iso(),
        "user_id": user["id"] if user else None,
        "timeline": [{"at": now_iso(), "status": "payment_confirmed", "note": "Paid via " + body.payment}],
        "audit": [{"at": now_iso(), "who": user["email"] if user else "guest", "change": "created"}],
    }
    data["bookings"].insert(0, booking)
    data["notifications"].append({"at": now_iso(), "event": "booking_created", "booking": bid, "channel": "email"})
    save(data)
    return attach(booking)


def attach(b: dict[str, Any]) -> dict[str, Any]:
    out = dict(b)
    out["pickup"] = loc(b["pickup_id"])
    out["dest"] = loc(b["dest_id"])
    out["class"] = klass(b.get("class_id") or "standard")
    drv = None
    data = load()
    if b.get("driver_id"):
        drv = next((d for d in data["drivers"] if d["id"] == b["driver_id"]), None)
        if drv:
            out["driver"] = {k: drv[k] for k in ("id", "first", "rating", "photo", "lang", "vehicle_id", "status") if k in drv}
            veh = next((v for v in data["vehicles"] if v["id"] == drv.get("vehicle_id")), None)
            if veh:
                out["driver"]["plate"] = veh["plate"]
                out["driver"]["model"] = f"{veh['brand']} {veh['model']}"
    return out


@app.get("/api/bookings")
def list_bookings(email: Optional[str] = None, authorization: Optional[str] = Header(None)) -> list[dict[str, Any]]:
    data = load()
    user = user_from(authorization)
    rows = data["bookings"]
    if user and user["role"] == "customer":
        rows = [b for b in rows if b.get("user_id") == user["id"] or b.get("email") == user["email"]]
    elif email:
        rows = [b for b in rows if b.get("email") == email]
    return [attach(b) for b in rows]


@app.get("/api/bookings/{bid}")
def get_booking(bid: str, email: Optional[str] = None) -> dict[str, Any]:
    data = load()
    b = next((x for x in data["bookings"] if x["id"] == bid), None)
    if not b:
        raise HTTPException(404, "Not found")
    if email and b.get("email") != email:
        raise HTTPException(404, "Not found")
    return attach(b)


@app.post("/api/bookings/{bid}/cancel")
def cancel(bid: str) -> dict[str, Any]:
    return set_status(bid, StatusIn(status="cancelled", note="customer cancel"))


@app.post("/api/bookings/{bid}/status")
def set_status(bid: str, body: StatusIn) -> dict[str, Any]:
    data = load()
    b = next((x for x in data["bookings"] if x["id"] == bid), None)
    if not b:
        raise HTTPException(404, "Not found")
    b["status"] = body.status
    b["timeline"].append({"at": now_iso(), "status": body.status, "note": body.note})
    save(data)
    return attach(b)


@app.post("/api/bookings/{bid}/assign")
def assign(bid: str, body: AssignIn, authorization: Optional[str] = Header(None)) -> dict[str, Any]:
    data = load()
    b = next((x for x in data["bookings"] if x["id"] == bid), None)
    d = next((x for x in data["drivers"] if x["id"] == body.driver_id), None)
    if not b or not d:
        raise HTTPException(404, "Not found")
    b["driver_id"] = d["id"]
    b["status"] = "driver_assigned"
    d["status"] = "busy"
    b["timeline"].append({"at": now_iso(), "status": "driver_assigned", "note": d["first"]})
    save(data)
    return attach(b)


@app.post("/api/bookings/{bid}/rebook")
def rebook_token(bid: str) -> dict[str, Any]:
    data = load()
    b = next((x for x in data["bookings"] if x["id"] == bid), None)
    if not b:
        raise HTTPException(404, "Not found")
    return {"pickup_id": b["pickup_id"], "dest_id": b["dest_id"], "pax": b.get("pax"), "bags": b.get("bags"), "class_id": b.get("class_id")}


@app.get("/api/admin/metrics")
def metrics(authorization: Optional[str] = Header(None)) -> dict[str, Any]:
    data = load()
    bs = data["bookings"]
    def n(st): return sum(1 for b in bs if b["status"] == st)
    gmv = sum(b.get("quote", {}).get("twd_total", 0) for b in bs if b.get("payment_status") == "paid")
    return {
        "bookings": len(bs),
        "pending": n("searching_driver") + n("payment_confirmed"),
        "active": sum(1 for b in bs if b["status"] in {"driver_en_route", "driver_arrived", "on_board", "trip_started"}),
        "completed": n("trip_completed"),
        "cancelled": n("cancelled"),
        "gmv": gmv,
        "avg": int(gmv / max(1, len(bs))),
        "drivers_online": sum(1 for d in data["drivers"] if d["status"] == "online"),
        "vehicles": sum(1 for v in data["vehicles"] if v["status"] == "active"),
        "customers": sum(1 for u in data["users"] if u["role"] == "customer"),
        "conversion": 42,
        "fleet_os": FLEET_OS_URL,
    }


@app.get("/api/drivers")
def drivers() -> list[dict[str, Any]]:
    return load()["drivers"]


@app.post("/api/drivers/{did}/toggle")
def toggle_driver(did: str) -> dict[str, Any]:
    data = load()
    d = next((x for x in data["drivers"] if x["id"] == did), None)
    if not d:
        raise HTTPException(404, "Not found")
    d["status"] = "offline" if d["status"] == "online" else "online"
    save(data)
    return d


@app.post("/api/tickets")
def ticket(body: TicketIn) -> dict[str, Any]:
    data = load()
    row = {"id": "TK-" + uuid.uuid4().hex[:6].upper(), "at": now_iso(), **body.model_dump(), "status": "open"}
    data["tickets"].append(row)
    save(data)
    return row


@app.post("/api/events")
def track(body: EventIn) -> dict[str, str]:
    return {"ok": "tracked"}


@app.post("/api/demo/reset")
def reset() -> dict[str, str]:
    save(empty_store())
    return {"ok": "reset"}


@app.get("/robots.txt")
def robots() -> PlainTextResponse:
    return PlainTextResponse("User-agent: *\nAllow: /\nSitemap: /sitemap.xml\n")


@app.get("/sitemap.xml")
def sitemap() -> Response:
    urls = ["/", "/results.html", "/help.html", "/airport-transfer/taiwan/tpe-taoyuan-airport"]
    xml = '<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f"<url><loc>{u}</loc></url>" for u in urls) + "</urlset>"
    return Response(xml, media_type="application/xml")


@app.get("/")
def home() -> FileResponse:
    return FileResponse(ROOT / "index.html")


@app.get("/airport-transfer/taiwan/tpe-taoyuan-airport")
def seo_tpe() -> FileResponse:
    return FileResponse(ROOT / "seo.html")


@app.get("/{page_name}")
def pages(page_name: str) -> FileResponse:
    path = ROOT / page_name
    if path.exists() and path.suffix in {".html", ".json", ".txt"}:
        return FileResponse(path)
    raise HTTPException(404)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=4173, reload=False)
