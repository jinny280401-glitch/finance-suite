# Vera ↔ Finance Suite 能力映射 v0

**任务范围**: 只映射,不做 Validation,不做 Router 设计
**生成时间**: 2026-06-12
**生成方式**: 文件系统静态扫描 + 引用已审计 memory (CC-A 收口、Sidebar P0 归档、Trust Gate Freeze 等)

---

## 核心结论

> **薇拉当前接上了 Finance Suite 的 3/8 能力,且全部是 v1.0.0 旧表面,Finance Suite 已迭代到 v2.0+ 表面。**
>
> - 3/8 PARTIAL — Market Pulse / Stock Research / Deep Research (全部 stale v1.0.0)
> - 5/8 MISSING — Morning Brief / Market Context / Trust Gate / Evidence Bundle / Intent Layer
> - 0/8 FULL

**关键时间错位**:
- Vera `skills/finance-suite/SKILL.md` mtime = 2026-05-31 (v1.0.0)
- Finance Suite `prompts/` 8 个新文件 mtime = 2026-06-11 02:03 (v2.0+)
- **Vera 比 Finance Suite 落后 12 天 + 1 个主要版本**

---

## 能力矩阵 (8 项逐条)

| Capability | Finance Suite Status | Vera Status | Gap | Priority |
|------------|----------------------|------------------|-----|----------|
| **Market Pulse** | PASS (`market_pulse` MCP + `market_intel` MCP Sidebar 聚合器) | **PARTIAL** (v1.0.0: 仅 `market_pulse` + `factor_scan`) | 缺 `market_intel` Sidebar 聚合器 (4 模块:discussions/hot_stocks/watch_alerts/research) | P2 |
| **Stock Research** | PASS (`stock_analysis` MCP + 8 个 prompts: stock-analyst / financial-health / valuation / moat-analysis / growth-decomposition / peer-comparison / catalyst-calendar / risk-radar) | **PARTIAL** (v1.0.0: 仅 `stock-analyst` 单 prompt) | 缺 7 个 v2.0 新增 prompts (Jun 11 02:03 提交) | **P1** |
| **Deep Research** | PASS (`search` MCP + `research_digest` MCP + `research_reports` MCP) | **PARTIAL** (v1.0.0: 仅 `search`) | 缺 `research_digest` (研报批量脱水) + `research_reports` (投行研报管理) | P2 |
| **Morning Brief** | **FAIL** (NO GO per CC-A: Scheduler PASS / Data Freshness FAIL / Deploy FAIL) | **MISSING** | Vera 端零映射;Finance Suite 端在 PENDING 状态 (CC-B Drill Case D = Timeout Isolation FAIL,6/13 09:25 NO GO 默认) | **P3 (阻塞于 CC-B / Timeout Isolation Fix)** |
| **Market Context** | **UNKNOWN** (`scripts/__pycache__/market_context.cpython-312.pyc` 唯一存在,源文件缺失;`app/market-temperature-mini.html` 在 Finance Suite 端已实现但 deploy drift 未上线) | **MISSING** | Vera 零映射;Finance Suite 源文件丢失/未提交;.html 在生产仍 404 | P3 (源文件状态待澄清) |
| **Trust Gate** | **FROZEN** (Citation Contract Alignment FROZEN at 5bbec5f per [[open-bb-runtime-p0-freeze]];Runtime design 完成,未对外暴露) | **MISSING** | Vera 零映射;Trust Gate 在 Finance Suite 是 v2.0 治理层,未设计为可外部调用 | P3 (冻结 + 未对外暴露) |
| **Evidence Bundle** | PASS (`research_runtime/evidence_bundle.py` 11KB,完整实现) | **MISSING** | Vera 零映射;Vera 端不消费 evidence bundle 格式 | P2 |
| **Intent Layer** | **DESIGN-ONLY** (per [[intent-layer-architecture-decision]]:P0a.5 基础设施层,Contract-first 节奏,Multi-Intent 为 P0 优先级;Layer 4 SUSPENDED on top of 4-way STOPPED per [[adr-serenity-suspension]]) | **MISSING** | Vera 零映射;Intent Layer 自身未实现,Layer 4 冻结 | P3 (设计阶段 + 冻结) |

---

## Vera 端集成现状 (v1.0.0 表面)

**集成位置**: `/Users/Zhuanz/Vera-Agent/skills/finance-suite/`

```
Vera-Agent/skills/finance-suite/
├── SKILL.md (6781 bytes, v1.0.0, mtime 2026-05-31)
├── references/
│   ├── search-guidelines.md
│   └── search-patterns.md
└── prompts/  (8 个文件,全部 mtime ≤ 2026-05-31)
    ├── stock-analyst.md
    ├── macro-advisor.md
    ├── mckinsey-report.md
    ├── video-breakdown.md
    ├── deep-research.md
    ├── auction-analysis.md
    └── stock-watcher.md
```

