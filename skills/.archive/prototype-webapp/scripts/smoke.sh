#!/usr/bin/env bash
set -euo pipefail
APP_DIR="${1:-.}"
PORT="${2:-3000}"
BASE="http://localhost:${PORT}"

echo "[1] npm install"
(cd "$APP_DIR" && npm install --silent)

echo "[2] start app"
(cd "$APP_DIR" && node server.js) &
PID=$!
sleep 2

echo "[3] smoke /"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/" || true)
echo "/ status=$STATUS"
test "$STATUS" = "200" || { echo "FAIL: / expected 200 got $STATUS"; kill "$PID"; exit 1; }

echo "[4] cleanup"
kill "$PID"
echo "smoke ok"
