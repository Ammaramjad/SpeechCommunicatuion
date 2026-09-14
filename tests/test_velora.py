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


def test_roundtrip_doubles_total():
    one = client.post("/api/quote", json={"pickup_id": "tpe", "dest_id": "taipei-101", "class_id": "standard", "when": "2026-09-16T10:00"}).json()
    two = client.post("/api/quote", json={"pickup_id": "tpe", "dest_id": "taipei-101", "class_id": "standard", "when": "2026-09-16T10:00", "roundtrip": True}).json()
    assert abs(two["breakdown"]["total"] - one["breakdown"]["total"] * 2) <= 2


def test_stop_increases_price():
    base = client.post("/api/quote", json={"pickup_id": "tpe", "dest_id": "taipei-101", "class_id": "standard"}).json()
    stop = client.post("/api/quote", json={"pickup_id": "tpe", "dest_id": "taipei-101", "class_id": "standard", "stops": ["ximen"]}).json()
    assert stop["breakdown"]["total"] > base["breakdown"]["total"]


def test_live_flight_incident_and_review():
    b = client.post("/api/bookings", json={
        "pickup_id": "tpe", "dest_id": "taipei-101", "when": "2026-09-16T10:00",
        "first": "Ada", "last": "Lovelace", "email": "ada@example.com", "phone": "+1",
        "class_id": "business", "terms": True, "flight": "CI011", "track_flight": True, "channel": "app",
    }).json()
    bid = b["id"]
    assert b["driver"]["first"]
    live = client.get(f"/api/bookings/{bid}/live").json()
    assert live["live"]["driver_pos"]["lat"]
    assert live["live"]["eta_min"] >= 0
    fl = client.post(f"/api/bookings/{bid}/ops", json={"kind": "flight_sync", "note": "CI011"}).json()
    assert fl["flight_delay_min"] >= 0
    assert any(a["type"] == "flight" for a in fl["alerts"])
    late = client.post(f"/api/bookings/{bid}/ops", json={"kind": "passenger_late", "minutes": 10}).json()
    assert late["passenger_late_min"] >= 10
    inc = client.post(f"/api/bookings/{bid}/ops", json={"kind": "incident", "note": "collision"}).json()
    assert inc["replacement"]["first"]
    assert inc["driver"]["id"] != b["driver"]["id"]
    rv = client.post(f"/api/bookings/{bid}/review", json={"driver": 5, "text": "Safe swap", "name": "Ada"}).json()
    assert rv["verified"] is True
    assert "Safe swap" in rv["text"]


def test_driver_profile():
    p = client.get("/api/drivers/d01/profile").json()
    assert p["first"] == "Wei"
    assert p["rating"] >= 4.8
    assert "reviews" in p


def test_manifest_served():
    r = client.get("/manifest.json")
    assert r.status_code == 200
    assert "VELORA" in r.text


def test_login_and_fleet_os_attached():
    auth = client.post("/api/auth/login", json={"email": "admin@velora.demo", "password": "demo"}).json()
    assert auth["user"]["role"] == "admin"
    meta = client.get("/api/meta").json()
    assert "fleet-dispatch-demo-8c37.surge.sh" in meta["fleet_os"]
    metrics = client.get("/api/admin/metrics").json()
    assert "fleet_os" in metrics


def test_velora_booking_syncs_to_fleet_os():
    b = client.post("/api/bookings", json={
        "pickup_id": "tpe", "dest_id": "taipei-101", "when": "2026-09-16T10:00",
        "first": "Ada", "last": "Lovelace", "email": "ada@example.com", "phone": "+1",
        "class_id": "business", "terms": True, "channel": "velora",
    }).json()
    assert b["fleet_job_id"].startswith("FO-")
    jobs = client.get("/api/fleet/jobs").json()
    assert any(j["booking_id"] == b["id"] and j["channel"] == "velora" for j in jobs)


def test_klook_order_ingest_and_fleet_sync():
    payload = {
        "external_id": "KL-998877",
        "pickup_name": "Taoyuan International Airport (TPE)",
        "dest_name": "Taipei 101 / Xinyi",
        "when": "2026-09-17T14:00",
        "first": "Klook", "last": "Guest", "email": "guest@klook.demo", "phone": "+886900000001",
        "class_id": "standard", "flight": "CI011", "track_flight": True,
    }
    r = client.post("/api/channels/klook/orders", json=payload, headers={"X-Partner-Key": "velora-demo-partner-key"})
    assert r.status_code == 200
    body = r.json()
    assert body["booking"]["channel"] == "klook"
    assert body["booking"]["external_id"] == "KL-998877"
    assert body["fleet_job"]["channel"] == "klook"
    ch = client.get("/api/admin/channels").json()
    assert ch["bookings_by_channel"].get("klook", 0) >= 1


def test_catalog_has_discovery_sections():
    cat = client.get("/api/catalog").json()
    assert cat["destinations"]
    assert cat["favorites"]
    assert cat["service_tabs"]
    assert cat["promo_shelf"]
