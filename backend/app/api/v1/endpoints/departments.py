"""Degree program (course) management — admin CRUD with delete guard."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_admin
from app.models.user import User
from app.schemas.department import DepartmentCreate, DepartmentOut, DepartmentUpdate
from app.services import department_service
from app.services.auth_service import write_audit


router = APIRouter(prefix="/departments", tags=["departments"])


@router.get("", response_model=list[DepartmentOut])
@router.get("/", response_model=list[DepartmentOut], include_in_schema=False)
def list_departments(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[DepartmentOut]:
    return [DepartmentOut.model_validate(row) for row in department_service.list_departments(db)]


@router.post("", response_model=DepartmentOut, status_code=status.HTTP_201_CREATED)
def create_department(
    payload: DepartmentCreate,
    db: Session = Depends(get_db),
    me: User = Depends(require_admin),
) -> DepartmentOut:
    try:
        dept = department_service.create_department(db, name=payload.name, code=payload.code)
    except department_service.DepartmentConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    write_audit(
        db,
        user_id=me.id,
        action="department.create",
        entity="department",
        entity_id=dept.id,
        meta={"code": dept.code, "name": dept.name},
    )
    return DepartmentOut.model_validate(department_service.department_to_dict(db, dept))


@router.patch("/{department_id}", response_model=DepartmentOut)
def update_department(
    department_id: int,
    payload: DepartmentUpdate,
    db: Session = Depends(get_db),
    me: User = Depends(require_admin),
) -> DepartmentOut:
    try:
        dept = department_service.update_department(
            db,
            department_id,
            name=payload.name,
            code=payload.code,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except department_service.DepartmentConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    write_audit(
        db,
        user_id=me.id,
        action="department.update",
        entity="department",
        entity_id=dept.id,
        meta={"code": dept.code, "name": dept.name},
    )
    return DepartmentOut.model_validate(department_service.department_to_dict(db, dept))


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_department(
    department_id: int,
    db: Session = Depends(get_db),
    me: User = Depends(require_admin),
):
    try:
        department_service.delete_department(db, department_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except department_service.DepartmentInUseError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    write_audit(
        db,
        user_id=me.id,
        action="department.delete",
        entity="department",
        entity_id=department_id,
        meta={},
    )
    return None
