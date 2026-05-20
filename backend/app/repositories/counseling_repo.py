"""Counseling-session repository."""

from __future__ import annotations

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.counseling_session import CounselingSession
from app.repositories.base import CrudRepo


class CounselingRepo(CrudRepo[CounselingSession]):
    def __init__(self) -> None:
        super().__init__(CounselingSession)

    def list_for_student(self, db: Session, student_id: int) -> Sequence[CounselingSession]:
        return db.execute(
            select(CounselingSession)
            .where(CounselingSession.student_id == student_id)
            .order_by(CounselingSession.created_at.desc())
        ).scalars().all()


counseling_repo = CounselingRepo()
