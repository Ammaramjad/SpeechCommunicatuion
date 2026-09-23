# B2C International Mobility Platform — Architecture Assessment

## A. Existing Architecture Assessment

| Layer | Current state | Verdict |
|-------|---------------|---------|
| **Product** | `velora/` — FastAPI + vanilla JS multi-page app | **Extend** as primary product |
| **Legacy demo** | `b2c-rides/` — Taiwan RideLook + Fleet OS UI | Reference only; link external Fleet OS |
| **Research** | `mr_avt/`, `train.py`, `data/demo/` | **Protected — do not modify** |
| **Persistence** | JSON `store.json` (thread-locked) | **Replace** with SQLAlchemy + PostgreSQL/SQLite |
| **Auth** | SHA256 passwords, Bearer tokens in JSON, RBAC defined but not enforced | **Replace** bcrypt + JWT + enforced permissions |
| **Payments** | Always `paid`; UI labels only | **Build** provider abstraction |
| **Live tracking** | Interpolated positions | **Build** WebSocket + real location store |
| **Flights** | Hash-based mock | **Build** provider abstraction + fallback |
| **Frontend** | Mobile-friendly VELORA dark UI, 6 languages in JS | **Extend** 3-step booking + i18n files |
| **Deploy** | Render, GitHub Pages, Surge | **Keep**; add DB + secrets for production |

## B. Reusable Modules

- VELORA search → quote → book → track UX flows
- `catalog.py` vehicle classes, locations, fixed routes (seed into DB)
- Booking ops: flight sync, incident, driver swap, late passenger/driver
- Channel ingest (Klook/partner) → Fleet OS job queue pattern
- `b2c-rides/dispatch.js` ITRI scoring concept for Dispatch 2.0
- `tests/test_velora.py` API regression baseline
- Admin/ops HTML shell

## C. Missing Modules (Phase 1 MVP)

- Relational DB + migrations
- Canonical booking entity with subtype fields (not duplicate tables per service)
- Enforced RBAC + audit log
- Pricing rules in DB (not hard-coded)
- Payment authorize/capture/refund with idempotency
- Dispatch engine with accept/reject/timeout
- Flight provider abstraction
- WebSocket live trips
- OTP boarding verification (structured)
- Configurable cancellation policies

## D. Target Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Customer Web/App  │  Driver Portal  │  Ops/Admin Console   │
└────────────┬────────────────┬─────────────────┬──────────────┘
             │                │                 │
        /api/v1/*       /api/v1/driver/*   /api/v1/ops/*
             │                │                 │
┌────────────▼────────────────▼─────────────────▼──────────────┐
│  FastAPI — velora/server.py + platform/api/v1                 │
│  Middleware: auth, RBAC, rate limit, audit                    │
└────────────┬─────────────────────────────────────────────────┘
             │
┌────────────▼─────────────────────────────────────────────────┐
│  Services: Booking, Pricing, Dispatch, Payment, Flight,     │
│            Notification, StateMachine, Wallet (phase 2)      │
└────────────┬─────────────────────────────────────────────────┘
             │
┌────────────▼─────────────────────────────────────────────────┐
│  SQLAlchemy ORM — PostgreSQL (prod) / SQLite (dev)            │
└─────────────────────────────────────────────────────────────┘
```

Legacy `/api/*` endpoints remain for backward compatibility during migration.

## E. Database Changes

New schema under `velora/platform/models/`. Key tables:

- `users`, `roles`, `permissions`, `role_permissions`, `user_roles`
- `customers`, `passengers`
- `drivers`, `driver_documents`, `vehicles`, `vehicle_types`, `fleets`, `partners`
- `bookings` (canonical), `booking_stops`, `booking_addons`, `booking_passengers`
- `booking_status_history`, `quotes`, `pricing_rules`, `pricing_components`
- `dispatches`, `dispatch_attempts`, `driver_locations`
- `payments`, `payment_transactions`, `refunds`
- `flights`, `flight_events`
- `cancellation_policies`, `coupons`
- `audit_logs`, `analytics_events`
- `system_settings` (owner-configurable business rules)

## F. API Changes

Versioned REST:

- `POST /api/v1/auth/register`, `/login`, `/refresh`
- `POST /api/v1/pricing/quote`
- `POST /api/v1/bookings`, `GET /api/v1/bookings/{id}`
- `POST /api/v1/bookings/{id}/transition`
- `POST /api/v1/dispatch/assign`, `/accept`, `/reject`
- `POST /api/v1/payments/intent`, `/capture`, `/refund`
- `GET /api/v1/flights/{number}`
- `GET /api/v1/ops/bookings`, `/ops/dashboard`
- WebSocket: `/api/v1/ws/trips/{id}` (phase 1 stub → phase 2 full)

## G. Frontend Changes

- New `book.html` — mobile-first 3-step flow wired to `/api/v1`
- Extend `admin.html` → ops console with live booking list + manual assign
- i18n JSON files under `assets/i18n/` (extract from `core.js`)
- Driver portal wired to dispatch accept/reject

## H. Security / RBAC

| Role | booking.create | dispatch.manual | pricing.manage | payment.refund |
|------|----------------|-----------------|----------------|----------------|
| CUSTOMER | ✓ | | | |
| DRIVER | | | | |
| DISPATCHER | ✓ | ✓ | | |
| OPS_MANAGER | ✓ | ✓ | | ✓ |
| FINANCE | | | | ✓ |
| ADMIN | ✓ | ✓ | ✓ | ✓ |
| SUPER_ADMIN | all | all | all | all |

All `/api/v1/ops/*` and `/api/v1/admin/*` require permission checks + audit.

## I. Phase 1 Implementation Order

1. Canonical booking model + migrations ✓ (this PR)
2. Auth/RBAC ✓
3. Three-step booking UI ✓
4. Vehicle capacity matching ✓
5. Pricing engine 1.0 ✓
6. Payment gateway abstraction ✓
7. Dispatch 1.0 ✓
8. Driver acceptance ✓
9. Basic flight tracking ✓
10. Operations console 1.0 ✓

## J. Risks / Dependencies

- **Scope:** Full spec = 11+ months; MVP focuses on unified booking + real DB + RBAC
- **JSON migration:** Dual-write period; legacy `/api/bookings` delegates to v1 where possible
- **Payments:** Stripe test mode for MVP; never store PAN
- **Maps:** Continue OpenStreetMap/Leaflet; Google Places optional later
- **Fleet OS:** Keep external iframe; sync via `fleet_jobs`

## K. Implementation Checklist

- [x] Architecture document
- [x] SQLAlchemy schema + `create_all` (Alembic planned)
- [x] Seed roles, permissions, pricing rules, vehicle types
- [x] Auth register/login with JWT + bcrypt
- [x] POST /api/v1/pricing/quote (itemized)
- [x] POST /api/v1/bookings (capacity check, state machine)
- [x] Payment intent + capture + refund abstraction
- [x] Dispatch assign + driver accept/reject
- [x] Flight provider with fallback
- [x] book.html 3-step mobile UI
- [x] Ops dashboard v1 (`/api/v1/ops/*`)
- [x] Audit log on admin actions
- [x] Integration tests (full booking lifecycle)
- [x] Legacy `/api/*` compatibility preserved
