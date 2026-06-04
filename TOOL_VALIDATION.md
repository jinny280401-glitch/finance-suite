# Phase B Tool Validation Matrix

Date: 2026-06-03

Purpose: classify every Finance Suite MCP tool before E2E user-path testing. Tools marked `FAIL` must not enter model context. Tools marked `PARTIAL` may be used only with the listed limitation text. Tools marked `BLOCKED` require credentials, permissions, browser session, or another external condition before production answers can use them.

## Status Legend

| Status | Meaning | Model Context Rule |
|---|---|---|
| PASS | Can be used directly for production answers within its stated scope. | May enter context with `_qc` attached. |
| PARTIAL | Usable but incomplete, delayed, scoped, or fallback-dependent. | May enter context only with limitation note. |
| FAIL | Returns unsafe, stale, misleading, or unusable data for the stated task. | Must not enter context. |
| BLOCKED | Cannot be validated or used until an external dependency is available. | Must not enter context except as a capability note. |

## Matrix

| Tool | Status | Production Use | Data Source / Dependency | QC / Guardrail | Notes |
|---|---|---|---|---|---|
| `market_pulse` | PASS | Market Context Engine v0.1 first data source; use for market structure summary. | AkShare / Eastmoney market pools | `_qc_auction` tracks missing critical dimensions. | Use now for market temperature, hot ranks, limit-up pool, top gainers. Do not wait for `macro_snapshot`. |
| `macro_snapshot` | FAIL | Do not use for current macro answers until P0 is fixed upstream. | AkShare macro endpoints | P0 guard active: stale GDP/PMI/M2 are removed from body and recorded in `_qc.stale_data`; current status is `failure` when all core indicators are stale. | Latest observed GDP 2007, PMI/M2 2008, CPI stale; only LPR usable. |
| `stock_analysis` | PARTIAL | Basic fundamental overview only. | Wind preferred, AkShare fallback, JQData fallback | Must include limitation: not approved for intraday price, capital flow, or short-term trading calls. | P1 partial. Do not use for盘中行情、资金流、短线判断. |
| `factor_scan` | PARTIAL | Quant/factor idea generation with QC caveat. | trading-system MCP, JoinQuant/Wind/Tushare/AkShare fallback chain | Must preserve `_qc.sources`, `fallback_source`, and `stale_data`. | If JoinQuant trial fallback is used, label delayed historical data clearly. |
| `market_intel` | PARTIAL | Sidebar-style market context panels. | Snowball/Eastmoney/watchlist/research digest aggregation | Use panel-level `_qc`; failed panels must be excluded from answer evidence. | Useful for context, but not all panels are guaranteed live. |
| `xueqiu_fetch` | BLOCKED | Not approved until browser/autocli session is validated. | AutoCLI + Chrome logged-in Snowball session | If unavailable, returns failure. | Validate login/session before using for production answers. |
| `search` | BLOCKED | Not approved until Tavily/Brave keys and freshness are validated. | Tavily / Brave | Must cite source freshness when enabled. | External key dependency. |
| `video_extract` | BLOCKED | Not approved until Supadata/Bilibili path is validated. | Supadata / Bilibili APIs | Must show transcript/source availability. | External quota/session dependency. |
| `watchlist_manage` | PARTIAL | User state management and watchlist lookup. | Local watchlist state | Not a market-data source. | Can support personalized context, but cannot validate market claims. |
| `wind_query` | BLOCKED | Not approved until Wind terminal/API permission is confirmed. | Wind terminal/API | Permission failures must be `BLOCKED`, not model evidence. | Use only after `connect` passes. |
| `jqdata_query` | PARTIAL | Historical/reference data inside trial window only. | JQData trial | Must mention data range limit. | Current note says trial range is 2025-01-26 to 2026-02-02; not approved for current market claims. |
| `ths_query` | BLOCKED | Not approved until iFinD SDK/token works. | THS token or iFinDPy SDK | Connection failure means blocked. | Needs `THS_TOKEN` or SDK credentials. |
| `emquant_query` | BLOCKED | Not approved until Choice EmQuantAPI SDK/credentials work. | EmQuantAPI SDK + credentials | Connection failure means blocked. | Needs `EM_USERNAME` / `EM_PASSWORD` and SDK. |
| `research_digest` | PARTIAL | Research discovery and cached digest support. | Eastmoney/AkShare + SQLite + optional LLM | Use `_qc`; cache and batch mode must be disclosed. | Good for idea surfacing; not sufficient as sole source for investment conclusion. |
| `research_reports` | PARTIAL | Curated external report link inventory. | Static/curated sources | Must not imply exhaustive or live coverage. | Use as reference list, not factual market data. |
| `sinafinance_fetch` | PARTIAL | Real-time headline awareness only. | Sina Finance 7x24 feed | Headlines require verification before analysis claims. | News feed can support context, not final conclusions alone. |
| `zhihu_fetch` | BLOCKED | Not approved for finance answers by default. | AutoCLI + Chrome login/session | Requires session validation. | Non-core finance capability. |
| `barchart_fetch` | BLOCKED | Not approved until AutoCLI/extension/session validated. | Barchart via AutoCLI | Requires session validation. | US options data, external browser dependency. |

## E2E Gate

Do not run the 20-scenario E2E suite until:

1. `macro_snapshot` remains blocked from model context when core indicators are stale.
2. `stock_analysis` prompts and routing label it as `PARTIAL`.
3. E2E harness records: user query, routed intent, tool called, `_qc.status`, data source, answer limitation, and pass/fail.

Initial E2E should be 3-5 scenarios only, using `market_pulse` as the first Market Context Engine v0.1 source.
