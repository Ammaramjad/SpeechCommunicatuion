from fastapi.testclient import TestClient
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "velora"))
from server import app, save, empty_store

client = TestClient(app)


def setup_function():
    save(empty_store())


def test_search_returns_classes_and_twd_total():
    r = client.post("/api/search", json={"pickup_id": "tpe", "dest_id": "taipei-101", "when": "2026-09-16T10:00", "pax": 2, "bags": 2})
    assert r.status_code == 200
    body = r.json()
    assert body["count"] >= 5
    assert body["results"][0]["price"]["currency"] == "TWD"
    assert body["results"][0]["price"]["breakdown"]["total"] > 0


def test_guest_booking_and_retrieve():
    b = client.post("/api/bookings", json={
        "pickup_id": "tpe", "dest_id": "taipei-101", "when": "2026-09-16T10:00",
        "first": "Ada", "last": "Lovelace", "email": "ada@example.com", "phone": "+1",
        "class_id": "business", "terms": True, "pax": 2, "bags": 2,
    })
    assert b.status_code == 200
    bid = b.json()["id"]
    assert bid.startswith("VR-")
    got = client.get(f"/api/bookings/{bid}").json()
    assert got["email"] == "ada@example.com"
    assert got["quote"]["breakdown"]["total"] > 0


def test_login_and_fleet_os_attached():
    auth = client.post("/api/auth/login", json={"email": "admin@velora.demo", "password": "demo"}).json()
    assert auth["user"]["role"] == "admin"
    meta = client.get("/api/meta").json()
    assert "fleet-dispatch-demo-8c37.surge.sh" in meta["fleet_os"]
    metrics = client.get("/api/admin/metrics").json()
    assert "fleet_os" in metrics
