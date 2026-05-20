"""Thin facade around `app.ml.explain` so endpoints stay decoupled from ML internals."""

from __future__ import annotations

from typing import Any

from app.ml.explain import explain_one
from app.ml.registry import load_artifact


def explain(features: dict[str, Any]) -> dict[str, Any]:
    model, meta = load_artifact()
    if model is None:
        return {"top_factors": [], "narrative": "No trained model available."}
    return explain_one(model, features, meta)
