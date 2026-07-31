#!/usr/bin/env bash
# Start both backend and frontend dev servers
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Starting Federal Spending Search..."
echo ""

# Start backend
echo "[backend] Installing deps..."
pip install -q -r "$SCRIPT_DIR/backend/requirements.txt"
echo "[backend] Starting FastAPI on :8000..."
uvicorn backend.app.main:app --reload --port 8000 --app-dir "$SCRIPT_DIR" &
BACKEND_PID=$!

# Start frontend
echo "[frontend] Installing deps..."
cd "$SCRIPT_DIR/frontend"
npm install --silent
echo "[frontend] Starting Vite on :5173..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "  Backend:  http://localhost:8000/api/health"
echo "  Frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both servers."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
