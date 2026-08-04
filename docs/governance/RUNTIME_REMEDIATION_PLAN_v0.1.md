# Runtime Governance Remediation Plan v0.1

**Status:** DRAFT — Planning Only
**Window:** Runtime Governance Remediation Planning v0.1 (OPEN)
**Mode:** Planning. Implementation NOT AUTHORIZED. Production change NONE.
**Baseline:** `finance-suite/main` — Runtime Validation v0.1 Final Report (`8fe031c`, C Adversarial Review PASS)
**Independent Evidence Review:** [R01_R02_R03_EVIDENCE_REQUIREMENTS.md](../../../Documents/New%20project%206/finance-suite/docs/reviews/R01_R02_R03_EVIDENCE_REQUIREMENTS.md) (Repo B)
**Governing principle:** UNKNOWN is a legal state, not a failure state.

---

## 0. Baseline Reconciliation Note

C's independent review noted that commit `8fe031c` was not present in its workspace history and therefore did not treat Runtime Validation v0.1 conclusions as independently verified.

**Reconciliation:** `8fe031c` exists in `finance-suite` (Repo A). C reviewed from Repo B (`New project 6`), where the commit is absent by design — Repo A holds runtime/governance, Repo B holds research/review. C's caution was correct: it did not import an unverified baseline. This note records the repository boundary, not a defect.

**Consequence for this plan:** R-01/R-02/R-03 evidence requirements stand on their own analytical merit. They do not depend on Runtime Validation v0.1 conclusions being accepted.

---

## 1. Purpose and Scope

This plan converts three identified governance gaps into **remediation scope definitions**. It does not authorize implementation, does not propose code changes, and does not claim any capability.

### What this plan produces

| Output | Definition |
|---|---|
| Problem domain | What governance gap exists (not what code is broken) |
| Evidence requirement | What evidence must exist before the gap can be closed |
| Acceptance condition | What must be demonstrable, and by whom |
| Forbidden claims | What MUST NOT be stated while the gap is open |

### What this plan does NOT produce

- Implementation proposals
- Code changes
- Deployment authorization
- Priority ranking beyond governance dependency
- Capability claims

---

## 2. Remediation Tracks

Tracks are defined by **governance gap**, not by code module. A single code path may appear in multiple tracks; a single track may span multiple code paths.

### R-01 — Runtime Evidence

**Origin:** Auction P0 (`Unexpected token '<'`)

**Governance gap:**

```
Incident occurred
      ↓
Evidence retention insufficient
      ↓
Root cause attribution impossible
```

**Problem domain:** The system cannot prove which layer produced a failing response. Per Evidence Governance v1.0 §7.1, an RCA missing one or more required fields MUST be classified `Evidence Confidence: LOW` / `Root Cause: UNKNOWN (evidence insufficient)`.

**Evidence requirement** (per C independent review):

| Field | Proves | Collection class |
|---|---|---|
| `request_id` | A single request traceable across proxy → backend → response | Pre-incident propagation + post-incident collection |
| `timestamp` (UTC, precision + clock source) | Ordering and latency comparability across layers | Pre-incident + post-incident |
| `status_code` at nginx AND backend | Whether failure was edge-generated, upstream-returned, or proxy-transformed | Pre-incident + post-incident |
| `content_type` at upstream AND final response | Whether consumer received expected representation; bounds interpretation of parse errors | Pre-incident + post-incident |
| nginx ↔ backend correlation | The nginx response and a specific backend attempt are the same transaction | Pre-incident (shared identifier + retained logs) |

#### R-01a — Incident Scene Preservation (per F-01)

The five fields above establish *answerability* but do not establish that the answer describes the **original occurrence**. A request-scoped, time-bounded, integrity-verifiable evidence package is required:

| Requirement | Definition |
|---|---|
| Raw proxy records | nginx access + error log entries for the incident window, retained before rotation |
| Backend / application records | Application log events for the same window, including exception traces |
| Provider attempt records | Whether a Provider was invoked, its request, and its returned status |
| Response headers | Final response headers AND upstream response headers, both retained |
| Response body capture | Bounded capture (size-limited, redacted) of the actual response body |
| Deployment / config / process identity | Which code version, config revision, and process served the request |
| Retention window | Explicit minimum retention period, longer than log rotation interval |
| Redaction rule | What MUST be redacted before retention (credentials, PII) |
| Integrity binding | Hash or signature over the assembled package, so later tampering is detectable |
| Preservation timing | The package MUST be assembled **before** any restart, redeploy, or log rotation |

