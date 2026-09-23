"""ORM models for the mobility platform."""
from mobility.models.audit import AuditLog
from mobility.models.auth import Permission, Role, User, role_permissions, user_roles
from mobility.models.booking import (
    Booking,
    BookingAddon,
    BookingPassenger,
    BookingStatusHistory,
    BookingStop,
    Quote,
)
from mobility.models.fleet import Driver, Location, Vehicle, VehicleType
from mobility.models.flight import Flight, FlightEvent
from mobility.models.payment import Payment, PaymentTransaction, Refund
from mobility.models.pricing import Addon, CancellationPolicy, PricingRule
from mobility.models.dispatch import Dispatch, DispatchAttempt


def load_all_models() -> None:
    """Import all models so metadata is registered."""
    return None


__all__ = [
    "AuditLog",
    "Permission",
    "Role",
    "User",
    "role_permissions",
    "user_roles",
    "Booking",
    "BookingAddon",
    "BookingPassenger",
    "BookingStatusHistory",
    "BookingStop",
    "Quote",
    "Driver",
    "Location",
    "Vehicle",
    "VehicleType",
    "Flight",
    "FlightEvent",
    "Payment",
    "PaymentTransaction",
    "Refund",
    "Addon",
    "CancellationPolicy",
    "PricingRule",
    "Dispatch",
    "DispatchAttempt",
    "load_all_models",
]
