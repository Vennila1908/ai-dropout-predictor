"""Student CRUD smoke tests."""

from __future__ import annotations

import uuid


def _payload() -> dict:
    return {
        "roll_no": f"T{uuid.uuid4().hex[:8].upper()}",
        "name": "Test Student",
        "age": 20,
        "gender": "M",
        "department_id": None,
        "semester": 3,
        "attendance_pct": 72.5,
        "internal_marks": 55,
        "semester_marks": 60,
        "backlogs": 1,
        "fee_paid": True,
        "fee_delay_days": 0,
        "financial_status": "medium",
        "family_background": "stable",
        "behavioral_indicators": "calm",
        "extracurricular": "music",
        "placement_readiness": "medium",
        "counselor_remarks": "",
        "faculty_notes": "",
    }


def test_create_get_update_list(app_client, auth_headers) -> None:
    payload = _payload()
    r = app_client.post("/api/v1/students", json=payload, headers=auth_headers)
    assert r.status_code in {200, 201}, r.text
    sid = r.json()["id"]

    g = app_client.get(f"/api/v1/students/{sid}", headers=auth_headers)
    assert g.status_code == 200
    assert g.json()["roll_no"] == payload["roll_no"]

    p = app_client.patch(f"/api/v1/students/{sid}", json={"backlogs": 4}, headers=auth_headers)
    assert p.status_code == 200
    assert p.json()["backlogs"] == 4

    listed = app_client.get("/api/v1/students?page=1&page_size=10", headers=auth_headers)
    assert listed.status_code == 200
    assert listed.json()["total"] >= 1


def test_student_can_load_own_record(app_client, auth_headers) -> None:
    payload = _payload()
    created = app_client.post("/api/v1/students", json=payload, headers=auth_headers)
    assert created.status_code in {200, 201}, created.text

    user = app_client.post(
        "/api/v1/users",
        json={
            "email": f"{payload['roll_no'].lower()}@example.com",
            "password": "StudentOwn1!",
            "full_name": payload["name"],
            "role": "student",
            "roll_no": payload["roll_no"],
        },
        headers=auth_headers,
    )
    assert user.status_code == 201, user.text

    login = app_client.post(
        "/api/v1/auth/login",
        json={"email": f"{payload['roll_no'].lower()}@example.com", "password": "StudentOwn1!"},
    )
    assert login.status_code == 200, login.text

    own = app_client.get(
        "/api/v1/students/me",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )
    assert own.status_code == 200
    assert own.json()["roll_no"] == payload["roll_no"]
    assert own.json()["attendance_pct"] == payload["attendance_pct"]


def test_student_me_includes_department(app_client, auth_headers) -> None:
    dept = app_client.post(
        "/api/v1/departments",
        json={"name": "Bachelor of Science in Computer Programming", "code": "BSCP"},
        headers=auth_headers,
    )
    assert dept.status_code == 201, dept.text
    dept_id = dept.json()["id"]

    payload = _payload()
    payload["department_id"] = dept_id
    created = app_client.post("/api/v1/students", json=payload, headers=auth_headers)
    assert created.status_code in {200, 201}, created.text

    user = app_client.post(
        "/api/v1/users",
        json={
            "email": f"{payload['roll_no'].lower()}@example.com",
            "password": "StudentOwn1!",
            "full_name": payload["name"],
            "role": "student",
            "roll_no": payload["roll_no"],
        },
        headers=auth_headers,
    )
    assert user.status_code == 201, user.text

    login = app_client.post(
        "/api/v1/auth/login",
        json={"email": f"{payload['roll_no'].lower()}@example.com", "password": "StudentOwn1!"},
    )
    assert login.status_code == 200, login.text

    own = app_client.get(
        "/api/v1/students/me",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )
    assert own.status_code == 200
    body = own.json()
    assert body["department_id"] == dept_id
    assert body["department_code"] == "BSCP"
    assert body["department_name"] == "Bachelor of Science in Computer Programming"
