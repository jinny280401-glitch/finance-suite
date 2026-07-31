# 看票分析 RCA

**Date:** 2026-07-30 (Asia/Shanghai)  
**Status:** `FOUND`  
**Window:** Read-only diagnosis  
**Production change:** `NONE`  
**Fix applied:** `NO`
**Implementation authorization:** `GRANTED`  
**Production deployment authorization:** `NOT GRANTED`

## 1. Problem Description

用户从生产站点的“看票分析”页面提交股票名称或代码后，分析未返回报告，页面进入错误状态。

本次故障的已确认分类是：

```text
BACKEND_FAILURE
+
WORKER_LOCAL_DB_POOL_SATURATION
```

当前证据不支持将故障归因于 AkShare、搜索服务、LLM、Prompt、Trust Gate 或 Evidence Manifest。请求在进入这些层之前，已于身份认证依赖的数据库查询处失败。

## 2. Reproduction Steps

### User path

```text
Entry: https://www.touziagent.com/app/stock.html
Page: 看票分析
Button: 开始分析
Input type: 股票代码或名称
Examples shown by page: 比亚迪 / 002594 / 宁德时代
Observed incident input: UNKNOWN (request body is not logged)
Observed stock code: UNKNOWN
```

前端于 `2026-07-30 14:43` 前后可正常加载，并构造：

```http
POST /api/analyze
Content-Type: application/json

{"skill_type":"stock","query":"<user input>"}
```

### Expected

API 应完成认证、用量检查、股票解析、结构化数据与搜索获取、LLM 分析、QC/Trust 处理，并返回带 `result`、`sources`、`kline`、`_qc` 和 `qa_result` 的结构化响应。若运行时失败，应返回明确的降级或服务不可用状态，而不是未解释的通用错误。

### Actual

同一客户端在同一 worker 上连续得到两次 HTTP 500：

```text
2026-07-30 14:43:15  PID 2907242  POST /api/analyze  500
2026-07-30 14:43:55  PID 2907242  POST /api/analyze  500
```

前端会尝试解析 JSON；该 ASGI 500 没有可用的结构化 `detail/message` 时，页面显示通用“分析失败”。

### Error

两次生产栈均终止于：

```text
app/auth.py:get_current_user
  -> _user_from_token
  -> db.query(User).first()
  -> SQLAlchemy QueuePool checkout
  -> QueuePool limit of size 5 overflow 10 reached,
     connection timed out, timeout 30.00
```

`finance-suite.service` 当时仍为 `active`，由 Uvicorn 以 4 workers 运行。因此这不是整个服务不可达，而是 worker 局部退化。

## 3. Root Cause

### Confirmed immediate root cause

生产 worker `PID 2907242` 的 SQLAlchemy QueuePool 已耗尽。FastAPI 在解析 `/api/analyze` 的 `get_current_user` 依赖时无法取得连接，等待 30 秒后抛出 `sqlalchemy.exc.TimeoutError`，由 ASGI 返回 HTTP 500。

只读进程检查显示：

| Worker PID | SQLite DB file descriptors | Threads | Sockets | State |
|---|---:|---:|---:|---|
| 2907239 | 1 | 8 | 7 | not saturated by this measure |
| 2907240 | 1 | 29 | 13 | not saturated by this measure |
| 2907241 | 1 | 18 | 7 | not saturated by this measure |
| 2907242 | 15 | 34 | 24 | degraded / pool ceiling reached |

`15` 正好对应 SQLAlchemy 默认 QueuePool 的 `pool_size=5` 加 `max_overflow=10`。部署代码没有显式覆盖这些参数。文件描述符只能证明该 worker 已打开 15 个 SQLite 连接；真正证明当时“全部不可借用”的证据是同步出现的 QueuePool checkout timeout，不能仅凭 FD 数量推断 checked-out 状态。

这些 SQLite FD 并非一次性同时建立：可见创建时间从 `2026-07-17`、`07-21`、`07-27`、`07-28` 延续到 `07-30`。这与连接池逐步扩张并保持物理连接打开一致，不足以单独证明连接泄漏。

### Root cause chain

```text
POST /api/analyze
  -> request assigned to PID 2907242
  -> FastAPI resolves get_current_user
  -> auth queries SQLite users table
  -> worker-local QueuePool has no available connection
  -> 30-second checkout timeout
  -> unhandled SQLAlchemy TimeoutError
  -> HTTP 500
  -> frontend renders generic analysis failure
```

