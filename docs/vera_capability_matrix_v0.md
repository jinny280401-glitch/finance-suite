# Vera Capability Matrix v0 — 2026-06-12

## 来源

**本矩阵由 Vera Integration Audit Window A 摸底产出**,read-only 不修改任何源文件。
摸底路径:
- `~/.openclaw/agents/vera/skills/finance-suite/SKILL.md` (Vera 金融技能入口)
- `~/.openclaw/agents/vera/workspace/{AGENTS,SOUL,TOOLS,MEMORY,IDENTITY,CLAUDE}.md` (Vera 人格 + 运行规则)
- `~/.openclaw/agents/vera/skills/finance-suite/prompts/*.md` (8 个技能 prompt)
- `~/.openclaw/agents/vera/skills/finance-suite/references/{search-guidelines,search-patterns}.md`
- `~/finance-suite/scripts/{workflow_orchestrator,auction_data,macro_data,watchlist}.py` (finance-suite 主仓)
- 实战证据: Case 001 张雪机车 (G 提供截图)

## 矩阵 (8 行 × 4 列)

| 能力 | Finance Suite 有吗 | Vera 能调吗 | Integration 状态 |
|------|-------------------|-----------------|------------------|
| **通识问答** (例: "张雪机车是谁") | ❌ 不需 FS (GPT/Claude 自身) | ❌ **未路由** — 无 fallback 路径 | 🔴 **MISSING** |
| **个股研究 / 看票分析** | ✅ stock_analysis MCP + workflow_orchestrator | ✅ stock-analyst.md 触发 stock_analysis | 🟢 **FULL** (但仅交易视角) |
| **Morning Brief** | ✅ workflow_orchestrator.py --workflow morning-brief | ❌ **未集成** — SKILL.md 无 morning-brief 路由 | 🔴 **MISSING** |
| **Deep Research (行业/企业)** | ✅ research_runtime + deep-research prompt | ✅ deep-research.md 触发 search | 🟢 **FULL** (Tavily/Brave 实时检索) |
| **Market Pulse (集合竞价/涨停/异动)** | ✅ auction_data + market_pulse MCP | ✅ auction-analysis.md 触发 market_pulse + factor_scan | 🟢 **FULL** |
| **Trust Gate (Evidence → LLM)** | ✅ trust_gate_runtime_v0 + citation_contract_v0 | ⚠️ deep-research.md 显式标注 "来源 + 检索日期", 但**其他技能 (看票/宏观/集合竞价) 无强制 Evidence 输出** | 🟡 **PARTIAL** |
| **双版本输出 (Professional + Grandma)** | ✅ Engram 6/12 加 "奶奶级解释版" 设计 | ❌ **未集成** — Vera 8 个 prompt 均只输出专业版, 无双 render 路径 | 🔴 **MISSING** |
| **Evidence Traceability Tagline** | ✅ evidence_lineage_contract_v0 | ⚠️ deep-research.md 部分覆盖 (来源标注), 看票/宏观无统一 Tagline 格式 | 🟡 **PARTIAL** |
| **Intent Layer (Multi-Intent Routing)** | ✅ intent-layer-architecture-decision (P0 优先级) | ⚠️ Vera 有**关键词触发表**,但**无独立 Intent Layer**;Market Context / 通识 / Mixed Query 三类无路由 | 🟡 **PARTIAL** |

## 状态色含义

- 🟢 **FULL** — 端到端打通, 用户可消费
- 🟡 **PARTIAL** — 路径存在但有缺口 (部分技能覆盖 / 无统一格式)
- 🔴 **MISSING** — 能力在 FS 存在但 Vera 完全无路由, 或 FS 也缺失

## 关键发现 (Audit 阶段 1)

### 1. **通识问答 = 全空 (G 截图 Case 001 实证)**

Vera 当前路由表 (`finance-suite/SKILL.md` 技能路由) **完全没有"通识问答"或"未识别实体"fallback**。

**正确链路 (G 提议的四级降级):**
```
Finance Suite 有结果 → 用 FS 结果
否则 LLM 通识能力    → 直接答
再否则 主动搜索       → Tavily/Brave 检索
最后才是              → "我不知道"
```

**实际链路 (Vera 当前):**
```
Finance Suite 没命中 → 直接 "我不知道"
(无中间降级)
```

这正是 G 截图里"薇拉答'我没听过张雪机车'"的根因:**Agent Routing Failure,不是模型问题**。

### 2. **Morning Brief = 全空 (G 6/12 主要工作未消费)**

finance-suite 6/12 完成 Timeout Isolation Fix Window,workflow_orchestrator.py 修复完整。但 Vera 8 个 prompt 路由表**完全没有 morning-brief 路径**, SKILL.md 触发关键词也未包含"早报 / Morning Brief / 09:25 / 集合竞价早盘"等。

**结果:** Finance Suite 6/12 的工作**对薇拉不可见**。即使 9:25 brief 跑通, 用户也无法通过薇拉触发。

### 3. **Trust Gate 降级到 PARTIAL**

finance-suite 的 Trust Gate (trust_gate_runtime_v0 + citation_contract_v0) 设计完整。但 Vera 的 8 个 prompt:
- ✅ `deep-research.md` — 显式 "来源: [标题](URL), 检索日期" 标注 (符合 Citation Contract)
- ❌ `stock-analyst.md` / `auction-analysis.md` / `macro-advisor.md` / `mckinsey-report.md` — **未强制** Evidence 标注
- ❌ `video-breakdown.md` / `industry-report.md` / `stock-watcher.md` — 未摸底 (后续)

