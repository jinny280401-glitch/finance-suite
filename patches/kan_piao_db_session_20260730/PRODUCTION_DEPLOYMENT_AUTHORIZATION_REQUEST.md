# Production Deployment Authorization Request

**Incident:** 看票分析 / worker-local DB pool saturation  
**Date:** 2026-07-30  
**Implementation review:** `PASS`  
**Production deployment:** `PENDING LOW-TRAFFIC WINDOW`  
**Production filesystem preparation:** `STARTED BY EXTERNAL OPERATOR`  
**Runtime activation:** `PENDING RESTART`  
**Application behavior change:** `NOT ACTIVE`

## Current Runtime Stabilization Window

```text
Root Cause: CONFIRMED (code-level)
Runtime Evidence: PARTIAL / WAITING INSTRUMENTATION ACTIVATION
Instrumentation On Disk: PREPARED
Instrumentation Runtime: NOT ACTIVE
Stage A Restart: READY FOR LOW-TRAFFIC WINDOW
Stage B Session Isolation: NOT AUTHORIZED / WAIT FOR STAGE A EVIDENCE
Production Behavior: UNCHANGED
Provider Integration: PAUSED / NO DEPENDENCY
```

**Authorization request:** `APPROVED FOR SCHEDULING`  
**Immediate patch/restart authorization:** `NOT GRANTED`  
**Preparation artifacts:** `APPROVED`  
**Traceability:** `PARTIAL / SHA-256 PINNED`  
**Runtime identity:** `PASS`  
**Git source revision mapping:** `UNKNOWN`

Review decision: ready for a low-traffic deployment window. Backup commands, patch commands, rollback plan and validation checklist are approved as preparation artifacts only. No immediate patch application or service restart is authorized.

Read-only recheck at `2026-07-30 15:33:56 +08:00` found that an external operator had already written observability code to `app/database.py` and created its backup. The four live workers still date from `2026-07-17`; therefore the instrumentation is present on disk but not loaded by the serving runtime.

```text
Instrumentation On Disk: PREPARED
Instrumentation Self-test: OBSERVED IN A SEPARATE DRY-RUN PROCESS
Instrumentation Active In Uvicorn Workers: NO
Runtime Activation: PENDING RESTART
```

## Execution Entry Gate

Every condition must be explicitly satisfied before the first production write:

```text
[ ] Low-traffic date/time window confirmed
[ ] Named operator approval confirmed
[ ] Current target hashes rechecked against pinned baseline
[ ] Current traffic and worker snapshot captured
[ ] Backup timestamp reserved
[ ] Rollback operator and trigger authority confirmed
```

Once the gate is open, execution order is fixed:

```text
backup
  -> verify backup and pre-change hashes
  -> stage/apply patch chain
  -> verify candidate hashes and compile
  -> restart service
  -> run health, auth, quota, analysis and pool-lifecycle validation
  -> declare success or execute rollback
```

## Current Production Baseline

Observed at `2026-07-30 15:15:37 +08:00`:

```text
finance-suite.service: active
service start: 2026-07-17 09:59:55 +08:00
restart count: 0
uvicorn application workers: 4
multiprocessing resource tracker: 1 (not an application worker)
established TCP connections to port 8000: 0
active request metric: NOT EXPOSED
QueuePool timeouts since service start: 36
QueuePool timeouts today: 36
QueuePool timeouts in prior 60 minutes: 10
/api/analyze HTTP 500 today: 8
```

Worker resource snapshot:

| PID | Role | DB FDs | Threads | Sockets |
|---:|---|---:|---:|---:|
| 2907239 | application worker | 1 | 8 | 7 |
| 2907240 | application worker | 1 | 29 | 14 |
| 2907241 | application worker | 1 | 18 | 7 |
| 2907242 | application worker / degraded | 15 | 34 | 24 |

There were no established port-8000 connections at the snapshot instant, but the application exposes no active-request counter. Therefore `active requests = 0` is **not verified**.

The attempted `GET /health` returned HTTP 404. Read-only route inspection subsequently confirmed the valid health endpoint is `GET /api/health`, implemented in `app/main.py:84-86`.

## Target Integrity

Current production on-disk SHA-256 values:

```text
app/auth.py
d5151409431e4384be97ceae29ad968e6b4c041e591233342d8c791d7cf3a804

app/database.py
d932177900a1f8066ca300e5b4ce13b1dbecba30f50c583930ded4000f32d06e

app/routers/api.py
2f78db6f78b85e3083efe0582868d5799cf6197075c049c43097888aea127889
```

## Change Manifest

