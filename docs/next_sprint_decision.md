# Next Sprint Decision — 2026-06-07

## 当前状态快照

| 项目 | 状态 |
|---|---|
| Trust Gate Runtime Sprint 2 | CLOSED |
| Meta Workflow | DESIGN FREEZE |
| Examples | DESIGN FREEZE |
| 市场温度计 Benchmark | 已提交 1992440 |
| macro_data fetcher | BUG CONFIRMED |

---

## 明天行程建议（G 排序）

上午：阅读 docs/market_temperature_github_benchmark.md
下午：CC 输出 docs/research_runtime_v1_gap_analysis.md
晚上：基于 Gap Analysis 选定下一条 Sprint

---

## 待选 Sprint（二选一）

| 选项 | 方向 |
|---|---|
| A. Research Runtime v1 | Evidence→Trust Gate→Workflow→Section→Artifact 主链路闭环 |
| B. Market Context v1 | 市场温度计结构化指标块接入 |
| C. Workflow Runtime v0 | 编排层骨架 |
| D. Macro Data Freshness Fix | GDP/CPI/PMI 取值修复（READY，Medium priority） |

**G 投票：Research Runtime v1**
理由：Trust Gate 地基已打好，最自然的演进是把主链路真正闭环。

---

## Macro Data Freshness Fix — 独立小 Sprint

**Status: READY**
**Priority: Medium**

验收标准：
1. GDP 不再取 2007 年数据
2. CPI 不再取旧窗口
3. 所有宏观指标按日期排序后取最新窗口
4. 增加 smoke 覆盖

不进当前 Sprint，另开独立任务时执行。

---

## 冻结项

Sidebar UI — 冻结（原因：现阶段缺的是 Runtime/Market Context/Workflow，不是 UI）
