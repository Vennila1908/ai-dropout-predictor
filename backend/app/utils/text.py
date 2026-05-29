"""Tiny text-cleanup helpers used by parsers and the LLM service."""

from __future__ import annotations

import json
import re


_WHITESPACE_RE = re.compile(r"\s+")


def squash_whitespace(s: str) -> str:
    return _WHITESPACE_RE.sub(" ", s).strip()


def truncate(s: str, max_len: int = 500) -> str:
    s = s or ""
    return s if len(s) <= max_len else s[: max_len - 1] + "…"


def extract_json_block(text: str) -> dict | list | None:
    """Best-effort: return the first JSON object/array embedded in ``text``.

    Tries direct parse first, then `{...}` / `[...]` slice, otherwise None.
    """
    text = (text or "").strip()
    if not text:
        return None
    for trial in (text, _between(text, "{", "}"), _between(text, "[", "]")):
        if trial is None:
            continue
        try:
            return json.loads(trial)
        except (json.JSONDecodeError, ValueError):
            continue
    return None


def _between(s: str, open_c: str, close_c: str) -> str | None:
    start = s.find(open_c)
    end = s.rfind(close_c)
    if start == -1 or end == -1 or end <= start:
        return None
    return s[start : end + 1]
