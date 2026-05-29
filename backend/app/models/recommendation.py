"""Recommendation ORM model — output of LLM or fallback service."""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import ForeignKey, Index, JSON, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.prediction import Prediction
    from app.models.student import Student
    from app.models.user import User


class RecommendationSource(str, enum.Enum):
    llm = "llm"
    fallback = "fallback"


class RecommendationStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    dismissed = "dismissed"


class Recommendation(Base, TimestampMixin):
    __tablename__ = "recommendations"
    __table_args__ = (Index("idx_reco_student_created", "student_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    prediction_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("predictions.id", ondelete="SET NULL"), nullable=True
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    plan_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    source: Mapped[RecommendationSource] = mapped_column(
        SAEnum(RecommendationSource, name="reco_source"), default=RecommendationSource.fallback, nullable=False
    )
    status: Mapped[RecommendationStatus] = mapped_column(
        SAEnum(RecommendationStatus, name="reco_status"),
        default=RecommendationStatus.pending,
        nullable=False,
    )
    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    student: Mapped["Student"] = relationship("Student", back_populates="recommendations")
    prediction: Mapped[Optional["Prediction"]] = relationship("Prediction", back_populates="recommendations")
    author: Mapped[Optional["User"]] = relationship("User")
