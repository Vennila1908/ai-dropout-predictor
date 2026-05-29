# Security

## Authentication

* **bcrypt** password hashing via `passlib[bcrypt]` (cost factor 12).
* **JWT** access tokens (default 30 min) and refresh tokens (default 7 days),
  signed with HS256 and `SECRET_KEY` from the environment.
* Tokens carry `sub` (user id), `role`, and `exp`. They are validated on every
  protected request via a shared FastAPI dependency.
* Logout is client-side (drop the token); for full revocation, add a
  short-TTL Redis denylist keyed by `jti` (out of scope for the demo build).

## Authorization

* `Depends(get_current_user)` resolves the user.
* `RoleGate({"admin"})` / `RoleGate({"admin", "faculty"})` dependencies guard
  role-restricted routes.
* Faculty are scoped to their `department_id` for student listing and writes;
  admins see everything.
* Students can only read their own profile + predictions + recommendations.

## Input Validation

* Every request body and query parameter goes through a **Pydantic v2** schema.
* Numeric ranges enforced: `attendance_pct ∈ [0, 100]`, `backlogs ∈ [0, 50]`,
  etc. (see `backend/app/schemas/student.py`).
* File upload validation:
  * Extension allowlist: `.csv, .xlsx, .xls, .pdf, .docx`.
  * MIME sniffing of the first bytes; reject mismatches.
  * Size cap from `MAX_UPLOAD_BYTES` (default 10 MB).

## SQL & Storage

* All queries use SQLAlchemy ORM or `text()` with bound parameters — **no
  f-string SQL**.
* Uploaded files are stored under `uploads/` with a UUID filename; the
  original name is kept only as a string column.

## Rate Limiting

`slowapi` is wired into FastAPI:

* `POST /api/v1/auth/login` → 10 / minute / IP
* `POST /api/v1/chat/query` → 30 / minute / user
* Other endpoints → unlimited (tune in `app/core/rate_limit.py`).

## CORS

`CORS_ORIGINS` is a comma-separated allowlist. The default Vite dev origin
(`http://localhost:5173`) is included for convenience. Use `*` only in a
trusted dev environment.

## Audit Logging

`AuditLog` rows are written for: login (success + failure), user CRUD,
student CRUD, predictions, recommendations, uploads. Each row includes
`user_id`, `action`, `entity`, `entity_id`, and a JSON `meta`.

## LLM & Privacy

* All LLM traffic is HTTP to **localhost** Ollama. No data leaves the host.
* Prompts include only the **specific student record** under review (or
  pre-aggregated stats for chat) — never the entire dataset.
* The chat endpoint's system prompt explicitly forbids inventing students.

## Threat Model Snapshot

| Threat                          | Mitigation                                              |
|---------------------------------|---------------------------------------------------------|
| Credential stuffing on /login   | bcrypt + slowapi rate limit + audit log                 |
| SQL injection                   | ORM-only; Pydantic validation                           |
| Path traversal on uploads       | UUID filenames, no original path joined                 |
| Malicious file uploads          | extension + MIME + size + first-bytes sniff             |
| JWT theft (XSS)                 | HttpOnly recommended at proxy; short access TTL; CSP    |
| LLM data exfiltration           | Local-only Ollama; no `requests` to public hosts        |
| Privilege escalation            | RoleGate on every write; per-department scoping         |
| Denial of service via /ml/train | Background task + admin-only + once per N min cooldown  |

## Reporting

Found something? Email security@example.com (or open a private issue if
self-hosted). Do not include credentials or production data.
