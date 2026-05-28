"""Prediction endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_admin_or_faculty
from app.models.user import User
from app.schemas.prediction import BatchPredictionRequest, BatchPredictionResult, PredictionOut
from app.schemas.validators import RESERVED_ROLL_NOS, ROLL_NO_PATTERN
from app.services import prediction_service
from app.services.auth_service import write_audit


router = APIRouter(prefix="/predictions", tags=["predictions"])


def _reject_reserved_roll_no(roll_no: str) -> None:
    if roll_no.lower() in RESERVED_ROLL_NOS:
        raise HTTPException(status_code=404, detail="Student not found")


@router.post("/batch", response_model=BatchPredictionResult, dependencies=[Depends(require_admin_or_faculty)])
def run_batch(
    payload: BatchPredictionRequest = Body(default_factory=BatchPredictionRequest),
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
) -> BatchPredictionResult:
    res = prediction_service.predict_batch(
        db,
        roll_nos=payload.roll_nos,
        student_ids=payload.student_ids,
        department_id=payload.department_id,
    )
    write_audit(db, user_id=me.id, action="prediction.batch", entity="prediction", meta={"total": res["total"], "succeeded": res["succeeded"]})
    return BatchPredictionResult.model_validate(res)


@router.post("/{roll_no}", response_model=PredictionOut, dependencies=[Depends(require_admin_or_faculty)])
def run_prediction(
    roll_no: str = Path(..., pattern=ROLL_NO_PATTERN),
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
) -> PredictionOut:
    _reject_reserved_roll_no(roll_no)
    res = prediction_service.predict_for_student(db, roll_no)
    if not res:
        raise HTTPException(status_code=404, detail="Student not found")
    write_audit(
        db,
        user_id=me.id,
        action="prediction.create",
        entity="student",
        entity_id=res["student_id"],
        meta={"roll_no": roll_no, "risk": res["risk_level"]},
    )
    return PredictionOut.model_validate(res)


@router.get("/{roll_no}/latest", response_model=PredictionOut)
def latest(
    roll_no: str = Path(..., pattern=ROLL_NO_PATTERN),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PredictionOut:
    _reject_reserved_roll_no(roll_no)
    res = prediction_service.latest_for_student(db, roll_no)
    if not res:
        raise HTTPException(status_code=404, detail="No prediction yet")
    return PredictionOut.model_validate(res)


@router.get("/{roll_no}/history", response_model=list[PredictionOut])
def history(
    roll_no: str = Path(..., pattern=ROLL_NO_PATTERN),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[PredictionOut]:
    _reject_reserved_roll_no(roll_no)
    return [PredictionOut.model_validate(r) for r in prediction_service.history_for_student(db, roll_no)]
