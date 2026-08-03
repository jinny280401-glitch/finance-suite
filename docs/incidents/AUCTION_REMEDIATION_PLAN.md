# Auction Remediation Plan

**Incident**: INC-20260730-01 (RCA COMPLETE)
**RCA reference**: `docs/incidents/INCIDENT_RCA_CARD_AUCTION_20260730.md`
**Date**: 2026-07-30
**Scope**: Planning only. No API additions. No AkShare modifications. No data source additions. No implementation.

This document answers the four remediation questions per user direction. Each answer is grounded in SOT facts; design-time proposals are explicitly marked DESIGN (not implemented) where they would enter the Implementation Window.

---

## Q1. 哪些路径存在？

The auction / market-pulse data path is currently served by **three layers** in the SOT:

### Layer L1 — Data layer (single canonical)

`/Users/Zhuanz/finance-suite/scripts/auction_data.py` (8196 bytes, mtime 2026-06-29)

- Exposes `get_auction_data()` (async) and `format_auction_data()` (sync)
- 7 fetch helpers calling AkShare directly: `_fetch_zt_pool`, `_fetch_strong_pool`, `_fetch_previous_zt`, `_fetch_changes`, `_fetch_hot_rank`, `_fetch_hot_up`, `_fetch_spot_sorted`
- Provides: `zt_pool`, `strong_pool`, `previous_zt`, `big_buy`, `hot_rank`, `hot_up`, `top_gainers`

### Layer L2 — Aggregation layer (built on L1)

`/Users/Zhuanz/finance-suite/scripts/market_context.py`

- `import auction_data` (line 15) — explicitly depends on L1
- `market_context.snapshot()` calls `await auction_data.get_auction_data(include_top_gainers=False)` (line 342)
- Generates market-context summary fields: `zt_pool_count`, `strong_pool_count`, `previous_zt_count`, etc., with `source: "eastmoney_auction"` (line 84)
- Note (header comment): "只读聚合层：基于现有 auction_data 取数结果生成市场结构摘要"

### Layer L3 — Consumers

Three consumers of L1/L2 are currently present in the SOT:

| Consumer | File | Line | Calls |
|---|---|---|---|
| MCP tool | `mcp_server.py` | 447–460 | `market_pulse()` → `auction_data.get_auction_data()` + `_qc_auction(data)` + `auction_data.format_auction_data(data)` |
| Web API (market-context) | `server_scripts/intel_api.py` | 226–230 | `market_context()` → `market_context.snapshot()` (which calls L1 internally) |
| Web API (golden-pit) | `server_scripts/intel_api.py` | 266+ | `golden_pit()` — independent handler, not auction_data path |

### Frontend consumer

`/Users/Zhuanz/finance-suite/app/auction.html` calls:
- `/api/intel/golden-pit?realtime=true` (line 329)
- `/api/analyze` (line 335)
- Does **not** directly call `/api/intel/market-context`. The "Auction" page is composed primarily from golden-pit + analyze, not from `market_pulse`/`market-context` directly.

### Historical context (NOT a current path)

The 2026-07-17 hotfix memory (`project_auction_qc_hotfix_20260717.md`) mentions `app/auction_data.py` as the Web API path that received the time-gate + QC hotfix. **This file does not exist in the current SOT** (`ls app/auction_data.py` → No such file). Either (a) it was removed in a later commit, or (b) it lived only on the production server filesystem. Cannot be confirmed without server-side inspection (out of RCA scope).

---

## Q2. 哪条是 canonical？

### Declared canonical (current SOT, working tree)

**`scripts/auction_data.py` is the single canonical data layer for auction/market-pulse data.**

Reasoning:
- It is the only file that defines `get_auction_data()` and `format_auction_data()` in the working tree.
- Both the MCP tool (`mcp_server.py`) and the aggregation layer (`market_context.py`) import from it.
- `_qc_auction()` (the QC function) is in `mcp_server.py` but its data originates from `scripts/auction_data.py`.

### Canonical consumer for the auction page

The frontend `app/auction.html` makes two primary calls (`/api/intel/golden-pit` and `/api/analyze`). **Neither directly consumes `auction_data.py`** — they consume the golden-pit analysis and analyze services, which are independent of the auction_data path.

This means: **the `market_pulse` MCP tool / `auction_data.py` path may NOT be the proximate cause of "Auction missing" on the auction HTML page** — that page may be displaying empty due to `/api/intel/golden-pit` or `/api/analyze` failures, not auction_data failures.

Confirmation of the proximate cause requires live read of these two endpoints (out of scope for this plan).

### Drift history

Per 2026-07-17 memory: at that time there were two `auction_data.py` files (`app/` and `scripts/`). The current SOT only has the `scripts/` one. **The drift was apparently resolved (in part) by removal of the `app/` copy** — but no commit message in the local git history confirms this removal, suggesting it may have happened on the production server without local commit.

---

## Q3. 哪些旧路径需要废弃？

### Status of each known path

| Path | Current status | Disposition |
|---|---|---|
| `scripts/auction_data.py` (L1) | Active | KEEP — single canonical data layer |
| `scripts/market_context.py` (L2) | Active | KEEP — read-only aggregation on L1 |
| `mcp_server.py market_pulse()` (consumer) | Active | KEEP — exposes auction data to LLM tools |
| `server_scripts/intel_api.py market_context()` (consumer) | Active | KEEP — exposes aggregation to Web |
| `server_scripts/intel_api.py golden_pit()` (consumer) | Active | KEEP — independent of auction path |
| `app/auction.html` (frontend) | Active | KEEP — primary user-facing surface |
| `app/auction_data.py` (historical Web path) | **Absent from SOT** | NO ACTION NEEDED in SOT; verify production server separately |

