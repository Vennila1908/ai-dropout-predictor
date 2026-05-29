"""User schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.validators import EmailAddress, PersonNameLong, RollNumber

UserRoleLiteral = Literal["admin", "faculty", "student"]


class UserBase(BaseModel):
    email: EmailAddress
    full_name: str = Field(min_length=1, max_length=255)
    role: UserRoleLiteral
    roll_no: Optional[str] = Field(default=None, max_length=40)
    department_id: Optional[int] = None
    is_active: bool = True


class UserRollLookup(BaseModel):
    roll_no: str
    full_name: str
    department_id: Optional[int] = None


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)
    full_name: PersonNameLong
    roll_no: RollNumber | None = None


class UserUpdate(BaseModel):
    full_name: PersonNameLong | None = None
    role: Optional[UserRoleLiteral] = None
    department_id: Optional[int] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime
