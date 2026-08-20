# Branch Identity Closure — Evidence v0.2

**repo:** `finance-suite`（+ `finance-suite-backend`）
**rev-2（2026-08-20）：** 响应 C evidence-audit REQUEST_CHANGES（8 findings）+ 合并 Phase 4 production observation。
**rev-1 → rev-2 变更：** 补 F1/F2/F3/F5/F6/F7 逐字 stdout；F4 撤回并升级为 RCA；结论 2/6 撤回；F5 术语澄清；F8 footer 已修。
**rev-2 → rev-3 变更（2026-08-20）：** 响应 C 二次 REQUEST_CHANGES —— 修正 `search_trust_gate.py` 归属（不在 e266213，在 backend `fix/search-trust-gate-p0` 分支 `8a88685→5a523e0`，未 merge）。raw receipt / topology 状态 / git 冻结仍 pending（见 §9）。
**rev-3 → rev-4 变更（2026-08-20）：** 响应 C 三次 REQUEST_CHANGES —— Phase 4 `MATCH`/`DRIFT`/`已证` 全部降为「C 二手摘要，待原始 receipt 复核」；topology 6 处 ownership 断言对齐 UNDECIDED；§9 改为已修/未闭合账本。
**rev-4 → rev-5 变更（2026-08-20）：** Phase 4 raw receipt 已物化（`PHASE4_PRODUCTION_RECEIPT_v0.1.md`，含原始 SSH stdout + 独立 git SHA-256 复核）→ Phase 4 = CLOSED/PROVEN；Phase 2 ownership 已完成（4/5 DECIDED）→ §3/§4/§9 对齐当前态。
**rev-5 → rev-6 变更（2026-08-20）：** 响应 C REQUEST_CHANGES Major #2 —— rev-5 曾把 Phase 2 ownership 挂在 Phase 4 receipt 物化之后叙述，被误读为「receipt 支撑 ownership」。G 裁决：Phase 4 receipt 与 Phase 2 ownership 是两条独立证据层，receipt 不得作为 ownership 推断依据。Phase 2 ownership 裁决已单独物化为 `PHASE2_CANONICAL_OWNERSHIP_DECISION_v0.1.md`（G，2026-08-20，晚于 receipt 的「Phase 2 继续暂停」态）。本文件 §4/§6/§9 的 "4/5 DECIDED" 断言改为指向该独立 artifact，不再由本文件或 receipt 自证。

---

## 1. 原始命令 + 逐字 stdout

### 1.1 DAG 身份（finance-suite）

```
$ git rev-parse main
faa01d4bb4ecd2dd54401f40db023751047d15ac

$ git rev-parse origin/main
48c9cdf841660043b93dfa4f182ab5e8bd5501e7

$ git rev-parse runtime-validation-v0.1
13e2acd86473601f4c8953555280a47b9a874a35

$ git merge-base main origin/main
48c9cdf841660043b93dfa4f182ab5e8bd5501e7

$ git merge-base runtime-validation-v0.1 origin/main
cefc660fd7c97f372e300773b32b83d4a9f374a4

$ git rev-list --left-right --count main...origin/main
1	0

$ git rev-list --left-right --count runtime-validation-v0.1...origin/main
68	2
```

### 1.2 F1 — faa01d4 日期（`git show -s --format=fuller`）

```
commit faa01d4bb4ecd2dd54401f40db023751047d15ac
Author:     Zhuanz <zhuanz@touziagent.com>
AuthorDate: Mon Aug 3 21:39:46 2026 +0800
Commit:     Zhuanz <zhuanz@touziagent.com>
CommitDate: Tue Aug 11 23:18:07 2026 +0800
```

→ author 08-03，commit 08-11，是 rebase/cherry-pick 痕迹，非 08-03 历史点。

### 1.3 F2 — 48c9cdf merge 结构（`git cat-file -p`）