| File | Before SHA-256 | Candidate after SHA-256 | Purpose |
|---|---|---|---|
| `app/auth.py` | `d5151409431e4384be97ceae29ad968e6b4c041e591233342d8c791d7cf3a804` | `62d75b5d2bc0b1818ead5f93054cbc77bc8df080690723eb0518fe583e7389cf` | Close authentication DB scope before route execution; translate pool timeout to explicit HTTP 503. |
| `app/routers/api.py` | `2f78db6f78b85e3083efe0582868d5799cf6197075c049c43097888aea127889` | `07f69b005db54dab00813cf0c2e9be7156a14d2dc07811dfc208d9cca3a3dfb8` | Split quota read and usage write into short sessions; add per-request pool lifecycle observations; remove request-wide DB dependency. |
| `app/database.py` | Original runtime source: `af51165de392e6a42ad8c489bfe5dac9ed611cb451bfe23be07cb0b3042c6ddf` | Current on-disk instrumentation: `d932177900a1f8066ca300e5b4ce13b1dbecba30f50c583930ded4000f32d06e` | Global checkout/checkin observability prepared by an external operator; not loaded by current workers. |

Patch sequence:

1. `production_backend.patch`
2. `pool_lifecycle_instrumentation.patch`

The sequence applies cleanly to the pinned `auth.py` and `api.py` snapshots, produces the candidate hashes above, compiles, and passes six isolated tests. The separate on-disk `database.py` instrumentation is not part of this patch chain.

## Required Behavioral Proof

Deployment validation must prove the resource lifecycle, not merely HTTP 200:

```text
Before
request
  -> DB checkout
  -> provider/search/LLM wait (up to 180s)
  -> DB connection remains checked out

After
request
  -> authentication DB checkout
  -> release
  -> short quota-read checkout
  -> release
  -> provider/search/LLM execution with no DB checkout
  -> short usage-write checkout
  -> commit / rollback
  -> release
```

Required evidence:

1. Pool checkout/checkin observation around an authenticated stock request.
2. `checkedout == 0` during a deliberately delayed LLM phase, excluding unrelated requests.
3. A short connection checkout only when usage is recorded.
4. Connection count returns to baseline after success, timeout and cancellation.
5. Forced pool exhaustion returns HTTP 503 plus `Retry-After`, not opaque HTTP 500.
6. Login, usage and stock-analysis behavior remain correct across all four workers.
7. No Provider, Trust Gate, QC or fallback behavior changes.

## Backup Set

An external operator already created `app/database.py.bak_cc_20260730-152848`, which matches the original pre-instrumentation file. This is evidence of preparation, not a complete deployment backup set.

After the low-traffic window and operator are authorized, create one new, common-timestamp backup set of:

```text
app/auth.py
app/database.py
app/routers/api.py
```

Record SHA-256 for originals and backups before continuing. The new `database.py` backup must capture the current instrumented file (`d932177...`); retain the earlier `152848` backup separately as the pre-instrumentation rollback point.

### Authorized-window backup commands

These commands are prepared but have not been executed:

```bash
set -euo pipefail
ROOT=/home/ubuntu/finance-suite-web
TS=$(date +%Y%m%d_%H%M%S)

cd "$ROOT"
sha256sum app/auth.py app/database.py app/routers/api.py

install -p -m 0644 app/auth.py "app/auth.py.bak_cc_${TS}"
install -p -m 0644 app/database.py "app/database.py.bak_cc_${TS}"
install -p -m 0644 app/routers/api.py "app/routers/api.py.bak_cc_${TS}"

sha256sum \
  "app/auth.py.bak_cc_${TS}" \
  "app/database.py.bak_cc_${TS}" \
  "app/routers/api.py.bak_cc_${TS}"
```

Execution must stop if any pre-change hash differs from the pinned baseline.

## Staged Restart And Fix Plan

The deployment is intentionally split by an evidence hold point.

### Stage A: Activate prepared instrumentation

At the authorized low-traffic window:

1. Recheck all hashes and create the common-timestamp backup set.
2. Compile the current on-disk files.
3. Restart the service without applying the session-isolation patches.
4. Confirm the four new workers loaded `database.py` hash `d932177...`.
5. Run one approved authenticated analysis request and collect checkout/checkin hold durations.
6. Stop at the evidence hold point. Instrumentation evidence must be reviewed before Stage B.

Stage A runtime activation commands, prepared but not executed:

```bash
set -euo pipefail
ROOT=/home/ubuntu/finance-suite-web
cd "$ROOT"

sha256sum app/auth.py app/database.py app/routers/api.py
"$ROOT/venv/bin/python" -m py_compile app/auth.py app/database.py app/routers/api.py
sudo systemctl restart finance-suite.service
sudo systemctl is-active finance-suite.service
curl -fsS http://127.0.0.1:8000/api/health
```

### Evidence hold point

Proceed to Stage B only if Stage A proves that the analysis request holds a checkout across Provider/Search/LLM and the operator authorizes continuation. If the evidence contradicts the hypothesis, do not apply the session-isolation patch.

### Stage B: Apply session isolation and request-scoped observations

