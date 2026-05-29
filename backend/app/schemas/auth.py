"""Auth-related schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.user import UserOut
from app.schemas.validators import EmailAddress, PersonNameLong


class LoginIn(BaseModel):
    email: EmailAddress
    password: str = Field(min_length=4, max_length=128)


class RegisterIn(BaseModel):
    email: EmailAddress
    password: str = Field(min_length=8, max_length=128)
    full_name: PersonNameLong
    role: str = Field(default="student", pattern="^(admin|faculty|student)$")
    department_id: int | None = None


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut


class RefreshIn(BaseModel):
    refresh_token: str


class AccessTokenOnly(BaseModel):
    access_token: str
    token_type: str = "bearer"
