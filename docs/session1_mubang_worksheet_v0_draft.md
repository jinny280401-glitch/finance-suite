# Session 1 — 沐邦高科 Case 8 列 Worksheet v0 Draft

> **Status:** Pre-Session-1 draft. 现场可重填 / 拆 assertion。
> **Created:** 2026-06-08
> **Owner:** Session 1 participants
> **Parent docs:**
> - L0 ontology: `docs/L0_verification_ontology_v0_draft.md`
> - 8 列 template: `docs/8_column_worksheet_template_v0_draft.md`
> - T1 evidence (C): `docs/session1_t1_mubang_inquiry_findings_v0.md`
> - Agent directive: `docs/agent_directive_supply_chain_consistency_discovery_v0.md`

---

## 0. Session 1 Goal (per user lock-in)

**不是**判断沐邦好坏。**是**验证 L0 ontology 能否在 1 个真实 case 上稳定工作。具体 4 件事：

```
1. Type 分类        5 类 invariant (Mirror / Capacity / Cash-Logistics / Temporal / Transitivity)
                    能否准确指派到 assertion
2. Evidence Mapping  监管问询函 / 公告 / 卖方研报 等 filing 能否锚定到 8 列的列 4
3. Conflict 类型     5 个 subtype (direct / chain / amount / direction / timing)
                    能否在 conflicting_evidence 时正确分桶
4. Verdict 生成     5 状态 (verified / tried_not_found / not_attempted / conflicting_evidence / tolerance_unresolved)
                    能否在 4 个 assertion 上各产出 1 个合理状态
```

**延后到 P0d**：Verdict Aggregation（一个 Question 下多 Assertion 的 Verdict 怎么聚合）。

---

## 1. Case Meta

```
Case:              沐邦高科 (603398.SH) 跨界光伏 negative test
ListedCompany:     沐邦高科 (原名 邦宝益智, 2022 跨界)
OperatingEntity:   豪安能源 (光伏子公司)
Key Counterparty:  共青城奇峰 (后被确认关联)
Date of Run:       2026-06-08
Run Owner:         C
Reviewer:          User / G review pending
```

---

## 2. Question (唯一)

> **Q1**: 沐邦高科跨界光伏业务的客户收入是否能支撑其产能扩张故事？

**为什么只 1 个 Question**：
- 4 个 assertion 都服务于 "产能扩张故事" 这一个核心问题
- Question 必须聚焦，否则 8 列 worksheet 散

---

## 3. Assertions (4 个)

### Assertion A — 关联客户共青城奇峰 [NEGATIVE TEST]

| 列 | 值 |
|---|---|
| attempt_id | `A-001-mubang-related-customer` |
| 1. Serenity Question | (Q1 引用) |
| 2. Assertion | [NEGATIVE TEST] 豪安能源 2024 年对共青城奇峰 3178.54 万元硅片销售具备独立商业实质且非关联交易 |
| 3. Extraction Field | `OperatingEntity.revenue_cny`=3178.54万; `Counterparty.is_related_party`=True (公司承认); `Counterparty.downstream_sale`=1994.40万; `price_diff`=1184.14万 |
| 4. Evidence Source | [L1] MB-2025-AR-PARTIAL-REPLY (cninfo 2025-07-11, 关于共青城奇峰关联交易、收入冲减、前期未列关联方部分); [L5 lead only] MB-2025-NBD-1 / MB-2025-NBD-2 (媒体交叉线索，不单独支撑 verdict) |
| 5. Matching Rule | **Type 1 (Mirror Relations)** + **Type 3 (Cash vs Logistics)** |
| 6. Tolerance | `is_related_party` 0/1 binary, **no tolerance**; 价格差 ±5%; 下游转售比例 ±10% |
| 7. Verdict | **`conflicting_evidence`** |
| 8. Conflict Source | **`direct_contradiction`** (公司未列为关联方 vs 实际近亲属控制) + secondary `amount_contradiction` (3178.54 vs 1994.40 差 1184.14) |

**4-Goal 验证标记**：

