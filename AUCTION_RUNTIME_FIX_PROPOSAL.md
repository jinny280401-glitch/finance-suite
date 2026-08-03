# AUCTION_RUNTIME_FIX_PROPOSAL v0.2

**Status:** PROPOSAL / NOT AUTHORIZED FOR IMPLEMENTATION
**Date:** 2026-08-03 (v0.1), revised 2026-08-03 (v0.2 after AkShare patchability verification)
**Author:** Claude Code (forensic analysis)
**Precedes:** Fix Authorization → Implementation → Validation
**Changelog v0.2:** Replaced `socket.setdefaulttimeout()` with scoped `requests.get/post` monkey-patch after verifying all 7 AkShare functions use module-level `requests` calls (no `Session` objects, no `from requests import`). Added explicit Layer 1 vs Layer 2 hierarchy.

---

## 1. Blocking Boundary Identification

### Call Chain Trace

```
auction_data.py:155  loop.run_in_executor(_executor, _fetch_zt_pool, None)
  → auction_data.py:52   _fetch_zt_pool()
    → ak.stock_zt_pool_em(date)
      → requests.get("https://push2ex.eastmoney.com/getTopicZTPool", params=..., timeout=NOT SET)
        → urllib3.HTTPConnectionPool.urlopen()
          → socket.settimeout(None)   ← blocks indefinitely
            → sock.recv()              ← C-level blocking I/O, uninterruptible from Python
```

### Confirmed: All 7 Auction Data Functions Have No Timeout

| auction_data wrapper | AkShare function | HTTP call | timeout= |
|---|---|---|---|
| `_fetch_zt_pool()` | `stock_zt_pool_em()` | `requests.get(url, params=params)` | **NONE** |
| `_fetch_strong_pool()` | `stock_zt_pool_strong_em()` | `requests.get(url, params=params)` | **NONE** |
| `_fetch_previous_zt()` | `stock_zt_pool_previous_em()` | `requests.get(url, params=params)` | **NONE** |
| `_fetch_changes()` | `stock_changes_em()` | `requests.get(url, params=params)` | **NONE** |
| `_fetch_hot_rank()` | `stock_hot_rank_em()` | `requests.post(url, json=payload)` | **NONE** |
| `_fetch_hot_up()` | `stock_hot_up_em()` | `requests.post(url, json=payload)` | **NONE** |
| `_fetch_spot_sorted()` | `stock_zh_a_spot_em()` → `fetch_paginated_data()` → `request_with_retry()` | `session.get(url, params=params, timeout=15)` | **15s ✅** |

### Key Finding: 6 of 7 Are Patchable

`stock_zh_a_spot_em` (used by `top_gainers`) already has HTTP-level timeout via `request_with_retry(url, params=params, timeout=15)`. It's the other 6 functions that lack any timeout.

All 6 problematic functions use `requests.get()` or `requests.post()` at module level — **not** `from requests import get` (which would capture at import time) and **not** `Session.get()` (which would bypass a module-level patch). This means a monkey-patch on `requests.get` / `requests.post` **will** affect AkShare's internal calls, because the name `requests` is resolved at call time.

```
Verified for each of the 6 functions:
  stock_zt_pool_em:         requests.get(url, params=params)  ← patchable
  stock_zt_pool_strong_em:  requests.get(url, params=params)  ← patchable
  stock_zt_pool_previous_em: requests.get(url, params=params) ← patchable
  stock_changes_em:         requests.get(url, params=params)  ← patchable
  stock_hot_rank_em:        requests.post(url, json=payload)  ← patchable
  stock_hot_up_em:          requests.post(url, json=payload)  ← patchable
  stock_zh_a_spot_em:       request_with_retry(..., timeout=15) ← already has timeout ✅
```

**Root blocking point:** Python `requests` library called without `timeout=` parameter → `socket.settimeout(None)` → C-level `recv()` blocks indefinitely. AkShare's own `request_with_retry` helper already passes `timeout=15` — the 6 functions that don't use it are the gap.

---

## 2. Why `asyncio.wait_for` Alone Is Insufficient

### Current top_gainers pattern (the "obvious" fix):

```python
top_gainers_task = loop.run_in_executor(_executor, _fetch_spot_sorted)
results["top_gainers"] = await asyncio.wait_for(
    top_gainers_task,
    timeout=_TOP_GAINERS_TIMEOUT_SECONDS,  # default 3s
)
```

### What happens when timeout fires:

```
asyncio.wait_for raises TimeoutError
  → coroutine resumes, exception caught → results["top_gainers"] = None
  → BUT: the thread inside _executor is STILL blocked in requests.get()
  → thread continues running socket.recv() until OS TCP timeout (~2-15 min)
  → thread slot in _executor is LEAKED for the duration
```

### Thread Pool Exhaustion Scenario

Given `_executor = ThreadPoolExecutor(max_workers=4)` shared across ALL requests:

```
Request 1: 4 AkShare calls hang → 4 threads stuck
Request 2: submits new tasks → executor queue full → wait forever
   → uvicorn worker blocked on await → nginx 504 AGAIN
```

The sequential await pattern in `get_auction_data()` (line 163: `for key, task in tasks.items(): results[key] = await task`) means a single request can occupy up to 6 thread-seconds sequentially, but if each call hangs, it burns threads permanently.

### Summary

| Layer | `asyncio.wait_for` effect | Thread freed? |
|---|---|---|
| Coroutine | `TimeoutError` raised, execution resumes | NO |
| asyncio Future | Cancelled (Python can't cancel running thread) | NO |
| Thread in executor | Still blocked in `socket.recv()` | NO |
| HTTP request | Still in-flight until OS TCP timeout | NO |

**`asyncio.wait_for` prevents the COROUTINE from hanging, but does NOT prevent thread pool exhaustion.**

---

## 3. Timeout Strategy Selection

### Verification: AkShare Calls Are Patchable

Before evaluating strategies, we verified that all 6 problematic AkShare functions use `requests.get()` / `requests.post()` resolved at **call time** (module-level name `requests`, not `from requests import get` which would capture at import time). None use `Session` objects internally. This means monkey-patching `requests.get` and `requests.post` WILL affect AkShare's internal HTTP calls.

```
Evidence from source inspection:
  stock_zt_pool_em:         import requests; ... requests.get(url, params=params)
  stock_zt_pool_strong_em:  import requests; ... requests.get(url, params=params)
  stock_zt_pool_previous_em: import requests; ... requests.get(url, params=params)
  stock_changes_em:         import requests; ... requests.get(url, params=params)
  stock_hot_rank_em:        import requests; ... requests.post(url, json=payload)
  stock_hot_up_em:          import requests; ... requests.post(url, json=payload)

All: no Session objects, no from-imports, no HTTPAdapter, no global timeout config.
```

### Option A (RECOMMENDED): Monkey-patch `requests.get/post` with Default Timeout

```python
import requests

_DEFAULT_TIMEOUT = (3, 15)  # (connect_timeout, read_timeout)

_original_get = requests.get
_original_post = requests.post

def _get(url, **kwargs):
    kwargs.setdefault('timeout', _DEFAULT_TIMEOUT)
    return _original_get(url, **kwargs)

def _post(url, **kwargs):
    kwargs.setdefault('timeout', _DEFAULT_TIMEOUT)
    return _original_post(url, **kwargs)

requests.get = _get
requests.post = _post
```

| Aspect | Assessment |
|---|---|
| Effectiveness | ✅ `requests` passes timeout to urllib3 → `socket.settimeout(15)` → `recv()` actually interrupted → thread freed |
| Scoping | ⚠️ Process-global for `requests.get/post`, but **only applies when caller omits `timeout=`** — existing calls with explicit timeout are unaffected |
| Side effects | Other endpoints' `requests.get/post()` calls without timeout also get 15s default — **this is a safety improvement**, not a regression |
| Reversibility | `requests.get = _original_get; requests.post = _original_post` |
| Conflict risk | Low — no other module in finance-suite is known to monkey-patch `requests` |
| Tuple timeout | `(3, 15)` = 3s connect + 15s read, gives faster failure on DNS/TCP issues vs single-value |

### Option B: `socket.setdefaulttimeout()` — Global Socket Timeout

```python
import socket
socket.setdefaulttimeout(15)
```

| Aspect | Assessment |
|---|---|
| Effectiveness | ✅ Same as Option A |
| Scope | ❌ **Process-global for ALL socket operations** — affects DNS lookups, database connections, any third-party library that opens sockets |
| Risk | Harder to debug (unexpected `socket.timeout` in unrelated code); timeout source not obvious from traceback |
| Verdict | **Fallback only** if Option A is insufficient |

### Option C: `asyncio.wait_for` Alone (REJECTED)

Per §2 analysis: `asyncio.wait_for` only cancels the coroutine's wait, does NOT free the thread. Thread pool exhaustion risk remains.

### Option D: Replace `_fetch_*()` with Direct `requests` Calls (REJECTED)

Duplicates AkShare's DataFrame parsing logic. Maintenance burden on every AkShare upgrade.

### Decision: **Option A + Concurrent Execution (Two-Layer Defense)**

```
┌─────────────────────────────────────────────────────┐
│ Layer 1: PREVENT INFINITE BLOCKING (root cause)     │
│ requests.get/post monkey-patch → timeout=(3, 15)    │
│ → socket actually interrupted → thread freed        │
├─────────────────────────────────────────────────────┤
│ Layer 2: PREVENT SLOW AGGREGATE (safety net)        │
│ asyncio.wait_for(18s) + asyncio.gather              │
│ → coroutine returns controlled JSON even if Layer 1 │
│   somehow bypassed                                  │
└─────────────────────────────────────────────────────┘
```

**Layer 1 is the fix. Layer 2 is the safety net.** This distinction must be preserved in code comments — future maintainers should not see `asyncio.wait_for` and assume the problem is solved. The `requests` monkey-patch is what actually prevents thread blocking.

---

## 4. Proposed Change

### File: `/home/ubuntu/finance-suite-web/app/auction_data.py`

### Change 1: Add `requests.get/post` monkey-patch with default timeout (after imports)

**Location:** After line 16 (`import akshare as ak`), insert:

```python
import requests

# ── Timeout enforcement for AkShare HTTP calls ──────────────────────────
# AkShare's stock_zt_pool_em / stock_zt_pool_strong_em / stock_changes_em /
# stock_hot_rank_em / stock_hot_up_em all call requests.get/post() WITHOUT
# a timeout= parameter. In Python requests, this defaults to blocking
# indefinitely (socket.settimeout(None)), which means one slow eastmoney
# endpoint can permanently occupy a ThreadPoolExecutor thread.
#
# We patch requests.get and requests.post to inject a default timeout of
# (connect=3s, read=15s) when the caller omits the timeout argument.
# Calls that already pass an explicit timeout= are unaffected.
#
# This is Layer 1 (root cause). Layer 2 (safety net) is the asyncio.wait_for
# in get_auction_data() — see there for the two-layer design rationale.

_DEFAULT_AKSHARE_TIMEOUT = (3, 15)  # (connect_timeout, read_timeout)

_original_requests_get = requests.get
_original_requests_post = requests.post


def _requests_get_with_timeout(url, **kwargs):
    kwargs.setdefault("timeout", _DEFAULT_AKSHARE_TIMEOUT)
    return _original_requests_get(url, **kwargs)


def _requests_post_with_timeout(url, **kwargs):
    kwargs.setdefault("timeout", _DEFAULT_AKSHARE_TIMEOUT)
    return _original_requests_post(url, **kwargs)


requests.get = _requests_get_with_timeout
requests.post = _requests_post_with_timeout
```

**Trade-off acknowledged:** This patch affects ALL `requests.get/post()` calls in the uvicorn worker, not just AkShare's. However:
- It only adds a default — any call that already passes `timeout=` is unaffected
- No HTTP call in a web server should block indefinitely, so this is a safety improvement for the entire worker
- It's narrower than `socket.setdefaulttimeout()` (affects only `requests`, not raw sockets, DNS, or database connections)

### Change 2: Add `asyncio.wait_for` to 6 untimed tasks + concurrent execution (Layer 2)

**Current code** (`auction_data.py:149-166`):

```python
async def get_auction_data(include_top_gainers: bool = True) -> dict:
    """并发获取集合竞价相关全部数据"""
    requested_at = datetime.now(_SHANGHAI_TZ)
    loop = asyncio.get_event_loop()

    tasks = {
        "zt_pool": loop.run_in_executor(_executor, _fetch_zt_pool, None),
        "strong_pool": loop.run_in_executor(_executor, _fetch_strong_pool, None),
        "previous_zt": loop.run_in_executor(_executor, _fetch_previous_zt, None),
        "big_buy": loop.run_in_executor(_executor, _fetch_changes, "大笔买入"),
        "hot_rank": loop.run_in_executor(_executor, _fetch_hot_rank),
        "hot_up": loop.run_in_executor(_executor, _fetch_hot_up),
    }

    results = {}
    for key, task in tasks.items():
        try:
            results[key] = await task
        except Exception:
            results[key] = None
```

**Proposed code:**

```python
# ── Layer 2: asyncio-level safety net ──────────────────────────────────
# Layer 1 (requests monkey-patch above) prevents threads from blocking
# forever by injecting timeout=(3,15) into every AkShare HTTP call.
# Layer 2 bounds the COROUTINE's total wait time. Under normal operation
# Layer 1 fires first and Layer 2 never triggers — this is a safety net
# for any edge case where Layer 1 is somehow bypassed.
#
# Per-task timeout: read_timeout (15s) + connect_timeout (3s) + buffer (3s) = 21s.
# Round up to 25s for margin. With 7 tasks running concurrently on 4 threads,
# worst-case wall time = ceil(7/4) × 25s ≈ 50s — well within nginx's 120s.
_TASK_TIMEOUT = 25


async def get_auction_data(include_top_gainers: bool = True) -> dict:
    """并发获取集合竞价相关全部数据 — 每个调用受 Layer 1 (HTTP timeout) + Layer 2 (asyncio timeout) 双重保护"""
    requested_at = datetime.now(_SHANGHAI_TZ)
    loop = asyncio.get_event_loop()

    tasks = {
        "zt_pool": loop.run_in_executor(_executor, _fetch_zt_pool, None),
        "strong_pool": loop.run_in_executor(_executor, _fetch_strong_pool, None),
        "previous_zt": loop.run_in_executor(_executor, _fetch_previous_zt, None),
        "big_buy": loop.run_in_executor(_executor, _fetch_changes, "大笔买入"),
        "hot_rank": loop.run_in_executor(_executor, _fetch_hot_rank),
        "hot_up": loop.run_in_executor(_executor, _fetch_hot_up),
    }

    # Execute all tasks concurrently, each bounded by timeout.
    # asyncio.gather with return_exceptions=True ensures one task's
    # timeout doesn't cancel the others.
    task_names = list(tasks.keys())
    task_futures = [
        asyncio.wait_for(tasks[name], timeout=_TASK_TIMEOUT)
        for name in task_names
    ]
    gathered = await asyncio.gather(*task_futures, return_exceptions=True)

    results = {}
    for name, outcome in zip(task_names, gathered):
        if isinstance(outcome, Exception):
            results[name] = None
            results[f"{name}_error"] = f"{type(outcome).__name__}: {outcome}"
        else:
            results[name] = outcome
```

### Change 3: Keep existing `top_gainers` timeout, harmonize naming

`top_gainers` already uses `asyncio.wait_for(timeout=3s)` via `_TOP_GAINERS_TIMEOUT_SECONDS`. With the `requests` monkey-patch from Change 1, the underlying `request_with_retry(url, ..., timeout=15)` also has HTTP-level protection (already had it — this function was the one that already used timeout).

Minor alignment: use the same error key pattern as Change 2:
```python
# Current: results["top_gainers_error"] = f"timeout_{...}"
# Keep this key name — the formatter reads it. Pattern is already
# consistent with the new {name}_error convention.
```

### Summary of Changes

| File | Change | Lines affected |
|---|---|---|
| `auction_data.py` | Add `requests.get/post` monkey-patch (Layer 1) | +24 (after imports) |
| `auction_data.py` | Replace sequential `for` with `asyncio.gather` + `wait_for` (Layer 2) | ~25 lines (149-166 + _TASK_TIMEOUT) |

**Zero changes to:** `api.py`, `skills.py`, nginx config, frontend, systemd, or any other file.

---

## 5. Resource Leak Risk Assessment

### Thread Pool Starvation: MITIGATED

**Before fix:** Thread stuck in `socket.recv()` forever → thread leaked until OS TCP timeout (~2-15 min).

**After fix (Layer 1):** `requests.get(url, params=params, timeout=(3,15))` → urllib3 sets `socket.settimeout(15)` → `socket.timeout` raised after 15s read → `_fetch_*()` `except Exception: pass` catches → thread freed and returned to pool.

**After fix (Layer 2, belt-and-suspenders):** If Layer 1 somehow bypassed → `asyncio.wait_for(task, timeout=25)` raises `TimeoutError` → coroutine moves on. Thread still leaks in this edge case, but the coroutine doesn't hang. Thread eventually freed by OS-level TCP timeout.

Worst case with Layer 1 working: all 4 threads busy for 15s each. With `asyncio.gather` executing 7 tasks concurrently, max wall time = ceil(7/4) × 15s ≈ 30s. Well within 120s nginx `proxy_read_timeout`.

### Side Effects of `requests.get/post` Monkey-Patch: ACCEPTABLE

Other endpoints in the same worker that call `requests.get/post()` without `timeout=` will also get the `(3, 15)` default. Analysis:
- **If they already pass `timeout=`:** No effect (`kwargs.setdefault` is a no-op)
- **If they don't pass `timeout=`:** Previously they could block indefinitely; now they can't. This is a safety improvement — no HTTP call in a web server should block forever.
- **If they expect very long responses (>15s):** The `timeout` tuple is `(connect=3, read=15)` — the read timeout resets between chunks of a streaming response, so long-running SSE/streaming endpoints are NOT affected as long as data keeps arriving.
- **Traceability:** Any `requests.ReadTimeout` exception's traceback will clearly show `_requests_get_with_timeout` in the call chain, making it debuggable.

---

## 6. Regression Acceptance Test

### TC-RUNTIME-AUCTION-001: Provider Call Hangs (Layer 1 verification)

```
Given:  push2ex.eastmoney.com is unreachable (simulated via /etc/hosts 127.0.0.1)
When:   POST /api/analyze {"skill_type":"auction","query":"2026-08-03"}
Then:
  - Response arrives within 25s (not 120s)
  - requests.ReadTimeout raised by _requests_get_with_timeout (visible in traceback)
  - _fetch_*() except block catches → returns None
  - Thread freed back to _executor pool (verify: thread count before == after)
  - HTTP status is 200 (backend returns controlled JSON)
  - Content-Type is application/json
  - Response body contains _qc with status="partial" or "failure"
  - No "Unexpected token '<'" on frontend
  - No nginx 504 in error.log
  - Backend journalctl shows the /api/analyze request completed (not missing)
```

### TC-RUNTIME-AUCTION-002: Normal Operation (All Providers Up)

```
Given:  All eastmoney endpoints responding normally
When:   POST /api/analyze {"skill_type":"auction","query":"2026-08-03"}
Then:
  - Response arrives within 10s (typical 2-5s for AkShare)
  - _qc.auction_results_ready is true (during market hours)
  - All 7 data dimensions present (zt_pool, strong_pool, previous_zt, big_buy, hot_rank,
    hot_up, top_gainers)
  - No regression in data quality vs pre-fix
```

### TC-RUNTIME-AUCTION-003: Partial Failure (One Endpoint Slow, Layer 2 verification)

```
Given:  One eastmoney endpoint (e.g. push2ex) responds slowly (connect OK, read hangs > 25s
        despite Layer 1 — edge case simulation)
When:   POST /api/analyze {"skill_type":"auction","query":"2026-08-03"}
Then:
  - Response arrives within 30s
  - Failed dimension has {name}_error field with "TimeoutError" indicator (Layer 2 fired)
  - Other 6 dimensions have valid data (asyncio.gather return_exceptions=True worked)
  - HTTP status is 200
  - No worker thread permanently stuck (OS TCP timeout eventually frees it)
```

### TC-RUNTIME-AUCTION-004: Thread Pool Not Exhausted

```
Given:  10 concurrent auction requests, at least 1 eastmoney endpoint slow
When:   All 10 complete
Then:
  - All 10 return controlled JSON (200, not 504)
  - _executor._threads count never exceeds 4 (no thread leak)
  - No nginx upstream timeout errors
```

---

## 7. Rollback Plan

```bash
# Restore auction_data.py from backup
ssh -J admin@8.138.2.55 ubuntu@119.28.156.125 \
  "cp /home/ubuntu/finance-suite-web/app/auction_data.py.bak_codex_<ts> \
      /home/ubuntu/finance-suite-web/app/auction_data.py && \
   sudo systemctl restart finance-suite"

# Verify
curl -s -o /dev/null -w '%{http_code}' \
  https://www.touziagent.com/api/health
# Expect: 200
```

---

## Fix Authorization Status

```
Auction P0 Fix Proposal v0.2
Root Blocking Cause:     IDENTIFIED (high confidence)
                         → requests.get/post() without timeout= in 6 AkShare functions
Implementation Approach: SPECIFIED
                         → Layer 1: requests monkey-patch (timeout injection)
                         → Layer 2: asyncio.wait_for + gather (safety net)
Change Scope:            APPROVED (auction_data.py only)
Validation:              REQUIRED (TC-RUNTIME-AUCTION-001 through 004)
Production Deployment:   NOT AUTHORIZED
```

This proposal describes what to change, why, and how to verify. Implementation requires explicit authorization. No production code has been modified.
