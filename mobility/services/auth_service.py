"""Authentication service."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from mobility.auth import create_access_token, hash_password, verify_password
from mobility.models.auth import Role, User


def register_user(db: Session, email: str, password: str, name: str, phone: str | None = None) -> User:
    existing = db.query(User).filter(User.email == email.lower()).first()
    if existing:
        raise ValueError("Email already registered")
    user = User(
        id=str(uuid.uuid4()),
        email=email.lower(),
        password_hash=hash_password(password),
        name=name,
        phone=phone,
    )
    role = db.query(Role).filter(Role.code == "CUSTOMER").first()
    if role:
        user.roles.append(role)
    db.add(user)
    db.flush()
    return user


def authenticate(db: Session, email: str, password: str) -> tuple[User, str]:
    user = db.query(User).filter(User.email == email.lower(), User.is_active.is_(True)).first()
    if not user or not verify_password(password, user.password_hash):
        raise ValueError("Invalid credentials")
    token = create_access_token(user.id, {"email": user.email})
    return user, token


def user_permissions(db: Session, user: User) -> set[str]:
    perms: set[str] = set()
    for role in user.roles:
        for perm in role.permissions:
            perms.add(perm.code)
    return perms


def user_to_dict(user: User, permissions: set[str] | None = None) -> dict[str, Any]:
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "phone": user.phone,
        "preferred_language": user.preferred_language,
        "preferred_currency": user.preferred_currency,
        "roles": [r.code for r in user.roles],
        "permissions": sorted(permissions or []),
    }
