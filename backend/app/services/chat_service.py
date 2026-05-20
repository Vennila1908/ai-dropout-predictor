"""Offline chat assistant — feeds aggregated stats to the local LLM with guardrails."""

from __future__ import annotations

from typing import Any, AsyncIterator

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.student import Student
from app.services import analytics_service
from app.services.llm_service import LLMUnavailable, llm_service


logger = get_logger(__name__)


SYSTEM_PROMPT = (
    "You are an academic-analytics assistant embedded inside a college "
    "dropout-prediction system. You ONLY answer using the data block "
    "provided below. Never invent students, teachers, or numbers that are "
    "not present in the data block. If the user asks for information you "
    "do not have, say so plainly. Keep answers concise (≤8 sentences)."
)


def _filtered_students(db: Session, filters: dict | None) -> list[Student]:
    """Apply lightweight filters from the chat request."""
    filters = filters or {}
    stmt = select(Student)
    if "department_id" in filters and filters["department_id"]:
        stmt = stmt.where(Student.department_id == int(filters["department_id"]))
    if "max_attendance" in filters and filters["max_attendance"] is not None:
        stmt = stmt.where(Student.attendance_pct <= float(filters["max_attendance"]))
    if "min_backlogs" in filters and filters["min_backlogs"] is not None:
        stmt = stmt.where(Student.backlogs >= int(filters["min_backlogs"]))
    return list(db.execute(stmt.limit(50)).scalars().all())


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
    """Return a non-streaming answer (text + source: 'llm' | 'fallback')."""
    block = _data_block(db, filters)
    prompt = f"{block}\n\nQUESTION:\n{message}\n\nANSWER:"
    try:
        text = await llm_service.generate(prompt, system=SYSTEM_PROMPT)
        return {"answer": text or _fallback_answer(message, db, filters), "source": "llm"}
    except LLMUnavailable as exc:
        logger.info("Chat fallback engaged: %s", exc)
        return {"answer": _fallback_answer(message, db, filters), "source": "fallback"}


async def stream_answer(db: Session, *, message: str, filters: dict | None = None) -> AsyncIterator[str]:
    """Yield chunks of the answer for SSE."""
    block = _data_block(db, filters)
    prompt = f"{block}\n\nQUESTION:\n{message}\n\nANSWER:"
    try:
        async for chunk in llm_service.stream(prompt, system=SYSTEM_PROMPT):
            yield chunk
    except LLMUnavailable:
        yield _fallback_answer(message, db, filters)