### Deeper ownership cause

`/api/analyze` 在路由执行前取得 request-scoped `Session`。认证查询是该 Session 的第一个 SQL 操作，会 checkout 一个连接；`get_db()` 只在整个路由退出后的 dependency cleanup 中调用 `db.close()`。因此该连接会跨越后续 potentially long provider/search/LLM awaits 保持在同一请求生命周期内。这一资源边界可由部署代码直接验证。

LLM 调用的单次 timeout 为 180 秒，且退化 worker 当时还存在多个外部 HTTPS 连接和 34 个线程。它们支持“长请求并发会放大池压力”，但当前只读证据不能把每一个网络 socket 或 15 个 checkout 一一绑定到具体 `/api/analyze` 请求，也不能区分所有连接是正常长持有还是异常取消后的泄漏。

当天截至复核时，PID `2907242` 已记录 33 次 QueuePool timeout；其他 worker 仍能返回 `/api/analyze` HTTP 200。这进一步证明故障是持续的 worker-local 资源退化，而非一次性前端或 provider 错误。

因此：

```text
Immediate failure cause: VERIFIED
Worker-local saturation: VERIFIED
Request-scoped DB connection spans long analysis path: VERIFIED BY CODE
Exact owning requests/tasks: NOT YET VERIFIED
Connection leak after dependency cleanup: NOT PROVEN
```

## 4. Affected Layer

| Layer | Status | Evidence |
|---|---|---|
| UI Layer | `OBSERVED / REQUEST SENT` | Page loaded; submit handler sent `POST /api/analyze`; error renderer executed for non-OK response. |
| API Route | `VERIFIED / REACHED` | Production access log recorded two requests to the existing route. |
| Authentication / DB dependency | `FAILED / ROOT CAUSE` | Both stacks failed in `get_current_user` while checking out a DB connection. |
| Business Logic | `NOT REACHED` | Skill validation and usage check occur after dependency resolution. |
| Data Provider | `NOT REACHED` | Stock resolution, AkShare and search tasks begin later in the route. |
| LLM / Analysis Pipeline | `NOT REACHED` | `generate_analysis` occurs after data retrieval. |
| Trust / QC Layer | `NOT REACHED` | QualityGate, report QC and trust contract are downstream of LLM execution. |
| Response Render | `DEGRADED DISPLAY, NOT ROOT CAUSE` | Frontend renders a generic error because the backend 500 is not a structured domain response. |

**Failure Layer:** `Service / Backend Infrastructure`, specifically authentication database connection acquisition.

The page's visible Presentation Truth Guard correctly states that authenticated live evidence is not established. It did not reject these requests and is not the cause of the HTTP 500.

## 5. Recent Change / Regression Check

```text
Regression: YES - runtime behavior is worker-dependent and has degraded
Related Commit: UNKNOWN / NOT PROVEN
```

Evidence:

- The failing service process has been active since `2026-07-17 09:59:55`.
- Deployed `app/routers/api.py` was last modified at `2026-07-17 09:58:16`; `app/auth.py` at `2026-05-06`; `app/database.py` at `2026-03-28`.
- The deployed stock page hash matches repository commit `7eddfc9` (`2026-07-18`), but the deployed backend hashes could not be mapped to a repository commit from the current repository history.
- Trust Layer and Evidence Manifest code is not present in the failing stack and is downstream of the failure.
- Provider integration code is not reached.
- Company Panorama / Research Runtime is not part of this deployed `/api/analyze` failure path.
- The API route exists and received the requests; there is no evidence of a missing or renamed route.

Production source layout (`app/routers/api.py`, `static/app/stock.html`) differs from the current local worktree layout. This is deployment traceability drift and prevents assigning a code-regression commit, but it is not by itself the immediate failure cause.

## 6. Fix Proposal

Implementation Window was authorized after RCA review. A production-targeted patch candidate and isolated validation tests now exist under `patches/kan_piao_db_session_20260730/`. The patch has not been applied to the production runtime because deployment authorization is a separate gate.

### P0-a: Verify and correct DB connection ownership

- Instrument per-worker pool checkout/checkin and request duration.
- Identify which requests own the 15 connections in the degraded worker.
- Split authentication/usage DB work from provider, search and LLM waits so no checked-out DB connection crosses the long external-I/O phase.
- Re-open a short DB scope only when recording final usage, with explicit rollback/close behavior.
- Verify cleanup on timeout, cancellation and exception paths.
- Validate identical behavior across all workers under concurrent stock-analysis requests.

