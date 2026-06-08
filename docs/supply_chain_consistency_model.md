# Supply Chain Consistency Model

日期：2026-06-08

状态：P0a.5 MODEL FREEZE DRAFT。不是 Gate Contract，不是 Runtime 设计。

## 1. 决策

在编写 `Supply Chain Consistency Gate Contract` 之前，先冻结产业链一致性的判断模型。

本模型只回答一个问题：

```text
产业链一致性如何从“研究问题”拆成“字段、证据、匹配、容忍度、判定”？
```

如果这条链无法被手工跑通，后续 Gate 契约不得进入实现。

## 2. 为什么不是直接写 Gate

“验证产业链”这个说法过大。不同字段会导致完全不同的判定：

- 只看营业收入，可能看不出供应商关系。
- 只看采购金额，可能看不出产能利用率。
- 只看订单公告，可能看不出应收和存货压力。
- 只看研报，可能把观点误当事实。

因此年报、公告、问询函、招投标、海关数据都只是 **Evidence Source / 证据容器**。它们不能直接进入 Gate 判定。

真正进入 Gate 的必须是可抽取字段，例如：

```text
supplier_name
customer_name
supplier_revenue_share_pct
customer_purchase_share_pct
shipment_volume
capacity_value
capacity_utilization
ar_growth_yoy
inventory_growth_yoy
capex_in_progress_yoy
contract_amount
delivery_period
related_party_flag
```

## 3. Model Pipeline

产业链一致性验证必须先被拆成以下链路：

```text
Serenity Question
↓
Assertion
↓
Extraction Field
↓
Evidence Source
↓
Matching Rule
↓
Tolerance
↓
Verdict
```

每一次验证尝试是一行 append-only 记录。不得用“LLM 综合判断”替代这条链。

## 4. 8 列工作表

P0a.5 pressure test 使用 8 列工作表：

| # | Column | 作用 |
|---|---|---|
| 1 | Serenity Question | 方法论提出的产业链问题 |
| 2 | Assertion | 可独立验证的断言 |
| 3 | Extraction Field | 需要抽取的字段 |
| 4 | Evidence Source | 字段来自哪个证据容器 |
| 5 | Matching Rule | 用什么勾稽规则匹配 |
| 6 | Tolerance | 容忍度，必须有数值和单位 |
| 7 | Verdict | 5 状态判定 |
| 8 | Conflict Source | 仅 `conflicting_evidence` 时填写 |

硬约束：

- 一个 Question 至少拆出一个 Assertion；pressure test 中建议至少 3 个。
- 每个 Assertion 只对应一个主 Matching Rule。
- Evidence Source 必须有可追溯 ID 或 URL。
- Tolerance 禁止写“合理”“大致”“差不多”。
- Verdict 不得用二值 `success=true`。

## 5. Verdict Contract Draft

P0a.5 暂定 5 状态，后续 P0d 冻结为正式 contract：

| Verdict | 含义 | Runtime 风险 |
|---|---|---|
| `verified` | 找到支撑证据，且在容忍度内匹配 | 可用于研究结论，但仍需 citation |
| `tried_not_found` | 主动查询过，未找到支撑证据 | 不得升级为反证，只能标为未找到 |
| `not_attempted` | 还没有查询 | 只能作为待核验事项 |
| `conflicting_evidence` | 找到反证或上下游对不上 | 最高风险，必须披露 |
| `tolerance_unresolved` | 有数据，但超出容忍度或口径无法判定 | 不得输出强结论 |

`conflicting_evidence` 必须单独保留，不能和 `tried_not_found` 混在一起。

```text
没找到证据 ≠ 找到反证
```

## 6. Conflict Source Draft

`conflicting_evidence` 至少区分：

| Conflict Source | 示例 |
|---|---|
| `direct_contradiction` | A 说 B 是客户，B 的披露否认或不支持 |
| `chain_contradiction` | 上游、下游整体链条方向对不上 |
| `amount_contradiction` | 金额、数量、产能量级对不上 |
| `direction_contradiction` | A 声称增长，但上游/下游关键字段下降 |
| `timing_contradiction` | 交付期、确认收入、建设周期跨期对不上 |

