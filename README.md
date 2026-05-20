# AI Dropout Predictor

> An offline-first, full-stack platform that predicts which students are at
> risk of dropping out, **explains why**, and generates personalized
> counseling plans — all on a single laptop, with no cloud LLM calls.

![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-5-646CFF?logo=vite&logoColor=white)
![Tailwind](https://img.shields.io/badge/Tailwind-3.4-38B2AC?logo=tailwindcss&logoColor=white)

---

## ✨ Highlights

- **End-to-end ML pipeline** — feature engineering, training, evaluation,
  selection of the best of {LogReg, RF, GBM, XGBoost?}, persistence, and
  inference. Auto-trains on first use.
- **Explainable AI** — SHAP for tree models with a deterministic
  permutation-based fallback. Every prediction ships with top contributing
  factors *and* a plain-language narrative.
- **Local LLM only** — recommendations and chat are powered by a local
  Ollama daemon (default `phi3`). If Ollama is offline, a deterministic
  fallback keeps the app fully functional.
- **Safe file ingestion** — CSV / Excel / PDF / DOCX parsing with extension +
  MIME validation, fuzzy column mapping (rapidfuzz), and a 3-step Upload
  Wizard.
- **Production patterns** — JWT + bcrypt auth, role-based access, audit log,
  rate limits, CORS allowlist, Pydantic-validated I/O, structured logging,
  Alembic migrations, Dockerfiles, docker-compose profiles.
- **Modern UI** — React 18 + Vite + Tailwind, dark/light mode, React Query,
  Zustand, React Hook Form + Zod, Recharts, Framer Motion, react-hot-toast,
  lucide icons.

---

## 📸 Screens (placeholders)

> Replace these with screenshots after running the app.

| Login | Dashboard | Student detail | Upload wizard | Chat |
|-------|-----------|----------------|---------------|------|
| `docs/screens/login.png` | `docs/screens/dashboard.png` | `docs/screens/student.png` | `docs/screens/upload.png` | `docs/screens/chat.png` |

---

## 🏗 Architecture

See [`docs/architecture.md`](docs/architecture.md) for the full write-up
and [`docs/diagrams/`](docs/diagrams/) for Mermaid diagrams (architecture,
ER, workflow, ML pipeline, sequence diagrams for auth & prediction).

```
React 18 SPA  ──HTTPS──▶  FastAPI  ──HTTP──▶  Ollama (local)
   │                          │
   │                  SQLAlchemy + scikit-learn + SHAP
   │                          │
   ▼                          ▼
 Browser                SQLite / Postgres
```

---

## 📁 Folder structure

```
ai-dropout-predictor/
├── backend/                FastAPI app + ML + parsers + tests + alembic
│   └── app/
│       ├── api/v1/         Routers, one file per resource
│       ├── core/           Config, security, deps, logging, rate limit
│       ├── db/             Base, session, init+seed
│       ├── models/         SQLAlchemy 2.x ORM models
│       ├── schemas/        Pydantic v2 DTOs
│       ├── repositories/   Query encapsulation
│       ├── services/       Business logic (auth, ml, llm, ...)
│       ├── ml/             Feature engineering, training, prediction, XAI
│       ├── parsers/        CSV / Excel / PDF / DOCX + fuzzy column mapper
│       └── utils/          Files, text, time
├── frontend/               React 18 + Vite + TS + Tailwind
│   ├── src/components/     UI primitives + layout + charts + features
│   ├── src/pages/          Routed views
│   ├── src/features/       Per-domain API client modules
│   ├── src/lib/            axios, queryClient, utils, constants
│   └── src/store/          Zustand auth + UI stores
├── ml/                     Trained artifacts + standalone training scripts
├── datasets/               sample_students.csv (committed)
├── scripts/                setup.ps1, setup.sh, start_*, pull_llm, train_model
├── docker/                 Reference Nginx config + README pointer
├── docs/                   Architecture, schema, API, ML, LLM, security, ...
├── docker-compose.yml      Default + postgres + ollama profiles
└── PROJECT_SUMMARY.md      What's built + 3-command quickstart
```

---

## 🚀 Quickstart

### One-command start (recommended)

Spin up everything — venv, deps, DB seed, initial model, Ollama (if installed),
backend, frontend, and your browser — with a single script:

```powershell
.\scripts\start_all.ps1     # Windows / PowerShell
```

```bash
./scripts/start_all.sh      # macOS / Linux / WSL
```

The script is idempotent: subsequent runs detect prior setup and skip it.
If Ollama is not installed it warns and continues (recommendations + chat
fall back to the deterministic offline plan). The detailed step-by-step
quickstart below is still useful when you want to run pieces individually.

### Windows (PowerShell)

```powershell
git clone <this-repo> ai-dropout-predictor
cd ai-dropout-predictor

.\scripts\setup.ps1                # venv + deps + DB + seed + initial model
.\scripts\pull_llm.ps1              # optional: ollama pull phi3
.\scripts\start_backend.ps1         # → http://localhost:8000/docs
.\scripts\start_frontend.ps1        # → http://localhost:5173
```

### Unix / macOS / Linux

```bash
git clone <this-repo> ai-dropout-predictor && cd ai-dropout-predictor

bash scripts/setup.sh
ollama pull phi3                    # optional
source backend/.venv/bin/activate
uvicorn app.main:app --reload --app-dir backend &     # backend
( cd frontend && npm run dev )                        # frontend
```

### Docker

```bash
docker compose up -d --build                          # default (sqlite, no LLM)
docker compose --profile postgres up -d --build       # + postgres
docker compose --profile full up -d --build           # + postgres + ollama
docker exec -it dropout-ollama ollama pull phi3       # pull the model
```

---

## 🔑 Sample credentials

The seed creates three accounts on first startup:

| Email                | Password    | Role    |
|----------------------|-------------|---------|
| admin@example.com    | Admin@123   | admin   |
| faculty@example.com  | Faculty@123 | faculty |
| student@example.com  | Student@123 | student |

**Change them before any deployment.**

---

## 📚 Documentation

| Doc | What's inside |
|-----|---------------|
| [`docs/architecture.md`](docs/architecture.md) | Container view, layered backend, data flow |
| [`docs/database-schema.md`](docs/database-schema.md) | All tables, indexes, ER diagram |
| [`docs/api.md`](docs/api.md) | Every endpoint and its contract |
| [`docs/ml-pipeline.md`](docs/ml-pipeline.md) | Features, models, evaluation, persistence |
| [`docs/explainable-ai.md`](docs/explainable-ai.md) | SHAP path + fallback; output shape |
| [`docs/llm-integration.md`](docs/llm-integration.md) | Ollama prompts + offline fallback |
| [`docs/setup-guide.md`](docs/setup-guide.md) | Prereqs, env vars, troubleshooting |
| [`docs/deployment.md`](docs/deployment.md) | Compose, k8s, hardening checklist |
| [`docs/security.md`](docs/security.md) | Threat model + mitigations |
| [`docs/future-scope.md`](docs/future-scope.md) | What to build next (12 ideas) |
| [`docs/diagrams/`](docs/diagrams/) | Renderable Mermaid sources |

Swagger UI: http://localhost:8000/docs · ReDoc: http://localhost:8000/redoc

---

## 🔌 API quick reference

```
POST   /api/v1/auth/login                          → tokens + user
GET    /api/v1/students?q=&risk=&page=&page_size=  → paginated list
POST   /api/v1/uploads (multipart)                 → preview + suggested mapping
POST   /api/v1/uploads/{id}/confirm                → commit students
POST   /api/v1/predictions/{student_id}            → run + persist + explain
POST   /api/v1/recommendations/{id}/generate       → LLM or fallback
POST   /api/v1/chat/query                          → offline assistant
GET    /api/v1/analytics/bundle                    → single dashboard payload
GET    /api/v1/health · /api/v1/health/llm         → liveness + ollama probe
```

Full reference in [`docs/api.md`](docs/api.md).

---

## 🧠 ML / XAI in 30 seconds

1. **Features** — `attendance_pct`, `internal_marks`, `semester_marks`,
   `backlogs`, `fee_delay_days`, `fee_paid`, `age`, `semester`,
   `financial_status_ord`, `placement_readiness_ord`, `engagement_score`.
2. **Train** — splits 80/20, fits LogReg + RandomForest + GradientBoosting +
   XGBoost (if importable), keeps the best by macro-F1.
3. **Persist** — `ml/artifacts/model.joblib` + `model_meta.json` (metrics,
   confusion matrix, importances, feature means, leaderboard).
4. **Explain** — SHAP `TreeExplainer` for tree models, otherwise a
   per-sample `(value − mean) × importance` heuristic. Always returns
   top contributing features + a templated narrative.

---

## 🤖 LLM behavior

* All LLM traffic is HTTP to **localhost** Ollama. Default model: `phi3`,
  configurable via `LLM_MODEL` (also tested with `mistral`, `tinyllama`,
  `gemma:2b`).
* `RecommendationService` builds a tightly-scoped prompt from the student
  record + latest prediction + last 3 counseling sessions and asks for a
  JSON plan. Output is parsed defensively.
* If Ollama is unreachable, **the system never fails** — it falls back to a
  deterministic plan derived from risk factors and tags `source = "fallback"`.
* `ChatService` injects only **aggregated, sanitized** stats into the prompt
  with a system prompt that forbids inventing students.

---

## 🛡 Security

Highlights (full list in [`docs/security.md`](docs/security.md)):

* bcrypt password hashing (cost 12), JWT access + refresh tokens.
* Role-based authorization via FastAPI dependencies + a `RoleGate` helper.
* slowapi rate limits on `/auth/login` (10/min) and `/chat/query` (30/min).
* File upload allowlist + magic-number sniff + 10 MB cap.
* Pydantic v2 validation on every request body and query parameter.
* SQLAlchemy ORM-only data access — zero string-formatted SQL.
* Audit log on auth, user CRUD, student CRUD, predictions, recommendations,
  uploads.

---

## 🔮 Future Scope

Highlights from [`docs/future-scope.md`](docs/future-scope.md):

1. **IoT attendance** via RFID/NFC + MQTT.
2. **Computer-vision attendance** with on-device face recognition.
3. **Engagement analysis** from classroom / online-class video.
4. **Voice counseling** with Whisper.cpp transcription + local LLM summaries.
5. **WhatsApp / parent alerts** for high-risk students.
6. **Native mobile app** (React Native / Expo).
7. **Predictive semester analysis** with sequence models.
8. **What-if simulator** ("if attendance → 85 %, what's the new risk?").
9. **Cohort recommendations** via clustering of high-risk students.
10. **ERP / SIS integration** (Moodle, Canvas, SAP SLcM).
11. **Multi-tenant SaaS mode** with SSO.
12. **Continuous learning loop** with counselor feedback.

---

## 🧪 Tests

```bash
cd backend
.venv/bin/pytest -q     # or .venv\Scripts\pytest.exe -q on Windows
```

Smoke tests cover health, login, students CRUD, upload preview, and
end-to-end prediction (which exercises auto-training).

---

## 🎓 Viva / Presentation Pack

* All Mermaid diagrams under [`docs/diagrams/`](docs/diagrams/) render
  natively on GitHub or in any Mermaid-aware viewer.
* [`docs/architecture.md`](docs/architecture.md) and
  [`docs/ml-pipeline.md`](docs/ml-pipeline.md) double as slide decks.
* [`PROJECT_SUMMARY.md`](PROJECT_SUMMARY.md) at the repo root contains the
  3-command demo, what was built, and known limitations.

---

## 📜 License

MIT — see [`LICENSE`](LICENSE).
