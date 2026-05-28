"""Prediction + explainability schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.student import RiskLevelLiteral
from app.schemas.validators import RollNumber


class FeatureContribution(BaseModel):
    feature: str
    value: float | int | str
    contribution: float
    direction: Literal["increases_risk", "decreases_risk", "neutral"]


class Explanation(BaseModel):
    top_factors: List[FeatureContribution]
    narrative: str


class PredictionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
    student_id: int
    roll_no: str
    risk_level: RiskLevelLiteral
    confidence: float
    model_version: str
    features: dict[str, Any] = Field(default_factory=dict)
    explanation: Explanation
    created_at: datetime


class BatchPredictionRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    roll_nos: Optional[List[RollNumber]] = None
    student_ids: Optional[List[int]] = None  # legacy — mapped to roll numbers server-side
    department_id: Optional[int] = None


class BatchPredictionResult(BaseModel):
    total: int
    succeeded: int
    failed: int
    predictions: List[PredictionOut]


class MLStatus(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_name: Optional[str] = None
    trained_at: Optional[datetime] = None
    feature_list: List[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    confusion_matrix: List[List[int]] = Field(default_factory=list)
    feature_importances: List[dict] = Field(default_factory=list)
    class_labels: List[str] = Field(default_factory=list)
    artifact_present: bool = False


class TrainResponse(BaseModel):
    job_id: str
    status: Literal["started", "running", "completed", "failed"]
    detail: Optional[str] = None
