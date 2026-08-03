# Vera Runtime Verification Framework v0.1

**Status:** FIRST PRESENTATION RUNTIME CASE CLOSED
**Freeze status:** NOT GRANTED — Reason: Layer 4 Evidence Governance Gap requires Framework revision (v0.2)
**Effective date:** 2026-07-31
**Window:** D29+ Runtime Verification Governance
**Role:** Runtime Verification Governance Owner (CCB)
**Authority:** CCB defines rules; C executes; CCA owns architecture; CCB does not run Runtime

### Execution Feedback v0.1 (received 2026-07-31)

| Layer | Status | Evidence |
|-------|--------|----------|
| L1 Static Asset | **PASS** | Asset verification |
| L2 Frontend Runtime | **PASS — PE Band production runtime case** | C smoke + post-fix export binding |
| L3 Application Runtime | **PASS (findings attached)** | C Runtime Execution Report v0.1, E-01..E-05; F-04: long-lived DB connection 56.986s, no QueuePool timeout |
| L4 Research Workflow | **FAIL — Evidence Governance Gap** | C report L4.1-L4.3, F-01..F-03; production path lacks 7-step trace and claim-to-evidence binding |
| L4 Failure Lattice | VERIFY | not executed |
| L4 Cancellation/Timeout | VERIFY | not executed |
| L5 Production Runtime | NOT IN SCOPE | separate authorization required |
| Production Capability | NOT CLAIMED | per Capability Maturity Ladder |

### Layer status rationale

- **L2 PASS — PE Band**: PE Band evidence proves Production Asset → Browser Load → Frontend Runtime → Rendered Artifact. It is a Layer 2 (Frontend Runtime) case, not Layer 3.
- **L3 PASS (findings attached)**: PASS because authenticated `/api/analyze` returned HTTP 200 with response contract (result / sources / _qc / qa_result). NOT clean PASS because F-04 documents DB connection held for 56.986s with no QueuePool timeout. The Finding is recorded, not promoted to FAIL and not ignored.
- **L4 FAIL**: not because report generation failed, not because API failed, not because Provider was absent. Layer 4 FAIL because production path lacks the 7-step state machine trace AND response lacks claim-level evidence governance (`evidence_id` / `allowed_use` / `blocked_fields`). This is the most valuable finding of the first execution cycle.

```text
Report Generated   ≠  Research Workflow Verified
Research Workflow Executed ≠ Evidence Governance Closed
Evidence Governance Closed ≠ Production Capability
```

### C's stop-and-document discipline

C executed, observed the gap, did **not** repair. Findings flow to CCB for Framework review. This validates the role split: C is Evidence Collector, not Framework Designer.

### Framework Coverage Verdict (CCB)

Framework covered all C-collected evidence classes. One §5.4 amendment needed: **response-level provenance field check** must be a Layer 3 evidence requirement (not only Layer 4). Additional Layer 4 contract needed: **Claim → Evidence → Allowed Use → Blocked Fields → Output Decision** binding requirement.

These gaps do **not** invalidate v0.1; they are the expected output of the first execution cycle.

---

## 0. Boundary Statement (binding for this document)

```text
DESIGN SPEC         = framework document exists at known path; rules are consistent
Runtime NOT EXECUTED = this document does not start, install, or probe any Runtime
Production NOT CLAIMED = no production / LIVE VERIFIED license exists as a result of this Framework
```

Inherited from `docs/architecture/VERA_ENTERPRISE_ARCHITECTURE_v1.0.md` §0:

```text
Architecture Defined  ≠  Runtime Implemented  ≠  Production Capability

DEFINED    = a specification exists at a known path and is internally consistent
RESERVED   = an interface boundary exists; downstream implementation PENDING
PENDING    = explicitly awaiting future window, no code on disk
NOT CLAIMED = no production / LIVE VERIFIED license exists for this scope
```

This Framework inherits, does not amend, the Capability Claim Maturity Ladder (L0–L6) in `Vera_Capability_Claim_Governance_Framework_v1.md`.

---

## 1. Purpose

### 1.1 Current Vera verified layers

Vera has verified the following:

- **Presentation Layer** — static asset delivery, frontend browser runtime, valuation chart rendering (post 2026-07-31 export fix).
- **Enterprise Architecture** — `docs/architecture/VERA_ENTERPRISE_ARCHITECTURE_v1.0.md` is a complete design artifact (6 layers, Institution Security Layer, Desensitization Gateway, External Intelligence Provider, Valuation Evidence Module); §9 Review Checklist 5/5 PASS; status DESIGN/Architecture SPEC, Runtime NOT IMPLEMENTED, Production NOT CLAIMED.

