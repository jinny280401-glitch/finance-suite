# Case 001 — 张雪机车 Agent Routing Failure 追溯

## 背景 (G 提供截图)

**用户问题 (WeChat 14:20):**
> 我考虑要接的是张雪机车的老股，天使轮的，按50亿估值接手，合适吗?

**薇拉回答:**
> 俊哥，说实话，我没有听过张雪机车这家公司。
> 这个名字听起来像是做电动摩托、智能出行或者机车相关的...
> (列出九号公司/小牛/雅迪/极核虬龙)
> ...
> 建议: 查工商信息/看业务数据/问行业的人

**豆包回答 (对照组):**
> 张雪机车天使轮老股、50亿估值接手: 结论先行——极度不划算, 风险极高
> 1. 核心估值矛盾: A轮仅10.9亿, 50亿属于短期泡沫
> 2. 估值性质: 只是市场传闻"有机构意向报价", 没有真实资金
> 3. 跨轮次估值严重倒挂...

## 根因 (5 层追溯)

### 第 1 层: 路由 (Vera SKILL.md 关键词匹配)

**Vera 路由表 (finance-suite/SKILL.md):**
| 触发关键词 | 技能 |
|-----------|------|
| 看票/分析XX股票/个股/XX能买吗 | 看票分析 (stock-analyst.md) |
| ... | ... |

**用户 query 拆解:**
- 实体: "张雪机车" — Vera 不识别 (无 FS 数据)
- 关键词: "老股" + "估值" + "接手" + "合适吗" — **命中 "估值/合适/分析" 触发 stock-analyst**

**根因 #1:** 关键词路由把"张雪机车"误判为 stock-analyst 案例, 但实际是 **mixed query (通识实体 + 估值分析)**。

### 第 2 层: 数据 (stock_analysis MCP 调用)

Vera 触发 stock-analyst → 调 `stock_analysis(query="张雪机车")` (来自 MCP server `mcp__finance-suite__stock_analysis`)

**预期行为:** AkShare 找 A 股 → 找不到"张雪机车" → 返 `_qc.status=failure, completeness=0, missing_dimensions=[code, name]`

**实际行为:** Vera 收到 stock_analysis 失败结果 → **没有 fallback 路径**

**根因 #2:** stock-analyst prompt 没写"数据缺失时怎么办", Vera 不知道下一步。

### 第 3 层: 降级 (search-guidelines.md 的三级降级**未触发**)

**关键发现:** `skills/finance-suite/references/search-guidelines.md` **已经定义了三级降级**:

```
第一级: 数据充分 → 正常输出
第二级: 数据有限 → 部分输出 + 标注 "基于有限搜索结果"
第三级: 搜索失败 → 显著提示 "实时数据获取失败, 基于模型训练知识, 建议稍后重试"
```

**但 Case 001 没走任何一级降级。** Vera 直接说"我不知道",跳过了所有降级。

**根因 #3:** `search-guidelines.md` 只在**主动调 search 工具时**适用。当 stock-analyst 没主动调 search,降级策略不生效。**降级策略与 stock-analyst 流程未联通**。

### 第 4 层: 主动搜索 (Tavily/Brave 未触发)

TOOLS.md 列了: "数据源: AkShare (东方财富) / Tavily / Brave"。

**但 stock-analyst.md prompt 没强制** 在 stock_analysis 失败时调 Tavily/Brave 主动搜索。

**正确行为:** stock_analysis 失败 → 自动触发 `search(query="张雪机车 估值 50亿", search_type="stock")` → 用搜索结果回答

**根因 #4:** Vera prompt 模板**未集成** search-guidelines 的"搜索失败 → Tavily 兜底" 流程。

### 第 5 层: 兜底 (LLM 自身通识能力未启用)

LLM (Claude Code) 自身**有**通识知识。"张雪机车"作为知名机车品牌, Claude 训练数据中应有涉及。

**但 stock-analyst prompt 把 Vera 锁死在"金融分析师"人设里**, 人设 + 数据缺失 → "我不知道"。

**正确行为:** 数据/搜索都失败 → 启用 LLM 通识 + search-guidelines 第三级提示 "以下基于模型训练知识, 可能不反映最新情况"

**根因 #5:** Vera 缺"通识 fallback"路由。即使前面所有层都失败, 也没有"启用 LLM 自身通识能力 + 标注"的兜底路径。

## 根因汇总

