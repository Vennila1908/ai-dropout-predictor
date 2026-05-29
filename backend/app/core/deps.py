"""FastAPI dependency helpers: DB sessions, auth, role gates."""

from __future__ import annotations

from collections.abc import Generator
from typing import Iterable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import SessionLocal
from app.models.user import User, UserRole


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_db() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session and ensure it is always closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the user from a Bearer token. Raises 401 if missing/invalid."""
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong token type")

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing subject")

    user = db.get(User, int(sub))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    request.state.user = user  # used by rate-limiter key fn
    return user


def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return user


class RoleGate:
    """FastAPI dependency that allows access only to listed roles.

    Usage::

        @router.get("/admin/...", dependencies=[Depends(RoleGate({"admin"}))])
    """

    def __init__(self, allowed: Iterable[str | UserRole]) -> None:
        self.allowed = {UserRole(r) if not isinstance(r, UserRole) else r for r in allowed}

    def __call__(self, user: User = Depends(get_current_user)) -> User:
        if user.role not in self.allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {sorted(r.value for r in self.allowed)}",
            )
        return user


# Convenient pre-built gates.
require_admin = RoleGate({UserRole.admin})
require_admin_or_faculty = RoleGate({UserRole.admin, UserRole.faculty})