```
tree d9490a9bce1505ae38d0c27da6ff0c18a343c67d
parent cefc660fd7c97f372e300773b32b83d4a9f374a4
parent 22a26bdf589d12a2042a06d04eae4144f92db47a
author jinny280401-glitch <jinny280401@gmail.com> 1786461477 +0800
committer GitHub <noreply@github.com> 1786461477 +0800
```

→ **committer = GitHub**，这是 GitHub PR merge，证实 48c9cdf 是远端 merge 而非本地 commit。

### 1.4 F2 — right-side commits（`git log --oneline cefc660..origin/main`）

```
48c9cdf Merge pull request #2 from jinny280401-glitch/codex/hero-path-a-clean
22a26bd fix(auction): P0 frontend contract — parse {_qc,data,count} instead of Golden Pit {hits,watchlist}
```

### 1.5 F3 — `--is-ancestor`（exit code）

```
$ git merge-base --is-ancestor origin/main main;            exit=0  (YES)
$ git merge-base --is-ancestor 22a26bd runtime-validation-v0.1; exit=1  (NO)
```

### 1.6 F5 — data/ ops/ tracked（`git ls-files`）

```
data/ tracked files: 1
ops/  tracked files: 11
```

### 1.7 F6 — backend 仓 market_intel（`git ls-files --error-unmatch`）

```
$ git -C finance-suite-backend ls-files --error-unmatch scripts/market_intel.py
error: pathspec 'scripts/market_intel.py' did not match any file(s) known to git
$ git -C finance-suite-backend ls-files --error-unmatch scripts/market_intel_schema.py
error: pathspec 'scripts/market_intel_schema.py' did not match any file(s) known to git
```

→ backend `scripts/` 目录无任何 tracked 文件；market_intel*.py 仅存在于 frontend，untracked。

### 1.8 F7 — README clean-clone 实测（/tmp 干净 venv）

```
$ pip list | grep -iE '^(mcp|fastapi|akshare|tushare|pandas|uvicorn)'
mcp       2.0.0        ← mcp>=1.27.0 无上限，装到 2.0.0
fastapi   0.141.1
...

$ ls mcp/server/         ← 无 fastmcp.py（有 apps.py/lowlevel/mcpserver/…）
__init__.py  __main__.py  apps.py  lowlevel  mcpserver  …

$ from mcp.server.fastmcp import FastMCP
ModuleNotFoundError: No module named 'mcp.server.fastmcp'

$ import mcp_server
File ".../mcp_server.py", line 64, in <module>
    from mcp.server.fastmcp import FastMCP
ModuleNotFoundError: No module named 'mcp.server.fastmcp'
```

**根因（已定位，非疑似）：** `requirements.txt` 写 `mcp>=1.27.0` 无上限 → pip 解析到 `mcp 2.0.0` → 2.0 移除了 `mcp.server.fastmcp` 模块 → `mcp_server.py:64` 的 1.x 旧 import 路径失败。

### 1.9 F7 — trust_gate/ 不在 origin/main

```
$ git ls-tree origin/main trust_gate/   → 空输出，exit=0（无任何 tracked 条目）
```

---

## 2. DAG 三问答案（SOUND，有 stdout 支撑）

- **Q1 faa01d4 = main HEAD**（`rev-parse main`），非 08-03 历史点（§1.2 commit date 08-11）。
- **Q2 main = origin/main + 1**：48c9cdf 是 faa01d4 直接 parent（§1.1 merge-base + §1.3 cat-file），`--is-ancestor` = YES（§1.5）。
- **Q3 rv-v0.1 68/2 真分叉**：merge-base cefc660（§1.1）；behind 2 = 22a26bd + 48c9cdf（§1.4）；rv-v0.1 缺 22a26bd（§1.5 exit=1）。

---

## 3. Phase 4 Production Identity Observation（receipt 已物化，PROVEN）

