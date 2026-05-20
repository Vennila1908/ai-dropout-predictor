"""Auth endpoints — login, refresh, register, me."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.core.rate_limit import limiter
from app.core.security import create_token, decode_token
from app.models.user import User
from app.repositories.user_repo import user_repo
from app.schemas.auth import AccessTokenOnly, LoginIn, RefreshIn, RegisterIn, TokenPair
from app.schemas.user import UserOut
from app.services.auth_service import authenticate, issue_tokens, register_user, write_audit


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterIn, request: Request, db: Session = Depends(get_db)) -> UserOut:
    """Register a user.

    * If the users table is empty → bootstrap allowed without auth (first admin).
    * Otherwise → must already be admin (handled by the dedicated /users endpoint).
    """
    user_count = user_repo.count_total(db)
    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bootstrap already complete; use /users (admin) to create users.",
        )
    if user_repo.get_by_email(db, payload.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = register_user(
        db,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        role=payload.role or "admin",  # bootstrap user is admin by default
        department_id=payload.department_id,
    )
    write_audit(db, user_id=user.id, action="auth.register", entity="user", entity_id=user.id, meta={})
    return UserOut.model_validate(user)


@router.post("/login", response_model=TokenPair)
@limiter.limit(settings.rate_limit_login)
def login(payload: LoginIn, request: Request, db: Session = Depends(get_db)) -> TokenPair:
    user = authenticate(db, email=payload.email, password=payload.password)
    if not user:
        write_audit(db, user_id=None, action="auth.login.failed", entity="user", meta={"email": payload.email})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    tokens = issue_tokens(user)
    write_audit(db, user_id=user.id, action="auth.login.success", entity="user", entity_id=user.id, meta={})
    return TokenPair(**tokens, user=UserOut.model_validate(user))


@router.post("/refresh", response_model=AccessTokenOnly)
def refresh(payload: RefreshIn, db: Session = Depends(get_db)) -> AccessTokenOnly:
    try:
        claims = decode_token(payload.refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    if claims.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong token type")
    sub = claims.get("sub")
    user = db.get(User, int(sub)) if sub else None
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return AccessTokenOnly(access_token=create_token(user.id, role=user.role.value, token_type="access"))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)
