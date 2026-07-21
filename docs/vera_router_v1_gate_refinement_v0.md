# Vera Router v1 — Gate Refinement (Window D.1)

**实施窗口**: Window D.1 — Finance Intent Gate Refinement
**Kickoff**: G 2026-06-12 显式指令 (Window D PARTIAL 收口后)
**状态**: ✅ **PASS** — G 3 验收 + 16 场景实测全过

---

## 背景 (镜像 G kickoff)

Window D 实施后,Gate 按 G 字面 6 项 allow-list 实施,但实测发现:
- Case 001 张雪机车仍能进入 stock-analyst (因为"估值/合适"命中"投资分析请求"类目)
- 部分合法股票问题被误拒 (茅台/比亚迪短名没"公司/股份"后缀)

G 2026-06-12 决策:**选 B 方案 (收紧"投资分析请求")**,Window D.1 = Gate Refinement:
- ✅ 允许改 Gate 规则 + 测试
- ❌ 不引入白名单 (5000+ 不可持续)
- ❌ 不引入 LLM NER (延迟/复杂度/成本上升)
- ❌ 不动 Trust Gate / Finance Suite

---

## 新 Contract (G 2026-06-12)

```
金融对象成立 = 强信号 OR (启发式证券简称 AND 金融动作) AND NOT 私募语境
allow_stock_research = 金融对象成立
```

### 强信号 (Strong Signal)
- 股票代码 — 6 位数字 / A 股代码 / 美股 ticker
- 上市公司 — 含"公司/股份/集团/控股"后缀
- 基金 — 含"基金/ETF"
- 指数 — 含"指数/上证/深证/创业板/科创板/沪深300/..."
- 公告主体 — 含"公告/披露/重组/..."

### 启发式证券简称 (Heuristic Security Name)
- 2-4 字中文 + 紧邻金融动作
- 金融动作词: 跌/涨/PE/PB/能买/能卖/股价/收盘/财报/...
- 例: "茅台跌了能买吗" → "茅台" + "跌了" → 启发式证券简称
- 例: "贵州茅台 PE 多少" → "贵州茅台" (4 字) + "PE" → 启发式

### 私募/未上市语境 (Private Equity Context) — 否定
- 老股/天使轮/Pre-A/A 轮/B 轮/C 轮/D 轮/接盘
- 拟上市/未上市/IPO 前/股权转让/独角兽
- 种子轮/战略融资/份额转让/原始股
- **估值/融资 不算私募** (上市公司也用)
- 命中任一 → 即使有强信号也拒

### Mixed Query 防御 (Window D.1 修正)
- 模式: "但/不过/其实/实际上" + 金融词;消费品 + "但" + 金融词;"对比/vs" + 金融词
- **Window D.1 修正**: 仅在无强信号时生效 (避免"比亚迪股份"被"比"+"股"误伤)

---

## G 3 验收 (全部严格通过)

| Case | 输入 | 预期 | 实际 | 命中 |
|------|------|------|------|------|
| **001** | "我考虑要接的是张雪机车的老股，天使轮的，按50亿估值接手，合适吗?" | **False** | False ✅ | 私募语境: 老股 + 天使轮 |
| **002** | "贵州茅台 PE 多少" | **True** | True ✅ | 启发式: 贵州茅台 + 强信号股票代码 (PE 的 P/E) |
| **003** | "茅台跌了能买吗" | **True** | True ✅ | 启发式证券简称: 茅台 + 金融动作 跌了 |

---

## 16 场景实测全过

| 输入 | 场景 | 预期 | 实际 | 备注 |
|------|------|------|------|------|
| Case 001 | 张雪机车老股 | False | False ✅ | 私募语境拒 |
| Case 002 | 贵州茅台 PE | True | True ✅ | 强信号 |
| Case 003 | 茅台跌了能买 | True | True ✅ | 启发式简称+动作 |
| 比亚迪股份 PE 多少 | 上市公司+PE | True | True ✅ | Window D 之前误判,D.1 修复 |
| 比亚迪股份 怎么样 | 上市公司+无动作 | (True) | True ✅ | 强信号优先 |
| 茅台股份 PE 多少 | 上市公司+PE | True | True ✅ | 强信号 |
| 000001 这只股票 | 股票代码 | True | True ✅ | 强信号 |
| 茅台估值合理吗, 能买入吗 | 上市公司估值 | True | True ✅ | 启发式简称+投资动作 |
| 最近股市怎么样 | 无标的 | (False) | False ✅ | 无金融对象 |
| 今天天气怎么样 | 闲聊 | False | False ✅ | 无 |
| 张雪机车是谁 | 通识 | False | False ✅ | 无 |
| 比特币怎么样 | 非股票 | (False) | False ✅ | 启发式简称"比特币"无金融动作 |
| 最近老股转让有什么坑 | 老股转让 | False | False ✅ | 私募语境 |
| 拟上市公司怎么估值 | 拟上市+估值 | False | False ✅ | 私募语境 (强信号也拒) |
| 帮我推荐股票 | 无标的 | False | False ✅ | 无 |
| 茅台酒与茅台股票的区别 | mixed query | (False) | False ✅ | mixed query 拒 |

