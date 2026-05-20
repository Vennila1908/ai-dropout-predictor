"""Student CRUD endpoints + timeline + bulk import."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_admin_or_faculty
from app.models.user import User
from app.repositories.counseling_repo import counseling_repo
from app.repositories.prediction_repo import prediction_repo
from app.repositories.student_repo import student_repo
from app.schemas.common import Page
from app.schemas.student import (
    RiskLevelLiteral,
    StudentCreate,
    StudentOut,
    StudentTimelineOut,
    StudentUpdate,
    TimelineEvent,
)
from app.services import student_service
from app.services.auth_service import write_audit


router = APIRouter(prefix="/students", tags=["students"])


@router.get("", response_model=Page[StudentOut])
def list_students(
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
    q: str | None = Query(default=None),
    department_id: int | None = Query(default=None),
    risk: RiskLevelLiteral | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    sort: str = Query(default="-created_at"),
) -> Page[StudentOut]:
    items, total = student_service.list_students(
        db,
        q=q,
        department_id=department_id,
        risk=risk,
        page=page,
        page_size=page_size,
        sort=sort,
    )
    return Page[StudentOut](
        items=[StudentOut.model_validate(s) for s in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=StudentOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin_or_faculty)])
def create_student(payload: StudentCreate, db: Session = Depends(get_db), me: User = Depends(get_current_user)) -> StudentOut:
    try:
        item = student_service.create_student(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    write_audit(db, user_id=me.id, action="student.create", entity="student", entity_id=item["id"], meta={"roll_no": item["roll_no"]})
    return StudentOut.model_validate(item)


@router.get("/{student_id}", response_model=StudentOut)
def get_student(student_id: int, db: Session = Depends(get_db)) -> StudentOut:
    item = student_service.get_student(db, student_id)
    if not item:
        raise HTTPException(status_code=404, detail="Student not found")
    return StudentOut.model_validate(item)


@router.patch("/{student_id}", response_model=StudentOut, dependencies=[Depends(require_admin_or_faculty)])
def update_student(student_id: int, payload: StudentUpdate, db: Session = Depends(get_db), me: User = Depends(get_current_user)) -> StudentOut:
    item = student_service.update_student(db, student_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail="Student not found")
    write_audit(db, user_id=me.id, action="student.update", entity="student", entity_id=student_id, meta={})
    return StudentOut.model_validate(item)


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin_or_faculty)])
def delete_student(student_id: int, db: Session = Depends(get_db), me: User = Depends(get_current_user)) -> None:
    if not student_service.delete_student(db, student_id):
        raise HTTPException(status_code=404, detail="Student not found")
    write_audit(db, user_id=me.id, action="student.delete", entity="student", entity_id=student_id, meta={})


@router.get("/{student_id}/timeline", response_model=StudentTimelineOut)
def student_timeline(student_id: int, db: Session = Depends(get_db)) -> StudentTimelineOut:
    student = student_repo.get(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    events: list[TimelineEvent] = []
    for p in prediction_repo.list_for_student(db, student_id):
        events.append(
            TimelineEvent(
                type="prediction",
                timestamp=p.created_at,
                title=f"Risk = {p.risk_level.value} (conf {p.confidence:.2f})",
                detail={"narrative": (p.explanation_json or {}).get("narrative", "")},
            )
        )
    for c in counseling_repo.list_for_student(db, student_id):
        events.append(
            TimelineEvent(
                type="counseling",
                timestamp=c.created_at,
                title="Counseling session",
                detail={"notes": c.notes, "outcome": c.outcome},
            )
        )
    for note in student.notes:
        events.append(
            TimelineEvent(
                type="note",
                timestamp=note.created_at,
                title="Faculty note",
                detail={"note": note.note},
            )
        )
    events.sort(key=lambda e: e.timestamp, reverse=True)
    return StudentTimelineOut(student_id=student_id, events=events)


@router.post("/bulk", response_model=dict[str, int], dependencies=[Depends(require_admin_or_faculty)])
def bulk_create(payload: list[StudentCreate], db: Session = Depends(get_db), me: User = Depends(get_current_user)) -> dict[str, int]:
    res = student_service.bulk_create(db, payload)
    write_audit(db, user_id=me.id, action="student.bulk_create", entity="student", meta=res)
    return res
