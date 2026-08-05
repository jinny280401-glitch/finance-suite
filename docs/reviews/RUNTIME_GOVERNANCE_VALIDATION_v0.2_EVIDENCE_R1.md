# Runtime Governance Validation v0.2 — Evidence Round 1

**Window:** Runtime Governance Validation v0.2
**Round:** R1 (static verification only, no live access)
**Baseline:** `cefc660` (main, tag `v0.1-main-consolidation`)
**Mode:** Validation Only
**Date:** 2026-08-05

---

## 0. v0.1 Evidence Hash Re-verify (baseline integrity check)

v0.1 报告 §4 列出的两份 evidence SHA-256 在 `cefc660` 基线里重核:

| Evidence | v0.1 reported hash | v0.2 re-computed hash | Match |
|---|---|---|---|
| `docs/signal-validation-v0.1/evidence/auction_signal_snapshot_20260724_095651.json` | `4532569999bdd12e9863c1c835893b982f3c2ce95d69ebd9d6520d236263eac0` | `4532569999bdd12e9863c1c835893b982f3c2ce95d69ebd9d6520d236263eac0` | **YES** |
| `docs/signal-validation-v0.1/evidence/market_context_crosscheck_20260724_095631.json` | `72a17651b6a8885a228c64181ecb9c72e9bab0abc40c4edf01a49e7df1bfbff4` | `72a17651b6a8885a228c64181ecb9c72e9bab0abc40c4edf01a49e7df1bfbff4` | **YES** |

Tool: `shasum -a 256` (macOS). 工具差异 vs `sha256sum` 已在 v0.1 报告中说明,本轮沿用同一工具。

**Baseline integrity**: PASS. v0.1 evidence 未在 cefc660 → 当前工作区之间发生 silent drift。

---

## 1. UA-F7 — `market_context` module resolution

**Question (v0.1 carry-forward):** `server_scripts/intel_api.py:226`(v0.1 报告中) / 当前核实 line 230 引用 `import market_context`,在 `cefc660` 基线里是否能 resolve?

### Method

```bash
git ls-tree -r cefc660 --name-only | grep "market_context"
```

### Result

```
docs/signal-validation-v0.1/evidence/market_context_crosscheck_20260724_095631.json
```

**基线里没有 `market_context` 的 Python 源文件。** 只有一份 evidence crosscheck JSON。

### Cross-check: 运行时残留

`scripts/__pycache__/market_context.cpython-312.pyc` 在工作区存在,但 `cefc660` 基线里不存在该 `.pyc` —— 编译缓存是当前工作区(分支 `runtime-validation-v0.1`)的本地状态,不属于基线。

### Verdict

**UA-F7 — RESOLVED: NO.**

`import market_context` 在 `cefc660` 是 dangling import。运行时一旦执行该路径,必然 `ModuleNotFoundError`。基线层面已经穷尽可静态验证范围;无法判定生产环境的 `market_context.py` 是否通过基线外的部署通道(SSH / 容器外挂)注入。

**Carry-forward UNKNOWN (live-only):** 生产环境 `market_context` 模块究竟来自何处、是否被注入、是否在 incident 当时为生产版本,无法在静态验证范围回答。

---

## 2. UA-F8 — Backend deployment mechanism

**Question (v0.1 carry-forward):** `deploy.sh` 已确认只覆盖 `app/*.html`,后端 auction 代码如何进生产?

### Method

完整 Read `deploy.sh` 全文(头部 1-50 行 + 关键 block),逐节核对。

### Result

`deploy.sh` 总共做了以下事情:

1. **拉取静态前端资产** (line 13-39):`index.html` + 8 个 `app/*.html`(deep-research / stock / macro / **auction** / meeting / video / xueqiu-hot)+ 5 个 Sidebar P0 资产(workbench-config.html / sidebar-registry.js / market-temperature-mini.{js,css,html,fixture.js})+ `index.html`(首页模板)。
2. **验证文件**(line 42-44):`ls -lh` 确认。
3. **备份 + 重写 nginx 配置**(line 46-115):`/api/` 转发到 `127.0.0.1:8000`,根路径 `/` 也转发到 `127.0.0.1:8000`(Flask/uvicorn 后端)。
4. **nginx reload**(line 117-123)。

