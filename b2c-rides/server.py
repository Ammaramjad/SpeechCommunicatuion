#!/usr/bin/env python3
"""RideLook Taiwan B2C + Fleet OS dispatch API."""
from __future__ import annotations

import json
import math
import random
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent
STORE = ROOT / "data" / "store.json"
STORE.parent.mkdir(exist_ok=True)

app = FastAPI(title="RideLook Taiwan Fleet API")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def twd(n: int) -> int:
    return int(n)


CATALOG = {
    "currency": "TWD",
    "symbol": "NT$",
    "cities": ["台北", "新北", "桃園", "台中", "台南", "高雄", "花蓮", "墾丁"],
    "places": [
        {"id": "tpe", "name_zh": "桃園國際機場 TPE", "name_en": "Taoyuan Airport TPE", "lat": 25.0777, "lng": 121.2328, "kind": "airport"},
        {"id": "tsa", "name_zh": "松山機場 TSA", "name_en": "Songshan Airport TSA", "lat": 25.0694, "lng": 121.5525, "kind": "airport"},
        {"id": "rmq", "name_zh": "台中國際機場 RMQ", "name_en": "Taichung Airport RMQ", "lat": 24.2647, "lng": 120.6206, "kind": "airport"},
        {"id": "khh", "name_zh": "高雄國際機場 KHH", "name_en": "Kaohsiung Airport KHH", "lat": 22.5771, "lng": 120.3500, "kind": "airport"},
        {"id": "taipei-main", "name_zh": "台北車站", "name_en": "Taipei Main Station", "lat": 25.0478, "lng": 121.5170, "kind": "city"},
        {"id": "ximen", "name_zh": "西門町", "name_en": "Ximending", "lat": 25.0420, "lng": 121.5080, "kind": "city"},
        {"id": "xinyi", "name_zh": "信義區／台北 101", "name_en": "Xinyi / Taipei 101", "lat": 25.0330, "lng": 121.5654, "kind": "city"},
        {"id": "beitou", "name_zh": "北投溫泉", "name_en": "Beitou Hot Springs", "lat": 25.1365, "lng": 121.5065, "kind": "city"},
        {"id": "jiufen", "name_zh": "九份老街", "name_en": "Jiufen Old Street", "lat": 25.1097, "lng": 121.8443, "kind": "city"},
        {"id": "hsr-taoyuan", "name_zh": "高鐵桃園站", "name_en": "THSR Taoyuan", "lat": 25.0132, "lng": 121.2152, "kind": "rail"},
        {"id": "taichung", "name_zh": "台中火車站", "name_en": "Taichung Station", "lat": 24.1368, "lng": 120.6850, "kind": "city"},
        {"id": "kaohsiung", "name_zh": "高雄捷運美麗島", "name_en": "Formosa Boulevard", "lat": 22.6314, "lng": 120.3019, "kind": "city"},
        {"id": "kenting", "name_zh": "墾丁大街", "name_en": "Kenting Main Street", "lat": 21.9483, "lng": 120.7794, "kind": "city"},
    ],
    "routes": [
        {"id": "tpe-taipei", "from": "tpe", "to": "taipei-main", "mins": 50, "from_price": 1280, "img": "https://images.unsplash.com/photo-1474181487882-5abf3f0ba6c2?auto=format&fit=crop&w=900&q=60"},
        {"id": "tpe-xinyi", "from": "tpe", "to": "xinyi", "mins": 55, "from_price": 1380, "img": "https://images.unsplash.com/photo-1474181487882-5abf3f0ba6c2?auto=format&fit=crop&w=900&q=60"},
        {"id": "tpe-ximen", "from": "tpe", "to": "ximen", "mins": 48, "from_price": 1250, "img": "https://images.unsplash.com/photo-1526481280695-3c46980681a4?auto=format&fit=crop&w=900&q=70"},
        {"id": "tpe-jiufen", "from": "tpe", "to": "jiufen", "mins": 70, "from_price": 1680, "img": "https://images.unsplash.com/photo-1524413840807-0c3cb6fa808d?auto=format&fit=crop&w=900&q=60"},
        {"id": "tsa-xinyi", "from": "tsa", "to": "xinyi", "mins": 20, "from_price": 480, "img": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?auto=format&fit=crop&w=900&q=60"},
        {"id": "khh-city", "from": "khh", "to": "kaohsiung", "mins": 25, "from_price": 520, "img": "https://images.unsplash.com/photo-1578271887552-5ac3a72752bc?auto=format&fit=crop&w=900&q=60"},
        {"id": "rmq-tc", "from": "rmq", "to": "taichung", "mins": 30, "from_price": 650, "img": "https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?auto=format&fit=crop&w=900&q=60"},
        {"id": "tpe-hsr", "from": "tpe", "to": "hsr-taoyuan", "mins": 15, "from_price": 420, "img": "https://images.unsplash.com/photo-1474487548417-781cb71495f3?auto=format&fit=crop&w=900&q=60"},
    ],
    "vehicles": [
        {"id": "sedan", "class": "sedan", "name_zh": "舒適轎車 Toyota Camry", "name_en": "Comfort sedan Camry", "seats": 3, "bags": 3, "price": 1280, "old": 1580, "img": "https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&w=900&q=60", "shared": False},
        {"id": "premium", "class": "premium", "name_zh": "豪華轎車 Mercedes E-Class", "name_en": "Luxury Mercedes E-Class", "seats": 3, "bags": 3, "price": 2680, "old": 3200, "img": "https://images.unsplash.com/photo-1618843479313-40f8afb4b4d8?auto=format&fit=crop&w=900&q=60", "shared": False},
        {"id": "suv", "class": "suv", "name_zh": "休旅車 Toyota RAV4 / CR-V", "name_en": "SUV RAV4 / CR-V", "seats": 4, "bags": 4, "price": 1680, "old": 1980, "img": "https://images.unsplash.com/photo-1519641471654-76ce0107ad1b?auto=format&fit=crop&w=900&q=60", "shared": False},
        {"id": "mpv", "class": "mpv", "name_zh": "商務車 Toyota Alphard", "name_en": "MPV Toyota Alphard", "seats": 6, "bags": 6, "price": 2280, "old": 2680, "img": "https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?auto=format&fit=crop&w=900&q=60", "shared": False},
        {"id": "van", "class": "van", "name_zh": "九人座廂型車", "name_en": "9-seater van", "seats": 8, "bags": 8, "price": 2480, "old": 2880, "img": "https://images.unsplash.com/photo-1544620341-11cb2cd49d66?auto=format&fit=crop&w=900&q=60", "shared": False},
        {"id": "shuttle", "class": "shuttle", "name_zh": "共享接駁 Shuttle", "name_en": "Shared shuttle", "seats": 10, "bags": 1, "price": 380, "old": 450, "img": "https://images.unsplash.com/photo-1570125909232-eb263c188f7e?auto=format&fit=crop&w=900&q=60", "shared": True},
    ],
    "taxi_classes": [
        {"id": "taxi", "name_zh": "一般計程車", "name_en": "Standard taxi", "eta": 3, "price": 185},
        {"id": "plus", "name_zh": "舒適型", "name_en": "Comfort", "eta": 5, "price": 265},
        {"id": "xl", "name_zh": "六人座", "name_en": "XL 6-seater", "eta": 7, "price": 420},
        {"id": "black", "name_zh": "尊榮黑卡", "name_en": "Black luxury", "eta": 9, "price": 880},
    ],
    "rentals": [
        {"id": "yaris", "name_zh": "Toyota Yaris 或同級", "name_en": "Toyota Yaris or similar", "trans": "AT", "seats": 5, "day": 1680, "img": "https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?auto=format&fit=crop&w=900&q=60"},
        {"id": "corolla", "name_zh": "Toyota Corolla Cross", "name_en": "Corolla Cross", "trans": "AT", "seats": 5, "day": 2280, "img": "https://images.unsplash.com/photo-1519641471654-76ce0107ad1b?auto=format&fit=crop&w=900&q=60"},
        {"id": "sienta", "name_zh": "Toyota Sienta 七人座", "name_en": "Sienta 7-seater", "trans": "AT", "seats": 7, "day": 2680, "img": "https://images.unsplash.com/photo-1464219789935-c2d9d9aba894?auto=format&fit=crop&w=900&q=60"},
    ],
    "promos": {
        "WELCOME": {"type": "flat", "value": 100, "label_zh": "新客折 NT$100", "label_en": "NT$100 off"},
        "TPE200": {"type": "flat", "value": 200, "label_zh": "機場接送折 NT$200", "label_en": "NT$200 airport off"},
        "FAMILY": {"type": "pct", "value": 10, "label_zh": "家庭 9 折", "label_en": "10% family off"},
    },
}

DRIVERS_SEED = [
    {"id": "d1", "name": "林志偉", "name_en": "Chih-Wei Lin", "phone": "0912-111-223", "plate": "TPE-3388", "vehicle": "sedan", "rating": 4.97, "lat": 25.06, "lng": 121.30, "lang": ["zh-TW", "en"]},
    {"id": "d2", "name": "陳淑芬", "name_en": "Shu-Fen Chen", "phone": "0933-555-019", "plate": "KHH-2291", "vehicle": "suv", "rating": 4.93, "lat": 25.04, "lng": 121.52, "lang": ["zh-TW"]},
    {"id": "d3", "name": "王大明", "name_en": "Ta-Ming Wang", "phone": "0988-200-441", "plate": "TPE-8801", "vehicle": "mpv", "rating": 4.99, "lat": 25.08, "lng": 121.24, "lang": ["zh-TW", "en", "ja"]},
    {"id": "d4", "name": "黃建宏", "name_en": "Chien-Hung Huang", "phone": "0921-774-330", "plate": "TXG-1024", "vehicle": "van", "rating": 4.88, "lat": 24.16, "lng": 120.64, "lang": ["zh-TW"]},
    {"id": "d5", "name": "高橋蓮", "name_en": "Ren Takahashi", "phone": "0975-018-662", "plate": "TPE-6666", "vehicle": "premium", "rating": 5.0, "lat": 25.03, "lng": 121.56, "lang": ["zh-TW", "en", "ja"]},
    {"id": "d6", "name": "吳佩玲", "name_en": "Pei-Ling Wu", "phone": "0918-909-121", "plate": "KHH-4410", "vehicle": "taxi", "rating": 4.91, "lat": 22.63, "lng": 120.30, "lang": ["zh-TW"]},
]


def empty_store() -> dict[str, Any]:
    drivers = []
    for d in DRIVERS_SEED:
        row = dict(d)
        row["status"] = "available"
        row["job_id"] = None
        drivers.append(row)
    return {"bookings": [], "drivers": drivers, "alerts": []}


def load() -> dict[str, Any]:
    if not STORE.exists():
        data = empty_store()
        save(data)
        return data
    return json.loads(STORE.read_text())


def save(data: dict[str, Any]) -> None:
    STORE.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def place(pid: str) -> dict[str, Any]:
    for p in CATALOG["places"]:
        if p["id"] == pid:
            return p
    raise HTTPException(404, "Unknown place")


def vehicle(vid: str) -> dict[str, Any]:
    for v in CATALOG["vehicles"] + CATALOG["rentals"]:
        if v["id"] == vid:
            return v
    for v in CATALOG["taxi_classes"]:
        if v["id"] == vid:
            return v
    raise HTTPException(404, "Unknown vehicle")


def night_surcharge(when: str) -> bool:
    try:
        hour = int(when[11:13])
    except Exception:
        return False
    return hour >= 23 or hour < 6


def quote_amount(body: dict[str, Any]) -> dict[str, int]:
    vid = body.get("vehicle_id") or "sedan"
    v = vehicle(vid)
    base = int(v.get("price") or v.get("day") or 0)
    hours = int(body.get("hours") or 1)
    days = int(body.get("days") or 1)
    btype = body.get("type") or "airport_pickup"
    if btype == "hourly":
        base = 880 * hours
    elif btype == "rental":
        base = int(v.get("day", 1680)) * days
    elif btype == "instant":
        base = int(v.get("price", 185))
    extras = 0
    extras += 150 if body.get("meet") else 0
    extras += 200 if body.get("child_seat") else 0
    extras += 120 if body.get("english") else 0
    extras += 200 if body.get("pet") else 0
    extras += 250 if body.get("one_way_rental") else 0
    extras += 450 if body.get("insurance") else 0
    night = twd(round(base * 0.2)) if night_surcharge(body.get("when") or "") else 0
    sub = base + extras + night
    discount = 0
    promo = CATALOG["promos"].get((body.get("promo") or "").upper())
    if promo:
        discount = promo["value"] if promo["type"] == "flat" else twd(round(sub * promo["value"] / 100))
    total = max(0, sub - discount)
    return {"base": base, "extras": extras, "night": night, "discount": discount, "total": total}


class QuoteIn(BaseModel):
    type: str = "airport_pickup"
    from_id: str = "tpe"
    to_id: str = "taipei-main"
    when: str = ""
    pax: int = 2
    bags: int = 2
    vehicle_id: str = "sedan"
    hours: int = 8
    days: int = 2
    meet: bool = True
    child_seat: bool = False
    english: bool = False
    pet: bool = False
    one_way_rental: bool = False
    insurance: bool = False
    promo: str = ""


class BookingIn(QuoteIn):
    channel: str = "web"
    name: str = "林小華"
    phone: str = "0912-000-888"
    flight: str = "CI 011"
    notes: str = ""


class StatusIn(BaseModel):
    status: str
    note: str = ""


class AssignIn(BaseModel):
    driver_id: str


class DispatchBookIn(BookingIn):
    channel: str = "dispatch"


class AlertIn(BaseModel):
    message: str
    level: str = "info"


def attach_place_names(booking: dict[str, Any]) -> dict[str, Any]:
    out = dict(booking)
    try:
        out["from_place"] = place(booking["from_id"])
        out["to_place"] = place(booking["to_id"])
    except HTTPException:
        out["from_place"] = {"name_zh": booking.get("from_id"), "name_en": booking.get("from_id")}
        out["to_place"] = {"name_zh": booking.get("to_id"), "name_en": booking.get("to_id")}
    try:
        out["vehicle"] = vehicle(booking["vehicle_id"])
    except HTTPException:
        out["vehicle"] = {"name_zh": booking.get("vehicle_id"), "name_en": booking.get("vehicle_id")}
    data = load()
    out["driver"] = next((d for d in data["drivers"] if d["id"] == booking.get("driver_id")), None)
    return out


@app.get("/api/catalog")
def catalog() -> dict[str, Any]:
    return CATALOG


@app.post("/api/quote")
def api_quote(body: QuoteIn) -> dict[str, Any]:
    fare = quote_amount(body.model_dump())
    return {"currency": "TWD", "symbol": "NT$", "fare": fare, "night": fare["night"] > 0}


@app.get("/api/promo/{code}")
def api_promo(code: str) -> dict[str, Any]:
    promo = CATALOG["promos"].get(code.upper())
    if not promo:
        raise HTTPException(404, "Invalid promo")
    return {"code": code.upper(), **promo}


@app.get("/api/bookings")
def list_bookings(channel: Optional[str] = None) -> list[dict[str, Any]]:
    rows = load()["bookings"]
    if channel:
        rows = [b for b in rows if b.get("channel") == channel]
    return [attach_place_names(b) for b in sorted(rows, key=lambda x: x["created_at"], reverse=True)]


@app.get("/api/bookings/{bid}")
def get_booking(bid: str) -> dict[str, Any]:
    data = load()
    b = next((x for x in data["bookings"] if x["id"] == bid), None)
    if not b:
        raise HTTPException(404, "Booking not found")
    return attach_place_names(b)


@app.post("/api/bookings")
def create_booking(body: BookingIn) -> dict[str, Any]:
    data = load()
    fare = quote_amount(body.model_dump())
    bid = "RL" + uuid.uuid4().hex[:8].upper()
    otp = f"{random.randint(1000, 9999)}"
    booking = {
        **body.model_dump(),
        "id": bid,
        "otp": otp,
        "status": "new",
        "driver_id": None,
        "fare": fare,
        "currency": "TWD",
        "created_at": now_iso(),
        "timeline": [{"at": now_iso(), "status": "new", "note": f"Created via {body.channel}"}],
    }
    if body.type == "instant":
        assigned = next((d for d in data["drivers"] if d["status"] == "available"), None)
        if assigned:
            booking["driver_id"] = assigned["id"]
            booking["status"] = "assigned"
            assigned["status"] = "busy"
            assigned["job_id"] = bid
            booking["timeline"].append({"at": now_iso(), "status": "assigned", "note": assigned["name"]})
    data["bookings"].insert(0, booking)
    save(data)
    return attach_place_names(booking)


@app.post("/api/bookings/{bid}/status")
def set_status(bid: str, body: StatusIn) -> dict[str, Any]:
    data = load()
    b = next((x for x in data["bookings"] if x["id"] == bid), None)
    if not b:
        raise HTTPException(404, "Booking not found")
    b["status"] = body.status
    b["timeline"].append({"at": now_iso(), "status": body.status, "note": body.note})
    if body.status in {"completed", "cancelled"} and b.get("driver_id"):
        for d in data["drivers"]:
            if d["id"] == b["driver_id"]:
                d["status"] = "available"
                d["job_id"] = None
    save(data)
    return attach_place_names(b)


@app.post("/api/bookings/{bid}/assign")
def assign(bid: str, body: AssignIn) -> dict[str, Any]:
    data = load()
    b = next((x for x in data["bookings"] if x["id"] == bid), None)
    d = next((x for x in data["drivers"] if x["id"] == body.driver_id), None)
    if not b or not d:
        raise HTTPException(404, "Booking or driver not found")
    if b.get("driver_id"):
        prev = next((x for x in data["drivers"] if x["id"] == b["driver_id"]), None)
        if prev:
            prev["status"] = "available"
            prev["job_id"] = None
    b["driver_id"] = d["id"]
    b["status"] = "assigned"
    d["status"] = "busy"
    d["job_id"] = bid
    b["timeline"].append({"at": now_iso(), "status": "assigned", "note": d["name"]})
    save(data)
    return attach_place_names(b)


@app.get("/api/drivers")
def drivers() -> list[dict[str, Any]]:
    return load()["drivers"]


@app.post("/api/drivers/{did}/toggle")
def toggle_driver(did: str) -> dict[str, Any]:
    data = load()
    d = next((x for x in data["drivers"] if x["id"] == did), None)
    if not d:
        raise HTTPException(404, "Driver not found")
    if d["status"] == "offline":
        d["status"] = "available"
    elif d["status"] == "available":
        d["status"] = "offline"
    save(data)
    return d


@app.get("/api/fleet/summary")
def fleet_summary() -> dict[str, Any]:
    data = load()
    bookings = data["bookings"]
    drivers = data["drivers"]
    active = [b for b in bookings if b["status"] not in {"completed", "cancelled"}]
    gmv = sum(b.get("fare", {}).get("total", 0) for b in bookings if b["status"] != "cancelled")
    return {
        "currency": "TWD",
        "active_jobs": len(active),
        "available_drivers": sum(1 for d in drivers if d["status"] == "available"),
        "busy_drivers": sum(1 for d in drivers if d["status"] == "busy"),
        "gmv": gmv,
        "on_time": 97,
        "alerts": data.get("alerts", [])[-8:],
        "channels": {
            "web": sum(1 for b in bookings if b.get("channel") == "web"),
            "app": sum(1 for b in bookings if b.get("channel") == "app"),
            "dispatch": sum(1 for b in bookings if b.get("channel") == "dispatch"),
        },
    }


@app.post("/api/fleet/alert")
def add_alert(body: AlertIn) -> dict[str, Any]:
    data = load()
    row = {"id": uuid.uuid4().hex[:6], "at": now_iso(), **body.model_dump()}
    data["alerts"].append(row)
    save(data)
    return row


@app.post("/api/demo/reset")
def reset() -> dict[str, str]:
    save(empty_store())
    return {"ok": "reset"}


app.mount("/assets", StaticFiles(directory=ROOT / "assets"), name="assets")


@app.get("/")
def hub() -> FileResponse:
    return FileResponse(ROOT / "index.html")


@app.get("/{page_name}")
def html_page(page_name: str) -> FileResponse:
    if not page_name.endswith(".html"):
        raise HTTPException(404)
    path = ROOT / page_name
    if not path.exists():
        raise HTTPException(404)
    return FileResponse(path)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=4173, reload=False)
