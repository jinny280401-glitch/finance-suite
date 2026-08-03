# Golden Pit Evidence Collection Governance Boundary v0

**Window**: Golden Pit Evidence Collection Window (D29 directional)
**Status**: DESIGN — read-only governance boundary, **does not lift D23 COMPETITION FROZEN**
**Effective date**: 2026-07-30
**Supersedes**: None (added layer; does not amend `golden-pit-d23-freeze` or `project_golden_pit_simulation_experiment_v0_2`)
**Layer relationship**: This document is **collector-only**. It constrains HOW evidence may be gathered from the frozen v0.2 artifacts; it does NOT re-open Stage 2, does NOT fix BF-GP-001/002, and does NOT authorize any forward execution.

---

## 1. Three confirmations (per user directive, 2026-07-30)

### 1.1 Frozen strategy identity

**Locked**:
- `~/.claude/plans/fancy-imagining-phoenix.md` — **v0.2 DESIGN FROZEN**
- `~/trading-system/experiments/golden-pit-v0/` — full package
- `GATE_MANIFEST.md` — version **v0.2.1**
- `SIGNAL_FORMULA_MAP_v0.2.md` — frozen signal formulas
- `STAGE2_SMOKE_EVIDENCE_CLOSE_CARD.md` — hash-locked Stage 2 evidence

**Identity invariants** (any of these changes = NOT v0.2 anymore):
1. Two-layer separation: `jqdatasdk` (local SDK) ≠ `jqdata` (web backtest framework). Platform Smoke runs **only** on `joinquant.com`. (Per D23 memory §"核心设计决策".)
2. Pre-registration locks: RQ-1, RQ-2, RQ-3, Primary Metric (Calmar), Failure Criteria. All frozen **before** any backtest execution.
3. Single-variable isolation:
   - Phase 1: only entry parameter changes (10-day exit rule fixed)
   - Phase 2: only exit parameter changes
4. Signal Flow funnel: 候选池 → 观察池 → 信号 → 成交 → 盈利/止损 (this 5-stage funnel is structural, not just naming).

**Identity verification path**:
A new evidence collection may read these sources. Any drift detection must be flagged, but **does NOT trigger a fix** — drift observed under COMPETITION FROZEN is recorded, not remediated.

### 1.2 Allowed experiment scope

**Allowed** (read-only, no execution):
| # | Operation | Result type |
|---|-----------|-------------|
| A1 | SHA-256 re-hash of `STAGE2_SMOKE_EVIDENCE_CLOSE_CARD.md` and compare against baseline | Identity confirmation |
| A2 | File existence check across `~/trading-system/experiments/golden-pit-v0/` | Structural integrity |
| A3 | Inspect `SIGNAL_FORMULA_MAP_v0.2.md` and verify parameter freeze (no edit) | Config snapshot |
| A4 | Inspect `GATE_BOUNDARY_AUDIT.md` and verify boundary definitions unchanged | Boundary record |
| A5 | Cross-reference v0.2 spec with STAGE2_EVIDENCE_REPORT_DRAFT.md completeness | Coverage record |
| A6 | Re-emit `EXPERIMENT_MATRIX_v0.2.md` rows into a derived observation table (read-only) | Observation (not measurement) |
| A7 | Hash-chain validation across `STAGE2_SMOKE_EVIDENCE_CLOSE_CARD.md` and dependent docs | Identity chain |

**Forbidden** (would lift COMPETITION FROZEN — never under this window):
| # | Operation | Why forbidden |
|---|-----------|---------------|
| F1 | Re-run Stage 2 platform smoke | Re-execution; pollutes Stage 2 evidence |
| F2 | Fix BF-GP-001 / BF-GP-002 | Stated preserved-as-is in D23 freeze |
| F3 | Activate Stage 3 (PAUSED → RUNNING) | Per D23 freeze |
| F4 | Modify any parameter in `SIGNAL_FORMULA_MAP_v0.2.md` | Strategy mutation, **explicitly forbidden by user directive** |
| F5 | Run Historical Backtest or Forward Simulation | HOLD / NOT STARTED states must remain |
| F6 | Compute Calmar / Sharpe / returns / drawdown | **收益评价 forbidden by user directive** |
| F7 | Run any LLM/Agent to "interpret" Stage 2 evidence into strategy claims | Boundary collapse — would re-introduce PARTIAL→VERIFIED inference shortcut |
| F8 | Add, delete, or rename files in `~/trading-system/experiments/golden-pit-v0/` | Identity mutation |

### 1.3 Evidence classification

| Tier | Definition | Examples | Allowed | Forbidden |
|------|------------|----------|---------|-----------|
| **Tier 0** | Hash integrity | `sha256(Stage2_Close_Card) == baseline` | ✅ Collect | — |
| **Tier 1** | Structural (existence) | File present / directory listing | ✅ Collect | — |
| **Tier 2** | Config snapshot | Parameter values from frozen formula map, verbatim | ✅ Collect | ❌ Modify |
| **Tier 3** | Measured outcome | Calmar, drawdown, hit rate, win/loss | ❌ **Not collected** | ❌ Not computed |
| **Tier 4** | Forward simulation | Stage 3 / Forward sim outputs | ❌ Not started | ❌ Not started |

