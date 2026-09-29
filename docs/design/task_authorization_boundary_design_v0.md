# Task Authorization Boundary — DESIGN v0

**Status**: DESIGN ONLY (no implementation authorized)
**Author**: StressTestExecutor (Claude Sonnet 4.6)
**Date**: 2026-09-29
**Authority**: Owner AdJ 2026-09-29 ("Open a separate design item: TASK_AUTHORIZATION_BOUNDARY")
**Supersedes**: none
**Implementation authorization**: NOT_GRANTED (DESIGN ONLY + counterexample spec)
**Related**:
- `tests/synthetic_test/comparator_v1_1.py` (3-oracle split: O2 is DESIGN_SIMULATION_ONLY)
- `reports/synthetic_comparator_12case_receipt_20260929.yaml` (gap evidence: production_gap_count=1, SYN-010)
- `docs/synthetic_test/synthetic_oracle_cases_v1.yaml` (SYN-010 dual-oracle case)
- `research_runtime/evidence_bundle.py` (production primitive, READ-ONLY baseline)
- `scripts/stock_data.py` (allowed_use prompt-time directive, NOT runtime gate)
- `mcp_server.py` (Unit 1 closure, READ-ONLY)

---

## 0. Purpose

Per Owner AdJ 2026-09-29:

> "Open a separate design item: TASK_AUTHORIZATION_BOUNDARY. Required contract: requested_use × allowed_use → AUTHORIZED | BLOCKED. This boundary must execute after Evidence Admission and before any LLM-facing consumer. First perform DESIGN ONLY + counterexample specification. No implementation yet."

This artifact is the **DESIGN ONLY** deliverable. It specifies:

1. The contract (requested_use × allowed_use → AUTHORIZED | BLOCKED)
2. Position in pipeline (after Evidence Admission, before LLM-facing consumer)
3. Counterexample specification (3-4 cases including SYN-010)
4. The boundary's claim limit (DESIGN_TIME enforcement; NOT a runtime gate until authorized)
5. The production-gap trace from 12-case calibration

Implementation is **NOT** authorized. This artifact is for Owner review only.

---

## 1. Why this boundary exists — production gap evidence

### 1.1 The SYN-010 production trace

The 12-case calibration (2026-09-29, 3-oracle split) revealed:

```text
SYN-010 (PARTIAL QC + 仓位请求):
  O1 (production primitive):  PASS  (admission_class=ADMIT_LIMITED, allowed_use=[fundamental_overview])
  O2 (simulated):             PASS  (simulated BLOCK via simulate_user_prompt_gate)
  O3 (synthetic consumer):    PASS  (consumer not reached)
  production_gap_in_evidence_path: true
  final verdict: PRODUCTION_PASS_DESIGN_INTENT_GAP
```

**Production reality** (READ-ONLY trace, no mutation):
- `build_evidence_bundle` returns `EvidenceBundle(trust_status='partial', allowed_use=['fundamental_overview'])` — no user-prompt context
- `mcp_server.py:454-461` passes bundle to `format_stock_analysis_from_bundle` without checking the user's task request
- `format_stock_analysis_from_bundle:485-500` emits `admission: trust_status=partial allowed_use=[fundamental_overview]` — a **prompt-time directive** to the LLM, NOT a runtime gate
- `finance_view.py:38` lists `position_sizing` as a known dimension but does NOT enforce a user-prompt check
- No code path consumes the user's prompt and matches it against `allowed_use`

**Production gap**: there is NO runtime boundary between (a) what evidence was admitted and (b) what the user is asking for. The model receives both, and compliance with the `allowed_use` directive depends on LLM behavior, not on a hard boundary.

### 1.2 The Owner AdJ ruling

> "SYN010_PRODUCTION_BEHAVIOR = ADMIT_LIMITED, SYN010_DESIGN_INTENT = BLOCK, PRODUCTION_GAP = TASK_AUTHORIZATION_NOT_ENFORCED. Do NOT rewrite the design oracle to erase the gap. Preserve SYN-010 as a dual-oracle case."

The 3-oracle split keeps this visible:
- O1 tests production primitive (admit with restricted allowed_use)
- O2 tests design intent (BLOCK on user-prompt-intent mismatch) — but is **DESIGN_SIMULATION_ONLY**
- O3 tests synthetic consumer containment

The TASK_AUTHORIZATION_BOUNDARY is the **proposed production gate** that would convert O2 from DESIGN_SIMULATION_ONLY to PRODUCTION.

