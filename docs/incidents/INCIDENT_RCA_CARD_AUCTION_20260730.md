# INCIDENT RCA CARD — Auction Missing

**Date of RCA**: 2026-07-30
**Source of Truth (SOT)**: `/Users/Zhuanz/finance-suite/` (working tree at HEAD `cdac1ca docs(memory): record fusion audit freeze`)
**Scope**: Read-only. No code change. No deploy. No architecture change.

---

## 1. User Symptom

"Auction missing" — user reports that the 集合竞价 (opening auction / market pulse) feature does not return expected data on the production site `https://www.touziagent.com`.

The exact reproduction step (user narrative): opening the auction page → no data displayed, or data area appears blank.

## 2. Frontend Entry

- **Page**: `/app/auction.html` (file path: `/Users/Zhuanz/finance-suite/app/auction.html`, 454 lines, title "集合竞价 — Finance Suite")
- **Auth gate** (lines 11–13 of file):
  ```js
  const isLocalDemo = ['localhost', '127.0.0.1'].includes(location.hostname);
  if (!isLocalDemo && localStorage.getItem('fs_auth') !== 'ok') {
    location.replace('/?redirect=/app/auction.html');
  }
  ```
  Production requires `fs_auth === 'ok'` in `localStorage`. On `touziagent.com` (non-localhost), an unauthenticated visit is redirected to login.
- **Visible behavior**: page renders title + chrome + empty sections when data fetch returns failure/empty/partial.

## 3. API Endpoint

- **Production endpoint**: `https://www.touziagent.com/api/intel/market-context` (per `auction_signal_evidence_v0.1.md` cross-check record)
- **MCP tool name** (internal): `market_pulse` (registered in `mcp_server.py:23` and `mcp_server.py:447`)
- **Endpoint pattern**: Web API path is the actual served route for the HTML page; MCP path is exposed for LLM-tool consumption.

## 4. Backend Route

Two parallel backend implementations exist (drift risk per memory `project_auction_qc_hotfix_20260717.md`):

| Path | File | Owner | Status |
|---|---|---|---|
| Web API path | `/Users/Zhuanz/finance-suite/app/auction_data.py` | server_scripts router (via `intel_api.py`) | **Has 2026-07-17 time-gate + QC hotfix** |
| MCP path | `/Users/Zhuanz/finance-suite/scripts/auction_data.py` | `mcp_server.py:447 market_pulse()` | **Lacks 7/17 hotfix** (per memory: "scripts/auction_data.py 未改为复用 app/auction_data.py") |

`market_pulse()` body (mcp_server.py:447–460):
```python
@mcp.tool()
async def market_pulse() -> str:
    try:
        import auction_data
        data = await auction_data.get_auction_data()
        qc = _qc_auction(data)
        formatted = auction_data.format_auction_data(data)
        return _wrap_response(qc, formatted)
    except Exception as e:
        return _make_error_response(f"market_pulse 异常: {e}")
```

## 5. Provider Dependency

- **Single source**: AkShare (`import akshare as ak`) — explicit comment in `_qc_auction` docstring: "当前 market_pulse 为 AkShare 单源聚合，未做多源降级。"
- **Provider functions called** (per `scripts/auction_data.py:13–80+`):
  - `ak.stock_zt_pool_em(date=date)` — 涨停池
  - `ak.stock_zt_pool_strong_em(date=date)` — 强势股
  - `ak.stock_zt_pool_previous_em(date=date)` — 昨日涨停
  - `ak.stock_changes_em(symbol=...)` — 盘中异动
  - `ak.stock_hot_rank_em()` — 人气排行
  - `ak.stock_hot_up_em()` — 飙升榜
  - `ak.stock_top_gainers_em()` — 涨幅排行
- **No fallback provider**: when AkShare fails, the function returns `None` from each `_fetch_*` helper; aggregation produces empty lists; QC status degrades to `partial` or `failure`.

## 6. Database Dependency

**None.** The auction data path is purely a real-time AkShare → in-memory aggregation. No SQLite, no Postgres, no Redis, no persistent store is touched by `auction_data.py` or `_qc_auction`.

## 7. Last Known Working State

**Working state (good)**:
- **2026-07-17 09:54:30** — auction hotfix deployed (`project_auction_qc_hotfix_20260717.md` CLOSED). Realtime smoke at that time: `phase=morning_session, ready=True, zt_pool=23, gate_reason=None`. Web API path (`app/auction_data.py`) carried the new QC stack.
- **2026-07-24 09:56:51** — signal-validation evidence collected 116 `previous_zt` rows locally. Production cross-check at `touziagent.com/api/intel/market-context` returned `_qc.status=partial`, `source_type=real`, and explicitly **blocked `previous_zt`** — meaning the production path was already in degraded state by then.

**Known regressions / fragility**:
- 2026-05-16 commit `62f3a7a fix(auth): handle 401 in auction/stock pages, add escapeHtml and qc panel` — auction page had a 401-handling bug
- 2026-07-08 (per recent commits): `6c774e0 fix(market-context): make empty data explicit` — empty data was silently producing bad output
- 2026-07-08: `9cdbadb fix: gate auction analysis on validated market data` — gating logic added
- The `codex/auction-time-gate-qc-20260717` branch exists but the **memory entry explicitly notes "scripts/auction_data.py 未改为复用 app/auction_data.py（两份独立实现漂移风险）"** — drift risk remains.

## 8. Root Cause Classification

**Top candidate (most likely)**: `EXTERNAL_PROVIDER_DEGRADED` — AkShare endpoint returning empty/partial data, causing `_qc.status=partial` or `failure`, causing the page to render with empty sections ("missing").

**Secondary candidates (in order)**:
1. `ARCHITECTURE_DRIFT` — two parallel implementations (`app/auction_data.py` vs `scripts/auction_data.py`) where the MCP path (`scripts/`) lacks the 7/17 hotfix that the Web path has. If user is hitting the MCP route, time-gate + QC stack may be missing → bare-data → wrong rendering.
2. `RUNTIME_GATING` — 09:25 time gate (per 7/17 hotfix): if called before 09:25 or after market close, data is explicitly marked invalid and not surfaced. User could be hitting at off-hours.
3. `AUTH_GATE_BLOCKING` — `fs_auth` not in `localStorage`; redirect to login. Symptom would be a redirect rather than empty page, so lower likelihood.
4. `UNKNOWN` — frontend JS error preventing render. Not currently evidenced.

**Most likely root cause (single-line)**:
> AkShare single-source data path returning partial/empty result during market off-hours or provider degradation, with `_qc_auction` correctly downgrading `status` to `partial`/`failure`, causing page to render empty sections that user perceives as "missing".

**Confirmation method (not run per RCA scope)**:
- Inspect `market_pulse` MCP tool response at `https://www.touziagent.com/api/intel/market-context` (or equivalent) and read `qc.status` + `qc.missing_dimensions`.
- Compare against production `datetime.now()` in CST — outside 09:25–15:00 window would explain gating.
- Compare `scripts/auction_data.py` vs `app/auction_data.py` to confirm QC drift.

## Sign-off

| Aspect | Statement |
|---|---|
| Scope | Read-only. No code modified. No deployment attempted. No architecture changes. |
| Evidence basis | File reads, git log, memory recall. |
| Boundary | This RCA surfaces the candidate root cause; confirmation requires live read of the production endpoint, which is outside this RCA scope. |