**Critical invariant**: this classification system is **read-only by design**. Tier 0/1/2 evidence may grow in count, but the schema and sources do not change. Tier 3 and Tier 4 remain out of bounds for **this** window indefinitely (or until COMPETITION FROZEN is lifted by separate decision).

---

## 2. Window restrictions (carry-overs from prior freezes)

This window does NOT lift, soften, or restate:
- **D23 COMPETITION FROZEN** (per `golden-pit-d23-freeze`)
- **D26 关窗声明** (no new capability, no production chain edits, no implementation)
- **D27 Gate Decision** (D27 Window: DESIGN REVIEW, Implementation: NOT AUTHORIZED, Production: NOT CLAIMED)
- **D28 read-only audit posture**

Cross-window pollution is real. Any evidence collection that depends on lifted state from these is invalid by construction.

---

## 3. Discipline requirements (collector-side)

| # | Discipline | Why |
|---|------------|-----|
| D1 | Every collection run emits a **timestamped read receipt** at a known path | Provenance = evidence-layer requirement |
| D2 | No collection may **trigger** a side-effect that mutates the frozen package | Even an unintended write violates F8 |
| D3 | Tier 3 / Tier 4 results may not appear in any collector output, even by accident | Discipline > "I didn't mean to compute it" |
| D4 | All paths accessed are **absolute, never relative**; no `cd` into the package dir | Path discipline = `feedback_use_absolute_paths_for_open` |
| D5 | BF-GP-001 / BF-GP-002 findings are **preserved as-is**, may be referenced, **may not be retroactively closed** by collector | OPEN/UNFIXED status is the truth |
| D6 | If a hash mismatch is detected (A1 returns false), collection halts; the mismatch event is recorded, not adjudicated | Identity drift = window-pause trigger, not trigger for fix |
| D7 | Collector must NOT cite this window's outputs as "Golden Pit strategy validated" at any future point | Boundary collapse prevention |

---

## 4. Failure modes (window-internal)

| # | Failure | Detection | Window response |
|---|---------|-----------|-----------------|
| FM1 | Hash drift (Tier 0 fail) | `sha256sum` differs from baseline | Halt collection; emit drift receipt; do not re-run Stage 2 |
| FM2 | File missing (Tier 1 fail) | `ls` returns fewer files than frozen inventory | Halt; emit missing-file receipt |
| FM3 | Accidental Tier 3 computation | Any `calmar / sharpe / return` token appears in collector output | Reject the run; redact from receipt |
| FM4 | F4 / F5 / F6 violation detected | Audit trail sees execution-related syscall | Window collapses; revert to D23 freeze as base |
| FM5 | Boundary collapse (D7 violated downstream) | External citation observed at P1+ level | Self-report to D28 audit trail |

---

## 5. Evidence outputs this window may produce (only)

For each collection run:
1. **Hash integrity receipt** (Tier 0)
2. **Structural inventory receipt** (Tier 1)
3. **Config snapshot receipt** (Tier 2 with verbatim quoting)
4. **Drift report** (if FM1/FM2 triggered)
5. **Boundary-preserved acknowledgments** (BF-GP-001/002 status, Stage 3 PAUSED status, Historical Backtest HOLD status)

Each receipt is **append-only** and timestamped.

This window explicitly does **NOT** produce:
- Strategy effectiveness claims (FM3 + F6 prohibition)
- Stage 3 reactivation
- Backtest results
- Forward simulation results

---

## 6. Relationship to Memory Receipt v0 (next window)

Per `project_d23_runtime_trust_next_window_spec`, Memory Receipt v0 is the next-window precondition for any Trust Gate memory-side capability. The receipts produced by this Golden Pit Evidence Collection Window are **candidate** Memory Receipt v0 inputs:
- Each receipt above corresponds to a memory-receipt-style artifact.
- For Memory Receipt v0 promotion, additional provenance guarantees are required (per Receipt v0 spec, not this window).

This window's collection discipline is **necessary but not sufficient** for Memory Receipt v0 promotion.

---

## 7. Disallowed actions under this window

Carried verbatim from user directive 2026-07-30:
- ❌ 调参 — any parameter change
- ❌ 策略修改 — any strategy mutation
- ❌ 收益评价 — any return/return-like metric computation or comparison

Plus from §1.2:
- ❌ F1–F8 (all listed re-execution / fix / claim operations)

---

## 8. Sign-off

| Role | Statement |
|------|-----------|
| Author (CC, this session) | This boundary document is read-only governance. It defines a narrow evidence-collection discipline; it does not lift D23 COMPETITION FROZEN or any prior freeze. |
| Window authority (user) | Approve-and-go, or amend §1.2 / §1.3 before activation. |
