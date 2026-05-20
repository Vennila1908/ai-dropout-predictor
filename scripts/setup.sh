#!/usr/bin/env bash
# One-shot bootstrap for the AI Dropout Predictor on Unix / macOS / Linux.
set -euo pipefail

SKIP_FRONTEND=0
SKIP_TRAIN=0
for arg in "$@"; do
  case "$arg" in
    --skip-frontend) SKIP_FRONTEND=1 ;;
    --skip-train) SKIP_TRAIN=1 ;;
    *) echo "Unknown flag: $arg" >&2; exit 1 ;;
  esac
done

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
VENV="$BACKEND/.venv"

need() { command -v "$1" >/dev/null 2>&1 || { echo "ERR: $1 not found. $2" >&2; exit 1; } }

# Locate a Python 3.11+ interpreter. Try the version-suffixed binaries first
# so we tolerate distros where bare `python` / `python3` are too old.
find_python_311plus() {
  PY_CMD=""
  PY_VER=""
  PY_ATTEMPTS=()
  local cand out major minor patch
  for cand in python3.12 python3.11 python3 python; do
    if ! command -v "$cand" >/dev/null 2>&1; then
      PY_ATTEMPTS+=("$cand: not found on PATH")
      continue
    fi
    out="$("$cand" --version 2>&1 || true)"
    if [[ "$out" =~ Python[[:space:]]+([0-9]+)\.([0-9]+)(\.([0-9]+))? ]]; then
      major="${BASH_REMATCH[1]}"
      minor="${BASH_REMATCH[2]}"
      patch="${BASH_REMATCH[4]:-}"
      if (( major > 3 || (major == 3 && minor >= 11) )); then
        PY_CMD="$cand"
        PY_VER="$major.$minor${patch:+.$patch}"
        return 0
      else
        PY_ATTEMPTS+=("$cand: Python $major.$minor (too old; need >= 3.11)")
      fi
    else
      PY_ATTEMPTS+=("$cand: unexpected --version output: ${out//$'\n'/ | }")
    fi
  done
  return 1
}

echo "▶ Checking prerequisites..."
if ! find_python_311plus; then
  echo "ERR: No Python 3.11+ interpreter found. Tried:" >&2
  for a in "${PY_ATTEMPTS[@]}"; do printf "       - %s\n" "$a" >&2; done
  echo "     Install Python 3.11 or newer from https://www.python.org/downloads/" >&2
  echo "     Then re-open this terminal so PATH refreshes." >&2
  exit 1
fi
echo "  • Using Python $PY_VER (via '$PY_CMD')"

if [[ "$SKIP_FRONTEND" -eq 0 ]]; then
  need node "Install Node.js 20+ first"
  need npm "npm should ship with Node.js"
fi

echo "▶ Creating Python virtualenv at $VENV"
if [[ ! -d "$VENV" ]]; then
  "$PY_CMD" -m venv "$VENV"
fi
PY="$VENV/bin/python"
"$PY" -m pip install --upgrade pip
"$PY" -m pip install -r "$BACKEND/requirements.txt"

if [[ ! -f "$BACKEND/.env" ]]; then
  cp "$BACKEND/.env.example" "$BACKEND/.env"
  echo "  • Created backend/.env from .env.example"
fi

echo "▶ Initializing database + seeding admin/departments/sample students"
( cd "$BACKEND" && "$PY" -m app.db.init_db )

if [[ "$SKIP_TRAIN" -eq 0 ]]; then
  echo "▶ Training initial ML model"
  "$PY" "$ROOT/ml/training_scripts/train_baseline.py" \
      --dataset "$ROOT/datasets/sample_students.csv" \
      --output "$ROOT/ml/artifacts"
fi

if [[ "$SKIP_FRONTEND" -eq 0 ]]; then
  echo "▶ Installing frontend dependencies (may take a minute)"
  ( cd "$FRONTEND" && [[ -f .env.local ]] || cp .env.example .env.local; npm install --no-audit --no-fund --loglevel=error )
fi

cat <<EOF

✔ Setup complete!

Next steps:
  1. (Optional) Pull the LLM model:           ollama pull phi3
  2. Start backend (terminal 1):              source backend/.venv/bin/activate && uvicorn app.main:app --reload --app-dir backend
  3. Start frontend (terminal 2):             cd frontend && npm run dev
  4. Open http://localhost:5173 and log in:   admin@example.com / Admin@123
EOF
