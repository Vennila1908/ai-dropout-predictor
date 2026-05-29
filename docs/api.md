# API Reference

Base URL (dev): `http://localhost:8000/api/v1`

OpenAPI / Swagger UI is auto-generated at `http://localhost:8000/docs`.
ReDoc is at `http://localhost:8000/redoc`.

All write endpoints require `Authorization: Bearer <access_token>` unless
explicitly marked public.

## Auth

| Method | Path                | Auth   | Description                                                                  |
|--------|---------------------|--------|------------------------------------------------------------------------------|
| POST   | `/auth/register`    | public¹| Register first user (admin) or admin-creates-user.                           |
| POST   | `/auth/login`       | public | Returns `{access_token, refresh_token, user}`. Rate limited (10/min).        |
| POST   | `/auth/refresh`     | public | Exchanges refresh token for a new access token.                              |
| GET    | `/auth/me`          | jwt    | Returns the currently authenticated user.                                    |

¹ Allowed without auth only when zero users exist (bootstrap). After that,
admin-only.

## Users (admin)

| Method | Path             | Description                          |
|--------|------------------|--------------------------------------|
| GET    | `/users`         | List users, paginated.               |
| POST   | `/users`         | Create user; password is hashed.     |
| PATCH  | `/users/{id}`    | Partial update.                      |
| DELETE | `/users/{id}`    | Soft delete (sets `is_active=false`).|

## Students

| Method | Path                                | Description                                               |
|--------|-------------------------------------|-----------------------------------------------------------|
| GET    | `/students`                         | Query: `q, department_id, risk, page, page_size, sort`.   |
| POST   | `/students`                         | Create one student.                                       |
| GET    | `/students/{id}`                    | Single student + latest prediction.                       |
| PATCH  | `/students/{id}`                    | Partial update.                                           |
| DELETE | `/students/{id}`                    | Hard delete (admin) or soft (faculty).                    |
| GET    | `/students/{id}/timeline`           | Merged risk_history + counseling + faculty_notes.         |
| POST   | `/students/bulk`                    | JSON array import.                                        |

## Uploads

| Method | Path                          | Description                                                            |
|--------|-------------------------------|------------------------------------------------------------------------|
| POST   | `/uploads`                    | multipart file → preview rows + suggested column mapping.              |
| POST   | `/uploads/{id}/confirm`       | Body: `{ mapping: { source_col → target_col } }` → commit students.    |
| GET    | `/uploads`                    | History list.                                                          |

## Predictions

| Method | Path                                  | Description                                       |
|--------|---------------------------------------|---------------------------------------------------|
| POST   | `/predictions/{student_id}`           | Run prediction; persists + risk_history.          |
| POST   | `/predictions/batch`                  | Body: `{ student_ids?: int[], department_id? }`.  |
| GET    | `/predictions/{student_id}/latest`    | Latest persisted prediction.                      |
| GET    | `/predictions/{student_id}/history`   | All historical predictions.                       |

## ML

| Method | Path                          | Description                                                 |
|--------|-------------------------------|-------------------------------------------------------------|
| POST   | `/ml/train`                   | Background-task training; returns `{job_id, status}`.       |
| GET    | `/ml/status`                  | Active model meta: name, metrics, confusion matrix, etc.    |
| GET    | `/ml/feature-importance`      | Top-N features for the active model.                        |

## Recommendations

| Method | Path                                              | Description                                                  |
|--------|---------------------------------------------------|--------------------------------------------------------------|
| POST   | `/recommendations/{student_id}/generate`          | LLM-or-fallback recommendation from latest prediction.       |
| GET    | `/recommendations/{student_id}`                   | All recommendations for a student.                           |
| PATCH  | `/recommendations/{id}`                           | Update `status` / `summary`.                                 |

## Counseling

| Method | Path                                  | Description                                |
|--------|---------------------------------------|--------------------------------------------|
| POST   | `/counseling`                         | Create a counseling_session.               |
| GET    | `/counseling/student/{student_id}`    | Sessions for a student.                    |
| PATCH  | `/counseling/{id}`                    | Update notes / outcome / next_followup.    |

## Analytics

| Method | Path                                      | Description                              |
|--------|-------------------------------------------|------------------------------------------|
| GET    | `/analytics/overview`                     | Student counts, risk split, trend deltas.|
| GET    | `/analytics/risk-distribution`            | Counts grouped by `risk_level`.          |
| GET    | `/analytics/department-risk`              | Risk split per department.               |
| GET    | `/analytics/attendance-trends`            | Avg attendance by semester.              |
| GET    | `/analytics/prediction-confidence`        | Confidence histogram.                    |

## Reports

| Method | Path                              | Description                                 |
|--------|-----------------------------------|---------------------------------------------|
| GET    | `/reports/students.xlsx`          | Excel export of all students + risk.        |
| GET    | `/reports/student/{id}.pdf`       | Per-student PDF report.                     |
| GET    | `/reports/department/{id}.pdf`    | Department-level PDF.                       |

## Chat (offline)

| Method | Path             | Description                                                                  |
|--------|------------------|------------------------------------------------------------------------------|
| POST   | `/chat/query`    | `{ message, context_filters? }` → text/SSE. Rate limited (30/min). No cloud. |

## Health

| Method | Path           | Description                                  |
|--------|----------------|----------------------------------------------|
| GET    | `/health`      | `{ status, db, version }`.                   |
| GET    | `/health/llm`  | Pings Ollama; reports active model + status. |

## Error Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "attendance_pct must be between 0 and 100",
    "details": {"field": "attendance_pct"}
  }
}
```

HTTP status codes follow REST conventions: `400` validation, `401` unauth,
`403` forbidden, `404` missing, `409` conflict, `413` payload too large,
`429` too many requests, `500` server error.