**Governance rule:** Evidence collected *after* a restart is post-fix verification evidence, not incident evidence. The two MUST NOT be conflated (Evidence Governance v1.0 §7.2).

#### R-01b — Three-State Separation (per F-02)

The acceptance condition MUST require three separately-recorded states. Evidence of the first two does NOT certify the third:

```
State 1: Occurrence
  What: the incident happened, with this identity, at this time
  Evidence: the preserved package (R-01a)

State 2: Explanation
  What: this event chain is consistent with the observed occurrence
  Evidence: correlated trace across layers

State 3: Root Cause Proven
  What: this cause produced the occurrence, and alternatives are excluded
  Evidence: State 2 + falsifiable hypothesis + counter-cases that
            distinguish it from every competing explanation
```

**Required counter-cases:** the proposed evidence MUST be shown to distinguish between at least these five failure modes, each producing a similar client-visible symptom:

| Counter-case | Distinguishing evidence needed |
|---|---|
| Edge-generated HTML (nginx error page) | nginx status ≠ upstream status; no backend record |
| Upstream-generated HTML (backend error page) | backend record exists with HTML content_type |
| Proxy transformation (nginx rewrote upstream response) | upstream headers ≠ final headers |
| Provider error surfaced as HTML | provider attempt record with non-JSON response |
| Client-side parsing defect | server records show valid JSON; failure is client-only |

**Acceptance condition (revised):** For a synthetic or real incident, the system MUST:
1. Produce a preserved incident package per R-01a
2. Record occurrence, explanation, and root-cause-proof as three distinct states per R-01b
3. Demonstrate, via controlled fault injection, that the evidence distinguishes all five counter-cases
4. Answer all four questions in Evidence Governance v1.0 §7.3 TC-RUNTIME-EVIDENCE-001

**Explicit rule:** Satisfying (1) and (2) alone permits an explanation. It does NOT permit a `Root Cause: CONFIRMED` classification. Only (3) plus excluded alternatives permits that.

**Forbidden claims while R-01 is open:**
- "Auction P0 is fixed"
- "The root cause was timeout"
- "The root cause was the Provider"
- Any `Root Cause: CONFIRMED` classification for the original incident

**Current verdict:** NOT PROVEN. The listed fields are closure requirements, not evidence that they exist.

---

### R-02 — Model Identity Evidence

**Origin:** Scheduler model resolution

**Governance gap:**

```
Model capability claim
      ↓
No model identity attestation
      ↓
Claim unverifiable
```

**Problem domain:** Four distinct states are currently conflated (per F-03, the gateway-accepted state was missing from the v0.1 draft):

```
model configured  ≠  model resolved  ≠  gateway accepted  ≠  model executed
```

**Evidence requirement** (per C independent review + F-03 correction):

| Layer | Evidence source | Absence consequence | Signal class |
|---|---|---|---|
| **1. Configured** | Versioned config snapshot + revision digest + effective-load timestamp + run identity | Response model or fallback log misread as operator intent | Observable, but needs immutable per-run attestation to bind to execution |
| **2. Resolved** | Scheduler process state or registry resolution event (requested ID, resolved ID, fallback chain, registry version, timestamp, run ID) | Configured model misread as available or selected | Fallback log is partial; per-run attestation needed |
| **3. Gateway Accepted** *(NEW per F-03)* | Gateway admission / normalization / routing record: requested model, gateway-accepted model, gateway request/attempt ID, decision outcome (accepted / rejected / alias-rewritten / route-substituted), mapping to provider attempt | Gateway rejection, alias rewrite, fallback, or route substitution goes unobserved. Chain becomes non-contiguous: resolved → executed may skip an identity change. | **No current evidence source.** Requires new gateway attestation. |
| **4. Executed** | Provider response receipt tied to same run + gateway attempt ID (serving-model identity, attempt outcome, integrity/usage receipt) | Load/selection misread as successful inference | Response-body model field is **observability, not API contract**; correlated execution attestation required |

**Why the fourth layer is required (F-03):** A provider receipt can show a downstream result while gateway-level identity substitution remains invisible. The v0.1 draft's three-layer chain could bind `configured → resolved → executed` while the gateway accepted a *different* identity, or no model at all. Distinguish three gateway outcomes explicitly:

