"""Offline chat assistant — feeds aggregated stats to the local LLM with guardrails."""

from __future__ import annotations

import re
from typing import Any, AsyncIterator

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.logging import get_logger
from app.models.student import Student
from app.services import analytics_service
from app.services.llm_service import LLMUnavailable, llm_service
from app.services.student_service import _hydrate


logger = get_logger(__name__)


SYSTEM_PROMPT = (
    "You are an academic-analytics assistant embedded inside a college "
    "dropout-prediction system. You ONLY answer using the data block "
    "provided below. Never invent students, teachers, or numbers that are "
    "not present in the data block. If the user asks for information you "
    "do not have, say so plainly. The UI renders charts and tables from the "
    "same data — do NOT repeat raw student rows, pipe-separated lists, or "
    "roll-number dumps in your reply. Give a brief 1–3 sentence summary "
    "with counts and one insight only."
)


def _infer_filters(message: str) -> dict[str, Any]:
    """Derive lightweight DB filters from natural-language chat prompts."""
    msg = message.lower()
    filters: dict[str, Any] = {}

    backlog_match = re.search(r"(\d+)\+?\s*backlogs?", msg)
    if backlog_match:
        filters["min_backlogs"] = int(backlog_match.group(1))
    elif "backlog" in msg:
        filters["min_backlogs"] = 3

    att_match = re.search(r"attendance\s+(?:below|under|≤|<=?)\s*(\d+)", msg)
    if att_match:
        filters["max_attendance"] = float(att_match.group(1))
    elif re.search(r"(?:below|under)\s+60", msg) and "attendance" in msg:
        filters["max_attendance"] = 60.0

    return filters


def _merged_filters(message: str, context: dict | None) -> dict[str, Any]:
    filters = dict(context or {})
    for key, value in _infer_filters(message).items():
        filters.setdefault(key, value)
    return filters


def _filtered_students(db: Session, filters: dict | None) -> list[Student]:
    """Apply lightweight filters from the chat request."""
    filters = filters or {}
    stmt = select(Student).options(joinedload(Student.department))
    if filters.get("department_id"):
        stmt = stmt.where(Student.department_id == int(filters["department_id"]))
    if filters.get("max_attendance") is not None:
        stmt = stmt.where(Student.attendance_pct <= float(filters["max_attendance"]))
    if filters.get("min_backlogs") is not None:
        stmt = stmt.where(Student.backlogs >= int(filters["min_backlogs"]))
    return list(db.execute(stmt.order_by(Student.backlogs.desc(), Student.attendance_pct).limit(50)).scalars().all())


def _build_artifacts(db: Session, *, message: str, filters: dict | None) -> dict[str, Any]:
    """Structured data for rich assistant UI (tables, charts, stat cards)."""
    overview = analytics_service.overview(db)
    risk_distribution = analytics_service.risk_distribution(db)
    department_risk = analytics_service.department_risk(db)
    matched = _filtered_students(db, filters)
    students = [_hydrate(db, s) for s in matched[:25]]

    msg = message.lower()
    wants_students = bool(students) or any(
        token in msg
        for token in ("student", "list", "show", "who", "backlog", "attendance", "roll")
    )
    wants_risk = any(token in msg for token in ("risk", "overview", "summary", "how many", "distribution"))
    wants_departments = any(
        token in msg for token in ("department", "dept", "cse", "profile", "breakdown")
    )

    return {
        "overview": overview if wants_risk or wants_students else None,
        "risk_distribution": risk_distribution if wants_risk else None,
        "department_risk": department_risk if wants_departments else None,
        "students": students if wants_students else None,
        "total_matching_students": len(matched),
        "filters_applied": filters or None,
    }


def _data_block(db: Session, filters: dict | None) -> str:
    overview = analytics_service.overview(db)
    rd = analytics_service.risk_distribution(db)
    dr = analytics_service.department_risk(db)

    students = _filtered_students(db, filters)
    student_lines = []
    for s in students[:25]:
        student_lines.append(
            f"  - {s.roll_no} | {s.name} | dept_id={s.department_id} | sem={s.semester} | "
            f"att={s.attendance_pct:.0f}% | backlogs={s.backlogs} | internal={s.internal_marks:.0f}"
        )
    students_str = "\n".join(student_lines) or "  (no students match filters)"

    rd_str = ", ".join(f"{b['risk_level']}={b['count']}" for b in rd)
    dr_str = "\n".join(
        f"  - {row['department_code']}: low={row['low']} medium={row['medium']} high={row['high']}"
        for row in dr
    )

    return (
        "DATA\n"
        f"- Total students: {overview['total_students']}\n"
        f"- Avg attendance: {overview['avg_attendance']}%\n"
        f"- Avg internal marks: {overview['avg_internal_marks']}\n"
        f"- Risk split: {rd_str}\n"
        f"- High-risk %: {overview['high_risk_pct']}%\n"
        "DEPARTMENT RISK\n"
        f"{dr_str or '  (none)'}\n"
        "STUDENT SAMPLE (first 25 matching filters)\n"
        f"{students_str}\n"
    )