| Goal | 验证 |
|---|---|
| Type 分类 | Type 1 (供应商-客户镜像) + Type 3 (现金-物流一致) 是否准确指派？ |
| Evidence Mapping | cninfo PDF + 媒体 cross-validation 能否锁定 filing_id？ |
| Conflict 类型 | `direct_contradiction` vs `amount_contradiction` 哪个是 primary？ |
| Verdict 生成 | `conflicting_evidence` 是否合理？(公司自己承认 → 应该是高 confidence) |

**Open items (from C)**：
- Page-level PDF 引用待现场确认
- 关联关系是 2025 年报问询后才被监管确认，前期公司自己说"不是关联方"

---

### Assertion B — 10000 吨硅提纯项目资金 [NEGATIVE TEST]

| 列 | 值 |
|---|---|
| attempt_id | `B-001-mubang-fund-flow` |
| 1. Serenity Question | (Q1 引用) |
| 2. Assertion | [NEGATIVE TEST] 10000 吨/年智能化硅提纯循环利用项目募集资金投入与在建工程形成金额一致，且资金未通过供应商流向关联方或被挪用 |
| 3. Extraction Field | `CapexProject.total_budget`; `CapexProject.disclosed_capex`; `amount_cny`; `is_related_party` (供应商中基建设); `fund_diversion_flag` |
| 4. Evidence Source | [L1] MB-2025-AR-PARTIAL-REPLY (cninfo 2025-07-11), problem one (募集资金违规，主问题 deferred) + problem four (募投项目真实性 / 中基建设 4,800 万转出) |
| 5. Matching Rule | **Type 3 (Cash vs Logistics)** |
| 6. Tolerance | 募集资金投入 vs 在建工程形成 ±10%; `fund_diversion_flag` 0/1 binary |
| 7. Verdict | **`conflicting_evidence`** (局部反证成立；完整资金流逐项对账仍 deferred) |
| 8. Conflict Source | `chain_contradiction` (募集资金经供应商转出/流转) + secondary `amount_contradiction` (21,920.00 / 28,858.00 / 22,967.63 / 4,501.31 / 3.24 亿 / 1.05 亿 / 3,078.65 万多口径不一致) |

**4-Goal 验证标记**：

| Goal | 验证 |
|---|---|
| Type 分类 | Type 3 单选是否准确？(是否需要 Type 5 transitivity?) |
| Evidence Mapping | regulator 列出多个不一致金额 (21920 / 28858 / 22967.63 万元), 哪个是 ground truth? |
| Conflict 类型 | `amount_contradiction` (多金额不一致) vs `chain_contradiction` (资金链断) |
| Verdict 生成 | **核心争议**: 公司对 problem 1 "未实质回复", 是 `tolerance_unresolved` (公司没回答, 暂时 undecidable) 还是 `conflicting_evidence` (regulator 已识别多个反证, 推断 conflict)? |

**Open items (from C)**：
- 公司对 problem 1 答复 deferred, 现场需要决定如何处理 "公司没答"
- 4,800 万经中基建设转出已披露, 是否构成 "已承认 conflict" 阈值？

**Session 1 决策点结果**：B 不能仅因 problem one deferred 而整体写 `not_attempted`。L1 同一回复已披露 4,800 万募集资金通过中基建设转出，足以反驳 assertion 中“资金未通过供应商流向关联方或被挪用”的子句；但“募集资金投入与在建工程形成金额一致”的完整逐项对账仍 deferred，形成 L0 gap：compound assertion 需要拆分或允许 row-level notes。

---

### Assertion C — 2023 扩产合理性 [NEGATIVE TEST]

