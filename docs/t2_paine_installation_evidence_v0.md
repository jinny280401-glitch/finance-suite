# T2 Paine Installation Evidence v0 (Task #19 Closure)

> Case: 派能科技 2022 户储暴增 vs 2023 暴跌 — installation field 补齐
> Purpose: 把 reversal findings 第 9 行 Conflict 的 installation 字段从定性升级为数值，
>          使派能 Field→Rule→Verdict 闭环（带 evidence gap）。
> Parent: `t2_paine_reversal_findings_v0.md` / `t2_paine_2022_vs_2023_comparison_v0.md`
> Evidence pull date: 2026-06-11
> Scope guard: 不引入新 provider；全部数字来自 reversal findings 已登记的 4 份卖方研报 + 公司 IR。

## 1. Installation 数字全表（8 项，含来源与质量评级）

| # | 口径 | 数值 | 年份 | 来源 | 引用方 | Quality Tier |
|---|---|---|---|---|---|---|
| 1 | 全球户用光伏新增装机 | 29 / 41 / 56 **GW** | 2022/23/24E | 东吴 2022-04-27 | Technavio / 彭博 | 测算·预测 (L4 forecast) |
| 2 | 全球户储电池需求空间 | 6 / 13 / 24 **GWh** | 2022/23/24E | 东吴 2022-04-27 | 东吴测算 | 测算·预测 (L4 forecast) |
| 3 | **全球户储装机规模** | **12.2 / 23.6 / 34.4 GWh** | **2021A/2022A/2023E** | **华福 2023-04-10** | 华福测算 | 测算·预测 (L4 forecast) ★ Rule-3 用 23.6/34.4 |
| 4 | 欧洲户储装机增速 | +177% / +102% / +40% | 2022/23/24E | 华福 2023-04-10 | 华福测算 | 只有增速·无绝对 GWh (L4 forecast) |
| 5 | 德国 2022 户储装机 | **2.1 GWh+** (22 万套) | 2022A | 华福 2023-04-10 | **EUPD** | 第三方实际值 (3rd-party actual) |
| 6 | 德国 2021 户储装机 | 729MW / 1268MWh | 2021A | 华福 2023-04-10 | ISEA | 第三方实际值 (3rd-party actual) |
| 7 | 美国 2022 前三季装机 | 460MW / 1120MWh | 2022Q1-3 | 华福 2023-04-10 | WoodMac | 第三方实际值 (3rd-party actual) |
| 8 | 欧洲户储装机"相对稳健" | 定性 (no number) | 2023 | 派能 IR 2024-04-30 | 公司口径 | 定性 (qualitative) |

## 2. Rule-3 选用的字段锚点

```
Installation Field (Rule-3 input)
  2022 Global Residential Storage Installation = 23.6 GWh
  2023 Global Residential Storage Installation = 34.4 GWh
  Source: 华福证券 2023-04-10《扎根户储扬帆起航，定增扩产量利双升》
          原文：全球户储装机规模 12.2/23.6/34.4GWh，同比增长 115%/93%/46%
  Tier:   L4 forecast (sell-side estimate, 2023 为 E 预测值)
```

为什么不用 #3 的 12.2：12.2 = 2021 global，是序列单点，无法支撑 `installation_growth`。
Rule-3 需要的是 2022→2023 同比关系，故取 23.6→34.4。

为什么不用 #5 德国 EUPD 2.1GWh（唯一第三方实际值）：单点、仅德国、仅 2022，
无配对的 2023 actual，无法构成 `installation_growth`。只能作为"欧洲装机非零"的旁证。

## 3. Rule-3 推导（Field → Rule → Verdict 闭环）

```
INPUT FIELDS
  shipment      3.5 → 1.9 GWh   (-47%)   Paine company level   [L2 年报 + L4 estimate]
  installation  23.6 → 34.4 GWh (+46%)   Global market level   [L4 forecast]
  inventory     0.6 GWh         (+14%)   Paine company level   [L4 estimate]

RULE-3 (channel-inventory invariant)
  IF shipment_growth < installation_growth  AND  inventory_change > 0
  THEN channel_destocking / inventory-cycle explanation supported

EVALUATION
  shipment_growth (-47%) < installation_growth (+46%)   ✓
  inventory_change (+14%) > 0                           ✓
  → channel_destocking 命中

VERDICT
  shipment 大幅下滑 与 installation 增长 不一致
  → "终端需求崩塌" 解释被削弱 (demand_collapse weakened)
  → "渠道去库存/库存周期" 解释获得字段支持 (channel_destocking supported)
  → 与 reversal findings 的叙事结论一致，但此处由 Rule 推出，非由叙事断言。
```

