# Research Runtime — Provider Evidence Consumption Review

**Status**: VERIFICATION DESIGN (not implementation)
**Effective date**: 2026-07-29
**Scope**: Validate that Research Runtime consumes Gildata-supplied Evidence Bundles within the discipline set by:
- `docs/evidence_manifest_contract_v0.md` (Evidence dataclass contract)
- `docs/evidence/Vera_Evidence_Manifest_Protocol_v0.1.md` (3-question protocol: saw / allowed-to-say / reached-user)
- `docs/governance/Vera_Capability_Claim_Governance_Framework_v1.md` (Capability Maturity L0–L6)
- `research_runtime/evidence_bundle.py` (Trust Gate Runtime v0)
**Out of scope**: Investment value, return projections, strategy effectiveness. This review only validates whether Evidence is consumed without leakage.
**Window constraint**: D26 freeze active — this document describes a verification flow only. It does not introduce new capability, modify the production chain, or enter implementation.

---

## 0. Pre-conditions observed before drafting

| # | Observation | Evidence | Implication for validation |
|---|-------------|----------|------------------------------|
| P0 | "Gildata" string does not appear anywhere in `finance-suite/` repo (`grep -r Gildata` returns nothing) | empty grep result, 2026-07-29 | Gildata has **no declared Evidence Manifest entry** in this workspace. Any Runtime consumption of a "Gildata bundle" today is by definition operating on UNVERIFIED input. |
| P1 | `evidence_manifest_contract_v0.md` declares an `evidence_id` of the form `evidence:<uuid-hex-8>`, with `forbidden fields = {raw_response, gateway_response, provider_payload, _qc, raw, payload}` | evidence_manifest_contract_v0.md §2.1–2.2 | Runtime MUST NOT surface these fields in any consumer-visible artifact. The validator's job is to prove they do not. |
| P2 | Evidence Manifest Protocol v0.1 binds three evidence-faces: **saw / allowed-to-say / reached-user** | Evidence_Manifest_Protocol_v0.1.md §2 | The test flow must capture all three. Anything missing one face is incomplete evidence. |
| P3 | `EvidenceBundle.allowed_use` is the only mechanism Runtime uses to gate downstream speech (`research_runtime/evidence_bundle.py` _allowed_use) | `_allowed_use` in `research_runtime/evidence_bundle.py` | Validator MUST assert that every output sentence maps to (a) an evidence_id with non-empty allowed_use intersection, OR (b) a structural artifact not making fact claims. |
| P4 | Capability Maturity Ladder: Feature exists ≠ Capability may be claimed (L0–L6) | Capability_Claim_Governance_Framework_v1.md §2, §3 | Runtime consumption of a Bundle does NOT, by itself, raise claim maturity. This review MUST NOT conclude "Research Runtime is LIVE VERIFIED." |

---

## 1. Test flow (Input → Process → Output)

### 1.1 Inputs (deterministic, reproducible)

| Input | Source | Constraint |
|-------|--------|-----------|
| `bundle` | One serialized `EvidenceBundle` object constructed by injecting a synthetic "Gildata-payload-shaped" payload through the existing `evidence_bundle._run_trust_gate` path | MUST contain the FORBIDDEN_FIELDS so validator can prove Runtime strips them. MUST set `allowed_use` to a known subset (e.g. `["fundamental_overview"]`) so unauthorized uses surface as diff. |
| `session` | `ResearchSession` from `research_runtime/workflow.py` configured with `provider="local_research_stub"` and a fixed `symbol` | Locks run-to-run determinism; no live network. |
| `llm_enabled=False` | Workflow construct enforces | Prevents the validator from being confounded by stochastic LLM output. Disagreement with production LLM run is a separate question. |

### 1.2 Process (one well-defined path)

```text
[1] Construct EvidenceBundle from synthetic Gildata-shaped payload
    ↓ invoke
[2] evidence_bundle._run_trust_gate(bundle)
    ↓ returns TrustGateResult { allowed_bundles, blocked_items, passthrough_items }
[3] ResearchSession.run(context built from gate_result)
    ↓ produces
[4] (a) Research Draft — text artifact
    (b) Evidence Trace — per-sentence evidence_id map
    (c) Unsupported Claim Check — verdict list
```

Process MUST emit a JSONL `events.jsonl` capturing each hop's input/output identity (for replay), per `research_runtime/events.py`.

### 1.3 Outputs (three contracts, all mandatory)