| 列 | 值 |
|---|---|
| attempt_id | `C-001-mubang-expansion-vs-impairment` |
| 1. Serenity Question | (Q1 引用) |
| 2. Assertion | [NEGATIVE TEST] 2023 年所称适度产能扩张在 2024 年仍按计划推进, 关键在建项目 (10GW TOPCON, 5000 吨硅提纯, 3GW 单晶硅棒) 不存在重大减值或延期风险 |
| 3. Extraction Field | `capacity_value`; `capacity_status`; `yoy_capex_growth`; `project_progress_pct`; `impairment_amount_cny` |
| 4. Evidence Source | [L1] MB-2023-AR-REPLY (cninfo 2024-07-27, 2023 baseline / 适度产能扩张); [L1] MB-2025-AR-PARTIAL-REPLY (2024 固定资产和在建工程 / 延期 / 减值 / 5000 吨尚未达投产条件) |
| 5. Matching Rule | **Type 2 (Capacity Chain)** + **Type 4 (Temporal Alignment)** |
| 6. Tolerance | 工程进度 ±10%; 时间窗口 ±2 季度; 减值金额 ±15% |
| 7. Verdict | **`conflicting_evidence`** |
| 8. Conflict Source | **`timing_contradiction`** (2023 承诺 vs 2024 延期/减值) + `chain_contradiction` (扩产计划 vs 项目真实进度) |

**4-Goal 验证标记**：

| Goal | 验证 |
|---|---|
| Type 分类 | Type 2 (产能链) + Type 4 (时间窗) 双指派是否合理？ |
| Evidence Mapping | 两个跨年度 filing 能否对账？(2023 baseline vs 2024 实际) |
| Conflict 类型 | `timing_contradiction` (主) + `chain_contradiction` (次) 哪个优先？ |
| Verdict 生成 | 多项目都减值 (9565.74 万 + 3993.89 万 + 1.05 亿其他减少), `conflicting_evidence` 置信度高 |

**Numeric anchors (from C)**：

| 项目 | 2024 末余额 | 进度 | 减值 |
|---|---:|---:|---:|
| 10GW TOPCON | 10.78 亿 | 42.27% | 延期 (2023-03-30 → 2024-09) |
| 5000 吨硅提纯 | 2.40 亿 | 57.9% | 9,565.74 万 |
| 二期 3GW 单晶 | 2.84 亿 | 57.9% | 3,993.89 万 |
| 在建工程其他减少 | — | — | 1.05 亿 |

---

### Assertion D — 2023 baseline [VERIFIED BASELINE]

| 列 | 值 |
|---|---|
| attempt_id | `D-001-mubang-2023-baseline` |
| 1. Serenity Question | (Q1 引用) |
| 2. Assertion | 2023 年光伏板块营收 9.43 亿元 (同比 +37.76%)、毛利率 8.24% (同比 -11.05pct) 是公司自己披露的 historical fact |
| 3. Extraction Field | `revenue_cny`=9.43亿; `yoy_revenue_growth`=+37.76%; `gross_margin_pct`=8.24%; `yoy_margin_change_pct`=-11.05pct |
| 4. Evidence Source | [L1] MB-2023-AR-REPLY (cninfo 2024-07-27, 监管工作函回复载体); [L2] 公司在回复中披露的 2023 光伏板块历史经营数据 |
| 5. Matching Rule | **Type 4 (Temporal Alignment)** — 作为 2023 historical baseline 锚点；非严格 Type 1 mirror，因为本行没有外部 counterparty 对照 |
| 6. Tolerance | ±2% (财务数据 round-trip 容差) |
| 7. Verdict | **`verified`** |
| 8. Conflict Source | (空) |

**4-Goal 验证标记**：

| Goal | 验证 |
|---|---|
| Type 分类 | Type 1 单选是否合理？(没有 cross-counterparty, 更像 "公司自证", 不严格是 mirror) |
| Evidence Mapping | 2023 年报工作函回复是 filing 还是解读？ (它是监管要求公司对 2023 年报做的解释) |
| Conflict 类型 | (空, verified) |
| Verdict 生成 | `verified` 的依据不是 "未发现冲突"，而是同一 [L1] filing 中正文披露与后文营业收入表相互闭合：正文列示 9.43 亿元/+37.76%/8.24%/-11.05pct，后文表格列示营业收入 94,255.10 万元、上期 68,420.07 万元、变动比例 37.76%。本 verdict 只覆盖 historical baseline 数字本身，不覆盖扩产合理性。 |

