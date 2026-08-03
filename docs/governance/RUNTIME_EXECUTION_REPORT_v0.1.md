# Vera Runtime Execution Report v0.1

**Execution role:** C — Runtime Verification Executor  
**Execution date:** 2026-07-31 (UTC+8)  
**Rulebook:** `docs/governance/RUNTIME_VERIFICATION_FRAMEWORK_v0.1.md`  
**Window:** Runtime Verification Execution Window v0.1  
**Change policy:** Evidence collection only; no repair, deployment, or capability promotion

## 1. Execution Scope

This execution attempted the two authorized layers:

```text
Layer 3 — Application Runtime
Frontend route context -> API -> Backend -> Response

Layer 4 — Research Workflow
Research request -> Evidence input -> Processing -> Report output -> Output boundary
```

The production request used a unique, non-cached query and an existing demo
account obtained through the server-side credential handoff. No password,
token, or cookie was copied into this report.

### Explicit exclusions

- No production code or static asset modification.
- No defect repair.
- No service restart.
- No Provider or Trust Gate modification.
- No Architecture, D29, Capability Matrix, or Framework modification.
- No Auction execution.
- No Layer 5 or `LIVE VERIFIED` claim.

### Prerequisite annotation

The separate PE Band review established a production Layer 2 presentation
defect. This authorized execution therefore collects direct Layer 3 and Layer 4
evidence but does not promote the whole bottom-up chain. A direct API PASS does
not erase the Layer 2 FAIL.

## 2. Environment

| Item | Observed value |
|---|---|
| Production host | `VM-0-4-ubuntu` / `119.28.156.125` |
| Public endpoint | `https://www.touziagent.com` |
| Probe path | SSH via `admin@8.138.2.55` to `ubuntu@119.28.156.125` |
| Service | `finance-suite.service` — `active` |
| Service start | `2026-07-30 16:48:43 +08:00` |
| Service restart count | `0` |
| Uvicorn command | `uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4` |
| Process layout | 1 parent, 4 application workers, 1 resource tracker |
| Python | `3.12.3` |
| FastAPI | `0.115.0` |
| Uvicorn | `0.30.0` |
| SQLAlchemy | `2.0.35` |

### Production source fingerprints

| File | SHA-256 |
|---|---|
| `app/main.py` | `05923571dd1bb705549cf19afa0a09e55f4d650f2d757344534ffd7ed86fe1cd` |
| `app/routers/api.py` | `2f78db6f78b85e3083efe0582868d5799cf6197075c049c43097888aea127889` |
| `app/database.py` | `d932177900a1f8066ca300e5b4ce13b1dbecba30f50c583930ded4000f32d06e` |
| `app/auth.py` | `d5151409431e4384be97ceae29ad968e6b4c041e591233342d8c791d7cf3a804` |

## 3. Layer 3 Results

### L3.1 Backend Availability — PASS

| Check | Evidence | Result |
|---|---|---|
| FastAPI service | `finance-suite.service` active; four application workers observed | PASS |
| Health endpoint | `GET http://127.0.0.1:8000/api/health` -> HTTP `200`, body `{"status":"ok"}` | PASS |
| Route registration | Production OpenAPI lists `GET /api/health`, `POST /api/login`, and `POST /api/analyze` | PASS |
| Authentication path | `POST /api/login` -> HTTP `200` in `442.6 ms`; access-token cookie issued | PASS |

### L3.2 API Analysis Flow — PASS

**Request ID:** `RUNTIME-V01-20260731-1524-CST`

```json
{
  "method": "POST",
  "url": "https://www.touziagent.com/api/analyze",
  "json": {
    "skill_type": "stock",
    "query": "运行时验证 600519 贵州茅台 基本面与风险边界，请基于当前真实可用证据生成报告。Request ID: RUNTIME-V01-20260731-1524-CST"
  }
}
```

