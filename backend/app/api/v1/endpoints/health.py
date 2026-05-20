"""Health endpoints — used by docker compose, k8s probes, and the UI."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import __version__
from app.core.deps import get_db
from app.services.llm_service import llm_service


router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    db_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001
        db_ok = False
    return {"status": "ok" if db_ok else "degraded", "db": db_ok, "version": __version__}


@router.get("/health/llm")
async def health_llm() -> dict:
    return await llm_service.ping()