**关键观察:**

- `deploy.sh` 拉取列表里只有前端资产(`.html` / `.js` / `.css`),**没有任何后端代码拉取动作**(`scripts/auction_data.py` / `scripts/mcp_server.py` / `server_scripts/intel_api.py` 都没出现在 curl 列表里)。
- 但 nginx 配置里 `/api/` 转发到 `127.0.0.1:8000` —— 后端进程必须存在,且必须已在运行。
- **后端进程的代码部署机制不在 `deploy.sh` 覆盖范围。** 它要么通过 systemd / docker / 手动 git pull / ssh rsync / 其他渠道,要么 `127.0.0.1:8000` 在 incident 当时根本没在跑。

### Cross-check: 后端服务的证据

- `docs/signal-validation-v0.1/evidence/market_context_crosscheck_20260724_095631.json` 是 2026-07-24 抓的 production cross-check —— 证明后端至少在 2026-07-24 那一刻是可访问的。
- 没有 production deployment log / systemd unit / docker-compose 等价物进入 `cefc660` 基线。

### Verdict

**UA-F8 — RESOLVED: STATIC FINDING.**

`deploy.sh` 的部署覆盖范围在静态可读范围内已经穷尽。结论已超出 v0.1 报告原表述:

- v0.1 原表述:"`deploy.sh` 只拉 `app/*.html`,后端代码如何进生产 UNKNOWN"
- v0.2 静态证据:**`deploy.sh` 没有任何后端代码拉取动作**,后端部署不在其覆盖范围。这不是"机制 UNKNOWN",而是"`deploy.sh` 不是后端部署的载体"。

**Carry-forward UNKNOWN (live-only):** 后端真实部署机制(SSH / systemd / docker / 其他)在 production 环境如何运作,production 进程实际指向的代码版本,均无法在静态范围回答。

---

## 3. UA-F5 — `scripts/` 与 `app/` parity as root cause

**Question (v0.1 carry-forward):** `scripts/auction_data.py` 与 `app/auction.html` 之间是否构成 root cause?

### Method

```bash
git ls-tree -r cefc660 --name-only | grep -E "(deploy\.sh|auction_data|intel_api|market_context)"
```

```
deploy.sh
docs/signal-validation-v0.1/evidence/market_context_crosscheck_20260724_095631.json
scripts/auction_data.py
server_scripts/intel_api.py
```

基线里同时存在两条数据路径:

1. **MCP 路径**:`scripts/auction_data.py`(被 `mcp_server.py:market_pulse()` 调用)→ 返回结构化 JSON
2. **Web API 路径**:`server_scripts/intel_api.py:market_context_layer()`(被 nginx → `127.0.0.1:8000` 调用)→ 返回渲染上下文

### Cross-check: app/auction.html 数据流

未在本轮 Read 全文。但 v0.1 报告 §2 A1 列出 `app/auction.html EXISTS`,且 v0.1 evidence 已抓过 production cross-check。

### Verdict

**UA-F5 — PARTIAL RESOLVED.**

- **静态可证**:`scripts/` 和 `app/` 不存在 1:1 对应关系,两条路径(MCP / Web API)在基线层面是平行结构,各自有自己的数据获取与渲染入口。
- **静态不可证**:production 当时 `app/auction.html` 实际请求走的是哪条路径(UA-F9 carry-forward)。

**Carry-forward (live-only):** 真实 production 流量在 incident 当时走 MCP path 还是 Web API path。

---

## 4. Round 1 Summary

