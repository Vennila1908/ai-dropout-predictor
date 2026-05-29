"""Feature engineering — turn a Student record into a numeric feature vector.

The same code path is used at training time and inference time so the two
never drift.
"""

from __future__ import annotations

from typing import Any, Mapping

import numpy as np
import pandas as pd

from app.models.student import Student


FEATURE_COLUMNS: list[str] = [
    "attendance_pct",
    "internal_marks",
    "semester_marks",
    "backlogs",
    "fee_delay_days",
    "fee_paid",
    "age",
    "semester",
    "financial_status_ord",
    "placement_readiness_ord",
    "engagement_score",
]

CLASS_LABELS: list[str] = ["low", "medium", "high"]


def _ord(value: str | None, mapping: dict[str, int], default: int = 1) -> int:
    if value is None:
        return default
    return mapping.get(str(value).lower(), default)


_FIN_ORD = {"low": 0, "medium": 1, "high": 2}
_PLACE_ORD = {"low": 0, "medium": 1, "high": 2}


def engagement_score(attendance_pct: float, extracurricular: str | None, behavioral_indicators: str | None) -> float:
    """Heuristic 0..1 score combining attendance + extracurricular activity + behavior."""
    attendance = max(0.0, min(1.0, (attendance_pct or 0) / 100.0))
    extra_len = len(extracurricular or "")
    extra_norm = min(1.0, extra_len / 100.0)
    bad_signals = ("warning", "fight", "absent", "late", "discipline", "complaint")
    behavior_clean = 1.0
    if behavioral_indicators:
        low = behavioral_indicators.lower()
        if any(sig in low for sig in bad_signals):
            behavior_clean = 0.0
    return round(0.6 * attendance + 0.3 * extra_norm + 0.1 * behavior_clean, 4)


def student_to_features(student: Student | Mapping[str, Any]) -> dict[str, float]:
    """Convert a :class:`Student` ORM (or a mapping) to a feature dict."""
    g = (lambda k, default=None: getattr(student, k, default)) if not isinstance(student, Mapping) else student.get

    attendance_pct = float(g("attendance_pct", 0) or 0)
    return {
        "attendance_pct": attendance_pct,
        "internal_marks": float(g("internal_marks", 0) or 0),
        "semester_marks": float(g("semester_marks", 0) or 0),
        "backlogs": int(g("backlogs", 0) or 0),
        "fee_delay_days": int(g("fee_delay_days", 0) or 0),
        "fee_paid": int(bool(g("fee_paid", True))),
        "age": int(g("age", 20) or 20),
        "semester": int(g("semester", 1) or 1),
        "financial_status_ord": _ord(_to_str(g("financial_status", "medium")), _FIN_ORD, 1),
        "placement_readiness_ord": _ord(_to_str(g("placement_readiness", "medium")), _PLACE_ORD, 1),
        "engagement_score": engagement_score(
            attendance_pct, _to_str(g("extracurricular", "")), _to_str(g("behavioral_indicators", ""))
        ),
    }


def _to_str(v: Any) -> str:
    if v is None:
        return ""
    if hasattr(v, "value"):
        return str(v.value)
    return str(v)


def features_dataframe(records: list[Mapping[str, Any]]) -> pd.DataFrame:
    """Convert a list of student-like records to a feature DataFrame."""
    rows = [student_to_features(r) for r in records]
    df = pd.DataFrame(rows, columns=FEATURE_COLUMNS)
    return df


def label_for(record: Mapping[str, Any]) -> str:
    """Synthetic rule-based label used by the dataset generator and by tests."""
    attendance = float(record.get("attendance_pct", 0) or 0)
    backlogs = int(record.get("backlogs", 0) or 0)
    internal = float(record.get("internal_marks", 0) or 0)
    fee_delay = int(record.get("fee_delay_days", 0) or 0)

    if attendance < 60 or backlogs >= 3 or internal < 40:
        return "high"
    if attendance < 75 or backlogs >= 1 or internal < 55 or fee_delay > 30:
        return "medium"
    return "low"


def feature_array(records: list[Mapping[str, Any]]) -> np.ndarray:
    return features_dataframe(records).to_numpy(dtype=float)
