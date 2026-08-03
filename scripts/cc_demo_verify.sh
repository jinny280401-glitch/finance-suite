#!/usr/bin/env bash
# D29 Demo Entry Verification — for C to run
# CC has already started the static server on 127.0.0.1:8765 (PID stored at /tmp/cc_demo_server.pid)
# This script verifies each candidate demo entry returns HTTP 200.

set -uo pipefail
PORT=8765
BASE="http://127.0.0.1:${PORT}"

# Candidate demo entries from D29_PACKAGE_CHECKLIST §3
PATHS=(
  "/"
  "/app/index.html"
  "/app/stock.html"
  "/app/deep-research.html"
  "/app/macro.html"
  "/app/auction.html"
)

echo "=== server liveness ==="
PID=$(cat /tmp/cc_demo_server.pid 2>/dev/null || echo "")
if [ -n "$PID" ] && ps -p "$PID" > /dev/null 2>&1; then
  echo "server alive: pid=$PID port=$PORT"
else
  echo "WARN: server PID $PID not running — restart with:"
  echo "  cd /Users/Zhuanz/finance-suite && python3 -m http.server $PORT --bind 127.0.0.1 &"
  exit 1
fi

echo
echo "=== HTTP probe each demo entry ==="
for path in "${PATHS[@]}"; do
  resp=$(curl -sS -o /dev/null -w '%{http_code}|%{size_download}|%{time_total}' --max-time 5 "${BASE}${path}" 2>&1)
  printf '%-32s %s\n' "$path" "$resp"
done

echo
echo "=== inspect index.html head (verify it points to expected first-visit screen) ==="
curl -sS --max-time 5 "${BASE}/app/index.html" | head -20

echo
echo "=== inspect auction.html head (RISK: INC-01 OPEN, do not run live) ==="
curl -sS --max-time 5 "${BASE}/app/auction.html" | head -20

echo
echo "=== when done, stop server with: ==="
echo "  kill \$(cat /tmp/cc_demo_server.pid)"
