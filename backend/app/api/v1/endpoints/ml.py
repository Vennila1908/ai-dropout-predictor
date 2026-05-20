"""ML training/status endpoints."""

from __future__ import annotations

import threading
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_db, require_admin
from app.core.logging import get_logger
from app.ml.predict import reset_cache as reset_predict_cache
from app.ml.train import train_from_dataset
from app.schemas.prediction import MLStatus, TrainResponse
from app.services import prediction_service


logger = get_logger(__name__)
router = APIRouter(prefix="/ml", tags=["ml"])


_jobs: dict[str, dict] = {}
_jobs_lock = threading.Lock()


def _run_training(job_id: str) -> None:
    with _jobs_lock:
        _jobs[job_id]["status"] = "running"
    try:
        meta = train_from_dataset(settings.default_dataset_path)
        reset_predict_cache()
        with _jobs_lock:
            _jobs[job_id].update(status="completed", finished_at=datetime.now(timezone.utc), result=meta.get("metrics"))
    except Exception as exc:  # noqa: BLE001
        logger.exception("Training failed: %s", exc)
        with _jobs_lock:
            _jobs[job_id].update(status="failed", error=str(exc), finished_at=datetime.now(timezone.utc))


@router.post("/train", response_model=TrainResponse, dependencies=[Depends(require_admin)])
def train(background_tasks: BackgroundTasks) -> TrainResponse:
    job_id = uuid.uuid4().hex[:12]
    with _jobs_lock:
        _jobs[job_id] = {
            "id": job_id,
            "status": "started",
            "started_at": datetime.now(timezone.utc),
        }
    background_tasks.add_task(_run_training, job_id)
    return TrainResponse(job_id=job_id, status="started", detail="Training scheduled in background.")


@router.get("/jobs/{job_id}", response_model=TrainResponse)
def job_status(job_id: str) -> TrainResponse:
    with _jobs_lock:
        job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return TrainResponse(job_id=job_id, status=job["status"], detail=str(job.get("error") or ""))


@router.get("/status", response_model=MLStatus)
def status() -> MLStatus:
    return MLStatus.model_validate(prediction_service.status())


@router.get("/feature-importance")
def feature_importance(_: Session = Depends(get_db)) -> list[dict]:
    return prediction_service.status().get("feature_importances", [])
