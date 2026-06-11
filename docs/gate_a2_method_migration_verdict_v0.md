# Gate A-2 Verdict — Method Migration Assessment v0

> Scope: 沐邦 + 派能 Cross-Case，Serenity 方法论可迁移性裁决
> Decision authority: G (user)
> Author: CC (Claude Code)
> Date: 2026-06-11
> Precondition satisfied: Task #19 (Paine installation field) CLOSED
> Parent: `gate-a1-closed-method-gap-located` / `t2_paine_installation_evidence_v0.md`

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

## 6. 后续（非本 Gate 范围，仅登记）

- Method PROVEN 需更多样本（Session 2 北方华创 / Session 3 工业富联等）补足 n。
- 派能 evidence gap 若要闭合 → 需 G 批准引入新 provider（突破 "不扩 provider" 冻结边界）。
- 本 Gate 不解冻 Layer 4 / Runtime / Contract，维持既有冻结。

## 7. Changelog

- 2026-06-11: v0。G 裁决。Task #19 closure 后 Method Migration NOT YET → DEMONSTRATED (N=2)。
  Gate A-2 PASS / Method CANDIDATE / Method Proven NO / PASS WITH EVIDENCE GAP。
