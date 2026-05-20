"""Recommendation generation — LLM with a deterministic offline fallback."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.counseling_session import CounselingSession
from app.models.recommendation import Recommendation, RecommendationSource, RecommendationStatus
from app.repositories.prediction_repo import prediction_repo
from app.repositories.recommendation_repo import recommendation_repo
from app.repositories.student_repo import student_repo
from app.services.llm_service import LLMUnavailable, llm_service


logger = get_logger(__name__)


def _student_block(student) -> str:
    return (
        f"- Name: {student.name}\n"
        f"- Roll: {student.roll_no}, Department: {getattr(student.department, 'code', '?')}, Semester: {student.semester}\n"
        f"- Attendance %: {student.attendance_pct}\n"
        f"- Internal marks: {student.internal_marks}, Semester marks: {student.semester_marks}\n"
        f"- Backlogs: {student.backlogs}, Fee delay (days): {student.fee_delay_days}\n"
        f"- Financial status: {student.financial_status.value}\n"
        f"- Placement readiness: {student.placement_readiness.value}"
    )


def _prediction_block(pred) -> str:
    if not pred:
        return "(No prediction available — assume medium risk for the plan.)"
    explanation = pred.explanation_json or {}
    factors = explanation.get("top_factors", [])
    factor_str = ", ".join(
        f"{f['feature']}={f.get('value')}({f.get('direction')})" for f in factors[:5]
    ) or "n/a"
    return (
        f"- Risk: {pred.risk_level.value} (confidence {pred.confidence:.2f})\n"
        f"- Top factors: {factor_str}\n"
        f"- Narrative: {explanation.get('narrative', '')}"
    )


def _counseling_block(sessions: list[CounselingSession]) -> str:
    if not sessions:
        return "(No prior counseling sessions.)"
    lines: list[str] = []
    for s in sessions[:3]:
        lines.append(f"- [{s.created_at.date().isoformat()}] {s.notes[:240]}")
    return "\n".join(lines)


def _build_prompt(student, pred, sessions: list[CounselingSession]) -> str:
    return (
        "You are an academic counselor's assistant. Output only valid JSON.\n\n"
        "STUDENT\n"
        f"{_student_block(student)}\n\n"
        "PREDICTION\n"
        f"{_prediction_block(pred)}\n\n"
        "PAST COUNSELING (most recent 3)\n"
        f"{_counseling_block(sessions)}\n\n"
        "TASK\n"
        "Produce a JSON object with keys: \n"
        '  "summary": one-sentence summary,\n'
        '  "intervention_plan": [ { "action": "...", "owner": "faculty|student|admin|parent|counselor", "timeline": "..." } ],\n'
        '  "faculty_actions": [ "..." ],\n'
        '  "student_roadmap": [ { "week": 1, "focus": "...", "activities": [ "..." ] } ]\n'
        "Do not invent facts not present above."
    )


def _fallback_plan(student, pred) -> dict[str, Any]:
    """Deterministic, useful plan when the LLM is offline."""
    actions: list[dict[str, str]] = []
    faculty: list[str] = []
    roadmap: list[dict[str, Any]] = []
    risk = pred.risk_level.value if pred else "medium"

    if student.attendance_pct < 75:
        actions.append({"action": "Schedule weekly attendance review with mentor.", "owner": "faculty", "timeline": "weekly"})
        faculty.append("Track attendance every Monday and flag drops >5%.")
    if student.backlogs > 0:
        actions.append({"action": "Enrol in remedial classes for pending subjects.", "owner": "student", "timeline": "this month"})
        faculty.append("Coordinate with subject coordinators for remedial slots.")
    if student.fee_delay_days > 30:
        actions.append({"action": "Refer to financial-aid office for fee restructuring.", "owner": "counselor", "timeline": "next 2 weeks"})
    if student.internal_marks < 50:
        actions.append({"action": "Pair with peer tutor; bi-weekly progress checks.", "owner": "student", "timeline": "ongoing"})
        faculty.append("Match with a top-quartile peer mentor in the same subjects.")
    if student.placement_readiness.value == "low":
        actions.append({"action": "Enrol in a placement-prep cohort.", "owner": "student", "timeline": "this semester"})

    if not actions:
        actions.append({"action": "Maintain current trajectory; quarterly check-in.", "owner": "faculty", "timeline": "quarterly"})

    roadmap = [
        {"week": 1, "focus": "Stabilize attendance + diagnose gaps", "activities": ["Daily attendance log", "Subject-wise gap test", "Pick 1 weakest subject"]},
        {"week": 2, "focus": "Remediation + mentor pairing", "activities": ["Remedial classes", "Peer tutor sessions", "Weekly mentor 1:1"]},
        {"week": 4, "focus": "Mid-cycle review", "activities": ["Mock internal", "Reset goals", "Update parent if risk persists"]},
        {"week": 8, "focus": "Recovery validation", "activities": ["Repeat assessment", "Plan placement prep if eligible"]},
    ]

    summary = (
        f"{student.name} is currently at {risk} risk. "
        f"Top concerns: attendance {student.attendance_pct:.0f}%, backlogs {student.backlogs}, "
        f"internal marks {student.internal_marks:.0f}."
    )
    return {
        "summary": summary,
        "intervention_plan": actions,
        "faculty_actions": faculty or ["Continue routine monitoring."],
        "student_roadmap": roadmap,
    }


def _normalize_plan(raw: dict) -> dict[str, Any]:
    """Coerce arbitrary LLM JSON into our `RecommendationPlan` shape."""
    summary = str(raw.get("summary") or "").strip() or "Personalized recommendation generated."
    plan = {
        "intervention_plan": _normalize_actions(raw.get("intervention_plan", [])),
        "faculty_actions": [str(x) for x in raw.get("faculty_actions", []) if x],
        "student_roadmap": _normalize_roadmap(raw.get("student_roadmap", [])),
    }
    return {"summary": summary, "plan": plan}


def _normalize_actions(items: Any) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    if not isinstance(items, list):
        return out
    for it in items:
        if isinstance(it, str):
            out.append({"action": it, "owner": "faculty", "timeline": "this week"})
        elif isinstance(it, dict):
            owner = str(it.get("owner") or "faculty").lower()
            if owner not in {"faculty", "student", "admin", "parent", "counselor"}:
                owner = "faculty"
            out.append(
                {
                    "action": str(it.get("action") or it.get("title") or "").strip() or "Action",
                    "owner": owner,
                    "timeline": str(it.get("timeline") or "this week"),
                }
            )
    return out


def _normalize_roadmap(items: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not isinstance(items, list):
        return out
    for it in items:
        if not isinstance(it, dict):
            continue
        try:
            week = int(it.get("week", len(out) + 1))
        except (TypeError, ValueError):
            week = len(out) + 1
        out.append(
            {
                "week": week,
                "focus": str(it.get("focus") or it.get("theme") or "").strip() or f"Week {week} focus",
                "activities": [str(a) for a in (it.get("activities") or []) if a],
            }
        )
    return out


async def generate_for_student(db: Session, student_id: int, *, created_by: int | None) -> dict[str, Any] | None:
    student = student_repo.get(db, student_id)
    if not student:
        return None
    pred = prediction_repo.latest(db, student.id)
    sessions = (
        db.execute(
            select(CounselingSession)
            .where(CounselingSession.student_id == student_id)
            .order_by(CounselingSession.created_at.desc())
            .limit(3)
        )
        .scalars()
        .all()
    )

    source = RecommendationSource.fallback
    plan_dict: dict[str, Any]

    try:
        prompt = _build_prompt(student, pred, sessions)
        raw = await llm_service.generate_json(
            prompt,
            schema_hint='{"summary":"str","intervention_plan":[],"faculty_actions":[],"student_roadmap":[]}',
        )
        if raw and (raw.get("intervention_plan") or raw.get("summary")):
            normalized = _normalize_plan(raw)
            plan_dict = {"summary": normalized["summary"], **normalized["plan"]}
            source = RecommendationSource.llm
        else:
            plan_dict = _fallback_plan(student, pred)
    except LLMUnavailable as exc:
        logger.info("Falling back to deterministic plan: %s", exc)
        plan_dict = _fallback_plan(student, pred)

    rec = Recommendation(
        student_id=student.id,
        prediction_id=pred.id if pred else None,
        summary=plan_dict["summary"],
        plan_json={
            "intervention_plan": plan_dict.get("intervention_plan", []),
            "faculty_actions": plan_dict.get("faculty_actions", []),
            "student_roadmap": plan_dict.get("student_roadmap", []),
        },
        source=source,
        status=RecommendationStatus.pending,
        created_by=created_by,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return _to_response(rec)


def list_for_student(db: Session, student_id: int) -> list[dict[str, Any]]:
    return [_to_response(r) for r in recommendation_repo.list_for_student(db, student_id)]


def update_status(db: Session, rec_id: int, *, status: str | None, summary: str | None) -> dict[str, Any] | None:
    rec = recommendation_repo.get(db, rec_id)
    if not rec:
        return None
    if status:
        rec.status = RecommendationStatus(status)
    if summary is not None:
        rec.summary = summary
    db.commit()
    db.refresh(rec)
    return _to_response(rec)


def _to_response(rec: Recommendation) -> dict[str, Any]:
    return {
        "id": rec.id,
        "student_id": rec.student_id,
        "prediction_id": rec.prediction_id,
        "summary": rec.summary,
        "plan": rec.plan_json or {"intervention_plan": [], "faculty_actions": [], "student_roadmap": []},
        "source": rec.source.value,
        "status": rec.status.value,
        "created_by": rec.created_by,
        "created_at": rec.created_at,
        "updated_at": rec.updated_at,
    }
