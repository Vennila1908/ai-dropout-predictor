"""One-shot DB bootstrap: create tables + seed initial data if empty."""

from __future__ import annotations

from sqlalchemy import inspect, text

from app.core.logging import get_logger
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.db.seed import seed_all
import app.models  # noqa: F401  (register models on Base.metadata)


logger = get_logger(__name__)


def _apply_lightweight_migrations() -> None:
    """Add columns/indexes that create_all() does not apply to existing databases."""
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return
    columns = {c["name"] for c in inspector.get_columns("users")}
    if "roll_no" not in columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN roll_no VARCHAR(40)"))
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_roll_no ON users (roll_no)"))
        logger.info("Added users.roll_no column")


def init_db() -> None:
    """Create all tables and seed default data on first run."""
    logger.info("Creating database tables (if not exist)...")
    Base.metadata.create_all(bind=engine)
    _apply_lightweight_migrations()

    db = SessionLocal()
    try:
        seed_all(db)
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
