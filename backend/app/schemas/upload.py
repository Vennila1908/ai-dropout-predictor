"""Upload schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

UploadStatusLiteral = Literal["pending", "parsed", "imported", "failed"]


class UploadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    original_name: str
    file_type: str
    size_bytes: int
    rows_imported: int
    status: UploadStatusLiteral
    error: Optional[str] = None
    uploaded_by: Optional[int] = None
    created_at: datetime


class ColumnSuggestion(BaseModel):
    source: str
    target: Optional[str] = None
    score: float = 0.0
    candidates: List[str] = Field(default_factory=list)


class UploadPreview(BaseModel):
    upload_id: int
    detected_columns: List[str]
    suggested_mapping: List[ColumnSuggestion]
    preview_rows: List[Dict[str, Any]]
    total_rows: int
    target_fields: List[str]


class UploadConfirmIn(BaseModel):
    mapping: Dict[str, str] = Field(
        description="Map of source column name → target student field name."
    )
    skip_invalid: bool = True


class UploadConfirmResult(BaseModel):
    upload_id: int
    rows_imported: int
    rows_skipped: int
    errors: List[str] = Field(default_factory=list)