## 4. Residual Risk（必须随 Verdict 一起呈现，不可省略）

### 4.1 ADR 六字段记录（per `evidence_gap_source_adr_v0.md` §"Required Recording Fields"）

| Field | Value |
| --- | --- |
| **Gap Type** | Quality Gap (Type B — Field Hierarchy Mismatch) |
| **Description** | installation 字段为 global market level（华福卖方测算, 2023=E 预测），与同 Rule 内的 shipment / inventory 字段（Paine company level）口径不对等。三者处于不同分析层级，无法在严格意义上构成同一层级的"同比对照"。 |
| **Impact Scope** | 影响 Rule-3 (channel-inventory invariant) 的因果链强度：Rule 仍可被触发达成 verdict，但 verdict 强度从 PROVEN 降为 SUPPORTED；具体削弱 `channel_destocking is PROVEN`，仅保留 `demand_collapse is WEAKENED`。 |
| **Blocks Method Validation** | No（Field→Rule→Verdict 闭环存在；Method Validation 仍可进行） |
| **Confidence Penalty** | Medium（gap 影响 verdict 因果链强度，但不影响 Field/Rule/Verdict 结构本身的存在） |
| **Mitigation Path** | 引入 SolarPower Europe 欧洲住宅储能装机年报作为 Paine-relevant market level 的独立第三方 actual 源；或引入 EUPD 全欧年度户储装机 actual（不止德国）以构造 2022→2023 实际同比。两者均为新 provider / 新数据范畴，需 G 批准突破"不扩 provider"冻结边界；当前 out of scope。 |

### 4.2 完整 Residual Risk 展开

```
EVIDENCE QUALITY RISK — 字段口径不对等 (level mismatch)
  installation : GLOBAL market level   (华福卖方测算, 2023 为预测值 E)
  shipment     : PAINE company level   (公司年报 + 卖方估算)
  inventory    : PAINE company level   (卖方估算)

后果：
  Global Installation Growth  ≠  Direct Proof of Paine End-Demand

因此 Rule-3 的能力边界是：
  ✓ 可支持   demand_collapse is WEAKENED
  ✗ 不可支持 channel_destocking is PROVEN

  即：能反驳"终端需求崩塌"这个强叙事，
      但不能把"渠道去库"升级为已证明的结论。

次级风险：
  - installation 2023 = 34.4 GWh 是华福 2023-04 的 E 预测值，非事后实际值
  - 唯一第三方实际锚 (德国 EUPD 2.1GWh / ISEA / WoodMac) 为单点、不成对，未入 Rule
  - 真正可消除此 gap 的独立源 (SolarPower Europe 欧洲住宅储能装机年报) = 新 provider，
    out of current scope，未引入。
```

> **本节为 Review Alignment Patch (per G 2026-06-11 拍板)**:仅补 ADR 六字段表,不改 §3 Rule-3 推导、不改 §5 Closure 状态、不改 §6 Changelog 既有结论。

## 5. Task #19 Closure 状态

```
Field exists        ✓  installation 23.6 → 34.4 GWh (was: 定性)
Rule exists         ✓  Rule-3 channel-inventory invariant
Verdict exists      ✓  channel_destocking supported / demand_collapse weakened
Field→Rule→Verdict  ✓  闭环（由 Rule 推出，非叙事断言）

Residual Risk       ⚠  global-vs-company level mismatch
Method status       CANDIDATE (not PROVEN)
Evidence level      PASS WITH EVIDENCE GAP
```

## 6. Changelog

- 2026-06-11: v0。Task #19 closure。抓取 reversal findings 已登记 4 份研报 + IR，
  补齐 installation 字段（8 数字表 + 质量评级）。Rule-3 取华福全球口径 23.6→34.4 GWh。
  保留 global-vs-company level mismatch 作为 residual risk（per G 指令）。
  判定 PASS WITH EVIDENCE GAP / METHOD CANDIDATE，非 METHOD PROVEN。