> **证据状态（rev-5 更新）：** Phase 4 raw receipt 已物化为 `PHASE4_PRODUCTION_RECEIPT_v0.1.md`（含 C 原始只读 SSH `sha256sum` stdout + Session A 独立本地 git SHA-256 复核）。下表 verdict 由 receipt §3 比对矩阵汇总，**PROVEN**。receipt 边界：仅覆盖 6 个采样文件；`app/main.py` / `app/routers/intel.py` 不在 raw receipt（见 receipt §6），不背书整棵生产 tree。

生产入口 = systemd 启动 `app.main:app`；landing 目录**无 git metadata**（deploy target，非 canonical repo）。

| File | production path | verdict（receipt 已物化，PROVEN） |
|---|---|---|
| mcp_server.py | `<landing>/mcp_server.py` | MATCH backend main e266213 |
| auction_data.py | `<landing>/app/auction_data.py` | MATCH backend main e266213 |
| auction_data.py | `<landing>/scripts/auction_data.py` | DRIFT（历史 frontend `fcafa4d`，orphan） |
| stock_data.py | `<landing>/app/stock_data.py` | MATCH backend main e266213 |
| index.html | `<landing>/templates/index.html` | MATCH backend main e266213 |
| deploy-backend.sh | not present | UNKNOWN（OBS-5：production 未发现 *deploy*.sh 部署痕迹） |
| api.py | `<landing>/app/routers/api.py` | MATCH backend main e266213（receipt §4 反证 C 的 drift 误报） |
| search_trust_gate.py | absent | ABSENT（e266213 亦无；仅在 `fix/search-trust-gate-p0` 分支，未 merge） |

**结论（receipt PROVEN，见 `PHASE4_PRODUCTION_RECEIPT_v0.1.md` §5）：生产 6 采样文件 = backend main e266213（5 个）+ 历史 frontend fcafa4d 遗留（`scripts/auction_data.py`，1 个 orphan）。api.py / search_trust_gate.py 相对 main 无漂移（C 的 drift 系基线错误，已反证）。canonical ownership 由独立的 `PHASE2_CANONICAL_OWNERSHIP_DECISION_v0.1.md`（G，2026-08-20）裁决，非由本 receipt 推断（见 §4）。**

### 生产 tree 模型（mixed-revision deployment tree；标签 PROVEN 见 receipt §3/§4）

```
Production Landing（non-git）
├── app/main.py ─────────── backend（receipt 未采样，非 PROVEN）
├── app/routers/intel.py ── backend（receipt 未采样，非 PROVEN）
├── app/auction_data.py ── backend e266213 MATCH（PROVEN）
├── app/stock_data.py ──── backend e266213 MATCH（PROVEN）
├── app/routers/api.py ─── backend e266213 MATCH（PROVEN，receipt §4 反证 drift）
├── search_trust_gate.py ─ ABSENT（e266213 亦无；仅在 fix/search-trust-gate-p0，未 merge）
├── mcp_server.py ──────── backend e266213 MATCH（PROVEN；runtime consumption UNKNOWN）
└── scripts/auction_data.py ─ historical frontend fcafa4d DRIFT（orphan，disposition pending）
```

---

## 4. 治理结论（rev-2 修订）

1. `CANONICAL_REPOSITORY_TOPOLOGY_v0.1` 状态 → **CLOSED**（两条独立证据层各自闭合：Phase 4 receipt PROVEN=生产文件身份；Phase 2 ownership 4/5 DECIDED=`PHASE2_CANONICAL_OWNERSHIP_DECISION_v0.1.md`（G）；header/footer 已对齐，见 topology rev）。
2. **mcp_server.py —— canonical owner = FRONTEND（`PHASE2_CANONICAL_OWNERSHIP_DECISION_v0.1.md` 裁决）。** 三分离：
   - production file identity = **backend@e266213 MATCH**（receipt 已物化，PROVEN）
   - FastAPI app tree 不引用该文件 → FastAPI consumption = **NOT OBSERVED**
   - MCP runtime consumption = **UNKNOWN**（需独立证明）
   - canonical repository ownership = **FRONTEND**（`PHASE2_CANONICAL_OWNERSHIP_DECISION_v0.1.md` 裁决；production/owner drift OPEN：生产身份是 backend copy，但 canonical owner 裁决为 frontend）