| Output | Schema minimum | What it must prove |
|--------|----------------|--------------------|
| **Research Draft** | Plain text with sentence IDs `S001..SNN` | Every sentence either (a) carries an evidence_id ref, or (b) is a structural connective (no fact claim). |
| **Evidence Trace** | `[{sentence_id, evidence_id, allowed_use_intersection, qc_status, provider_tier}]` | Per-sentence provenance. Empty intersection ⇒ Structural. |
| **Unsupported Claim Check** | `[{sentence_id, kind: "no_source"\|"out_of_scope"\|"boundary_violation"\|"forbidden_field_leak", verdict: "FAIL"\|"PASS"}]` | Final verdict per failure mode (Section 2). |

These three outputs together answer the three Manifest Protocol questions: **saw** (bundle input identity), **allowed-to-say** (allowed_use intersection), **reached-user** (which sentences survive filtering).

---

## 2. Failure modes (the four things Runtime MUST NOT do)

This is the validator's pass/fail lattice. Each cell has a deterministic check.

| Failure mode | Definition | Detection | Verdict |
|---|---|---|---|
| **F1: No-source conclusion** | A sentence making a fact claim (price, ratio, ranking) that has no `evidence_id` in its Evidence Trace row | Trace row has `evidence_id == null` AND sentence pattern matches fact-claim regex (`\$\d+|\d+(\.\d+)?%|\bPE\b|\bROE\b|第一名|领先`) | FAIL if any match |
| **F2: Out-of-scope reasoning** | A sentence whose `allowed_use` for the cited evidence is empty/overlapping-empty, yet the sentence makes a claim requiring a non-cited dimension (e.g. evidence allows `fundamental_overview`, sentence asserts a peer-comparison judgment) | Trace row `allowed_use_intersection` disjoint from sentence's required use-class; use-class inferred from claim-pattern dictionary | FAIL if any match |
| **F3: Boundary-violating prediction** | A sentence asserting future state, target price, returns, or strategy outcome — any of which is out-of-scope per task constraints | Sentence pattern matches prediction-claim regex (`目标价|预计|预期|benchmark|跑赢|超额收益|建议`), and Evidence Trace shows no `live_verified_license` evidence_id | FAIL if any match (block in CI; this is a hard guard, not a soft warning) |
| **F4: Forbidden-field leak** | Any FORBIDDEN field (`raw_response`, `gateway_response`, `provider_payload`, `_qc`, `raw`, `payload`) appearing in Research Draft or Evidence Trace serialized form | String-grep serialized output for exact field names; differ against baseline | FAIL if any match |

The four modes are **independent**; each yields PASS/FAIL. The overall review is PASS only if **all four are PASS**. Any single FAIL is a v0 veto. Aggregation as "soft warning" is prohibited — see Section 4.

---

## 3. Agent Review Chain (4-stage, no parallel false-economy)

The chain is gated, not parallel. Each stage's output is a precondition for the next. A stage that rejects short-circuits with a verdict — it does not "carry forward with caveat."

```text
[Stage 1: Research Agent]
  - Consumes: EvidenceBundle (after Trust Gate)
  - Produces: Research Draft (with sentence IDs)
  - Hard rule: every sentence_id MUST carry or explicitly disclaim provenance
       ❌ "当前估值偏高" — disallowed unless evidence_id is logged in the same sentence
       ✅ "基于 <evidence_id> 的数据 — 见上方 Evidence Trace" — allowed

[Stage 2: Evidence Critic Agent]
  - Consumes: (Draft, Evidence Trace)
  - Produces: Per-sentence audit
  - Checklist (each sentence):
       (a) Has evidence_id?                   → else mark F1
       (b) evidence_id's allowed_use covers claim-type? → else mark F2
       (c) Claim is past/present fact (not prediction)? → else mark F3
       (d) No FORBIDDEN_FIELDS in serialized byte stream? → else mark F4
  - Output: a per-sentence pass/fail table

[Stage 3: Contradiction Check Agent]
  - Consumes: (Draft, Evidence Trace, Critic's audit)
  - Produces: Internal-consistency report
  - Looks for:
       (a) Cross-sentence numeric contradictions
       (b) A claim that maps to two different evidence_ids with conflicting values
       (c) A claim whose evidence_id changes between sentences without notice
  - Output: contradiction list (empty = PASS)

[Stage 4: Trust Gate (existing v0)]
  - Consumes: All three prior outputs
  - Produces: Final verdict (PASS / FAIL / DEFER)
  - DEFER criteria: missing any of Draft/Trace/Unsupported Claim Check,
       OR Trust Gate result has empty allowed_bundles AND Draft has fact claims.
       DEFER is not PASS — a deferred test result is, by framework rule,
       treated as UNVERIFIED, which is below Evidence Verified (L5).
```

