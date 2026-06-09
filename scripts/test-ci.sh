#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$ROOT/backend/.venv"
PY="$VENV/bin/python"
PIP="$VENV/bin/pip"

# Create venv if it doesn't exist
if [ ! -f "$PY" ]; then
  echo "Creating virtualenv..."
  python3 -m venv "$VENV"
  $PIP install --quiet --upgrade pip
  $PIP install --quiet ruff pytest fastapi uvicorn httpx slowapi python-multipart nltk openai
fi

echo "=== Lint ==="
$VENV/bin/ruff check "$ROOT/backend/"
$VENV/bin/ruff format --check "$ROOT/backend/"

echo "=== Unit Tests ==="
cd "$ROOT"
$PY -m pytest tests/test_text_formatter.py -v

echo "=== Frontend Build ==="
cd "$ROOT/frontend"
npm ci --silent
npm run build

echo "=== All checks passed ==="
