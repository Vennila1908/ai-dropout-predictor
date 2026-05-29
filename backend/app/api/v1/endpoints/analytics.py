"""Analytics dashboard endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.schemas.analytics import (
    AnalyticsBundle,
    AttendanceTrendPoint,
    ConfidenceBucket,
    DepartmentRisk,
    OverviewStats,
    RiskBucket,
)
from app.services import analytics_service


router = APIRouter(prefix="/analytics", tags=["analytics"], dependencies=[Depends(get_current_user)])


@router.get("/overview", response_model=OverviewStats)
def overview(db: Session = Depends(get_db)) -> OverviewStats:
    return OverviewStats.model_validate(analytics_service.overview(db))


@router.get("/risk-distribution", response_model=list[RiskBucket])
def risk_distribution(db: Session = Depends(get_db)) -> list[RiskBucket]:
    return [RiskBucket.model_validate(b) for b in analytics_service.risk_distribution(db)]


@router.get("/department-risk", response_model=list[DepartmentRisk])
def department_risk(db: Session = Depends(get_db)) -> list[DepartmentRisk]:
    return [DepartmentRisk.model_validate(d) for d in analytics_service.department_risk(db)]


@router.get("/attendance-trends", response_model=list[AttendanceTrendPoint])
def attendance_trends(db: Session = Depends(get_db)) -> list[AttendanceTrendPoint]:
    return [AttendanceTrendPoint.model_validate(p) for p in analytics_service.attendance_trends(db)]


@router.get("/prediction-confidence", response_model=list[ConfidenceBucket])
def prediction_confidence(db: Session = Depends(get_db)) -> list[ConfidenceBucket]:
    return [ConfidenceBucket.model_validate(b) for b in analytics_service.confidence_distribution(db)]


@router.get("/bundle", response_model=AnalyticsBundle)
def bundle(db: Session = Depends(get_db)) -> AnalyticsBundle:
    return AnalyticsBundle.model_validate(analytics_service.bundle(db))