Do not treat increasing `pool_size` or `max_overflow` as the root fix. It may delay recurrence while preserving the ownership defect.

### P0-b: Explicit runtime failure expression

- Convert pool-acquisition failure into an authorized, structured service-degraded response.
- Ensure the frontend distinguishes authentication expiry from backend resource exhaustion.
- Preserve Trust/QC boundaries; do not fabricate empty provider data or mark the response healthy.

Any response-contract change must be separately approved and validated with consumers.

### Validation gate

```text
Authenticated stock request
  -> auth DB checkout succeeds on every worker
  -> provider/search/LLM path executes
  -> QC/Trust response is explicit
  -> DB connections return after success, failure, cancellation and timeout
```

Required proof:

- No QueuePool saturation during defined concurrent load.
- Pool checked-out counts return to baseline after each test class.
- A forced resource failure produces an explicit degraded response, not HTTP 200 empty and not an opaque HTTP 500.
- Golden stock inputs return report, source and QC fields without bypassing Trust Gate.

## 6a. Root Cause Restatement (post Phase 0)

> **本事件不是数据库连接池容量不足，而是资源生命周期设计错误。**

```text
Connection Pool Capacity  ×  Connection Holding Time  =  Failure Risk
```

容量是表象。把 `pool_size` 从 5 改到 50 只会把爆炸时间从 5 个并发慢请求推迟到 50 个，缺陷仍在。真正的缺陷是：

```text
Request Lifetime  ==  DB Connection Lifetime
```

`get_db()` 本身是正确的标准 FastAPI 依赖（`finally: db.close()` 无误）。问题不是**连接没释放**，而是**释放太晚**。

### Code-level confirmation (line-exact, deployed artifact)

Verified against deployed `app/routers/api.py` sha256 `2f78db6f78b85e30…` on 2026-07-30:

| Line | Event | DB connection state |
|---|---|---|
| 700 | `user = Depends(get_current_user)` | checkout (auth query) — **RCA §2 failure point** |
| 701 | `db = Depends(get_db)` | session opened |
| 710 | `check_usage_allowed(db, ...)` | **DB use #1** (milliseconds) |
| 740–997 | AkShare / Tavily / `generate_analysis` (LLM timeout 180s) | **held, zero DB operations** |
| 1093–1099 | `db.add(usage); db.commit()` | **DB use #2** (milliseconds) |
| 1249 | route ends → `get_db()` finally `db.close()` | released |

Actual DB need: two millisecond-scale operations. Actual occupancy: up to 180+ seconds.

### Saturation arithmetic (measured, not assumed)

Pool parameters were read by live introspection inside the production venv (not inferred from defaults):

```text
QueuePool  pool_size=5  max_overflow=10  timeout=30.0  recycle=-1  pre_ping=False
5 + 10 = 15  ==  observed db_fd=15 on PID 2907242
```

`app/database.py` L16 `create_engine(...)` passes only `connect_args`; no pool parameter is overridden. RCA §3's `15 = 5 + 10` premise is therefore **confirmed by measurement**, upgrading it from inference.

---

## 6b. Runtime Principle: Transactional Resource Isolation

**Long-running research tasks must not own transactional resources.**
**长耗时研究任务不得持有事务型资源。**

Extracted from this incident as a binding constraint on all future Provider / Agent expansion. This principle is the durable asset of this RCA; the specific fix is not.

### Rule 1 — Resource acquisition must be scoped by usage, not request lifetime

```text
WRONG                              RIGHT
─────                              ─────
acquire DB                         auth   → acquire → query → release
  auth                             quota  → acquire → check → release
  quota                            research (Provider/Search/LLM)
  Provider / Search / LLM            → NO transactional resource held
  usage write                      usage  → acquire → write → release
release
```

Invariant: `Business Flow Lifetime ≠ Resource Lifetime`.

### Rule 2 — Provider failures must not consume core runtime resources

Gildata / Wind / Choice / iFinD / AkShare / Tavily / LLM all belong to the **External / Slow Boundary**. No transactional resource may be held across that boundary.

```text
DB snapshot → Immutable Context → External Research
```

Never: `DB transaction ──┬── Provider call`

### Rule 3 — Timeout must release resources before returning

