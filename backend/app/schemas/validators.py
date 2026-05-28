"""Shared Pydantic field types and validation helpers."""

from __future__ import annotations

import re
from typing import Annotated

from pydantic import Field

# Basic email shape check for API input/output (e.g. seeded demo logins like roll@student.edu).
EmailAddress = Annotated[str, Field(max_length=255, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")]

ROLL_NO_PATTERN = r"^[A-Za-z0-9]+$"
RESERVED_ROLL_NOS = frozenset({"batch"})
PERSON_NAME_PATTERN = r"^[A-Za-z ]+$"

RollNumber = Annotated[str, Field(min_length=1, max_length=40, pattern=ROLL_NO_PATTERN)]
PersonName = Annotated[str, Field(min_length=1, max_length=160, pattern=PERSON_NAME_PATTERN)]
PersonNameLong = Annotated[str, Field(min_length=1, max_length=255, pattern=PERSON_NAME_PATTERN)]

_ROLL_NO_RE = re.compile(ROLL_NO_PATTERN)
_PERSON_NAME_RE = re.compile(PERSON_NAME_PATTERN)


def normalize_roll_no(value: str) -> str:
    """Strip non-alphanumeric characters from a roll number."""
    return re.sub(r"[^A-Za-z0-9]", "", value.strip())


def is_valid_roll_no(value: str) -> bool:
    return bool(_ROLL_NO_RE.fullmatch(value.strip()))


def is_valid_person_name(value: str) -> bool:
    stripped = value.strip()
    return bool(stripped) and bool(_PERSON_NAME_RE.fullmatch(stripped))
