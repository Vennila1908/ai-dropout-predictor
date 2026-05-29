"""Structured-ish logging setup. Plain text for dev, JSON-friendly for prod-ish."""

from __future__ import annotations

import logging
import sys

from app.core.config import settings


_FMT_DEV = "%(asctime)s %(levelname)-7s %(name)s — %(message)s"
_FMT_PROD = '{"ts":"%(asctime)s","lvl":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}'


def configure_logging() -> None:
    """Idempotently configure the root logger based on APP_ENV."""
    fmt = _FMT_DEV if settings.app_env == "development" else _FMT_PROD
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S"))

    root = logging.getLogger()
    if any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        return  # already configured (e.g. uvicorn reload)

    root.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    root.addHandler(handler)

    for noisy in ("uvicorn.access", "sqlalchemy.engine", "httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
