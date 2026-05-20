#!/usr/bin/env bash
# One-command end-to-end launcher for the AI Dropout Predictor (Unix / macOS / Linux).
#
# Performs prerequisite checks, runs setup if needed, ensures the local LLM
# (Ollama) is pulled & running when available, starts FastAPI + Vite as
# background processes, waits for /health, and opens the browser.
#
# Idempotent: safe to run multiple times.
#
# Usage:    ./scripts/start_all.sh

set -uo pipefail

# ─── Paths (resolved relative to this script) ────────────────────────────────
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
VENV="$BACKEND/.venv"
PY="$VENV/bin/python"
BACKEND_ENV="$BACKEND/.env"

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
NO_BROWSER="${NO_BROWSER:-0}"

# ─── Logging helpers ─────────────────────────────────────────────────────────
if [[ -t 1 ]]; then
  C_CYAN='\033[36m'; C_GREEN='\033[32m'; C_YEL='\033[33m'
  C_RED='\033[31m';  C_GRAY='\033[90m'; C_RESET='\033[0m'
else
  C_CYAN=''; C_GREEN=''; C_YEL=''; C_RED=''; C_GRAY=''; C_RESET=''
fi
section() { printf "\n${C_GRAY}%s${C_RESET}\n${C_CYAN} %s${C_RESET}\n${C_GRAY}%s${C_RESET}\n" \
  "────────────────────────────────────────────────────────────────────────" \
  "$1" \
  "────────────────────────────────────────────────────────────────────────"; }
ok()   { printf "  ${C_GREEN}[ok]${C_RESET}   %s\n" "$1"; }
skip() { printf "  ${C_GRAY}[skip]${C_RESET} %s\n" "$1"; }
info() { printf "  ${C_GRAY}[..]${C_RESET}   %s\n" "$1"; }
warn() { printf "  ${C_YEL}[warn]${C_RESET} %s\n" "$1"; }
fail() { printf "  ${C_RED}[err]${C_RESET}  %s\n" "$1" >&2; }

