"""Explainability — SHAP when possible, deterministic fallback otherwise."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.core.logging import get_logger
from app.ml.features import CLASS_LABELS, FEATURE_COLUMNS


logger = get_logger(__name__)


_FRIENDLY = {
    "attendance_pct": "Attendance %",
    "internal_marks": "Internal marks",
    "semester_marks": "Semester marks",
    "backlogs": "Active backlogs",
    "fee_delay_days": "Fee delay (days)",
    "fee_paid": "Fee paid",
    "age": "Age",
    "semester": "Semester",
    "financial_status_ord": "Financial status",
    "placement_readiness_ord": "Placement readiness",
    "engagement_score": "Engagement score",
}

_HIGHER_IS_RISKIER = {"backlogs", "fee_delay_days"}
_LOWER_IS_RISKIER = {
    "attendance_pct",
    "internal_marks",
    "semester_marks",
    "engagement_score",
    "placement_readiness_ord",
    "financial_status_ord",
}


def _direction(feature: str, value: float, mean: float, contribution: float) -> str:
    """Decide whether the feature is pushing risk up or down."""
    if feature in _HIGHER_IS_RISKIER:
        return "increases_risk" if value > mean else "decreases_risk"
    if feature in _LOWER_IS_RISKIER:
        return "increases_risk" if value < mean else "decreases_risk"
    if abs(contribution) < 1e-6:
        return "neutral"
    return "increases_risk" if contribution > 0 else "decreases_risk"


def _means_from_meta(meta: dict) -> dict[str, float]:
    means = meta.get("feature_means") or {}
    return {f: float(means.get(f, 0.0)) for f in FEATURE_COLUMNS}


def _fallback_contributions(
    features: dict[str, float], meta: dict
) -> list[tuple[str, float, float]]:
    """`(value − mean) × importance`-style contribution score."""
    importances = {row["feature"]: float(row["importance"]) for row in meta.get("feature_importances", [])}
    means = _means_from_meta(meta)
    out: list[tuple[str, float, float]] = []
    for f in FEATURE_COLUMNS:
        v = float(features.get(f, 0.0) or 0.0)
        m = means.get(f, 0.0)
        imp = importances.get(f, 0.0)
        contribution = (v - m) * imp
        # Flip sign so positive = "increases risk".
        if f in _LOWER_IS_RISKIER:
            contribution = -contribution
        out.append((f, v, contribution))
    out.sort(key=lambda x: -abs(x[2]))
    return out


def explain_one(model: Any, features: dict[str, float], meta: dict) -> dict:
    """Return an explanation dict for a single prediction.

    {
      "top_factors": [{feature, value, contribution, direction}, ...],
      "narrative": "..."
    }
    """
    contributions: list[tuple[str, float, float]]
    used_shap = False
    try:
        import shap

        inner = getattr(model, "named_steps", {}).get("clf", model)
        if any(t in type(inner).__name__ for t in ("Forest", "Boost", "Tree", "XGB")):
            df = pd.DataFrame([features], columns=FEATURE_COLUMNS)
            transformed = model.named_steps["pre"].transform(df) if hasattr(model, "named_steps") else df.to_numpy()
            explainer = shap.TreeExplainer(inner)
            sv = explainer.shap_values(transformed)
            arr = np.asarray(sv)
            if arr.ndim == 3:
                idx = int(np.argmax(model.predict_proba(df)[0]))
                values = arr[idx, 0, :] if arr.shape[0] == len(CLASS_LABELS) else arr[0, idx, :]
            else:
                values = arr[0]
            contributions = [
                (FEATURE_COLUMNS[i], float(features.get(FEATURE_COLUMNS[i], 0.0)), float(values[i]))
                for i in range(len(FEATURE_COLUMNS))
            ]
            contributions.sort(key=lambda x: -abs(x[2]))
            used_shap = True
    except Exception as exc:  # noqa: BLE001
        logger.debug("SHAP unavailable / failed; falling back: %s", exc)

    if not used_shap:
        contributions = _fallback_contributions(features, meta)

    means = _means_from_meta(meta)
    top_factors = []
    for f, v, c in contributions[:6]:
        top_factors.append(
            {
                "feature": f,
                "value": v,
                "contribution": float(round(c, 4)),
                "direction": _direction(f, v, means.get(f, 0.0), c),
            }
        )

    return {
        "top_factors": top_factors,
        "narrative": _build_narrative(features, top_factors, means),
    }


def _build_narrative(features: dict[str, float], factors: list[dict], means: dict[str, float]) -> str:
    if not factors:
        return "No strongly contributing features detected for this student."
    bits: list[str] = []
    for f in factors[:3]:
        name = _FRIENDLY.get(f["feature"], f["feature"])
        v = f["value"]
        m = means.get(f["feature"], 0.0)
        if f["direction"] == "increases_risk":
            comp = "below" if f["feature"] in _LOWER_IS_RISKIER else "above"
            bits.append(f"{name} = {_fmt(v)} ({comp} cohort avg of {_fmt(m)})")
        elif f["direction"] == "decreases_risk":
            bits.append(f"{name} = {_fmt(v)} (a protective factor)")
    if not bits:
        return "Risk drivers are roughly balanced across all features."
    return "Top contributing factors: " + "; ".join(bits) + "."


def _fmt(v: float) -> str:
    if isinstance(v, float):
        return f"{v:.1f}" if abs(v) < 100 else f"{v:.0f}"
    return str(v)