**为什么必须加 D**：
- SC2 要求 5 种 Verdict 至少覆盖 4 种。3 个 negative 都是 `conflicting_evidence`, D 提供 `verified` 锚点
- 验证 L0 ontology **不只**测 negative, 也能正常处理 verified
- 数据可信度最高 (公司自己披露 + 监管函引用), 给 negative assertion 平衡

---

## 4. 4-Goal Coverage Matrix (Session 1 验证目标总览)

| Goal | A (related) | B (fund) | C (expansion) | D (baseline) |
|---|---|---|---|---|
| Type 分类 | Type 1+3 双指派 | Type 3 单选 (待讨论) | Type 2+4 双指派 | Type 1 单选 (待讨论) |
| Evidence Mapping | cninfo + 媒体 cross | cninfo 多金额 | 跨年 filing 对账 | 单 filing 引用 |
| Conflict 类型 | direct + amount | amount vs chain (待定) | timing + chain | (空) |
| Verdict 生成 | conflicting (高) | **关键决策点** | conflicting (高) | verified (高) |

**5 种 Verdict 实际触发**：
- A → `conflicting_evidence`
- B → `tolerance_unresolved` OR `conflicting_evidence` (Session 1 决定)
- C → `conflicting_evidence`
- D → `verified`
- 覆盖: 2-3 / 5 (A/C/D 已覆盖, B 决定后覆盖 3-4 / 5)

**SC2 验收**: 5 种 Verdict 至少 4 种, conflicting_evidence 必须出现。Session 1 完成后, 应至少 3 种。完整 SC2 验收留 Session 2+3 (派能/半导体/苹果链)。

---

## 5. 5-Goal NOT in Scope (per user)

| 延后项 | 留到 |
|---|---|
| Verdict Aggregation (Q1 下 4 个 Verdict 怎么聚合) | **P0d** Verdict Contract |
| Cross-case ontology 稳定性 (SC1) | Session 2+3 |
| 5 Verdict 全覆盖 (SC2) | Session 2+3 |
| P0a.5b.a 5 个不可验证问题清单 (SC3) | Session 4 |
| Tolerance 默认值 (P0a.5c) | Session 4 |
| L0 v0.1 修订 (3 个发现: Counterparty 下游链 / is_related_party invariant / Filing 反向 relation) | Session 1 后 |

---

## 6. Session 1 Runtime Notes

### 6.1 时间分配 (90 分钟)

```
0-10 min   重读 L0 ontology + 8 列模板 + 本 worksheet, 锁定 4 件事的验证标准
10-30 min  Assertion A 现场跑 (8 列填 + 4-Goal 检查)
30-50 min  Assertion B 现场跑 (Verdict 决策点重点讨论)
50-70 min  Assertion C 现场跑 (跨年对账重点)
70-85 min  Assertion D 现场跑 (verified 路径)
85-90 min  4-Goal Coverage Matrix 总结 + 决议 L0 v0.1 修订清单
```

### 6.2 现场决策点

1. **B 的 Verdict 决策**: `tolerance_unresolved` vs `conflicting_evidence` (公司 deferred answer)
2. **C 的 Conflict Source 主次**: `timing_contradiction` vs `chain_contradiction` 哪个 primary
3. **D 的 Type 选择**: Type 1 (mirror) 是否合理, 还是该新增 Type 7 "公司自证"
4. **L0 v0.1 修订清单**: 3 个发现 (Counterparty 下游链 / is_related_party invariant / Filing 反向) 是否都进 v0.1

### 6.3 不能现场决定的问题

- Verdict Aggregation 怎么定义 (Q1 聚合函数) → P0d
- 是否要把 B 的 `tolerance_unresolved` 当成新 Verdict 子状态 → P0d
- 5 Verdict 全覆盖怎么在 Session 1 强制达成 → 不可能, 留给 Session 2+3

---

## 7. Evidence Strength L1-L5 (per G lock-in, 2026-06-08)

### 7.1 为什么需要这个

不同 source 的 evidence 强度不同。当 conflicting_evidence 涉及多 source, 必须有 strength hierarchy 才能 derive final_verdict。缺这个, conflicting 不可自动 solve。

