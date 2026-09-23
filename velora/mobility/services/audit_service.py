"""Audit logging service."""
from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy.orm import Session

from mobility.models.audit import AuditLog


def log_action(
    db: Session,
    *,
    actor_id: str | None,
    actor_email: str | None,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    before: Any = None,
    after: Any = None,
    ip_address: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    row = AuditLog(
        id=str(uuid.uuid4()),
        actor_id=actor_id,
        actor_email=actor_email,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_json=json.dumps(before) if before is not None else None,
        after_json=json.dumps(after) if after is not None else None,
        ip_address=ip_address,
        metadata_json=json.dumps(metadata) if metadata else None,
    )
    db.add(row)
    db.flush()
    return row