3. `auction.html` source ownership = frontend；production served revision = **UNKNOWN**。（不变）
4. `market_intel*.py`：frontend-only untracked（backend 无此文件，§1.7 stdout）。非 canonical conflict。
5. `data/` `ops/`：frontend tracked assets（§1.6）。**术语澄清：** 此处 `ops/` = 顶层 tracked 目录（11 文件），与 UNTRACKED_FILES_DISPOSITION 的 `docs/operations/`（untracked 文档目录，LOCAL_ONLY）**不是同一目录**，无冲突。
6. **撤回 v0.1「双部署链 / MCP 代码在 finance-suite → OpenClaw workspace」。** 降级为：
   - **可保留的 static fact**：存在 `deploy.sh` / `deploy-backend.sh` 两个脚本，其内容声明了部署方向（`deploy.sh` 抓 GitHub main；`deploy-backend.sh` 注释提到 ECS `<prod-host>`、OpenClaw workspace）。
   - **不可写成 runtime lineage**：deployment configuration/target observed ≠ production execution provenance proven。线上实际由什么部署、消费哪版，本证据未证。
   - 当前 verdict：**NOT PROVEN / RETRACTED**。
7. `README` = **NOT CLEAN-CLONE READY**：§1.8 已定位根因（mcp 2.0.0 移除 fastmcp）。README §2 引用 `trust_gate/`，该目录不在 origin/main（§1.9）。
8. **Phase 2 ownership 裁决（`PHASE2_CANONICAL_OWNERSHIP_DECISION_v0.1.md`，G，2026-08-20，晚于 receipt 的「Phase 2 继续暂停」态，read-only）：** `app/auction_data.py` + `app/stock_data.py` canonical owner = **BACKEND**（production identity = e266213 MATCH，receipt PROVEN 仅证身份；frontend 副本为 stale mirror）。`index.html` = FRONTEND（backend `templates/` copy = deploy artifact/mirror）。`deploy-backend.sh` = **SPLIT / NAMING COLLISION / FINAL DISPOSITION PENDING**。`scripts/auction_data.py` = **historical orphan（disposition pending，不计入 5 项 ownership 分母）**。

---

## 5. RCA（F4 升级）：source-repository inference → runtime truth

**错误：** v0.1 结论 2/6 把 repo 内部证据（行数 2029 vs 1325、提交频率 3 vs 1、文件新旧、`deploy-backend.sh` 注释）提升为生产身份结论。

**根因：** 无 production observation 时，用 codebase-internal 推断替代 production-side 观测，并把「脚本声称的部署方向」当成「线上当前部署事实」。

**后果：** 结论 2（mcp_server.py frontend canonical）与结论 6（MCP lineage → frontend）方向**反了**——生产实际匹配 backend e266213。

**Governance lesson：**
- Repository-internal evidence（line count / commit frequency / file age / comments / deploy-script intent）**不得升格为 production identity claim**。
- Production identity 需要 production-side observation。
- Canonical ownership 需要独立的 ownership decision，不得仅从 production presence 推断。
- 三分离：文件从哪版来 / 谁当前消费 / 谁应拥有，各自独立裁决。

---

## 6. 明确不做（下一步不定义为实现任务）

- 不做 68 commits reconcile（rename / merge / rebase / cherry-pick / 新 handoff branch 均未选型）。
- 不修 production api.py drift；不部署任何修复。
- 不裁决 MCP / Trust Gate / production repair。
- ~~下一步（Phase 2，另行授权）：只裁决 auction_data.py + stock_data.py 的 canonical ownership；不连带 MCP / Trust Gate / reconcile / repair。~~ → **Phase 2 已完成（`PHASE2_CANONICAL_OWNERSHIP_DECISION_v0.1.md`，G，08-20，read-only）**：auction/stock = BACKEND，mcp = FRONTEND，deploy-backend.sh SPLIT/NAMING COLLISION/FINAL DISPOSITION PENDING，scripts/auction_data.py orphan（见 §4 第 8 条）。

