"""User management endpoints — admin-only."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_admin, require_admin_or_faculty
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.repositories.student_repo import student_repo
from app.repositories.user_repo import user_repo
from app.schemas.user import UserCreate, UserOut, UserRollLookup, UserUpdate
from app.schemas.validators import ROLL_NO_PATTERN
from app.services.auth_service import write_audit


router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut], dependencies=[Depends(require_admin)])
def list_users(db: Session = Depends(get_db)) -> list[UserOut]:
    users = user_repo.list(db, offset=0, limit=500)
    return [UserOut.model_validate(u) for u in users]


@router.get("/lookup-by-roll", response_model=UserRollLookup, dependencies=[Depends(require_admin_or_faculty)])
def lookup_user_by_roll(
    roll_no: str = Query(min_length=1, max_length=40, pattern=ROLL_NO_PATTERN),
    db: Session = Depends(get_db),
) -> UserRollLookup:
    user = user_repo.get_by_roll_no(db, roll_no.strip())
    if not user or user.role != UserRole.student or not user.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No student login account found for this roll number")
    return UserRollLookup(roll_no=user.roll_no or roll_no.strip(), full_name=user.full_name, department_id=user.department_id)


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
def create_user(payload: UserCreate, db: Session = Depends(get_db), me: User = Depends(require_admin)) -> UserOut:
    if user_repo.get_by_email(db, payload.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    roll_no = payload.roll_no.strip() if payload.roll_no else None
    full_name = payload.full_name
    department_id = payload.department_id

    if payload.role == "student":
        if not roll_no:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Roll number is required for student accounts")
        if user_repo.get_by_roll_no(db, roll_no):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account already exists for this roll number")
        student = student_repo.get_by_roll_no(db, roll_no)
        if student:
            full_name = student.name
            department_id = student.department_id

    user = User(
        email=payload.email,
        full_name=full_name,
        hashed_password=hash_password(payload.password),
        role=UserRole(payload.role),
        roll_no=roll_no,
        department_id=department_id,
        is_active=payload.is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    write_audit(db, user_id=me.id, action="user.create", entity="user", entity_id=user.id, meta={"email": user.email})
    return UserOut.model_validate(user)


@router.patch("/{user_id:int}", response_model=UserOut)
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


@router.delete("/{user_id:int}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db), me: User = Depends(require_admin)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    db.commit()
    write_audit(db, user_id=me.id, action="user.deactivate", entity="user", entity_id=user.id, meta={})
    return None
