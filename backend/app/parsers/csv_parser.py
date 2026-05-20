"""CSV parser using pandas (handles encoding detection via chardet)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import chardet
import pandas as pd


def parse_csv(path: Path, *, max_preview_rows: int = 25) -> tuple[list[str], list[dict[str, Any]], int]:
    """Return ``(columns, preview_rows, total_rows)`` from a CSV file."""
    with path.open("rb") as f:
        raw = f.read(64 * 1024)
    detected = chardet.detect(raw) or {}
    encoding = detected.get("encoding") or "utf-8"

    df = pd.read_csv(path, encoding=encoding, dtype=str, keep_default_na=False)
    df.columns = [str(c).strip() for c in df.columns]
    columns = list(df.columns)
    preview = df.head(max_preview_rows).to_dict(orient="records")
    return columns, preview, int(df.shape[0])


def iter_csv_rows(path: Path) -> tuple[list[str], list[dict[str, Any]]]:
    """Read all rows (used at confirm time)."""
    with path.open("rb") as f:
        raw = f.read(64 * 1024)
    encoding = (chardet.detect(raw) or {}).get("encoding") or "utf-8"
    df = pd.read_csv(path, encoding=encoding, dtype=str, keep_default_na=False)
    df.columns = [str(c).strip() for c in df.columns]
    return list(df.columns), df.to_dict(orient="records")
