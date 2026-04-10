#!/usr/bin/env bash
# Run once after cloning: bash scripts/setup.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

echo "=== RAG University Assistant — Dev Setup ==="
echo ""

# --- Check required tools ---

echo "Checking system requirements..."

for cmd in git node npm; do
  command -v "$cmd" &>/dev/null || { echo "Error: $cmd is not installed."; exit 1; }
done

# Python 3.12 is required — 3.13+ breaks pydantic-core and other native packages
if ! command -v python3 &>/dev/null; then
  echo "Error: python3 is not installed."
  exit 1
fi

PY_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
PY_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
if [[ "$PY_MAJOR" -lt 3 || "$PY_MINOR" -lt 12 ]]; then
  echo "Error: Python 3.12+ required (found $PY_MAJOR.$PY_MINOR)."
  echo "Download Python 3.12 from https://python.org"
  exit 1
fi
echo "  Python $PY_MAJOR.$PY_MINOR OK"

NODE_MAJOR=$(node -e 'process.stdout.write(String(process.version.split(".")[0].slice(1)))')
if [[ "$NODE_MAJOR" -lt 18 ]]; then
  echo "Error: Node.js 18+ required (found $NODE_MAJOR)."
  exit 1
fi
echo "  Node.js $NODE_MAJOR OK"

# --- Environment file ---

echo ""
echo "Setting up environment..."

if [[ ! -f "$ROOT/.env" ]]; then
  cp "$ROOT/.env.example" "$ROOT/.env"
  echo "  Created .env from .env.example."
  echo "  *** Add your OPENAI_API_KEY to .env before running the app. ***"
else
  echo "  .env already exists, skipping."
fi

# --- Python virtual environment ---

echo ""
echo "Setting up Python virtual environment..."

if [[ ! -d "$ROOT/.venv" ]]; then
  python3 -m venv "$ROOT/.venv"
  echo "  Created .venv"
else
  echo "  .venv already exists, skipping."
fi

# activate — works in both Git Bash (Scripts/) and Linux/Mac (bin/)
if [[ -f "$ROOT/.venv/Scripts/activate" ]]; then
  source "$ROOT/.venv/Scripts/activate"
else
  source "$ROOT/.venv/bin/activate"
fi

# install uv for fast dependency resolution, then use it for everything else
pip install uv --quiet
echo "  Installing Python dependencies via uv (this may take a moment)..."
uv pip install -r "$ROOT/backend/requirements.txt" --quiet

# --- Data directories ---

echo ""
echo "Creating data directories..."

for dir in data/policies data/syllabi data/sample_queries backend/uploads; do
  mkdir -p "$ROOT/$dir"
  touch "$ROOT/$dir/.gitkeep"
done
echo "  data/policies/, data/syllabi/, data/sample_queries/, backend/uploads/ OK"

# --- Frontend dependencies ---

echo ""
echo "Setting up frontend..."

if [[ -f "$ROOT/frontend/package.json" ]]; then
  cd "$ROOT/frontend" && npm install --silent && cd "$ROOT"
  echo "  Frontend dependencies installed."
else
  echo "  frontend/package.json not found — skipping."
  echo "  Re-run this script after the frontend is scaffolded."
fi

# --- Smoke test ---

echo ""
echo "Running smoke test..."

for pkg in fastapi chromadb openai pypdf pdfplumber tiktoken rank_bm25 sentence_transformers; do
  if python3 -c "import $pkg" &>/dev/null; then
    echo "  $pkg OK"
  else
    echo "  WARNING: $pkg could not be imported — check your installation."
  fi
done

# --- Done ---

echo ""
echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "  1. Fill in OPENAI_API_KEY (and other values) in .env"
echo "  2. Add university policy PDFs to data/policies/"
echo "  3. Ingest policies into ChromaDB:"
echo "       python scripts/ingest_policies.py"
echo "  4. Start the backend:"
echo "       source .venv/Scripts/activate"
echo "       uvicorn backend.main:app --reload"
echo "  5. Start the frontend:"
echo "       cd frontend && npm run dev"