| UA ID | v0.2 status | Evidence |
|---|---|---|
| UA-F1 | UNKNOWN (carried, live-only) | — |
| UA-F2 | UNKNOWN (carried, live-only) | — |
| UA-F3 | UNKNOWN (carried, live-only) | — |
| UA-F4 | UNKNOWN (carried, live-only) | — |
| UA-F5 | PARTIAL | §3 |
| UA-F6 | UNKNOWN (carried, live-only) | — |
| UA-F7 | RESOLVED (static finding: NO) | §1 |
| UA-F8 | RESOLVED (static finding: deploy.sh 不是后端部署载体) | §2 |
| UA-F9 | UNKNOWN (carried, live-only) | — |

**Track A 9 条:** 6 条 UNKNOWN carried (UA-F1/F2/F3/F4/F6/F9),2 条 RESOLVED(UA-F7/F8),1 条 PARTIAL(UA-F5)。

**Track B 6 条:** 全部保持 v0.1 状态,本轮不动。

---

## 5. Claim Boundary Re-statement

v0.1 报告结尾的三条治理区分:

> Local runtime evidence ≠ Production runtime evidence
> Fix exists ≠ Root cause proven
> HTTP 200 ≠ Business success

v0.2 R1 没产生需要新增的第四条。三条依然成立,且 R1 的全部 RESOLVED 项都是"否定性证据"(deploy.sh 不覆盖后端 / market_context 在基线里 resolve 失败),正好印证 `Fix exists ≠ Root cause proven` —— Web path 的 7/17 hotfix 与 production incident 的 root cause 之间,在静态可证范围内,链路依然断裂。

---

## 6. Cross-Reference: Related Runtime Observation

**附录位置:** 本段在 R1 evidence 主结论写完之后追加(2026-08-05),不动已有内容。

**存在另一条 R1 记录**(originSession `be3c0e91-5f29-49da-8490-f69a6396680c`):

- 路径:`~/.claude/projects/-Users-Zhuanz/memory/project_auction_p0_observation_r1_complete.md`
- 标签:Auction P0 Runtime Observation R1
- 状态:COMPLETE(Observation only, NOT remediation)
- Verdict:INSUFFICIENT EVIDENCE FOR ROOT CAUSE

**与本 R1 evidence 的关系:** Related Artifact(非 Same,非 Independent)。

| 维度 | 本 R1 evidence (CC / 6024287a) | be3c0e91 Observation R1 |
|---|---|---|
| evidence scope | 基线 artifact 维度:9 UA UNKNOWN 静态可达性 + SHA-256 重核 | runtime symptom + 5 反向候选根因 + production source drift 具体识别 |
| verdict 表述 | Partial Proven(carried) | INSUFFICIENT EVIDENCE FOR ROOT CAUSE |
| 未解项指向 | UA-F6 / UA-F9(部署状态 / 路径归属) | production `app/auction_data.py` 的 formatter / as_of 生成点 |
| next action | v0.3 Deployment Authorization Window(已 R1 Identity Decision 暂停) | Production Source Reconcile(PENDING HUMAN AUTHORIZATION) |

**互补维度,不可合并也非独立:**

- 本 R1 evidence 给出基线 artifact 维度(模块 resolve / 脚本覆盖 / code parity / SHA-256)
- be3c0e91 给出 runtime 现象维度(09:28 用户报告 / 5 反向排除 / production source drift 具体识别)
- 两条合起来构成完整的 R1 evidence 全景;任何一条缺失都会让 R1 失去一个观察维度

**R-02 命名提议:** be3c0e91 记录第 144 行提议命名 `R-02 Runtime Source Identity / Deployment Drift`。**本段不认证该命名进入 Case Registry**,理由见 `docs/reviews/R1_IDENTITY_DECISION.md` §4.4。

**v0.3 启动前置条件:** R1 Identity Decision 流程 Step 1/2/3 完成 + G 显式批准 scope。完整决策见 `docs/reviews/R1_IDENTITY_DECISION.md`。

---

**End of Round 1 Report**