# Auction Signal Runtime Capability Verification

**Status:** P0 CLOSED — Capability Assumption vs Production Reality; regression NOT PROVEN  
**Date:** 2026-07-31  
**Scope:** 集合竞价 09:25-09:30 生产运行能力与历史证据边界核验

**Authoritative P0 record:** `docs/incidents/AUCTION_HISTORICAL_PRODUCTION_SUCCESS_VERIFICATION.md`

> Current evidence does not prove a production regression. The observed
> difference may represent a mismatch between local capability and production
> runtime capability. Local success is not production capability evidence.

Current classification:

```text
Historical Production Success:          NOT PROVEN
Regression:                              NOT PROVEN
Production Capability at 09:25-09:30:   NOT ESTABLISHED
P0 Historical Verification:              CLOSED
Trigger Audit:                           NOT STARTED under the P0 decision
H4 Gate Analysis:                        BLOCKED
Provider Analysis:                       NOT ENTERED
Production Changes:                      NONE
```

**Authoritative boundary:** Only the P0 record and the classification above are current conclusions. Sections describing H1/H4, trigger drift, code-path differences, or gate behavior are retained as pre-P0 investigation notes and are non-authoritative. They do not establish a root cause and do not authorize further investigation or repair.

The production host is now readable through `ProxyJump=admin@8.138.2.55`. This access-path correction does not change the P0 verdict: the retained service journal contains one qualifying `/api/intel/market-context` HTTP 200 request at `2026-07-10T09:28:47+08:00`, but no retained response body or attributable artifact proves non-empty auction signal content.

---

## Executive Summary

**Core Finding:** P0 只读核验没有找到能够同时绑定生产来源、09:25-09:30 时间窗口和有效集合竞价信号内容的历史证据。因此，当前不能把现象分类为已证明的生产回归，也不能把本地脚本成功升级为生产运行能力。

生产日志中发现 2026-07-10 09:28:47 的 `/api/intel/market-context` HTTP 200 请求，但没有保留响应正文或可归属的竞价信号产物。该记录只能证明生产请求发生和 API 返回 200，不能证明有效 auction signal 曾经生成。

以下变化点与假设保留为**早期调查记录**，不构成已授权的 Trigger Audit、H4 Gate Analysis 或根因结论。P0 为 `NOT FOUND` 后，本文件不得据此继续自动展开这些调查。

**确认的变化 (2026-07-17 前后):**

1. **Trigger 观测 (H1 — 当前状态 CONFIRMED / 漂移 NOT PROVEN):** 唯一活跃的本地 launchd 任务 `d13-morning-brief-hydration` 配置为 **09:30** 启动（开盘后），不在 09:25-09:30 窗口内。
   ```text
   Current Trigger:     09:30  CONFIRMED
   Historical Trigger:  UNKNOWN
   Trigger Drift:       NOT PROVEN
   ```
   「以前是 09:25、现在漂移到 09:30」缺少历史 production scheduler 证据，不得表述为已确认的漂移。H1 至多为 `STRONGLY SUPPORTED`，且在 P0 判定 `NOT FOUND` 后失去"回归"语义。

2. **Time Gate 引入 (archived pre-P0 observation):** 生产 `app/auction_data.py` 在 2026-07-17 09:58 被修改，增加 `market_phase()` 函数和 `auction_results_ready` / `gate_reason="auction_not_complete_before_09_25"` 逻辑。此项不证明该 gate 导致回归；H4 未获授权继续分析。

3. **两条代码路径分裂 (Architecture Finding):** 
   - Git 分支 `codex/auction-time-gate-qc-20260717` (commit `9cdbadb`) 修改了 `scripts/auction_data.py` (+245 行) 和 `mcp_server.py`，增加完整 QC 栈和时间闸门。
   - 生产 `app/auction_data.py` **不在该分支上** (`git show` 显示 size 0)，说明它是独立 patch，与 MCP 路径不共享代码。
   - 本地 `scripts/auction_data.py` (8196 bytes, SHA-256 `d395249e...`) **无任何时间闸门**；生产 `scripts/auction_data.py` (7311 bytes, Apr 3) 与本地不一致。

