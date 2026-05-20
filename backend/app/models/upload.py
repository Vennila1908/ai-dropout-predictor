"""Upload ORM model — tracks file uploads + their processing status."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class UploadStatus(str, enum.Enum):
    pending = "pending"
    parsed = "parsed"
    imported = "imported"
    failed = "failed"


class Upload(Base):
    __tablename__ = "uploads"
    __table_args__ = (Index("idx_uploads_user_created", "uploaded_by", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)  # uuid name on disk
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rows_imported: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[UploadStatus] = mapped_column(
        SAEnum(UploadStatus, name="upload_status"), default=UploadStatus.pending, nullable=False
    )
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    uploaded_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    uploader: Mapped[Optional["User"]] = relationship("User")
