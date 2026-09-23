"""Mobility platform API v1 integration tests."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1] / "velora"
sys.path.insert(0, str(ROOT))

_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["MOBILITY_DATABASE_URL"] = f"sqlite:///{_db_file.name}"

from mobility.database import SessionLocal, init_db  # noqa: E402
from mobility.seed import seed_if_empty  # noqa: E402

init_db()
_db = SessionLocal()
seed_if_empty(_db)
_db.close()

from server import app, save, empty_store  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_store():
    save(empty_store())


def _login(email: str = "admin@velora.demo") -> str:
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "demo"})
    assert r.status_code == 200
    return r.json()["token"]


def test_v1_quote_and_search():
    r = client.post(
        "/api/v1/pricing/quote",
        json={"pickup_id": "tpe", "dest_id": "taipei-101", "class_id": "standard", "when": "2026-09-16T10:00"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["breakdown"]["total"] > 0
    search = client.post(
        "/api/v1/pricing/search",
        json={"pickup_id": "tpe", "dest_id": "taipei-101", "when": "2026-09-16T10:00", "pax": 2, "bags": 2},
    )
    assert search.status_code == 200
    assert search.json()["count"] >= 5


def test_capacity_rejection():
    r = client.post(
        "/api/v1/pricing/quote",
        json={"pickup_id": "tpe", "dest_id": "taipei-101", "class_id": "economy", "pax": 20, "bags": 20},
    )
    assert r.status_code == 400


def test_full_booking_lifecycle():
    booking = client.post(
        "/api/v1/bookings",
        json={
            "pickup_id": "tpe",
            "dest_id": "taipei-101",
            "when": "2026-09-16T10:00",
            "first": "Ada",
            "last": "Lovelace",
            "email": "ada@example.com",
            "phone": "+886900000001",
            "class_id": "business",
            "pax": 2,
            "bags": 2,
            "flight": "CI011",
            "track_flight": True,
            "idempotency_key": "test-life-1",
        },
    )
    assert booking.status_code == 200
    b = booking.json()
    assert b["reference"].startswith("MB-")
    assert b["status"] in ("ASSIGNED", "CONFIRMED")
    assert b["driver_id"]

    admin_token = _login("dispatch@velora.demo")
    accept = client.post(
        f"/api/v1/dispatch/respond/{b['id']}",
        json={"accept": True},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert accept.status_code == 200

    admin_token = _login("admin@velora.demo")
    current = client.get(f"/api/v1/bookings/{b['id']}").json()
    for status in ("ARRIVED", "IN_PROGRESS", "COMPLETED"):
        if current["status"] == status:
            continue
        tr = client.post(
            f"/api/v1/bookings/{b['id']}/transition",
            json={"status": status, "reason": "test"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert tr.status_code == 200, tr.text
        current = tr.json()

    final = client.get(f"/api/v1/bookings/{b['id']}").json()
    assert final["status"] == "COMPLETED"


def test_ops_dashboard_requires_permission():
    r = client.get("/api/v1/ops/dashboard")
    assert r.status_code == 401
    token = _login("admin@velora.demo")
    ok = client.get("/api/v1/ops/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert ok.status_code == 200
    assert "total_bookings" in ok.json()


def test_flight_fallback():
    r = client.get("/api/v1/flights/CI011")
    assert r.status_code == 200
    assert r.json()["flight_number"] == "CI011"


def test_unauthorized_ops_access():
    token = _login("emma@velora.demo")
    r = client.get("/api/v1/ops/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