### Code paths NOT recommended for addition (deferred)

- A new `auction_data.py` somewhere else — **do not** create.
- An alternative aggregation layer paralleling `market_context.py` — **do not** create.
- A new MCP tool aliasing `market_pulse` — **do not** create.

### Recommended cleanup actions (DEFERRED to implementation window)

1. Add a top-level docstring to `scripts/auction_data.py` declaring it the **single canonical data layer** for auction / market-pulse data, with explicit "do not duplicate" warning.
2. Add a similar note to `mcp_server.py market_pulse()` docstring confirming it is the canonical MCP tool for this data.
3. (Out of SOT) Verify whether `app/auction_data.py` exists on the production server; if yes, mark it for removal there.
4. Search for any other importers of `auction_data` outside the three documented consumers; if found, decide per-importer.

These are documentation-level changes, not code-logic changes.

---

## Q4. Fallback 是否需要设计？

### Current state

`_qc_auction()` docstring (mcp_server.py:172): **"当前 market_pulse 为 AkShare 单源聚合，未做多源降级。"**

This is explicit: **no fallback exists today**. Each AkShare call returns `None` on failure (per the `_fetch_*` helpers' try/except pattern), and the aggregator tolerates empty results. The result: when AkShare degrades, the user sees empty/partial data with `_qc.status=partial` — exactly the symptom reported.

### DESIGN answer (per D27 Provider Architecture §7 Failure and Downgrade Rules)

Yes — fallback design is needed at the **provider layer**, not at the function layer. Concretely:

- **Tier 1 (primary)**: AkShare — current
- **Tier 2 (degraded)**: When AkShare returns empty/timeout for `zt_pool`, `hot_rank`, `top_gainers` (the three critical dimensions), the system should attempt to fall back to an alternative institutional source, **only for the dimensions that failed**, not for the full payload
- **Tier 3 (failure)**: If no source can produce a dimension, return `_qc.status=partial` with `missing_critical_dimensions` listed — same as today, but explicit and audited

### Hard constraints for any future fallback design

Per `INSTITUTIONAL_PROVIDER_ARCHITECTURE_v0.1.md` §3.2 mandatory invariants:
- `CREDENTIAL_EXISTS != CREDENTIAL_LOADED != TRANSPORT_VERIFIED != SESSION_ESTABLISHED`
- A provider MUST NOT skip a state. Each promotion requires evidence produced at that stage.
- Multi-source fallback MUST NOT be collapsed into a single-source capability claim.

Per `INSTITUTIONAL_PROVIDER_ARCHITECTURE_v0.1.md` §8 anti-patterns:
- Using ping or endpoint reachability to prove business capability.
- Treating a sandbox or mock test as production evidence.
- Describing an API call success as "integrated".

### Preconditions before any fallback design is opened

Per D27 Phase 1 FROZEN state and W1–W3 UNKNOWN status:

- **W1**: Authorized Provider Credential — UNKNOWN. No alternative provider's credential exists today for institutional A-share data. Designing fallback without W1 is speculative.
- **W2**: Real Evidence Retrieval end-to-end — UNKNOWN (per `D27_W1_W2_W3_FACT_CHECK.md`).
- **W3**: Live Runtime Validation — UNKNOWN.

**Therefore: fallback design is BLOCKED on W1–W3.** Any fallback implementation attempted today would either (a) re-use the same AkShare credential and thus not be a real fallback, or (b) require a new provider credential that does not exist.

### What CAN be done today (design layer only, no implementation)

1. Document the Tier 1 / Tier 2 / Tier 3 contract in `INSTITUTIONAL_PROVIDER_ARCHITECTURE_v0.2` (out of scope for this remediation plan, listed here for completeness).
2. Document the per-dimension fallback policy (which dimensions are critical, which have substitutes, which have none) as a SPEC only.
3. Add `_qc.dimension_sources` already-existing field to record per-dimension source attribution when fallback is eventually wired — this is already in `_qc_auction()` today as `dimension_sources` (always `"akshare"`).

### What CANNOT be done today

- Implement any new provider call.
- Add a new AkShare endpoint call.
- Modify any `_fetch_*` helper.
- Wire any fallback to a real alternative provider.

---

## Summary

| Question | Answer |
|---|---|
| Paths | 3 layers: L1 `scripts/auction_data.py` (canonical), L2 `scripts/market_context.py` (aggregation), L3 (3 consumers: MCP + 2 Web routes); frontend auction.html consumes golden-pit + analyze, not auction_data directly |
| Canonical | `scripts/auction_data.py` is the single canonical data layer |
| Old paths to deprecate | `app/auction_data.py` no longer exists in SOT; verify production server separately. No other paths to deprecate. |
| Fallback design | NEEDED at provider layer per D27 architecture §7, but **BLOCKED on W1–W3 UNKNOWN**. Only documentation-level changes are possible today. |

## Next-Step Permission Required

Before any further action, the user must explicitly authorize one of:
- (A) Document the Tier 1/2/3 fallback contract in SPEC form only (no code).
- (B) Open D27-B Integration Validation window to begin unlocking W1–W3 (required before any fallback implementation).
- (C) Defer all auction-path work to a separate window, leaving INC-01 in OPEN state.

Until then, this remediation plan is the deliverable. **No code change. No deployment. No architecture change.**

## Sign-off

| Aspect | Statement |
|---|---|
| Scope | Planning only. No implementation. |
| SOT basis | Working tree at HEAD `cdac1ca`. |
| Boundary | D27 Phase 1 FROZEN + W1–W3 UNKNOWN gate is respected. No fallback implementation is proposed in violation of that gate. |
