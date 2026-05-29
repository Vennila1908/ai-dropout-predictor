"""Prediction service — runs the model + persists results + appends history."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.ml.explain import explain_one
from app.ml.features import student_to_features
from app.ml.predict import model_meta, predict_many, predict_one
from app.ml.registry import has_artifact, load_artifact
from app.models.prediction import Prediction, RiskLevel
from app.models.risk_history import RiskHistory
from app.models.student import Student
from app.repositories.prediction_repo import prediction_repo
from app.repositories.student_repo import student_repo


logger = get_logger(__name__)


def _persist(db: Session, student: Student, raw: dict, explanation: dict) -> Prediction:
    pred = Prediction(
        student_id=student.id,
        risk_level=RiskLevel(raw["risk_level"]),
        confidence=float(raw["confidence"]),
        model_version=str(raw.get("model_version", "v1")),
        features_json=raw.get("features", {}),
        explanation_json=explanation,
    )
    db.add(pred)
    db.add(
        RiskHistory(
            student_id=student.id,
            risk_level=pred.risk_level,
            confidence=pred.confidence,
            snapshot_date=datetime.now(timezone.utc),
        )
    )
    db.commit()
    db.refresh(pred)
    return pred


def _to_response(p: Prediction, *, roll_no: str) -> dict[str, Any]:
    return {
        "id": p.id,
        "student_id": p.student_id,
        "roll_no": roll_no,
        "risk_level": p.risk_level.value,
        "confidence": p.confidence,
        "model_version": p.model_version,
        "features": p.features_json or {},
        "explanation": p.explanation_json or {"top_factors": [], "narrative": ""},
        "created_at": p.created_at,
    }


def predict_for_student(db: Session, roll_no: str) -> dict[str, Any] | None:
    student = student_repo.get_by_roll_no(db, roll_no)
    if not student:
        return None
    record = student_to_features(student)
    raw = predict_one(record)
    model, meta = load_artifact()
    explanation = explain_one(model, raw["features"], meta) if model else {"top_factors": [], "narrative": ""}
    pred = _persist(db, student, raw, explanation)
    return _to_response(pred, roll_no=student.roll_no)


def predict_batch(
    db: Session,
    *,
    roll_nos: list[str] | None,
    student_ids: list[int] | None = None,
    department_id: int | None,
) -> dict[str, Any]:
    students: list[Student] = []
    if not roll_nos and student_ids:
        roll_nos = []
        for sid in student_ids:
            student = student_repo.get(db, sid)
            if student:
                roll_nos.append(student.roll_no)
    if roll_nos:
        students = [s for s in (student_repo.get_by_roll_no(db, roll_no) for roll_no in roll_nos) if s]
    else:
        students, _ = student_repo.search(
            db,
            q=None,
            department_id=department_id,
            risk=None,
            page=1,
            page_size=10000,
            sort="id",
        )
    if not students:
        return {"total": 0, "succeeded": 0, "failed": 0, "predictions": []}

    records = [student_to_features(s) for s in students]
    raws = predict_many(records)
    model, meta = load_artifact()
    out: list[dict] = []
    succeeded = 0
    for student, raw in zip(students, raws):
        try:
            explanation = explain_one(model, raw["features"], meta) if model else {"top_factors": [], "narrative": ""}
            pred = _persist(db, student, raw, explanation)
            out.append(_to_response(pred, roll_no=student.roll_no))
            succeeded += 1
        except Exception as exc:  # noqa: BLE001
            logger.error("Prediction failed for student %s: %s", student.id, exc)
            db.rollback()
    return {
        "total": len(students),
        "succeeded": succeeded,
        "failed": len(students) - succeeded,
        "predictions": out,
    }


def latest_for_student(db: Session, roll_no: str) -> dict[str, Any] | None:
    student = student_repo.get_by_roll_no(db, roll_no)
    if not student:
        return None
    p = prediction_repo.latest(db, student.id)
    return _to_response(p, roll_no=student.roll_no) if p else None


def history_for_student(db: Session, roll_no: str) -> list[dict[str, Any]]:
    student = student_repo.get_by_roll_no(db, roll_no)
    if not student:
        return []
    return [_to_response(p, roll_no=student.roll_no) for p in prediction_repo.list_for_student(db, student.id)]


def status() -> dict[str, Any]:
    if not has_artifact():
        return {"artifact_present": False}
    meta = model_meta()
    return {
        "artifact_present": True,
        "model_name": meta.get("model_name"),
        "trained_at": meta.get("trained_at"),
        "feature_list": meta.get("feature_list", []),
        "metrics": meta.get("metrics", {}),
        "confusion_matrix": meta.get("confusion_matrix", []),
        "feature_importances": meta.get("feature_importances", []),
        "class_labels": meta.get("class_labels", []),
    }
