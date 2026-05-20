"""Excel parser (xlsx/xls) via openpyxl-backed pandas."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def parse_excel(path: Path, *, max_preview_rows: int = 25) -> tuple[list[str], list[dict[str, Any]], int]:
    df = pd.read_excel(path, dtype=str, keep_default_na=False)
    df.columns = [str(c).strip() for c in df.columns]
    return list(df.columns), df.head(max_preview_rows).to_dict(orient="records"), int(df.shape[0])


def iter_excel_rows(path: Path) -> tuple[list[str], list[dict[str, Any]]]:
    df = pd.read_excel(path, dtype=str, keep_default_na=False)
    df.columns = [str(c).strip() for c in df.columns]
    return list(df.columns), df.to_dict(orient="records")
