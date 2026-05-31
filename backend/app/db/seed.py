"""Idempotent seed: departments, users, sample students, and demo predictions.

Imports students from `datasets/sample_students.csv` when the table is empty.
Runs ML predictions for nine curated low/medium/high showcase rolls via
``seed_risk_demo_predictions``. Use ``python -m app.db.seed --risk-demo-predictions``
to refresh those predictions after retraining.
"""

from __future__ import annotations

import csv
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import hash_password
from app.repositories.prediction_repo import prediction_repo
from app.repositories.student_repo import student_repo
from app.schemas.validators import normalize_roll_no
from app.models.department import Department
from app.models.student import FinancialStatus, PlacementReadiness, Student
from app.models.user import User, UserRole
from app.services import prediction_service


logger = get_logger(__name__)

_STUDENT_EMAIL_DOMAIN = "student.edu"


_DEFAULT_DEPARTMENTS = [
    ("B.Sc. Computer Science", "BSCS"),
    ("Bachelor of Computer Applications", "BCA"),
    ("B.Sc. Physics", "BSCP"),
    ("B.Sc. Mathematics", "BSCM"),
    ("B.Sc. Chemistry", "BSCC"),
    ("Bachelor of Business Administration", "BBA"),
    ("B.Com", "BCOM"),
    ("M.Com", "MCOM"),
    ("B.Com (Honours)", "BCOMH"),
    ("B.Com (Computer Applications)", "BCOMCA"),
]


# Old engineering-style codes → new degree program codes (one-time migration on startup).
_LEGACY_DEPT_CODE_MAP: dict[str, str] = {
    "CSE": "BSCS",
    "IT": "BCA",
    "ECE": "BSCP",
    "MECH": "BSCM",
    "CIVIL": "BSCC",
    "MBA": "BBA",
}


def _migrate_legacy_department_codes(db: Session, departments: dict[str, Department]) -> None:
    """Re-point students/users from legacy dept rows to the new degree program codes."""
    by_code = {d.code: d for d in db.execute(select(Department)).scalars().all()}
    migrated_students = 0
    for old_code, new_code in _LEGACY_DEPT_CODE_MAP.items():
        old_dept = by_code.get(old_code)
        new_dept = departments.get(new_code) or by_code.get(new_code)
        if not old_dept or not new_dept or old_dept.id == new_dept.id:
            continue
        for student in db.execute(select(Student).where(Student.department_id == old_dept.id)).scalars():
            student.department_id = new_dept.id
            migrated_students += 1
        for user in db.execute(select(User).where(User.department_id == old_dept.id)).scalars():
            user.department_id = new_dept.id
        # Align roll_no prefixes (e.g. CSE040002 → BSCS040002).
        for student in db.execute(select(Student).where(Student.roll_no.like(f"{old_code}%"))).scalars():
            student.roll_no = new_code + student.roll_no[len(old_code) :]
            if student.department_id != new_dept.id:
                student.department_id = new_dept.id
    if migrated_students:
        db.commit()
        logger.info("Migrated %d students from legacy engineering dept codes to degree programs", migrated_students)

    # Drop empty legacy department rows so the UI only lists degree programs.
    by_code = {d.code: d for d in db.execute(select(Department)).scalars().all()}
    retired = 0
    for old_code in _LEGACY_DEPT_CODE_MAP:
        old_dept = by_code.get(old_code)
        if not old_dept:
            continue
        has_students = db.execute(
            select(Student.id).where(Student.department_id == old_dept.id).limit(1)
        ).first()
        has_users = db.execute(select(User.id).where(User.department_id == old_dept.id).limit(1)).first()
        if not has_students and not has_users:
            db.delete(old_dept)
            retired += 1
    if retired:
        db.commit()
        logger.info("Retired %d legacy engineering department rows", retired)


def seed_departments(db: Session) -> dict[str, Department]:
    existing = {d.code: d for d in db.execute(select(Department)).scalars().all()}
    for name, code in _DEFAULT_DEPARTMENTS:
        if code not in existing:
            dept = Department(name=name, code=code)
            db.add(dept)
            existing[code] = dept
        elif existing[code].name != name:
            existing[code].name = name
    db.commit()
    logger.info("Seeded %d departments", len(existing))
    return existing


