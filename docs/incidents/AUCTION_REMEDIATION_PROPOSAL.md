# Auction Remediation Proposal

**Incident:** INC-20260730-01  
**Source:** `AUCTION_REMEDIATION_INVESTIGATION_20260730.md`  
**Window:** REMEDIATION PLANNING  
**Status:** DESIGN COMPLETE / DECISION PENDING  
**Implementation:** NOT AUTHORIZED  
**Production Change:** NOT ALLOWED

## 1. Problem Statement

The Morning Auction incident is not a verified provider-availability failure. During the controlled production comparison, the same `golden-pit` request returned ten rows from one worker and timed out to an empty result from another. Provider data was available during the incident window.

The confirmed problem is the combination of:

```text
Worker-local resource exhaustion
  +
Failure state not propagated
  +
Runtime path fragmentation
```

The user-visible symptom, "auction data missing," is therefore downstream of three distinct runtime defects:

1. One Uvicorn worker reached its full per-process SQLAlchemy pool capacity and could not authenticate `/api/analyze` requests.
2. Blocking provider failures or timeouts were converted into `None`, then into an HTTP 200 partial response with empty data and incomplete diagnostic state.
3. Ordinary auction analysis and `golden-pit` use different collectors, executors, QC behavior, and response projections; deployed production source is not reproducibly represented by the current Git SOT.

This proposal designs repair options. It does not select a production change, alter an API contract, change pool parameters, add a fallback, replace a provider, or implement code.

## 2. Fix Option 1 - Worker Resource Isolation

### Objective

Prevent a single long-running or stuck request set from retaining every database connection and degrading all auction work assigned to one worker.

### Problem

`/api/analyze` obtains a database-backed user and usage state near request start, performs external provider/search/LLM work, and writes usage near request end. A connection may remain checked out for the lifetime of the long request. Worker PID `2907242` held the full effective pool capacity and also showed elevated thread and socket usage.

Changing pool capacity would change only the saturation threshold. It would not establish correct connection ownership, cancellation, or resource release.

### Evidence

- Effective per-worker pool: `QueuePool`, size 5, overflow 10, timeout 30 seconds, recycle disabled.
- PID `2907242`: 15 database file descriptors, 34 threads, and 24 socket descriptors.
- Other workers: one database file descriptor each at the same observation point.
- Twenty-one pool checkout timeouts on 2026-07-30 came from PID `2907242`.
- Stack traces end at authentication's user query before the auction provider path executes.
- Database descriptors in the degraded worker had accumulated across multiple dates.

### Potential Solution

Design the implementation around **short, explicit database ownership** and **bounded external work**, in this order:

1. **Separate database phases.** Authentication and quota read form a short read phase. Provider/search/LLM execution occurs without an owned database connection. Usage recording forms a separate short write phase after a result reaches a recordable terminal state.
2. **Define request terminal states.** Success, provider degradation, application timeout, cancellation, client disconnect, and unexpected exception must all release request-scoped resources through one audited lifecycle.
3. **Bound external execution.** Assign explicit end-to-end and per-operation time budgets. Cancellation must stop admission of new work and prevent timed-out tasks from retaining database or executor ownership.
4. **Isolate blocking work by domain.** Auction provider work should use a bounded, observable execution resource rather than the event loop's shared default executor. Resource queues and saturation must be visible per worker.
5. **Use worker lifecycle controls only as containment.** A health supervisor or graceful worker replacement may limit blast radius after a worker becomes unhealthy, but must not be accepted as the primary fix for retained resources.

This is the preferred design direction. Exact session boundaries and execution primitives remain implementation-window decisions.

### Trade-off

- Short database phases reduce saturation risk but introduce consistency questions between quota read and usage write.
- A separate write phase must define idempotency so retries or disconnects do not double-count usage.
- Strict time budgets improve isolation but may increase explicit degraded responses during slow upstream periods.
- Dedicated bounded execution prevents cross-domain starvation but adds queueing, metrics, and lifecycle complexity.
- Worker replacement can restore capacity but may interrupt in-flight requests and conceal the underlying defect if used alone.

