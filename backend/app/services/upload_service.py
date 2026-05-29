"""Upload service — parse + preview + commit."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.department import Department
from app.models.student import FinancialStatus, PlacementReadiness, Student
from app.models.upload import Upload, UploadStatus
from app.parsers.column_mapper import TARGET_FIELDS, suggest_mapping
from app.parsers.csv_parser import iter_csv_rows, parse_csv
from app.parsers.docx_parser import iter_docx_rows, parse_docx
from app.parsers.excel_parser import iter_excel_rows, parse_excel
from app.parsers.pdf_parser import iter_pdf_rows, parse_pdf
from app.repositories.student_repo import student_repo
from app.repositories.upload_repo import upload_repo
from app.schemas.validators import is_valid_person_name, is_valid_roll_no, normalize_roll_no


logger = get_logger(__name__)


def _parse_by_ext(ext: str, path: Path) -> tuple[list[str], list[dict[str, Any]], int]:
    if ext == ".csv":
        return parse_csv(path)
    if ext in {".xlsx", ".xls"}:
        return parse_excel(path)
    if ext == ".pdf":
        return parse_pdf(path)
    if ext == ".docx":
        return parse_docx(path)
    raise ValueError(f"unsupported extension: {ext}")


def _iter_by_ext(ext: str, path: Path) -> tuple[list[str], list[dict[str, Any]]]:
    if ext == ".csv":
        return iter_csv_rows(path)
    if ext in {".xlsx", ".xls"}:
        return iter_excel_rows(path)
    if ext == ".pdf":
        return iter_pdf_rows(path)
    if ext == ".docx":
        return iter_docx_rows(path)
    raise ValueError(f"unsupported extension: {ext}")


def register_upload(
    db: Session,
    *,
    disk_path: Path,
    original_name: str,
    size_bytes: int,
    ext: str,
    user_id: int | None,
) -> Upload:
    upload = Upload(
        filename=disk_path.name,
        original_name=original_name,
        file_type=ext.lstrip("."),
        size_bytes=size_bytes,
        rows_imported=0,
        status=UploadStatus.pending,
        uploaded_by=user_id,
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)
    return upload


def preview_upload(db: Session, upload: Upload) -> dict[str, Any]:
    """Parse the file and produce a preview + suggested column mapping."""
    disk_path: Path = (Path(__file__).resolve().parents[2] / "uploads" / upload.filename)
    if not disk_path.exists():
        # The configured upload_dir might be a different location.
        from app.core.config import settings

        disk_path = settings.upload_path / upload.filename

    ext = f".{upload.file_type}"
    try:
        columns, preview_rows, total = _parse_by_ext(ext, disk_path)
    except Exception as exc:  # noqa: BLE001
        upload.status = UploadStatus.failed
        upload.error = str(exc)
        db.commit()
        raise

    suggestions = suggest_mapping(columns)
    upload.status = UploadStatus.parsed
    db.commit()
    return {
        "upload_id": upload.id,
        "detected_columns": columns,
        "suggested_mapping": suggestions,
        "preview_rows": preview_rows,
        "total_rows": total,
        "target_fields": TARGET_FIELDS,
    }


def confirm_upload(
    db: Session, upload: Upload, mapping: dict[str, str], skip_invalid: bool = True
) -> dict[str, Any]:
    """Read the file again with the user-confirmed mapping and insert students."""
    from app.core.config import settings

    disk_path = settings.upload_path / upload.filename
    ext = f".{upload.file_type}"
    _, rows = _iter_by_ext(ext, disk_path)

    departments = {d.code: d.id for d in db.query(Department).all()}
    inserted, skipped, errors = 0, 0, []
    for row in rows:
        try:
            mapped = _apply_mapping(row, mapping)
            if not mapped.get("roll_no") or not mapped.get("name"):
                if skip_invalid:
                    skipped += 1
                    continue
                raise ValueError(f"row missing roll_no/name: {row}")

            roll_no = normalize_roll_no(str(mapped["roll_no"]))
            name = str(mapped.get("name", "")).strip()
            if not is_valid_roll_no(roll_no) or not is_valid_person_name(name):
                if skip_invalid:
                    skipped += 1
                    errors.append(f"invalid roll_no/name: roll_no={mapped.get('roll_no')!r}, name={name!r}")
                    continue
                raise ValueError(f"row has invalid roll_no or name: roll_no={mapped.get('roll_no')!r}, name={name!r}")

            if student_repo.get_by_roll_no(db, roll_no):
                skipped += 1
                continue

            dept_code = (mapped.get("department_code") or "").strip().upper() or None
            dept_id = departments.get(dept_code) if dept_code else None
            if dept_id is None:
                # Auto-create unknown departments to keep the import lossless.
                if dept_code:
                    new_dept = Department(name=dept_code.title(), code=dept_code)
                    db.add(new_dept)
                    db.commit()
                    db.refresh(new_dept)
                    departments[dept_code] = new_dept.id
                    dept_id = new_dept.id

            student = Student(
                roll_no=roll_no,
                name=name,
                age=_int(mapped.get("age", 20), 20),
                gender=str(mapped.get("gender", "U")).strip()[:16] or "U",
                department_id=dept_id,
                semester=_int(mapped.get("semester", 1), 1),
                attendance_pct=_float(mapped.get("attendance_pct", 75), 75.0),
                internal_marks=_float(mapped.get("internal_marks", 50), 50.0),
                semester_marks=_float(mapped.get("semester_marks", 50), 50.0),
                backlogs=_int(mapped.get("backlogs", 0), 0),
                fee_paid=_bool(mapped.get("fee_paid", True)),
                fee_delay_days=_int(mapped.get("fee_delay_days", 0), 0),
                financial_status=FinancialStatus(_enum_or(mapped.get("financial_status"), "medium", {"low", "medium", "high"})),
                family_background=str(mapped.get("family_background", "")),
                behavioral_indicators=str(mapped.get("behavioral_indicators", "")),
                extracurricular=str(mapped.get("extracurricular", "")),
                placement_readiness=PlacementReadiness(_enum_or(mapped.get("placement_readiness"), "medium", {"low", "medium", "high"})),
                counselor_remarks=str(mapped.get("counselor_remarks", "")),
            )
            db.add(student)
            inserted += 1
            if inserted % 200 == 0:
                db.flush()
        except Exception as exc:  # noqa: BLE001
            if skip_invalid:
                skipped += 1
                errors.append(f"{exc}")
                continue
            db.rollback()
            upload.status = UploadStatus.failed
            upload.error = str(exc)
            db.commit()
            raise

    db.commit()
    upload.rows_imported = inserted
    upload.status = UploadStatus.imported
    db.commit()
    return {
        "upload_id": upload.id,
        "rows_imported": inserted,
        "rows_skipped": skipped,
        "errors": errors[:25],
    }


def _apply_mapping(row: dict, mapping: dict[str, str]) -> dict:
    out: dict = {}
    for source, target in mapping.items():
        if not target:
            continue
        out[target] = row.get(source, "")
    return out


def _int(v, default: int) -> int:
    try:
        if v is None or v == "":
            return default
        return int(float(v))
    except (TypeError, ValueError):
        return default


def _float(v, default: float) -> float:
    try:
        if v is None or v == "":
            return default
        return float(v)
    except (TypeError, ValueError):
        return default


def _bool(v) -> bool:
    if isinstance(v, bool):
        return v
    if v is None:
        return True
    s = str(v).strip().lower()
    return s in {"1", "true", "yes", "y", "paid", "ok"}


def _enum_or(v, default: str, allowed: set[str]) -> str:
    if v is None:
        return default
    s = str(v).strip().lower()
    return s if s in allowed else default


def list_uploads(db: Session) -> list[Upload]:
    return list(upload_repo.list_recent(db, limit=100))
