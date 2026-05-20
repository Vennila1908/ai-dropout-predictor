"""Idempotent seed: creates default departments + admin/faculty/student users.

Also imports a handful of demo students from `datasets/sample_students.csv`
when the students table is empty so the dashboards have something to show.
"""

from __future__ import annotations

import csv
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import hash_password
from app.models.department import Department
from app.models.student import FinancialStatus, PlacementReadiness, Student
from app.models.user import User, UserRole


logger = get_logger(__name__)


_DEFAULT_DEPARTMENTS = [
    ("Computer Science", "CSE"),
    ("Information Technology", "IT"),
    ("Electronics", "ECE"),
    ("Mechanical", "MECH"),
    ("Civil", "CIVIL"),
    ("Business Administration", "MBA"),
]


def seed_departments(db: Session) -> dict[str, Department]:
    existing = {d.code: d for d in db.execute(select(Department)).scalars().all()}
    for name, code in _DEFAULT_DEPARTMENTS:
        if code not in existing:
            dept = Department(name=name, code=code)
            db.add(dept)
            existing[code] = dept
    db.commit()
    logger.info("Seeded %d departments", len(existing))
    return existing


def seed_users(db: Session, departments: dict[str, Department]) -> None:
    if db.execute(select(User).limit(1)).first():
        return  # already seeded
    cse = departments.get("CSE")
    users = [
        User(
            email=settings.seed_admin_email,
            full_name="Administrator",
            hashed_password=hash_password(settings.seed_admin_password),
            role=UserRole.admin,
            department_id=None,
            is_active=True,
        ),
        User(
            email="faculty@example.com",
            full_name="Dr. Jane Faculty",
            hashed_password=hash_password("Faculty@123"),
            role=UserRole.faculty,
            department_id=cse.id if cse else None,
            is_active=True,
        ),
        User(
            email="student@example.com",
            full_name="Alex Student",
            hashed_password=hash_password("Student@123"),
            role=UserRole.student,
            department_id=cse.id if cse else None,
            is_active=True,
        ),
    ]
    db.add_all(users)
    db.commit()
    logger.info("Seeded %d users (admin/faculty/student)", len(users))


def seed_sample_students(db: Session, departments: dict[str, Department]) -> None:
    """Import demo students from sample_students.csv if the table is empty."""
    if db.execute(select(Student).limit(1)).first():
        return
    csv_path: Path = settings.default_dataset_path
    if not csv_path.exists():
        logger.warning("Sample dataset not found at %s — skipping student seed.", csv_path)
        return

    inserted = 0
    code_to_id = {code: dept.id for code, dept in departments.items()}
    default_dept_id = code_to_id.get("CSE") or next(iter(code_to_id.values()), None)

    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                dept_id = code_to_id.get(row.get("department_code", "CSE")) or default_dept_id
                student = Student(
                    roll_no=row["roll_no"].strip(),
                    name=row["name"].strip(),
                    age=int(row.get("age") or 20),
                    gender=row.get("gender", "U"),
                    department_id=dept_id,
                    semester=int(row.get("semester") or 1),
                    attendance_pct=float(row.get("attendance_pct") or 75),
                    internal_marks=float(row.get("internal_marks") or 50),
                    semester_marks=float(row.get("semester_marks") or 50),
                    backlogs=int(row.get("backlogs") or 0),
                    fee_paid=str(row.get("fee_paid", "true")).lower() in {"1", "true", "yes", "y"},
                    fee_delay_days=int(row.get("fee_delay_days") or 0),
                    financial_status=FinancialStatus(row.get("financial_status", "medium")),
                    family_background=row.get("family_background", ""),
                    behavioral_indicators=row.get("behavioral_indicators", ""),
                    extracurricular=row.get("extracurricular", ""),
                    placement_readiness=PlacementReadiness(row.get("placement_readiness", "medium")),
                    counselor_remarks=row.get("counselor_remarks", ""),
                )
                db.add(student)
                inserted += 1
                if inserted % 100 == 0:
                    db.flush()
            except Exception as exc:  # noqa: BLE001
                logger.warning("Skipping malformed sample row: %s", exc)
                continue
    db.commit()
    logger.info("Seeded %d sample students from %s", inserted, csv_path)


def seed_all(db: Session) -> None:
    """Run every seed step. Safe to call repeatedly — each step is idempotent."""
    departments = seed_departments(db)
    seed_users(db, departments)
    seed_sample_students(db, departments)