def _polish_answer(text: str, artifacts: dict[str, Any]) -> str:
    """Replace LLM pipe-dumps with a short summary when the UI shows a table."""
    cleaned = (text or "").strip()
    if not cleaned:
        return cleaned

    has_student_table = bool(artifacts.get("students"))
    looks_like_row_dump = "|" in cleaned and (
        "backlogs=" in cleaned or "dept_id=" in cleaned or "att=" in cleaned
    )
    if has_student_table and looks_like_row_dump:
        total = artifacts.get("total_matching_students") or len(artifacts["students"])
        shown = len(artifacts["students"])
        if shown < total:
            return f"Found {total} matching students (showing {shown} in the table below)."
        return f"Found {total} matching student{'s' if total != 1 else ''} — see the table below."

    if has_student_table and len(cleaned) > 400:
        total = artifacts.get("total_matching_students") or len(artifacts["students"])
        return f"Found {total} matching students. Details are in the table below."

    return cleaned


def _fallback_answer(message: str, db: Session, filters: dict | None) -> str:
    """Deterministic, useful answer when the LLM is unreachable."""
    overview = analytics_service.overview(db)
    students = _filtered_students(db, filters)
    msg = message.lower()
    if "below" in msg and "attendance" in msg:
        threshold_filter = filters.get("max_attendance") if filters else 60
        threshold = threshold_filter if threshold_filter else 60
        low = [s for s in students if s.attendance_pct <= float(threshold)]
        names = ", ".join(f"{s.roll_no} ({s.attendance_pct:.0f}%)" for s in low[:10])
        return f"{len(low)} student(s) have attendance ≤ {threshold}%. First few: {names or 'none'}."
    if "high risk" in msg or "highrisk" in msg:
        return f"Currently {overview['risk_split'].get('high', 0)} students are at high risk ({overview['high_risk_pct']}% of cohort)."
    if "summary" in msg or "overview" in msg:
        return (
            f"Cohort summary: {overview['total_students']} students, avg attendance "
            f"{overview['avg_attendance']}%, avg internal {overview['avg_internal_marks']}, "
            f"high-risk = {overview['risk_split'].get('high', 0)}."
        )
    return (
        "(Local LLM is unavailable — running in deterministic mode.) "
        f"You have {overview['total_students']} students, {overview['risk_split'].get('high', 0)} at high risk. "
        "Try a more specific question like 'students with attendance below 60%'."
    )


async def answer(db: Session, *, message: str, filters: dict | None = None) -> dict[str, Any]:
    """Return a non-streaming answer (text + source + visualization artifacts)."""
    merged = _merged_filters(message, filters)
    artifacts = _build_artifacts(db, message=message, filters=merged)
    block = _data_block(db, merged)
    prompt = f"{block}\n\nQUESTION:\n{message}\n\nANSWER:"
    try:
        text = await llm_service.generate(prompt, system=SYSTEM_PROMPT)
        raw = text or _fallback_answer(message, db, merged)
        return {
            "answer": _polish_answer(raw, artifacts),
            "source": "llm",
            "artifacts": artifacts,
        }
    except LLMUnavailable as exc:
        logger.info("Chat fallback engaged: %s", exc)
        return {
            "answer": _fallback_answer(message, db, merged),
            "source": "fallback",
            "artifacts": artifacts,
        }


async def stream_answer(db: Session, *, message: str, filters: dict | None = None) -> AsyncIterator[str]:
    """Yield chunks of the answer for SSE."""
    block = _data_block(db, filters)
    prompt = f"{block}\n\nQUESTION:\n{message}\n\nANSWER:"
    try:
        async for chunk in llm_service.stream(prompt, system=SYSTEM_PROMPT):
            yield chunk
    except LLMUnavailable:
        yield _fallback_answer(message, db, filters)
