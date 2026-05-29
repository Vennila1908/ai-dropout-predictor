"""Prediction ORM model — every model run on a student is persisted here."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Index, JSON, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.recommendation import Recommendation
    from app.models.student import Student


class RiskLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Prediction(Base):
    __tablename__ = "predictions"
    __table_args__ = (
        Index("idx_predictions_student_created", "student_id", "created_at"),
        Index("idx_predictions_risk", "risk_level"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    risk_level: Mapped[RiskLevel] = mapped_column(SAEnum(RiskLevel, name="risk_level"), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    model_version: Mapped[str] = mapped_column(String(120), nullable=False, default="v1")
    features_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    explanation_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    student: Mapped["Student"] = relationship("Student", back_populates="predictions")
    recommendations: Mapped[list["Recommendation"]] = relationship(
        "Recommendation", back_populates="prediction"
    )
