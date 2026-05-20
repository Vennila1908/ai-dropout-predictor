"""Recommendation repository."""

from __future__ import annotations

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.recommendation import Recommendation
from app.repositories.base import CrudRepo


class RecommendationRepo(CrudRepo[Recommendation]):
    def __init__(self) -> None:
        super().__init__(Recommendation)

    def list_for_student(self, db: Session, student_id: int) -> Sequence[Recommendation]:
        return db.execute(
            select(Recommendation)
            .where(Recommendation.student_id == student_id)
            .order_by(Recommendation.created_at.desc())
        ).scalars().all()


recommendation_repo = RecommendationRepo()