| Gateway outcome | Meaning |
|---|---|
| **Accepted** | Gateway admitted the request with a specific model identity |
| **Invoked** | Gateway forwarded to a provider (accepted ≠ invoked; admission may be followed by a routing failure) |
| **Successfully executed** | Provider returned a completed inference (invoked ≠ executed; a 503 is invoked-but-not-executed) |

**Acceptance condition (revised):** For a single scheduler run, the system MUST produce a record that independently identifies all **four** model-identity states, bound to a common run identifier AND a gateway attempt identifier. A response-body `model` field alone does NOT satisfy any layer.

**Forbidden claims while R-02 is open:**
- "The system uses model X" (without specifying which of the three layers)
- Any user-visible capability claim tied to a specific model identity
- Treating a response `model` field as proof of execution identity

**Current verdict:** PARTIALLY PROVEN. Historical resolution-failure narrative is supported; the three-way distinction for a *successful* run is not.

---

### R-03 — Artifact Parity

**Origin:** D13 render script drift

**Governance gap:**

```
source  ≠  build artifact  ≠  runtime served
```

**Problem domain:** A local build, a stale deployment, or an independently copied artifact can be mistaken for reviewed source in production. A `.pyc` establishes prior compiled-artifact presence, not source identity.

**Evidence requirement** (per C independent review + F-04 correction):

The v0.1 draft defined two transitions. Per F-04, **runtime-loaded artifact identity is a third independent state** — a deployment manifest or response marker may identify an *intended* or *externally reported* version, not the artifact actually loaded in memory by the serving process.

```
reviewed source  →  compiled artifact  →  runtime-loaded artifact  →  served response
```

| Transition | Identity required | Verifiability |
|---|---|---|
| **1. source → compiled artifact** | Source commit/tree hash + deterministic build recipe/version + artifact digest + build record linking input digest to output digest | **Verifiable** only with retained provenance record + reproducible/recomputable digest. Otherwise asserted only. |
| **2. compiled artifact → runtime-loaded artifact** *(NEW per F-04)* | Running process identity + actual loaded module/package/image digest (read from the live process, not from the deployment record) + load timestamp + request-serving worker identity | **Verifiable** only by observing the running process. A deployment manifest is an assertion about what *should* be loaded. |
| **3. runtime-loaded artifact → served response** | Request-tied served version marker or digest, correlated to the worker that produced the response | **Verifiable** only if the marker is derived from the loaded artifact, not from a static config value. |

**Why the third state is required (F-04):** Stale workers, hot-reloaded modules, copied packages, sidecars, or a version marker detached from application code can preserve transitions 1 and 3 while runtime executes different code. Concretely:

| Failure mode | Transitions 1+3 still appear valid | What actually happens |
|---|---|---|
| Stale long-lived worker | Deployment record names new build; response marker reads from config | Worker still has old module in memory |
| Hot-reloaded module | Both endpoints report expected version | Only some modules reloaded; mixed state |
| Manually copied package | Digest matches the copy source | Copy diverged from reviewed commit |
| Marker detached from code | Marker is a constant string | Marker cannot detect drift by construction |

**Acceptance condition (revised):** For a served response, the system MUST produce a request-correlated proof chain across **all three** transitions. Each link MUST be independently observed:
1. Build record proves source → compiled artifact
2. Live process inspection proves compiled artifact → runtime-loaded artifact
3. Request correlation proves runtime-loaded artifact → served response

A deployment record plus a response marker satisfies only links 1 and 3. That combination does NOT establish parity.

**Forbidden claims while R-03 is open:**
- "Production runs commit X"
- "The deployed version is Y"
- Treating a deployment log entry as proof of what is currently served

**Current verdict:** NOT PROVEN. Neither transition is established.

---

## 3. Cross-Track Evidence Dependency

Per C's independent review, these are **evidence dependencies**, not implementation dependencies.

### 3.1 Correlation Contract (per F-05)

The v0.1 draft asserted that R-01 "supplies the common run/request context" without defining what that context is. Per F-05, the three tracks operate on **different identity scopes that need not be one-to-one**. The correlation contract MUST be specified before the dependency claim is testable.

**Identity scopes required:**