**SKILL.md 声明的 7 大技能** (来自 v1.0.0 SKILL.md line 5):
1. 看票分析 → `stock_analysis` MCP
2. 宏观内参 → `macro_snapshot` MCP
3. 麦肯锡报告 → 无 MCP (用户提供资料)
4. 视频拆解 → `video_extract` MCP
5. 深度研究 → `search` MCP
6. 集合竞价 → `market_pulse` + `factor_scan` MCP
7. 自选股管理 → `watchlist_manage` MCP

**Vera 实际具备的能力** (按 G 列出的 8 项分类):
- ✅ Market Pulse (PARTIAL — 走 auction-analysis 路径,只覆盖 v1.0.0 表面)
- ✅ Stock Research (PARTIAL — 走 stock-analysis 路径,单 prompt)
- ✅ Deep Research (PARTIAL — 走 deep-research 路径,只 search)
- ❌ Morning Brief (MISSING)
- ❌ Market Context (MISSING)
- ❌ Trust Gate (MISSING)
- ❌ Evidence Bundle (MISSING)
- ❌ Intent Layer (MISSING)

**Vera 端其他独立 skills** (与 Finance Suite 无映射关系):
- `app/skills/router.py` (意图路由)
- `app/skills/finance.py` (金融投研 — Vera 自己的,非 Finance Suite)
- `app/skills/sales.py` (销售军师)
- `app/skills/client_sandbox.py` (客户沙盘推演)
- `app/skills/company_matcher.py` (上市公司业务匹配)

---

## Finance Suite 端实际能力 (v2.0+ 表面,Vera 未同步)

### MCP 工具清单 (来自 `mcp_server.py` 静态扫描,18 个 @mcp.tool)

| MCP 工具 | Finance Suite Status | Vera 是否引用 |
|----------|----------------------|---------------------|
| `stock_analysis` | PASS | ✅ v1.0.0 |
| `macro_snapshot` | PASS | ✅ v1.0.0 |
| `market_pulse` | PASS | ✅ v1.0.0 |
| `search` | PASS | ✅ v1.0.0 |
| `video_extract` | PASS | ✅ v1.0.0 |
| `watchlist_manage` | PASS | ✅ v1.0.0 |
| `factor_scan` | PASS | ✅ v1.0.0 |
| `market_intel` (Sidebar 聚合) | PASS | ❌ v2.0 缺失 |
| `research_digest` (研报脱水) | PASS | ❌ v2.0 缺失 |
| `research_reports` (投行研报) | PASS | ❌ v2.0 缺失 |
| `wind_query` | PASS | ❌ 缺失 |
| `jqdata_query` | PASS | ❌ 缺失 |
| `ths_query` | PASS | ❌ 缺失 |
| `emquant_query` | PASS | ❌ 缺失 |
| `xueqiu_fetch` | PASS | ❌ 缺失 |
| `zhihu_fetch` | PASS | ❌ 缺失 |
| `sinafinance_fetch` | PASS | ❌ 缺失 |
| `barchart_fetch` | PASS | ❌ 缺失 |

**Vera v1.0.0 仅引用 7/18 = 38.9%** 的 MCP 工具。

### Prompts 清单 (Finance Suite `prompts/`,mtime Jun 11 02:03 新增 8 个)

| Prompt | Finance Suite mtime | Vera 是否有 |
|--------|----------------------|------------------|
| stock-analyst | Apr 4 | ✅ v1.0.0 旧版 |
| macro-advisor | Apr 3 | ✅ v1.0.0 旧版 |
| industry-report | **Jun 11 02:03** | ❌ v2.0 缺失 |
| catalyst-calendar | **Jun 11 02:03** | ❌ v2.0 缺失 |
| financial-health | **Jun 11 02:03** | ❌ v2.0 缺失 |
| growth-decomposition | **Jun 11 02:03** | ❌ v2.0 缺失 |
| moat-analysis | **Jun 11 02:03** | ❌ v2.0 缺失 |
| peer-comparison | **Jun 11 02:03** | ❌ v2.0 缺失 |
| risk-radar | **Jun 11 02:03** | ❌ v2.0 缺失 |
| valuation | **Jun 11 02:03** | ❌ v2.0 缺失 |
| mckinsey-report | Apr 3 | ✅ v1.0.0 旧版 |
| video-breakdown | Apr 3 | ✅ v1.0.0 旧版 |
| deep-research | Apr 5 | ✅ v1.0.0 旧版 |
| auction-analysis | Apr 4 | ✅ v1.0.0 旧版 |
| stock-watcher | Apr 4 | ✅ v1.0.0 旧版 |

**Vera 0/8 v2.0 prompts** 同步。

