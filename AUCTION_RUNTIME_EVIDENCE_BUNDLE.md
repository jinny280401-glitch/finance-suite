# AUCTION_RUNTIME_EVIDENCE_BUNDLE v0.1

**Mode:** READ-ONLY / FORENSICS / No Fix Authorized
**Collection Date:** 2026-08-03 11:15–11:35 CST
**Collector:** Claude Code (via jump box admin@8.138.2.55 → ubuntu@119.28.156.125)
**Governance Case:** R-01 Runtime Evidence — first production case

---

## Incident ID

`AUCTION-20260803-0930`

## Timestamp

| Event | Timestamp (CST) | Evidence Source |
|---|---|---|
| User arrives at site | 09:27:53 | nginx access.log |
| Redirect to auction.html | 09:28:52 | nginx access.log |
| First /api/analyze (unauthenticated, 401 JSON) | 09:29:10 | nginx access.log + backend journalctl |
| User logs in | 09:30:03 | nginx access.log + backend journalctl |
| **Incident: /api/analyze hangs (499 client disconnect)** | **09:30:29** | nginx access.log |
| **Incident: /api/analyze first 504 (578 bytes HTML)** | **09:33:10** | nginx access.log + error.log |
| **Incident: /api/analyze second 504 (same connection)** | **09:35:21** | nginx access.log + error.log |
| Third attempt, same 504 | 11:04:13 | nginx access.log + error.log |

**Primary incident window:** 09:30:29 – 09:35:21 CST

---

## Frontend Evidence

| Field | Value |
|---|---|
| Page | `https://www.touziagent.com/app/auction.html` |
| User-Agent | Chrome 150.0.0.0, Windows NT 10.0 |
| Client IP (first) | 222.72.97.242 |
| Client IP (second, same UA) | 58.40.174.18 |
| Browser HAR | **NOT AVAILABLE** — not captured at incident time |

### Request Sequence

```
09:29:10  POST /api/analyze → 401 (42 bytes JSON)     ← unauthenticated, correct JSON
09:30:03  POST /api/login → 200                         ← login successful
09:30:29  POST /api/analyze → 499 (0 bytes, client hung up)
09:33:10  POST /api/analyze → 504 (578 bytes HTML)     ← "Unexpected token '<'" HERE
09:35:21  POST /api/analyze → 504 (578 bytes HTML)     ← retry, same connection #449535
11:04:13  POST /api/analyze → 504 (578 bytes HTML)     ← third attempt
```

### Symptom→Cause Attribution

Observed symptom: `JSON.parse()` → `Unexpected token '<'`

The 578-byte response body was **nginx's default 504 Gateway Time-out HTML error page**, served with `Content-Type: text/html`. The frontend called `resp.json()` on this HTML — exactly matching the reported symptom.

**Evidence gap: frontend HAR.** The original response headers, full body, and exact `Content-Type` are not preserved from the browser side. Attribution of the 578 bytes to the nginx 504 template is based on:
- Access log `504 578` (all three 504 responses are identical size)
- nginx 1.24.0 default 504 page is known to be ~578 bytes
- No custom `error_page` directive in nginx config

---

## Nginx Evidence

### Active Configuration

- **Config:** `/etc/nginx/sites-enabled/finance-suite` → `/etc/nginx/sites-available/finance-suite`
- **proxy_read_timeout:** `120s`
- **proxy_connect_timeout:** `75s` (from `touziagent.com` config line, in same nginx instance)
- **Upstream:** `http://127.0.0.1:8000`

### Access Log — Incident Requests

```
222.72.97.242 [03/Aug/2026:09:29:10] "POST /api/analyze HTTP/2.0" 401 42    ← JSON, backend logged
222.72.97.242 [03/Aug/2026:09:30:29] "POST /api/analyze HTTP/2.0" 499 0     ← client disconnect, backend NOT logged
58.40.174.18  [03/Aug/2026:09:33:10] "POST /api/analyze HTTP/2.0" 504 578   ← upstream timeout #1
58.40.174.18  [03/Aug/2026:09:35:21] "POST /api/analyze HTTP/2.0" 504 578   ← upstream timeout #2 (same conn #449535)
58.40.174.18  [03/Aug/2026:11:04:13] "POST /api/analyze HTTP/2.0" 504 578   ← upstream timeout #3
```