### 7.2 L1-L5 定义

| Level | Source Type | 例子 | 强度 |
|---|---|---|---|
| **L1** | 监管问询函 (regulator inquiry) | MB-2025-AR-PARTIAL-REPLY, MB-2025-PERF-INQUIRY | 最高 |
| **L2** | 上市公司公告 (listed company announcement) | cninfo 公告, 定期报告, 临时公告 | 高 |
| **L3** | 审计意见 (audit opinion) | 审计报告, 内控审计报告 | 高 |
| **L4** | 卖方研报 (sell-side research) | 卖方券商研报 | 中 |
| **L5** | 媒体报道 (media coverage) | 财经媒体, 行业自媒体 | 弱 |

**NOT in L1-L5**（不是 evidence）：
- LLM 生成的 "fact"（不在任何 source）
- 推特/雪球个人发言
- 同事口头
- 任何无法追溯到具体 filing_id / source_url 的陈述

### 7.3 Per-Assertion Evidence Strength Map

| Assertion | Primary Source(s) | Strength | 备注 |
|---|---|---|---|
| A 关联客户 | MB-2025-AR-PARTIAL-REPLY (regulator) + MB-2025-NBD-1 (媒体) | **L1** + L5 | L1 自证 conflict, L5 仅作 catalyst |
| B 资金流 | MB-2025-AR-PARTIAL-REPLY problem 1 (regulator) | **L1** | regulator 列出反证, 公司 deferred |
| C 扩产减值 | MB-2023-AR-REPLY + MB-2025-AR-PARTIAL-REPLY (regulator × 2) | **L1** + L1 | 跨年 regulator material, 双 L1 |
| D 2023 baseline | MB-2023-AR-REPLY (regulator 引用公司 L2 数据) | **L1** (载体) + L2 (数据) | 单源 verified, 但数据本身是 L2 (公司披露) |

### 7.4 Strength Hierarchy 在 Verdict 推导中的作用（示例）

| 场景 | 来源 | 推导 |
|---|---|---|
| L1 说 "X 是关联方" vs L4 说 "X 不是关联方" | regulator vs 卖方 | L1 wins → final_verdict = conflicting_evidence |
| L4 (A 券商) 说 "产能扩张合理" vs L4 (B 券商) 说 "产能扩张有风险" | 同级卖方 | 平局, 需 sub-tier (大行 vs 中小行, TBD) |
| L5 (媒体) 报道 vs L1 (regulator) 数据 | 媒体 vs regulator | L1 wins, L5 仅作 catalyst 信号, **不作 evidence 基础** |
| L1 (监管问询) 公司未答 vs L2 (公司公告) 解释 | regulator 质疑 vs 公司自辩 | L1 wins, 公司 deferred 视为 `tolerance_unresolved` 而非 `verified` |

### 7.5 Session 1 现场记录任务

每行 Column 4 (Evidence Source) 必须**显式标注 L1-L5**。pre-fill 表格里 4 个 assertion 的 strength 已在 Section 7.3 标好, 现场确认即可。

### 7.6 Open Items for Session 1 → L0 v0.1

- L1-L5 之间的相对强度: numerical (L1=100, L2=?, L3=?, L4=?, L5=?) 还是 ordinal?  **L0 v0.1 决定**
- L4 内部 sub-tier (大行/中小行) 是否需要? **L0 v0.1 决定**
- L5 是否完全排除作 evidence, 还是分 sub-type (财经头条 vs 行业数据汇编)? **L0 v0.1 决定**

## 8. Changelog

- 2026-06-08: v0 草稿。基于 C 的 T1 findings + 用户 5 条指令 (GO 1-5)。4 assertions: A 关联客户 (Type 1+3) / B 资金流 (Type 3) / C 扩产减值 (Type 2+4) / D 2023 baseline (Type 1)。Verdict Aggregation 显式延后到 P0d。
- 2026-06-08 (晚): 加 Section 7 Evidence Strength L1-L5 (per G 反馈)。L1-L5 backlog 进 L0 v0.1 修订清单。