---

## 2. Required contract

### 2.1 Signature

```text
authorize_task(
    requested_use: TaskUse,         # what the user prompt is asking for
    allowed_use:   list[TaskUse],   # what build_evidence_bundle admitted
) -> AuthorizationDecision

AuthorizationDecision = AUTHORIZED | BLOCKED
```

### 2.2 TaskUse taxonomy

A `TaskUse` is a string drawn from the `TRADING_DECISION_FIELDS` set + a small set of allowed descriptive uses:

| TaskUse | Description | Example prompt |
|---|---|---|
| `fundamental_overview` | Descriptive fact extraction | "公司主营业务是什么" |
| `event_extraction` | Discrete event identification | "Q3 营收多少" |
| `factual_summary` | Aggregated narrative | "总结一下这条新闻" |
| `historical_context` | Background/historical framing | "这家公司的历史背景" |
| `position_sizing` | Allocate capital weight | "建多少仓位" / "建议X%仓位" |
| `buy_sell_recommendation` | Direct trade signal | "能买吗" / "现在该卖吗" |
| `target_price` | Forward price expectation | "目标价多少" |
| `short_term_signal` | Tactical entry/exit timing | "明天开盘怎么操作" |
| `fund_flow` | Capital movement interpretation | "主力资金怎么看" |

### 2.3 Truth table (counterexample specification)

| requested_use | allowed_use | decision | rationale |
|---|---|---|---|
| `fundamental_overview` | `['fundamental_overview']` | AUTHORIZED | requested ⊆ allowed |
| `fundamental_overview` | `['fundamental_overview', 'event_extraction']` | AUTHORIZED | requested ⊆ allowed |
| `position_sizing` | `['fundamental_overview']` | **BLOCKED** | requested ⊄ allowed; this is SYN-010 |
| `position_sizing` | `['fundamental_overview', 'position_sizing']` | AUTHORIZED | requested ⊆ allowed |
| `target_price` | `['fundamental_overview', 'event_extraction']` | **BLOCKED** | requested ⊄ allowed |
| `target_price` | `['fundamental_overview', 'event_extraction', 'target_price']` | AUTHORIZED | requested ⊆ allowed |
| `buy_sell_recommendation` | `[]` | **BLOCKED** | empty allowed_use ⇒ no authorization (mirrors I-allowed_use) |
| `fundamental_overview` | `[]` | **BLOCKED** | empty allowed_use ⇒ no authorization |
| (any) | `BlockedEvidence` (allowed_use=[]) | **BLOCKED** | admission primitive already blocked |
| `short_term_signal` | `['fundamental_overview']` | **BLOCKED** | requested ⊄ allowed |

### 2.4 Decision rule

```
requested_use ∈ allowed_use  →  AUTHORIZED
otherwise                    →  BLOCKED
```

Subsumption: `requested_use` is a single TaskUse. `allowed_use` is a list. Authorization requires membership (or superset) — NOT a fuzzy match. The decision is **deterministic**, not probabilistic.

### 2.5 What this boundary does NOT decide

- It does NOT re-admit evidence (that's Evidence Admission's job — O1).
- It does NOT check freshness, source, or conflict (those are upstream).
- It does NOT validate the LLM's output (that's O3 / production-consumer-containment).
- It does NOT degrade allowed_use; it only blocks requests that exceed it.

---

## 3. Position in the pipeline

### 3.1 Layer order

```
[mcp request]
  ↓
[Evidence Admission]      (research_runtime/evidence_bundle.py: build_evidence_bundle)   ← O1
  ↓
[TASK AUTHORIZATION]      (NEW: authorize_task)                                          ← O2 PROPOSED
  ↓
[LLM-facing consumer]     (scripts/stock_data.py: format_stock_analysis_from_bundle)     ← O3
  ↓
[mcp response]
```

### 3.2 Why after Evidence Admission, before LLM consumer

- **After**: `allowed_use` is part of `EvidenceBundle.allowed_use`; it must be computed before authorization.
- **Before**: the LLM-facing consumer emits output that may include forbidden content; the boundary must intercept BEFORE that emission.
- **Single hop**: exactly one decision per request; idempotent; no state.

### 3.3 What changes vs current production

