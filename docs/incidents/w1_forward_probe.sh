#!/bin/bash
# W1 Forward Observation Probe — Auction 09:25-09:30 Production Capability
#
# Purpose: capture what production ACTUALLY returns inside 09:25:00-09:30:00,
#          with full response body retained + SHA-256, so that content evidence
#          exists (P0 failed precisely because no body was ever retained).
#
# READ-ONLY. Does not modify production, code, config, or any provider.
# Only issues HTTPS GETs against a public endpoint and writes files locally.

set -uo pipefail

# Enforce the declared timezone for all date calculations and timestamps.
export TZ=Asia/Shanghai

ENDPOINT="https://www.touziagent.com/api/intel/market-context"

# Unique run isolation: directory includes start datetime + PID so concurrent or
# repeated invocations on the same calendar day cannot overwrite each other.
RUN_ID="$(date '+%Y%m%dT%H%M%S')_$$"
OUTDIR="/Users/Zhuanz/finance-suite/docs/incidents/w1_evidence_${RUN_ID}"
mkdir -p "$OUTDIR"

LOG="$OUTDIR/probe_log.txt"
DIMENSIONS="$OUTDIR/dimensions.txt"

log() { echo "[$(date '+%Y-%m-%dT%H:%M:%S%z')] $*" | tee -a "$LOG"; }

log "W1 probe start. endpoint=$ENDPOINT outdir=$OUTDIR run_id=$RUN_ID"
log "Capture plan: one request every ~30s from 09:24:30 to 09:31:00 Asia/Shanghai"
log "Timezone enforced: TZ=$TZ"

# Capture loop: run until 09:31:00, sample every ~30s.
# Includes 09:24:xx (expected blocked) and 09:30:xx (expected outside window)
# as controls, so the 09:25-09:29 window can be compared against both sides.
while true; do
  # Force base-10: date emits a leading zero (e.g. 092430), which bash
  # arithmetic would otherwise read as octal.
  NOW_HHMMSS=$((10#$(date +%H%M%S)))
  # stop after 09:31:00
  if [ "$NOW_HHMMSS" -gt $((10#093100)) ]; then
    log "Past 09:31:00, stopping."
    break
  fi
  # don't start before 09:24:30
  if [ "$NOW_HHMMSS" -lt $((10#092430)) ]; then
    sleep 5
    continue
  fi

  TS_START=$(date '+%Y-%m-%dT%H:%M:%S%z')
  BODY="$OUTDIR/response_${TS_START}.json"
  HDR="$OUTDIR/headers_${TS_START}.txt"

  CODE=$(curl -s --max-time 25 \
    -o "$BODY" -D "$HDR" \
    -w '%{http_code}' \
    "$ENDPOINT" 2>>"$LOG" || echo "CURL_FAIL")

  TS_END=$(date '+%Y-%m-%dT%H:%M:%S%z')

  if [ -s "$BODY" ]; then
    SHA=$(shasum -a 256 "$BODY" | awk '{print $1}')
    SIZE=$(wc -c < "$BODY" | tr -d ' ')
  else
    SHA="EMPTY_BODY"
    SIZE=0
  fi

  log "sample start=$TS_START end=$TS_END http=$CODE bytes=$SIZE sha256=$SHA"

  # Extract the decision-relevant fields immediately, so the verdict does not
  # depend on re-reading many files later. The full response body remains the
  # authoritative evidence; this file is only a convenience index.
  python3 - "$BODY" "$TS_START" "$TS_END" "$CODE" "$SIZE" "$SHA" >> "$DIMENSIONS" 2>>"$LOG" <<'PY'
import json, sys
path, ts_start, ts_end, http_code, size, sha = sys.argv[1:7]
try:
    d = json.load(open(path))
except Exception as e:
    print(f"ts_start={ts_start}\tts_end={ts_end}\thttp={http_code}\tsize={size}\tsha={sha}\tPARSE_FAIL={e}")
    sys.exit()
qc = d.get("_qc", {}) or {}
# Walk the full tree for gate/phase/ready/auction-related scalar fields.
# Do not truncate lists; flatten deeply but avoid dumping full row arrays.
def walk(o, p="", out=None):
    if out is None:
        out = {}
    if isinstance(o, dict):
        for k, v in o.items():
            kp = f"{p}/{k}" if p else k
            if any(t in k.lower() for t in ("gate", "phase", "ready", "block", "auction")):
                if isinstance(v, (str, int, float, bool)) or v is None:
                    out[kp] = v
                elif isinstance(v, dict) and v:
                    out[kp] = {sk: sv for sk, sv in v.items()
                               if isinstance(sv, (str, int, float, bool)) or sv is None}
            if isinstance(v, (dict, list)):
                walk(v, kp, out)
    elif isinstance(o, list):
        # descend into list items only if they are dicts (e.g. data_availability entries)
        for i, v in enumerate(o):
            if isinstance(v, (dict, list)):
                walk(v, f"{p}[{i}]", out)
    return out
deep = walk(d)
avail = d.get("data_availability", {}) or {}
print(f"ts_start={ts_start}\tts_end={ts_end}\thttp={http_code}\tsize={size}\tsha={sha}"
      f"\tstatus={d.get('status')}\tqc_status={qc.get('status')}"
      f"\tqc_source_type={qc.get('source_type')}\tcompleteness={qc.get('completeness')}"
      f"\tgate_fields={deep}\tdata_availability={avail}")
PY

  sleep 30
done

log "W1 probe complete."
log "Manifest:"
( cd "$OUTDIR" && shasum -a 256 response_*.json 2>/dev/null | tee sha256_manifest.txt ) >> "$LOG" 2>&1
log "Evidence dir: $OUTDIR"
