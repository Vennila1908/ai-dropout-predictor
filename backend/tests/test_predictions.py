"""Prediction smoke tests — auto-trains on a tiny inline dataset."""

from __future__ import annotations

import csv
import os
import uuid
from pathlib import Path


def _seed_dataset(monkeypatch_env: bool = True) -> Path:
    """Write a tiny synthetic dataset and point ML_DEFAULT_DATASET at it."""
    p = Path(os.environ["ML_ARTIFACT_DIR"]).parent / "tiny_students.csv"
    p.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        # roll_no,name,age,gender,department_code,semester,attendance_pct,internal_marks,
        # semester_marks,backlogs,fee_paid,fee_delay_days,financial_status,family_background,
        # behavioral_indicators,extracurricular,placement_readiness,counselor_remarks
        ["S001", "A", 20, "M", "BSCS", 1, 95, 90, 88, 0, True, 0, "high", "", "", "debate club", "high", ""],
        ["S002", "B", 21, "F", "BSCS", 2, 50, 35, 40, 4, False, 60, "low", "", "warning", "", "low", ""],
        ["S003", "C", 22, "M", "BSCS", 3, 70, 50, 55, 1, True, 5, "medium", "", "", "", "medium", ""],
        ["S004", "D", 19, "F", "BSCP", 1, 85, 70, 72, 0, True, 0, "medium", "", "", "music", "high", ""],
        ["S005", "E", 23, "M", "BSCM", 4, 55, 45, 48, 2, True, 20, "low", "", "", "", "low", ""],
    ] * 12  # repeat to give the splitter enough rows per class
    cols = [
        "roll_no", "name", "age", "gender", "department_code", "semester", "attendance_pct",
        "internal_marks", "semester_marks", "backlogs", "fee_paid", "fee_delay_days",
        "financial_status", "family_background", "behavioral_indicators", "extracurricular",
        "placement_readiness", "counselor_remarks",
    ]
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        w.writerows(rows)
    if monkeypatch_env:
        os.environ["ML_DEFAULT_DATASET"] = str(p)
    return p


def test_predict_for_student_auto_trains(app_client, auth_headers) -> None:
    _seed_dataset()
    # Drop any cached settings + model.
    from app.core.config import get_settings
    get_settings.cache_clear()  # type: ignore[attr-defined]
    from app.ml import predict as predict_mod
    predict_mod.reset_cache()

    # Create a student, then trigger a prediction.
    payload = {
        "roll_no": f"P{uuid.uuid4().hex[:8].upper()}",
        "name": "Predict Me",
        "age": 21,
        "gender": "M",
        "department_id": None,
        "semester": 2,
        "attendance_pct": 55,
        "internal_marks": 40,
        "semester_marks": 45,
        "backlogs": 3,
        "fee_paid": True,
        "fee_delay_days": 10,
        "financial_status": "low",
        "family_background": "",
        "behavioral_indicators": "",
        "extracurricular": "",
        "placement_readiness": "low",
        "counselor_remarks": "",
        "faculty_notes": "",
    }
    s = app_client.post("/api/v1/students", json=payload, headers=auth_headers)
    assert s.status_code in {200, 201}, s.text
    sid = s.json()["roll_no"]

    r = app_client.post(f"/api/v1/predictions/{sid}", headers=auth_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["risk_level"] in {"low", "medium", "high"}
    assert 0 <= body["confidence"] <= 1


def test_predict_batch_route_not_captured_as_roll_no(app_client, auth_headers, monkeypatch) -> None:
    from app.services import prediction_service

    monkeypatch.setattr(
        prediction_service,
        "predict_batch",
        lambda db, *, roll_nos, student_ids, department_id: {
            "total": 0,
            "succeeded": 0,
            "failed": 0,
            "predictions": [],
        },
    )

    r = app_client.post("/api/v1/predictions/batch", json={}, headers=auth_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body == {"total": 0, "succeeded": 0, "failed": 0, "predictions": []}
