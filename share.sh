#!/usr/bin/env bash
# Share your local VELORA with anyone (temporary public URL)
set -euo pipefail
cd "$(dirname "$0")"
PORT="${PORT:-4173}"

pip install -q -r requirements.txt
if ! python3 -c "import fastapi" 2>/dev/null; then pip install -r requirements.txt; fi

if lsof -i:"$PORT" >/dev/null 2>&1; then
  echo "Server already on port $PORT"
else
  echo "Starting VELORA on port $PORT..."
  python3 server.py &
  sleep 2
fi

echo ""
echo "=== Share this link with anyone ==="
echo "(Press Ctrl+C to stop the tunnel)"
echo ""
npx --yes localtunnel --port "$PORT"