## 7. Matching Rule Draft

P0a.5 只定义规则家族，不冻结具体函数。

| Rule Family | 目的 | 示例 |
|---|---|---|
| `mirror_match` | A 的客户/供应商披露与 B 的供应商/客户披露是否镜像 | A 前五大客户出现 B，B 前五大供应商出现 A |
| `capacity_chain_match` | 产能扩张是否有产线、在建工程、备案、设备采购支撑 | 公告产能翻倍，但在建工程/项目备案不支持 |
| `cash_logistics_match` | 订单/出货增长是否被应收、存货、合同负债、采购承接 | 出货增长但应收异常暴涨、现金流不匹配 |
| `temporal_match` | 上下游变化是否在合理时间窗口内发生 | 上游采购应早于中游产出 |
| `transitivity_match` | A-B-C 多级链路是否能连起来 | A 给 B 供关键材料，B 的下游 C 需求是否存在 |

## 8. 首批 Assertion 类型

首批 pressure test 只覆盖三类断言：

1. **产能扩张**
   - 典型说法：公司产能翻倍、新产线投产、瓶颈产能释放。
   - 字段方向：`capacity_value`、`capex_in_progress_yoy`、`project_status`、`approval_id`。

2. **订单 / 出货增长**
   - 典型说法：订单爆发、出货大增、客户需求强。
   - 字段方向：`contract_amount`、`shipment_volume`、`ar_growth_yoy`、`inventory_growth_yoy`、`contract_liability_yoy`。

3. **产业链卡点地位**
   - 典型说法：公司是核心供应商、控制 scarce layer、客户绕不开。
   - 字段方向：`supplier_name`、`customer_name`、`supplier_revenue_share_pct`、`customer_purchase_share_pct`、`patent_id`、`certification_status`。

## 9. Evidence Source 不等于 Evidence Field

Evidence Source 是容器：

- 年报、半年报、季报
- 公司公告
- 交易所问询函及回复
- 招投标记录
- 项目备案、环评、能评
- 海关数据
- 专利、认证、标准
- 上下游上市公司公告

Extraction Field 才是 Gate 可处理的字段。报告或研报中的文字描述不能直接作为字段，必须抽取为可比对值。

## 10. Serenity 边界

Serenity Skill 可以提出：

- 产业链问题
- 需要拆分的 assertion
- 候选 evidence source
- 下一步核验清单

Serenity Skill 不得：

- 生成最终 Verdict
- 自己生产 Evidence
- 直接读取 raw Provider data
- 跳过 QC / Trust Gate
- 把研报观点升级为已验证事实

## 11. Pressure Test 顺序

P0a.5 必须先手工跑，不写 runtime 代码。

建议顺序：

1. 选一个公开资料丰富的真实案例：新能源、算力、AI 服务器、消费电子之一。
2. 选一篇真实研报或主题报告。
3. 从研报中抽 3-5 个 claim，其中至少一个 negative test。
4. 用 8 列工作表手工填表。
5. 记录哪些字段能抽，哪些字段抽不到，哪些证据源只能作为线索。
6. 反推：
   - `Extraction Schema v0`
   - `Matching Function v0`
   - `Tolerance Contract v0`
   - `Verdict Contract v0`

## 12. 后续路线

```text
P0a External Intelligence Provider Strategy
  PASS

P0a.5 Supply Chain Consistency Model
  NEXT

P0b Extraction Schema v0

P0c Matching + Tolerance Contract v0

P0d Verdict Contract v0

P1 Supply Chain Consistency Gate Runtime
```

## 13. Non-Goals

本模型不做：

- 不写 runtime。
- 不接新 Provider。
- 不定义完整 Extraction Schema。
- 不定义完整 Matching Function。
- 不定义 ReportAssembly 行为。
- 不让 LLM 用“感觉”判定产业链一致性。

如果 pressure test 跑不通，P0b 不得启动。
