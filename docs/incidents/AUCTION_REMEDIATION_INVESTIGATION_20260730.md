# Auction Remediation Investigation

**Incident:** INC-20260730-01  
**Date:** 2026-07-30  
**Status:** RCA REFINEMENT COMPLETE  
**Window:** Diagnosis Enhancement Only  
**Boundary:** No production code, configuration, database, service, or deployment change was performed.

## 1. Investigation Scope

This window deepens the production SOT behind `INCIDENT_RCA_CARD_AUCTION_20260730.md`. It does not implement or validate a repair. Evidence was collected read-only from the deployed service, active process state, service journal, HTTP responses, deployed source, and the local repository.

The production runtime is:

```text
www.touziagent.com
  -> finance-suite.service
  -> uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
  -> /home/ubuntu/finance-suite-web
```

The four worker processes have been alive since 2026-07-17 09:59:55 CST. Production has no Git metadata, so its files cannot be tied to a production commit from the host itself.

## 2. Connection Pool Findings

### Observed

- Production constructs the engine with `create_engine("sqlite:///./finance_suite.db", connect_args={"check_same_thread": False})`; no pool arguments are explicit.
- The effective pool is SQLAlchemy `QueuePool`:

```text
pool_size: 5
max_overflow: 10
pool_timeout: 30.0 seconds
pool_recycle: -1 (disabled)
```

- On 2026-07-30 the journal contains 21 pool timeout exceptions, all from worker PID `2907242`:

```text
QueuePool limit of size 5 overflow 10 reached,
connection timed out, timeout 30.00
```

- The exception occurs while `get_current_user()` performs a user query for requests including `POST /api/analyze`. The API returns HTTP 500.
- Read-only `/proc` inspection showed this worker holding exactly 15 file descriptors to `finance_suite.db`, matching `pool_size + max_overflow`. Other workers held one database descriptor each:

| Worker PID | DB file descriptors | Threads | Socket descriptors |
|---|---:|---:|---:|
| 2907239 | 1 | 8 | 7 |
| 2907240 | 1 | 29 | 10 |
| 2907241 | 1 | 18 | 7 |
| 2907242 | 15 | 34 | 24 |

- The 15 descriptors in PID `2907242` were opened across multiple dates, including 2026-07-17, 2026-07-21, 2026-07-27, 2026-07-28, and 2026-07-30. They were not a single short burst.
- The same process had multiple long-lived outbound HTTPS sockets, including `CLOSE-WAIT` sockets.
- `get_db()` has a `finally: db.close()` cleanup. However, `/api/analyze` acquires and queries the session near request start, performs provider/search/LLM work, and writes usage near request end. The transaction-bound connection can therefore remain checked out for the entire long request.

### Evidence

- Deployed `app/database.py:14-17,59-65`: implicit QueuePool configuration and dependency cleanup.
- Deployed `app/routers/api.py:697-710`: `/analyze` obtains `get_current_user` and `get_db`, then queries usage.
- Deployed `app/routers/api.py:1092-1099`: usage write/commit occurs only near the end of the analysis path.
- System journal between 09:35 and 10:46 CST: 21 pool timeout traces from PID `2907242`, with the stack ending in `app/auth.py:get_current_user` pool checkout.
- `/proc/<pid>/fd`, `/proc/<pid>/task`, and socket-state inspection supplied the process comparison above.

### Inference

- **Strongly supported:** PID `2907242` has reached its per-process configured pool capacity. Increasing pool size is not proven to repair the underlying lifecycle problem.
- **Strongly supported:** saturation is worker-local, not a uniform database outage. The other three workers do not show the same database descriptor state.
- **Likely mechanism, not yet verified by request/task trace:** long-running or stuck `/api/analyze` requests retain database sessions while waiting on external operations. Because dependency cleanup occurs after request completion, a hung request also prevents connection return.
- The old descriptor dates plus the worker-local 15/15 state are evidence of retained connections. They are consistent with a leak from the pool's perspective, but they do not by themselves prove that `db.close()` is missing or defective; stuck request lifetimes can produce the same state.

### Unknown

- Which 15 request/task instances own the checked-out sessions.
- Whether each owning request is still executing Python, blocked on an outbound call, or waiting on executor capacity.
- Which external operation first caused the retained request set.
- Whether connection invalidation, cancellation, or response disconnect handling contributes.

## 3. Worker Path Findings

### 3.1 Ordinary Morning Auction Path

```text
auction.html
  -> POST /api/analyze {skill_type: "auction"}
  -> app.routers.api.analyze
  -> get_current_user / get_db
  -> check_usage_allowed
  -> app.auction_data.get_validated_auction_data
  -> AkShare / Eastmoney dimensions
  -> QC + formatting + LLM response
  -> usage commit
  -> HTTP response
```