**严格通过 12/12 (expected 非 None 的 12 用例)**

---

## 实施未触碰 (Window D.1 边界严格遵守)

- ❌ 不引入 5000+ 上市公司白名单
- ❌ 不引入 LLM NER (无 LLM 调用增加)
- ❌ 不动 Trust Gate (Citation Contract)
- ❌ 不动 Finance Suite (MCP / prompts / scripts)
- ❌ 不动 Vera prompt 文件 (stock-analyst.md 等)
- ❌ 不动 router.py 集成逻辑 (Window D 已完成)
- ❌ 不引入新依赖

**只动**:
- ✅ `Vera-Agent/app/skills/capability_router.py` — Gate 规则重构
- ✅ `Vera-Agent/tests/test_capability_router.py` — 测试更新

---

## 已知 Trade-off (透明)

1. **启发式证券简称假阳性**: N-gram 启发式可能误识别非证券短名 (例: "茅台估值合理吗" 命中"台估值合")。**当前接受这个误差**,因为:
   - 用户真实意图是"茅台估值",allow=True 是对的
   - 误差是"抓到噪声简称 + 真实意图匹配",而非"误判真意"

2. **私募语境单 token 触发**: 命中 1 个私募词就拒。可能误拒"老茅台股份" (无私募语境,正常) — 实测 "最近老股转让有什么坑" 正确拒。

3. **mixed query 模式保留但弱化**: 仍可能误伤,但仅在无强信号时生效,影响有限。

4. **2-4 字中文短名**: 当前规则不区分"茅台" vs "白牛" (都是 2 字中文)。如果需要进一步精确,需 G 决策引入更强的实体识别 (但 G 已拒绝白名单和 LLM NER)。

---

## 文件清单

| 文件 | 状态 | 大小 |
|------|------|------|
| `Vera-Agent/app/skills/capability_router.py` | 重构 (Gate 规则) | 30+ KB |
| `Vera-Agent/tests/test_capability_router.py` | 重写 (16 场景 + G 3 验收) | 13+ KB |
| `docs/vera_router_v1_gate_refinement_v0.md` | 本文件 | - |

---

## 与 G 优先级的对齐

| G P 优先级 | Capability | 状态 |
|------------|------------|------|
| P0 | Vera Router Implementation | **Window D + D.1 PASS** ✅ |
| P1 | Stock Research v2 Sync | ⏸ 等 Window D.1 收口 |
| P1 | Evidence Bundle Integration | ⏸ |
| P2 | Deploy Contract Drift | FROZEN |
| P3 | Data Freshness | FROZEN |

**Window D.1 收口标准** (per G):
- ✅ 张雪机车 → 不进 stock-analyst
- ✅ 贵州茅台 PE多少 → 进 stock-analyst
- ✅ 茅台跌了能买吗 → 进 stock-analyst
- 三条全过 → Window D PASS

---

## 引用

- [[vera_router_v1_implementation]] — Window D 实施 (v1 初版)
- [[vera_case_001_zhangxue_20260612]] — Case 001 5 层根因追溯
- [[vera_audit_window_a_20260612_v0]] — Window A 收口
- [[vera_capability_matrix_v0]] — 8 行 × 4 列矩阵
- [[vera_finance_suite_mapping_v0]] — Mapping v0 (3/8 PARTIAL)
- [[workflow-fallback-contract]] — FS 侧 3 级降级, Vera v1 对齐
- [[intent-layer-architecture-decision]] — Multi-Intent 架构决策 (本 Gate 是简化落地)
