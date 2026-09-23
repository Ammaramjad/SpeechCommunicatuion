"""Controlled booking state transitions."""
from __future__ import annotations

BOOKING_TRANSITIONS: dict[str, set[str]] = {
    "DRAFT": {"CONFIRMED", "CANCELLED", "FAILED"},
    "CONFIRMED": {"ASSIGNED", "CANCELLED", "REFUND_PENDING", "FAILED"},
    "ASSIGNED": {"EN_ROUTE", "CANCELLED", "REFUND_PENDING", "NO_SHOW"},
    "EN_ROUTE": {"ARRIVED", "CANCELLED", "NO_SHOW"},
    "ARRIVED": {"IN_PROGRESS", "NO_SHOW", "CANCELLED"},
    "IN_PROGRESS": {"COMPLETED", "CANCELLED"},
    "COMPLETED": set(),
    "CANCELLED": {"REFUND_PENDING"},
    "REFUND_PENDING": {"REFUNDED"},
    "REFUNDED": set(),
    "FAILED": set(),
    "NO_SHOW": {"REFUND_PENDING"},
}

PAYMENT_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"authorized", "failed", "cancelled"},
    "authorized": {"captured", "failed", "cancelled", "refund_pending"},
    "captured": {"refund_pending"},
    "refund_pending": {"refunded", "partially_refunded"},
    "refunded": set(),
    "partially_refunded": {"refund_pending"},
    "failed": set(),
    "cancelled": set(),
}

DISPATCH_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"searching", "assigned", "failed"},
    "searching": {"assigned", "failed", "timeout"},
    "assigned": {"accepted", "rejected", "timeout", "cancelled"},
    "accepted": {"completed", "cancelled"},
    "rejected": {"searching", "failed"},
    "timeout": {"searching", "failed"},
    "completed": set(),
    "failed": set(),
    "cancelled": set(),
}


def can_transition(current: str, new: str, machine: dict[str, set[str]]) -> bool:
    return new in machine.get(current, set())


def assert_booking_transition(current: str, new: str) -> None:
    if not can_transition(current, new, BOOKING_TRANSITIONS):
        raise ValueError(f"Invalid booking transition: {current} -> {new}")