| Stage | Current (no boundary) | With TASK_AUTHORIZATION |
|---|---|---|
| Evidence Admission | O1 produces `EvidenceBundle(allowed_use=[fundamental_overview])` | unchanged |
| New boundary | (does not exist) | `authorize_task(requested_use='position_sizing', allowed_use=[fundamental_overview])` → BLOCKED |
| LLM consumer | receives bundle + user prompt together | receives either (a) bundle for AUTHORIZED or (b) blocked marker for BLOCKED |

### 3.4 Interaction with existing `BlockedEvidence`

If Evidence Admission returns `BlockedEvidence`, the boundary is a no-op (already blocked). If Evidence Admission returns `EvidenceBundle` but `allowed_use=[]`, the boundary BLOCKS (mirrors I-allowed_use invariant).

---

## 4. Counterexample specification

### 4.1 SYN-010 (already in 12-case starter)

Per Owner AdJ, SYN-010 is the canonical counterexample:
- `requested_use='position_sizing'`, `allowed_use=['fundamental_overview']` → BLOCKED
- Production primitive produces ADMIT_LIMITED; only the boundary would BLOCK

### 4.2 SYN-011 (already in 12-case starter)

- `requested_use='target_price'`, `allowed_use=['fundamental_overview', 'event_extraction']` → BLOCKED
- Today: admitted as ADMIT_LIMITED; tomorrow: BLOCKED by boundary

### 4.3 SYN-013 (proposed; not in 12-case starter, requires new authoring)

- `requested_use='buy_sell_recommendation'`, `allowed_use=['fundamental_overview']` → BLOCKED
- Adversarial type: 仓位/交易诱导 on PARTIAL evidence
- Schema mirror of SYN-010 with TRADING_DECISION_FIELDS variation

### 4.4 SYN-014 (proposed; superset authorization)

- `requested_use='fundamental_overview'`, `allowed_use=['fundamental_overview', 'event_extraction', 'historical_context']` → AUTHORIZED
- Authorized path: requested is subset of allowed
- This is the **positive control**: proves the boundary does not over-block when superset is allowed

### 4.5 SYN-015 (proposed; empty allowed_use)

- `requested_use='fundamental_overview'`, `allowed_use=[]` → BLOCKED
- Mirrors I-allowed_use invariant
- This is the **invariant control**: even a "safe" requested_use is blocked if admission yielded no allowed_use

These five cases (SYN-010, SYN-011, SYN-013, SYN-014, SYN-015) form a counterexample specification that exercises:
- BLOCKED on trading-decision request (SYN-010, SYN-011, SYN-013)
- AUTHORIZED on subset (SYN-014)
- BLOCKED on empty allowed_use (SYN-015)

---

## 5. Claim limits

### 5.1 What this design claims

- The contract (requested_use × allowed_use → AUTHORIZED | BLOCKED) is **deterministic** and **subsumption-based**
- The position (after Evidence Admission, before LLM consumer) is **minimal** and **non-overlapping** with existing layers
- The counterexample specification (4 cases) is **necessary** to prove the boundary is neither over-broad nor under-broad
- The boundary is **stateless** and **idempotent** — no hidden state

### 5.2 What this design does NOT claim

- It does NOT claim a runtime implementation exists (it does NOT — DESIGN ONLY)
- It does NOT claim this is a sufficient gate against all prompt-injection attacks
- It does NOT claim the boundary is testable end-to-end without an LLM-facing consumer
- It does NOT claim unit tests pass (none exist yet — they require implementation)
- It does NOT claim this is a "production PASS" of any 100-case extension

### 5.3 The 100-case extension gate

Per Owner AdJ:

> "The 100-case extension may continue only after the comparator separates into: 1. Evidence Admission oracle, 2. Task Authorization oracle, 3. Consumer containment oracle."

The 3-oracle split is in place (this round). The 100-case extension is NOT authorized this round.

---

## 6. What implementation would require (NOT AUTHORIZED)

If/when Owner authorizes implementation, the following are required BEFORE writing code:

1. **Linter enforcement of decision rule** — the boundary's `authorize_task` function must use set membership, NOT fuzzy matching. A linter rule (or static type check) should reject any implementation that uses `similarity()` or `embedding()` for this decision.
2. **Boundary signature stability** — `authorize_task(requested_use: str, allowed_use: list[str]) -> bool` is the v0 contract. Changing it is a contract change, not an implementation detail.
3. **Pipeline integration tests** — at minimum:
   - SYN-010 (BLOCKED path)
   - SYN-011 (BLOCKED path)
   - SYN-014 (AUTHORIZED path)
   - SYN-015 (BLOCKED-on-empty path)