| Response property | Observed value |
|---|---|
| Started | `2026-07-31T15:22:19.317433+08:00` |
| Finished | `2026-07-31T15:23:16.309957+08:00` |
| Status | HTTP `200` |
| Latency | `56,992.0 ms` |
| Content type | `application/json` |
| Body size | `29,798 bytes` |
| Body SHA-256 | `3f68c90ee8f15a44586515fd4ea8743f396752f874f9986d96660933303f2ab9` |
| Cache status | Unique query; response did not declare `cached: true` |
| Runtime dispatch | `runtime_mode=real`, `mock=false`, `fallback=false` |
| Selected engine | `finance-suite.stock_analysis` |

Required response contract:

| Field | Observed shape | Result |
|---|---|---|
| `result` | non-empty string, `4,382` characters | PASS |
| `sources` | array, `17` entries | PASS |
| `_qc` | object, `10` keys | PASS |
| `qa_result` | object, `4` keys | PASS |

### L3.3 Report Generation — PASS

The request resolved `贵州茅台` to `600519`, dispatched the stock engine,
returned a non-empty structured report, and attached sources, QC data, report
date metadata, data-availability metadata, and a final dispatch seal.

This proves one production request completed:

```text
Authenticated request
  -> stock resolution
  -> structured/search retrieval
  -> LLM analysis
  -> QC construction
  -> report response
```

It does not prove research correctness, provenance closure, SLA, scale, or
Research Runtime state-machine execution.

### L3 Pool Lifecycle Evidence — PASS WITH FINDING

The production pool instrumentation recorded the same worker around the
verification request:

```text
2026-07-31T15:22:19 pid=3294277 action=checkout checkedout=1 size=5 overflow=-4
2026-07-31T15:22:19 pid=3294277 action=checkin  checkedout=1 size=5 overflow=-4 held_s=0.291
2026-07-31T15:22:19 pid=3294277 action=checkout checkedout=1 size=5 overflow=-4
2026-07-31T15:23:16 pid=3294277 action=checkin  checkedout=1 size=5 overflow=-4 held_s=56.986
```

No QueuePool timeout, traceback, or HTTP 500 was recorded in the request
window. The `56.986 s` checkout is nevertheless a confirmed resource-lifecycle
finding; see `F-04`.

### Layer 3 Recommendation

```text
Layer 3 Application Runtime: PASS (findings attached)
Whole-chain promotion: NOT PERMITTED while Layer 2 production presentation remains FAIL
Production Capability: NOT CLAIMED
```

## 4. Layer 4 Results

### L4.1 Evidence Input — FAIL

Evidence-like inputs were present, but the response did not establish the
required provenance boundary.

| Check | Observation | Result |
|---|---|---|
| Source list | `17` source objects returned | OBSERVED |
| Source timestamps | All 17 response source objects had no `date`, `published_date`, or `published_at` value | FAIL |
| Report freshness | `source_date_unknown=true`, `latest_source_date=null`, `is_stale=true` | FAIL |
| Matched evidence | `_qc.fact_coverage.matched_search_hits=0` | FAIL |
| Cited evidence | `_qc.fact_coverage.cited_sources_count=0`; `_qc.sources=[]` | FAIL |
| Evidence status | Fundamental/news/research marked `partial`; realtime/macro/capital-flow/valuation marked `unavailable` | OBSERVED |

The report returned 17 links, but link presence is not equivalent to claim-level
evidence binding.

### L4.2 Research Runtime — FAIL

The production request executed a real application pipeline, but it did not
emit the Framework's required seven-step state trace:

```text
PLAN -> RETRIEVE -> BUILD_CTX -> ANALYZE -> QC -> SYNTHESIZE -> DONE
```

Read-only inspection of the deployed `app/routers/api.py` showed a direct route
implementation for retrieval, `generate_analysis`, QC assembly, usage commit,
and response return. No deployed `ResearchSession`, `run_research_workflow`, or
seven-step state-machine invocation was found in the production tree.

