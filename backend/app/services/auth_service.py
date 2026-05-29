"""Authentication + token issuance + audit logging."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.security import create_token, hash_password, verify_password
from app.models.audit_log import AuditLog
from app.models.user import User, UserRole
from app.repositories.user_repo import user_repo


def authenticate(db: Session, *, email: str, password: str) -> User | None:
    """Return the user iff credentials are valid AND the account is active."""
    user = user_repo.get_by_email(db, email)
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def issue_tokens(user: User) -> dict[str, str]:
    return {
        "access_token": create_token(user.id, role=user.role.value, token_type="access"),
        "refresh_token": create_token(user.id, role=user.role.value, token_type="refresh"),
    }


def register_user(
    db: Session,
    *,
    email: str,
    password: str,
    full_name: str,
    role: str,
    department_id: int | None,
) -> User:
    user = User(
        email=email,
        full_name=full_name,
        hashed_password=hash_password(password),
        role=UserRole(role),
        department_id=department_id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def write_audit(
    db: Session,
    *,
    user_id: int | None,
    action: str,
    entity: str,
    entity_id: int | None = None,
    meta: dict[str, Any] | None = None,
) -> None:
    db.add(
        AuditLog(
            user_id=user_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            meta_json=meta or {},
        )
    )
    db.commit()