Every LLM timeout, Provider timeout, Search timeout, and client cancellation must be proven to reach resource release:

```text
REQUIRED:  Exception → finally → resource release
FORBIDDEN: Exception → HTTP 500 → connection leaked
```

Cancellation paths (`asyncio.CancelledError`) require the same proof as exception paths — this is the case current evidence has **not** closed (see §3 `Connection leak after dependency cleanup: NOT PROVEN`).

### Rule 4 — Pool exhaustion is a Runtime degradation event, not a crash

```text
CURRENT:  QueuePool exhausted → unhandled TimeoutError → opaque HTTP 500
TARGET:   QueuePool exhausted → runtime observes resource pressure
                              → explicit degraded response (503 + Retry-After)
                              → client retry / fallback
```

The frontend must be able to distinguish authentication expiry from backend resource exhaustion. Today it cannot, which is why the user saw only 通用"分析失败".

### Rule 5 — Every long-running capability requires a resource budget

```text
Research Task
  ├── Time Budget
  ├── Memory Budget
  ├── Connection Budget
  └── External API Budget
```

This is the boundary between an Agent Runtime and simple API orchestration. Research Runtime currently declares none of these budgets.

### Governance placement

This principle belongs to Research Runtime governance, not to this incident record. Promotion into `RESEARCH_RUNTIME_PROVIDER_CONSUMPTION_REVIEW.md` requires its own window and is **not** performed by this RCA.

---

## 6c. Phase 0 — Deployment Traceability Lock (2026-07-30)

**Verdict: `PARTIAL` — Runtime Identity established, Source Revision mapping not.**

| Dimension | Status | Evidence |
|---|---|---|
| Running code path | ✅ ESTABLISHED | systemd `WorkingDirectory=/home/ubuntu/finance-suite-web`, `ExecStart=…uvicorn app.main:app --workers 4` |
| Worker topology | ✅ ESTABLISHED | master `2907228`; children `2907239/40/41/42`; `NRestarts=0`; up since 2026-07-17 09:59:55 CST |
| DB pool config | ✅ MEASURED | live introspection in production venv: QueuePool 5/10/30.0 |
| Dependency versions | ✅ ESTABLISHED | SQLAlchemy 2.0.35 / FastAPI 0.115.0 / uvicorn 0.30.0 / starlette 0.38.6 / Python 3.12.3 |
| Deployed artifact identity | ✅ ESTABLISHED | sha256 + mtime + `__pycache__` consistency (see below) |
| **Source revision mapping** | ❌ **NOT ESTABLISHED** | production dir is `NOT_A_GIT_REPO`; 10+ `.bak_*` files indicate repeated manual hotfixes |

```text
2f78db6f78b85e3083efe0582868d5799cf6197075c049c43097888aea127889  2026-07-17T09:58:16  app/routers/api.py
af51165de392e6a42ad8c489bfe5dac9ed611cb451bfe23be07cb0b3042c6ddf  2026-03-28T14:27:15  app/database.py
d5151409431e4384be97ceae29ad968e6b4c041e591233342d8c791d7cf3a804  2026-05-06T22:09:25  app/auth.py
```

**Why PARTIAL and not BLOCKED**: a commit hash is *version-audit* evidence, not *running-entity* evidence — it proves source once existed in a repository, not that it is executing. Direct measurement (sha256 + `__pycache__` mtime consistency + in-venv pool introspection) is the stronger evidence and it is present. The missing commit map degrades rollback convenience and change auditability; it does not weaken the claim "the file being modified is the file being executed."

**Compensating control (sha256-pinned protocol)**: every Phase 1 change records before-hash, `.bak_cc_<ts>` backup, after-hash, and validation result in this document.

## 6d. Phase 1 — Instrumentation status

```text
Instrumentation Artifact:  PREPARED
Runtime Registration:      NOT ACTIVE
Activation Condition:      Service Restart Required
```

The artifact exists on the production filesystem but is **not registered in any running process**. The four workers were started 2026-07-17 09:59:55 CST and continue executing the pre-instrumentation bytecode. Until a restart occurs, this change has zero runtime effect — no event listener is attached, no log line is produced by live traffic.