### Validation Needed

- Record pool checkout/check-in with request ID and worker PID; prove checked-out connections return to baseline.
- Exercise success, provider timeout, LLM timeout, unexpected exception, cancellation, and client disconnect.
- Run concurrent ordinary auction requests above expected peak load without changing pool parameters.
- Verify no connection is held during provider/search/LLM waiting periods.
- Verify quota and usage semantics under retries and partial failures.
- Demonstrate that degrading one auction execution resource does not exhaust authentication/database capacity.
- Test every Uvicorn worker directly or through a worker-identifying diagnostic header in a non-production validation environment.

## 3. Fix Option 2 - Error Propagation

### Objective

Replace silent empty-success behavior with an explicit, machine-readable degradation state that reaches every consumer.

Target behavior:

```text
Failure
  -> Explicit degraded status
  -> Consumer aware
  -> User-visible boundary
```

Not:

```text
Failure
  -> None
  -> HTTP 200 empty
  -> Valid-empty interpretation
```

### Problem

Provider helpers catch broad exceptions and return `None`. The collector can distinguish timeout, provider error, empty result, and optional skip, but `golden_pit()` does not bind its `_dimension_status` into response QC. An empty candidate list is returned with HTTP 200, `partial`, a nominal real source, and no causal dimensions.

Transport success is being allowed to resemble evidence success. In a financial runtime, a valid empty market result and an unobserved result caused by execution failure must not share the same consumer interpretation.

### Evidence

- On PID `2907242`, `golden-pit` returned HTTP 200, `partial`, and `count=0` at the dimension timeout boundary.
- On PID `2907240`, the same request returned HTTP 200, `success`, and ten rows.
- `_safe_auction_dimension()` creates status values for timeout and provider error.
- Low-level `_fetch_*` helpers swallow exceptions and return `None`, erasing original error type and message.
- `golden_pit()` ignores `_dimension_status` and emits a generic partial QC record.
- The response lists `eastmoney_auction` and `source_type=real` even when no evidence row was admitted.

### Potential Solution

Design one auction evidence-state schema before changing any response contract. The schema should distinguish:

| Field | Design purpose |
|---|---|
| `status` | `success`, `partial`, `degraded`, or `failure` at the evidence layer |
| `reason_code` | Stable reason such as `provider_timeout`, `worker_saturated`, `provider_error`, `valid_empty`, or `not_ready` |
| `dimension_status` | Per-dimension state, latency, source, admitted row count, and error reference |
| `evidence_admitted` | Whether any verified provider row passed QC |
| `missing_dimensions` | Required dimensions not available to the consumer |
| `timeout_dimensions` | Dimensions that exceeded their declared time budget |
| `source_attribution` | Source only for evidence actually received and admitted |
| `request_id` / `worker_id` | Trace correlation without exposing sensitive internals to ordinary users |
| `consumer_action` | Render data, render partial boundary, retry if allowed, or stop |

Design rules:

1. Preserve the original exception at the collector boundary; sanitize only at the external response boundary.
2. Define `valid_empty` independently from `fetch_failed` and `timed_out`.
3. Compute aggregate QC from dimension states rather than the length of the projected candidate list alone.
4. Do not claim a real source for a dimension from which no evidence was received.
5. Define frontend rendering for success, partial-with-evidence, degraded-without-evidence, failure, and not-ready market phase.
6. Maintain HTTP status and response compatibility decisions as a separate contract review. This planning window does not choose or modify them.

### Trade-off

- Richer state improves truthfulness but increases schema and frontend complexity.
- Exposing raw provider errors can leak internals; stable reason codes and server-side trace references are safer.
- Changing HTTP status may break existing consumers; keeping HTTP 200 requires consumers to treat QC as authoritative. The contract decision needs an inventory of consumers first.
- More explicit degradation may appear as a higher error rate even though it is a more accurate representation of existing failures.
- Retry guidance can amplify a saturated worker unless admission control and backoff are designed together.

### Validation Needed