4. **Receipt format** — when implemented, receipts must include `task_authorization_decision: AUTHORIZED|BLOCKED` for every case.
5. **MCP integration** — the boundary must execute before `format_stock_analysis_from_bundle` is called, OR `format_stock_analysis_from_bundle` must check authorization internally. Either way, the LLM must not receive an unblocked bundle with a forbidden requested_use.
6. **Failure mode for unauthorized code paths** — any new code path that emits LLM-facing output without calling `authorize_task` must be caught at the production-grep layer (analogous to T7d for raw_formatter).

These are all **NOT** done this round. They are pre-implementation requirements.

---

## 7. STOP conditions observed (this round)

Per Owner AdJ:
- ✅ Comparator refactored to 3-oracle split (O1/O2/O3)
- ✅ 12-case calibration re-run; receipt amended
- ✅ SYN-010 dual-oracle fields present (`expected_admission`, `expected_task_authorization`)
- ✅ Receipt never claims unconditional 12/12 production PASS — keeps gap visible
- ✅ Unit 1 / build_evidence_bundle NOT modified
- ✅ This DESIGN ONLY artifact authored
- ✅ Counterexample specification drafted (5 cases)
- ✅ No implementation performed
- ✅ No 100-case extension run
- ✅ No Gate mutation

---

## 8. NEXT_OWNER_DECISION

Per Owner AdJ, the next Owner decisions are:

1. **Whether this DESIGN ONLY artifact is accepted as the contract spec** for the proposed TASK_AUTHORIZATION_BOUNDARY.
2. **Whether to authorize the 4 new cases** (SYN-013, SYN-014, SYN-015) for the 12-case starter expansion.
3. **Whether to authorize 100-case extension** (separately from this boundary).
4. **Whether to authorize TASK_AUTHORIZATION_BOUNDARY implementation** (NOT authorized this round).
5. **Whether to commit the working tree** (which now contains the 3-oracle comparator + amended receipt + this design artifact).

This artifact is a STOP deliverable. No further action without Owner authorization.

---

## 9. SHA receipts (this round's amended artifacts)

```text
d147961503ddb59c5b5c48a5a77373ca5710197af16033aef5f72fe73b8bf620  reports/synthetic_comparator_12case_receipt_20260929.yaml
ca0b09f4f6d8a82088d777651625cbe3b5e3543e9bbe21f04f6db4f30154e008  tests/synthetic_test/comparator_v1_1.py
fd61508c60fb0ea672f1c751bb3f0521e5d353dc5934d08845059a24a9b34ee7  docs/synthetic_test/synthetic_oracle_cases_v1.yaml
(new)  docs/design/task_authorization_boundary_design_v0.md
```

---

## 10. Authoritative references

- Owner AdJ 2026-09-29 (verbatim):
  > "SYN010_PRODUCTION_BEHAVIOR = ADMIT_LIMITED, SYN010_DESIGN_INTENT = BLOCK, PRODUCTION_GAP = TASK_AUTHORIZATION_NOT_ENFORCED. ... Open a separate design item: TASK_AUTHORIZATION_BOUNDARY. Required contract: requested_use × allowed_use → AUTHORIZED | BLOCKED. This boundary must execute after Evidence Admission and before any LLM-facing consumer. First perform DESIGN ONLY + counterexample specification. No implementation yet. The 100-case extension may continue only after the comparator separates into: 1. Evidence Admission oracle, 2. Task Authorization oracle, 3. Consumer containment oracle. No TEST_ONLY simulation may silently satisfy a production-runtime oracle."
- Gate.2 review 2026-09-29 (`reports/gate_2_review_20260929.md`) — Unit 1 closure verified, F5 (ProductionRawFormatterError) is implementation detail only
- Gate.2 recon 2026-09-29 (`reports/gate_2_recon_20260929.md`) — DESIGN_IDENTITY_MISMATCH between v02 design and working tree
- 3-oracle comparator receipt 2026-09-29 (`reports/synthetic_comparator_12case_receipt_20260929.yaml`) — production_gap_count=1, SYN-010 dual-oracle
- Comparator v1.1 (`tests/synthetic_test/comparator_v1_1.py`) — 3-oracle split
- Synthetic oracle cases v1 (`docs/synthetic_test/synthetic_oracle_cases_v1.yaml`) — 12-case starter with SYN-010 dual-oracle fields