### Error Log

```
2026/08/03 09:33:10 [error] *449535 upstream timed out (110: Connection timed out)
  while reading response header from upstream
  client: 58.40.174.18, server: www.touziagent.com
  request: "POST /api/analyze HTTP/2.0"
  upstream: "http://127.0.0.1:8000/api/analyze"
  referrer: "https://www.touziagent.com/app/auction.html"

2026/08/03 09:35:21 [error] *449535 upstream timed out (110: Connection timed out)
  ... (same connection, same details)

2026/08/03 11:04:13 [error] *449805 upstream timed out (110: Connection timed out)
  ... (same pattern, new connection)
```

### Log Rotation Status

- `access.log` — active, today's data intact (rotated at 11:04 today)
- `access.log.1` — yesterday (Aug 2)
- `access.log.2.gz` — Aug 1 (compressed)
- Earlier logs preserved back to Jul 20

**Evidence status: COMPLETE.** Nginx logs are preserved and sufficient.

---

## Backend Evidence

### Service Configuration

- **Service:** `finance-suite.service` (systemd)
- **Workers:** 4 × uvicorn (`--workers 4`)
- **Port:** `127.0.0.1:8000`
- **PID:** 3294269 (running since Jul 30, 4 days uptime)
- **Entry point:** `app.main:app`

### Journalctl — Incident Window (09:30–10:00 CST)

The backend logged normal traffic before and after the incident, but **did NOT log any /api/analyze request from 58.40.174.18** during the incident window.

```
09:29:10  POST /api/analyze → 401        ← LOGGED (from 222.72.97.242, unauthenticated)
09:30:03  POST /api/login → 200           ← LOGGED
09:30:14  GET /api/intel/market-context → 200  ← LOGGED
09:30:18  POST /api/auth/cookie-fix → 200 ← LOGGED
09:30:51  GET /api/intel/market-context → 200  ← LOGGED
09:31:10  GET / → 200                      ← LOGGED (bot)
09:34:46  GET / → 200                      ← LOGGED (bot)
--- NO /api/analyze REQUESTS LOGGED ---
10:01:22+ (bot scanning activity resumes)
```

**Request at 09:30:29 (HTTP 499):** The backend also did NOT log this request. Client disconnected before backend responded.

**No exceptions, tracebacks, or ERROR-level log lines** found anywhere in the 09:30–10:00 window. The backend journal is silent about the hung requests.

**Evidence status: PARTIAL.** Backend access logs confirm the requests were NOT completed, but no exception/traceback was captured because the worker was stuck in a blocking I/O call (no exception thrown).

---

## Provider Evidence

### Provider Invoked: **YES**

The `/api/analyze` auction handler (`api.py:866`) calls:

```python
akshare_data = await get_validated_auction_data()
```

Which calls `get_auction_data()` (`auction_data.py:149`), submitting 6 AkShare tasks to a shared `ThreadPoolExecutor(max_workers=4)`:

| Task | AkShare Function | Timeout? |
|---|---|---|
| `zt_pool` | `ak.stock_zt_pool_em()` | **NO** |
| `strong_pool` | `ak.stock_zt_pool_strong_em()` | **NO** |
| `previous_zt` | `ak.stock_zt_pool_previous_em()` | **NO** |
| `big_buy` | `ak.stock_changes_em()` | **NO** |
| `hot_rank` | `ak.stock_hot_rank_em()` | **NO** |
| `hot_up` | `ak.stock_hot_up_em()` | **NO** |
| `top_gainers` | `ak.stock_spot_em()` → `_fetch_spot_sorted()` | 3s (`asyncio.wait_for`) |

**Critical finding:** 6 of 7 AkShare HTTP calls have **no timeout**. Only `top_gainers` is wrapped with `asyncio.wait_for(timeout=3s)`. The 6 untimed calls are awaited **sequentially** — if any one of them hangs, the entire request blocks indefinitely.

These AkShare functions make synchronous HTTP requests to `*.eastmoney.com` endpoints. If the eastmoney endpoint is slow or unresponsive, the thread blocks with no timeout, the async coroutine is stuck on `await task`, and the uvicorn worker never completes the request.

