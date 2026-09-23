"""FastAPI dependencies."""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from mobility.auth import decode_access_token
from mobility.database import get_db
from mobility.models.auth import User
from mobility.services.auth_service import user_permissions

security = HTTPBearer(auto_error=False)


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> User | None:
    if not creds:
        return None
    try:
        payload = decode_access_token(creds.credentials)
    except ValueError:
        raise HTTPException(401, "Invalid token")
    user = db.get(User, payload["sub"])
    if not user or not user.is_active:
        raise HTTPException(401, "User not found")
    return user


def require_user(user: Annotated[User | None, Depends(get_current_user)]) -> User:
    if not user:
        raise HTTPException(401, "Authentication required")
    return user


def require_permission(permission: str):
    def checker(
        db: Annotated[Session, Depends(get_db)],
        user: Annotated[User, Depends(require_user)],
    ) -> User:
        perms = user_permissions(db, user)
        if permission not in perms and "SUPER_ADMIN" not in {r.code for r in user.roles}:
            raise HTTPException(403, f"Missing permission: {permission}")
        return user

    return checker


def client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None
