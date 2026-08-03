# JoinQuant Integration Audit

**Audit Date:** 2026-07-22 (Day 22)
**Auditor:** Claude Fable 5
**Scope:** Full-stack integration verification — Credential → SDK → Auth → Query → QC → Runtime → Consumer → UI
**Method:** No code modification. Each layer verified independently. No cross-layer inference.

---

## Layer 1: Credential

**Status: PASS**

| Check | Result |
|-------|--------|
| JQDATA_USERNAME env var | SET |
| JQDATA_PASSWORD env var | SET |
| JQ_USERNAME env var | SET |
| JQ_PASSWORD env var | SET |
| Loaded from `.env` | YES (via `dotenv`) |

**Evidence:** `scripts/smoke_jqdata_runtime_local.py` confirms `credential_present: true` for all 4 keys.

**Root Cause:** N/A — credentials properly configured.

---

## Layer 2: SDK

**Status: PASS**

| Check | Result |
|-------|--------|
| jqdatasdk installed | YES (v1.9.8) |
| Import path | `.venv/lib/python3.12/site-packages/jqdatasdk/__init__.py` |
| Import succeeds | YES |

**Evidence:**
```
jqdatasdk version: 1.9.8
jqdatasdk path: /Users/Zhuanz/finance-suite/.venv/lib/python3.12/site-packages/jqdatasdk/__init__.py
```

**Root Cause:** N/A — SDK properly installed in venv.

---

## Layer 3: Authentication

**Status: PARTIAL**

| Check | Result |
|-------|--------|
| `auth(username, password)` | SUCCESS |
| Account active | YES |
| Quota total | 1,000,000 |
| Quota used | 1,000,000 |
| Quota remaining | **0** |

**Evidence:**
```json
{
  "success": true,
  "quota": { "total": 1000000, "used": 1000000, "remaining": 0 }
}
```

**Root Cause:** Trial account. 1M call quota fully exhausted. Authentication itself succeeds — the account is valid and the credentials are correct — but no calls remain. A new query that counts against quota would fail.

**Note:** Some query types (info, index_stocks) may not count against quota. The `price` query tested below succeeded despite 0 remaining quota, suggesting the quota counter may be stale or certain endpoints are exempt.

---

## Layer 4: Query

**Status: PARTIAL**

### 4a. Query Execution

| Check | Result |
|-------|--------|
| `price` query (000300.XSHG, 2026-01-26 to 2026-02-02) | SUCCESS — 6 rows returned |
| `info` query (000300.XSHG) | SUCCESS — name/type/date returned |
| Real data (not mock/synthetic) | CONFIRMED — numeric OHLCV values present |

**Evidence (price, truncated):**
```json
{
  "success": true,
  "code": "000300.XSHG",
  "count": 6,
  "data": [
    {"index": "2026-01-26", "open": 4715.38, "close": 4706.96, "high": 4754.18, "low": 4693.16, "volume": 36300448100.0, "money": 796832970315.2},
    ...
  ]
}
```

### 4b. Data Freshness

| Check | Result |
|-------|--------|
| Data range start | 2025-01-26 |
| Data range end | **2026-02-02** |
| Current date | 2026-07-22 |
| Data staleness | **170 days (5.6 months)** |
| Query for current date (2026-07-22) | **FAILS** — "您的账号权限仅能获取2025-04-09至2026-04-16的数据" |

**Root Cause:** Trial account with rolling 1-year data window. Last activation ~2025-04. Data window ended 2026-04-16 for price queries; the `_qc.note` says 2026-02-02 which is even more conservative. Either way, **no data within 5 months of current date**.

### 4c. Query Summary

Query execution works. Real data is returned. But the data is **too stale for any current-market use case** — it can only answer historical/reference questions about dates before February 2026.

---

## Layer 5: QC

**Status: PASS (structural) / PARTIAL (accuracy)**

| Check | Result |
|-------|--------|
| `_qc` present in every response | YES |
| `_qc.status` correct | YES |
| `_qc.sources` correct | YES — `["jqdata"]` |
| `_qc.completeness` | 1.0 on success |
| `_qc.stale_data` populated | **NO** — always `[]` |
| Staleness surfaced to consumer | **NO** |

