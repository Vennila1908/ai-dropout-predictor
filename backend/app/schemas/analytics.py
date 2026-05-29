"""Analytics-dashboard schemas."""

from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel


class RiskBucket(BaseModel):
    risk_level: str
    count: int


class DepartmentRisk(BaseModel):
    department_id: int
    department_name: str
    department_code: str
    low: int
    medium: int
    high: int


class AttendanceTrendPoint(BaseModel):
    semester: int
    avg_attendance: float
    student_count: int


class ConfidenceBucket(BaseModel):
    bucket: str  # e.g. "0.5-0.6"
    count: int


class OverviewStats(BaseModel):
    total_students: int
    total_faculty: int
    total_predictions: int
    risk_split: Dict[str, int]
    avg_attendance: float
    avg_internal_marks: float
    high_risk_pct: float
    last_trained_at: str | None = None


class AnalyticsBundle(BaseModel):
    overview: OverviewStats
    risk_distribution: List[RiskBucket]
    department_risk: List[DepartmentRisk]
    attendance_trends: List[AttendanceTrendPoint]
    confidence_distribution: List[ConfidenceBucket]
