"""Inference helper — single point of access for the trained model."""

from __future__ import annotations

import threading
from typing import Any

import numpy as np
import pandas as pd

from app.core.config import settings
from app.core.logging import get_logger
from app.ml.features import CLASS_LABELS, FEATURE_COLUMNS, features_dataframe
from app.ml.registry import has_artifact, load_artifact
from app.ml.train import train_from_dataset


logger = get_logger(__name__)

_LOCK = threading.Lock()
_MODEL: Any | None = None
_META: dict = {}


def _ensure_loaded() -> None:
    global _MODEL, _META
    if _MODEL is not None:
        return
    with _LOCK:
        if _MODEL is not None:
            return
        if not has_artifact():
            logger.info("No model artifact found — training from default dataset.")
            try:
                train_from_dataset(settings.default_dataset_path)
            except FileNotFoundError as exc:
                logger.error("Cannot auto-train: %s", exc)
                raise
        _MODEL, _META = load_artifact()
        if _MODEL is None:
            raise RuntimeError("Model artifact present but failed to load.")


def model_meta() -> dict:
    _ensure_loaded()
    return _META


def reset_cache() -> None:
    """Drop the in-process model cache (e.g. after a retraining)."""
    global _MODEL, _META
    with _LOCK:
        _MODEL, _META = None, {}


def predict_one(record: dict) -> dict:
    """Run a single prediction. Returns ``{risk_level, confidence, probabilities, features}``."""
    _ensure_loaded()
    df = features_dataframe([record])
    proba = _MODEL.predict_proba(df)[0]
    idx = int(np.argmax(proba))
    risk = CLASS_LABELS[idx] if idx < len(CLASS_LABELS) else "medium"
    return {
        "risk_level": risk,
        "confidence": float(proba[idx]),
        "probabilities": {lbl: float(p) for lbl, p in zip(CLASS_LABELS, proba)},
        "features": df.iloc[0].to_dict(),
        "model_version": _META.get("model_name", "unknown"),
    }


def predict_many(records: list[dict]) -> list[dict]:
    _ensure_loaded()
    if not records:
        return []
    df = features_dataframe(records)
    proba = _MODEL.predict_proba(df)
    out: list[dict] = []
    for i, p in enumerate(proba):
        idx = int(np.argmax(p))
        risk = CLASS_LABELS[idx] if idx < len(CLASS_LABELS) else "medium"
        out.append(
            {
                "risk_level": risk,
                "confidence": float(p[idx]),
                "probabilities": {lbl: float(pp) for lbl, pp in zip(CLASS_LABELS, p)},
                "features": df.iloc[i].to_dict(),
                "model_version": _META.get("model_name", "unknown"),
            }
        )
    return out


def feature_means() -> dict[str, float]:
    """Cohort-level feature means stored in the meta if present, else zeros."""
    return _META.get("feature_means") or {f: 0.0 for f in FEATURE_COLUMNS}
