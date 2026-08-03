# Vera Runtime Verification Framework v0.2

**Status:** DESIGN SPEC COMPLETE (pending validation by second execution cycle)
**Supersedes:** v0.1 (status now `EXECUTION FEEDBACK RECEIVED / FREEZE BLOCKED`)
**Freeze:** PENDING — not FROZEN. Second C execution under v0.2 rules required.
**Effective date:** 2026-07-31
**Window:** D29+ Runtime Verification Governance — v0.2 Revision
**Role:** Runtime Verification Governance Owner (CCB)
**Authority:** CCB defines rules; C executes; CCA owns architecture; CCB does not run Runtime

### Closure loop (binding)

```text
v0.2 DESIGN SPEC COMPLETE
    ↓
C second Runtime Execution (under v0.2 rules)
    ↓
Execution Evidence
    ↓
CCB Review
    ↓
    ├── Framework covers reality → FROZEN
    └── Framework misses evidence class → v0.x Revision → re-execute
```

FROZEN is **not** automatic on v0.2 publication. FROZEN requires PASS-or-equivalent evidence on the amended Layer 3 + Layer 4 rules.

---

## 0. Revision Scope (binding)

v0.2 is a **minimal amendment** triggered by C's Runtime Execution Report v0.1 (2026-07-31), with a secondary trigger from C's Configuration Gate Audit v0.1 (same day).

| Element | v0.1 | v0.2 amendment |
|---------|------|----------------|
| §5.4 Layer 3 evidence chain | ends at HTTP 200 | + **response provenance field check** (mandatory) |
| §5.5 Layer 4 evidence chain | 7-step state machine trace | + **Claim → Evidence → Allowed Use → Blocked Fields → Output Decision** binding requirement |
| §7.3 Layer 3 Checklist | 8 items | + 1 item (provenance field check) |
| §7.4 Layer 4 Checklist | 3 items | + 1 item (claim-level evidence binding check) |
| §7.6 Runtime Verification Entry Rule | implicit | **explicit**: Target Runtime / Credential Source / Provider Identity / Data Source / Runtime Consumer must be declared per execution (NEW, triggered by Configuration Gate Audit) |
| §3 Status Schema | unchanged | unchanged |
| §6 Execution Boundary | unchanged | unchanged (CCB still does not execute) |

**No new layers, no new statuses, no new roles.** This is a documented amendment to evidence requirements, not an expansion of scope.

---

## 1. Boundary Statement (binding for this document)

Inherited from v0.1 §0, unchanged.

```text
DESIGN SPEC         = framework document exists at known path; rules are consistent
Runtime NOT EXECUTED = this document does not start, install, or probe any Runtime
Production NOT CLAIMED = no production / LIVE VERIFIED license exists as a result of this Framework

Architecture Defined  ≠  Runtime Implemented  ≠  Production Capability
```

---

## 2. Runtime Verification Layers (unchanged from v0.1)

```
Layer 1  Static Asset Verification
Layer 2  Frontend Runtime Verification
Layer 3  Application Runtime Verification          ← §5.4 amended
Layer 4  Research Workflow Verification            ← §5.5 amended
Layer 5  Production Runtime Verification           (separate authorization)
```

---

## 3. Status Schema (unchanged)

Five statuses: `PASS` / `FAIL` / `VERIFY` / `NOT CLAIMED` / `EXCLUDED`.

---

## 4. Current Status Mapping (carried from v0.1, with one update)

| Layer | Status | Source |
|-------|--------|--------|
| L1 Static Asset | mostly PASS; byte identity FAIL (drift) | C + D29 evidence |
| L2 Frontend Runtime | PASS for post-fix; pre-fix FAIL (PE Band export) | C smoke report |
| L3 Application Runtime | **PASS (findings attached)** — F-04: 56.986s DB hold, no QueuePool timeout | C Runtime Execution Report v0.1 |
| L3 Response Provenance Field Check | **VERIFY** — not required by v0.1; required by v0.2 §5.4 | NEW in v0.2 |
| L4 Research Workflow | **FAIL — Evidence Governance Gap** — F-01/02/03 | C Runtime Execution Report v0.1 L4.1–L4.3 |
| L4 Claim→Evidence Binding | **VERIFY** — not required by v0.1; required by v0.2 §5.5 | NEW in v0.2 |
| L5 Production Runtime | NOT IN SCOPE | separate authorization |

---

## 5. Evidence Requirement Per Layer

### 5.1 Layer 1 (unchanged)
### 5.2 Layer 2 (unchanged)
### 5.3 unchanged
### 5.4 Layer 3 — Application Runtime (AMENDED)

```
uvicorn process starts  →  router registers  →  POST /api/analyze reachable  →
request enters get_current_user  →  quota check  →  provider calls  →
LLM completes  →  response with result/sources/_qc/qa_result  →  HTTP 200
```

