"""Prediction endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_admin_or_faculty
from app.models.user import User
from app.schemas.prediction import BatchPredictionRequest, BatchPredictionResult, PredictionOut
from app.services import prediction_service
from app.services.auth_service import write_audit


router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.post("/{student_id}", response_model=PredictionOut, dependencies=[Depends(require_admin_or_faculty)])
def run_prediction(student_id: int, db: Session = Depends(get_db), me: User = Depends(get_current_user)) -> PredictionOut:
    res = prediction_service.predict_for_student(db, student_id)
    if not res:
        raise HTTPException(status_code=404, detail="Student not found")
    write_audit(db, user_id=me.id, action="prediction.create", entity="student", entity_id=student_id, meta={"risk": res["risk_level"]})
    return PredictionOut.model_validate(res)


@router.post("/batch", response_model=BatchPredictionResult, dependencies=[Depends(require_admin_or_faculty)])
def run_batch(
    payload: BatchPredictionRequest,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
) -> BatchPredictionResult:
    res = prediction_service.predict_batch(db, student_ids=payload.student_ids, department_id=payload.department_id)
    write_audit(db, user_id=me.id, action="prediction.batch", entity="prediction", meta={"total": res["total"], "succeeded": res["succeeded"]})
    return BatchPredictionResult.model_validate(res)


@router.get("/{student_id}/latest", response_model=PredictionOut)
def latest(student_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> PredictionOut:
    res = prediction_service.latest_for_student(db, student_id)
    if not res:
        raise HTTPException(status_code=404, detail="No prediction yet")
    return PredictionOut.model_validate(res)


@router.get("/{student_id}/history", response_model=list[PredictionOut])
def history(student_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> list[PredictionOut]:
    return [PredictionOut.model_validate(r) for r in prediction_service.history_for_student(db, student_id)]
