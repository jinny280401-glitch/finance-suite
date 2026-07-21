# Vera Integration Audit — Window A 收口 (2026-06-12)

## Window A 结论

```
Vera Integration Audit Window A
STATUS
  CLOSED (v0)
RESULT
  Capability Matrix v0  ✅ 出
  Case 001 张雪机车    ✅ 5 层根因追溯完成
  Window B 设计         ⏸ 等 G 显式开
```

## 关键结论 (一句话)

**Vera 当前能消费的 Finance Suite 能力 < 50%, 缺通识 fallback + Morning Brief 路由 + Intent Layer + 双版本输出, Case 001 张雪机车 = 5 层 Routing Failure 实证。**

## 优先级反转 (G 决策)

```
旧:  P0 Deploy Contract Drift / P1 Vera Audit
新:  P0 Vera Integration Audit / P1 Deploy Contract Drift
```

**理由 (G):** "用户已经在用薇拉, 但薇拉没有消费能力层" — 这比 Morning Brief 不能上线**风险更大**(用户已经在受影响)。

## Window A 产出 (3 个文件)

1. `docs/vera_capability_matrix_v0.md` — 8 行 × 4 列矩阵
2. `docs/vera_case_001_zhangxue_20260612.md` — 5 层根因追溯
3. `docs/vera_audit_window_a_20260612_v0.md` — 本文件 (Window A 收口)

## Capability Matrix v0 摘要

| 能力 | FS 有吗 | Vera 能调吗 | 状态 |
|------|---------|----------------|------|
| 通识问答 | ❌ 不需 | ❌ 未路由 | 🔴 MISSING |
| 个股研究 | ✅ | ✅ | 🟢 FULL |
| Morning Brief | ✅ | ❌ 未集成 | 🔴 MISSING |
| Deep Research | ✅ | ✅ | 🟢 FULL |
| Market Pulse | ✅ | ✅ | 🟢 FULL |
| Trust Gate | ✅ | ⚠️ 部分 | 🟡 PARTIAL |
| 双版本输出 | ✅ (Engram) | ❌ | 🔴 MISSING |
| Evidence Tagline | ✅ | ⚠️ deep-research 覆盖 | 🟡 PARTIAL |
| Intent Layer | ✅ (FS 侧) | ⚠️ 关键词路由 | 🟡 PARTIAL |

**统计:** 🟢 3 FULL / 🟡 3 PARTIAL / 🔴 3 MISSING

## Case 001 张雪机车 根因 (5 层)

| 层 | 应有行为 | 实际行为 |
|----|---------|---------|
| L1 路由 | 识别 mixed query | 误判 stock-analyst |
| L2 数据 | stock_analysis 失败有标记 | 失败但没标记 |
| L3 降级 | search-guidelines 三级降级触发 | 未触发 (没调 search) |
| L4 主动搜索 | Tavily/Brave 自动兜底 | 未集成到 prompt |
| L5 通识兜底 | LLM 自身知识启用 | 人设锁死, 直接"我不知道" |

**根因本质:** L1 失败 → 直接跳 L5 ("我不知道"), L2/L3/L4 **整层缺失**。

**与 G 提议的四级降级链对齐:**
```
FS 有结果 → 用 FS       [L1 数据]      ❌ 未命中
否则 LLM 通识 → 直接答  [L5 兜底]      ❌ 未启用
再否则 主动搜索         [L4 搜索]      ❌ 未触发
最后才是 "我不知道"      [Vera]    ✅ 命中, 但前 3 级全跳
```

## 主问题改写

```
旧 (CC-A): "Morning Brief 能不能上线?"
中 (CC-A): "Morning Brief 为什么没有价值?"
新 (Vera Audit v0):
  "Finance Suite 能力如何被薇拉真正消费?"
  
答案:
  - 5 能力已打通 (看票/深度/宏观/麦肯锡/视频/集合竞价/自选)
  - 2 能力缺失 (Morning Brief / 通识 fallback)
  - 3 能力部分 (Trust Gate / Intent Layer / Evidence Tagline)
  - 1 能力未实现 (双版本输出)
  - 即使用户已经在用薇拉, 实际可消费 FS 能力 < 50%
```

## Window B 建议 (等 G 显式开)

**目标:** 5 场景端到端 Integration Validation, 验证修复效果

**5 场景草案 (G 已提议,需 G 确认):**
1. **科技早盘** — Intent Layer + Morning Brief 集成 (FS 新能力未消费)
2. **贵州茅台怎么样** — 看票 + Evidence Tagline (已有路径, 验 Trust Gate 完整性)
3. **今天热点是什么** — Market Pulse + 涨停池/异动 (已有路径, 验数据流)
4. **市场温度如何** — 跨技能聚合 (Market Pulse + 宏观 + 自选)
5. **给奶奶解释一下** — 双版本输出 (Engram 决策的 persona 切换)

**新增 Case 001 变体 (建议加):**
- **"张雪机车 50亿估值 合适吗"** — 通识 fallback + 主动搜索 (Case 001 直接复用)

## Window 边界 (本 Window A)

- ✅ read-only 摸底 Vera-Agent 主目录 + finance-suite 主仓
- ✅ 输出 Capability Matrix v0
- ✅ 完成 Case 001 5 层根因追溯
- ❌ 未修改任何源文件 (Vera / finance-suite 都未动)
- ❌ 未启动 Window B
- ❌ 未启动 Case 001 修复 (根因找到了, 修属于 Window B / 后续)

## 状态板更新 (Vera Audit 线)

```
Vera Audit
Capability Mapping     PASS (v0)
Case 001 Tracing       PASS (5 层根因)
Integration Validation ⏸ 等 G 显式开 Window B
Routing Fix            ⏸ 等 Window B 设计
```

## Engram 写入

待 G 决策:
- Engram lesson 1: "Vera 通识 fallback 缺失 = 5 层 Routing Failure 实证"
- Engram lesson 2: "Finance Suite 能力 50% 未被 Vera 消费" (产品层问题)

## 引用

- [[cc-a-infra-audit-verdict]] — 主问题改写范式
- [[cc-b-verdict-revoked-20260612]] — G 战略反转依据 (P0 Audit 升, P0 Deploy 降)
- [[cc-b-drill-pass-20260612]] — 4 case 验证范式 (本 Window 借鉴)
- [[tomorrow-0925-brief-no-go]] — 状态板基线
- [[sidebar-production-case-a-20260612]] — Deploy 独立线, 本 Window 暂不触碰
- [[intent-layer-architecture-decision]] — Intent Layer 设计在 FS, Vera 未落地
- [[workflow-fallback-contract]] — 三级降级契约, Vera 部分对齐
- [[engram-lesson-format-rule]] — 双版本输出设计在 Engram, Vera 无消费路径