---

## 7. 边界声明

本 session 未执行 add / commit / merge / reset / cleanup / push / deploy，未动 `2036bf9` 路由。F8 footer 修复（见 §8）是唯一对 Session B 文档的写入，且为 G 明确授权的机械矛盾修正。

## 8. F8 修复记录

`CANONICAL_REPOSITORY_TOPOLOGY_v0.1.md` footer `Status: FROZEN` → `Status: PROVISIONAL`（与 header L4 一致），依据 rev-2 结论 1「保持 PROVISIONAL 不得升级」。
> **rev-5 更新：** 该 PROVISIONAL 状态已被 supersede —— Phase 4 receipt 物化（生产文件身份 PROVEN）与 `PHASE2_CANONICAL_OWNERSHIP_DECISION_v0.1.md`（G，ownership 4/5 DECIDED，独立裁决）两者各自闭合后，topology header/footer 同步升级为 `PROVEN/CLOSED`（见 topology rev + 本文件 §4 第 1 条「CLOSED」）。F8 的 FROZEN→PROVISIONAL 是 rev-2 时的中间态，非当前态。

## 9. 待办账本（rev-5；需授权项与已修项分开，本 session 未越权执行）

对应 C 三轮 REQUEST_CHANGES + 后续 Phase 4 receipt 物化 + Phase 2 ownership 裁决。当前闭合状态：

**已修（rev-3/rev-4/rev-5，机械一致修正，无架构裁决）：**
1. `search_trust_gate.py` 归属 —— 不在 e266213，在 backend `fix/search-trust-gate-p0` 分支（rev-3 已修）。
2. Phase 4 段首承认 SHA-256 原始 stdout 未物化（rev-3 已修）→ **rev-5 已物化**：raw receipt `PHASE4_PRODUCTION_RECEIPT_v0.1.md` 已固化（C 原始 SSH stdout + Session A 独立 git SHA-256 复核）。
3. topology header + boundary 表 "Data provider implementations"（rev-3 降 UNRESOLVED）→ **rev-5 已对齐**：Phase 2 DECIDED（`PHASE2_CANONICAL_OWNERSHIP_DECISION_v0.1.md`：auction/stock = BACKEND，mcp = FRONTEND），topology 已 CLOSED。
4. Phase 4 表/结论/tree/§4.2 的 `MATCH`/`DRIFT`/`已证` → **rev-5 升级为 PROVEN**（receipt 支撑身份，非二手摘要；不涉及 ownership）。
5. topology 6 处 ownership/责任断言 → **rev-5 全部对齐 `PHASE2_CANONICAL_OWNERSHIP_DECISION_v0.1.md` 裁决结果**（rev-6：引用改为指向该独立 artifact，不再由 receipt 推断）。

**分类（rev-5 终态）：**

1. **Repository evidence/ownership reconciliation = COMPLETE**（两条独立证据层：Phase 4 receipt PROVEN=文件身份；Phase 2 4/5 DECIDED=`PHASE2_CANONICAL_OWNERSHIP_DECISION_v0.1.md`（G）=ownership；三文档已对齐 canonical state）。

2. **Handoff closure blockers**（真正阻塞 Repository Handoff CLOSED，需独立授权，本 session 无权执行）：
   - canonical-main materialization（把已批准的 handoff set 安全搬到两个 canonical main）
   - commit / push
   - origin fresh-clone acceptance

3. **Non-blocking backlog**（不阻塞 handoff，可延后归档）：
   - `scripts/auction_data.py` orphan disposition
   - `deploy-backend.sh` SPLIT final disposition
   - freeze-bound asset cleanup（untracked → staged/frozen/归档）
