"""Student ORM model."""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.counseling_session import CounselingSession
    from app.models.department import Department
    from app.models.faculty_note import FacultyNote
    from app.models.prediction import Prediction
    from app.models.recommendation import Recommendation
    from app.models.risk_history import RiskHistory


class FinancialStatus(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class PlacementReadiness(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Student(Base, TimestampMixin):
    __tablename__ = "students"
    __table_args__ = (
        Index("idx_students_department", "department_id"),
        Index("idx_students_created", "created_at"),
        Index("idx_students_roll", "roll_no"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    roll_no: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    gender: Mapped[str] = mapped_column(String(16), nullable=False, default="U")

    department_id: Mapped[Optional[int]] = mapped_column(ForeignKey("departments.id"), nullable=True)
    semester: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    attendance_pct: Mapped[float] = mapped_column(Float, nullable=False, default=75.0)
    internal_marks: Mapped[float] = mapped_column(Float, nullable=False, default=50.0)
    semester_marks: Mapped[float] = mapped_column(Float, nullable=False, default=50.0)
    backlogs: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    fee_paid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    fee_delay_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    financial_status: Mapped[FinancialStatus] = mapped_column(
        SAEnum(FinancialStatus, name="financial_status"), default=FinancialStatus.medium, nullable=False
    )

    family_background: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default="")
    behavioral_indicators: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default="")
    extracurricular: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default="")
    placement_readiness: Mapped[PlacementReadiness] = mapped_column(
        SAEnum(PlacementReadiness, name="placement_readiness"),
        default=PlacementReadiness.medium,
        nullable=False,
    )
    counselor_remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default="")
    faculty_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default="")

    department: Mapped[Optional["Department"]] = relationship("Department", back_populates="students")
    predictions: Mapped[List["Prediction"]] = relationship(
        "Prediction", back_populates="student", cascade="all, delete-orphan"
    )
    recommendations: Mapped[List["Recommendation"]] = relationship(
        "Recommendation", back_populates="student", cascade="all, delete-orphan"
    )
    counseling_sessions: Mapped[List["CounselingSession"]] = relationship(
        "CounselingSession", back_populates="student", cascade="all, delete-orphan"
    )
    risk_history: Mapped[List["RiskHistory"]] = relationship(
        "RiskHistory", back_populates="student", cascade="all, delete-orphan"
    )
    notes: Mapped[List["FacultyNote"]] = relationship(
        "FacultyNote", back_populates="student", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Student id={self.id} roll_no={self.roll_no}>"