```
用户: "张雪机车 50亿估值 合适吗"
   ↓
Layer 1 路由: 关键词"估值/合适" → 误判 stock-analyst (实际 mixed query)
   ↓
Layer 2 数据: stock_analysis MCP 返 _qc.failure (AkShare 找不到)
   ↓
Layer 3 降级: search-guidelines 三级降级**未触发** (因为没调 search)
   ↓
Layer 4 主动搜索: Tavily/Brave 未自动兜底 (prompt 没强制)
   ↓
Layer 5 兜底: LLM 通识能力**未启用** (人设锁死)
   ↓
最终回答: "我没听过张雪机车这家公司"
```

**根因本质 (G 提议的四级降级链):**
```
Finance Suite 有结果 → 用 FS       [Layer 2 数据]      ❌ 未命中 (AkShare 找不到)
否则 LLM 通识能力  → 直接答        [Layer 5 兜底]      ❌ 未启用 (人设锁死)
再否则 主动搜索    → Tavily/Brave  [Layer 4 搜索]      ❌ 未触发
最后才是            → "我不知道"   [Vera 当前]    ✅ 命中 (但前 3 级全跳)
```

## Vera 当前 vs 应有降级链

| 降级级别 | 应有行为 | 实际行为 | 差距 |
|----------|---------|---------|------|
| L1: Finance Suite | `stock_analysis` 返结果 → 输出 | 返 None, 死路 | ❌ 数据失败没标记 |
| L2: LLM 通识 | 数据空 → 直接答"虽然 FS 没数据, 但我知道..." | 完全跳过, 直接 "我不知道" | ❌ 通识未启用 |
| L3: 主动搜索 | 提示 "数据不足, 我搜一下" → Tavily 调 | 没调, 直接放弃 | ❌ 搜索未集成到 stock-analyst |
| L4: "我不知道" | 兜底, 承认不知道 | ✅ 命中 | 🟢 命中, 但前 3 级全跳 |

**问题:** L1 失败 → 直接跳 L4, L2/L3 **整层缺失**。

## 与豆包的对比 (G 提供对照组)

| 维度 | 豆包 | 薇拉 (Vera) |
|------|------|-------------------|
| 是否知道张雪机车 | ✅ 知道 (A轮10.9亿/赛事夺冠/情绪炒作) | ❌ 不知道 (AkShare 找不到) |
| 是否做估值分析 | ✅ 有结论 (极度不划算/风险极高) | ❌ 跑题 (列九号/小牛/雅迪) |
| 知识来源 | 通识 + 主动搜索 | 仅 Finance Suite 数据 |
| 失败处理 | 通识兜底 | 直接放弃 |

**核心差距:** 豆包有 L2/L3 (通识+主动搜索), 薇拉只有 L4 ("我不知道")。

## 修复方向 (本 Case 001 不修, 写给 Window B 决策)

**最小修复 (单点 Case 001):**
- 改 `prompts/stock-analyst.md`: 加 "stock_analysis 失败 → 触发 Tavily search 兜底" 强制流程

**根治修复 (Case 001 + Case N):**
- 在 `references/search-guidelines.md` 加 **第四级降级**: "通识 fallback — 当 search 也失败, 基于模型训练知识回答 + 显著提示"
- 在 `finance-suite/SKILL.md` 加 **通识问答路由** (兜底层): "无关键词命中 → 走 LLM 通识 + Tavily 自动搜索"
- 在 `workspace/AGENTS.md` 加 **Agent Routing Failure 防御规则**: "禁止在 L1/L2/L3 失败前说'我不知道'"

## 状态

- ✅ 根因定位: 5 层追溯完成
- ✅ 与 G 四级降级链对齐: 缺 L2/L3, 过度依赖 L4
- ⏸ **不在 Window A 修** — 修属于 Window B (Integration Validation) 范围
- ⏸ 下一条: Window B 设计 5 场景验证 (含张雪机车变体), 测修复效果

## 引用

- [[vera_capability_matrix_v0]] — 矩阵中 8 行能力的 PARTIAL/MISSING 状态来源
- [[workflow-fallback-contract]] — FS 侧的三级降级契约, Vera 未对齐
- [[intent-layer-architecture-decision]] — Multi-Intent Router, 本 Case 缺路由层是根因 #1
- [[cc-b-drill-pass-20260612]] — 类似诊断范式 (Drill 证伪旧因果链, Audit 找新盲点)
