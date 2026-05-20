"""Student business logic on top of the repository."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.prediction import Prediction
from app.models.student import FinancialStatus, PlacementReadiness, Student
from app.repositories.student_repo import student_repo
from app.schemas.student import StudentCreate, StudentUpdate


def _hydrate(db: Session, student: Student) -> dict[str, Any]:
    """Pack a Student + its latest prediction + department into a dict for response."""
    base = {
        c.name: getattr(student, c.name) for c in Student.__table__.columns
    }
    base["department_code"] = student.department.code if student.department else None
    base["department_name"] = student.department.name if student.department else None
    latest: Prediction | None = student_repo.latest_prediction(db, student.id)
    base["latest_risk"] = latest.risk_level.value if latest else None
    base["latest_confidence"] = float(latest.confidence) if latest else None
    return base


def get_student(db: Session, student_id: int) -> dict[str, Any] | None:
    s = student_repo.get(db, student_id)
    if not s:
        return None
    return _hydrate(db, s)


def list_students(
    db: Session,
    *,
    q: str | None,
    department_id: int | None,
    risk: str | None,
    page: int,
    page_size: int,
    sort: str,
) -> tuple[list[dict[str, Any]], int]:
    items, total = student_repo.search(
        db,
        q=q,
        department_id=department_id,
        risk=risk,
        page=page,
        page_size=page_size,
        sort=sort,
    )
    return [_hydrate(db, s) for s in items], total


def create_student(db: Session, payload: StudentCreate) -> dict[str, Any]:
    if student_repo.get_by_roll_no(db, payload.roll_no):
        raise ValueError(f"roll_no {payload.roll_no} already exists")
    student = Student(
        **payload.model_dump(exclude={"financial_status", "placement_readiness"}),
        financial_status=FinancialStatus(payload.financial_status),
        placement_readiness=PlacementReadiness(payload.placement_readiness),
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return _hydrate(db, student)


def update_student(db: Session, student_id: int, payload: StudentUpdate) -> dict[str, Any] | None:
    s = student_repo.get(db, student_id)
    if not s:
        return None
    data = payload.model_dump(exclude_unset=True)
    if "financial_status" in data and data["financial_status"] is not None:
        data["financial_status"] = FinancialStatus(data["financial_status"])
    if "placement_readiness" in data and data["placement_readiness"] is not None:
        data["placement_readiness"] = PlacementReadiness(data["placement_readiness"])
    for k, v in data.items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)
    return _hydrate(db, s)


def delete_student(db: Session, student_id: int) -> bool:
    s = student_repo.get(db, student_id)
    if not s:
        return False
    db.delete(s)
    db.commit()
    return True


def bulk_create(db: Session, items: list[StudentCreate]) -> dict[str, int]:
    inserted = 0
    skipped = 0
    for item in items:
        try:
            if student_repo.get_by_roll_no(db, item.roll_no):
                skipped += 1
                continue
            db.add(
                Student(
                    **item.model_dump(exclude={"financial_status", "placement_readiness"}),
                    financial_status=FinancialStatus(item.financial_status),
                    placement_readiness=PlacementReadiness(item.placement_readiness),
                )
            )
            inserted += 1
        except Exception:  # noqa: BLE001
            skipped += 1
    db.commit()
    return {"inserted": inserted, "skipped": skipped}
