"""Upload repository."""

from __future__ import annotations

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.upload import Upload
from app.repositories.base import CrudRepo


class UploadRepo(CrudRepo[Upload]):
    def __init__(self) -> None:
        super().__init__(Upload)

    def list_recent(self, db: Session, limit: int = 50) -> Sequence[Upload]:
        return db.execute(
            select(Upload).order_by(Upload.created_at.desc()).limit(limit)
        ).scalars().all()


upload_repo = UploadRepo()
