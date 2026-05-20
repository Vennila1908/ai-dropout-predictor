"""PDF parser — extracts the first detected table.

Tries pdfplumber first (good with line-grids), then PyMuPDF as a fallback
(text-only — heuristic table reconstruction).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.logging import get_logger


logger = get_logger(__name__)


def _table_to_records(table: list[list[str]]) -> tuple[list[str], list[dict[str, Any]]]:
    if not table or len(table) < 2:
        return [], []
    headers = [(c or "").strip() or f"col_{i}" for i, c in enumerate(table[0])]
    records: list[dict[str, Any]] = []
    for row in table[1:]:
        rec: dict[str, Any] = {}
        for i, h in enumerate(headers):
            rec[h] = (row[i] or "").strip() if i < len(row) else ""
        records.append(rec)
    return headers, records


def parse_pdf(path: Path, *, max_preview_rows: int = 25) -> tuple[list[str], list[dict[str, Any]], int]:
    """Return ``(columns, preview, total_rows)`` from the first table found."""
    headers: list[str] = []
    rows: list[dict[str, Any]] = []

    try:
        import pdfplumber

        with pdfplumber.open(str(path)) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables() or []
                for tbl in tables:
                    h, r = _table_to_records(tbl)
                    if h:
                        headers = headers or h
                        rows.extend(r)
        if rows:
            return headers, rows[:max_preview_rows], len(rows)
    except Exception as exc:  # noqa: BLE001
        logger.warning("pdfplumber failed; falling back to PyMuPDF: %s", exc)

    try:
        import fitz  # PyMuPDF

        with fitz.open(str(path)) as doc:
            text_lines: list[str] = []
            for page in doc:
                text_lines.extend(line for line in page.get_text("text").splitlines() if line.strip())
        if text_lines:
            split = [ln.split() for ln in text_lines]
            cols = [f"col_{i}" for i in range(max((len(s) for s in split), default=1))]
            rows = [dict(zip(cols, parts + [""] * (len(cols) - len(parts)))) for parts in split]
            return cols, rows[:max_preview_rows], len(rows)
    except Exception as exc:  # noqa: BLE001
        logger.error("PyMuPDF parse also failed: %s", exc)

    return [], [], 0


def iter_pdf_rows(path: Path) -> tuple[list[str], list[dict[str, Any]]]:
    headers, _, _ = parse_pdf(path, max_preview_rows=10**9)
    headers, rows, _ = parse_pdf(path, max_preview_rows=10**9)
    return headers, rows