Prepared production commands, not executed:

```bash
set -euo pipefail
ROOT=/home/ubuntu/finance-suite-web
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT

mkdir -p "$STAGE/app/routers"
install -p "$ROOT/app/auth.py" "$STAGE/app/auth.py"
install -p "$ROOT/app/routers/api.py" "$STAGE/app/routers/api.py"

cd "$STAGE"
git apply /tmp/production_backend.patch
git apply /tmp/pool_lifecycle_instrumentation.patch
"$ROOT/venv/bin/python" -m py_compile app/auth.py app/routers/api.py

cd "$ROOT"
git apply /tmp/production_backend.patch
git apply /tmp/pool_lifecycle_instrumentation.patch

sha256sum app/auth.py app/database.py app/routers/api.py
"$ROOT/venv/bin/python" -m py_compile app/auth.py app/database.py app/routers/api.py

sudo systemctl restart finance-suite.service
sudo systemctl is-active finance-suite.service
```

Expected restart scope:

```text
Uvicorn parent: 1
Application workers: 4
Resource tracker: 1 auxiliary process
In-flight requests: terminated by full service restart
Target interruption: approximately 3-15 seconds
Hard upper bound: UNKNOWN
```

Stage B requires a second service restart. Because no active-request metric exists, a zero-established-connection snapshot cannot prove zero in-flight work. Both restarts must remain inside a declared low-traffic window or separately approved interruption windows.

## Validation Checklist

### Immediate service checks

1. `systemctl is-active finance-suite.service` returns `active`.
2. Exactly four application workers are present after startup settles.
3. `GET http://127.0.0.1:8000/api/health` returns the expected `{"status":"ok"}` response.
4. Startup logs show no import, syntax, DB initialization or repeated worker crash error.

### Functional checks

1. Login with an authorized test account succeeds; invalid credentials remain rejected.
2. `/api/check-auth` and `/api/usage` preserve their response semantics.
3. Authenticated `/api/analyze` with an approved golden stock input returns the expected report/QC contract.
4. Provider, Trust Gate, QC and fallback selections remain unchanged.

### Resource-lifecycle checks

After Stage B, for one trace ID, journal evidence must contain:

```text
phase=quota_released
phase=before_llm
phase=after_llm
phase=usage_write_released
```

The same trace must show no connection retained by that request across the LLM interval. Worker DB resources must return to the post-start baseline after success. Timeout and cancellation tests must also return to baseline.

The production system must not be intentionally driven into pool exhaustion merely to test 503. The explicit 503 path is covered by the isolated constrained-pool test; production validation observes the response only if the condition occurs naturally or a separately authorized staging fault-injection environment is available.

## Rollback Procedure

Prepared rollback order:

1. Stop further validation traffic.
2. Restore `auth.py`, then `database.py`, then `routers/api.py` from the common-timestamp deployment backup set. To remove instrumentation entirely, use the separately retained `database.py.bak_cc_20260730-152848` only under an explicit rollback decision.
3. Verify restored hashes equal the recorded pre-change hashes.
4. Restart the full service.
5. Verify `/api/health`, worker count, login, usage and one approved analysis request.
6. Confirm rollback in the incident log; do not claim remediation success.

Prepared commands, not executed:

```bash
set -euo pipefail
ROOT=/home/ubuntu/finance-suite-web
TS='<authorized backup timestamp>'
cd "$ROOT"

install -p -m 0644 "app/auth.py.bak_cc_${TS}" app/auth.py
install -p -m 0644 "app/database.py.bak_cc_${TS}" app/database.py
install -p -m 0644 "app/routers/api.py.bak_cc_${TS}" app/routers/api.py

sha256sum app/auth.py app/database.py app/routers/api.py
"$ROOT/venv/bin/python" -m py_compile app/auth.py app/database.py app/routers/api.py
sudo systemctl restart finance-suite.service
sudo systemctl is-active finance-suite.service
curl -fsS http://127.0.0.1:8000/api/health
```

## Rollback Triggers

Rollback immediately on any of:

- Authentication or login regression.
- `/api/analyze` regression unrelated to the known pre-change saturation.
- Pool checkout retained during LLM execution.
- QueuePool exhaustion recurrence after restart and controlled validation.
- Unexpected worker count or repeated worker crash/restart.
- Failure to produce an explicit 503 under forced resource exhaustion.

## Authorization Boundary

The request is approved for scheduling, not execution. Until the low-traffic window and operator approval are both confirmed, no backup, patch transfer, patch application, service restart, production test request or rollback action may begin.

## Runtime Reliability Principle

```text
Long-running research tasks must not own transactional resources.
```

Provider, Search and LLM work may be long-running. DB connections, transactions and quota locks must remain short-scoped, observable and releasable on success, timeout, exception and cancellation. This principle applies to future institutional-provider consumers without implying any Provider capability claim.
