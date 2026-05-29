"""Standalone CLI to train the baseline model and persist the artifact.

Usage:
    python ml/training_scripts/train_baseline.py \
        --dataset datasets/sample_students.csv \
        --output  ml/artifacts
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Train the dropout-risk baseline model.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=repo_root / "datasets" / "sample_students.csv",
        help="CSV file used for training.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=repo_root / "ml" / "artifacts",
        help="Directory where model.joblib + model_meta.json will be written.",
    )
    args = parser.parse_args()

    # The training code lives inside the backend app for code reuse with
    # the FastAPI service. We add backend/ to sys.path so this CLI can
    # import it without installing the package.
    sys.path.insert(0, str(repo_root / "backend"))

    os.environ["ML_ARTIFACT_DIR"] = str(args.output.resolve())
    os.environ["ML_DEFAULT_DATASET"] = str(args.dataset.resolve())

    from app.ml.train import train_from_dataset  # noqa: E402

    if not args.dataset.exists():
        print(f"ERR: dataset not found at {args.dataset}", file=sys.stderr)
        return 2

    args.output.mkdir(parents=True, exist_ok=True)
    print(f"▶ Training from {args.dataset}")
    meta = train_from_dataset(args.dataset)
    print(f"✔ Best model: {meta['model_name']}")
    metrics = meta.get("metrics", {})
    print(f"  macro_f1 = {metrics.get('macro_f1'):.4f}, accuracy = {metrics.get('accuracy'):.4f}")
    print(f"  artifact written to {args.output / 'model.joblib'}")

    print("\nLeaderboard:")
    for row in meta.get("leaderboard", []):
        print(f"  - {row['model']:<28s} macro_f1 = {row['macro_f1']:.4f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