### 1.2 The gap

What is NOT yet verified:

- Whether the design actually runs.
- Whether Application Runtime (FastAPI / Router / Provider / LLM / Report) executes end-to-end.
- Whether Research Workflow state machine transitions complete in a real execution trace.
- Whether Production Runtime at `touziagent.com` matches the verified local artifacts.

### 1.3 What this Framework is

A governance framework that:

1. Defines the 5 verification layers (presentation → production).
2. Defines the status schema (`PASS` / `FAIL` / `VERIFY` / `NOT CLAIMED` / `EXCLUDED`).
3. Defines the evidence requirement per layer (what counts as proof).
4. Defines execution boundaries (CCB writes rules, C executes).
5. Maps current state to the schema.

### 1.4 What this Framework is NOT

- ❌ Not a verification execution (no Runtime is started).
- ❌ Not a Runtime implementation (no uvicorn, no FastAPI install, no probe).
- ❌ Not a Production deployment authorization (separate window required).
- ❌ Not a promotion to capability claim (L0 → L6 progression requires separate evidence).

---

## 2. Runtime Verification Layers

Five-layer verification, bottom-up. Each layer must PASS before the next may be attempted.

```
┌────────────────────────────────────────────────────────────────┐
│ Layer 5    Production Runtime Verification                     │  ← touziagent.com live system
├────────────────────────────────────────────────────────────────┤
│ Layer 4    Research Workflow Verification                       │  ← 7-step state machine end-to-end
├────────────────────────────────────────────────────────────────┤
│ Layer 3    Application Runtime Verification                     │  ← FastAPI / Router / Provider / LLM / Report
├────────────────────────────────────────────────────────────────┤
│ Layer 2    Frontend Runtime Verification                        │  ← Browser-side JS execution / Canvas / DOM
├────────────────────────────────────────────────────────────────┤
│ Layer 1    Static Asset Verification                           │  ← HTTP 200 / file presence / byte identity
└────────────────────────────────────────────────────────────────┘
```

### Layer 1 — Static Asset Verification

**What it proves**: The static bytes that the Runtime will load exist and are reachable.

**Evidence required**:
- HTTP 200 from target URL.
- File existence at declared path.
- Optional: SHA-256 fingerprint (production vs local).

**Does NOT prove**: Content correctness, version identity, runtime execution.

### Layer 2 — Frontend Runtime Verification

**What it proves**: JavaScript executes in a browser; DOM/Canvas render as designed.

**Evidence required**:
- Page loads without `Uncaught` page error.
- Key functions exposed on `window` are typed as `function`.
- Canvas/DOM measurements show non-trivial rendering (e.g., pixel count > threshold).

**Does NOT prove**: Backend connectivity, API contract correctness, real data path.

### Layer 3 — Application Runtime Verification

**What it proves**: FastAPI app starts, router dispatches, Provider fetches, LLM completes, Report generates end-to-end.

**Evidence required**:
- `POST /api/analyze` (or equivalent) returns a structured 200 response.
- Response contains `result`, `sources`, `_qc`, `qa_result` (per `app/routers/api.py` contract).
- Trace evidence: request → router → DB / Provider / LLM → response with intermediate logs.

**Does NOT prove**: Production fidelity, SLA, scale.

**Key gotcha identified 2026-07-31**: `python3 -m http.server` (or any static server) returns **501 Not Implemented** to POST because it only supports GET/HEAD. This is not an API defect — it is a server type mismatch. RCA per `KAN_PIAO_ANALYSIS_RCA.md` §2. Layer 3 verification requires a real FastAPI / uvicorn process. Static servers cannot be used as Layer 3 verification substrate.

### Layer 4 — Research Workflow Verification

**What it proves**: The 7-step state machine (`PLAN → RETRIEVE → BUILD_CTX → ANALYZE → QC → SYNTHESIZE → DONE`) transitions complete in a single execution trace.

**Evidence required**:
- Per-step log evidence (every transition entered and exited).
- Failure path tested: at least one forced degradation at each step proves the failure lattice.
- Cancellation / timeout tested for resource release (per `RESEARCH_RUNTIME_PROVIDER_CONSUMPTION_REVIEW.md`).

**Does NOT prove**: Production at scale, real Provider SLA.

