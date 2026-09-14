from fastapi.testclient import TestClient
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "b2c-rides"))
from server import app, save, empty_store

client = TestClient(app)


def setup_function():
    save(empty_store())


def test_quote_twd_and_promo():
    r = client.post("/api/quote", json={"vehicle_id": "sedan", "promo": "TPE200", "when": "2026-09-15T10:00"})
    assert r.status_code == 200
    body = r.json()
    assert body["currency"] == "TWD"
    assert body["fare"]["discount"] == 200
    assert body["fare"]["total"] == 1280 + 150 - 200  # meet default True


def test_web_and_app_bookings_share_backend():
    w = client.post("/api/bookings", json={"channel": "web", "vehicle_id": "sedan", "from_id": "tpe", "to_id": "xinyi", "when": "2026-09-15T10:00"})
    a = client.post("/api/bookings", json={"channel": "app", "type": "instant", "vehicle_id": "taxi", "from_id": "xinyi", "to_id": "ximen", "when": "2026-09-15T11:00", "meet": False})
    assert w.status_code == 200 and a.status_code == 200
    jobs = client.get("/api/bookings").json()
    channels = {j["channel"] for j in jobs}
    assert "web" in channels and "app" in channels
    summary = client.get("/api/fleet/summary").json()
    assert summary["channels"]["web"] >= 1
    assert summary["channels"]["app"] >= 1
def test_live_cards_cancel_and_itri_autodispatch():
    live = client.get("/api/live/marketplace").json()
    assert live["cards"]
    assert live["cards"][0]["live_price"] >= live["cards"][0]["from_price"]
    jobs = client.get("/api/bookings").json()
    newbie = next(j for j in jobs if j["status"] == "new")
    c = client.post(f"/api/bookings/{newbie['id']}/cancel")
    assert c.status_code == 200
    assert c.json()["status"] == "cancelled"
    auto = client.post("/api/fleet/auto-dispatch").json()
    assert auto["engine"].startswith("ITRI")
    board = client.get("/api/fleet/itri").json()
    assert "OSRM" in board["map_engines"]
