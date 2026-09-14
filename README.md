# VELORA

Premium **private-car marketplace** with professional drivers. Original brand (not a Klook clone). Fleet operations attach to the existing Fleet Dispatch prototype rather than rebuilding it.

Fleet OS: https://fleet-dispatch-demo-8c37.surge.sh/

## Run

```bash
cd velora
pip install fastapi uvicorn
python3 server.py
```

Open http://127.0.0.1:4173

| Surface | Path |
| --- | --- |
| Customer website | `/` |
| Search results | `/results.html` |
| Checkout | `/ride.html` |
| App (Apple-style live map) | `/app.html` |
| Live tracking (web) | `/track.html?id=VR-…` |
| Account | `/account.html` |
| Driver | `/driver.html` |
| Admin / dispatch link | `/admin.html` |
| Help | `/help.html` |

Demo logins (password `demo`): `emma@velora.demo`, `driver@velora.demo`, `admin@velora.demo`

Promos: `VELORA10`, `AIRPORT200`, `NEWGUEST`

## Channel → Fleet OS sync

All bookings — VELORA web/app, Klook partner, phone desk, and external API — auto-sync into the Fleet OS dispatch queue (`fleet_jobs`).

| Endpoint | Purpose |
| --- | --- |
| `POST /api/channels/klook/orders` | Ingest Klook OTA orders (header `X-Partner-Key`) |
| `POST /api/channels/partner/orders` | Ingest any external OTA / corporate channel |
| `GET /api/fleet/jobs` | Fleet OS dispatch feed |
| `GET /api/admin/channels` | Channel metrics + recent sync queue |

Demo partner key: `velora-demo-partner-key`

Speech-research code in this repository is unchanged. Older RideLook demos remain under `b2c-rides/`.
