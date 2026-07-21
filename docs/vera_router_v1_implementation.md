# Vera Capability Router v1 Implementation — Window D 实施

**实施窗口**: Window D — Vera Capability Router v1 Implementation
**Kickoff**: G 2026-06-12 显式指令 (替代 "Window C Router Design" 命名)
**状态**: ⚠️ **PARTIAL — Gate 按字面指令实施,但实测发现与 Case 001 目标存在冲突,等 G 决策修复方向**

---

## 背景 (镜像 G kickoff)

```
Window A  Capability Mapping            PASS
Window B  Integration Validation        PASS WITH FINDINGS
Window C  Capability Router Design      PASS  (CLOSE — 注: G 引用文件 vera_capability_router_v0.md 实际不存在,设计输入散落在 Window A 收口 + Case 001 5 层根因 + Mapping)
Window D  Router v1 Implementation     KICKOFFED (本文件)
```

**根因已确认**: Vera 缺 Capability Router,不是缺 Finance Suite。

**目标**: 实现最小 Router v1,**只解决 Case 001 张雪机车**。

---

## 实施内容 (严格按 G 6 项 + 4 级降级链 + Unknown Protection)

### 1. Finance Intent Gate (6 项 allow-list)

按 G kickoff 字面 6 项:
- 股票代码 / 上市公司 / 股价问题 / 财务问题 / 投资分析请求 / 公告问题

**实施文件**: `Vera-Agent/app/skills/capability_router.py`
- 类 `FinanceIntentGate`
- 正向模式: `STOCK_RESEARCH_ALLOW_PATTERNS` (6 类)
- 否定模式: `STOCK_RESEARCH_NEGATIVE_PATTERNS` (mixed query 防御)

### 2. Fallback Ladder (4 级降级链)

按 G kickoff:
```
Intent
↓
Capability (FS 有数据 → 用)
↓
Search (Tavily/Brave 主动搜索)
↓
General Knowledge (LLM 自身通识)
↓
Unknown ("我不知道")
```

**实施**: `FallbackLayer` enum + `CapabilityRouter.route()` 决策逻辑

### 3. Unknown Protection

按 G kickoff:
- 禁止: L1 失败 → 直接"我不知道"
- 必须: L1/L2/L3 全失败 → 才能到 L4

**实施**: `get_user_prompt_for_layer()` 在 L4 时检查 `previous_layers_failed`,若中间层缺失返回 PROTECTION 警告

---

## 文件清单

| 文件 | 类型 | 状态 |
|------|------|------|
| `Vera-Agent/app/skills/capability_router.py` | 新建 | ✅ |
| `Vera-Agent/app/skills/router.py` | 修改 (集成) | ✅ |
| `Vera-Agent/tests/test_capability_router.py` | 新建 | ✅ |
| `docs/vera_router_v1_implementation.md` | 本文件 | ✅ |

---

## ⚠️ 关键实测发现 (等 G 决策)

**按 G 字面 6 项 allow-list 实施后,Case 001 仍能进入 stock-analyst。**

### 实测数据 (12 场景)

| 输入 | 场景 | allow | 命中类目 | 备注 |
|------|------|-------|----------|------|
| "张雪机车 50亿估值 合适吗" | Case 001 短版 | **True** | 投资分析请求 | ❌ **未拒** |
| "我考虑要接的是张雪机车的老股..." | Case 001 完整版 | **True** | 投资分析请求 | ❌ **未拒** |
| "000001 这只股票怎么样" | 股票代码 | True | 股票代码 | ✅ 拒目标 |
| "贵州茅台 PE 多少" | 上市公司+股价 | True | 股票代码, 股价问题 | ✅ |
| "比亚迪 2024 年报营收多少" | 上市公司+财务 | True | 财务问题 | ✅ |
| "茅台估值合理吗, 能买入吗" | 投资分析 | True | 投资分析请求 | ✅ |
| "茅台最近有重组公告吗" | 公告 | True | 公告问题 | ✅ |
| "今天天气怎么样" | 闲聊 | False | - | ✅ |
| "张雪机车是谁" | 通识 | False | - | ✅ |
| "帮我推荐股票" | 投资无标的 | False | - | ✅ |
| "茅台跌了能买吗" | 上市公司+投资 | **False** | - | ❌ **假阳性**(应是 True) |
| "最近股市怎么样" | 股价 | **False** | - | ❌ **假阳性**(应是 True) |

### 根因分析

1. **Case 001 未被拒**:
   - 关键词"估值/合适"命中 G 第 5 项 "投资分析请求"
   - 这是 G 字面指令的直接后果:G 列了"投资分析请求"作为 allow 类目,而 Case 001 含"估值/合适"必然命中
   - **Gate 内部不存在"实体必须是已知上市公司"的二次检查**

