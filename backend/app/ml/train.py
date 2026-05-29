"""Training pipeline — picks the best of {LogReg, RF, GB, XGB?} by macro-F1.

Used by:
* `POST /api/v1/ml/train` (background task)
* The standalone CLI in `ml/training_scripts/train_baseline.py`
* The synthetic-dataset bootstrapper invoked at first prediction.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split

from app.core.logging import get_logger
from app.ml.features import CLASS_LABELS, FEATURE_COLUMNS, features_dataframe, label_for
from app.ml.preprocess import wrap_with_preprocessor
from app.ml.registry import save_artifact


logger = get_logger(__name__)


def _candidates() -> list[tuple[str, Any]]:
    cands: list[tuple[str, Any]] = [
        ("LogisticRegression", LogisticRegression(max_iter=400, multi_class="auto")),
        ("RandomForestClassifier", RandomForestClassifier(n_estimators=200, max_depth=12, random_state=42)),
        ("GradientBoostingClassifier", GradientBoostingClassifier(n_estimators=200, max_depth=4, random_state=42)),
    ]
    try:
        from xgboost import XGBClassifier

        cands.append(
            (
                "XGBClassifier",
                XGBClassifier(
                    n_estimators=300,
                    max_depth=5,
                    learning_rate=0.08,
                    objective="multi:softprob",
                    num_class=3,
                    eval_metric="mlogloss",
                    random_state=42,
                    tree_method="hist",
                ),
            )
        )
    except Exception as exc:  # noqa: BLE001
        logger.info("XGBoost not available, skipping: %s", exc)
    return cands


def _load_dataframe(dataset_path: Path) -> pd.DataFrame:
    if not dataset_path.exists():
        raise FileNotFoundError(f"Training dataset not found: {dataset_path}")
    df = pd.read_csv(dataset_path)
    df.columns = [c.strip() for c in df.columns]
    return df


def _ensure_label(df: pd.DataFrame) -> pd.DataFrame:
    if "risk_level" in df.columns:
        return df
    df = df.copy()
    df["risk_level"] = [label_for(rec) for rec in df.to_dict(orient="records")]
    return df


def _feature_importance(model, feature_names: list[str]) -> list[dict]:
    """Extract feature importances if available."""
    inner = getattr(model, "named_steps", {}).get("clf", model)
    importances: np.ndarray | None = None
    if hasattr(inner, "feature_importances_"):
        importances = np.asarray(inner.feature_importances_, dtype=float)
    elif hasattr(inner, "coef_"):
        coef = np.asarray(inner.coef_)
        importances = np.abs(coef).mean(axis=0) if coef.ndim > 1 else np.abs(coef)
    if importances is None or len(importances) != len(feature_names):
        return []
    pairs = sorted(zip(feature_names, importances), key=lambda x: -x[1])
    return [{"feature": k, "importance": float(v)} for k, v in pairs]


def train_from_dataset(dataset_path: Path) -> dict:
    """Train candidates on ``dataset_path``, save the best, return its meta dict."""
    df = _ensure_label(_load_dataframe(dataset_path))
    df = df.dropna(subset=["risk_level"])
    feature_df = features_dataframe(df.to_dict(orient="records"))
    y_raw = df["risk_level"].astype(str).str.lower()

    # Map labels to integers in a stable order.
    label_to_idx = {lab: i for i, lab in enumerate(CLASS_LABELS)}
    y = y_raw.map(label_to_idx).fillna(label_to_idx["medium"]).astype(int).to_numpy()

    X_train, X_test, y_train, y_test = train_test_split(
        feature_df, y, test_size=0.2, stratify=y, random_state=42
    )

    best_name, best_model, best_score, best_metrics = "", None, -1.0, {}
    leaderboard: list[dict] = []
    for name, est in _candidates():
        try:
            pipe = wrap_with_preprocessor(est)
            pipe.fit(X_train, y_train)
            preds = pipe.predict(X_test)
            macro_f1 = f1_score(y_test, preds, average="macro")
            leaderboard.append({"model": name, "macro_f1": float(macro_f1)})
            logger.info("Candidate %s — macro_f1=%.4f", name, macro_f1)
            if macro_f1 > best_score:
                best_score = macro_f1
                best_name = name
                best_model = pipe
                report = classification_report(
                    y_test, preds, target_names=CLASS_LABELS, output_dict=True, zero_division=0
                )
                best_metrics = {
                    "accuracy": float((preds == y_test).mean()),
                    "macro_f1": float(macro_f1),
                    "per_class_f1": {
                        lab: float(report[lab]["f1-score"]) for lab in CLASS_LABELS if lab in report
                    },
                    "report": report,
                }
        except Exception as exc:  # noqa: BLE001
            logger.error("Candidate %s failed: %s", name, exc)

    if best_model is None:
        raise RuntimeError("No model could be trained — check dataset.")

    cm = confusion_matrix(y_test, best_model.predict(X_test)).tolist()
    feature_means = {col: float(feature_df[col].mean()) for col in FEATURE_COLUMNS}
    meta = {
        "model_name": best_name,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "feature_list": FEATURE_COLUMNS,
        "metrics": best_metrics,
        "confusion_matrix": cm,
        "feature_importances": _feature_importance(best_model, FEATURE_COLUMNS),
        "feature_means": feature_means,
        "class_labels": CLASS_LABELS,
        "leaderboard": leaderboard,
        "dataset": str(dataset_path),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
    }
    save_artifact(best_model, meta)
    return meta