**Verified failure boundary:** On PID `2907242`, authentication cannot check out a database connection. The request fails with HTTP 500 before auction provider execution. This is a **worker/backend failure**, not evidence of provider failure.

### 3.2 Golden-Pit Path

```text
auction.html trigger match
  -> GET /api/intel/golden-pit
  -> app.routers.intel.golden_pit
  -> app.routers.intel._get_auction_data
  -> six _safe_auction_dimension tasks
  -> event-loop default ThreadPoolExecutor
  -> app.auction_data._fetch_* helpers
  -> AkShare / Eastmoney
  -> candidate projection
  -> HTTP 200 + QC envelope
```

Eight consecutive read-only requests provided a worker-controlled comparison:

| Worker | Requests | Result | Latency |
|---|---:|---|---|
| PID 2907242 | 3 | HTTP 200, `partial`, `count=0` | 5.64-6.54 s |
| PID 2907240 | 5 | HTTP 200, `success`, `count=10` | 1.67-2.95 s |

The endpoint, reverse proxy, route, provider date, and request payload were the same. The response difference tracks the selected Uvicorn worker.

### Failure Boundary Decision

| Boundary | Finding | Status |
|---|---|---|
| Provider | The same deployed provider functions returned core datasets in a fresh production process, and PID `2907240` returned ten candidates during the controlled sequence. | **AVAILABLE / NOT THE COMMON FAILURE** |
| Worker | PID `2907242` alone returned empty data at dimension timeout and simultaneously held 15 DB descriptors, 34 threads, and 24 socket descriptors. | **VERIFIED DEGRADED** |
| API | Router completed and returned valid JSON with HTTP 200. It did not expose dimension failure details. | **TRANSPORT OK; FAILURE SEMANTICS DEFECTIVE** |

### Timeout and Exception Handling

- `_safe_auction_dimension()` applies `asyncio.wait_for()` around `run_in_executor(None, ...)`; it records timeout or provider error.
- Cancelling/timing out the asyncio future does not guarantee termination of the already-running blocking provider function. Repeated slow calls can therefore continue occupying default-executor threads. Thread exhaustion is a supported inference from the worker state, not yet a stack-level verification.
- Each provider helper in `app/auction_data.py` catches every exception and returns `None`. This erases the original exception before `_safe_auction_dimension()` can label it `provider_error`; it is observed only as empty data.
- `_get_auction_data()` creates `_dimension_status`, but `golden_pit()` does not bind it into the response QC. It emits generic `partial` with HTTP 200 when no candidates exist.
- No worker abnormal exit was found. The degraded worker remained alive and served responses; the failure mode is poisoned/depleted execution capacity, not process exit.

### Empty Data Production Point

```text
blocking provider call
  -> helper catches exception and returns None
     OR caller timeout yields None
  -> _get_auction_data stores None plus internal dimension status
  -> golden_pit finds no candidates
  -> API discards dimension status
  -> HTTP 200 / partial / data=[] / count=0
```

Thus `data=[]` is constructed in the backend response layer. It is not a verified raw provider response.

## 4. Path Divergence Map

### Deployed Production Paths

```text
Frontend: static/app/auction.html
  |
  +-- Path A: ordinary query
  |     POST /api/analyze
  |       -> app/routers/api.py
  |       -> app/auction_data.py:get_validated_auction_data
  |       -> module ThreadPoolExecutor(max_workers=4)
  |       -> time gate + full auction QC
  |       -> LLM/runtime response
  |
  +-- Path B: golden trigger (黄金坑/四重门/hjk/ghk)
        GET /api/intel/golden-pit
          -> app/routers/intel.py
          -> private _get_auction_data
          -> event-loop default executor
          -> direct _fetch_* reuse
          -> candidate-only response, reduced QC
```

These paths share low-level fetch helpers but do not share collection, timeout, QC, or response semantics.

### Repository vs Production Drift

The local repository at HEAD `cdac1ca7333ebfa80313f00690153961a9a0b75a0` contains:

```text
app/auction.html
scripts/auction_data.py
server_scripts/intel_api.py
```

Production instead serves:

```text
static/app/auction.html
app/auction_data.py
app/routers/intel.py
app/routers/api.py
```

Production has no Git metadata, and `app/auction_data.py` is absent from the current repository SOT. Therefore the earlier assertion that `scripts/auction_data.py` is the single canonical runtime data layer is not true for the deployed service.

### Drift Classification

```text
Canonical Path: UNKNOWN (not established in deployed, versioned SOT)
Legacy Path: EXISTS (local scripts/server_scripts layout remains)
Hotfix Coverage: PARTIAL
```

`POST /api/analyze` contains the 2026-07-17 time gate and full QC. `GET /api/intel/golden-pit` is a parallel hotfix/specialized path with separate executor and reduced QC. The production implementation is not reproducibly represented by the current Git tree.

