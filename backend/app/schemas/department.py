"""Degree program / course (department) schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class DepartmentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    code: str = Field(min_length=2, max_length=20, pattern=r"^[A-Za-z0-9-]+$")


class DepartmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    code: str | None = Field(default=None, min_length=2, max_length=20, pattern=r"^[A-Za-z0-9-]+$")


class DepartmentOut(BaseModel):
    id: int
    name: str
    code: str
    student_count: int = 0
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
