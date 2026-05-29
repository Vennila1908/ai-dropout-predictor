"""Tiny generic repository helpers."""

from __future__ import annotations

from typing import Any, Generic, Iterable, Sequence, Type, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session


T = TypeVar("T")


class CrudRepo(Generic[T]):
    """Minimal CRUD wrapper to keep services free of SQLAlchemy boilerplate."""

    def __init__(self, model: Type[T]):
        self.model = model

    def get(self, db: Session, id_: int) -> T | None:
        return db.get(self.model, id_)

    def list(
        self,
        db: Session,
        *,
        offset: int = 0,
        limit: int = 50,
        order_by: Any | None = None,
        filters: Iterable[Any] = (),
    ) -> Sequence[T]:
        stmt = select(self.model)
        for f in filters:
            stmt = stmt.where(f)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        stmt = stmt.offset(offset).limit(limit)
        return db.execute(stmt).scalars().all()

    def count(self, db: Session, filters: Iterable[Any] = ()) -> int:
        stmt = select(func.count()).select_from(self.model)
        for f in filters:
            stmt = stmt.where(f)
        return int(db.execute(stmt).scalar_one() or 0)

    def add(self, db: Session, obj: T) -> T:
        db.add(obj)
        db.flush()
        return obj

    def delete(self, db: Session, obj: T) -> None:
        db.delete(obj)
        db.flush()
