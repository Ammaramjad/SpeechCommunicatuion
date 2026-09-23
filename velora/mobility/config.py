"""Platform configuration — env-driven, no secrets in code."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)


class Settings:
    app_name: str = "B2C International Mobility Platform"
    database_url: str = os.getenv(
        "MOBILITY_DATABASE_URL",
        f"sqlite:///{DATA / 'mobility.db'}",
    )
    jwt_secret: str = os.getenv("MOBILITY_JWT_SECRET", "change-me-in-production-use-env")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = int(os.getenv("MOBILITY_JWT_EXPIRE_MIN", "1440"))
    partner_webhook_key: str = os.getenv("MOBILITY_PARTNER_KEY", "velora-demo-partner-key")
    default_timezone: str = "UTC"
    default_currency: str = "TWD"
    airport_free_wait_minutes: int = int(os.getenv("MOBILITY_AIRPORT_WAIT_MIN", "60"))
    otp_expire_minutes: int = 10
    otp_max_attempts: int = 5
    dispatch_timeout_seconds: int = 90
    stripe_secret_key: str = os.getenv("STRIPE_SECRET_KEY", "")
    stripe_webhook_secret: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    flight_api_key: str = os.getenv("FLIGHT_API_KEY", "")


@lru_cache
def get_settings() -> Settings:
    return Settings()
