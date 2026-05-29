"""Recommendation schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

RecommendationStatusLiteral = Literal["pending", "in_progress", "completed", "dismissed"]
RecommendationSourceLiteral = Literal["llm", "fallback"]


class InterventionAction(BaseModel):
    action: str
    owner: Literal["faculty", "student", "admin", "parent", "counselor"] = "faculty"
    timeline: str = "this week"


class RoadmapWeek(BaseModel):
    week: int
    focus: str
    activities: List[str] = Field(default_factory=list)


class RecommendationPlan(BaseModel):
    intervention_plan: List[InterventionAction] = Field(default_factory=list)
    faculty_actions: List[str] = Field(default_factory=list)
    student_roadmap: List[RoadmapWeek] = Field(default_factory=list)


class RecommendationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    prediction_id: Optional[int] = None
    summary: str
    plan: RecommendationPlan
    source: RecommendationSourceLiteral
    status: RecommendationStatusLiteral
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class RecommendationUpdate(BaseModel):
    status: Optional[RecommendationStatusLiteral] = None
    summary: Optional[str] = None