**G 担心命中:** "Vera 直接调 Provider 绕过 Trust Gate" — 实际不是直接绕过,而是**部分路径没强制**走 Trust Gate。

### 4. **Intent Layer 退化到 PARTIAL**

G 关心的问题 5: "科技早盘 → Intent → Morning Brief 还是 Vera → 直接 Prompt?"

实际看 SKILL.md 的"技能路由表"是**关键词匹配**机制 (无独立 Intent 路由层)。意味着:
- "科技早盘" = 关键词模糊, 可能路由失败或路由到错误技能
- "今天涨停怎么样" = "涨停" 关键词命中 → auction-analysis, 但如果用户想"早盘前听 brief"则意图不符
- **Market Context / Mixed Query 类** — 无路由

finance-suite 6/12 之前的 P0a.5 Intent Layer 架构决策 (Multi-Intent P0 优先级) **未在 Vera 落地**。

### 5. **双版本输出 = 全空 (Engram 6/12 决策无消费)**

Engram 6/12 新增的"专业版 + 奶奶级解释版"双 render 是 Engram 长期规则 (per `engram-lesson-format-rule`)。

但 Vera 8 个 prompt **全部只输出专业版**, 无 user_profile / persona 切换逻辑。即使 finance-suite 后端支持双 render, Vera 也无对应 prompt 模板。

**根因:** 双版本设计是**生成层**的策略 (Engram 规则), 而 Vera 是**消费层**的 agent — 两层之间无翻译协议。

## 5 问直接回答 (G 关心)

| G 关心 | 答案 | 证据 |
|--------|------|------|
| 1. 调用链是否打通 | ⚠️ **半通** — 5 技能打通 (看票/深度/宏观/麦肯锡/视频/集合竞价/自选), 2 项缺失 (Morning Brief / 通识 fallback) | SKILL.md 路由表 + Case 001 |
| 2. Trust Gate 是否保留 | ⚠️ **部分保留** — deep-research 显式标注来源, 其他 7 个 prompt 无强制 Evidence | `prompts/*.md` 抽样 |
| 3. 双版本输出是否实现 | ❌ **未实现** — 8 个 prompt 均只专业版 | `prompts/*.md` 抽样 |
| 4. Evidence Traceability 贯通 | ⚠️ **deep-research 部分贯通** — 其他技能无统一 Tagline | `prompts/*.md` 抽样 |
| 5. Intent Layer 接通 | ⚠️ **关键词路由,无独立 Intent 层** — Market Context/通识/Mixed Query 三类无路由 | SKILL.md 路由机制是关键词表 |

## 主问题改写 (per [[cc-a-infra-audit-verdict]] 经验)

```
旧: "Morning Brief 能不能上线?"
中: "Morning Brief 为什么没有价值?"
新 (Vera Audit v0): 
  "Finance Suite 能力如何被薇拉真正消费?"
  
答案 (Case 001 实证):
  - 5 能力 (看票/深度/宏观/麦肯锡/视频/集合竞价/自选) 已打通
  - 2 能力 (Morning Brief / 通识 fallback) 缺失
  - Trust Gate / Intent Layer / 双版本输出 三层防御部分缺失
  - 即使用户已经在用薇拉, 实际能消费的 Finance Suite 能力 < 50%
```

## 优先级建议 (本 Audit 阶段 1 输出)

**P0 必修 (阻断用户感知):**
- 🔴 **通识问答 fallback** — Case 001 类问题不再"我不知道" → LLM 自身通识 + 主动搜索兜底
- 🔴 **Morning Brief 路由** — Vera 触发"早报 / 集合竞价早盘"能正确路由到 workflow_orchestrator

**P1 应修 (质量降级):**
- 🟡 **Trust Gate 强制覆盖** — 看票/宏观/集合竞价 三个高频技能也强制 Evidence 标注
- 🟡 **Intent Layer 升级** — 关键词表 → Multi-Intent Router (P0a.5 架构决策落地)

**P2 优化 (用户分层):**
- 🟡 **Evidence Tagline 统一格式** — 全技能统一 "来源 + 检索日期 + 强度"
- 🔴 **双版本输出** — Persona 切换 (Professional / Grandma) 走 user_profile, 但 Engram 决策在生成层, 需先有 Vera 翻译协议

## Window A 边界 (本阶段)

- ✅ read-only 摸底 Vera-Agent 主目录 + finance-suite 主仓
- ✅ 输出 Capability Matrix v0 (本文件)
- ❌ 未修改任何源文件
- ❌ 未启动 Window B (5 场景 Integration Validation)
- ❌ 未启动 Case 001 修复 (只摸根因, 不在 Window A 修)

## 关联

- [[cc-a-infra-audit-verdict]] — 主问题改写范式
- [[cc-b-verdict-revoked-20260612]] — G 战略反转 (Audit 升 P0, Deploy 降 P1)
- [[cc-b-drill-pass-20260612]] — Morning Brief 修复未上 Vera (本 Audit 关键发现 #2)
- [[intent-layer-architecture-decision]] — Intent Layer 设计在 FS 存在, Vera 未落地
- [[workflow-fallback-contract]] — Trust Gate 三层防御, Vera 只部分覆盖
- [[engram-lesson-format-rule]] — 双版本输出 (Professional + Grandma) 在生成层有, 消费层无
