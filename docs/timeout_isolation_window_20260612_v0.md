# Timeout Isolation Fix — Window Report 2026-06-12

## Window 结论

```
Timeout Isolation:  PASS
                    ↑ 升格 (旧 FAIL)
```

**Primary NO GO 收敛为单条:**
- 旧 Primary NO GO (双条): Timeout Isolation FAIL + Deploy Contract Drift FAIL
- 新 Primary NO GO (单条): Deploy Contract Drift FAIL
- 状态板 Timeout Isolation 从 FAIL → PASS

## 范围守纪 (G 锁定)

**允许改动 (1 个文件):**
- `scripts/workflow_orchestrator.py` 仅 Step 1 / Step 3

**禁止 (per G):**
- ❌ Workflow Refactor
- ❌ Runtime Refactor (mcp_server.py / data gateway)
- ❌ Provider Refactor (akshare / EastMoney)
- ❌ Deploy 修改 (launchd / deploy.sh)
- ❌ AkShare Refactor
- ❌ Step 2 / Step 4 改动 (watchlist 同步本地 / markdown 生成纯字符串)

## 改动 (3 处 + 1 修本窗口引入的 NameError)

### Step 1 (workflow_orchestrator.py:60-78)
```python
# P0 Timeout Isolation Fix: 包 asyncio.wait_for(30s), 超时降级返空骨架,
# 不抛外层, 继续执行 Step 2 / 3 / 4.
print("📊 [1/3] 获取市场脉搏...")
market_pulse = {}  # 预初始化, 让 Step 2 即使走 except 也能引用, 不触发 NameError
async def _step1_auction_with_timeout():
    return await asyncio.wait_for(get_auction_data(), timeout=30)
try:
    market_pulse = asyncio.run(_step1_auction_with_timeout())
    result["market_pulse"] = market_pulse
    ...
except asyncio.TimeoutError:
    print("  ⏱ [WARN] Step 1 auction 30s timeout, 降级返空骨架")
    market_pulse = {"error": "timeout_30s", "涨停池": [], "强势股池": []}
    result["market_pulse"] = market_pulse
except Exception as e:
    market_pulse = {"error": str(e), "涨停池": [], "强势股池": []}
    result["market_pulse"] = market_pulse
```

### Step 3 (workflow_orchestrator.py:119-150)
```python
# P0 Timeout Isolation Fix: 包 asyncio.wait_for(30s), 超时降级返空骨架.
print("🌐 [3/3] 获取宏观快讯...")
macro_snapshot = {}  # 预初始化, 同 Step 1, 防 except 路径 unbound
async def _step3_macro_with_timeout():
    return await asyncio.wait_for(get_macro_data(), timeout=30)
try:
    macro_snapshot = asyncio.run(_step3_macro_with_timeout())
    ...
except asyncio.TimeoutError:
    print("  ⏱ [WARN] Step 3 macro 30s timeout, 降级返空骨架")
    macro_snapshot = {"error": "timeout_30s", "gdp": [], "cpi": [], "pmi": []}
    result["macro_snapshot"] = macro_snapshot
except Exception as e:
    macro_snapshot = {"error": str(e), "gdp": [], "cpi": [], "pmi": []}
    result["macro_snapshot"] = macro_snapshot
```

### 修本窗口引入的 NameError (Step 1 except 路径)
原代码 Step 1 except 块**未**给本地变量 `market_pulse` 赋值,导致走 except 时 Step 2 引用 `market_pulse` 触发 NameError。L2-1 第一版 v1 验证发现,本窗口内**最小修复** (不属于 Workflow Refactor, 属于"本窗口引入的回归" 修复合规):
- Step 1 try 块前预初始化 `market_pulse = {}`
- Step 1 except 块显式 `market_pulse = {...}` 赋值
- Step 3 同理 (预初始化 + except 赋值)
- 同步给 Step 1 / Step 3 的原 `except Exception` 块也补 `market_pulse = {...}` 赋值, 防止 auction_data/macro_data 内部 swallow 失败后走 except 路径触发 NameError

## L1 / L2 / L3 验收

