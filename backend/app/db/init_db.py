"""One-shot DB bootstrap: create tables + seed initial data if empty."""

from __future__ import annotations

from app.core.logging import get_logger
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.db.seed import seed_all
import app.models  # noqa: F401  (register models on Base.metadata)


logger = get_logger(__name__)


def init_db() -> None:
    """Create all tables and seed default data on first run."""
    logger.info("Creating database tables (if not exist)...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        seed_all(db)
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