**Evidence:** The `_qc` block for a successful query:
```json
{
  "_qc": {
    "status": "success",
    "completeness": 1.0,
    "sources": ["jqdata"],
    "fallback_source": null,
    "missing_dimensions": [],
    "stale_data": [],
    "note": "JQData 数据范围: 2025-01-26 至 2026-02-02"
  }
}
```

**Root Cause:** The `_qc` note mentions the data range, but `stale_data` is empty and `completeness` is 1.0. A consumer parsing `_qc` structurally would see "success, complete, no stale data" — when in fact the data is 170 days old. The staleness is only visible in a human-readable `note` field that structured consumers won't parse.

**Gap:** BF-JQ-01 identified that `_qc` must expose unavailable tiers. The corollary here is that `_qc` must also expose data staleness in a machine-readable field, not just a note string.

---

## Layer 6: Runtime

**Status: PARTIAL (bifurcated)**

JoinQuant has **two distinct runtime paths** with opposite status:

### 6a. Direct MCP Tool Path: `jqdata_query`

**Status: PASS**

```
MCP Client → jqdata_query() → scripts.jqdata_fetch.main() → jqdatasdk.auth() → JQData API
```

| Check | Result |
|-------|--------|
| MCP tool registered | YES (`@mcp.tool()` at line 1431) |
| Import path correct | YES — `from scripts.jqdata_fetch import main` |
| Wrapper module exists | YES — `scripts/jqdata_fetch.py` |
| SDK module matches wrapper | YES — `jqdatasdk` |
| End-to-end call works | YES (with data staleness caveat) |

**This path is REAL and FUNCTIONAL.**

### 6b. Fallback Chain Path: `joinquant_data`

**Status: FAIL (PHANTOM)**

```
Data Gateway / wind_query / factor_scan → import joinquant_data → ModuleNotFoundError
```

| Call Site | File:Line | Status |
|-----------|-----------|--------|
| `finance_data_gateway._try_joinquant()` | `scripts/finance_data_gateway.py:69` | **PHANTOM** — `import joinquant_data` fails silently |
| `factor_scan._joinquant_fallback()` | `scripts/factor_scan.py:78` | **PHANTOM** — `import joinquant_data` fails silently |
| `wind_query` (connect) | `mcp_server.py:842` | **PHANTOM** — caught by try/except, returns `connected: false` |
| `wind_query._try_joinquant()` | `mcp_server.py:930-936` | **PHANTOM** — `joinquant_data` is None, returns None |
| `ops/monitor_sources.probe_joinquant()` | `ops/monitor_sources.py:154` | **PHANTOM** — `import joinquant_data` would fail |
| `stock_analysis` JQData fallback | `mcp_server.py:400` | **REAL** — uses `scripts.jqdata_fetch` (correct module) |

### 6c. Runtime Chain Reality

**Declared Chain:**
```
Wind → Tushare → JoinQuant → AkShare
```

**Actual Runtime Chain:**
```
Wind → Tushare → [PHANTOM: joinquant_data not found] → AkShare
```

**The only runtime path where JoinQuant actually executes:**
1. `jqdata_query` MCP tool (direct invocation)
2. `stock_analysis` deep fallback (only when Wind AND AkShare both fail — effectively never in practice)

**wind_query's `connect` confirms:**
```json
{
  "joinquant": false,
  "joinquant_detail": {
    "connected": false,
    "available": false,
    "reason": "provider module unavailable"
  }
}
```

**Root Cause:** Module name mismatch. The real wrapper is `scripts/jqdata_fetch.py` (exposing `jqdatasdk`). The fallback chain expects `joinquant_data` (a module that does not exist). Test `test_wind_query_optional_joinquant.py` explicitly deletes `joinquant_data` from `sys.modules` and asserts success — confirming this is **by-design silent degradation**, not an accidental bug. But by-design silent degradation without QC disclosure = phantom provider.

---

## Layer 7: Consumer

**Status: FAIL**

