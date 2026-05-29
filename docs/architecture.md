# Architecture

## 1. System Overview

The **AI Dropout Predictor** is a full-stack, on-premises platform that helps
academic institutions identify students at risk of dropping out, explain *why*
the model thinks so, and generate counseling recommendations — entirely
offline, with no cloud LLM calls.

```
   ┌──────────────┐   HTTPS    ┌────────────────────────┐   HTTP    ┌──────────┐
   │  React SPA   │◀──────────▶│   FastAPI (Python 3.11)│◀─────────▶│  Ollama  │
   │ (Vite + TS)  │   JWT       │  REST + JSON / SSE     │           │  (local) │
   └──────┬───────┘             │  ML + XAI + Auth       │           └──────────┘
          │                     └──────────┬─────────────┘
          │                                │
          │                       ┌────────▼────────┐
          │                       │ SQLAlchemy ORM  │
          │                       │ SQLite/Postgres │
          │                       └─────────────────┘
          │
          ▼
   Browser (LocalStorage JWT, Tailwind dark/light)
```

## 2. Container View (C4 Level 2)

```mermaid
flowchart LR
  subgraph Client[Browser]
    SPA[React 18 SPA<br/>Vite, Tailwind, React Query]
  end

  subgraph Server[Application Server]
    API[FastAPI<br/>uvicorn, slowapi, JWT]
    ML[ML Service<br/>scikit-learn, xgboost, SHAP]
    LLM[LLM Service<br/>httpx → Ollama]
    PARSE[Parsers<br/>pandas, pdfplumber, PyMuPDF]
  end

  subgraph Data
    DB[(SQLite / Postgres)]
    FS[(uploads/, ml/artifacts/)]
  end

  Ollama[Ollama Daemon<br/>phi3 / mistral / gemma]

  SPA -->|REST + JWT| API
  API --> ML
  API --> LLM
  API --> PARSE
  ML --> FS
  LLM -->|HTTP| Ollama
  API --> DB
  PARSE --> FS
```

## 3. Layered Backend

```
api/v1/endpoints  →  services  →  repositories  →  models / db
       │
       └─ schemas (Pydantic)  ←  validation, OpenAPI contract
```

* **api/v1/endpoints** — thin FastAPI routers, only HTTP concerns.
* **services** — business logic, orchestration, transactions.
* **repositories** — encapsulate query patterns; no SQL leaks above.
* **models** — SQLAlchemy 2.x declarative models.
* **schemas** — Pydantic v2 request/response DTOs.
* **ml** — feature engineering, training, prediction, explainability.
* **parsers** — file ingestion (CSV/Excel/PDF/DOCX) → normalized rows.

## 4. Data Flow: Upload → Prediction → Recommendation

```mermaid
sequenceDiagram
    participant U as Faculty
    participant F as Frontend
    participant B as Backend
    participant P as Parsers
    participant M as ML Service
    participant L as LLM (Ollama)
    participant D as Database

    U->>F: Drop CSV/Excel/PDF
    F->>B: POST /uploads (multipart)
    B->>P: Detect type + parse
    P-->>B: Rows + suggested column map (rapidfuzz)
    B-->>F: 200 (upload_id, preview, mapping)
    U->>F: Confirm mapping
    F->>B: POST /uploads/{id}/confirm
    B->>D: INSERT students
    B-->>F: 200 (rows_imported)

    U->>F: Run prediction (single or batch)
    F->>B: POST /predictions/{student_id}
    B->>M: predict(features)
    M-->>B: {risk_level, confidence, explanation}
    B->>D: INSERT predictions, risk_history
    B-->>F: 200 (prediction)

    U->>F: Generate recommendation
    F->>B: POST /recommendations/{student_id}/generate
    B->>L: prompt(student + prediction + explanation)
    L-->>B: text → JSON (parsed defensively)
    Note over B: On error: deterministic fallback from risk factors
    B->>D: INSERT recommendations
    B-->>F: 200 (recommendation)
```

## 5. Roles

| Role     | Capabilities                                                                     |
|----------|----------------------------------------------------------------------------------|
| admin    | Full CRUD on users + everything faculty can do; system settings; ML training.    |
| faculty  | Manage students in their department, run predictions, log counseling sessions.   |
| student  | View their own predictions, recommendations, and history (read-only profile).    |

Authorization is enforced via FastAPI `Depends` chains and a `RoleGate` helper.

## 6. Technology Choices Rationale

* **FastAPI** — async-friendly, Pydantic-native, auto-OpenAPI.
* **SQLite default** — zero-config for demos; switch to Postgres via `DATABASE_URL`.
* **scikit-learn + optional XGBoost** — broad model coverage without forcing GPU.
* **SHAP w/ permutation fallback** — explainability that degrades gracefully.
* **Ollama local LLM** — privacy, zero cloud cost, fully offline.
* **React 18 + Vite + Tailwind + React Query** — modern, fast DX, small bundle.

## 7. Non-Functional Targets

* **Cold-start prediction**: <300 ms once model is loaded.
* **Bulk import**: 5,000 rows in <10 s on commodity hardware.
* **Offline mode**: every page that doesn't need the LLM must work; LLM features fall back to deterministic templated text.
* **Security**: bcrypt + JWT + parameterized queries + extension/MIME validation + slowapi rate limits.

See [`database-schema.md`](./database-schema.md), [`api.md`](./api.md),
[`ml-pipeline.md`](./ml-pipeline.md), and the Mermaid diagrams under
[`diagrams/`](./diagrams/) for deeper detail.
