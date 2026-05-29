"""Light wrappers around scikit-learn preprocessors."""

from __future__ import annotations

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.ml.features import FEATURE_COLUMNS


def build_preprocessor() -> ColumnTransformer:
    """All features are already numeric → just standardize them."""
    return ColumnTransformer(
        transformers=[("scale", StandardScaler(), FEATURE_COLUMNS)],
        remainder="drop",
    )


def wrap_with_preprocessor(estimator) -> Pipeline:
    return Pipeline(steps=[("pre", build_preprocessor()), ("clf", estimator)])