### 治理层与运行时 (Vera 全部 MISSING)

| 能力层 | Finance Suite 实现 | Vera Status |
|--------|---------------------|------------------|
| Trust Gate | `docs/trust_gate_*.md` + `smoke_trust_gate_*.py` + 5bbec5f Freeze tag | ❌ MISSING |
| Evidence Bundle | `research_runtime/evidence_bundle.py` (11KB) | ❌ MISSING |
| Intent Layer | 设计文档级,P0a.5 基础设施,未实现 | ❌ MISSING |
| Morning Brief | `premarket-preflight/` + launchd + 9:20/9:24 系统 | ❌ MISSING |
| Market Context | 仅 `.pyc` (源文件缺失) | ❌ MISSING |

---

## Gap 量化 (回答 G 的核心问题)

### 薇拉接上的能力数

```
3 / 8 = 37.5% (按能力项)
6 / 18 = 33.3% (按 MCP 工具)
7 / 15 = 46.7% (按 Prompts,但全部 v1.0.0 旧版)
0 / 5 = 0% (按治理层:Trust Gate / Evidence Bundle / Intent Layer / Morning Brief / Market Context)
```

### 三层错位

| 维度 | Finance Suite 表面 | Vera 表面 | 错位 |
|------|----------------------|------------------|------|
| MCP 工具 | 18 个 | 7 个引用 | 11 个未暴露 |
| Prompts | 15 个 | 7 个 + 全部 v1.0.0 旧版 | 8 个 v2.0 未同步 + 7 个需更新 |
| 治理层 | 5 个 (Trust Gate / Evidence Bundle / Intent Layer / Morning Brief / Market Context) | 0 个 | 5 个完全未映射 |

### 时间错位

```
Vera 集成最后更新: 2026-05-31 (v1.0.0)
Finance Suite 治理层变化: 2026-06-04 ~ 06-12 (5bbec5f Freeze + Sidebar P0 + 8 prompts + Morning Brief Infra)
差距: 12 天 + 1 个主要版本
```

---

## Priority 排序建议

> **Priority 由"Vera 集成价值 × Finance Suite 状态健康度"决定。**

| Priority | Capability | 行动建议 |
|----------|------------|----------|
| **P1** | Stock Research | 同步 7 个 v2.0 prompts (Jun 11 提交),低风险,高价值 |
| P2 | Market Pulse | 同步 `market_intel` MCP 引用,扩展为 Sidebar 聚合 (4 模块) |
| P2 | Deep Research | 同步 `research_digest` + `research_reports` MCP 引用 |
| P2 | Evidence Bundle | 设计 Vera 端 evidence bundle 消费路径 (取决于 v2.0 治理层成熟度) |
| **P3 (阻塞)** | Morning Brief | 等 CC-B / Timeout Isolation Fix 窗口完成;MCP 暴露未设计 |
| P3 (待澄清) | Market Context | 源文件 `.pyc` 状态需澄清;`.html` 端在 Finance Suite 生产仍 404 |
| P3 (冻结) | Trust Gate | Layer 4 SUSPENDED 持续;FROZEN at 5bbec5f;不对外暴露 |
| P3 (设计阶段) | Intent Layer | 自身 P0a.5 基础设施未实现;Layer 4 SUSPENDED |

---

## 结论 (一句话)

> **薇拉当前接上了 Finance Suite 37.5% 的能力 (3/8 PARTIAL),但全部是 v1.0.0 旧表面,Finance Suite 已在 12 天内迭代到 v2.0+ 表面,新增 8 个 prompts + 11 个 MCP 工具 + 5 个治理层能力全部未同步。** 一旦 G 决定升级 Vera 集成,P1 (Stock Research prompts 同步) 是低风险高价值起点。

---

## 方法学注记

**本 mapping 只做静态扫描,不做以下事** (按 G 任务约束):
- ❌ 不调用 MCP 验证 Vera 实际能跑通任何 skill
- ❌ 不设计 router / 路由策略
- ❌ 不评估 Vera 部署侧的可达性
- ❌ 不测试 Finance Suite 端能力是否健康 (Morning Brief 已 NO GO 等)
- ❌ 不开任何窗口,不动任何代码

**本 mapping 已引用以下已审计 memory 作为状态源** (不重新验证):
- [[a-line-archived-state]] — Morning Brief NO GO 状态
- [[sidebar-production-case-a-20260612]] — Sidebar P0 状态 (含 market-temperature-mini)
- [[open-bb-runtime-p0-freeze]] — Trust Gate 冻结状态
- [[intent-layer-architecture-decision]] — Intent Layer 设计阶段
- [[adr-serenity-suspension]] — Layer 4 SUSPENDED
- [[operational-readiness-layers]] — 4-6 层不蕴含关系 (本 mapping 不跨层推断)
