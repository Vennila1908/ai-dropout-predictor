"""Student repository."""

from __future__ import annotations

from typing import Sequence

from sqlalchemy import asc, desc, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.prediction import Prediction
from app.models.student import Student
from app.repositories.base import CrudRepo


class StudentRepo(CrudRepo[Student]):
    def __init__(self) -> None:
        super().__init__(Student)

    def get_by_roll_no(self, db: Session, roll_no: str) -> Student | None:
        return db.execute(select(Student).where(Student.roll_no == roll_no)).scalar_one_or_none()

    def search(
        self,
        db: Session,
        *,
        q: str | None,
        department_id: int | None,
        risk: str | None,
        page: int,
        page_size: int,
        sort: str,
    ) -> tuple[Sequence[Student], int]:
        stmt = select(Student).options(joinedload(Student.department))
        filters = []
        if q:
            like = f"%{q.lower()}%"
            filters.append(or_(Student.name.ilike(like), Student.roll_no.ilike(like)))
        if department_id is not None:
            filters.append(Student.department_id == department_id)
        if risk:
            # Risk filter requires joining the latest prediction; we filter post-load below.
            pass
        for f in filters:
            stmt = stmt.where(f)

        order_attr = sort.lstrip("-")
        order_col = getattr(Student, order_attr, Student.created_at)
        stmt = stmt.order_by(desc(order_col) if sort.startswith("-") else asc(order_col))

        total = self.count(db, filters)
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        items = db.execute(stmt).unique().scalars().all()

        if risk:
            # Filter by latest prediction risk in Python — keeps the list query simple.
            filtered = []
            for s in items:
                latest = self.latest_prediction(db, s.id)
                if latest and latest.risk_level.value == risk:
                    filtered.append(s)
            items = filtered
            total = len(items)
        return items, total

    def latest_prediction(self, db: Session, student_id: int) -> Prediction | None:
        return db.execute(
            select(Prediction)
            .where(Prediction.student_id == student_id)
            .order_by(Prediction.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()


student_repo = StudentRepo()
