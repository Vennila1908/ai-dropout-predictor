"""Analytics — aggregations for the dashboards."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.prediction import Prediction, RiskLevel
from app.models.student import Student
from app.models.user import User, UserRole
from app.ml.registry import load_artifact


def _latest_prediction_subq(db: Session):
    """Return a subquery that holds the latest prediction per student."""
    rn = (
        select(
            Prediction.id,
            Prediction.student_id,
            Prediction.risk_level,
            Prediction.confidence,
            Prediction.created_at,
            func.row_number().over(partition_by=Prediction.student_id, order_by=Prediction.created_at.desc()).label("rn"),
        )
    ).subquery()
    return rn


def overview(db: Session) -> dict[str, Any]:
    total_students = int(db.execute(select(func.count(Student.id))).scalar_one() or 0)
    total_faculty = int(
        db.execute(select(func.count(User.id)).where(User.role == UserRole.faculty)).scalar_one() or 0
    )
    total_predictions = int(db.execute(select(func.count(Prediction.id))).scalar_one() or 0)

    avg_attendance = float(db.execute(select(func.avg(Student.attendance_pct))).scalar() or 0)
    avg_internal = float(db.execute(select(func.avg(Student.internal_marks))).scalar() or 0)

    risk_split = {"low": 0, "medium": 0, "high": 0}
    sub = _latest_prediction_subq(db)
    rows = db.execute(
        select(sub.c.risk_level, func.count()).where(sub.c.rn == 1).group_by(sub.c.risk_level)
    ).all()
    for risk_level, count in rows:
        key = risk_level.value if hasattr(risk_level, "value") else str(risk_level)
        risk_split[key] = int(count)

    counted = sum(risk_split.values()) or 1
    high_pct = round(100.0 * risk_split.get("high", 0) / counted, 2)

    _, meta = load_artifact()
    last_trained = meta.get("trained_at") if meta else None

    return {
        "total_students": total_students,
        "total_faculty": total_faculty,
        "total_predictions": total_predictions,
        "risk_split": risk_split,
        "avg_attendance": round(avg_attendance, 2),
        "avg_internal_marks": round(avg_internal, 2),
        "high_risk_pct": high_pct,
        "last_trained_at": last_trained,
    }


def risk_distribution(db: Session) -> list[dict[str, Any]]:
    sub = _latest_prediction_subq(db)
    rows = db.execute(
        select(sub.c.risk_level, func.count()).where(sub.c.rn == 1).group_by(sub.c.risk_level)
    ).all()
    counts = {"low": 0, "medium": 0, "high": 0}
    for risk_level, count in rows:
        counts[risk_level.value if hasattr(risk_level, "value") else str(risk_level)] = int(count)
    return [{"risk_level": k, "count": v} for k, v in counts.items()]


def department_risk(db: Session) -> list[dict[str, Any]]:
    sub = _latest_prediction_subq(db)
    rows = db.execute(
        select(
            Department.id,
            Department.name,
            Department.code,
            sub.c.risk_level,
            func.count(),
        )
        .select_from(Student)
        .join(Department, Student.department_id == Department.id, isouter=True)
        .join(sub, sub.c.student_id == Student.id, isouter=True)
        .where((sub.c.rn == 1) | (sub.c.rn.is_(None)))
        .group_by(Department.id, Department.name, Department.code, sub.c.risk_level)
    ).all()

    bucket: dict[int, dict] = {}
    for dept_id, dept_name, dept_code, risk_level, count in rows:
        if dept_id is None:
            continue
        bucket.setdefault(
            dept_id,
            {"department_id": dept_id, "department_name": dept_name, "department_code": dept_code,
             "low": 0, "medium": 0, "high": 0},
        )
        if risk_level is None:
            continue
        key = risk_level.value if hasattr(risk_level, "value") else str(risk_level)
        if key in bucket[dept_id]:
            bucket[dept_id][key] += int(count)
    return list(bucket.values())


def attendance_trends(db: Session) -> list[dict[str, Any]]:
    rows = db.execute(
        select(Student.semester, func.avg(Student.attendance_pct), func.count())
        .group_by(Student.semester)
        .order_by(Student.semester)
    ).all()
    return [
        {"semester": int(sem), "avg_attendance": round(float(avg or 0), 2), "student_count": int(cnt)}
        for sem, avg, cnt in rows
    ]


def confidence_distribution(db: Session) -> list[dict[str, Any]]:
    sub = _latest_prediction_subq(db)
    confidences = [
        float(c[0]) for c in db.execute(select(sub.c.confidence).where(sub.c.rn == 1)).all() if c[0] is not None
    ]
    buckets = [(0.0, 0.5), (0.5, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.01)]
    out = []
    for lo, hi in buckets:
        count = sum(1 for c in confidences if lo <= c < hi)
        label = f"{lo:.1f}-{hi:.1f}" if hi <= 1.0 else f"{lo:.1f}-1.0"
        out.append({"bucket": label, "count": count})
    return out


def bundle(db: Session) -> dict[str, Any]:
    return {
        "overview": overview(db),
        "risk_distribution": risk_distribution(db),
        "department_risk": department_risk(db),
        "attendance_trends": attendance_trends(db),
        "confidence_distribution": confidence_distribution(db),
    }