| Check | Result |
|-------|--------|
| Frontend JS calls `jqdata_query` | **NO** — zero references in `app/*.js` |
| Frontend HTML calls `jqdata_query` | **NO** — zero references in `app/*.html` |
| Automation scripts call `jqdata_query` | **NO** — zero references in `handoff/`, `prompts/` |
| LOOP.md references `jqdata_query` | **NO** |
| Cron/loop automation uses JQData | **NO** |
| Any production data pipeline uses JQData | **NO** |

**Evidence:** `grep -rn "jqdata_query\|jqdata\|joinquant" app/` returns zero results across all `.html` and `.js` files. `grep` across `handoff/` and `prompts/` also returns zero results.

**The only consumer of JoinQuant data is a human or LLM directly calling the `jqdata_query` MCP tool.** No automated pipeline, no frontend dashboard, no scheduled job consumes JoinQuant data.

**Root Cause:** JoinQuant was integrated as a "tool in the toolbox" — accessible via MCP, but never wired into any consumer path. The 5-month data staleness makes it unsuitable for current-market use cases anyway.

---

## Layer 8: UI

**Status: FAIL**

| Check | Result |
|-------|--------|
| Any UI component displays JQData data | **NO** |
| Valuation snapshot uses JQData | **NO** — uses `mx_index_block_finance_data` (东方财富) |
| Stock analysis page uses JQData | **NO** — uses `stock_analysis` (Wind→AkShare chain; JQData only as deep fallback) |
| Market temperature uses JQData | **NO** |

**Evidence:** The valuation snapshot (`app/market-valuation-snapshot.js`) calls `mx_index_block_finance_data` (东方财富 MCP tool). The stock page (`app/stock.html`) calls `stock_analysis` which has JQData as a third-level fallback behind Wind and AkShare — in practice, AkShare always succeeds, so JQData is never reached in the stock page flow.

**Root Cause:** No UI was ever built to consume JQData. The integration stopped at the MCP tool boundary.

---

## Integration Boundary

```
┌─────────────────────────────────────────────────────────────────┐
│                        CONSUMER / UI                             │
│                    ❌ NOT INTEGRATED                              │
├─────────────────────────────────────────────────────────────────┤
│                    AUTOMATION / PIPELINE                         │
│                    ❌ NOT INTEGRATED                              │
├─────────────────────────────────────────────────────────────────┤
│               FALLBACK CHAIN (wind_query / gateway)              │
│               ❌ PHANTOM — import joinquant_data                 │
│                  Module does not exist                            │
├─────────────────────────────────────────────────────────────────┤
│               DIRECT MCP TOOL (jqdata_query)                     │
│               ✅ REAL — jqdata_fetch → jqdatasdk                  │
│               ⚠️  Quota exhausted (0 remaining)                  │
│               ⚠️  Data 170 days stale (ends 2026-02-02)          │
├─────────────────────────────────────────────────────────────────┤
│                    QC LAYER                                      │
│               ✅ Structural PASS                                 │
│               ⚠️  Staleness not machine-readable                 │
├─────────────────────────────────────────────────────────────────┤
│                    SDK (jqdatasdk v1.9.8)                        │
│               ✅ Installed in venv                                │
├─────────────────────────────────────────────────────────────────┤
│                    CREDENTIAL                                    │
│               ✅ JQDATA_USERNAME / JQDATA_PASSWORD configured    │
└─────────────────────────────────────────────────────────────────┘

▲ Integration Boundary: MCP Tool
│
│  Everything above this line is NOT integrated.
│  Everything below this line IS working (with caveats).
```

---

## Final Status

