# Capability Claim Matrix v1.0

**Window**: D28 Trust Governance Validation Window
**Status**: DESIGN (read-only matrix, no claim promotion)
**Effective date**: 2026-07-30
**Scope**: Cross-walk of capability maturity for each named runtime / provider / system

> **Reading rule**: A "+" cell means "this column's evidence contributes to that maturity level" — **not** "this maturity is achieved." A capability requires **all** prior cells to have supporting evidence before the next may be claimed.

---

## 1. Maturity column definitions

| Column | Meaning | Evidence examples |
|--------|---------|-------------------|
| `Design` | A normative document or design exists at a known path | MD doc registered in `docs/` with version + status |
| `Prototype` | Code / script / smoke harness exists at a known path | `research_runtime/*.py`, `smoke_*.py`, MCP server module |
| `Verified Runtime` | Runtime behavior has been observed in a smoke test, trace recorded, outcome reproducible | `/tmp/research_runtime_latest.json`, `events.jsonl`, smoke logs |
| `Production Capability` | `LIVE VERIFIED` license is issued for a declared scope | Per `Vera_Capability_Claim_Governance_Framework_v1.md` §5 |

**Crucial rule**: Production Capability claims are NOT enforceable without a license.

---

## 2. Matrix

| Artifact | + Design | + Prototype | + Verified Runtime | + Production Capability |
|----------|:--------:|:-----------:|:------------------:|:------------------------:|
| **Wind** | ✅ | ⚠ partial | ❌ | ❌ NOT CLAIMED |
| **Choice (EmQuantAPI)** | ✅ | ⚠ partial | ⚠ partial (Credential + Session only) | ❌ NOT CLAIMED |
| **iFinD (THS)** | ✅ | ⚠ partial (SDK not installed) | ❌ | ❌ NOT CLAIMED |
| **Gildata PoC** | ❌ (no doc on disk; only references in D27 architecture template) | ❌ | ❌ | ❌ NOT CLAIMED |
| **Memory Reliability** | ✅ (Memory Receipt v0 spec) | ❌ | ❌ | ❌ NOT CLAIMED |
| **Research Runtime** | ✅ (this window + D27 review) | ✅ (`research_runtime/*.py`) | ⚠ partial (smoke harness; no synthetic-bundle run artifact attached as of 2026-07-30) | ❌ NOT CLAIMED |

Legend:
- ✅ Evidence present
- ⚠ partial Evidence present but with explicit gap (named below)
- ❌ Evidence absent / claim not made

---

## 3. Row-level evidence trail

### 3.1 Wind

| Column | Evidence | Reference |
|--------|----------|-----------|
| + Design | Provider class referenced in `INSTITUTIONAL_PROVIDER_ARCHITECTURE_v0.1.md` §3 state machine | `docs/governance/INSTITUTIONAL_PROVIDER_ARCHITECTURE_v0.1.md` |
| + Prototype | Smoke scripts observed (`smoke_*.py` x multiple) but no Provider integration completed | repo-wide grep |
| + Verified Runtime | **No.** Last completed integration was blocked (per D19) | `project_d19_findings_20260716.md` (Wind: Credential ≠ Integration) |
| + Production Capability | **NOT CLAIMED.** Maturity ≤ L2 per audit | `feedback_choice_emquant_credential_vs_capability.md` lesson applies to Wind equivalently |

### 3.2 Choice (EmQuantAPI)

| Column | Evidence | Reference |
|--------|----------|-----------|
| + Design | Audit lesson locks Credential ≠ Capability semantics | `feedback_choice_emquant_credential_vs_capability.md` |
| + Prototype | `emquant_data.py` script + `emquant_query` MCP tool registered | `docs/ifind_emquant_integration.md` |
| + Verified Runtime | **Partial**: Credential accepted + Session established verified, but Provider Integration layer explicitly NOT yet proven | §"Five-layer classification" |
| + Production Capability | **NOT CLAIMED.** | Same |

### 3.3 iFinD (THS)