The response's `dispatch_trace` proves route and engine dispatch. It does not
prove the canonical Research Runtime state machine.

Supplemental local execution of the repository's separate
`research_runtime.run_research_workflow(symbol="600519.SH", mode="gateway")`
produced a 12-event trace and failed closed at Trust Gate:

```text
Provider: finance_data_gateway
Evidence retrieved: 1 gateway_quote
Trust Gate: allowed=0, blocked=1
Blocked reason: all_providers_failed
QC: passed=false, status=no_evidence
Final state: DONE
```

Local artifact fingerprints:

| Artifact | SHA-256 |
|---|---|
| `/tmp/research_runtime_latest.json` | `1725ba2b47c783ca06b0776bd431732e42d286ee144b5d7f0df87a3f871b2097` |
| `/tmp/research_runtime_events.jsonl` | `8e733e58dfb8e14a31ecf00958ea890ff29405eb1cf5781bd235f9d002c7da4c` |

That local fail-closed trace is evidence of a local skeleton, not proof that the
production `/api/analyze` path consumes it. The local state names also differ
from the seven-step Framework contract and contain no LLM report synthesis.

Required Layer 4 failure-lattice and cancellation/timeout exercises were not
run against production. Their status remains `VERIFY`; one successful
application request cannot substitute for them.

### L4.3 Output Boundary — FAIL

The production result contained a disclaimer and exposed data-availability
warnings, but it did not satisfy the Evidence Manifest / Capability Claim
binding requirements.

Observed response-wide key counts:

| Required governance key | Count |
|---|---:|
| `evidence_id` | 0 |
| `allowed_use` | 0 |
| `blocked_fields` | 0 |
| `trust_status` | 0 |
| `provider_tier` | 0 |
| `raw_response_hash` | 0 |
| `mapping_verified` | 0 |

At the same time:

- The report contained `60` numeric claim patterns.
- The report contained `36` textual source markers.
- `_qc.fact_coverage.cited_sources_count` was `0`.
- `section_data_usage` was empty.
- `_qc.hallucination_risk.level` was `medium` with
  `llm_inference_ratio=0.6`.
- `qa_result` still returned `passed=true`, `score=1.0`.

The disclaimer does not repair missing claim-to-evidence bindings. Therefore
the output boundary is not verified and contradicts the required governance
contract for a Layer 4 PASS.

### Layer 4 Recommendation

```text
Layer 4 Research Workflow: FAIL
Failure lattice per step: VERIFY
Cancellation / timeout release: VERIFY
Production Capability: NOT CLAIMED
```

## 5. Evidence

### E-01 — Service and health

- `finance-suite.service`: active.
- Four application workers observed under Uvicorn parent PID `3294269`.
- `/api/health`: HTTP 200, `{"status":"ok"}`.

### E-02 — Route registration

Production OpenAPI registered:

```text
GET  /api/health
POST /api/login
POST /api/analyze
```

### E-03 — Authenticated production response

- Request ID: `RUNTIME-V01-20260731-1524-CST`.
- HTTP 200 in `56.992 s`.
- Response body SHA-256:
  `3f68c90ee8f15a44586515fd4ea8743f396752f874f9986d96660933303f2ab9`.
- Full response retained temporarily at
  `/tmp/runtime_verification_response_v0_1.json` on both executor and production
  host with mode `0600`; the report records only redacted structural evidence.

### E-04 — Runtime dispatch

```text
selected_route=stock
resolved_name=贵州茅台
resolved_symbol=600519
engine_called=true
runtime_mode=real
mock=false
fallback=false
```

### E-05 — Pool lifecycle

The application worker checked a DB connection back in after `56.986 s`. No
QueuePool timeout appeared during this request window.

### E-06 — Evidence/provenance gap