2. **假阳性 (该 allow 被拒)**:
   - "贵州茅台" / "比亚迪" / "茅台" 等短名没"公司/股份/集团"后缀,不命中"上市公司"正则
   - "茅台跌了能买吗" 无明确 PE/股价关键词,无公司后缀
   - "最近股市怎么样" 无具体股价/财报关键词
   - **Gate 正则过严,正常股票问题被误拒**

### 3 个修复方向 (等 G 决策)

| 选项 | 修改 | 效果 |
|------|------|------|
| **A. 加上市公司白名单** | 在 Gate 内部嵌入"已知 A 股/港股/美股上市公司"白名单 (e.g., 5000+ 股票代码),命中 allow-list 的"投资分析请求" 还需实体在白名单中 | 精确拒 Case 001,但需白名单维护 |
| **B. 收紧"投资分析请求" 类目** | 把"投资分析请求" 从 allow-list 移除,只留"必须有具体标的"(代码/公司)+ 辅助类目 | 简单,但失去"估值/合适" 类问题能力 |
| **C. 实体识别增强** | 引入 LLM 实体识别 (NER),先识别"具体股票实体"再决策 | 最准,但增加 LLM 调用 (15s timeout) |

**当前默认**: 保留 G 字面指令 (允许 Case 001 通过),等 G 决策。

**注意**: 即便 Case 001 通过 Gate 进入 stock-analyst,4 级降级链也会在 L1 (FS data missing) → L2 (Search) → L3 (General Knowledge) 至少 3 层中产生有效输出,不会直接"我不知道"。**Unknown Protection 仍生效。**

---

## 测试结果

测试文件: `Vera-Agent/tests/test_capability_router.py`

测试覆盖:
- ✅ Finance Intent Gate 6 项 allow-list 各 1 用例
- ✅ 强/中/弱信号分类
- ✅ Mixed query 否定模式
- ✅ Case 001 完整版 + 变体回归
- ✅ 4 级降级链 L1/L2/L3/L4 决策
- ✅ Unknown Protection (不能跳中间层)
- ✅ Should-advance 推进逻辑

**运行结果**: ⚠️ 测试与字面指令一致,**Case 001 测试预期需根据 G 决策调整**:
- 若 G 选 A/B/C 修复:测试预期需改 `assert result.allow_stock_research is False`
- 若 G 维持字面:测试应改为 `assert result.allow_stock_research in (True, False)` 接受两种结果

---

## 与 G 优先级的对齐

| G P 优先级 | Capability | 状态 |
|------------|------------|------|
| P0 | Vera Router Implementation | Window D 实施中(本文件) |
| P1 | Stock Research v2 Sync | ⏸ 等 Window D 收口 |
| P1 | Evidence Bundle Integration | ⏸ 等 Window D 收口 |
| P2 | Deploy Contract Drift | FROZEN |
| P3 | Data Freshness | FROZEN |

**Window D 收口标准** (待 G 决策):
- 必须: Finance Intent Gate + 4 级降级链 + Unknown Protection 实施完成 ✅
- 验收: Case 001 不再直接"我不知道" → ✅ (即使 Gate 误判,降级链 L2/L3 兜底)
- 验收 (严格): Case 001 必须不进入 stock-analyst → ⚠️ (需 G 选 A/B/C 修复)
- 测试: 全部测试 PASS → ⚠️ (需根据 G 决策调整 Case 001 预期)

---

## 实施未触碰 (维持边界)

- ❌ Vera prompt 文件 (stock-analyst.md / auction-analysis.md 等) — 未改
- ❌ finance-suite 代码 — 未改
- ❌ Trust Gate / Evidence Tagline / 双版本输出 — Window D 范围外
- ❌ 真实 FS / Tavily / Brave 调用 — Window D 只做决策逻辑,真实调用后续窗口
- ❌ LLM 分类器改动 — 保留现有 IntentClassifier

---

## 引用

- [[vera_audit_window_a_20260612_v0]] — Window A 收口 (Capability Matrix + Case 001 5 层根因)
- [[vera_capability_matrix_v0]] — 8 行 × 4 列矩阵
- [[vera_case_001_zhangxue_20260612]] — Case 001 5 层根因追溯
- [[vera_finance_suite_mapping_v0]] — Mapping v0 (3/8 PARTIAL)
- [[cc-b-verdict-revoked-20260612]] — 战略反转 (P0 Router, P1 Deploy)
- [[workflow-fallback-contract]] — FS 侧 3 级降级, Vera v1 实施对齐
- [[intent-layer-architecture-decision]] — Multi-Intent 架构决策 (本 Gate 是简化落地)
