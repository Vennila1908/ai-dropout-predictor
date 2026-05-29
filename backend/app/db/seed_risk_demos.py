"""Seed demo students across low / medium / high risk tiers with ML predictions.

Safe to run repeatedly — students are keyed by roll_no (DEMOLOW*, etc.).
Existing demo rows get a prediction only when they have none yet.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.seed import seed_departments
from app.db.session import SessionLocal
from app.models.student import FinancialStatus, PlacementReadiness, Student
from app.repositories.prediction_repo import prediction_repo
from app.repositories.student_repo import student_repo
from app.services import prediction_service


logger = get_logger(__name__)

# Profiles crafted to align with label_for() rules in app/ml/features.py.
_RISK_DEMO_STUDENTS: list[dict[str, Any]] = [
    # ── Low risk ────────────────────────────────────────────────────────────
    {
        "roll_no": "DEMOLOW01",
        "name": "Priya Sharma",
        "department_code": "BSCS",
        "semester": 6,
        "attendance_pct": 92.0,
        "internal_marks": 78.0,
        "semester_marks": 81.0,
        "backlogs": 0,
        "fee_paid": True,
        "fee_delay_days": 0,
        "financial_status": "medium",
        "placement_readiness": "high",
        "extracurricular": "Coding club lead, hackathon winner",
        "behavioral_indicators": "Punctual, participates actively",
        "counselor_remarks": "Strong academic track; no intervention needed.",
        "target_risk": "low",
    },
    {
        "roll_no": "DEMOLOW02",
        "name": "Rahul Mehta",
        "department_code": "BCA",
        "semester": 5,
        "attendance_pct": 88.0,
        "internal_marks": 74.0,
        "semester_marks": 76.0,
        "backlogs": 0,
        "fee_paid": True,
        "fee_delay_days": 0,
        "financial_status": "high",
        "placement_readiness": "high",
        "extracurricular": "Robotics club, internship completed",
        "behavioral_indicators": "Collaborative, good peer feedback",
        "counselor_remarks": "On track for placement season.",
        "target_risk": "low",
    },
    {
        "roll_no": "DEMOLOW03",
        "name": "Ananya Iyer",
        "department_code": "BSCP",
        "semester": 4,
        "attendance_pct": 95.0,
        "internal_marks": 82.0,
        "semester_marks": 84.0,
        "backlogs": 0,
        "fee_paid": True,
        "fee_delay_days": 0,
        "financial_status": "medium",
        "placement_readiness": "medium",
        "extracurricular": "NSS volunteer, technical paper presenter",
        "behavioral_indicators": "Consistent performer",
        "counselor_remarks": "Reliable attendance and steady grades.",
        "target_risk": "low",
    },
    # ── Medium risk ─────────────────────────────────────────────────────────
    {
        "roll_no": "DEMOMED01",
        "name": "Vikram Singh",
        "department_code": "BSCS",
        "semester": 5,
        "attendance_pct": 68.0,
        "internal_marks": 52.0,
        "semester_marks": 54.0,
        "backlogs": 1,
        "fee_paid": True,
        "fee_delay_days": 15,
        "financial_status": "medium",
        "placement_readiness": "medium",
        "extracurricular": "Occasional lab sessions",
        "behavioral_indicators": "Missed two consecutive tutorials",
        "counselor_remarks": "Slipping attendance; one backlog to clear.",
        "target_risk": "medium",
    },
    {
        "roll_no": "DEMOMED02",
        "name": "Sneha Patel",
        "department_code": "BSCM",
        "semester": 6,
        "attendance_pct": 73.0,
        "internal_marks": 53.0,
        "semester_marks": 55.0,
        "backlogs": 1,
        "fee_paid": True,
        "fee_delay_days": 35,
        "financial_status": "medium",
        "placement_readiness": "medium",
        "extracurricular": "Workshop participant",
        "behavioral_indicators": "Quiet in class, limited office-hour visits",
        "counselor_remarks": "Borderline grades and one backlog — monitor closely.",
        "target_risk": "medium",
    },
    {
        "roll_no": "DEMOMED03",
        "name": "Karan Joshi",
        "department_code": "BCA",
        "semester": 4,
        "attendance_pct": 74.0,
        "internal_marks": 56.0,
        "semester_marks": 58.0,
        "backlogs": 1,
        "fee_paid": True,
        "fee_delay_days": 0,
        "financial_status": "medium",
        "placement_readiness": "medium",
        "extracurricular": "Part-time tutoring",
        "behavioral_indicators": "Irregular lab submissions",
        "counselor_remarks": "Needs academic coaching for backlog subject.",
        "target_risk": "medium",
    },
    # ── High risk ───────────────────────────────────────────────────────────
    {
        "roll_no": "DEMOHIGH01",
        "name": "Arjun Reddy",
        "department_code": "BSCS",
        "semester": 5,
        "attendance_pct": 42.0,
        "internal_marks": 32.0,
        "semester_marks": 35.0,
        "backlogs": 4,
        "fee_paid": False,
        "fee_delay_days": 90,
        "financial_status": "low",
        "placement_readiness": "low",
        "extracurricular": "",
        "behavioral_indicators": "Repeated absences, disciplinary warning on file",
        "counselor_remarks": "Urgent intervention — multiple failed courses.",
        "target_risk": "high",
    },
    {
        "roll_no": "DEMOHIGH02",
        "name": "Meera Nair",
        "department_code": "BSCP",
        "semester": 6,
        "attendance_pct": 55.0,
        "internal_marks": 38.0,
        "semester_marks": 40.0,
        "backlogs": 3,
        "fee_paid": False,
        "fee_delay_days": 120,
        "financial_status": "low",
        "placement_readiness": "low",
        "extracurricular": "",
        "behavioral_indicators": "Late to exams, missed counseling appointment",
        "counselor_remarks": "Family financial stress reported; at risk of dropout.",
        "target_risk": "high",
    },
    {
        "roll_no": "DEMOHIGH03",
        "name": "Rohit Khan",
        "department_code": "BSCC",
        "semester": 4,
        "attendance_pct": 48.0,
        "internal_marks": 36.0,
        "semester_marks": 38.0,
        "backlogs": 3,
        "fee_paid": False,
        "fee_delay_days": 60,
        "financial_status": "low",
        "placement_readiness": "low",
        "extracurricular": "",
        "behavioral_indicators": "Disengaged, frequent class absences",
        "counselor_remarks": "Schedule parent meeting and remedial plan.",
        "target_risk": "high",
    },
]


def _apply_row(student: Student, row: dict[str, Any], department_id: int) -> None:
    student.name = row["name"]
    student.department_id = department_id
    student.semester = row["semester"]
    student.attendance_pct = row["attendance_pct"]
    student.internal_marks = row["internal_marks"]
    student.semester_marks = row["semester_marks"]
    student.backlogs = row["backlogs"]
    student.fee_paid = row["fee_paid"]
    student.fee_delay_days = row["fee_delay_days"]
    student.financial_status = FinancialStatus(row["financial_status"])
    student.family_background = row.get("family_background", "")
    student.behavioral_indicators = row.get("behavioral_indicators", "")
    student.extracurricular = row.get("extracurricular", "")
    student.placement_readiness = PlacementReadiness(row["placement_readiness"])
    student.counselor_remarks = row.get("counselor_remarks", "")


def _build_student(row: dict[str, Any], department_id: int) -> Student:
    student = Student(
        roll_no=row["roll_no"],
        age=20,
        gender="U",
    )
    _apply_row(student, row, department_id)
    return student


def seed_risk_demo_students(db: Session) -> dict[str, int]:
    """Insert demo students (if missing) and run ML predictions with explanations."""
    departments = seed_departments(db)
    code_to_id = {code: dept.id for code, dept in departments.items()}
    default_dept_id = code_to_id.get("BSCS") or next(iter(code_to_id.values()), None)

    inserted = 0
    updated = 0
    predicted = 0
    student_ids: list[int] = []
    refreshed_ids: set[int] = set()

    for row in _RISK_DEMO_STUDENTS:
        dept_id = code_to_id.get(row["department_code"]) or default_dept_id
        if dept_id is None:
            logger.warning("No departments found — cannot seed %s", row["roll_no"])
            continue

        existing = student_repo.get_by_roll_no(db, row["roll_no"])
        if existing:
            _apply_row(existing, row, dept_id)
            student_ids.append(existing.id)
            refreshed_ids.add(existing.id)
            updated += 1
            continue

        student = _build_student(row, dept_id)
        db.add(student)
        db.flush()
        student_ids.append(student.id)
        inserted += 1

    db.commit()

    for sid in student_ids:
        if prediction_repo.latest(db, sid) and sid not in refreshed_ids:
            continue
        result = prediction_service.predict_for_student(db, sid)
        if result:
            predicted += 1
            logger.info(
                "Predicted %s risk=%s confidence=%.2f",
                result.get("student_id"),
                result.get("risk_level"),
                float(result.get("confidence") or 0),
            )

    summary = {
        "inserted": inserted,
        "updated": updated,
        "predicted": predicted,
        "total_demos": len(_RISK_DEMO_STUDENTS),
    }
    logger.info(
        "Risk demo seed complete: inserted=%d updated=%d predicted=%d (of %d demos)",
        inserted,
        updated,
        predicted,
        len(_RISK_DEMO_STUDENTS),
    )
    return summary


def main() -> None:
    db = SessionLocal()
    try:
        summary = seed_risk_demo_students(db)
        print(
            f"Done — inserted {summary['inserted']}, updated {summary['updated']}, "
            f"ran {summary['predicted']} predictions "
            f"({summary['total_demos']} demo profiles total)."
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