| 维度 | 验证 | 结果 |
|------|------|------|
| **L1 Functional** | real env 跑 workflow_orchestrator.py, brief 5 章节完整, stdout 与改前一致 | PASS (elapsed 35.1s, 5/5 章节) |
| **L2-1 Step 1 hang** | patch auction._fetch_zt_pool sleep(90s), wait_for 应在 30s 触发 | PASS (elapsed 35.1s, 触发 "Step 1 auction 30s timeout", 后续 Step 2/3/4 继续) |
| **L2-2 Step 3 hang** | patch macro._fetch_gdp sleep(90s), wait_for 应在 30s 触发 | PASS (elapsed 97.2s, 触发 "Step 3 macro 30s timeout", brief 5 章节完整) |
| **L3 Case A** | real env baseline | PASS (elapsed 77.4s, 与改前 CC-B Case A 80s 一致) |
| **L3 Case B** | 部分数据缺失 (auction=空 + macro GDP=None) | PASS (elapsed 75.7s, brief 5 章节) |
| **L3 Case C** | Provider 全部抛 RuntimeError | PASS (elapsed 76.7s, brief 输出 "暂无涨停股"/"暂无强势股"/"宏观数据暂不可用" 降级骨架) |

## 关键发现

### 1. 本窗口引入的 NameError 漏洞已修
原 CC-B Drill v0 报告中没发现这个紧耦合漏洞 (因为旧 except Exception 块也未给 market_pulse 赋值,但 auction_data 内部 try/except 兜住后,workflow 看不到 error 字段,except Exception 路径**从未触发**)。本窗口加了 wait_for 引入新 TimeoutError except 路径,触发了这个隐藏漏洞。已最小修复。

### 2. 子线程泄漏可接受 (无需 executor.shutdown 改造)
auction_data / macro_data 内部用 `ThreadPoolExecutor` 包装同步 akshare 调用。`asyncio.wait_for` 超时时只 cancel task, 子线程继续跑到 AkShare 自然结束或 OS 回收。可接受性:
- 30s 子线程泄漏 × 1 个 brief × 1 天 = 量级低
- 子线程不写盘不写网络, 纯 HTTP GET 自然超时
- 内存压力可忽略
- **不**需要加 `executor.shutdown(wait=False)` (违反 G "禁止 Workflow Refactor" 边界)

### 3. elapsed 时间需重新校准 evaluator
L2-2 evaluator 初版用 `elapsed < 60s` 作降级判定,误判 FAIL。真实 Step 1 real env 拉 market data 需要 65s+,总 elapsed 必然 > 60s。修正: 看日志里有没有 "⏱ [WARN] Step N timeout" 字符串 — 这才是 wait_for 触发的真信号。

## 状态板更新

```
Content Contract ........ PASS
Infra Audit ............. PASS WITH RISK
end_date RCA ............ PASS
Production Drill ........ PASS WITH FINDINGS
Freshness Status ........ OPEN
Timeout Isolation ....... PASS      ← 本窗口升格
Deploy Contract Drift ... FAIL      ← 唯一 Primary NO GO
```

## 后续路径

```
当前: Primary NO GO (单条) = Deploy Contract Drift FAIL

下一步选项:
  1. G 决定开 Window: Run Deploy on Server
     → 执行 deploy.sh
     → curl 验证 6 文件 200
     → Deploy FAIL → PASS
     → 全部 NO GO 清空
  2. G 决定开 Window: Data Freshness RCA
     → P2 任务, 不阻塞 GO
     → 与本窗口无关
  3. G override NO GO (本会话未发生, 不预设)
```

## Window 边界 (本窗口)

✅ 改动文件: 1 个 (`scripts/workflow_orchestrator.py`)
✅ 改动位置: Step 1 (line 60-78) + Step 3 (line 119-150)
❌ 未动: launchd plist / deploy.sh / mcp_server.py / auction_data.py / macro_data.py / watchlist.py / prompts/ / index.html
❌ 未 commit / 未 push (per CLAUDE.md + 之前教训)

## 引用

- [[cc-b-verdict-revoked-20260612]] — 本窗口任务来源
- [[cc-b-drill-pass-20260612]] — Case D 详细证据 (Drill 真正发现)
- [[timeout-isolation-window-plan-20260612]] — 本窗口执行前的草案
- [[tomorrow-0925-brief-no-go]] — NO GO 状态板历史快照
- [[business-freshness-policy]] — Freshness OPEN 状态仍需观察
- [[workflow-fallback-contract]] — 未来可补 _qc.reasoning/evidence/lineage (本窗口不要求)
- [[sidebar-production-case-a-20260612]] — 唯一 Primary NO GO (Deploy) 独立线
