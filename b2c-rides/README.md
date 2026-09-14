# RideLook Taiwan — B2C + Fleet OS

Klook-style **transport-only** demo for Taiwan.

- Currency: **TWD (NT$)**
- Languages: **繁體中文** and **English**
- One backend for website, guest app, Fleet OS dispatch, and driver app

## Run

```bash
cd b2c-rides
pip install fastapi uvicorn
python3 server.py
```

Open http://127.0.0.1:4173

| Surface | URL | Role |
| --- | --- | --- |
| Hub | `/` | Pick a demo |
| Website | `/web.html` | Guest bookings (Klook-like) |
| App | `/app.html` | Guest phone bookings |
| Fleet OS | `/dispatch.html` | Live jobs, assign, phone book-in, GMV |
| Driver | `/driver.html` | Accept / arrive / complete |

Promo codes: `WELCOME`, `TPE200`, `FAMILY`. Night surcharge 20% between 23:00–06:00.

Facebook reel links could not be fetched here; UI follows Klook Taiwan (客路) orange marketplace + phone app patterns, plus a Fleet OS dispatch console.
