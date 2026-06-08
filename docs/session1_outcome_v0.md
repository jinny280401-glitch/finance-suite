# Session 1 Outcome v0 — Mubang Supply Chain Consistency Model

> Status: Session 1 outcome only. Not P0b/P0c/P0d contract.
> Date: 2026-06-08
> Runner: C
> Scope: Mubang case; assertions A/B/D required, C reviewed within timebox.

## 1. Verdicts Produced

| Assertion | Scope | Evidence Source | Verdict | Conflict Source |
|---|---|---|---|---|
| A | 关联客户共青城奇峰 | [L1] MB-2025-AR-PARTIAL-REPLY; [L5 lead only] NBD media | `conflicting_evidence` | `direct_contradiction` + secondary `amount_contradiction` |
| B | 资金流 / deferred answer | [L1] MB-2025-AR-PARTIAL-REPLY problem one + problem four | `conflicting_evidence` | `chain_contradiction` + secondary `amount_contradiction` |
| C | 扩产减值 | [L1] MB-2023-AR-REPLY; [L1] MB-2025-AR-PARTIAL-REPLY | `conflicting_evidence` | `timing_contradiction` + secondary `chain_contradiction` |
| D | 2023 baseline | [L1] MB-2023-AR-REPLY; [L2] company disclosed historical data | `verified` |  |

## 2. Per-Assertion Notes

### A — 关联客户共青城奇峰

Final verdict: `conflicting_evidence`.

Reason: [L1] 公司 2025 年部分回复披露，前期未将共青城奇峰列为关联方；后续核查发现共青城奇峰实控人与豪安能源原实控人存在近亲属关系。公司同时披露对共青城奇峰合同销售金额 3,178.54 万元，下游终端客户销售金额 1,994.40 万元，差额 1,184.14 万元，并对交易价格不公允部分收入进行冲减。

Model result: Type 1 + Type 3 能稳定承载该行。Column 8 primary 应为 `direct_contradiction`，金额差异作为 secondary。

### B — 资金流 / deferred answer

Final verdict: `conflicting_evidence`.

Reason: problem one 的完整逐项资金流回复确实 deferred；但同一 [L1] 回复在 problem four / 预付款核查部分披露，内蒙古沐邦用于 10,000 吨项目的募集资金 4,800 万元通过供应商中基建设转出，并披露部分预付款流入控股股东后流转回上市公司。该证据足以反驳本 assertion 中“资金未通过供应商流向关联方或被挪用”的子句。

Boundary: “募集资金投入与在建工程形成金额一致”仍无法完整 verified，因为 21,920.00 万、28,858.00 万、22,967.63 万、4,501.31 万、3.24 亿、1.05 亿、3,078.65 万等口径仍需公司后续完整回复或逐项拆分。

Model result: B 暴露出 compound assertion gap。一个 assertion 同时包含“资金未挪用”和“金额一致”两类判断时，单一 verdict 会压扁信息：前者已 conflict，后者仍 deferred / unresolved。

### C — 扩产减值

Final verdict: `conflicting_evidence`.

Reason: [L1] 2023 工作函回复中，公司在毛利率下行背景下仍称“适度产能扩张具备合理性”；[L1] 2025 部分回复披露 2024 年末在建工程、项目进度、延期和减值：10GW TOPCON 期末余额 10.78 亿元、进度 42.27%，预计投产从 2023-03-30 延至 2024-09 后又延至 2025-08；5000 吨项目期末余额 2.40 亿元、进度 57.9%、减值 9,565.74 万元；二期 3GW 项目期末余额 2.84 亿元、进度 57.9%、减值 3,993.89 万元；5000 吨第一代项目尚未达到投产条件。

Model result: Type 4 primary 更自然，Type 2 secondary。冲突不是单一金额错配，而是跨期叙事从“适度扩张合理”转为“延期、减值、未达投产条件”。

### D — 2023 baseline

Final verdict: `verified`.