| Scope | Definition | Owning track | Cardinality |
|---|---|---|---|
| `request_id` | One inbound HTTP request at the edge | R-01 | 1 per client request |
| `scheduler_run_id` | One scheduled automation invocation | R-02 | 1 per cron/trigger firing |
| `gateway_attempt_id` | One admission decision at the gateway | R-02 | N per scheduler_run_id (retries, fallbacks) |
| `provider_attempt_id` | One provider invocation | R-02 | N per gateway_attempt_id |
| `worker_id` | One process instance serving requests | R-03 | 1 per process; N requests per worker |
| `artifact_digest` | One loaded code artifact identity | R-03 | 1 per worker at a point in time |

**Required join rules:**

```
R-01 ←→ R-03
  join: request_id → worker_id → artifact_digest
  rule: every request record MUST name the worker that served it;
        every worker record MUST name its loaded artifact digest

R-01 ←→ R-02
  join: request_id → scheduler_run_id (when request originated from automation)
  caveat: NOT all requests have a scheduler_run_id (user-initiated requests
          have none); NOT all scheduler runs produce an inbound request
          (some write directly to storage)

R-02 internal
  join: scheduler_run_id → gateway_attempt_id → provider_attempt_id
  rule: fan-out is expected (retries, fallbacks); every attempt MUST be
        recorded, not only the successful one
```

**Unresolved contract questions** (these are new UNKNOWN items, registered in §4):

| Question | Why it blocks the dependency claim |
|---|---|
| Propagation boundary | Does `request_id` survive across the async boundary into scheduler work? If not, R-01↔R-02 join is impossible for automation-triggered work. |
| Clock relationship | Are nginx, backend, and scheduler clocks synchronized, and to what precision? Without this, ordering across layers is not derivable. |
| Fan-in behavior | When multiple scheduler runs write to one served artifact, which run is attributable to a served response? |
| Retry identity | Does a retry reuse `gateway_attempt_id` or mint a new one? Both are defensible; the choice determines whether "the attempt failed" is countable. |

### 3.2 Dependency Claim (scoped)

```
R-01 supplies request_id and the correlation infrastructure.

R-03 acceptance REQUIRES the R-01 join (request → worker → artifact),
     because "served response" is only attributable if the request
     record names its worker.

R-02 acceptance PARTIALLY requires R-01: the four-layer model chain
     is internally correlatable via scheduler_run_id alone, but
     attributing a model to a *user-visible result* requires the
     R-01 join, which may not exist for all automation paths.
```

**Governance consequence (revised):** R-01 is the enabling track **for R-03 fully, and for R-02 partially**. The v0.1 draft's unqualified claim that R-01 enables both tracks is narrowed here per F-05. This is a dependency ordering, not a priority ranking.

---

## 4. UNKNOWN Register (per F-06)

The v0.1 draft asserted a total of 20 without providing the prior 15-item register, making the count non-reconcilable. Per F-06, the full register is reproduced here with source references.

### 4.1 Carried forward from Runtime Validation v0.1 (15 items)

Source: [RUNTIME_GOVERNANCE_VALIDATION_v0.1_FINAL_REPORT.md](../reviews/RUNTIME_GOVERNANCE_VALIDATION_v0.1_FINAL_REPORT.md)

| ID | Track | Question | Status in that report |
|---|---|---|---|
| UA-F1 | R-01 | HTML response source at incident time | Not captured |
| UA-F2 | R-01 | Original request ID | Not preserved |
| UA-F3 | R-01 | Response headers/body during failure | Not retained |
| UA-F4 | R-01 | Exhausted connections trigger | Not evidenced |
| UA-F5 | R-01 | `scripts/`↔`app/` parity as root cause | Not confirmed |
| UA-F6 | R-01 | Post-2026-07-24 production retest | Not performed |
| UA-F7 | R-01 | Production `market_context` module resolution | Module not in baseline |
| UA-F8 | R-03 | Backend deployment mechanism | `deploy.sh` incomplete for backend |
| UA-F9 | R-01 | Which path served production incident traffic | Cannot determine |
| UB-F1 | R-02 | Actual LLM model identity per request | No code, no log, no metadata |
| UB-F2 | R-02 | Model selection mechanism | No scheduler, router, or resolver component |
| UB-F3 | R-02 | Model identity determinism | Cannot verify from baseline |
| UB-F4 | R-02 | Verifiability of "Claude"/"GPT" capability claims | No runtime model attestation |
| UB-F5 | R-02 | LLM model fallback behavior | No model-level fallback chain |
| UB-F6 | R-02 | Research demo API model path | Rule fallback mentioned; no model identity capture |

