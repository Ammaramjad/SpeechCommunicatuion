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
| App (light) | `/app.html` |
| Account | `/account.html` |
| Driver | `/driver.html` |
| Admin / dispatch link | `/admin.html` |
| Help | `/help.html` |

Demo logins (password `demo`): `emma@velora.demo`, `driver@velora.demo`, `admin@velora.demo`

Promos: `VELORA10`, `AIRPORT200`, `NEWGUEST`

Speech-research code in this repository is unchanged. Older RideLook demos remain under `b2c-rides/`.
