"""Auth happy-path tests."""

from __future__ import annotations


def test_health(app_client) -> None:
    r = app_client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] in {"ok", "degraded"}


def test_login_and_me(app_client, admin_token, auth_headers) -> None:
    me = app_client.get("/api/v1/auth/me", headers=auth_headers)
    assert me.status_code == 200
    body = me.json()
    assert body["email"] in {"test-admin@example.com", "admin@example.com"}
    assert body["role"] == "admin"


def test_login_bad_password(app_client, admin_token) -> None:  # noqa: ARG001
    r = app_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "wrong"},
    )
    assert r.status_code in {401, 429}
