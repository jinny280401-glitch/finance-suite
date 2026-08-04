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

**Acceptance condition:** For a synthetic or real incident, the system MUST be able to answer all four questions in Evidence Governance v1.0 §7.3 TC-RUNTIME-EVIDENCE-001:
1. Which layer produced the response?
2. Which component failed?
3. Was the Provider invoked? What did it return?
4. Does returned content match the declared contract?

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

**Problem domain:** Three distinct states are currently conflated:

```
model configured  ≠  model loaded  ≠  model executed
```

**Evidence requirement** (per C independent review):

| Layer | Evidence source | Absence consequence | Signal class |
|---|---|---|---|
| **Configured** | Versioned config snapshot + revision digest + effective-load timestamp + run identity | Response model or fallback log misread as operator intent | Observable, but needs immutable per-run attestation to bind to execution |
| **Loaded** | Scheduler process state or registry resolution event (requested ID, resolved ID, fallback chain, registry version, timestamp, run ID) | Configured model misread as available or selected | Fallback log is partial; per-run attestation needed |
| **Executed** | Gateway/provider response receipt tied to same run ID (serving-model identity, attempt outcome, integrity/usage receipt) | Load/selection misread as successful inference | Response-body model field is **observability, not API contract**; correlated execution attestation required |

**Acceptance condition:** For a single scheduler run, the system MUST produce a record that independently identifies configured, loaded, and executed model, bound to a common run/request identifier. A response-body `model` field alone does NOT satisfy this.

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

**Evidence requirement** (per C independent review):

| Transition | Identity required | Verifiability |
|---|---|---|
| **source → build artifact** | Source commit/tree hash + deterministic build recipe/version + artifact digest + build record linking input digest to output digest | **Verifiable** only with retained provenance record + reproducible/recomputable digest. Otherwise asserted only. |
| **build artifact → runtime served** | Deployed artifact/image digest + deployment revision/manifest + runtime process/startup identity + served-response version marker or digest tied to a request | **Verifiable** only by correlating deployment/runtime identity with identity exposed or derivable from the served response. Deployment record alone is an assertion about serving. |

**Acceptance condition:** For a served response, the system MUST be able to derive or expose the artifact identity, and that identity MUST be traceable to a source commit through a retained build record.

**Forbidden claims while R-03 is open:**
- "Production runs commit X"
- "The deployed version is Y"
- Treating a deployment log entry as proof of what is currently served

**Current verdict:** NOT PROVEN. Neither transition is established.

---

## 3. Cross-Track Evidence Dependency

Per C's independent review, these are **evidence dependencies**, not implementation dependencies:

```
R-01 (transaction correlation)
   ├── supplies the common run/request context that
   │   R-03 needs to demonstrate its "runtime served" side
   └── supplies the context R-02 needs to associate
       execution with a user-visible result

R-02 must bind configured/resolved/executed identities
     to that same run context before output can be
     attributed to a model

R-03 must bind source/build/runtime identities before
     a served response can be attributed to reviewed source
```

**Governance consequence:** R-01 is the enabling track. R-02 and R-03 acceptance conditions cannot be fully demonstrated without R-01's correlation identifier existing first. This is a dependency ordering, not a priority ranking.

---

## 4. Open Questions (UNKNOWN — carried forward)

Per C's independent review, the following cannot be determined from current material:

| ID | Question | Track |
|---|---|---|
| OQ-1 | Whether the Auction P0 observation has any retained raw nginx access/error record, backend record, headers, or response body | R-01 |
| OQ-2 | Whether nginx and backend currently share a correlatable request identifier and synchronized clock basis | R-01 |
| OQ-3 | Whether scheduler state exposes a verifiable loaded-model identity distinct from its fallback log | R-02 |
| OQ-4 | Whether the provider/gateway can emit a stable execution receipt that contractually identifies the serving model | R-02 |
| OQ-5 | Whether D13 has a deployed build pipeline, artifact registry, runtime version marker, or reachable served endpoint for parity verification | R-03 |

These join the 15 UNKNOWN items carried forward from Runtime Validation v0.1.

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
Status:                       DRAFT
Evidence gaps identified:     3 (R-01, R-02, R-03)
Open questions registered:    5 (OQ-1..OQ-5)
Cross-track dependency:       R-01 enables R-02 and R-03
Implementation:               NOT AUTHORIZED
Production change:            NONE
Frozen assets:                UNTOUCHED
```

---

*This plan defines what evidence is required to close three governance gaps. It does not close them, does not authorize work toward closing them, and does not claim any capability. Each track's forbidden-claims list remains in force until that track's acceptance condition is independently demonstrated.*
