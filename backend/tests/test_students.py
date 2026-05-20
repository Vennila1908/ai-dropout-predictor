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

    l = app_client.get("/api/v1/students?page=1&page_size=10", headers=auth_headers)
    assert l.status_code == 200
    assert l.json()["total"] >= 1
