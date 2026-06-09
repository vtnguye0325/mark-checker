#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_PYTHON="$ROOT/backend/.venv/bin/python"

# --- Environment -------------------------------------------------------------
# Load .env (HF_MODEL_ID, HF_TOKEN, DEEPSEEK_API_KEY, …) into the environment so
# the backend picks them up at runtime.
if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

# The model is loaded from the Hugging Face hub at runtime. Point MODEL_DIR at
# the HF repo id (overridable: export MODEL_DIR=/path/to/local/model to use a
# local copy instead).
export MODEL_DIR="${MODEL_DIR:-${HF_MODEL_ID:-vtnguye/automating-abercrombie}}"

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
