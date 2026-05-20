"""Recommendation endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_admin_or_faculty
from app.models.user import User
from app.schemas.recommendation import RecommendationOut, RecommendationUpdate
from app.services import recommendation_service
from app.services.auth_service import write_audit


router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/{student_id}/generate", response_model=RecommendationOut, dependencies=[Depends(require_admin_or_faculty)])
async def generate(student_id: int, db: Session = Depends(get_db), me: User = Depends(get_current_user)) -> RecommendationOut:
    res = await recommendation_service.generate_for_student(db, student_id, created_by=me.id)
    if not res:
        raise HTTPException(status_code=404, detail="Student not found")
    write_audit(db, user_id=me.id, action="recommendation.generate", entity="student", entity_id=student_id, meta={"source": res["source"]})
    return RecommendationOut.model_validate(_shape(res))


@router.get("/{student_id}", response_model=list[RecommendationOut])
def list_for_student(student_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> list[RecommendationOut]:
    return [RecommendationOut.model_validate(_shape(r)) for r in recommendation_service.list_for_student(db, student_id)]


@router.patch("/{rec_id}", response_model=RecommendationOut, dependencies=[Depends(require_admin_or_faculty)])
def patch(rec_id: int, payload: RecommendationUpdate, db: Session = Depends(get_db), me: User = Depends(get_current_user)) -> RecommendationOut:
    res = recommendation_service.update_status(
        db, rec_id, status=payload.status, summary=payload.summary
    )
    if not res:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    write_audit(db, user_id=me.id, action="recommendation.update", entity="recommendation", entity_id=rec_id, meta={})
    return RecommendationOut.model_validate(_shape(res))


def _shape(raw: dict) -> dict:
    """Reshape the service-layer dict to fit the RecommendationOut schema."""
    plan = raw.get("plan") or {}
    return {
        "id": raw["id"],
        "student_id": raw["student_id"],
        "prediction_id": raw.get("prediction_id"),
        "summary": raw.get("summary", ""),
        "plan": {
            "intervention_plan": plan.get("intervention_plan", []),
            "faculty_actions": plan.get("faculty_actions", []),
            "student_roadmap": plan.get("student_roadmap", []),
        },
        "source": raw.get("source", "fallback"),
        "status": raw.get("status", "pending"),
        "created_by": raw.get("created_by"),
        "created_at": raw["created_at"],
        "updated_at": raw["updated_at"],
    }