The returned source list had 17 entries, but source dates, claim evidence IDs,
allowed-use bindings, section usage mappings, and cited-source counts were
absent or empty.

### E-07 — Local Research Runtime comparison

The local gateway-mode skeleton emitted 12 events, blocked its only gateway
evidence, produced no research evidence, and completed with QC false. It is not
wired into the observed production route.

## 6. Findings

### F-01 — Canonical Research Runtime trace is absent

**Finding:** The successful production request did not emit or execute the
required seven-step Research Runtime trace.  
**Root cause:** The deployed `/api/analyze` route implements retrieval, analysis,
QC, and response assembly directly; no production Research Runtime state-machine
call was found.  
**Evidence:** E-03, E-04, deployed `app/routers/api.py` read-only inspection, and
the absence of the seven transition records.  
**Impact:** Layer 3 can be evaluated, but Layer 4 cannot pass.

### F-02 — Claim-to-evidence binding is absent from the output

**Finding:** The report contains numeric and evaluative claims while the
response contains no `evidence_id`, `allowed_use`, `blocked_fields`, or populated
section-level evidence mapping.  
**Root cause:** The deployed trust-contract wrapper attaches availability and an
empty section-usage object, while QC is calculated independently of claim-level
manifest binding.  
**Evidence:** E-03 and E-06; `cited_sources_count=0`, `section_data_usage={}`,
`qa_result.passed=true`.  
**Impact:** Trust Gate and Capability Claim Framework compliance is not proven;
L4.3 fails.

### F-03 — Source freshness and relevance are unresolved

**Finding:** Returned sources have no usable timestamps and the runtime marks
the source date unknown.  
**Root cause:** Source objects did not carry dates usable by the report-as-of
calculation; the long unique query also yielded zero matched search hits in QC.  
**Evidence:** E-06; `source_date_unknown=true`, `matched_search_hits=0`.  
**Impact:** Currentness and claim-source relevance cannot be verified.

### F-04 — Request-scoped DB checkout spans the long analysis phase

**Finding:** A DB connection was held for `56.986 s`, essentially the full API
latency.  
**Root cause:** The deployed route receives a request-scoped DB session and
commits usage only after provider/search/LLM processing.  
**Evidence:** E-05 and deployed route order.  
**Impact:** This request succeeded, but the long hold preserves the previously
identified pool-saturation risk. This report does not repair it.

### F-05 — Local fail-closed behavior does not establish production wiring

**Finding:** The local Research Runtime correctly blocked failed gateway
evidence, but the production route did not consume that trace or its Trust Gate
result.  
**Root cause:** Local and production execution paths are separate.  
**Evidence:** E-04 and E-07.  
**Impact:** Local Runtime evidence cannot promote production Research Runtime.

## 7. Status Recommendation

```text
Layer 3 Application Runtime:       PASS (findings attached)
Layer 4 Research Workflow:         FAIL
Layer 4 Failure Lattice:           VERIFY
Layer 4 Cancellation / Timeout:    VERIFY
Layer 5 Production Runtime:        NOT IN SCOPE / NO STATUS PROMOTION
Production Presentation:           FAIL (pre-existing PE Band defect; unchanged)
Production Capability:             NOT CLAIMED
```

### Recommendation to CCB

The first execution feedback is sufficient to show that the Framework detects
a real separation between application execution and governed research-workflow
execution. CCB may consume this report as execution feedback, but should not
freeze a status table that still records the production stock frontend as PASS.
Any Framework freeze decision should preserve:

```text
Application request succeeded
  != Research Runtime state machine verified
  != claim-to-evidence boundary verified
  != Production Capability
```

No repair or new execution window is authorized by this report.

## Execution Closure

```text
Evidence collection: COMPLETE for the single authorized request
Production code change: NONE
Production static change: NONE
Service restart: NONE
Provider change: NONE
Trust Gate change: NONE
D29 change: NONE
Capability promotion: NONE
```
