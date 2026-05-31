"""Password hashing + JWT helpers.

Uses passlib[bcrypt] for hashing and python-jose for JWT.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TokenType = Literal["access", "refresh", "password_reset"]


def hash_password(plain: str) -> str:
    """Return a bcrypt hash for `plain`."""
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Constant-time compare of a plaintext to a stored bcrypt hash."""
    try:
        return _pwd_context.verify(plain, hashed)
    except Exception:
        return False


def _expiry_for(token_type: TokenType) -> timedelta:
    if token_type == "refresh":
        return timedelta(minutes=settings.refresh_token_expire_minutes)
    if token_type == "password_reset":
        return timedelta(minutes=settings.password_reset_token_expire_minutes)
    return timedelta(minutes=settings.access_token_expire_minutes)


def create_token(
    subject: str | int,
    *,
    role: str,
    token_type: TokenType = "access",
    extra: dict[str, Any] | None = None,
) -> str:
    """Mint a signed JWT.

    Parameters
    ----------
    subject : the user id (stored as `sub`).
    role    : the user role (stored as `role`); used by RoleGate.
    token_type : "access" or "refresh".
    extra   : optional extra claims merged into the payload.
    """
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + _expiry_for(token_type)).timestamp()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict[str, Any]:
    """Decode + validate a JWT, raising :class:`ValueError` on failure."""
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError as exc:
        raise ValueError(f"invalid token: {exc}") from exc
