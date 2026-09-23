"""Auth endpoints."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from mobility.api.deps import get_current_user, require_user
from mobility.api.v1.schemas import AuthLoginIn, AuthRegisterIn
from mobility.database import get_db
from mobility.models.auth import User
from mobility.services.auth_service import authenticate, register_user, user_permissions, user_to_dict

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
def register(body: AuthRegisterIn, db: Annotated[Session, Depends(get_db)]):
    try:
        user = register_user(db, body.email, body.password, body.name, body.phone or None)
        db.commit()
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    _, token = authenticate(db, body.email, body.password)
    perms = user_permissions(db, user)
    return {"token": token, "user": user_to_dict(user, perms)}


@router.post("/login")
def login(body: AuthLoginIn, db: Annotated[Session, Depends(get_db)]):
    try:
        user, token = authenticate(db, body.email, body.password)
    except ValueError:
        raise HTTPException(401, "Invalid credentials")
    perms = user_permissions(db, user)
    return {"token": token, "user": user_to_dict(user, perms)}


@router.get("/me")
def me(user: Annotated[User, Depends(require_user)], db: Annotated[Session, Depends(get_db)]):
    return user_to_dict(user, user_permissions(db, user))