**v0.2 addition — Response Provenance Field Check (mandatory)**

```
For each /api/analyze response:
  [ ] response body has `result`        (non-empty)
  [ ] response body has `sources`       (non-empty array OR explicit empty + reason in _qc)
  [ ] response body has `_qc`           (object)
  [ ] response body has `qa_result`     (object)
  [ ] each `sources[]` entry has a date field (date / published_date / published_at)
       OR _qc.source_date_unknown=true is explicitly set
  [ ] _qc.fact_coverage.matched_search_hits is recorded (≥0)
  [ ] _qc.fact_coverage.cited_sources_count is recorded (≥0)
```

**Rationale**: C's E-06 captured a real gap — 17 sources returned with zero timestamps, `matched_search_hits=0`, `cited_sources_count=0`. v0.1 missed requiring these fields be present. v0.2 makes them mandatory.

### 5.5 Layer 4 — Research Workflow (AMENDED)

```
PLAN entered  →  RETRIEVE entered  →  ...  →  DONE entered
```

**v0.2 addition — Claim → Evidence Governance Binding (mandatory)**

For each material claim in the output:

```
Claim (textual or numeric assertion in result)
  ↓
Evidence ID        — required: claim tagged with evidence_id
  ↓
Source             — required: source resolves to known provider or document
  ↓
Allowed Use        — required: claim type permitted by Evidence Manifest
  ↓
Blocked Fields     — required: any forbidden field blocked at Trust Gate
  ↓
Output Decision    — required: PASS / DEGRADE / BLOCK per allowed_use
```

**Rationale**: C's L4.3 (Output Boundary) found the response contained 60 numeric claim patterns and 36 textual source markers, but the output had `0` `evidence_id`, `0` `allowed_use`, `0` `blocked_fields`. The disclaimer does not repair missing claim-to-evidence bindings. v0.2 makes the binding mandatory for Layer 4 PASS.

This binding is the operational form of `Vera_Evidence_Manifest_Protocol_v0.1.md` §2 three questions — what did Vera see / what was Vera allowed to say / what reached the user.

### 5.6 Layer 5 (unchanged)

---

## 6. Execution Boundary (unchanged from v0.1)

CCB / CCA / C lanes explicitly locked. C is Evidence Collector, not Framework Designer. Framework amendments happen in v0.x revisions, not in C's execution window.

---

## 7. Execution Checklist (for C, under authorized window)

### 7.1 Layer 1 (unchanged)
### 7.2 Layer 2 (unchanged)
### 7.3 Layer 3 — Application Runtime (AMENDED)

```
[ ] uvicorn process starts (process, worker count, listening port, startup timestamp)
[ ] POST /api/analyze authenticated non-cached request
[ ] Response body contains: result / sources / _qc / qa_result
[ ] DB pool checkout/checkin events with held_s timestamps
[ ] No QueuePool timeout during execution
[ ] Layer 1 and Layer 2 remain PASS through this exercise

[v0.2 NEW — Response Provenance Field Check]
[ ] each sources[] entry has date OR _qc.source_date_unknown is explicit
[ ] _qc.fact_coverage.matched_search_hits recorded (≥0)
[ ] _qc.fact_coverage.cited_sources_count recorded (≥0)
[ ] captured F-04-class DB-hold duration explicitly reported (held_s)
```

### 7.4 Layer 4 — Research Workflow (AMENDED)

```
[ ] 7-step state machine trace (PLAN → DONE)
[ ] At least one controlled degradation scenario
[ ] Cancellation / timeout resource release evidence

[v0.2 NEW — Claim→Evidence Governance Binding]
[ ] each material claim tagged with evidence_id
[ ] each evidence_id resolves to known source
[ ] each claim type permitted by allowed_use
[ ] any forbidden field blocked at Trust Gate (or absent)
[ ] output decision per claim recorded
[ ] _qc.sources / section_data_usage / cited_sources_count populated
```

### 7.5 Layer 5 (unchanged — separate authorization)

### 7.6 Runtime Verification Entry Rule (v0.2 NEW — from C's Configuration Gate Audit v0.1)

Before any Runtime Verification case enters Layer 3 / Layer 4 / Layer 5 execution, it **must declare**:

```text
Target runtime:
  local static demo / local demo API / production FastAPI / MCP / script

Credential source:
  dotenv / shell / systemd / none / unknown

Provider identity:
  provider name + SDK/API route + credential alias

Data source:
  AkShare / Qwen / OpenRouter / JQData / iFinD / Choice / Tushare / other

Runtime consumer:
  frontend route / backend route / research runtime / MCP tool / script

Capability claim:
  NOT CLAIMED until evidence reaches runtime consumer
```

