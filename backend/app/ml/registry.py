"""On-disk model artifact registry — single artifact per process."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib

from app.core.config import settings
from app.core.logging import get_logger


logger = get_logger(__name__)


ARTIFACT_FILENAME = "model.joblib"
META_FILENAME = "model_meta.json"


def artifact_path() -> Path:
    return settings.ml_artifact_path / ARTIFACT_FILENAME


def meta_path() -> Path:
    return settings.ml_artifact_path / META_FILENAME


def save_artifact(model: Any, meta: dict) -> None:
    p = artifact_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, p)
    meta = {**meta, "trained_at": meta.get("trained_at") or datetime.now(timezone.utc).isoformat()}
    meta_path().write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")
    logger.info("Saved model artifact to %s", p)


def load_artifact() -> tuple[Any | None, dict]:
    p = artifact_path()
    if not p.exists():
        return None, {}
    try:
        model = joblib.load(p)
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to load model artifact: %s", exc)
        return None, {}
    meta: dict = {}
    if meta_path().exists():
        try:
            meta = json.loads(meta_path().read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to load model meta: %s", exc)
    return model, meta


def has_artifact() -> bool:
    return artifact_path().exists()
