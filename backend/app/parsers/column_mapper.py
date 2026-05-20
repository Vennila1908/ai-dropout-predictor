"""Fuzzy column-name → student-field mapping using rapidfuzz."""

from __future__ import annotations

from typing import Iterable

from rapidfuzz import fuzz, process


# Target fields the system understands. Order matters for tie-breaking.
TARGET_FIELDS: list[str] = [
    "roll_no",
    "name",
    "age",
    "gender",
    "department_code",
    "semester",
    "attendance_pct",
    "internal_marks",
    "semester_marks",
    "backlogs",
    "fee_paid",
    "fee_delay_days",
    "financial_status",
    "family_background",
    "behavioral_indicators",
    "extracurricular",
    "placement_readiness",
    "counselor_remarks",
]

# Hand-curated synonyms — these are matched first, before fuzzy fallback.
SYNONYMS: dict[str, list[str]] = {
    "roll_no": ["roll", "rollno", "roll number", "regno", "registration", "student id", "id", "studentid"],
    "name": ["student name", "full name", "student", "fullname"],
    "age": ["age", "years"],
    "gender": ["gender", "sex"],
    "department_code": ["department", "dept", "branch", "stream", "dept code", "department code"],
    "semester": ["semester", "sem", "term", "year"],
    "attendance_pct": ["attendance", "attendance %", "attendance percentage", "attend pct", "att%", "att"],
    "internal_marks": ["internal", "internal marks", "internals", "ia marks", "ca marks"],
    "semester_marks": ["sem marks", "semester marks", "final marks", "external marks", "ese", "marks"],
    "backlogs": ["backlogs", "arrears", "kt", "pending subjects", "supplementary"],
    "fee_paid": ["fee paid", "feepaid", "fees paid", "paid"],
    "fee_delay_days": ["fee delay", "fee delay days", "days delayed", "fee overdue", "due days"],
    "financial_status": ["financial status", "income level", "family income", "economic status"],
    "family_background": ["family", "family background", "background", "household"],
    "behavioral_indicators": ["behavior", "behaviour", "behavioral", "behavioural", "discipline"],
    "extracurricular": ["extracurricular", "activities", "clubs", "sports"],
    "placement_readiness": ["placement", "placement readiness", "career readiness"],
    "counselor_remarks": ["remarks", "counselor remarks", "counsellor remarks", "comments"],
}


def _normalize(s: str) -> str:
    return s.strip().lower().replace("-", " ").replace("_", " ")


def suggest_mapping(source_columns: Iterable[str]) -> list[dict]:
    """Suggest a target field for each source column.

    Returns a list of dicts ``{source, target, score, candidates}`` where
    ``score`` is in 0..100. ``target`` is None when nothing scores above 50.
    """
    suggestions: list[dict] = []
    used_targets: set[str] = set()

    for source in source_columns:
        norm = _normalize(source)

        # 1) Synonym hit short-circuits.
        synonym_hit: tuple[str, float] | None = None
        for target, syns in SYNONYMS.items():
            if target in used_targets:
                continue
            best = max((fuzz.WRatio(norm, _normalize(s)) for s in syns), default=0)
            if best >= 90 and (synonym_hit is None or best > synonym_hit[1]):
                synonym_hit = (target, float(best))
        if synonym_hit:
            suggestions.append(
                {
                    "source": source,
                    "target": synonym_hit[0],
                    "score": synonym_hit[1],
                    "candidates": _top_candidates(norm, used_targets),
                }
            )
            used_targets.add(synonym_hit[0])
            continue

        # 2) Fuzzy match against the target field names directly.
        choices = [t for t in TARGET_FIELDS if t not in used_targets]
        if not choices:
            suggestions.append({"source": source, "target": None, "score": 0.0, "candidates": []})
            continue
        best = process.extractOne(norm, [_normalize(c) for c in choices], scorer=fuzz.WRatio)
        if best is None or best[1] < 50:
            suggestions.append(
                {
                    "source": source,
                    "target": None,
                    "score": float(best[1]) if best else 0.0,
                    "candidates": _top_candidates(norm, used_targets),
                }
            )
            continue
        target = choices[best[2]]
        suggestions.append(
            {
                "source": source,
                "target": target,
                "score": float(best[1]),
                "candidates": _top_candidates(norm, used_targets),
            }
        )
        used_targets.add(target)
    return suggestions


def _top_candidates(norm_source: str, used: set[str], n: int = 3) -> list[str]:
    pool = [t for t in TARGET_FIELDS if t not in used]
    if not pool:
        return []
    ranked = process.extract(norm_source, pool, scorer=fuzz.WRatio, limit=n)
    return [c[0] for c in ranked]