| Column | Evidence | Reference |
|--------|----------|-----------|
| + Design | Spec exists; integration doc lists modes + env vars | `docs/ifind_emquant_integration.md` |
| + Prototype | ⚠ partial: "代码框架已完成, SDK 未安装" | `docs/ifind_emquant_integration.md` §"接入状态" |
| + Verified Runtime | ❌ SDK not installed → no runtime observed | Same |
| + Production Capability | **NOT CLAIMED.** | Same |

### 3.4 Gildata PoC

| Column | Evidence | Reference |
|--------|----------|-----------|
| + Design | ❌ Gildata string does not appear in repo (verified grep 2026-07-29). Architecture v0.1 mentions Gildata only as a design-template reference, not a documented capability target. | `RESEARCH_RUNTIME_PROVIDER_CONSUMPTION_REVIEW.md` §0 P0 |
| + Prototype | ❌ None | grep evidence (empty result for non-architecture refs) |
| + Verified Runtime | ❌ | n/a |
| + Production Capability | **NOT CLAIMED.** Maturity = L0 (UNKNOWN) | per Capability Maturity Ladder §3 |

### 3.5 Memory Reliability

| Column | Evidence | Reference |
|--------|----------|-----------|
| + Design | `project_d23_runtime_trust_next_window_spec.md` defines Memory Receipt v0 + Recall Gate + Freshness Model | memory anchor |
| + Prototype | ❌ No receipt-storing code exists; only spec | n/a |
| + Verified Runtime | ❌ | n/a |
| + Production Capability | **NOT CLAIMED.** | n/a |

### 3.6 Research Runtime

| Column | Evidence | Reference |
|--------|----------|-----------|
| + Design | `docs/governance/RESEARCH_RUNTIME_PROVIDER_CONSUMPTION_REVIEW.md` (this session); `evidence_manifest_contract_v0.md` | both |
| + Prototype | `research_runtime/workflow.py`, `research_runtime/evidence_bundle.py`, `smoke_research_runtime.py` | repo grep |
| + Verified Runtime | ⚠ partial: code paths execute; no synthetic-bundle run artifact (`/tmp/research_runtime_latest.json`) yet attached to the Consumption Review document. Smoke harness exists but no result was published alongside the protocol spec. | §3.5 audit finding (D28) |
| + Production Capability | **NOT CLAIMED.** | per Consumption Review §4 |

---

## 4. Critical absence list (the things still not true)

| # | Item | Why it matters |
|---|------|----------------|
| AB1 | No Provider is currently at `RUNTIME VERIFIED` maturity, let alone `PRODUCTION CAPABLE` | Any Capability Claim requiring Provider support must fail closed per Capability Maturity Ladder §3 |
| AB2 | No `LIVE VERIFIED` license exists for any row | Per Capability Claim Framework §5, LIVE VERIFIED is required for production-quality claim |
| AB3 | No Memory Reliability receipt has been emitted | Memory Receipt v0 is the next-window precondition for any Trust Gate memory-side capability |
| AB4 | Gildata PoC does not exist on disk | Any "we have a Gildata PoC" claim is contradicted by file absence |

---

## 5. How this matrix ages

- Each row's column may transition only by **adding** evidence to the next column; existing cells do not regress without an explicit revocation record.
- A "Verified Runtime" upgrade requires (a) a reproducible smoke or trace artifact at a known path AND (b) a Truth Guard sign-off recorded in the asset's documentation.
- A "Production Capability" entry is **only** achievable via a `LIVE VERIFIED` license under `Capability_Claim_Governance_Framework_v1.md §5`.

---

## 6. Disallowed actions

This matrix is **read-only documentation of current state**. It does NOT authorize:

- ❌ Promoting any cell from ⚠ to ✅ without produced evidence
- ❌ Calling any row "Production" without a license
- ❌ Citing this matrix as evidence for any Provider integration claim

## 7. Sign-off

| Role | Statement |
|------|-----------|
| Author | This matrix is grounded in file-system evidence; rows are not speculative. |
| Window authority | D28 PASS on this matrix does not promote any cell. |