Each stage's contract is enforced by a separate validator harness file. The 4 stages are siblings of the runtime smoke tests under `finance-suite/smoke_*` (e.g. `smoke_trust_gate_runtime_v0.py`).

### Why 4 stages, in this order

This is the cheapest chain that satisfies the Evidence Manifest Protocol's three faces. Parallelism would be a false economy: Stage 1 produces the artifact; Stage 2 audits it; Stage 3 requires the artifact+audit as a pair; Stage 4 requires all three prior outputs. There is no upstream-downstream collapse that parallelism would buy here.

---

## 4. Acceptance — what PASS proves, and what it does NOT

### What PASS proves

- Given a single Gildata-shaped EvidenceBundle and a ResearchSession constructed per Section 1, the Runtime emits a Research Draft in which:
  - Every fact-claim sentence has an evidence_id in the Evidence Trace,
  - Every claimed use-class is contained in the cited evidence's allowed_use,
  - No sentence asserts a future-state / target-price / strategy-outcome claim absent a `LIVE VERIFIED` license evidence_id,
  - The serialized output contains none of the FORBIDDEN_FIELDS.

### What PASS does NOT prove

- That Runtime is `LIVE VERIFIED` (L6). Per Capability Maturity Ladder, runtime consumption of one synthetic bundle does not authorize any external capability claim. The framework explicitly forbids inferring L5+ from L4 alone.
- That Runtime behaves correctly under arbitrary LLM stochasticity (this v0 is `llm_enabled=False`; LLM-on validation is a separate scope).
- That any real Gildata endpoint behaves like the synthetic bundle. The P0 observation (no Gildata string in repo) means production Gildata integration is **DECLARED BUT UNVERIFIED** — capability maturity ≤ L2 (`TRANSPORT VERIFIED` at best, and that claim itself is awaiting evidence).
- That Research Draft is "good research." Validator checks discipline, not quality.

### Failure of acceptance — explicit non-goals

This review document MUST NOT be cited as evidence for:
- Investment recommendations or implied buy/sell/hold signals,
- Expected returns, drawdowns, or benchmarks,
- Strategy performance comparisons.

Anyone attempting to do so is contravening the Capability Claim Governance Framework v1.0.

---

## 5. Open questions (Unknown ≠ resolved)

| # | Question | Why it matters | Status |
|---|----------|----------------|--------|
| Q1 | Does Gildata exist as a registered provider in the Evidence Manifest registry, with a recorded `provider_tier` and license? | P0 finding is that no Gildata string exists in the repo. Until verified, any "Gildata bundle" in test is synthetic. | UNKNOWN |
| Q2 | What is the canonical "Gildata-shaped" payload schema that Runtime must accept? | Without a contract, every test bundle is bespoke and test reproducibility is unproven. | UNKNOWN |
| Q3 | Does the Trust Gate v0 correctly classify Gildata as REAL/FALLBACK/MOCK based on freshness/tier signals? | `_classify_provider` requires `freshness` and `provider_tier` fields on the Gateway response. If Gildata payloads do not carry them, classification defaults silently. | UNKNOWN — would need Gildata contract docs |

These are NOT blockers for this review (which validates the Runtime against a synthetic, controlled bundle). They ARE blockers for any production-time claim that Gildata Runtime consumption is `RUNTIME VERIFIED` or beyond.

---

## 6. Handoff to next window

Per D26 Window Close Declaration, this review document is the sole verification output for the named scope (Research Runtime Provider Consumption). Next window (per `[[project_d23_runtime_trust_next_window_spec]]`) opens only against Memory Receipt v0 and Recall Boundary — **not** against this document's red lines. Any extension of this review into production Evidence promotion MUST re-open the window explicitly.

---

## 7. Sign-off block

| Role | Name | Statement |
|------|------|-----------|
| Author | (this document, 2026-07-29) | I have not introduced new runtime capability; I have described a verification flow only. |
| Validator | (to be assigned) | _____________________________ |
| Window authority | D26 declaration | PASS on this document does not lift D26 freeze. |
