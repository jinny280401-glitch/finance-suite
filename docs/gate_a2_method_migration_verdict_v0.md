# Gate A-2 Verdict — Method Migration Assessment v0

> Scope: 沐邦 + 派能 Cross-Case，Serenity 方法论可迁移性裁决
> Decision authority: G (user)
> Author: CC (Claude Code)
> Date: 2026-06-11
> Precondition satisfied: Task #19 (Paine installation field) CLOSED
> Parent: `gate-a1-closed-method-gap-located` / `t2_paine_installation_evidence_v0.md`
> Governance References: `evidence_gap_source_adr_v0.md` (ADR — Evidence Gap Source Must Be Explicitly Recorded)

## 1. Final Status Board

```
Gate A-2 ............... PASS
Framework Migration .... DEMONSTRATED
Method Migration ....... DEMONSTRATED (N=2)
Method Status .......... CANDIDATE
Evidence Level ......... PASS WITH EVIDENCE GAP
Method Proven .......... NO
Method Confidence ...... MEDIUM
```

## 2. Timeline — 为什么状态从 NOT YET 变为 DEMONSTRATED

| 阶段 | 事实 | Method N | Method Migration |
|---|---|---|---|
| **A — Task #19 之前** | Mubang: Field→Rule→Verdict ✓；Paine: Narrative→Verdict ✓；installation 缺失 | N=1 (仅 Mubang) | NOT YET |
| **B — Task #19 之后** | Mubang: Field→Rule→Verdict ✓；Paine: Field→Rule→Verdict ✓ (带 residual risk) | **N=2** | **DEMONSTRATED** |

阶段 A 的 "NOT YET" 前提是 **installation 缺失**。Task #19 完成后该前提被消除，
故不再适用 "Method Migration = NOT YET"。

## 3. 关键区分 — Migration ≠ Proven

```
Method Migration  = 方法在第二个不同案例上可复现 Field→Rule→Verdict 结构
                  → N=2 已满足 (Mubang + Paine)
                  → DEMONSTRATED

Method Proven     = 方法在足够样本上稳定且证据无重大 gap
                  → 当前 n=2，其中 1 PASS + 1 PASS WITH EVIDENCE GAP
                  → 远不足以称 PROVEN
                  → NO
```

两者最易混淆。迁移性已有两个不同案例支撑（财务字段案 + 卖方叙事案）；
但证明程度受限于样本量与派能的 evidence gap，故 Method 仅为 **CANDIDATE**。

## 4. Cross-Case 对照

| 维度 | 沐邦高科 | 派能科技 |
|---|---|---|
| 案例类型 | 财务字段自洽性 | 卖方叙事反转 |
| Field→Rule→Verdict | 成立 | 成立（带 residual risk） |
| Verdict | PASS | PASS WITH EVIDENCE GAP |
| 列5 Rule 吃什么 | 公司/监管披露硬数字 | 字段同比关系 (Rule-3) |
| Evidence 独立性 | 高（监管函 L1 自证） | 中（installation 为卖方测算 L4 + 口径不对等） |
| 主要 gap | 无 | global-vs-company level mismatch |

## 5. Residual Risk（随判定一起记录）

### 5.1 ADR 六字段记录（per `evidence_gap_source_adr_v0.md` §"Required Recording Fields"）

| Field | Value |
| --- | --- |
| **Gap Type** | Quality Gap (Type B — Field Hierarchy Mismatch) |
| **Description** | installation 字段为 global market level（华福卖方测算, 2023=E 预测），与同 Rule 内的 shipment / inventory 字段（Paine company level）口径不对等。三者处于不同分析层级，无法在严格意义上构成同一层级的"同比对照"。 |
| **Impact Scope** | 影响 Rule-3 (channel-inventory invariant) 的因果链强度：Rule 仍可被触发达成 verdict，但 verdict 强度从 PROVEN 降为 SUPPORTED；具体削弱 `channel_destocking is PROVEN`，仅保留 `demand_collapse is WEAKENED`。 |
| **Blocks Method Validation** | No（Field→Rule→Verdict 闭环存在；Method Validation 仍可进行） |
| **Confidence Penalty** | Medium（gap 影响 verdict 因果链强度，但不影响 Field/Rule/Verdict 结构本身的存在） |
| **Mitigation Path** | 引入 SolarPower Europe 欧洲住宅储能装机年报作为 Paine-relevant market level 的独立第三方 actual 源；或引入 EUPD 全欧年度户储装机 actual（不止德国）以构造 2022→2023 实际同比。两者均为新 provider / 新数据范畴，需 G 批准突破"不扩 provider"冻结边界；当前 out of scope。 |

> ADR 引用闭环:本节六字段格式遵循 `evidence_gap_source_adr_v0.md` §"Required Recording Fields"(Accepted, 2026-06-11)。六字段 gap 条目与 `t2_paine_installation_evidence_v0.md` §4.1 一致;gate_a2 → ADR → installation_evidence → reversal findings 形成完整追溯链。

### 5.2 完整 Residual Risk 展开

```
派能 PASS WITH EVIDENCE GAP 的 gap 内容：
  installation : global market level  (华福卖方测算, 2023=E 预测)
  shipment     : Paine company level
  inventory    : Paine company level
  → Global Installation Growth ≠ Direct Proof of Paine End-Demand
  → 可支持 demand_collapse WEAKENED；不可支持 channel_destocking PROVEN

消除此 gap 需引入 SolarPower Europe 欧洲住宅储能装机年报（新 provider，
out of current scope，未引入）。
```

> **本节为 Review Alignment Patch (per G 2026-06-11 拍板)**:仅补 ADR 六字段表 + 引用闭环,不改 §1 状态板、不改 §3 Migration/Proven 区分、不改 §4 Cross-Case 对照、不改 §6 后续登记。Method/Rule/Contract/Conclusion 全部维持。

## 6. 后续（非本 Gate 范围，仅登记）

- Method PROVEN 需更多样本（Session 2 北方华创 / Session 3 工业富联等）补足 n。
- 派能 evidence gap 若要闭合 → 需 G 批准引入新 provider（突破 "不扩 provider" 冻结边界）。
- 本 Gate 不解冻 Layer 4 / Runtime / Contract，维持既有冻结。

## 7. Changelog

- 2026-06-11: v0。G 裁决。Task #19 closure 后 Method Migration NOT YET → DEMONSTRATED (N=2)。
  Gate A-2 PASS / Method CANDIDATE / Method Proven NO / PASS WITH EVIDENCE GAP。

- 2026-06-11: v0 Review Alignment Patch (per G 拍板 Option A: Review / Cross-reference Alignment Only)。
  补两项对齐,不动结论:
  1. §5 Residual Risk 改写为 ADR §"Required Recording Fields" 六字段表 (§5.1),原文本块保留为 §5.2 展开。
  2. frontmatter 加 `Governance References: evidence_gap_source_adr_v0.md`,建立
     `gate_a2 → ADR → t2_paine_installation_evidence_v0 §4.1 → t2_paine_reversal_findings_v0` 完整追溯链。
  同步在 `t2_paine_installation_evidence_v0.md` §4.1 加六字段表。
  不动:§1 状态板 / §3 Migration≠Proven 区分 / §4 Cross-Case 对照 / Method / Rule-3 / Contract / Runtime / Scope / Session 2/3。
