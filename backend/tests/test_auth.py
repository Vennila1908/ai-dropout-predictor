"""Auth happy-path tests."""

from __future__ import annotations

from uuid import uuid4


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


def test_forgot_password_reset_flow(app_client, auth_headers) -> None:
    email = f"reset-flow-{uuid4().hex}@example.com"
    created = app_client.post(
        "/api/v1/users",
        json={"email": email, "password": "OldPass1!", "full_name": "Reset Flow", "role": "faculty"},
        headers=auth_headers,
    )
    assert created.status_code == 201

    request = app_client.post(
        "/api/v1/auth/forgot-password",
        json={"email": email},
        headers={"origin": "http://localhost:5173"},
    )
    assert request.status_code == 200
    token = request.json()["reset_token"]

    reset = app_client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "password": "NewPass1!"},
    )
    assert reset.status_code == 200

    old_login = app_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "OldPass1!"},
    )
    assert old_login.status_code in {401, 429}

    new_login = app_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "NewPass1!"},
    )
    assert new_login.status_code == 200


def test_reset_token_is_single_use(app_client, auth_headers) -> None:
    email = f"reset-single-use-{uuid4().hex}@example.com"
    created = app_client.post(
        "/api/v1/users",
        json={"email": email, "password": "OldPass1!", "full_name": "Reset Single Use", "role": "faculty"},
        headers=auth_headers,
    )
    assert created.status_code == 201

    request = app_client.post(
        "/api/v1/auth/forgot-password",
        json={"email": email},
    )
    assert request.status_code == 200
    token = request.json()["reset_token"]

    first = app_client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "password": "NewPass2!"},
    )
    assert first.status_code == 200

    second = app_client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "password": "NewPass3!"},
    )
    assert second.status_code == 400
