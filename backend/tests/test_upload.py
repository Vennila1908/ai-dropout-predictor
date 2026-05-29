"""Upload preview smoke test."""

from __future__ import annotations

import io


CSV_BLOB = (
    "Roll No,Student Name,Department,Semester,Attendance %,Internal,Backlogs,Fee Paid\n"
    "U101,Test Alpha,BSCS,1,82,72,0,Yes\n"
    "U102,Test Beta,BSCS,2,55,35,3,No\n"
)


def test_upload_preview(app_client, auth_headers) -> None:
    files = {"file": ("students.csv", io.BytesIO(CSV_BLOB.encode("utf-8")), "text/csv")}
    r = app_client.post("/api/v1/uploads", files=files, headers=auth_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "detected_columns" in body
    assert "suggested_mapping" in body
    assert any(s["target"] == "roll_no" for s in body["suggested_mapping"])