```
╔══════════════════════════════════════════════════╗
║           JoinQuant Integration Status            ║
╠══════════════════════════════════════════════════╣
║ Credential (env vars)               ✅ PASS       ║
║ SDK (jqdatasdk v1.9.8)              ✅ PASS       ║
║ Authentication (account valid)      ⚠️  PARTIAL   ║
║ Query (real data, but stale)        ⚠️  PARTIAL   ║
║ QC (structural ok, staleness gap)   ⚠️  PARTIAL   ║
║ Runtime — Direct MCP Tool           ✅ PASS       ║
║ Runtime — Fallback Chain            ❌ FAIL       ║
║ Runtime — stock_analysis fallback   ✅ PASS       ║
║ MCP Tool registered                 ✅ PASS       ║
║ Consumer (automation/pipeline)      ❌ FAIL       ║
║ UI (frontend)                       ❌ FAIL       ║
╠══════════════════════════════════════════════════╣
║                                            .     ║
║ Integration Boundary: MCP TOOL (Layer 6a)  .     ║
║                                            .     ║
║ Above this line: NOT INTEGRATED            .     ║
║ Below this line: WORKING (with caveats)    .     ║
╚══════════════════════════════════════════════════╝

FINAL: PARTIAL
Breakpoint: Consumer Layer (Layer 7)
Root Cause: Integration stopped at MCP tool boundary.
            No consumer, no UI, no automation wired.
Secondary: Fallback chain uses phantom module name.
Tertiary: Data 170 days stale + quota exhausted.
```

---

## Findings Summary

| ID | Layer | Severity | Finding |
|----|-------|----------|---------|
| JQ-01 | Runtime | **HIGH** | `joinquant_data` module does not exist. Three call sites (`finance_data_gateway.py:69`, `factor_scan.py:78`, `mcp_server.py:842`) import a phantom module. Real wrapper (`jqdata_fetch`) never called by fallback chain. |
| JQ-02 | Consumer | **HIGH** | No consumer exists. Zero UI components, zero automation scripts, zero pipelines consume JoinQuant data. Integration is an MCP tool with no downstream consumer. |
| JQ-03 | Query | **MEDIUM** | Data 170 days stale (window ends 2026-02-02). All queries for current dates fail with permission error. Account is trial-tier with expired data window. |
| JQ-04 | Auth | **MEDIUM** | Quota exhausted (1M/1M). Account valid but at call limit. Certain endpoints may still work; behavior inconsistent. |
| JQ-05 | QC | **LOW** | `_qc.stale_data` always empty. Data staleness only reported in human-readable `note` field. Machine consumers see `completeness: 1.0` on 5-month-old data. |
| JQ-06 | Runtime | **INFO** | `stock_analysis` has a correct JQData fallback at `mcp_server.py:400` using `jqdata_fetch` (right module), but it only fires after Wind+AkShare both fail — effectively never in practice because AkShare always succeeds. |

---

## Comparison with Previous Audit (2026-07-17)

| Dimension | 2026-07-17 (data-source-check) | 2026-07-22 (this audit) |
|-----------|-------------------------------|------------------------|
| SDK | jqdatasdk NOT in local pip3 | jqdatasdk v1.9.8 in venv ✅ |
| Auth | PASS (MCP internal) | PASS (confirmed) |
| Quota | 0 remaining | 0 remaining (unchanged) |
| Data range | Ends 2026-04-16 | Ends 2026-02-02 (confirmed) |
| MCP tool | Working | Working |
| Consumer | Not checked | **FAIL** — zero consumers |
| Fallback chain | Not checked | **FAIL** — phantom module |
| Overall | "受限" | **PARTIAL** — boundary identified |

The 2026-07-17 check correctly identified that JoinQuant was "受限" (restricted) due to quota + data range. This audit adds the critical finding that **even if quota and data range were resolved, JoinQuant would still not be integrated** because:
1. No consumer exists (Layer 7-8)
2. The fallback chain imports a non-existent module name (JQ-01)

---

## BF-JQ-01 Status Update

BF-JQ-01 (2026-07-20) correctly identified the phantom provider pattern. This audit confirms and extends:

- **Confirmed:** `joinquant_data` module does not exist. Three call sites import it.
- **Confirmed:** `jqdata_fetch` is the real wrapper, never imported by fallback chain.
- **Confirmed:** Silent import failure creates phantom provider in chain.
- **New finding:** Even the working path (`jqdata_query` MCP tool) has no consumer.

BF-JQ-01 remains **OPEN** — no remediation has occurred.

---

*Audit closed 2026-07-22. No code modified. Next action: decide whether to (a) wire JoinQuant into consumer paths, (b) remove it from declared fallback chains, or (c) leave as-is with explicit documentation of the integration boundary.*