- Contract fixtures for valid empty, partial evidence, provider timeout, provider exception, worker saturation, market-not-ready, and full success.
- Schema validation at collector, API projection, and frontend boundaries.
- Consumer inventory proving how the web page, market-context, MCP, monitoring, and any automated clients interpret each state.
- Browser tests proving degraded-without-evidence cannot render as a valid empty market result.
- Trace correlation from response reason code to server-side dimension and worker evidence.
- Compatibility review before any HTTP status or response-field change is authorized.

## 4. Fix Option 3 - Runtime Path Consolidation

### Objective

Replace multiple collector, executor, and QC implementations with one canonical auction evidence pipeline and consumer-specific projections.

### Problem

Production currently has two user-facing auction paths:

```text
Path A - Ordinary auction analysis
auction.html
  -> POST /api/analyze
  -> app/routers/api.py
  -> app/auction_data.py:get_validated_auction_data
  -> module ThreadPoolExecutor(max_workers=4)
  -> full time gate and auction QC
  -> analysis/LLM projection

Path B - Golden-pit trigger
auction.html
  -> GET /api/intel/golden-pit
  -> app/routers/intel.py:_get_auction_data
  -> shared event-loop default executor
  -> reduced QC
  -> candidate projection
```

The local repository instead contains `scripts/auction_data.py`, `server_scripts/intel_api.py`, and `app/auction.html`. Production contains `app/auction_data.py`, `app/routers/*.py`, and `static/app/auction.html`, without Git metadata. Therefore no deployed, versioned canonical module is currently established.

### Evidence

- Path A and Path B call the same low-level helpers through different collectors.
- They use different executor ownership and timeout behavior.
- Only Path A applies the full 2026-07-17 time gate and QC path.
- Path B collects dimension status but does not propagate it.
- The production module layout and hashes cannot be mapped to the current repository commit from the host.
- The current state is `Canonical Path: UNKNOWN`, `Legacy Path: EXISTS`, `Hotfix Coverage: PARTIAL`.

### Potential Solution

First establish a production runtime inventory, then design this target:

```text
Canonical Auction Collector
  -> Canonical Bounded Executor Policy
  -> Canonical Dimension Evidence Model
  -> Canonical Time Gate and QC
  -> Auction Evidence Result
       +-> Ordinary analysis projection
       +-> Golden-pit candidate projection
       +-> Market-context projection
       +-> MCP/tool projection, if retained
```

The canonical layer owns data collection, execution limits, time/freshness gates, per-dimension evidence status, and aggregate QC. Consumers own only their projections and presentation rules. A consumer must not fetch the provider independently or reinterpret failure as empty.

Planning sequence:

1. Inventory exact production files, hashes, routes, imports, service entrypoint, and deployment procedure.
2. Reconcile deployed code into a reviewed Git branch before selecting a canonical module.
3. Enumerate all runtime consumers and their contracts.
4. Select one collector based on demonstrated behavior and testability, not filename history.
5. Define adapter boundaries so projections cannot call low-level `_fetch_*` helpers directly.
6. Create a staged retirement map for legacy paths; deletion or merging requires separate authorization.

### Trade-off

- Consolidation reduces drift but has the broadest blast radius and consumer compatibility risk.
- Reconciling production into Git may reveal undocumented dependencies that delay implementation.
- A single logical pipeline can become a shared failure point unless its execution resources and projections remain isolated.
- Staged migration temporarily preserves parallel paths, so parity telemetry is required until retirement.
- Choosing canonical code before runtime inventory would risk fixing a non-production path.

### Validation Needed

- Complete route/import/deployment inventory with production hashes mapped to a reviewed commit.
- Consumer contract matrix covering the web frontend, `/api/analyze`, `golden-pit`, market-context, MCP/tool use, and monitoring.
- Golden dataset and failure fixtures executed against old and proposed projections.
- Parity checks for admitted evidence, time gate, QC, source attribution, and failure states.
- Load and hanging-provider tests for the canonical executor policy.
- A staged migration plan with observability, rollback criteria, and explicit legacy retirement authorization.
- Proof that no production consumer still calls a legacy collector before removal is considered.

