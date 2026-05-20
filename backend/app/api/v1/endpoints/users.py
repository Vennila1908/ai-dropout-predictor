"""User management endpoints — admin-only."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_admin
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.repositories.user_repo import user_repo
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.services.auth_service import write_audit


router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(require_admin)])


@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)) -> list[UserOut]:
    users = user_repo.list(db, offset=0, limit=500)
    return [UserOut.model_validate(u) for u in users]


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db), me: User = Depends(require_admin)) -> UserOut:
    if user_repo.get_by_email(db, payload.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=UserRole(payload.role),
        department_id=payload.department_id,
        is_active=payload.is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    write_audit(db, user_id=me.id, action="user.create", entity="user", entity_id=user.id, meta={"email": user.email})
    return UserOut.model_validate(user)


@router.patch("/{user_id}", response_model=UserOut)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db), me: User = Depends(require_admin)) -> UserOut:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    data = payload.model_dump(exclude_unset=True)
    if "password" in data and data["password"]:
        user.hashed_password = hash_password(data.pop("password"))
    if "role" in data and data["role"] is not None:
        user.role = UserRole(data.pop("role"))
    for k, v in data.items():
        setattr(user, k, v)
    db.commit()
    db.refresh(user)
    write_audit(db, user_id=me.id, action="user.update", entity="user", entity_id=user.id, meta={})
    return UserOut.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db), me: User = Depends(require_admin)) -> None:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    db.commit()
    write_audit(db, user_id=me.id, action="user.deactivate", entity="user", entity_id=user.id, meta={})
