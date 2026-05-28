"""Degree program (department) management."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.department import Department
from app.repositories.department_repo import department_repo


class DepartmentConflictError(ValueError):
    pass


class DepartmentInUseError(ValueError):
    pass


def _normalize_code(code: str) -> str:
    return code.strip().upper()


def list_departments(db: Session) -> list[dict]:
    rows: list[dict] = []
    for dept in department_repo.list_ordered(db):
        rows.append(department_to_dict(db, dept))
    return rows


def department_to_dict(db: Session, dept: Department) -> dict:
    return {
        "id": dept.id,
        "name": dept.name,
        "code": dept.code,
        "student_count": department_repo.student_count(db, dept.id),
        "created_at": dept.created_at,
    }


def create_department(db: Session, *, name: str, code: str) -> Department:
    name = name.strip()
    code = _normalize_code(code)
    if department_repo.get_by_code(db, code):
        raise DepartmentConflictError(f"Course code '{code}' is already in use")
    if department_repo.get_by_name(db, name):
        raise DepartmentConflictError(f"Course name '{name}' is already in use")
    dept = Department(name=name, code=code)
    department_repo.add(db, dept)
    db.commit()
    db.refresh(dept)
    return dept


def update_department(db: Session, department_id: int, *, name: str | None = None, code: str | None = None) -> Department:
    dept = department_repo.get(db, department_id)
    if not dept:
        raise LookupError("Course not found")
    if name is not None:
        name = name.strip()
        existing = department_repo.get_by_name(db, name)
        if existing and existing.id != dept.id:
            raise DepartmentConflictError(f"Course name '{name}' is already in use")
        dept.name = name
    if code is not None:
        code = _normalize_code(code)
        existing = department_repo.get_by_code(db, code)
        if existing and existing.id != dept.id:
            raise DepartmentConflictError(f"Course code '{code}' is already in use")
        dept.code = code
    db.commit()
    db.refresh(dept)
    return dept


def delete_department(db: Session, department_id: int) -> None:
    dept = department_repo.get(db, department_id)
    if not dept:
        raise LookupError("Course not found")
    count = department_repo.student_count(db, department_id)
    if count >= 1:
        raise DepartmentInUseError(f"Cannot delete — {count} student(s) are enrolled in this course")
    department_repo.delete(db, dept)
    db.commit()
