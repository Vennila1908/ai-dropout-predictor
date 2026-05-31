# Setup Guide

## Prerequisites

* **Python 3.11+** on `PATH` (`python --version`)
* **Node.js 20+** + **npm** (`node --version`)
* **Ollama** (optional but recommended) — https://ollama.com/download
* **Docker** (optional, for containerized run)

## Quickstart (Windows / PowerShell)

```powershell
git clone <this-repo> ai-dropout-predictor
cd ai-dropout-predictor

# 1. One-shot: venv + deps + DB + seed + initial model
./scripts/setup.ps1

# 2. (Optional) Pull the local LLM model used for recommendations + chat
./scripts/pull_llm.ps1     # runs: ollama pull phi3

# 3. Run backend (in one terminal)
./scripts/start_backend.ps1

# 4. Run frontend (in another terminal)
./scripts/start_frontend.ps1
```

Open: http://localhost:5173 — log in with the seeded admin
(see [Sample Credentials](#sample-credentials)).

## Quickstart (Unix / macOS / Linux)

```bash
git clone <this-repo> ai-dropout-predictor
cd ai-dropout-predictor

bash scripts/setup.sh
ollama pull phi3            # optional

# backend
source backend/.venv/bin/activate
uvicorn app.main:app --reload --app-dir backend --host 0.0.0.0 --port 8000

# frontend (in another terminal)
cd frontend && npm run dev
```

## Environment Variables

### Backend (`backend/.env`)

```
APP_NAME=AI Dropout Predictor
APP_ENV=development
SECRET_KEY=please-change-me
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_MINUTES=10080
DATABASE_URL=sqlite:///./app.db
CORS_ORIGINS=http://localhost:5173,http://localhost:8080
MAX_UPLOAD_BYTES=10485760
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=phi3
LLM_TIMEOUT_SECONDS=60
ML_ARTIFACT_DIR=../ml/artifacts
ML_DEFAULT_DATASET=../datasets/sample_students.csv
RATE_LIMIT_LOGIN=10/minute
RATE_LIMIT_CHAT=30/minute
```

### Frontend (`frontend/.env.local`)

```
VITE_API_BASE_URL=http://localhost:8000
```

## Database

* Defaults to **SQLite** (`backend/app.db`). Zero config.
* For Postgres, set `DATABASE_URL=postgresql+psycopg://user:pass@host:5432/db`
  in `backend/.env` and run `alembic upgrade head`.

## Sample Credentials

After running `setup.ps1` / `setup.sh` (or hitting any endpoint that triggers
the seed), these accounts exist:

| Email                | Password   | Role     |
|----------------------|------------|----------|
| admin@example.com    | Admin@123  | admin    |
| faculty@example.com  | Faculty@123| faculty  |
| student@example.com  | Student@123| student  |

Change these immediately in production.

Each seeded student also gets a login account:

| Email pattern              | Password    | Role    |
|----------------------------|-------------|---------|
| `{roll_no}@student.edu`    | Student@123 | student |

Examples: `bca050001@student.edu`, `bahep010014@student.edu`, `mba020003@student.edu`
(roll numbers are lowercase in the email; hyphens in program codes are omitted in roll numbers).

To load the new 30-program dataset on an existing database, delete `backend/app.db` (or reset Postgres) and restart the backend so the seed runs again.

## Training the ML Model

The setup script trains an initial model. To retrain manually:

```powershell
./scripts/train_model.ps1
# OR
python ml/training_scripts/train_baseline.py --dataset datasets/sample_students.csv
```

The artifact is written to `ml/artifacts/model.joblib` and the API picks it up
automatically (lazy-loaded, cached).

## Docker

```powershell
# Default (SQLite + no LLM container)
docker compose up -d --build

# With Postgres
docker compose --profile postgres up -d --build

# With Postgres + Ollama
docker compose --profile full up -d --build
docker exec -it dropout-ollama ollama pull phi3
```

Backend → http://localhost:8000  •  Frontend → http://localhost:8080

## Troubleshooting

* **`ModuleNotFoundError: No module named 'app'`** — run uvicorn from repo
  root with `--app-dir backend`, *or* activate the venv inside `backend/` and
  run `uvicorn app.main:app --reload`.
* **CORS errors** — add your frontend origin to `CORS_ORIGINS`.
* **LLM features look templated, not AI-generated** — Ollama isn't running or
  the model isn't pulled. Run `ollama serve` and `ollama pull phi3`.
* **`shap` import slow / fails** — that's fine; the system falls back to a
  permutation-based explainer automatically.