| Step | Result |
|---|---|
| Backup | `app/database.py.bak_cc_20260730-152848` — sha256 matches pre-change original |
| Change | append-only observability block, `database.py` 87 → 142 lines. No existing line modified. |
| before sha256 | `af51165de392e6a42ad8c489bfe5dac9ed611cb451bfe23be07cb0b3042c6ddf` |
| after sha256 | `d932177900a1f8066ca300e5b4ce13b1dbecba30f50c583930ded4000f32d06e` |
| `py_compile` | PASS |
| Isolated import | PASS (`QueuePool`, `checkedout=0`, log write verified) |
| Full app import | PASS (38 routes) |
| **Runtime activation** | ❌ **PENDING RESTART** — the 4 running workers still execute 2026-07-17 bytecode |

Rollback: `cp app/database.py.bak_cc_20260730-152848 app/database.py` + service restart.

What the instrumentation records per checkout/checkin: `pid`, `tid`, `checkedout`, `size`, `overflow`, and **`held_s`** — the quantity that converts the long-hold hypothesis into measurement. Log path: `logs/pool_instrument.log` (override via `CC_POOL_LOG`).

## 6e. Degraded worker forensic snapshot (PID 2907242)

Captured read-only 2026-07-30T07:32:36Z (15:32:36 CST). No Python-level stack tooling is installed and installing any is out of scope, so this is kernel/`/proc`-level only.

```text
State: S (sleeping)   Threads: 34   VmRSS: 246132 kB
thread wchan distribution:
  22  futex_wait_queue        ← thread-pool workers parked
   9  wait_woken
   1  unix_stream_data_wait
   1  io_sq_thread
   1  ep_poll                 ← event loop
```

SQLite FD open timestamps (the 15 connections):

```text
Jul 17 09:59  ×2   (fd 19, 24)
Jul 21 11:47  ×1   (fd 38)
Jul 21 13:21  ×1   (fd 39)
Jul 27 21:24  ×1   (fd 43)
Jul 28 10:03  ×1   (fd 44)
Jul 28 11:24  ×1   (fd 45)
Jul 28 16:04  ×7   (fd 46–52)   ← burst: overflow expansion under concurrent load
Jul 30 10:07  ×1   (fd 53)      ← final connection, ceiling reached
```

**What this proves**: pool growth was incremental over 13 days, with a 7-connection burst on 07-28 16:04 consistent with overflow expansion under concurrency; the ceiling was reached 07-30 10:07, ~4.5 hours before the observed 14:43 failures.

**What this does not prove**: which requests own the connections. `ptrace_scope=1` and `/proc/<pid>/task/*/stack` returning `Permission denied` block Python frame inspection; `futex_wait_queue` shows threads parked but not what they await. This remains `Exact owning requests: NOT YET VERIFIED` — the gap the instrumentation is designed to close.

---

## 7. Risk Assessment

| Risk | Level | Reason |
|---|---|---|
| Recurrence | `HIGH` | Degraded worker remains active and continues to own the full pool. |
| User impact | `HIGH` | Load balancing makes failure intermittent and worker-dependent. |
| False provider diagnosis | `HIGH` | The visible symptom is missing analysis, while providers are never called. |
| Trust boundary impact | `MEDIUM` | Opaque failure prevents reliable failure-state expression, but Trust/QC itself was not bypassed. |
| Fix blast radius | `MEDIUM-HIGH` | DB session lifetime and error contracts affect authentication and all analysis skills. |
| Commit attribution | `UNKNOWN` | Production backend artifacts are not traceable to a current repository commit. |

## RCA Card

```text
看票分析 RCA
Status: FOUND
Root Cause: Worker-local SQLAlchemy QueuePool saturation causes auth DB checkout timeout
Affected Component: app.auth.get_current_user / SQLAlchemy engine pool / POST /api/analyze dependency resolution
Failure Layer: Service / Backend Infrastructure
Recommended Fix: Verify connection ownership, shorten DB session scope, guarantee cleanup, and add explicit degraded error propagation under a separately authorized implementation window
Need Code Change: YES
Implementation Authorization: GRANTED (Phase 1, scoped)
Instrumentation Patch: WRITTEN TO DISK / IMPORT TESTS PASS / NOT ACTIVE IN RUNTIME
Session-Scope Fix (api.py): NOT WRITTEN
Fix Applied To Production: NO
Restart Authorization: PENDING LOW-TRAFFIC WINDOW
Production Change: NONE (disk write to database.py only; running workers still on 2026-07-17 code)
Trust Gate Bypass: NO
Provider Replacement: NO
```

This incident remains separate from the Shared Gate governance window. No provider capability claim is changed by this RCA.
