"""Student schemas."""

from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

FinancialStatusLiteral = Literal["low", "medium", "high"]
PlacementReadinessLiteral = Literal["low", "medium", "high"]
RiskLevelLiteral = Literal["low", "medium", "high"]


class StudentBase(BaseModel):
    roll_no: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=160)
    age: int = Field(ge=10, le=80)
    gender: str = Field(default="U", max_length=16)
    department_id: Optional[int] = None
    semester: int = Field(ge=1, le=12)
    attendance_pct: float = Field(ge=0.0, le=100.0)
    internal_marks: float = Field(ge=0.0, le=100.0)
    semester_marks: float = Field(ge=0.0, le=100.0)
    backlogs: int = Field(ge=0, le=50)
    fee_paid: bool = True
    fee_delay_days: int = Field(ge=0, le=730)
    financial_status: FinancialStatusLiteral = "medium"
    family_background: str = ""
    behavioral_indicators: str = ""
    extracurricular: str = ""
    placement_readiness: PlacementReadinessLiteral = "medium"
    counselor_remarks: str = ""
    faculty_notes: str = ""


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = Field(default=None, ge=10, le=80)
    gender: Optional[str] = None
    department_id: Optional[int] = None
    semester: Optional[int] = Field(default=None, ge=1, le=12)
    attendance_pct: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    internal_marks: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    semester_marks: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    backlogs: Optional[int] = Field(default=None, ge=0, le=50)
    fee_paid: Optional[bool] = None
    fee_delay_days: Optional[int] = Field(default=None, ge=0, le=730)
    financial_status: Optional[FinancialStatusLiteral] = None
    family_background: Optional[str] = None
    behavioral_indicators: Optional[str] = None
    extracurricular: Optional[str] = None
    placement_readiness: Optional[PlacementReadinessLiteral] = None
    counselor_remarks: Optional[str] = None
    faculty_notes: Optional[str] = None


class StudentOut(StudentBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime
    department_code: Optional[str] = None
    department_name: Optional[str] = None
    latest_risk: Optional[RiskLevelLiteral] = None
    latest_confidence: Optional[float] = None


class StudentListQuery(BaseModel):
    q: Optional[str] = None
    department_id: Optional[int] = None
    risk: Optional[RiskLevelLiteral] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=200)
    sort: str = Field(default="-created_at")


class TimelineEvent(BaseModel):
    type: Literal["prediction", "counseling", "note", "risk_snapshot"]
    timestamp: datetime
    title: str
    detail: dict


class StudentTimelineOut(BaseModel):
    student_id: int
    events: List[TimelineEvent]
