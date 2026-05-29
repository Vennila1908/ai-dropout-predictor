"""Prediction repository."""

from __future__ import annotations

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.prediction import Prediction
from app.repositories.base import CrudRepo


class PredictionRepo(CrudRepo[Prediction]):
    def __init__(self) -> None:
        super().__init__(Prediction)

    def list_for_student(self, db: Session, student_id: int) -> Sequence[Prediction]:
        return db.execute(
            select(Prediction)
            .where(Prediction.student_id == student_id)
            .order_by(Prediction.created_at.desc())
        ).scalars().all()

    def latest(self, db: Session, student_id: int) -> Prediction | None:
        return db.execute(
            select(Prediction)
            .where(Prediction.student_id == student_id)
            .order_by(Prediction.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()


prediction_repo = PredictionRepo()