### Canonical Repair Direction

The canonical direction is **found at the architectural level but not yet embodied by one deployable source path**:

```text
one versioned auction evidence service
  -> one bounded provider execution policy
  -> one dimension-status/QC contract
  -> ordinary analysis projection
  -> golden-pit candidate projection
```

This is a fix proposal, not an implementation claim. Selecting the exact module requires first reconciling production files into the versioned repository.

## 5. Confirmed Root Causes

### RC-1: Worker-Local Database Pool Saturation

**Root cause status:** CONFIRMED  
**Classification:** BACKEND_FAILURE

PID `2907242` holds the full effective pool capacity of 15 database descriptors. Authentication pool checkout then times out and `/api/analyze` returns HTTP 500. Pool capacity is the failure threshold, not the canonical repair; the reason connections remain owned must be resolved in the fix window.

### RC-2: Worker-Local Blocking Execution Degradation

**Root cause status:** CONFIRMED at worker boundary; deeper task owner remains unknown  
**Classification:** BACKEND_FAILURE

Identical golden-pit requests succeed on PID `2907240` and return empty at timeout on PID `2907242`. The provider is demonstrably available during the same sequence. Therefore the incident is not a common provider failure; it is worker-local execution degradation.

### RC-3: Failure Evidence Suppression

**Root cause status:** CONFIRMED  
**Classification:** API_FAILURE (diagnostic/contract contribution)

Provider helpers suppress exceptions, and the route omits collected dimension status. The API converts a degraded worker result into HTTP 200 with generic partial QC. This does not create worker depletion, but it creates the user-visible empty-success behavior and prevents the response from locating the fault.

### RC-4: Unversioned Parallel Runtime Paths

**Root cause status:** CONFIRMED  
**Classification:** ARCHITECTURE_DRIFT

Two production auction collectors have different executor and QC behavior, while the deployed module layout is absent from the repository SOT. A repair applied only to the repository's legacy layout or only one production route cannot be claimed to cover Morning Auction.

## 6. Remaining Unknowns

1. The exact Python task/request owning each of PID `2907242`'s 15 checked-out database connections.
2. The blocking call stacks occupying the degraded worker's threads and the first operation that caused depletion.
3. Whether client disconnects or cancellation leave long-running analysis tasks alive.
4. Whether the module-level four-thread auction executor used by `/api/analyze` is also depleted; no authenticated controlled trace was executed in this window.
5. The deployment process that produced `/home/ubuntu/finance-suite-web`, and the commit from which each production file originated.
6. Which current implementation is formally owned as canonical. Production behavior establishes that no single canonical path is presently enforced.

## 7. Proposed Fix Window

Open a separate, authorized implementation window only after production source is reconciled into Git. The window should take these inputs:

### Gate A: Make Production Reproducible

- Import the exact deployed source into a reviewed branch or prove its source commit by hashes.
- Declare one auction evidence service as canonical.
- Map both frontend branches and every MCP/market-context consumer to that service before changing behavior.

### Gate B: Prove Request and Resource Ownership

- Add per-worker request ID, active request, pool checkout/check-in, and provider-dimension duration telemetry.
- Capture task/thread stacks under a controlled reproduction.
- Establish separate time budgets for request, dimension, and blocking call; prove how cancellation releases resources.

### Gate C: Shorten Database Ownership

- Design authentication/usage reads and final usage write so a database connection is not held across provider, search, or LLM waits.
- Verify connection return on success, timeout, exception, and client disconnect.
- Do not use a larger pool as the acceptance criterion; prove bounded checked-out connections under concurrency.

### Gate D: Unify Provider Execution and QC

- Route both ordinary auction and golden-pit projections through the same bounded provider collector.
- Preserve original exception class, timeout dimension, source, and latency in QC.
- Do not report provider-derived sources or `source_type=real` when zero evidence rows were admitted.
- Ensure executor cancellation/resource behavior is tested with deliberately hanging provider calls.

### Required Validation

- Reproduce both frontend branches against every worker, not merely the load-balanced endpoint.
- Prove no worker-specific response divergence.
- Prove pool checkouts return to baseline after success, provider timeout, LLM timeout, exception, and disconnect.
- Verify Trust Gate output for success, partial, timeout, and failure.
- Deploy/restart only under a separately approved production change window.

## Final State

```text
RCA Refinement: COMPLETE
Connection Pool Evidence: FOUND
Worker / Provider / API Boundary: VERIFIED
Architecture Drift Scope: VERIFIED
Canonical Runtime Path: NOT YET ESTABLISHED
Fix Proposal: DEFINED, NOT IMPLEMENTED
Production Changes: NONE
```

RCA refinement complete. No production changes performed.
