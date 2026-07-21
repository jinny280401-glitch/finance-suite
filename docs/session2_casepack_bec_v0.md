# Session 2 — 北方华创 (002371.SZ) Case Pack v0

> **Status:** Case Pack v0 (材料汇编, 非 Verdict)
> **Created:** 2026-06-12
> **Owner:** CC (orchestrator explicit 升级 v0.2 已批准)
> **Path:** `docs/session2_casepack_bec_v0.md`
> **Boundary:** 整理已拉材料, **不改 Skeleton / 不改 L0 / 写契约 / 写 runtime / 升 Verdict / 开 Session 3**

---

## 0. 1-句总结

```
Session 2 北方华创 当前能产出的最严判断:
  合同负债 -25.28% 反向 不必然等于订单转弱
  公司 narrative + 1 条招标硬 Rule 共同支撑 explain_contradiction
  Verdict = PARTIAL_PLUS (不升 verified)
  remaining_gap: 缺 fab 客户年报/招标/供应商名单直接链路
```

---

## 1. Baseline Sheet (Task #20 交付, DONE)

### 1.1 字段级数值 (4 字段 × 2 年 = 8 数值, 全部 L1 年报)

| Field | 2023 | 2024 | YoY | 同向? | Source |
|---|---:|---:|---:|:---:|---|
| Revenue (亿元) | 220.79 | 298.38 | **+35.14%** | ✅ 扩张 | [2024 年报 P9](https://file.finance.sina.com.cn/211.154.219.97%3A9494/MRGG/CNSESZ_STOCK/2025/2025-4/2025-04-26/10998589.PDF) |
| Net Profit (亿元) | 38.99 | 56.21 | **+44.17%** | ✅ 扩张 | [2024 年报 P9](https://file.finance.sina.com.cn/211.154.219.97%3A9494/MRGG/CNSESZ_STOCK/2025/2025-4/2025-04-26/10998589.PDF) |
| Inventory (亿元) | 169.92 | 234.79 | **+38.17%** | ✅ 备货增加 | [2024 年报 P31](https://file.finance.sina.com.cn/211.154.219.97%3A9494/MRGG/CNSESZ_STOCK/2025/2025-4/2025-04-26/10998589.PDF) |
| Contract Liability (亿元) | 83.17 | 62.14 | **-25.28%** | ❌ **反向** | [2024 年报 P31/P155](https://file.finance.sina.com.cn/211.154.219.97%3A9494/MRGG/CNSESZ_STOCK/2025/2025-4/2025-04-26/10998589.PDF) |

### 1.2 4 阶段状态 (per G 区分)

| 阶段 | 状态 |
|---|---|
| Evidence | PASS |
| Baseline Extraction | PASS |
| Baseline Comparison | DONE |
| **Verification** | **PARTIAL / MIXED** (3 同向 + 1 反向) |
| **Verdict** | **NOT VERIFIED → PARTIAL_PLUS** (per C 投递, 升但不升 verified) |

### 1.3 公司 narrative (公司对 amount_contradiction 的解释)

```
"新签订单继续保持良好趋势, 客户结构、订单结构的变化, 客户预付款比例有所下降"
→ 解释 amount_contradiction, 但来源公司自述, 不可独立 verified
```

---

## 2. Field Mapping (per G 2 patches applied)

### 2.1 5 字段 (Skeleton APPROVED)

| Field | 字段名 | 数据类型 | 来源层级 | Evidence 状态 |
|---|---|---|---|---|
| A | 主要客户 (top customers) | 实体列表 | L1 年报 | **NOT STARTED** (前五客户匿名, 不能验证 fab 客户) |
| B | 客户采购/招标记录 | 数值+时点 | L1/L2 客户年报/招标 | **PARTIAL** (1 条招标: 润鹏半导体 BOE 清洗设备 1,365 万元) |
| C | 设备覆盖环节 (process coverage) | 枚举 (刻蚀/PVD/CVD/氧化/清洗) | L1/L4 | **NOT STARTED** |
| **D** | **国产替代位置** (Patched: 降级为辅助, 不作主锚) | 定性/半定量 | L4 研报 + L1 交叉验证 | **NOT STARTED** |
| E | 订单增长 (合同负债/存货/在手订单) | 数值+同比 | L1 年报 | **DONE** (Baseline Comparison Layer 闭环) |

### 2.2 3 Contradiction Patterns (待验证)

| Pattern | 状态 | 备注 |
|---|---|---|
| P1: 卡点宣传 vs 客户设备清单缺席 | **NOT STARTED** | 需 fab 客户年报"前五供应商" |
| P2: 卡点地位 vs 海外厂商主导招标 | **NOT STARTED** | 需招标公开记录(海外 vs 国产占比) |
| P3: 国产替代叙事 vs 实际节点/环节覆盖 | **NOT STARTED** | 需卖方研报话术 + 产品营收占比 |

### 2.3 Verified Baseline (per G Patch 2, 4 项, **尚未构成 verified loop**)

| Baseline 字段 | 2024 数值 | Evidence | Verification | Verdict |
|---|---|---|---|---|
| 营收 2024 | 298.38 亿 | ✅ [L1] 年报 P9 | ✅ 同比支持 | ✅ 闭合 |
| 归母净利 2024 | 56.21 亿 | ✅ [L1] 年报 P9 | ✅ 同比支持 (容差 ±15% 边缘外 +44%) | ⚠️ 边缘外 |
| 合同负债 2024 末 | 62.14 亿 | ✅ [L1] 年报 P31/P155 | ❌ **反向** (YoY -25.28%) | ❌ 反向 |
| 存货 2024 末 | 234.79 亿 | ✅ [L1] 年报 P31 | ✅ 同比支持 | ✅ 闭合 |

**Baseline 整体**: Extraction PASS / Comparison DONE / Verification **PARTIAL-MIXED** / Verdict **NOT VERIFIED** (合同负债反向 + 公司自辩 narrative 缺 Rule)

---

## 3. Evidence Inventory (7 条, 全部 [L1])

### 3.1 Baseline Layer (2 份年报)

| ID | Source | Page | Field 命中 | Implication |
|---|---|---|---|---|
| B-1 | [北方华创 2024 年报](https://file.finance.sina.com.cn/211.154.219.97%3A9494/MRGG/CNSESZ_STOCK/2025/2025-4/2025-04-26/10998589.PDF) | P9 / P31 / P155 | 营收 / 净利 / 合同负债 / 存货 | 2024 baseline 4/4 字段数值 |
| B-2 | [北方华创 2024 年报摘要](https://static.cninfo.com.cn/finalpage/2025-04-26/1223309251.PDF) | P9 | 营收 / 净利 (同源) | 同源交叉验证 |
| B-3 | [北方华创 2023 年报](https://file.finance.sina.com.cn/211.154.219.97%3A9494/MRGG/CNSESZ_STOCK/2024/2024-4/2024-04-30/10161098.PDF) | 同期章节 | 2023 baseline 4/4 字段数值 | YoY 闭环 |

### 3.2 Rule Layer (5 条, Task #21)

| ID | Source | Page | Direction | Implication |
|---|---|---|---|---|
| R-1 | [北方华创 2024 年报 P30-P31/P156](https://file.finance.sina.com.cn/211.154.219.97%3A9494/MRGG/CNSESZ_STOCK/2025/2025-4/2025-04-26/10998589.PDF) | P30-P31 / P156 | company_explanation | 公司 narrative 解释合同负债下降 (客户结构/预付款比例); **客户匿名 → 不能验证 fab 客户** |
| R-2 | [中芯国际 2024 AR P59/P35](https://www.hkexnews.hk/listedco/listconews/sehk/2025/0409/2025040900322.pdf) | P59 / P35 | downstream_capex_support (indirect) | 中芯 2025 capex 维持 significant, **未直接指向北方华创** |
| R-3 ⭐ (重分类: Primary Field B, Rule Layer cross-reference only) | [华润润鹏半导体招标 2025-12-12](https://www.crpsz.com/zbxx/006001/006001004/20251212/8edd69f2-0279-45ac-a1c3-a1ed274d89fe.html) | HTML 公告页 | **fab_bidding_direct → reclassified Primary Field B, Rule Layer secondary** | 招标人: 润鹏半导体 / 中标人: 北京北方华创 / BOE 清洗设备 / **1,365 万元** / **最硬证据 (Field B primary)** |
| R-4 | [北方华创 2024-05-27 投关](https://static.cninfo.com.cn/finalpage/2024-05-27/1220172406.PDF) | P2-P5 | company_explanation_plus | 订单饱满 + 存储产线扩产带动 + 重复订单; **仍 IR 自述** |
| R-5 | [北方华创 2026-05-15 投关](https://static.cninfo.com.cn/finalpage/2026-05-15/1225310975.PDF) | P1-P3 | forward_looking_support | 2026-2027 需求旺盛 + capex 维持高位; **不能回填 2024** |

### 3.3 Evidence 强度分布

```
[L1] 监管/公司正式:  7 条 (年报 3 份 + 投关 2 份 + 客户年报 1 份 + 招标 1 份)
[L4] 卖方研报:       0 条 (per C/G 决策, L4 不作主锚)
[L5] 媒体:          0 条
L1:L4:L5 = 7:0:0    (per G freeze: L1 主导, L4 辅助, L5 仅 catalyst)
```

### 3.4 唯一硬 Rule (1 条, 已重分类 Primary Field B, Rule Layer cross-reference only)

```
R-3 润鹏半导体 BOE 清洗设备 1,365 万元中标
  → 招标平台公示 (华润守正), 非公司自述
  → 把 北方华创 ↔ fab 客户 ↔ 设备采购订单 完整连起来
  → Primary = Field B (客户采购直接证据, 1 fab 1 项目)
  → Secondary = Rule Layer (仅 cross-reference, 不作主 Rule)
  → 但只是 1 个 fab 1 个项目, 不代表全部订单"verified 充足"
```

---

## 4. Gap Inventory (剩余缺口, 严格按 C/G 锁定)

### 4.1 缺口清单 (P0 → P3)

| P | Gap | 缺口 | 解锁什么 | 拉取方向 |
|---|---|---|---|---|
| **P0** | **fab 客户年报"前五供应商"披露** | 0 条 | Field A (实名客户) + Field B 客户名 + 直接命中 amount_contradiction Rule | 拉中芯/华虹/长存 2024 年报 |
| **P0** | **更多 fab 客户招标公告** | 1 条 (R-3) | Field B 多样本 + Rule Layer PARTIAL_PLUS → READY | 华润/中招/各地公共资源 |
| P1 | 北方华创问询函 | 0 条 | 客户结构变化的具体名字 (narrative → field) | 巨潮 cninfo 人工 |
| P1 | 北方华创投资者电话会议 (深度) | 0 条 | 客户结构 + 在手订单 + 预付款比例变化的数字支撑 | 巨潮 cninfo 人工 |
| P2 | 卖方研报话术 (L4 辅助) | 0 条 | Field C / D 辅助, 验证"卡点"叙事 | 财汇/同花顺/雪球 |
| P3 | 招标公开记录 (海外 vs 国产占比) | 0 条 | Pattern 2 验证 | 中国招标投标公共服务平台 |

### 4.2 已闭合缺口 (相对于 Skeleton)

```
✅ 2024 + 2023 baseline (4 字段 × 2 年 = 8 数值, Field E)
✅ 公司对 amount_contradiction 的 narrative 解释 (R-1, R-4, R-5)
✅ 下游 fab capex 间接支撑 (R-2)
✅ 1 条 fab 客户招标硬 Rule (R-3, 润鹏半导体)
✅ Baseline Comparison Layer 闭环 (YoY 4/4)
```

### 4.3 缺口影响评估 (per C 投递结论)

```
剩余 gap 全部集中在:
  - 跨 fab 客户样本 (不止 1 个 fab)
  - 客户实名披露 (不止匿名)
  
影响:
  - Field A (top customers): 仍 NOT STARTED
  - Field B (客户采购): 1 样本, 不构成 verified loop
  - Field C / D: NOT STARTED
  - Field E: 已 DONE, Verdict PARTIAL_PLUS
  - 0/3 Contradiction Pattern 跑过
```

### 4.4 派能对照 (per G 跨案实证)

```
派能案:   Rule 推到 narrative → 0 硬 Rule → NOT VERIFIED
北方华创: Rule 推到 narrative + 1 招标硬 Rule → PARTIAL_PLUS
  → 北方华创 Rule Layer 实际比派能强
  → 但 1 条招标不构成 verified loop, 仍 NOT VERIFIED → PARTIAL_PLUS

跨案例 L0 v0.1 backlog Compound Assertion risk 实证 #2:
  "Rule Layer ≥1 硬 Rule 不够, 需 多条 / 跨 fab / 跨时点"
```

---

## 5. Session 2 Execution Checklist (后续执行顺序)

### 5.1 当前可执行项 (无需新指令)

```
□ Task #21 继续拉 Rule 层 P0 缺口
  - fab 客户年报"前五供应商"披露
  - 更多 fab 招标公告
  → Rule Layer PARTIAL_PLUS → READY 升级路径
```

### 5.2 需要新指令的项 (per orchestrator 升级)

```
□ Field A (top customers) 拉取
  - 需 client explicit 升级 v0.2 → v0.3 (实名客户 + 公司完整客户名)
  - 当前 4-way STOPPED, 需 orchestrator explicit

□ Field C (设备覆盖环节) 拉取
  - 需 2024 年报"主营业务分行业/分产品" 章节
  - 需卖方研报话术 (L4, 辅助)
  - 当前是 Skeleton 层面, 拉取前需 orchestrator 确认

□ 0/3 Contradiction Pattern 启动
  - Pattern 1/2/3 跑通需 Field A/B/C/D 都拉到 L1 证据
  - 当前 P0 缺口未补, 不能跑

□ 输出 Session 2 Audit Card (最终)
  - 需 Field A/B/C/D 至少 1/5 拉到 L1 证据
  - 需 Rule Layer 从 PARTIAL_PLUS → READY
  - 需至少 1 个 Contradiction Pattern 跑过
```

### 5.3 显式不做 (per boundary)

```
❌ 改 Skeleton (G 2 patches 已锁, Field D 降级 + Baseline 4 项)
❌ 改 L0 ontology
❌ 写 P0b/c/d 契约
❌ 写 Runtime
❌ 改 Verdict (Verdict 升到 verified 需 G 显式批准)
❌ 开 Session 3 工业富联 (HOLD)
❌ 修 MCP / WebSearch / WebFetch (DEGRADED, NO WINDOW)
```

### 5.4 升级路径 (Rule Layer → READY → Verdict 可升)

```
当前:  PARTIAL_PLUS (5 条 Rule, 1 招标硬 Rule)
   ↓ 补 P0 缺口
目标:  READY (≥ 3 条 fab 客户硬 Rule + ≥ 1 条客户实名披露)
   ↓ G 显式批准
终点:  Verdict 可升 (verified / conflicting_evidence, 不再 NOT VERIFIED)
```

---

## 6. 关键发现 (per G 教导, 跨案例实证)

### 6.1 4 阶段区分 (per G 核心)

```
Evidence  ≠  Baseline Extraction  ≠  Baseline Comparison  ≠  Verification  ≠  Verdict

拿到 1 份年报 = Evidence PASS
字段从原文抽出 = Extraction PASS
算 YoY = Comparison PASS
判定 1 年数据 = Verification NOT VERIFIED (1 个时点 = 0 个时间锚)
推 Rule → Verdict = NOT VERIFIED (公司 narrative 不独立 verified)
```

### 6.2 Baseline ≠ Verification (G 关键发现)

```
派能:    验证过 installation/shipment/inventory 三元组缺一不可
北方华创: 验证 Baseline Extraction ≠ Verification
          → 拿到 1 年年报 ≠ 完成产业链验证
          → 升级路径 = 补 2023 baseline = Comparison Layer
          → Comparison Layer 补完后, 暴露新缺口 (Rule Layer)
          → Rule Layer 补完后, 仍需 跨 fab / 跨时点 才成 verified loop
```

### 6.3 Compound Assertion Risk (L0 v0.1 backlog 实证 #2)

```
派能:    反转测试 + 公司 narrative → 0 硬 Rule → NOT VERIFIED
北方华创: amount_contradiction + 公司 narrative + 1 招标硬 Rule
          → Rule Layer 比派能强, 但仍 NOT VERIFIED → PARTIAL_PLUS
          
→ Rule Layer "≥1 硬 Rule" 不够
→ 需 ≥ 3 条硬 Rule / 跨 fab / 跨时点 才能成 verified loop
→ 这是跨案例的 L0 v0.1 backlog Compound Assertion risk 实证
```

### 6.4 Session 2 实证的 L0 v0.1 backlog 更新建议

| Backlog 项 | 派能证据 | 北方华创证据 | 建议 |
|---|---|---|---|
| Compound Assertion Risk | 反转测试 + 0 硬 Rule | amount_contradiction + 1 硬 Rule | 升级: "需 ≥3 硬 Rule, 跨客户/跨时点" |
| Rule Layer 充分性 | NOT VERIFIED | PARTIAL_PLUS | 升级: "1 硬 Rule = PARTIAL_PLUS, 3+ 硬 Rule 才能升 verified" |
| Verified Loop 关闭条件 | 缺 installation | 缺 跨 fab 样本 | 升级: "Loop 关闭需 跨实体 / 跨时点 / 跨 source_type" |

---

## 7. 任务状态 (本次 Case Pack 编写时)

| # | 状态 | 任务 |
|---|---|---|
| 15 | 🟡 | Session 2 prep |
| 20 | ✅ | Task #20 Baseline Comparison Layer |
| **21** | 🟡 | **Task #21 Rule Layer (5 条已落, PARTIAL_PLUS, P0 缺口未补)** |

---

## 8. Changelog

- 2026-06-12: Case Pack v0 编写。5 节内容 (Baseline / Field Mapping / Evidence Inventory / Gap Inventory / Execution Checklist) + 1 节关键发现。Task #20 + #21 已落材料完整汇编。明确 Session 2 当前能产出的最严判断: **PARTIAL_PLUS (合同负债 -25.28% 不必然等于订单转弱, 但不构成 verified 充足)**。
