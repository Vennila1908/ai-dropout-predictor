# Project Summary — AI Dropout Predictor

A privacy-first full-stack platform that predicts and explains student
dropout risk and produces actionable counseling plans, entirely on a
single host (no cloud LLM calls).

---

## 1. What was built

### Backend (Python 3.11 · FastAPI · SQLAlchemy 2 · scikit-learn · SHAP)

* **API v1** with full CRUD for students, users, uploads, predictions,
  recommendations, counseling, analytics, reports, chat — see
  [`docs/api.md`](docs/api.md).
* **JWT auth** (access + refresh) with bcrypt hashing, `RoleGate`
  dependency, slowapi rate limits on `/auth/login` and `/chat/query`,
  audit log on every sensitive action.
* **Multi-format ingestion** — CSV / Excel / PDF / DOCX parsers + a
  rapidfuzz column mapper that suggests targets even when source headers
  differ. Returns a preview + per-column candidate list before any row
  reaches the DB.
* **ML pipeline** — feature engineering, train/select among LogReg + RF +
  GBM (+ XGBoost if available), persist `model.joblib` + `model_meta.json`,
  lazy-load on first prediction, auto-train on missing artifact.
* **Explainability** — SHAP `TreeExplainer` for tree models with a
  permutation-based fallback. Every prediction returns top contributing
  factors with sign + magnitude *and* a plain-language narrative.
* **Local LLM service** — async httpx client against Ollama
  (`phi3` by default, configurable). `RecommendationService` and
  `ChatService` use it with **deterministic offline fallbacks** so the
  app never breaks when Ollama is offline.
* **Reports** — Excel student export (openpyxl) + per-student & per-department
  PDFs (reportlab) including risk meter and explanation factors.
* **Database** — SQLite by default, Postgres-ready via `DATABASE_URL`.
  Alembic wired in; first run does `Base.metadata.create_all()` + seeds
  admin/faculty/student users + sample students from
  `datasets/sample_students.csv`.
* **Tests** — pytest fixtures + happy-path tests for health, auth,
  students CRUD, upload preview, and full-stack prediction (which exercises
  auto-training on a tiny inline dataset).

### Frontend (React 18 · Vite 5 · TypeScript 5 · Tailwind 3.4)

* **Tasteful enterprise theme** — neutral grays + indigo/violet primary +
  semantic risk palette. Class-based dark mode with no-flash inline
  detection.
* **App shell** — collapsible sidebar (mobile drawer), topbar with search,
  theme toggle, user menu, role-aware nav.
* **Pages** — Login, Admin Dashboard, Student Dashboard, Students list +
  detail, Uploads (3-step wizard), Predictions/XAI, Counseling, Analytics,
  Chat, Settings, 404.
* **State** — `@tanstack/react-query` for server state with skeletons and
  toasts; `zustand` for auth + UI; `react-hook-form` + `zod` for every
  form.
* **Charts** — Recharts: risk distribution (pie), department risk
  (stacked bar), attendance trends (line), feature importance (horizontal
  bar), confidence histogram (bar), risk meter.
* **Upload Wizard** — 3 steps with auto-suggested fuzzy mapping, editable
  column dropdowns, preview, and confirm.
* **Predictions UX** — single + batch, RiskMeter, ExplainabilityPanel
  (top factors with direction + contribution) and RecommendationPanel
  (LLM output + status controls).
* **Chat UX** — minimal chatbot with quick-prompt chips and an offline
  banner when Ollama isn't running.
* **API layer** — single axios instance with JWT interceptor that
  refreshes once on 401 then redirects to `/login`.

### Documentation, scripts, deployment

* [`docs/`](docs/) — architecture, db-schema, api, ml-pipeline,
  explainable-ai, llm-integration, setup-guide, deployment, security,
  future-scope, plus seven Mermaid diagrams under `docs/diagrams/`.
* `docker-compose.yml` with default (SQLite, no LLM container) + `postgres`
  and `ollama` profiles for opt-in expansion.
* PowerShell + Bash setup/start/train scripts.
* Pinned dependency versions for both `requirements.txt` and `package.json`.

---

## 2. 3-command demo

**One-command start (recommended):**

```powershell
.\scripts\start_all.ps1     # Windows / PowerShell
```

```bash
./scripts/start_all.sh      # macOS / Linux / WSL
```

This runs setup if needed, pulls the local LLM model when Ollama is
installed, starts both servers, waits for `/health`, and opens the browser.

**Manual / step-by-step (still supported):**

```powershell
.\scripts\setup.ps1
.\scripts\start_backend.ps1
.\scripts\start_frontend.ps1
```

Then open http://localhost:5173 and log in with `admin@example.com /
Admin@123`.

(Or on Unix: `bash scripts/setup.sh && uvicorn app.main:app --reload --app-dir backend & ( cd frontend && npm run dev )`.)

---

## 3. What you must do once

1. **Install Python 3.11+ and Node.js 20+** so the setup script works.
2. **(Optional but recommended) Install Ollama** and pull a small model:
   ```
   ollama pull phi3
   ```
   Without it, the app still works fully — recommendations and chat just
   use the deterministic offline fallbacks.
3. **Change the seeded admin password** before any non-local use.
4. **Set `SECRET_KEY`** to a strong random value in `backend/.env` for any
   real deployment.

---

## 4. Known limitations / non-goals

* **Bootstrap was performed without running `pip install` / `npm install`.**
  Dependency versions in `requirements.txt` and `package.json` are pinned
  to widely-used stable versions (FastAPI 0.115, SQLAlchemy 2.0.36,
  scikit-learn 1.5.2, React 18.3, Vite 5.4, Tailwind 3.4). The
  setup scripts install them on first run.
* **No initial model artifact ships in the repo.** Python 3 was unavailable
  in the build environment. The setup script (or `scripts/train_model.ps1`)
  trains the model the first time. The API also auto-trains on the first
  prediction if the artifact is missing.
* **Student dashboard is a stub** that lists what self-service will look
  like; the admin/faculty experience is the deep one.
* **Chat streaming is opt-in** (`stream: true` on `/chat/query`) — the UI
  uses the simpler non-streaming path by default.
* **Alembic migrations** are wired (`env.py`, `script.py.mako`) but no
  initial revision was generated; the app uses `create_all()` for the
  first run. Generate one before introducing schema changes.
* **No real student data is included** — `datasets/sample_students.csv`
  is fully synthetic.

---

## 5. Where to look first when extending

| You want to… | Start here |
|--------------|------------|
| Add a new API endpoint | `backend/app/api/v1/endpoints/` + matching `services/` + `schemas/` |
| Add a new ML feature | `backend/app/ml/features.py` (then retrain) |
| Add a new page | `frontend/src/pages/` + register in `frontend/src/router.tsx` |
| Add a new chart | `frontend/src/components/charts/` and import in any page |
| Tighten security | `backend/app/core/security.py`, `core/rate_limit.py`, `core/deps.py` |
| Switch to Postgres | `backend/.env` → `DATABASE_URL=postgresql+psycopg://...` |
| Configure the LLM model | `backend/.env` → `LLM_MODEL=mistral` (etc.) |

That's it — happy hacking. Open [`README.md`](README.md) for the full
walkthrough and [`docs/architecture.md`](docs/architecture.md) for the
deep-dive.