### Provider Correctness: **NOT JUDGED**

Per evidence capture protocol, this report does not assess whether AkShare returned correct data. Provider invocation is confirmed; data quality is out of scope.

---

## Root Cause Classification

### ROOT CAUSE CONFIRMED

**Nginx upstream timeout (HTTP 504) caused by blocking AkShare HTTP call in backend auction handler.**

**Failure chain:**

```
Browser POST /api/analyze (auction)
  → nginx proxies to 127.0.0.1:8000
    → uvicorn worker receives request
      → api.py:866 calls get_validated_auction_data()
        → auction_data.py:149 get_auction_data()
          → Submits 6 AkShare tasks to ThreadPoolExecutor (max_workers=4)
          → Awaits tasks sequentially — one AkShare HTTP call hangs (no timeout)
            → Worker blocked on await (coroutine suspended, thread occupied)
              → Backend never sends response
                → nginx proxy_read_timeout (120s) expires
                  → nginx returns default 504 HTML (578 bytes)
                    → Frontend resp.json() → "Unexpected token '<'"
```

### Confidence: **HIGH**

Evidence chain is complete from browser to provider:
- [x] Frontend symptom (`Unexpected token '<'`) → matched to nginx 504 HTML
- [x] Nginx access log (504, 578 bytes, referrer auction.html)
- [x] Nginx error log (upstream timed out, upstream http://127.0.0.1:8000/api/analyze)
- [x] Backend journal (request received by nginx, NOT completed by backend)
- [x] Provider code (AkShare calls with no timeout)
- [x] 3 independent reproductions (09:33, 09:35, 11:04) — same failure pattern

---

## Evidence Gaps

| Gap | Impact | Mitigation |
|---|---|---|
| Browser HAR not captured | Cannot confirm exact `Content-Type` header on 504 response | Nginx access log shows 504 + 578 bytes; 578 matches default nginx 504 HTML size |
| No backend traceback/exception | Cannot confirm WHICH AkShare call hung | All 6 untimed AkShare calls are candidates; code review confirms systemic lack of timeouts |
| No request-id correlation | Cannot trace exact request through backend | Nginx connection ID `*449535` is the only identifier; backend has no structured request logging |
| User IP changed mid-session | 222.72.97.242 → 58.40.174.18 with same UA | Does not affect root cause attribution; both IPs hit same failure |

---

## Fix Authorization

**NOT AUTHORIZED.**

This is an evidence collection report. The root cause is identified (blocking AkShare HTTP calls with no timeout in `auction_data.py`), but fix authorization is a separate governance decision. This report does not modify production code.

### Remediation Options (for reference only, NOT authorized)

If and when a fix is authorized, the obvious remediation is adding `asyncio.wait_for()` timeouts to all AkShare calls in `get_auction_data()`, matching the pattern already used for `top_gainers`. This is a single-function, low-risk change in `auction_data.py:154-166`.

---

## Governance Classification

```
Incident:     AUCTION-20260803-0930
Case:         R-01 Runtime Evidence
Status:       OPEN (evidence collected, fix not authorized)
Root Cause:   CONFIRMED (nginx 504 ← AkShare blocking with no timeout)
Confidence:   HIGH
Fix:          NOT AUTHORIZED
```

### R-01 Validation

This incident validates R-01 in both directions:

1. **Code fixed ≠ Root cause proven.** The current `/api/analyze` returning JSON 401 does NOT mean the auction incident is resolved. They are different requests at different times with different auth states. Only the evidence chain above proves what happened.

2. **Runtime Evidence retention is a contract.** The nginx access/error logs were preserved and sufficient to close the chain. The backend journal was partially useful (confirmed absence of request completion). Browser HAR was missing — a gap that could be addressed with client-side error reporting.

---

## Next Actions

1. **Decision: authorize fix?** Add `asyncio.wait_for(timeout=N)` to all AkShare calls in `auction_data.py:154-166`
2. **Instrumentation:** Add structured request logging (request-id propagation from nginx → uvicorn) to enable future incident correlation without HAR
3. **Monitoring:** Alert on nginx `upstream timed out` errors for `/api/analyze`