If any field is `UNKNOWN`, the case may proceed **only as scoped evidence collection, not as capability validation**.

**Rationale**: C's `SHARED_CONFIGURATION_GATE_AUDIT_v0.1.md` §3-§7 established that local and production are **not the same application runtime**: LLM identity drifts (local OpenRouter vs production Qwen), `.env` key sets differ materially, Python package versions differ, requirements hashes differ, and production has no git metadata. Without an explicit Target Runtime declaration, a Layer 3 PASS in local cannot be extrapolated to Layer 3 PASS in production, and vice versa. This rule closes that gap.

Source: `docs/governance/SHARED_CONFIGURATION_GATE_AUDIT_v0.1.md` §9.

---

## 8. Sign-off

| Role | Statement |
|------|-----------|
| Framework author (CCB) | v0.2 is a minimal amendment to v0.1 evidence requirements, triggered by C's execution feedback. Runtime NOT EXECUTED. Production NOT CLAIMED. CCB does not run Runtime. No new Capability Maturity promotion implied. |
| Architecture alignment (CCA) | Layer 4 amendment aligns with `Vera_Evidence_Manifest_Protocol_v0.1.md` §2 three-question protocol (operational form). No architecture change. |
| Execution handoff (C) | C's v0.2 checklist is the new rulebook. C executes under separate authorized window. |
| Window authority | v0.2 may be FROZEN only after the next Runtime Execution cycle returns PASS (or PASS-equivalent) on the amended Layer 3 + Layer 4 evidence requirements. FROZEN does not equal CLOSED. |

---

## 9. Review Checklist (binding before FROZEN, expanded)

- [ ] Each Layer has explicit status (L1 / L2 / L3 / L4 / L5 in §4 are populated).
- [ ] Status schema is consistent (§3).
- [ ] Evidence requirements are tiered (§5 Layer-by-Layer).
- [ ] Execution boundary is role-locked (§6).
- [ ] **CCA alignment preserved** (§0 inherits v1.0 Boundary; §5.4 / §5.5 reference Evidence Manifest Protocol).
- [ ] **v0.2 amendments are derived from v0.1 execution feedback** (§0 Revision Scope traces each amendment to C's evidence).
- [ ] **No scope expansion** (§0 Revision Scope explicitly enumerates what did NOT change).

When all 7 boxes pass, v0.2 may be marked **FROZEN**.

---

## 10. Final Statement

> **Vera 的可信不只是设计可信，不只是 Runtime 能跑，还要每一份输出都能追溯到 claim→evidence→allowed_use 的治理链条。本 v0.2 修订 C 第一次执行所暴露的 evidence 类缺失，不引入新 layer，不引入新 status，不引入新角色。**

---

## Appendix A — Revision Provenance

| Amendment | Triggered by | Source |
|-----------|--------------|--------|
| §5.4 Response Provenance Field Check | C E-06 captured 17 sources with 0 timestamps, 0 matched_hits, 0 cited_sources | C Runtime Execution Report v0.1 §5 E-06 |
| §5.5 Claim→Evidence Governance Binding | C L4.3 captured 60 claims / 36 markers with 0 evidence_id, 0 allowed_use, 0 blocked_fields | C Runtime Execution Report v0.1 §4 L4.3 |
| §7.3 +1 item (provenance field) | Same as §5.4 | Same |
| §7.4 +1 item (claim binding) | Same as §5.5 | Same |
| §9 +2 review items (provenance, feedback-derived) | Self-evident governance discipline | n/a |
| §0 revision scope | Self-documenting discipline | n/a |
| §7.6 Runtime Verification Entry Rule | C Configuration Gate Audit revealed local ≠ production runtime identity; without explicit Target Runtime declaration, Layer 3 PASS cannot extrapolate across environments | C `SHARED_CONFIGURATION_GATE_AUDIT_v0.1.md` §3, §6, §9 |

No other amendments. No new design. No new governance principle.

## Appendix B — Inherited Governance Assets (unchanged)

- `docs/architecture/VERA_ENTERPRISE_ARCHITECTURE_v1.0.md`
- `docs/governance/Vera_Capability_Claim_Governance_Framework_v1.md`
- `docs/governance/INSTITUTIONAL_PROVIDER_ARCHITECTURE_v0.1.md`
- `docs/governance/RESEARCH_RUNTIME_PROVIDER_CONSUMPTION_REVIEW.md`
- `docs/evidence/Vera_Evidence_Manifest_Protocol_v0.1.md`
- `docs/governance/KAN_PIAO_ANALYSIS_RCA.md`
- `docs/governance/D27_INSTITUTIONAL_EVIDENCE_PROVIDER_LAYER_STATUS.md`
- `docs/governance/RUNTIME_EXECUTION_REPORT_v0.1.md` — input to this revision