4. **路径 vs 时间的混淆 (Provenance Boundary):** 2026-07-24 09:56 证据显示：
   - 本地无 gate 的 `scripts/auction_data.py` 成功返回 `previous_zt` 116 条记录。
   - 生产 `/api/intel/market-context` 在**同一分钟** (09:56:31) 返回 `_qc.status=partial`，明确 **blocked `previous_zt`**。
   - 这表明"以前可以/现在不可以"可能是**路径差异**（local script vs production API），而非纯时间回归。

**缺失证据:**

- **历史成功运行 (Required Check #5):** 唯一找到的"历史成功"证据是 2026-07-24 本地 no-gate 脚本的采集，**不是生产 09:25-09:30 窗口的真实运行日志**。无法证明生产环境"以前"在 09:25-09:30 成功输出过信号。

- **生产 gate 分类逻辑 (H4 完整性):** 未在 P0 中裁定。SSH 已可通过 ProxyJump 只读访问，但 H4 不属于 P0，不能据此判定 gate 是否阻断该窗口。

- **Codex automation 触发 (H1 上游):** 记忆文档声称 Codex cron 08:57 执行 `d13-morning-brief` 并输出 `d13_handoff_latest.json`，但该文件在 `~/Documents/New project 6/` **不存在** (parse fail)，Codex automation 配置文件 `~/.codex/automations/` 和 `~/.feishu-codex-cli-bridge/automations.json` 均**不存在**。无法验证 Codex 是否真的在 09:25 前触发竞价采集。

---

## 1. 当前链路图 (As-Is, 2026-07-31)

```
[用户期望的 09:25-09:30 信号链路 — MISSING]
  (无活跃触发器运行在该窗口)

[实际运行的链路 — Launchd 09:30]
  09:30 launchd trigger (after market open)
    → /opt/homebrew/bin/python3.12 /Users/Zhuanz/finance-suite/scripts/brief-payload-builder.py
    → Reads: ~/Documents/New project 6/d13_morning_brief.html (人工产出, mtime 2026-07-30 09:53)
    → Writes: /Users/Zhuanz/finance-suite/data/morning_brief/latest.json
    → Does NOT call auction_data.py
    → Does NOT capture 09:25-09:30 auction signals

[Codex automation 声称的链路 — NOT VERIFIED]
  08:57 Codex cron `d13-morning-brief` 
    → 应输出 d13_handoff_latest.json
    → 文件不存在, automation config 不存在
    → 无法验证

[OpenClaw cron jobs — Loaded but unconfirmed]
  morning-brief-hydrate: "2 9 * * 1-5" Asia/Shanghai
  midday-pulse:          "5 12 * * 1-5"
  close-brief:           "20 16 * * 1-5"
  lastRun: None (no execution record)

[Production API — Partially accessible]
  https://www.touziagent.com/api/intel/market-context
    → Returns _qc.status=partial, source=eastmoney_akshare
    → No market_phase / gate_reason / auction_results_ready fields exposed
    → 2026-07-24 09:56:31 blocked previous_zt dimension
  
  /api/intel/auction, /api/auction, /api/intel/auction-data
    → All return HTTP 404 (endpoints do not exist)

[Production backend — SSH inaccessible]
  /home/ubuntu/finance-suite-web/app/auction_data.py (15860 bytes, Jul 17 09:58)
    → Contains market_phase(), auction_results_ready, gate_reason logic
    → Backup .bak-20260717-0957 (8196 bytes) has NO gate (grep empty)
    → Exact gate behavior (does it block 09:25-09:30?) UNKNOWN — SSH blocked by Clash TUN
```

**Data Flow:**
- **No auction signal collection happens at 09:25-09:30 in current runtime.**
- The only automated task (`launchd 09:30`) reads a pre-generated HTML artifact, not live auction data.
- Production `/api/intel/market-context` does not expose auction dimensions separately; it is a composite endpoint.

---

## 2. 历史成功链路 (Before — Evidence Status: PARTIAL)

**唯一可验证的"成功"证据:** 2026-07-24 09:56:51 本地采集

```
[Local script execution — 2026-07-24 09:56:51]
  Implementation: /Users/Zhuanz/finance-suite/scripts/auction_data.py (8196 bytes, no gate)
  Method: Manual execution or one-time script run (provenance unclear)
  Provider: Eastmoney via AkShare
  Dimension: previous_zt (ak.stock_zt_pool_previous_em)
  Result: 116 rows returned
    - 55 positive / 0 flat / 61 negative
    - Multiple rows carry 首次封板时间="092500" (auction-close timestamp)
  Snapshot: /Users/Zhuanz/finance-suite/docs/signal-validation-v0.1/evidence/auction_signal_snapshot_20260724_095651.json

[Production cross-check — 2026-07-24 09:56:31]
  Endpoint: https://www.touziagent.com/api/intel/market-context
  Result: _qc.status=partial, explicitly blocked previous_zt
  Conclusion: Production API did NOT return the same data as local script in the same minute
```

**Missing Evidence:**
- **No production 09:25-09:30 success log exists.** 
- The 7/24 success came from a local no-gate script, not production runtime.
- No timestamped artifact (JSON/log) from any "before" period (e.g., June, early July) showing production successfully emitted auction signals during 09:25-09:30.
- Cannot establish "Previous Working Runtime" as a fact without this evidence.

**Inference (NOT CONCLUSION):** If the local script succeeded while production blocked in the same minute, the regression may be a **path issue** (local vs production code divergence), not a time issue.

---

## 3. 当前失败链路

**Failure Mode:** No auction signals output during 09:25-09:30.

**Confirmed Failure Points:**

1. **No trigger fires in the 09:25-09:30 window.**
   - Launchd: 09:30 (after open)
   - Crontab: empty
   - OpenClaw: loaded but `lastRun=None`, no execution evidence
   - Codex: automation files missing, handoff JSON missing

2. **Production API does not expose auction endpoint.**
   - Tested `/api/intel/auction`, `/api/auction`, `/api/intel/auction-data` → all 404
   - `/api/intel/market-context` is composite, blocked `previous_zt` on 2026-07-24 09:56

3. **Two code paths exist, only one has gate:**
   - `scripts/auction_data.py` (local, 8196 bytes): NO gate
   - `app/auction_data.py` (production, 15860 bytes): HAS gate (added 2026-07-17)
   - Gate behavior (does it block 09:25-09:30?) UNKNOWN due to SSH block

---

## 4. Diff: What Changed Between 2026-07-17 前后

| Dimension | Before (≤ 2026-07-16) | After (2026-07-17 →) | Evidence |
|-----------|----------------------|---------------------|----------|
| **Trigger Time** | UNKNOWN (no historical log) | 09:30 launchd (after open) | launchd plist `StartCalendarInterval` all `Hour=9, Minute=30` |
| **Gate Logic** | NO gate in production `app/auction_data.py` | `market_phase()` + `auction_results_ready` + `gate_reason` added | Backup `.bak-20260717-0957` grep empty; current file Jul 17 09:58 has gate |
| **Code Path Split** | UNKNOWN (no pre-7/17 architecture doc) | `scripts/` (no gate) ≠ `app/` (has gate) | Git branch `9cdbadb` only touched `scripts/`; `app/auction_data.py` not on branch |
| **Provenance** | UNKNOWN | Local script succeeds, production API blocks (same minute 2026-07-24 09:56) | Auction evidence v0.1 doc + snapshot JSON |
| **Codex Automation** | UNKNOWN | Config files missing, handoff JSON missing | `~/.codex/automations/`, `~/.feishu-codex-cli-bridge/automations.json` do not exist |

**Net Change:** At least **2 simultaneous changes** occurred on 2026-07-17:
1. Production `app/auction_data.py` patched with time gate (commit separate from git branch).
2. Trigger schedule possibly always 09:30, never 09:25 (no historical success log to refute).

---

## 5. Root Cause

**Cannot be determined with current evidence.**

**Established Facts:**
- The only loaded local trigger (launchd) runs at **09:30, after market open**, not before 09:25.
- Production `app/auction_data.py` **did not have a time gate before 2026-07-17**; it has one now (added Jul 17 09:58).
- Local `scripts/auction_data.py` **has NO gate**; production `scripts/` version differs from local.
- The 2026-07-24 "success" evidence came from **local no-gate script**, not production 09:25-09:30 runtime.

**Hypotheses (priority order):**

**H1 (Trigger Drift) — STRONGLY SUPPORTED:**
- The trigger never ran before 09:25; it was always 09:30 (after open).
- If true, there is **no regression** — the system never captured 09:25-09:30 signals in production.
- Contradicts user claim "以前 9:25-9:30 可以正常抓取," but no historical production log exists to verify the claim.

**H4 (Gate Blocks Window) — PARTIALLY SUPPORTED:**
- The gate exists and was added 2026-07-17.
- But its behavior on 09:25-09:30 is UNKNOWN (SSH inaccessible).
- If `market_phase(09:2X)` returns a phase excluded by `auction_results_ready`, gate would block.
- The 7/17 memory doc says gate was added to **fix premature 09:19 calls**, not to block 09:25-09:30, but the exact threshold logic is unread.

**H2 (Data Source Change) — NOT SUPPORTED:**
- Provider is Eastmoney via AkShare in both "before" (7/24 local) and "now" (production API).
- No evidence of provider switch.

**H3 (Field Availability) — NOT ASSESSED:**
- Requires production auction endpoint access or SSH to read field mappings.
- Production endpoints return 404; SSH blocked.

**H5 (Path Divergence) — NEWLY RAISED:**
- The "success" vs "failure" difference may be **local script (no gate) vs production API (has gate)**, not time-based regression.
- If users were running local scripts before (manually or via untracked cron), and now rely on production API, the behavior change is explained by path, not by time.

**Blocking Issues:**
1. **SSH to production blocked by Clash TUN DNS hijack** (`198.18.0.11` fake-IP, `Connection closed by remote host`). Cannot read exact gate logic or production script content.
2. **No historical production 09:25-09:30 success log.** Cannot prove "before worked" as stated.
3. **Codex automation evidence missing.** Claimed 08:57 trigger has no config file, no handoff JSON, cannot verify it ever ran.

---

## 6. Evidence

### 6.1 Trigger Audit (H1)

**Local launchd job:**
```xml
~/Library/LaunchAgents/com.zhuanz.d13-morning-brief-hydration.plist
  ProgramArguments: /opt/homebrew/bin/python3.12 /Users/Zhuanz/finance-suite/scripts/brief-payload-builder.py
  StartCalendarInterval:
    - Hour=9, Minute=30, Weekday=1
    - Hour=9, Minute=30, Weekday=2
    - Hour=9, Minute=30, Weekday=3
    - Hour=9, Minute=30, Weekday=4
    - Hour=9, Minute=30, Weekday=5
  RunAtLoad: false
  launchctl list: loaded, exit 0
```
→ **Fires at 09:30, after market open.**

**Crontab:**
```
crontab -l
  57 8 * * 1  # weekly-digest (unrelated)
  0 9 9 6 *   # premarket-preflight (unrelated)
```
→ **No auction or morning-brief entry.**

**OpenClaw cron jobs:**
```json
~/.openclaw/cron/jobs.json
  morning-brief-hydrate: {"kind": "cron", "expr": "2 9 * * 1-5", "tz": "Asia/Shanghai"}
  midday-pulse:          {"kind": "cron", "expr": "5 12 * * 1-5", "tz": "Asia/Shanghai"}
  close-brief:           {"kind": "cron", "expr": "20 16 * * 1-5", "tz": "Asia/Shanghai"}
  All enabled=True, lastRun=None
```
→ **morning-brief-hydrate scheduled 09:02 (before open), but `lastRun=None` — no execution record.**

**Codex automation:**
```
~/.codex/automations/d13-morning-brief.json: No such file or directory
~/.feishu-codex-cli-bridge/automations.json: No such file or directory
~/Documents/New project 6/d13_handoff_latest.json: parse fail
```
→ **Claimed 08:57 Codex trigger has no config, no output artifact.**

**Conclusion (H1):** Only one trigger confirmed active: launchd 09:30. No trigger runs in 09:25-09:30 window.

---

### 6.2 Time Gate Audit (H4)

**Production `app/auction_data.py`:**
```
/home/ubuntu/finance-suite-web/app/auction_data.py
  Size: 15860 bytes
  Timestamp: Jul 17 09:58
  grep results (partial, SSH interrupted):
    Line 22: def market_phase(at: datetime | None = None) -> str:
    Line 36: elif hhmmss < 92500:
    Line 38: elif hhmmss < 93000:
    Line 190: "auction_results_ready": market_phase(requested_at) not in {...}
    Line 280: gate_reason = "auction_not_complete_before_09_25"
    Line 344: "【时间门阻断】09:25 集合竞价尚未结束。..."
    Line 428: if gate == "auction_not_complete_before_09_25": lines.append("集合竞价进行中...")
```

**Production backup (pre-change):**
```
/home/ubuntu/backups/auction/20260717-095430/auction_data.py.bak-20260717-0957
  Size: 8196 bytes
  grep '09:25|92500|93000|market_phase|时间闸门|gate_reason': EMPTY
```
→ **Gate did NOT exist before 2026-07-17 09:57.**

**Local `scripts/auction_data.py`:**
```
/Users/Zhuanz/finance-suite/scripts/auction_data.py
  Size: 8196 bytes
  SHA-256: d395249e7dff4050cb88a953ed0b54b27620cae0cb0177f8cd0a5e17e3d81a3c
  grep '09:25|92500|93000|market_phase|时间闸门|gate_reason': EMPTY
```
→ **Local script has NO gate.**

**Git branch `codex/auction-time-gate-qc-20260717`:**
```
commit 9cdbadb "fix: gate auction analysis on validated market data"
  scripts/auction_data.py: +245 lines
  app/auction_data.py: size 0 (not on this branch)
```
→ **Production `app/auction_data.py` gate was applied separately, not via this branch.**

**Blocking:** Cannot read exact `market_phase()` return values for 09:25-09:30 or the `auction_results_ready` exclusion set due to SSH block. Cannot determine if gate blocks 09:25-09:30 window.

---

### 6.3 Historical Success Evidence (Required Check #5)

**2026-07-24 09:56:51 local capture:**
```
Implementation: /Users/Zhuanz/finance-suite/scripts/auction_data.py (local, no gate)
Provider: Eastmoney via AkShare
Dimension: previous_zt (ak.stock_zt_pool_previous_em)
Result: 116 rows
Snapshot: /Users/Zhuanz/finance-suite/docs/signal-validation-v0.1/evidence/auction_signal_snapshot_20260724_095651.json
Multiple rows with 首次封板时间="092500" (auction-close timestamp present)
```

**Production cross-check (same minute):**
```
https://www.touziagent.com/api/intel/market-context at 2026-07-24 09:56:31
  _qc.status=partial
  previous_zt: BLOCKED (not returned)
  SHA-256: 72a17651b6a8885a228c64181ecb9c72e9bab0abc40c4edf01a49e7df1bfbff4
```

**Evidence Doc Conclusion:**
> "The production cross-check returned `_qc.status=partial`, `source_type=real`, and explicitly blocked `previous_zt`, so it is not used as row-level evidence."

→ **Local script succeeded; production API blocked in the same minute.**  
→ **"Success" is path-dependent (local vs production), not time-dependent.**

**Missing:** No production 09:25-09:30 success log from any prior date (June, early July). Cannot establish "Previous Working Runtime" for production.

---

### 6.4 Production API Endpoints (Current)

```
Tested 2026-07-31 00:49 CST:
  /api/intel/auction       → HTTP 404
  /api/auction             → HTTP 404
  /api/intel/auction-data  → HTTP 404
  /api/intel/market-pulse  → HTTP 404
  /api/intel/realtime      → HTTP 404

  /api/intel/market-context → HTTP 200
    _qc.status=partial, source=eastmoney_akshare, completeness=0.5
    No market_phase / gate_reason / auction_results_ready fields in response
    Top-level keys: status, source, title, positioning, generated_at, date_label, conclusion, metrics, context, themes, monitoring, data_availability, disclaimer, _qc
```

→ **No dedicated auction endpoint exists in production API.**

---

### 6.5 Code Path Divergence

| Path | File | Size | Gate? | Last Modified | Notes |
|------|------|------|-------|---------------|-------|
| Local (MCP) | `scripts/auction_data.py` | 8196 | NO | (local dev) | Matches pre-7/17 backup size; SHA-256 `d395249e...` |
| Production (MCP) | `/home/ubuntu/finance-suite-web/scripts/auction_data.py` | 7311 | UNKNOWN | Apr 3 18:02 | Different from local; cannot read via SSH |
| Production (Web API) | `/home/ubuntu/finance-suite-web/app/auction_data.py` | 15860 | YES | Jul 17 09:58 | Gate added; not on git branch `9cdbadb`; SSH blocked |
| Backup (pre-change) | `.../auction_data.py.bak-20260717-0957` | 8196 | NO | Jul 17 09:54 | Matches local size; no gate (grep empty) |

→ **At least 3 distinct versions exist; local ≠ production MCP ≠ production Web API.**

---

## 7. Recommendations

**Cannot proceed with implementation until evidence gaps closed:**

1. **Unblock SSH** — resolve Clash TUN DNS hijack (`198.18.0.11`); read production `app/auction_data.py` lines 18-60 (market_phase logic), 180-200 (auction_results_ready set), 260-300 (gate condition). Determine if 09:25-09:30 is classified as ready or blocked.

2. **Find historical production 09:25-09:30 success log** — search production `/home/ubuntu/finance-suite-web/` for timestamped JSON/log artifacts from June or early July showing auction signals output during 09:25-09:30. Without this, "以前可以抓到" remains an unverified claim.

3. **Verify Codex automation** — locate or reconstruct `~/.codex/automations/d13-morning-brief.json` and `d13_handoff_latest.json` to confirm whether 08:57 trigger ever ran and called `workflow_orchestrator.py` with auction collection.

4. **Establish SSOT for trigger schedule** — if Codex 08:57 was the intended trigger, document why it is now missing. If launchd 09:30 is correct, document why user expects 09:25-09:30 signals.

5. **Reconcile code paths** — decide whether `scripts/auction_data.py` should be the SSOT (no gate) or `app/auction_data.py` should be (has gate), and unify or explicitly document the split.

**Do NOT:**
- ❌ 修改策略
- ❌ 更换数据源
- ❌ 调参数让信号出现
- ❌ 修改过滤规则
- ❌ 接聚源数据库

**聚源数据库不是这个问题的答案。** 聚源解决的是机构级历史/基础数据能力，而集合竞价需要验证的是盘中实时采集链路。先证明 Runtime 为什么从可用变成不可用。

---

## Appendix: SSH Block Details

```
$ ssh ubuntu@119.28.156.125
kex_exchange_identification: Connection closed by remote host
Connection closed by 119.28.156.125 port 22

$ dig +short touziagent.com
198.18.0.11  # Clash fake-IP range

$ nc -zv 119.28.156.125 22
Connection to 119.28.156.125 port 22 [tcp/ssh] succeeded!
→ False positive — Clash TUN reports success on fake-IP interface, not real reachability

Clash processes running:
  verge-mihomo (PID 82880)
  clash-verge (PID 82833)
  clash-verge-service (PID 323)

~/.ssh/config: no entry for touziagent.com or 119.28.156.125
```

**Workaround attempted:** HTTPS 443 works (probed `/api/intel/market-context` successfully), but Web API does not expose `app/auction_data.py` code or internal `market_phase` logic.