## 5. Decision Matrix

| Option | Problem Addressed | Risk | Dependency | Priority |
|---|---|---|---|---|
| Worker Resource Isolation | Worker-local pool and execution-resource saturation; DB connections retained across long work | Medium-High: session-boundary consistency, cancellation, idempotent usage recording | Request/task ownership telemetry; concurrency model; controlled reproduction | **P0** |
| Error Propagation | Failure converted to `None`, incomplete QC, HTTP 200 empty interpreted as valid result | Medium: response compatibility and consumer behavior | Evidence-state schema; consumer inventory; contract review | **P0**, designed with Option 1 |
| Runtime Path Consolidation | Multiple collectors, executors, QC paths, and unversioned production drift | High: broad consumer and deployment blast radius | Production runtime inventory; source reconciliation; Options 1 and 2 contracts | **P1**, prerequisite work starts first |

### Decision Recommendation

Do not treat the options as mutually exclusive:

1. **First prerequisite:** reconcile the production runtime and add diagnostic observability in an authorized validation environment.
2. **First repair tranche:** implement Worker Resource Isolation and Error Propagation together. Isolation without truthful errors leaves silent degradation; truthful errors without isolation leaves the outage mechanism active.
3. **Second repair tranche:** migrate consumers to the canonical pipeline after the evidence-state and execution contracts are proven.
4. **Final tranche:** retire legacy paths only after parity, traffic, and consumer checks prove they are unused.

No option recommends increasing pool capacity, adding fallback data, or changing Provider.

## 6. Cross-Option Validation Gates

An implementation window must not claim recovery until all applicable gates pass:

| Gate | Required proof |
|---|---|
| Resource ownership | Connections, threads, tasks, and sockets return to bounded baseline after every terminal state |
| Worker parity | Identical requests have equivalent evidence/QC outcomes across all workers |
| Failure truth | Timeout, exception, saturation, valid empty, and market-not-ready remain distinguishable end to end |
| Consumer awareness | Every active consumer handles explicit degraded state without presenting valid empty data |
| Canonical routing | Every active auction consumer is mapped to the selected versioned collector |
| Provider boundary | Provider availability and worker availability are measured separately |
| Production SOT | Deployed hashes map to an approved commit and rollback artifact |

## 7. Proposed Implementation Windows

This planning record authorizes none of these windows. They are proposed decision units:

1. **W1 - Runtime Inventory and Instrumentation Design**  
   Establish deploy-source identity, consumer inventory, request correlation, and measurable resource ownership.

2. **W2 - Resource Lifecycle Implementation**  
   Implement and test short database phases, bounded execution, cancellation, and usage-write idempotency without changing pool parameters.

3. **W3 - Failure Contract Implementation**  
   Implement the approved evidence-state schema and consumer handling after contract review.

4. **W4 - Canonical Pipeline Migration**  
   Move projections one at a time, run parity evidence, and retain rollback. Legacy deletion is a separate gate.

5. **W5 - Production Validation**  
   Validate every worker and frontend branch under approved change control. Production recovery is not established before this window passes.

## 8. Relationship to Runtime Trust Principles

This incident illustrates a narrow runtime reliability chain:

```text
Data Input
  -> Runtime Processing
  -> Failure Expression
  -> Output Reliability
```

Provider data can be available while runtime processing is degraded. If the failure state is then represented as valid empty data, output reliability is lost even though transport succeeded. The remediation design therefore requires evidence state and failure state to remain distinguishable through collection, execution, QC, API projection, and frontend interpretation.

## 9. Planning Boundary

```text
Remediation Planning: COMPLETE
Implementation Authorization: NOT GRANTED
Pool Parameter Change: NONE
Fallback Added: NONE
Provider Changed: NONE
API/Response Contract Changed: NONE
Python/YAML Change: NONE
Production Restart/Deploy: NONE
```

Auction Remediation Planning Complete.  
No production changes performed.
