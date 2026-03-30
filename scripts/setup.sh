#!/usr/bin/env bash
# Run once after cloning: bash scripts/setup.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

# --- Check required tools ---

for cmd in python3 pip node npm git; do
  command -v "$cmd" &>/dev/null || { echo "Error: $cmd is not installed."; exit 1; }
done

PY_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
PY_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
if [[ "$PY_MAJOR" -lt 3 || "$PY_MINOR" -lt 10 ]]; then
  echo "Error: Python 3.10+ required."
  exit 1
fi

NODE_MAJOR=$(node -e 'process.stdout.write(String(process.version.split(".")[0].slice(1)))')
if [[ "$NODE_MAJOR" -lt 18 ]]; then
  echo "Error: Node.js 18+ required."
  exit 1
fi

# --- Environment file ---

if [[ ! -f "$ROOT/.env" ]]; then
  cp "$ROOT/.env.example" "$ROOT/.env"
  echo "Created .env from .env.example. Add your OPENAI_API_KEY before running the app."
fi

# --- Python virtual environment ---

if [[ ! -d "$ROOT/.venv" ]]; then
  python3 -m venv "$ROOT/.venv"
fi

source "$ROOT/.venv/bin/activate"
pip install --upgrade pip --quiet
pip install -r "$ROOT/backend/requirements.txt" --quiet

# --- Frontend dependencies ---

if [[ -f "$ROOT/frontend/package.json" ]]; then
  cd "$ROOT/frontend" && npm install --silent && cd "$ROOT"
else
  echo "Warning: frontend/package.json not found. Re-run this script after scaffolding the frontend."
fi

# --- Data directories ---

for dir in data/policies data/syllabi data/sample_queries backend/uploads; do
  mkdir -p "$ROOT/$dir"
done

# --- Smoke test ---

for pkg in fastapi langchain chromadb openai pypdf; do
  python3 -c "import $pkg" &>/dev/null || echo "Warning: $pkg could not be imported."
done

# --- Done ---

echo ""
echo "Setup complete. Next steps:"
echo "  1. source .venv/bin/activate"
echo "  2. Fill in OPENAI_API_KEY in .env"
echo "  3. python scripts/ingest_policies.py"
echo "  4. uvicorn backend.main:app --reload"
echo "  5. cd frontend && npm run dev"