def seed_users(db: Session, departments: dict[str, Department]) -> None:
    if db.execute(select(User).limit(1)).first():
        return  # already seeded
    bscs = departments.get("BSCS")
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
            full_name="Jane Faculty",
            hashed_password=hash_password("Faculty@123"),
            role=UserRole.faculty,
            department_id=bscs.id if bscs else None,
            is_active=True,
        ),
        User(
            email="student@example.com",
            full_name="Alex Student",
            hashed_password=hash_password("Student@123"),
            role=UserRole.student,
            department_id=bscs.id if bscs else None,
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
    default_dept_id = code_to_id.get("BSCS") or next(iter(code_to_id.values()), None)

    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                dept_id = code_to_id.get(row.get("department_code", "BSCS")) or default_dept_id
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


def _department_codes(departments: dict[str, Department]) -> list[str]:
    """Degree codes in canonical seed order (longest codes first for prefix matching)."""
    ordered = [code for _, code in _DEFAULT_DEPARTMENTS if code in departments]
    extra = sorted(c for c in departments if c not in ordered)
    codes = ordered + extra
    return sorted(codes, key=len, reverse=True)


def _realign_roll_no_prefix(roll_no: str, new_code: str, dept_codes: list[str]) -> str:
    """Replace a leading department code on roll_no (e.g. BSCS040002 → BCOM040002)."""
    upper = roll_no.upper()
    for code in dept_codes:
        if upper.startswith(code):
            return new_code + roll_no[len(code) :]
    return roll_no


def _student_login_email(roll_no: str, suffix: int | None = None) -> str:
    local = roll_no.strip().lower().replace(" ", "")
    if suffix and suffix > 1:
        local = f"{local}.{suffix}"
    return f"{local}@{_STUDENT_EMAIL_DOMAIN}"


def _migrate_student_local_emails(db: Session) -> None:
    """One-time fix: replace legacy @student.local demo emails with @student.edu."""
    users = list(db.execute(select(User).where(User.email.ilike("%@student.local"))).scalars().all())
    if not users:
        return
    for user in users:
        user.email = user.email.replace("@student.local", f"@{_STUDENT_EMAIL_DOMAIN}")
    db.commit()
    logger.info("Migrated %d legacy @student.local emails to @%s", len(users), _STUDENT_EMAIL_DOMAIN)


def _department_without_students(db: Session, department_ids: list[int]) -> bool:
    for dept_id in department_ids:
        if not db.execute(
            select(Student.id).where(Student.department_id == dept_id).limit(1)
        ).first():
            return True
    return False


def redistribute_students_across_departments(db: Session, departments: dict[str, Department]) -> None:
    """Round-robin students across every department when some have none."""
    dept_list = [departments[code] for _, code in _DEFAULT_DEPARTMENTS if code in departments]
    if not dept_list:
        return
    dept_ids = [d.id for d in dept_list]
    if not _department_without_students(db, dept_ids):
        return

    students = list(db.execute(select(Student).order_by(Student.id)).scalars().all())
    if not students:
        return

    codes = _department_codes(departments)
    used_rolls = {s.roll_no for s in students}
    reassigned = 0

    for index, student in enumerate(students):
        target = dept_list[index % len(dept_list)]
        if student.department_id == target.id:
            continue
        student.department_id = target.id
        reassigned += 1
        new_roll = _realign_roll_no_prefix(student.roll_no, target.code, codes)
        if new_roll != student.roll_no and new_roll not in used_rolls:
            used_rolls.remove(student.roll_no)
            used_rolls.add(new_roll)
            student.roll_no = new_roll

    db.commit()
    logger.info(
        "Redistributed %d students across %d departments (round-robin)",
        reassigned,
        len(dept_list),
    )


def seed_student_login_accounts(db: Session) -> None:
    """Create a student-role login for every student record missing an account."""
    students = list(db.execute(select(Student).order_by(Student.id)).scalars().all())
    if not students:
        return

    existing_rolls = {
        roll_no
        for roll_no in db.execute(
            select(User.roll_no).where(User.roll_no.isnot(None), User.role == UserRole.student)
        ).scalars()
    }
    existing_emails = {email.lower() for email in db.execute(select(User.email)).scalars()}
    default_password = hash_password(settings.seed_student_password)
    created = 0

    for student in students:
        if student.roll_no in existing_rolls:
            continue
        email = _student_login_email(student.roll_no)
        if email.lower() in existing_emails:
            suffix = 2
            while _student_login_email(student.roll_no, suffix).lower() in existing_emails:
                suffix += 1
            email = _student_login_email(student.roll_no, suffix)

        user = User(
            email=email,
            full_name=student.name,
            hashed_password=default_password,
            role=UserRole.student,
            roll_no=student.roll_no,
            department_id=student.department_id,
            is_active=True,
        )
        db.add(user)
        existing_rolls.add(student.roll_no)
        existing_emails.add(email.lower())
        created += 1

    if created:
        db.commit()
        logger.info("Created %d student login accounts (password: seed default)", created)


def _sanitize_roll_numbers(db: Session) -> None:
    """Normalize legacy roll numbers (e.g. DEMO-LOW-01) to alphanumeric-only form."""
    used_rolls = {roll for roll in db.execute(select(Student.roll_no)).scalars()}
    updated = 0

    for student in db.execute(select(Student)).scalars():
        normalized = normalize_roll_no(student.roll_no)
        if not normalized or normalized == student.roll_no:
            continue
        if normalized in used_rolls and normalized != student.roll_no:
            logger.warning("Skipping roll_no migration collision for student id=%s", student.id)
            continue
        used_rolls.discard(student.roll_no)
        used_rolls.add(normalized)
        student.roll_no = normalized
        updated += 1

    for user in db.execute(select(User).where(User.roll_no.isnot(None))).scalars():
        if not user.roll_no:
            continue
        normalized = normalize_roll_no(user.roll_no)
        if normalized and normalized != user.roll_no:
            user.roll_no = normalized

    if updated:
        db.commit()
        logger.info("Normalized %d student roll numbers to alphanumeric-only format", updated)


# Curated low / medium / high showcases (last 9 rows in sample_students.csv).
RISK_DEMO_ROLL_NUMBERS: tuple[str, ...] = (
    "BSCS060211",
    "BCA050212",
    "BSCP040213",
    "BSCS050214",
    "BSCM060215",
    "BCA040216",
    "BSCS050217",
    "BSCP060218",
    "BSCC040219",
)


def seed_risk_demo_predictions(db: Session, *, force: bool = False) -> dict[str, int]:
    """Run ML predictions for curated demo students (imported from sample_students.csv)."""
    predicted = 0
    skipped = 0
    missing: list[str] = []

    for roll_no in RISK_DEMO_ROLL_NUMBERS:
        student = student_repo.get_by_roll_no(db, roll_no)
        if not student:
            missing.append(roll_no)
            continue
        if not force and prediction_repo.latest(db, student.id):
            skipped += 1
            continue
        result = prediction_service.predict_for_student(db, roll_no)
        if result:
            predicted += 1
            logger.info(
                "Predicted %s (%s) risk=%s confidence=%.2f",
                roll_no,
                student.id,
                result.get("risk_level"),
                float(result.get("confidence") or 0),
            )

    if missing:
        logger.warning(
            "Demo students not in DB (import sample_students.csv first): %s",
            ", ".join(missing),
        )

    logger.info(
        "Risk demo predictions: predicted=%d skipped=%d missing=%d (of %d)",
        predicted,
        skipped,
        len(missing),
        len(RISK_DEMO_ROLL_NUMBERS),
    )
    return {
        "predicted": predicted,
        "skipped": skipped,
        "missing": len(missing),
        "total_demos": len(RISK_DEMO_ROLL_NUMBERS),
    }


def seed_all(db: Session) -> None:
    """Run every seed step. Safe to call repeatedly — each step is idempotent."""
    departments = seed_departments(db)
    _migrate_legacy_department_codes(db, departments)
    seed_users(db, departments)
    seed_sample_students(db, departments)
    seed_risk_demo_predictions(db)
    _sanitize_roll_numbers(db)
    redistribute_students_across_departments(db, departments)
    _migrate_student_local_emails(db)
    seed_student_login_accounts(db)


if __name__ == "__main__":
    import argparse

    from app.db.session import SessionLocal

    parser = argparse.ArgumentParser(description="Seed database or refresh risk-demo predictions.")
    parser.add_argument(
        "--risk-demo-predictions",
        action="store_true",
        help="Run ML predictions for the nine curated demo students only.",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.risk_demo_predictions:
            summary = seed_risk_demo_predictions(db, force=True)
            print(
                f"Done — ran {summary['predicted']} predictions, "
                f"skipped {summary['skipped']} (already had predictions), "
                f"missing {summary['missing']} of {summary['total_demos']} demo rolls."
            )
        else:
            seed_all(db)
            print("Seed complete.")
    finally:
        db.close()
