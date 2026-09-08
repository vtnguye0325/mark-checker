#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_PYTHON="$ROOT/backend/.venv/bin/python"

# --- Environment -------------------------------------------------------------
# Load .env (HF_MODEL_ID, HF_TOKEN, GEMINI_API_KEY, …) into the environment so
# the backend picks them up at runtime.
if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

# This script runs the backend on the host, not in the compose network, so the
# compose service name "postgres-dev" does not resolve. docker-compose.dev.yml
# publishes Postgres on 127.0.0.1:5432, so rewrite the host for the host run.
if [[ -n "${DATABASE_URL:-}" ]]; then
  export DATABASE_URL="${DATABASE_URL/@postgres-dev:/@127.0.0.1:}"
fi

# --- Postgres --------------------------------------------------------------
# The backend needs the dev Postgres. Start the compose service if it is not
# already running, then wait until it accepts connections.
if [[ "${DATABASE_URL:-}" == *"@127.0.0.1:"* || "${DATABASE_URL:-}" == *"@localhost:"* ]]; then
  if ! docker info >/dev/null 2>&1; then
    echo "Error: Docker daemon is not running. Start Docker Desktop, then re-run this script." >&2
    exit 1
  fi
  if [[ -z "$(docker compose -f "$ROOT/docker-compose.dev.yml" ps -q postgres-dev 2>/dev/null)" ]]; then
    echo "Starting Postgres (postgres-dev)…"
    docker compose -f "$ROOT/docker-compose.dev.yml" up -d postgres-dev
  fi
  echo "Waiting for Postgres…"
  for _ in $(seq 1 30); do
    if docker compose -f "$ROOT/docker-compose.dev.yml" exec -T postgres-dev pg_isready -q -U markchecker 2>/dev/null; then
      break
    fi
    sleep 1
  done
fi

# The model is loaded from the Hugging Face hub at runtime. Point MODEL_DIR at
# the HF repo id (overridable: export MODEL_DIR=/path/to/local/model to use a
# local copy instead).
export MODEL_DIR="${MODEL_DIR:-${HF_MODEL_ID:-vtnguye/automating-abercrombie}}"

# --- Free the dev ports -----------------------------------------------------
# Kill any process that already holds a port this script needs, then reuse the
# same port. A stale uvicorn or vite from a killed terminal keeps the old .env,
# so the reload of a changed key never happens without this.
free_port() {
  local port="$1"
  local pids
  pids="$(lsof -ti "tcp:$port" -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -n "$pids" ]]; then
    echo "Port $port is in use by PID(s) $pids — killing…"
    # shellcheck disable=SC2086
    kill $pids 2>/dev/null || true
    sleep 1
    pids="$(lsof -ti "tcp:$port" -sTCP:LISTEN 2>/dev/null || true)"
    if [[ -n "$pids" ]]; then
      # shellcheck disable=SC2086
      kill -9 $pids 2>/dev/null || true
      sleep 1
    fi
  fi
}

free_port 8000
free_port 5173

cleanup() {
  echo ""
  echo "Stopping services…"
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  echo "Done."
}
trap cleanup EXIT INT TERM

# --- Backend setup -----------------------------------------------------------
if [[ ! -x "$BACKEND_PYTHON" ]]; then
  echo "Creating backend virtualenv at backend/.venv…"
  python3 -m venv "$ROOT/backend/.venv"
fi

echo "Syncing backend dependencies…"
"$BACKEND_PYTHON" -m pip install -q -r "$ROOT/backend/requirements.txt"

# --- Frontend setup ----------------------------------------------------------
if [[ ! -d "$ROOT/frontend/node_modules" ]]; then
  echo "Installing frontend dependencies…"
  (cd "$ROOT/frontend" && npm install)
fi

echo "Starting backend on :8000…"
cd "$ROOT/backend"
"$BACKEND_PYTHON" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "Starting frontend on :5173…"
cd "$ROOT/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "Backend  → http://localhost:8000"
echo "Frontend → http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop."

wait
