"""Counseling-session schemas."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CounselingCreate(BaseModel):
    student_id: int
    notes: str = Field(min_length=1)
    outcome: Optional[str] = None
    next_followup: Optional[date] = None


class CounselingUpdate(BaseModel):
    notes: Optional[str] = None
    outcome: Optional[str] = None
    next_followup: Optional[date] = None


class CounselingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    student_id: int
    faculty_id: Optional[int] = None
    notes: str
    outcome: Optional[str] = None
    next_followup: Optional[date] = None
    created_at: datetime
