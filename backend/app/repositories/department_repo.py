"""Department (degree program) repository."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.student import Student
from app.repositories.base import CrudRepo


class DepartmentRepo(CrudRepo[Department]):
    def __init__(self) -> None:
        super().__init__(Department)

    def get_by_code(self, db: Session, code: str) -> Department | None:
        normalized = code.strip().upper()
        return db.execute(select(Department).where(func.upper(Department.code) == normalized)).scalar_one_or_none()

    def get_by_name(self, db: Session, name: str) -> Department | None:
        return db.execute(select(Department).where(Department.name == name.strip())).scalar_one_or_none()

    def student_count(self, db: Session, department_id: int) -> int:
        return int(
            db.execute(select(func.count()).select_from(Student).where(Student.department_id == department_id)).scalar_one()
            or 0
        )

    def list_ordered(self, db: Session) -> list[Department]:
        return list(db.execute(select(Department).order_by(Department.name)).scalars().all())


department_repo = DepartmentRepo()
