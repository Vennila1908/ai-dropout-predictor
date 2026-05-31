"""Centralized typed settings loaded from the environment / .env.

All other modules import :class:`settings` from here. Never read os.environ
directly elsewhere — that keeps configuration changes in one place and lets us
unit-test with overrides.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    """Application settings sourced from env vars / `.env`."""

    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ─── App ────────────────────────────────────────────────────────────────
    app_name: str = "AI Dropout Predictor"
    app_env: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    # ─── Auth ──────────────────────────────────────────────────────────────
    secret_key: str = Field(default="change-me-please-this-is-only-for-local-dev")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 60 * 24 * 7
    password_reset_token_expire_minutes: int = 30

    # ─── DB ────────────────────────────────────────────────────────────────
    database_url: str = "sqlite:///./app.db"

    # ─── CORS ──────────────────────────────────────────────────────────────
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://localhost:8080",
            "http://127.0.0.1:5173",
        ]
    )

    # ─── Uploads ───────────────────────────────────────────────────────────
    upload_dir: str = "./uploads"
    max_upload_bytes: int = 10 * 1024 * 1024  # 10 MB

    # ─── ML artifacts ──────────────────────────────────────────────────────
    ml_artifact_dir: str = "../ml/artifacts"
    ml_default_dataset: str = "../datasets/sample_students.csv"

    # ─── LLM ───────────────────────────────────────────────────────────────
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "phi3"
    llm_timeout_seconds: int = 60
    llm_max_tokens: int = 512

    # ─── Rate limits ───────────────────────────────────────────────────────
    rate_limit_login: str = "10/minute"
    rate_limit_chat: str = "30/minute"

    # ─── Seed ──────────────────────────────────────────────────────────────
    seed_admin_email: str = "admin@example.com"
    seed_admin_password: str = "Admin@123"
    seed_student_password: str = "Student@123"

    # ─── Validators ────────────────────────────────────────────────────────
    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors_origins(cls, v):
        """Accept JSON array, comma-separated string, single URL, or list."""
        if v is None or v == "":
            return []
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            s = v.strip()
            if s == "*":
                return ["*"]
            if s.startswith("["):
                try:
                    return json.loads(s)
                except json.JSONDecodeError:
                    pass
            return [item.strip() for item in s.split(",") if item.strip()]
        return v

    @property
    def upload_path(self) -> Path:
        """Absolute path to the upload directory (auto-created on access)."""
        p = (BACKEND_DIR / self.upload_dir).resolve() if not Path(self.upload_dir).is_absolute() else Path(self.upload_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def ml_artifact_path(self) -> Path:
        """Absolute path to ml_artifact_dir (auto-created on access)."""
        p = (BACKEND_DIR / self.ml_artifact_dir).resolve() if not Path(self.ml_artifact_dir).is_absolute() else Path(self.ml_artifact_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def default_dataset_path(self) -> Path:
        return (BACKEND_DIR / self.ml_default_dataset).resolve() if not Path(self.ml_default_dataset).is_absolute() else Path(self.ml_default_dataset)

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    """Cached accessor so settings parsing happens exactly once."""
    return Settings()


settings = get_settings()