### 4.2 New from Independent Evidence Review (5 items)

Source: [R01_R02_R03_EVIDENCE_REQUIREMENTS.md](../../../Documents/New%20project%206/finance-suite/docs/reviews/R01_R02_R03_EVIDENCE_REQUIREMENTS.md) (Repo B)

| ID | Track | Question |
|---|---|---|
| OQ-1 | R-01 | Whether the Auction P0 observation has any retained raw nginx access/error record, backend record, headers, or response body |
| OQ-2 | R-01 | Whether nginx and backend currently share a correlatable request identifier and synchronized clock basis |
| OQ-3 | R-02 | Whether scheduler state exposes a verifiable loaded-model identity distinct from its fallback log |
| OQ-4 | R-02 | Whether the provider/gateway can emit a stable execution receipt that contractually identifies the serving model |
| OQ-5 | R-03 | Whether D13 has a deployed build pipeline, artifact registry, runtime version marker, or reachable served endpoint for parity verification |

### 4.3 New from Adversarial Review of this Plan (4 items)

Source: [RUNTIME_REMEDIATION_ADVERSARIAL_REVIEW_v0.1.md](../../../Documents/New%20project%206/finance-suite/docs/reviews/RUNTIME_REMEDIATION_ADVERSARIAL_REVIEW_v0.1.md) (Repo B), F-05 correlation contract

| ID | Track | Question |
|---|---|---|
| OQ-6 | Cross | Propagation boundary — does `request_id` survive the async boundary into scheduler work? |
| OQ-7 | Cross | Clock relationship — are nginx, backend, and scheduler clocks synchronized, and to what precision? |
| OQ-8 | Cross | Fan-in behavior — when multiple scheduler runs write to one served artifact, which run is attributable to a served response? |
| OQ-9 | R-02 | Retry identity — does a retry reuse `gateway_attempt_id` or mint a new one? |

### 4.4 Reconciliation

```
Carried forward (v0.1 Final Report):        15
New from Evidence Requirements review:       5
New from Adversarial Review (F-05):          4
─────────────────────────────────────────────
Total registered UNKNOWN:                   24
```

**Change from v0.1 draft:** the draft stated 20. The adversarial review of this plan surfaced 4 additional correlation-contract questions (OQ-6..OQ-9). The count increases to 24.

**Governance note:** an increasing UNKNOWN count during a planning window is expected and correct. It indicates that adversarial review is finding real gaps, not that the system is degrading. No item has been cleared, merged, or reclassified.

---

## 5. Window Boundary

### Honored in this window

- [x] No production code modified
- [x] No `render.py` change
- [x] No scheduler change
- [x] No auction fix deployed
- [x] Evidence Governance v1.0 untouched
- [x] Trust Gate v1 untouched
- [x] Multi-Agent Trust Gate v1 untouched
- [x] No capability claim expanded
- [x] No UNKNOWN cleared as a goal

### NOT authorized by this plan

- Implementation of any evidence-capture mechanism
- Deployment of any fix
- Modification of any frozen governance asset
- Any statement that a track is "closed" or "resolved"

---

## 6. Window Exit Status

```
Runtime Governance Remediation Planning v0.1
Status:                       DRAFT (under revision per C adversarial review)
Evidence gaps identified:     3 (R-01, R-02, R-03)
  R-01:  incident preservation + 3-state separation + 5 counter-cases
  R-02:  4-layer model chain (configured/resolved/gateway-accepted/executed)
  R-03:  3-link artifact chain (source/compiled/runtime-loaded/served)
UNKNOWN registered:           24 (15 carried + 5 evidence-review + 4 adversarial-review)
Cross-track dependency:       R-01 enables R-03 fully, R-02 partially
                             (narrowed per F-05; R-02 internal chain is
                             self-sufficient, but user-visible attribution
                             requires R-01 join)
Implementation:               NOT AUTHORIZED
Production change:            NONE
Frozen assets:                UNTOUCHED
```

---

*This plan defines what evidence is required to close three governance gaps. It does not close them, does not authorize work toward closing them, and does not claim any capability. Each track's forbidden-claims list remains in force until that track's acceptance condition is independently demonstrated.*

*This Plan is under revision. All six findings (F-01..F-06) from C's adversarial review have been addressed; the Plan has not yet been re-submitted for C's re-review.*