# ─── Cleanup on Ctrl-C ───────────────────────────────────────────────────────
BACKEND_PID=""
FRONTEND_PID=""
cleanup() {
  echo ""
  info "Shutting down..."
  if [[ -n "$FRONTEND_PID" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null; then kill "$FRONTEND_PID" 2>/dev/null || true; fi
  if [[ -n "$BACKEND_PID"  ]] && kill -0 "$BACKEND_PID"  2>/dev/null; then kill "$BACKEND_PID"  2>/dev/null || true; fi
  exit 0
}
trap cleanup INT TERM

have() { command -v "$1" >/dev/null 2>&1; }

# Locate a Python 3.11+ interpreter. Try the version-suffixed binaries first
# so we tolerate distros where bare `python` / `python3` are too old.
# On success: PY_CMD is set to the chosen command, PY_VER to "X.Y(.Z)".
# On failure: PY_ATTEMPTS holds one line per probed candidate.
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

# ─── 1. Prerequisites ────────────────────────────────────────────────────────
section "[1/6] Checking prerequisites"

if ! find_python_311plus; then
  fail "No Python 3.11+ interpreter found. Tried:"
  for a in "${PY_ATTEMPTS[@]}"; do printf "         - %s\n" "$a" >&2; done
  fail "Install Python 3.11 or newer from https://www.python.org/downloads/"
  fail "Then re-open this terminal so PATH refreshes."
  exit 1
fi
ok "Python $PY_VER (via '$PY_CMD')"
export PY_CMD

if ! have node; then
  fail "Node.js not found on PATH. Install Node.js 20+ first."
  exit 1
fi
NODE_VER_RAW="$(node -v | tr -d 'v')"
NODE_MAJOR="${NODE_VER_RAW%%.*}"
if (( NODE_MAJOR < 20 )); then
  fail "Node.js $NODE_VER_RAW is too old. Need Node 20 or newer."
  exit 1
fi
ok "Node.js $NODE_VER_RAW"

if ! have npm; then
  fail "npm not found on PATH (it should ship with Node.js)."
  exit 1
fi
ok "npm $(npm -v)"

# ─── 2. Backend setup (venv + deps + DB + seed + initial model) ──────────────
section "[2/6] Backend setup"

if [[ ! -d "$VENV" || ! -x "$PY" ]]; then
  info "venv missing — running scripts/setup.sh (this may take a few minutes on first run)..."
  if ! bash "$ROOT/scripts/setup.sh" --skip-frontend; then
    fail "setup.sh failed"
    exit 1
  fi
  ok "Backend setup complete"
else
  skip "venv already exists at backend/.venv"
  if [[ ! -f "$BACKEND_ENV" ]]; then
    cp "$BACKEND/.env.example" "$BACKEND_ENV"
    ok "Created backend/.env from .env.example"
  fi
fi

# ─── 3. Frontend deps ────────────────────────────────────────────────────────
section "[3/6] Frontend dependencies"

if [[ ! -d "$FRONTEND/node_modules" ]]; then
  info "node_modules missing — running npm install in frontend/..."
  ( cd "$FRONTEND" \
    && { [[ -f .env.local ]] || cp .env.example .env.local; } \
    && npm install --no-audit --no-fund --loglevel=error ) || {
    fail "npm install failed"
    exit 1
  }
  ok "Frontend deps installed"
else
  skip "frontend/node_modules already exists"
fi

# ─── 4. Ollama / LLM (non-fatal) ─────────────────────────────────────────────
section "[4/6] Local LLM (Ollama)"

# Resolve desired model: backend/.env > $LLM_MODEL > phi3
LLM_MODEL_RESOLVED=""
if [[ -f "$BACKEND_ENV" ]]; then
  LLM_MODEL_RESOLVED="$(grep -E '^[[:space:]]*LLM_MODEL[[:space:]]*=' "$BACKEND_ENV" \
    | tail -n1 \
    | sed -E -e 's/^[[:space:]]*LLM_MODEL[[:space:]]*=[[:space:]]*//' \
             -e 's/^"(.*)"$/\1/' \
             -e "s/^'(.*)'$/\\1/" \
    || true)"
fi
[[ -z "$LLM_MODEL_RESOLVED" && -n "${LLM_MODEL:-}" ]] && LLM_MODEL_RESOLVED="$LLM_MODEL"
[[ -z "$LLM_MODEL_RESOLVED" ]] && LLM_MODEL_RESOLVED="phi3"

LLM_STATUS="fallback (no Ollama)"

ollama_up() {
  curl -fsS --max-time 2 "http://localhost:11434/api/tags" >/dev/null 2>&1
}

if ! have ollama; then
  warn "Ollama is not installed — AI recommendations + chat will use deterministic offline fallbacks."
  warn "Install from https://ollama.com/download to enable the local LLM."
else
  ok "ollama CLI found"

  if ! ollama_up; then
    info "Ollama server not responding — starting 'ollama serve' in the background..."
    nohup ollama serve >/dev/null 2>&1 &
    OLLAMA_PID=$!
    disown "$OLLAMA_PID" 2>/dev/null || true
    for _ in $(seq 1 30); do
      ollama_up && break
      sleep 0.5
    done
  fi

  if ollama_up; then
    ok "Ollama server is up at http://localhost:11434"
    if ollama list 2>/dev/null | awk '{print $1}' | grep -E "^${LLM_MODEL_RESOLVED}(:|$)" >/dev/null; then
      skip "Model '$LLM_MODEL_RESOLVED' is already pulled"
      LLM_STATUS="running ($LLM_MODEL_RESOLVED cached)"
    else
      info "Pulling model '$LLM_MODEL_RESOLVED' (first time only — this can take a while)..."
      if ollama pull "$LLM_MODEL_RESOLVED"; then
        ok "Pulled '$LLM_MODEL_RESOLVED'"
        LLM_STATUS="running ($LLM_MODEL_RESOLVED pulled)"
      else
        warn "ollama pull failed — continuing with offline fallback."
        LLM_STATUS="fallback (pull failed)"
      fi
    fi
  else
    warn "Ollama server still unreachable — continuing with offline fallback."
    LLM_STATUS="fallback (server unreachable)"
  fi
fi

# ─── 5. Launch backend + frontend ────────────────────────────────────────────
section "[5/6] Launching backend + frontend"

mkdir -p "$ROOT/.run-logs"
BACKEND_LOG="$ROOT/.run-logs/backend.log"
FRONTEND_LOG="$ROOT/.run-logs/frontend.log"

info "Starting backend (uvicorn :$BACKEND_PORT) → $BACKEND_LOG"
(
  cd "$BACKEND"
  "$PY" -m uvicorn app.main:app --host 0.0.0.0 --port "$BACKEND_PORT" --reload
) >"$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!
ok "Backend PID $BACKEND_PID"

info "Starting frontend (vite :$FRONTEND_PORT) → $FRONTEND_LOG"
(
  cd "$FRONTEND"
  : "${VITE_API_BASE_URL:=http://localhost:$BACKEND_PORT}"
  export VITE_API_BASE_URL
  npm run dev -- --port "$FRONTEND_PORT" --host
) >"$FRONTEND_LOG" 2>&1 &
FRONTEND_PID=$!
ok "Frontend PID $FRONTEND_PID"

# ─── 6. Wait for backend health, then open browser ───────────────────────────
section "[6/6] Waiting for backend /health"

BACKEND_URL="http://localhost:$BACKEND_PORT"
FRONTEND_URL="http://localhost:$FRONTEND_PORT"
HEALTH_URL="$BACKEND_URL/api/v1/health"

healthy=0
for i in $(seq 1 60); do
  if curl -fsS --max-time 2 "$HEALTH_URL" >/dev/null 2>&1; then
    healthy=1
    break
  fi
  if (( i % 5 == 0 )); then info "still waiting... (${i}s)"; fi
  sleep 1
done

if (( healthy == 1 )); then
  ok "Backend is healthy"
  if [[ "$NO_BROWSER" != "1" ]]; then
    if   have xdg-open; then xdg-open "$FRONTEND_URL" >/dev/null 2>&1 || true
    elif have open;     then open    "$FRONTEND_URL" >/dev/null 2>&1 || true
    elif have wslview;  then wslview "$FRONTEND_URL" >/dev/null 2>&1 || true
    else warn "No browser opener found (xdg-open/open). Visit $FRONTEND_URL manually."
    fi
  fi
else
  warn "Backend did not respond on /health within 60s — check $BACKEND_LOG for errors."
fi

# ─── Final summary ───────────────────────────────────────────────────────────
LINE="────────────────────────────────────────────────────────────────────────"
echo ""
printf "${C_GRAY}%s${C_RESET}\n" "$LINE"
printf "${C_GREEN}  AI Dropout Predictor — running${C_RESET}\n"
printf "${C_GRAY}%s${C_RESET}\n" "$LINE"
echo  "  Frontend (UI)    : $FRONTEND_URL"
echo  "  Backend  (API)   : $BACKEND_URL"
echo  "  Swagger / OpenAPI: $BACKEND_URL/docs"
echo  "  Health probe     : $HEALTH_URL"
echo  "  Local LLM        : $LLM_STATUS  (model: $LLM_MODEL_RESOLVED)"
echo  ""
printf "${C_YEL}  Default login    : admin@example.com  /  Admin@123${C_RESET}\n"
echo  ""
printf "${C_GRAY}  Press Ctrl-C in this terminal to stop both servers (PIDs $BACKEND_PID, $FRONTEND_PID).${C_RESET}\n"
printf "${C_GRAY}%s${C_RESET}\n" "$LINE"

# Block on the child processes so Ctrl-C cleanly tears them down via the trap.
wait "$BACKEND_PID" "$FRONTEND_PID"
