#!/usr/bin/env bash
# =============================================================================
# Stage A — activate pool instrumentation on production (finance-suite)
#
# STATUS: PREPARED ONLY. Not uploaded. Not executed.
# Scope:  service restart to register the already-written instrumentation.
#         Does NOT modify api.py. Does NOT fix the session-scope defect.
#
# Context: KAN_PIAO_ANALYSIS_RCA.md §6d
#   Instrumentation Artifact:  PREPARED  (app/database.py, 87 -> 142 lines)
#   Runtime Registration:      NOT ACTIVE (workers still on 2026-07-17 bytecode)
#   Activation Condition:      Service Restart Required
#
# Run on the production host as ubuntu:
#   bash stage_a_restart.sh          # full sequence, pauses before restart
#   bash stage_a_restart.sh --check  # pre-flight only, no restart
#   bash stage_a_restart.sh --rollback
#
# Restart interrupts all in-flight requests. LLM calls have a 180s timeout,
# so a user mid-analysis will be cut off. Intended for a low-traffic window.
# =============================================================================

set -uo pipefail

APP_DIR=/home/ubuntu/finance-suite-web
BACKUP=app/database.py.bak_cc_20260730-152848
SHA_BEFORE=af51165de392e6a42ad8c489bfe5dac9ed611cb451bfe23be07cb0b3042c6ddf
SHA_AFTER=d932177900a1f8066ca300e5b4ce13b1dbecba30f50c583930ded4000f32d06e
POOL_LOG=logs/pool_instrument.log
HEALTH_URL=http://127.0.0.1:8000/api/health

cd "$APP_DIR" || { echo "FATAL: $APP_DIR not found"; exit 1; }

say()  { printf '\n=== %s ===\n' "$*"; }
fail() { printf 'FAIL: %s\n' "$*"; exit 1; }

# ---------------------------------------------------------------- rollback ---
if [[ "${1:-}" == "--rollback" ]]; then
  say "ROLLBACK"
  [[ -f "$BACKUP" ]] || fail "backup missing: $BACKUP"
  sha256sum "$BACKUP" | grep -q "$SHA_BEFORE" || fail "backup sha mismatch - do not use"
  cp -p "$BACKUP" app/database.py
  sha256sum app/database.py
  echo "restored. restarting service..."
  sudo systemctl restart finance-suite
  sleep 8
  systemctl is-active finance-suite
  curl -fsS --max-time 10 "$HEALTH_URL" && echo " <- health OK"
  exit 0
fi

# --------------------------------------------------------------- pre-flight ---
say "PRE-FLIGHT 1/5 — backup exists and matches pre-change original"
[[ -f "$BACKUP" ]] || fail "backup missing: $BACKUP"
sha256sum "$BACKUP" | grep -q "$SHA_BEFORE" \
  || fail "backup sha does not match recorded pre-change hash"
echo "OK  $BACKUP"

say "PRE-FLIGHT 2/5 — current file is the instrumented version"
sha256sum app/database.py
sha256sum app/database.py | grep -q "$SHA_AFTER" \
  || fail "app/database.py is not the expected instrumented artifact"
echo "OK  matches recorded post-change hash"

say "PRE-FLIGHT 3/5 — syntax and import"
venv/bin/python3 -m py_compile app/database.py || fail "py_compile failed"
venv/bin/python3 -c 'from app.main import app; print("routes:", len(app.routes))' \
  || fail "full app import failed"
echo "OK"

say "PRE-FLIGHT 4/5 — current runtime state (pre-restart baseline)"
systemctl show finance-suite -p ActiveState -p ExecMainPID -p ExecMainStartTimestamp -p NRestarts
MASTER=$(systemctl show finance-suite -p ExecMainPID --value)
echo "--- worker db_fd counts (expect one saturated at 15) ---"
for pid in $(ps -eo pid,ppid | awk -v m="$MASTER" '$2==m {print $1}'); do
  n=$(ls -l /proc/"$pid"/fd 2>/dev/null | grep -c finance_suite.db)
  [[ "$n" == "0" ]] && continue
  printf 'PID %s  db_fd=%s\n' "$pid" "$n"
done

say "PRE-FLIGHT 5/5 — traffic check (decide if window is quiet enough)"
echo "requests in the last 5 minutes:"
journalctl -u finance-suite --since '5 min ago' --no-pager 2>/dev/null \
  | grep -c 'POST /api/analyze' || echo "(journal unreadable without privileges)"

if [[ "${1:-}" == "--check" ]]; then
  say "CHECK ONLY — stopping before restart"
  exit 0
fi

# ------------------------------------------------------------------ restart ---
say "RESTART — this interrupts all in-flight requests"
read -r -p "Type RESTART to proceed: " confirm
[[ "$confirm" == "RESTART" ]] || { echo "aborted"; exit 0; }

BEFORE_TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "restart_initiated_utc=$BEFORE_TS"
sudo systemctl restart finance-suite || fail "restart command failed"

# ----------------------------------------------------------- verification ----
say "VERIFY 1/4 — service active"
for i in $(seq 1 15); do
  state=$(systemctl is-active finance-suite)
  [[ "$state" == "active" ]] && break
  sleep 2
done
[[ "$state" == "active" ]] || fail "service not active after restart"
systemctl show finance-suite -p ExecMainPID -p ExecMainStartTimestamp -p NRestarts
echo "OK"

say "VERIFY 2/4 — worker count is 4"
NEW_MASTER=$(systemctl show finance-suite -p ExecMainPID --value)
sleep 5
WORKERS=$(ps -eo pid,ppid,cmd | awk -v m="$NEW_MASTER" '$2==m && /multiprocessing-fork/' | wc -l)
echo "workers=$WORKERS (expect 4)"
[[ "$WORKERS" == "4" ]] || echo "WARN: expected 4 workers, found $WORKERS"

say "VERIFY 3/4 — health endpoint"
curl -fsS --max-time 10 "$HEALTH_URL" || fail "health endpoint did not respond"
echo " <- OK"

say "VERIFY 4/4 — instrumentation is registered and emitting"
echo "generating one authenticated-path request to force a pool checkout..."
curl -fsS --max-time 10 -o /dev/null -w 'auth_probe_http=%{http_code}\n' \
  http://127.0.0.1:8000/api/check-auth || true
sleep 2
if [[ -f "$POOL_LOG" ]]; then
  echo "--- last 10 pool events ---"
  tail -10 "$POOL_LOG"
  if grep -q 'action=checkout' "$POOL_LOG"; then
    echo "OK  instrumentation is registered in the running workers"
  else
    echo "WARN  log exists but no checkout event yet - send real traffic and re-check"
  fi
else
  echo "WARN  $POOL_LOG absent. Instrumentation may not be active."
  echo "      Confirm the restart picked up the new database.py before concluding."
fi

# ----------------------------------------------------------------- summary ---
say "STAGE A COMPLETE"
cat <<SUMMARY
Instrumentation Artifact:  PREPARED
Runtime Registration:      ACTIVE (verify the checkout line above before trusting this)
Session-Scope Fix:         NOT WRITTEN  <- Stage B, not done here
Production Behavior:       UNCHANGED except for observability

Evidence Hold Point. Collect before entering Stage B:
  tail -f $POOL_LOG
  awk -F'held_s=' '/held_s=/ && \$2+0 > 5 {print}' $POOL_LOG   # holds over 5s
  grep -c action=checkout $POOL_LOG

The number that matters is held_s on /api/analyze requests. The hypothesis
predicts values approaching the LLM duration rather than milliseconds.

Rollback: bash stage_a_restart.sh --rollback
SUMMARY