Reason: [L1] 2023 年报工作函回复载体中披露/引用公司 2023 光伏板块营业收入 9.43 亿元，同比 +37.76%，毛利率 8.24%，同比 -11.05pct；同一回复后文营业收入表列示 94,255.10 万元、变动比例 37.76%。本行只验证 historical baseline，不验证扩产故事是否成立。

Positive evidence loop: D 的 `verified` 不是因为 “no conflict found / not challenged”。它来自同一 [L1] filing 内部的正向闭环：

1. 正文直接披露光伏板块营收 9.43 亿元、同比 +37.76%、毛利率 8.24%、同比 -11.05pct。
2. 后文营业收入表列示本期营业收入 94,255.10 万元、上期 68,420.07 万元、变动金额 25,835.03 万元、变动比例 37.76%。
3. 9.43 亿元与 94,255.10 万元在 ±2% round-trip tolerance 内一致；同比增长字段也一致。
4. 本 verdict 的范围只覆盖 2023 historical baseline 数字本身，不外推为 “扩产合理性 verified”。

Model result: D verified baseline pattern 成立，但必须被描述为 positive evidence closed-loop，而不是 absence-of-conflict。

## 3. Actual Ontology Gaps Found

1. Compound assertion needs handling.

B 同时包含 `fund_diversion_flag` 和 `capex_to_asset_amount_consistency`。实际运行中一个子句已经被 [L1] 反驳，另一个子句仍 deferred。L0 v0.1 需要决定：拆成两行 VerificationAttempt，还是在 row note 中允许 mixed boundary。

2. Historical baseline is not a clean Type 1 mirror.

D 没有 counterparty mirror，只是监管工作函回复中的 company historical fact。Type 4 Temporal Alignment 作为 baseline anchor 比 Type 1 更合适，但 L0 目前没有明确 “baseline fact” 的匹配姿势。

2a. Verified baseline needs positive evidence loop.

D 证明 `verified` 需要正向证据闭环：正文披露字段、同文表格字段、数值容差、verdict 范围限制。否则 `verified` 容易被误用成 “not challenged”。

3. Deferred answer is not itself a verdict.

B 显示 “公司另行回复 / deferred” 不能自动映射为 `not_attempted` 或 `tried_not_found`。如果同一材料中存在局部 L1 反证，verdict 仍可能是 `conflicting_evidence`，但 outcome 必须保留 deferred boundary。

4. Conflict Source may need primary / secondary convention.

A、B、C 都自然出现 primary + secondary conflict subtype。当前 Column 8 只有一个字段，但实际填表需要表达主次；本次暂用 “primary + secondary” 文本，不新增 subtype。

5. Evidence Source needs line/page precision backlog.

本次用 local text line anchors 和 source document ID 完成验证，但 worksheet 的 long-term audit 需要 PDF page-level citation 或 paragraph locator。该点是 Evidence Mapping 的实际 gap，不是 P0b 契约。

## 4. Open Items For Session 4 Synthesis

1. 是否把 B 拆成两行：
   - B1: 资金是否经供应商转出 / 被挪用
   - B2: 募集资金投入金额与在建工程形成金额是否一致

2. D-pattern 是否需要在 L0 v0.1 标注为 “baseline / historical fact row”，并规定其推荐 Matching Rule。

3. `verified` 是否需要显式记录 positive evidence loop，至少包含 field match、source locator、tolerance check、scope boundary。

4. Column 8 是否正式允许 primary / secondary conflict subtype，或保持单 primary + notes。

5. Evidence Source 是否要求最小 locator：document ID + page / section / local text anchor。

6. B 中 “deferred but partially contradicted” 应进入 P0a.5 的不可验证/延后分类说明，避免后续 verifier 把 deferred answer 误判成 `not_attempted`。

## 5. Blockers / Conflicts

No runtime blocker.

Main unresolved conflict: B 的完整资金流逐项对账依赖公司对 problem one 的后续完整回复；当前材料已足以识别局部反证，但不足以完成所有金额口径 reconciliation。

## 6. Files Touched

- `docs/session1_mubang_worksheet_v0_draft.md`
- `docs/session1_outcome_v0.md`

No commit. No push.
