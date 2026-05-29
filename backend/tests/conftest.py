"""Shared fixtures: in-memory SQLite, fresh app per test, authenticated client."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope="session", autouse=True)
def _isolated_runtime_dirs(tmp_path_factory) -> None:
    """Point uploads + ML artifacts at a tmp dir for the whole session."""
    base = tmp_path_factory.mktemp("runtime")
    os.environ["UPLOAD_DIR"] = str(base / "uploads")
    os.environ["ML_ARTIFACT_DIR"] = str(base / "ml_artifacts")
    os.environ["DATABASE_URL"] = f"sqlite:///{base / 'test.db'}"
    os.environ["SECRET_KEY"] = "test-secret-key"
    os.environ["ML_DEFAULT_DATASET"] = str(base / "no-dataset.csv")  # disables auto-train


@pytest.fixture()
def app_client() -> Generator[TestClient, None, None]:
    # Re-import so the env vars set above are picked up.
    from app.core.config import get_settings
    get_settings.cache_clear()  # type: ignore[attr-defined]

    from app.main import create_app
    app = create_app()
    with TestClient(app) as client:
        yield client


@pytest.fixture()
def admin_token(app_client: TestClient) -> str:
    """Bootstrap-register an admin and return their access token."""
    # Register (allowed if DB has zero users).
    register = app_client.post(
        "/api/v1/auth/register",
        json={"email": "test-admin@example.com", "password": "TestPass1!", "full_name": "Test Admin", "role": "admin"},
    )
    if register.status_code not in (200, 201):
        # Already bootstrapped — fall back to seeded admin if present.
        pass
    login = app_client.post(
        "/api/v1/auth/login",
        json={"email": "test-admin@example.com", "password": "TestPass1!"},
    )
    if login.status_code != 200:
        # Try the seeded admin.
        login = app_client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "Admin@123"},
        )
    assert login.status_code == 200, login.text
    return login.json()["access_token"]


@pytest.fixture()
def auth_headers(admin_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {admin_token}"}
