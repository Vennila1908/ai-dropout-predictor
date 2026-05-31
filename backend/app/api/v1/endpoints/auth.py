"""Auth endpoints — login, refresh, register, me."""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.core.security import create_token, decode_token
from app.models.user import User
from app.repositories.user_repo import user_repo
from app.schemas.auth import (
    AccessTokenOnly,
    ForgotPasswordIn,
    ForgotPasswordOut,
    LoginIn,
    RefreshIn,
    RegisterIn,
    ResetPasswordIn,
    TokenPair,
)
from app.schemas.user import UserOut
from app.services.auth_service import (
    authenticate,
    issue_password_reset_token,
    issue_tokens,
    register_user,
    reset_user_password,
    write_audit,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(request: Request, payload: RegisterIn = Body(...), db: Session = Depends(get_db)) -> UserOut:
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
def login(request: Request, payload: LoginIn = Body(...), db: Session = Depends(get_db)) -> TokenPair:
    user = authenticate(db, email=payload.email, password=payload.password)
    if not user:
        write_audit(db, user_id=None, action="auth.login.failed", entity="user", meta={"email": payload.email})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    tokens = issue_tokens(user)
    write_audit(db, user_id=user.id, action="auth.login.success", entity="user", entity_id=user.id, meta={})
    return TokenPair(**tokens, user=UserOut.model_validate(user))


@router.post("/forgot-password", response_model=ForgotPasswordOut, response_model_exclude_none=True)
def forgot_password(
    request: Request,
    payload: ForgotPasswordIn = Body(...),
    db: Session = Depends(get_db),
) -> ForgotPasswordOut:
    user = user_repo.get_by_email(db, payload.email)
    message = "If an active account uses that email, password reset instructions have been generated."
    if not user or not user.is_active:
        write_audit(db, user_id=None, action="auth.password_reset.requested", entity="user", meta={"email": payload.email})
        return ForgotPasswordOut(message=message)

    token = issue_password_reset_token(user)
    write_audit(db, user_id=user.id, action="auth.password_reset.requested", entity="user", entity_id=user.id, meta={})

    if not settings.debug:
        return ForgotPasswordOut(message=message)

    origin = request.headers.get("origin") or "http://localhost:5173"
    return ForgotPasswordOut(message=message, reset_token=token, reset_url=f"{origin}/forgot-password?token={token}")


@router.post("/reset-password")
def reset_password(payload: ResetPasswordIn = Body(...), db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        claims = decode_token(payload.token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token") from exc
    if claims.get("type") != "password_reset":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")
    sub = claims.get("sub")
    user = db.get(User, int(sub)) if sub else None
    if not user or not user.is_active or claims.get("pwd") != user.hashed_password[-16:]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

    reset_user_password(db, user=user, password=payload.password)
    write_audit(db, user_id=user.id, action="auth.password_reset.completed", entity="user", entity_id=user.id, meta={})
    return {"message": "Password has been reset. You can sign in with your new password."}


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
