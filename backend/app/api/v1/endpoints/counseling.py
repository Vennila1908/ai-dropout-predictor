"""Counseling-session endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_admin_or_faculty
from app.models.counseling_session import CounselingSession
from app.models.user import User
from app.repositories.counseling_repo import counseling_repo
from app.schemas.counseling import CounselingCreate, CounselingOut, CounselingUpdate
from app.services.auth_service import write_audit


router = APIRouter(prefix="/counseling", tags=["counseling"])


@router.post("", response_model=CounselingOut, dependencies=[Depends(require_admin_or_faculty)])
def create(payload: CounselingCreate, db: Session = Depends(get_db), me: User = Depends(get_current_user)) -> CounselingOut:
    sess = CounselingSession(
        student_id=payload.student_id,
        faculty_id=me.id,
        notes=payload.notes,
        outcome=payload.outcome,
        next_followup=payload.next_followup,
    )
    db.add(sess)
    db.commit()
    db.refresh(sess)
    write_audit(db, user_id=me.id, action="counseling.create", entity="counseling", entity_id=sess.id, meta={"student_id": sess.student_id})
    return CounselingOut.model_validate(sess)


@router.get("/student/{student_id}", response_model=list[CounselingOut])
def list_for_student(student_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> list[CounselingOut]:
    return [CounselingOut.model_validate(s) for s in counseling_repo.list_for_student(db, student_id)]


@router.patch("/{session_id}", response_model=CounselingOut, dependencies=[Depends(require_admin_or_faculty)])
def update(session_id: int, payload: CounselingUpdate, db: Session = Depends(get_db), me: User = Depends(get_current_user)) -> CounselingOut:
    sess = counseling_repo.get(db, session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(sess, k, v)
    db.commit()
    db.refresh(sess)
    write_audit(db, user_id=me.id, action="counseling.update", entity="counseling", entity_id=session_id, meta={})
    return CounselingOut.model_validate(sess)
