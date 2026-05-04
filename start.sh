#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "=== Building frontend ==="
cd frontend
npx vite build
cd ..

echo ""
echo "=== Starting backend on http://0.0.0.0:8000 ==="
PYTHONPATH="$PWD/src" uvicorn backend.main:app --host 0.0.0.0 --port 8000
