"""RBAC permission definitions."""
from __future__ import annotations

PERMISSIONS: list[tuple[str, str]] = [
    ("booking.view", "View bookings"),
    ("booking.create", "Create bookings"),
    ("booking.modify", "Modify bookings"),
    ("booking.cancel", "Cancel bookings"),
    ("booking.refund", "Refund bookings"),
    ("booking.assign", "Assign bookings"),
    ("driver.approve", "Approve drivers"),
    ("driver.suspend", "Suspend drivers"),
    ("dispatch.manual", "Manual dispatch"),
    ("dispatch.override", "Override dispatch"),
    ("pricing.manage", "Manage pricing"),
    ("payment.refund", "Process refunds"),
    ("settlement.manage", "Manage settlements"),
    ("customer.manage", "Manage customers"),
    ("complaint.manage", "Manage complaints"),
    ("analytics.view", "View analytics"),
    ("system.configure", "Configure system"),
]

ROLE_PERMISSIONS: dict[str, list[str]] = {
    "CUSTOMER": ["booking.view", "booking.create", "booking.cancel"],
    "DRIVER": ["booking.view"],
    "DISPATCHER": ["booking.view", "booking.create", "booking.modify", "booking.assign", "dispatch.manual"],
    "CUSTOMER_SERVICE": ["booking.view", "booking.modify", "booking.cancel", "complaint.manage", "customer.manage"],
    "OPERATIONS_MANAGER": [
        "booking.view", "booking.create", "booking.modify", "booking.cancel", "booking.assign",
        "booking.refund", "dispatch.manual", "dispatch.override", "payment.refund", "complaint.manage",
        "analytics.view",
    ],
    "FINANCE": ["booking.view", "payment.refund", "settlement.manage", "analytics.view"],
    "FLEET_MANAGER": ["booking.view", "driver.approve", "driver.suspend", "dispatch.manual"],
    "PARTNER": ["booking.view", "booking.create"],
    "ADMIN": [
        "booking.view", "booking.create", "booking.modify", "booking.cancel", "booking.refund",
        "booking.assign", "driver.approve", "driver.suspend", "dispatch.manual", "dispatch.override",
        "pricing.manage", "payment.refund", "settlement.manage", "customer.manage", "complaint.manage",
        "analytics.view", "system.configure",
    ],
    "SUPER_ADMIN": [p[0] for p in PERMISSIONS],
}