### Layer 5 — Production Runtime Verification

**What it proves**: The system deployed at `touziagent.com` (or any declared production endpoint) executes Layer 3 + Layer 4 contracts in real traffic.

**Evidence required**:
- Production probes via authorized jump host (SSH via `admin@8.138.2.55 → ubuntu@119.28.156.125` per C's verified path).
- Active worker count, DB connection state, QueuePool checkouts against manifest.
- Authenticated path with non-cached input producing real `held_s` evidence (per KAN_PIAO instrumentation pattern).

**Does NOT prove**: LIVE VERIFIED license (separate Capability Maturity ladder).

### Layer promotion rule

```
Layer N may attempt   ⇔   Layer N-1 has PASS (or PASS-equivalent exemption by C)
Layer N PASS          ⇔   evidence per §3 collected AND reviewed by C
Layer N FAIL          ⇔   evidence per §3 collected AND negative outcome observed
```

Layer promotion is **not** automatic. CCB may not skip layers.

---

## 3. Status Schema

Five mutually exclusive statuses, plus one annotation.

| Status | Meaning | When to assign |
|--------|---------|----------------|
| **PASS** | Evidence collected; observed outcome matches requirement | C reports positive evidence reviewed by CCB |
| **FAIL** | Evidence collected; observed outcome contradicts requirement | C reports negative evidence reviewed by CCB |
| **VERIFY** | Not yet executed; no evidence either way | Default state for any layer not yet attempted |
| **NOT CLAIMED** | No assertion; no evidence; no obligation | Default for anything outside Vera's stated scope |
| **EXCLUDED** | Explicitly out of scope by owner decision | Owner ruling (e.g., `auction.html` excluded from competition Demo surface) |
| **(annotation)** | `RCA attached` / `pe-band fix` / `boundary cited` | Adds context without changing status |

### State transitions

```
initial   →  VERIFY
VERIFY    →  PASS    (with evidence)
VERIFY    →  FAIL    (with evidence)
VERIFY    →  EXCLUDED  (owner ruling)
PASS      →  FAIL    (only with new evidence AND RCA)
FAIL      →  PASS    (only with new evidence AND RCA)
any       →  NOT CLAIMED  (scope withdrawal)
```

A PASS must carry an evidence trail — without evidence, PASS is invalid and must be downgraded to VERIFY or FAIL.

### Inherited discipline

From `Vera_Capability_Claim_Governance_Framework_v1.md` §3:

```
A capability claim's maturity = MIN(component_maturities)
Any component at L0 (UNKNOWN) → whole claim must fail closed
```

This Framework does not introduce new maturity levels. PASS in this Framework does NOT equal L4+ on the Capability Maturity Ladder. That promotion requires `LIVE VERIFIED` license (§5 of the Capability Claim Framework) and is out of CCB scope.

---

## 4. Current Vera Status Mapping

Snapshot at 2026-07-31. Anchored to KAN_PIAO RCA evidence + D29 Demo smoke + CCA v1.0.

### Layer-by-layer mapping

| Layer | Component | Status | Evidence / source |
|-------|-----------|--------|-------------------|
| **L1** Static Asset | `/app/index.html` reachable | **PASS** | HTTP 200 from local dev (CC) + production (C) |
| **L1** Static Asset | `/app/stock.html` reachable | **PASS** | HTTP 200 from local dev + production |
| **L1** Static Asset | `/app/deep-research.html` reachable | **PASS** | HTTP 200 from production |
| **L1** Static Asset | `/app/macro.html` reachable | **PASS** | HTTP 200 from production |
| **L1** Static Asset | `/app/morning-brief-mini.html` reachable | **EXCLUDED** | 404 both sides; Morning Brief integrated into `/app/index.html` |
| **L1** Static Asset | Production ↔ local byte identity | **FAIL** (drift) | C fingerprint: all entries MISMATCH, no consistent direction |
| **L2** Frontend Runtime | `index.html` page error | **PASS** | Browser load clean (C smoke) |
| **L2** Frontend Runtime | `stock.html` page error | **PASS** | Browser load clean (C smoke) |
| **L2** Frontend Runtime | `window.renderPEBandChart` is function | **PASS** | post-2026-07-31 export fix |
| **L2** Frontend Runtime | PE Band Canvas render | **PASS (fixture)** | Canvas 720×140, 16,660 non-transparent pixels (C smoke) |
| **L3** Application Runtime | `POST /api/analyze` returns structured 200 | **VERIFY** | Local dev static server returns 501 (not API defect; server type mismatch per KAN_PIAO RCA); production not yet probed end-to-end |
| **L3** Application Runtime | `GET /api/intel/market-context` | **VERIFY** | C smoke: returns 404 on local dev (server type mismatch); production not yet probed |
| **L3** Application Runtime | DB connection ownership / pool recovery | **VERIFY** | KAN_PIAO instrumentation ACTIVE; `held_s` not yet observed on a non-cached authenticated `/api/analyze` |
| **L4** Research Workflow | 7-step state machine full transition trace | **VERIFY** | Not executed |
| **L4** Research Workflow | Failure lattice per F1–F4 | **VERIFY** | Not executed |
| **L4** Research Workflow | Cancellation / timeout resource release | **VERIFY** | Not executed |
| **L5** Production Runtime | Production `touziagent.com` runtime identity | **VERIFY** | C has probed some endpoints (HTTP 200); full production Runtime Verification not yet executed |
| **L5** Production Runtime | Production API contract (`POST /api/analyze`) | **VERIFY** | Not yet executed |
| **L5** Production Runtime | Production Provider fallback chain | **VERIFY** | Per D27-A1 status board: NOT EXECUTED |

### Surface decisions (from D29_PACKAGE_CHECKLIST)

| Entry | Layer status | Surface decision |
|-------|--------------|------------------|
| `/app/index.html` | L1 PASS, L2 PASS, L3 VERIFY, L4 VERIFY, L5 VERIFY | Demo surface candidate |
| `/app/stock.html` | L1 PASS, L2 PASS, L3 VERIFY, L4 VERIFY, L5 VERIFY | Demo surface candidate |
| `/app/deep-research.html` | L1 PASS, L2 VERIFY, L3 VERIFY, L4 VERIFY, L5 VERIFY | Demo surface candidate |
| `/app/macro.html` | L1 PASS, L2 VERIFY, L3 VERIFY, L4 VERIFY, L5 VERIFY | Demo surface candidate |
| `/app/auction.html` | L1 PASS, L2 VERIFY, L3 VERIFY, L4 VERIFY, L5 VERIFY | **EXCLUDED from Demo surface** — INC-01 OPEN |
| `/app/morning-brief-mini.html` | 404 | **EXCLUDED** — file does not exist |

### Critical non-promotions

These MUST NOT be implied from current status:

- ❌ `PE Band PASS (fixture)` → `PE Band PASS` — fixture is not Runtime evidence.
- ❌ `Static Asset PASS` → `Application Runtime PASS` — Layer 1 does not imply Layer 3.
- ❌ Any Layer VERIFY → any higher Layer PASS — promotion requires evidence per §2.
- ❌ `Local dev DEMO Runtime` → `Production Runtime` — boundary per D29_PACKAGE_CHECKLIST §"Demo Runtime Environment".
- ❌ Architecture Defined → Production Capability — per CCA v1.0 §0 Boundary.

---

## 5. Evidence Requirement Per Layer

### 5.1 Evidence chain principle

```text
Static exists  ≠  Static correct
Static correct  ≠  Frontend executes
Frontend executes  ≠  Backend reachable
Backend reachable  ≠  Workflow complete
Workflow complete  ≠  Production identical
Production identical  ≠  Production capable
```

A single weak link in this chain invalidates any PASS above it.

### 5.2 Layer 1 evidence chain

```
file exists     →  HTTP 200  →  (optional) SHA-256 declared
```

Required artifacts:
- HTTP probe log (method, status, size, time).
- Optional: SHA-256 fingerprint.

### 5.3 Layer 2 evidence chain

```
HTTP 200  →  HTML parses  →  JS executes without Uncaught  →
key functions typed as `function`  →  Canvas/DOM measurements recorded
```

Required artifacts:
- Browser console log (zero `pageerror`).
- `typeof window.<key_function>` check.
- For canvas renderers: width × height + non-transparent pixel count.

### 5.4 Layer 3 evidence chain

```
uvicorn process starts  →  router registers  →  POST /api/analyze reachable  →
request enters get_current_user  →  quota check  →  provider calls  →
LLM completes  →  response with result/sources/_qc/qa_result  →  HTTP 200
```

Required artifacts:
- `uvicorn app.main:app` start log (workers count).
- One authenticated request with non-cached input.
- Response body containing the 4-field contract.
- Pool checkout/checkin events with timestamps.

### 5.5 Layer 4 evidence chain

```
PLAN entered  →  RETRIEVE entered  →  ...  →  DONE entered
(at each transition: entered/exit timestamps, intermediate outputs)
```

Required artifacts:
- 7-step trace log.
- At least one forced degradation per step.
- Cancellation/timeout resource release evidence.

### 5.6 Layer 5 evidence chain

```
Authorized jump host probe  →  production endpoint HTTP 200  →
authenticated non-cached analyze  →  response per §5.4 contract  →
worker count  →  pool state  →  Provider fallback chain observed
```

Required artifacts:
- Jump host probe logs.
- Production runtime snapshot.
- Same 4-field response evidence as Layer 3 but from production.

---

## 6. Execution Boundary

### 6.1 CCB (Runtime Verification Governance Owner) — this role

CCB may:

- ✅ Author this Framework document.
- ✅ Define Layer definitions, Status Schema, Evidence Requirements.
- ✅ Maintain Layer-by-Layer status table (§4).
- ✅ Define Execution Checklist (§7).
- ✅ Maintain State Board / alignment records.
- ✅ Review evidence collected by C and update Layer status.

CCB may NOT:

- ❌ Install uvicorn / FastAPI / production dependencies locally.
- ❌ Pull `app/main.py` or any production backend file to local.
- ❌ Start `uvicorn app.main:app` in any form.
- ❌ Probe `touziagent.com` or any production endpoint.
- ❌ Modify CCA v1.0 architecture document.
- ❌ Modify production assets (static HTML, JS, CSS).
- ❌ Modify patches/ directory assets.
- ❌ Trigger Patch deployment / Restart / Production modification.
- ❌ Claim PASS / FAIL based on inference — only on evidence.

### 6.2 CCA (Enterprise Architecture Owner)

CCA may:

- ✅ Author and maintain `VERA_ENTERPRISE_ARCHITECTURE_v1.0.md`.
- ✅ Provide Architecture ↔ Runtime interface review (per CCA v1.0 §2 + §8).
- ✅ Review CCB's Framework for architectural alignment (CCA does not execute Runtime).

CCA does NOT (in this Framework's scope):

- ❌ Run Runtime verification.
- ❌ Probe Production.

### 6.3 C (Runtime Verification Executor)

C may:

- ✅ Execute Layer 1 / 2 / 3 / 4 / 5 verification under authorized window.
- ✅ Run uvicorn / production-equivalent / production probe per separate authorization.
- ✅ Collect evidence per §5.
- ✅ Report evidence to CCB for status update.

C does NOT (in this Framework's scope):

- ❌ Author this Framework.
- ❌ Promote any Layer status without evidence.
- ❌ Bypass Layer promotion rules.

### 6.4 Boundary inheritance

```
DESIGN SPEC (CCB)  ≠  RUNTIME EXECUTED (C)  ≠  PRODUCTION CAPABILITY (CCA promotion gate)

CCB writes rules; C runs them; CCA gates the outcome.
```

No role may act outside its lane. No role may invoke another role's lane without explicit owner authorization.

---

## 7. Execution Checklist (for C, under authorized window)

This checklist is a **template**. Each item requires C to collect and CCB to verify.

### 7.1 Layer 1 — Static Asset Verification

```
[ ] HTTP 200 for each Demo surface candidate
[ ] HTTP 404 expected for non-existent paths (e.g., morning-brief-mini.html)
[ ] SHA-256 fingerprint comparison (production vs local) — declare match status
[ ] File existence at declared paths
[ ] EXCLUDED entries' surface decision documented (auction.html excluded reason)
```

### 7.2 Layer 2 — Frontend Runtime Verification

```
[ ] Browser console clean (no Uncaught pageerror)
[ ] typeof window.<key_function> for each gated function
[ ] Canvas/DOM measurement for each chart renderer
[ ] No new presentation defect introduced post-fix
[ ] PE Band specifically: function exists, canvas renders non-trivial pixels
```

### 7.3 Layer 3 — Application Runtime Verification

```
[ ] uvicorn process starts (production backend or production-equivalent)
[ ] Worker count matches expected (e.g., 4 for production)
[ ] POST /api/analyze reachable
[ ] One authenticated non-cached request
[ ] Response body contains: result / sources / _qc / qa_result
[ ] Pool checkout/checkin events recorded (per KAN_PIAO instrumentation)
[ ] No QueuePool timeout during the verification request
[ ] Layer 1 and Layer 2 remain PASS through this exercise
```

### 7.4 Layer 4 — Research Workflow Verification

```
[ ] 7-step state machine full transition (PLAN → DONE) traced
[ ] Per-step intermediate output captured
[ ] At least one forced degradation per step
[ ] Cancellation / timeout resource release verified
[ ] Failure lattice F1–F4 covered (per RESEARCH_RUNTIME_PROVIDER_CONSUMPTION_REVIEW.md)
```

### 7.5 Layer 5 — Production Runtime Verification

```
[ ] Authorized jump host probe succeeds
[ ] Production endpoint HTTP 200
[ ] Production authenticated non-cached /api/analyze returns per §5.4 contract
[ ] Worker count snapshot
[ ] Pool state snapshot
[ ] Provider fallback chain observed (or NOT_CLAIMED if no fallback exists)
[ ] No regression introduced by any Layer 3/4 exercise
```

---

## 8. Sign-off

| Role | Statement |
|------|-----------|
| Framework author (CCB) | This document is DESIGN SPEC COMPLETE. Review APPROVED. Runtime NOT EXECUTED. Production NOT CLAIMED. CCB does not run Runtime. No new Capability Maturity promotion implied. |
| Architecture alignment (CCA) | Inherited from `VERA_ENTERPRISE_ARCHITECTURE_v1.0.md` §0, §2 (Layer 4 Research Runtime), §8 (Capability Boundary Table Item 3). No amendment. |
| Execution handoff (C) | This Framework is the rulebook for C's Runtime Verification execution. C executes under separate authorized window. |
| Window authority | FROZEN status PENDING first Runtime Execution Feedback (per owner directive 2026-07-31). FROZEN does not equal CLOSED. |

---

## 9. Review Checklist (binding before FROZEN)

- [ ] **Each Layer has explicit status**: L1 / L2 / L3 / L4 / L5 in §4 are populated.
- [ ] **Status schema is consistent**: PASS / FAIL / VERIFY / NOT CLAIMED / EXCLUDED used per §3 rules; no ad-hoc status words.
- [ ] **Evidence requirements are tiered**: §5 Layer-by-Layer evidence chains defined.
- [ ] **Execution boundary is role-locked**: §6 CCB / CCA / C lanes explicit; no role may act outside.
- [ ] **CCA alignment preserved**: §0 inherits v1.0 Boundary; §2 references Layer 4; §8 reference Item 3 unchanged.

When all five boxes pass, this v0.1 may be marked **FROZEN**, not **CLOSED**.

---

## 10. Final Statement

> **Vera 的可信不只是设计可信。Presentation 验证不等于 Runtime 验证，Local 验证不等于 Production 验证。本 Framework 定义从 Presentation 到 Production 的五层验证规则，不执行验证本身。**

This statement is the v0.1 anchor. Any future document that contradicts it (e.g., by treating Layer 3 VERIFY as PASS, or by claiming production capability absent Layer 5 evidence) is invalid relative to v0.1.

---

## Appendix A — Inherited Governance Assets

This Framework inherits (does not amend):

- `docs/architecture/VERA_ENTERPRISE_ARCHITECTURE_v1.0.md` — Architecture SSOT
- `docs/governance/Vera_Capability_Claim_Governance_Framework_v1.md` — L0–L6 maturity ladder + LIVE VERIFIED license
- `docs/governance/INSTITUTIONAL_PROVIDER_ARCHITECTURE_v0.1.md` — Provider state machine
- `docs/governance/RESEARCH_RUNTIME_PROVIDER_CONSUMPTION_REVIEW.md` — Runtime consumption discipline
- `docs/evidence/Vera_Evidence_Manifest_Protocol_v0.1.md` — three-question protocol
- `docs/governance/KAN_PIAO_ANALYSIS_RCA.md` — pool lifecycle instrumentation pattern
- `docs/governance/D27_INSTITUTIONAL_EVIDENCE_PROVIDER_LAYER_STATUS.md` — D27-A1 frozen status

## Appendix B — Glossary

| Term | Definition |
|------|------------|
| Layer N | One of the five verification layers per §2 |
| Layer promotion | Advancing from VERIFY to PASS/FAIL based on collected evidence |
| `verify` (verb) | The action C takes to attempt Layer promotion |
| `VERIFY` (status) | Default state for not-yet-attempted layers |
| Evidence chain | The ordered artifact sequence required for Layer PASS |
| Boundary citation | A reference to an existing governance asset that defines a rule CCB inherits |