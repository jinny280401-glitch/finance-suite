# Evidence Strength L1-L5 — Design Freeze v0

> **Status:** DESIGN FREEZE for Session 1+ and L0 v0.1 backlog
> **Created:** 2026-06-08
> **Source:** C feedback on Session 1 worksheet Section 7
> **Scope:** Lock the L1-L5 hierarchy decisions; supersedes ad-hoc reasoning

---

## 0. Why this file exists

Section 7 of `session1_mubang_worksheet_v0_draft.md` introduced L1-L5 as a column-4 annotation. C's review surfaced 3 sharp issues that need to be **frozen as a design decision** before Session 1 runs:

1. Numerical vs ordinal — premature numerical weights would fake precision
2. L3 (audit) ordering is **not always** ≈ L2 (company) — depends on issue type
3. L5 (media) is **not zero-evidence** — needs explicit "what it's good for" and "what it's not"

This file is the single source of truth for those 3 decisions. L0 v0.1 will reference it.

---

## 1. Frozen Decisions (5 items)

### 1.1 Numerical vs Ordinal — frozen as ORDINAL

```
L1-L5 是 ordinal 关系, NOT numerical
L1 ≠ 100, L2 ≠ 50, etc.
```

**Why ordinal, not numerical**:
- Sample size too small (1 case so far)
- Numerical weights give false sense of rigor
- Ordinal forces humans to make the relative judgment case-by-case
- Easy to upgrade to numerical later if evidence supports it

**When to revisit**:
- After Session 4 (4 cases done) and we have multi-case empirical base
- If a Session produces ambiguous final_verdict because ordinal isn't enough

### 1.2 Default ordering — frozen

```
L1 > L3 ≈ L2 > L4 > L5
```

Read top-down: L1 is strongest, L5 is weakest. L3 and L2 are roughly comparable by default.

### 1.3 L3 conditional override — frozen

```
Default: L3 ≈ L2
Override (财务真实性 issues): L3 > L2
```

**What counts as 财务真实性 issues**:
- 审计否定意见 / 保留意见 / 重大错报
- 内控审计报告的 non-financial reporting defect
- 监管问询中关于"收入确认差错""关联方识别错误""项目真实性"等具体问题

**What does NOT count** (still L3 ≈ L2):
- 业务模式判断
- 战略合理性
- 行业景气度
- 管理层能力

**Determination authority**: Per-attempt, decided by Verifier (LLM agent) using `IssueType` classification. P0d will define the classification enum.

### 1.4 L5 use scope — frozen

```
L5 不作 verified 基础, 但保留 lead / catalyst / contradiction clue
```

**L5 CAN be**:
- Lead: 媒体首次爆料 → trigger 进一步 L1-L4 验证
- Catalyst: 加速已有 verdict 的发现 (e.g., L1 已经在查, L5 提前把细节 push 出来)
- Contradiction clue: L5 反向爆料与 L1/L2 冲突 → 倒逼重新核查 L1/L2

**L5 CANNOT be**:
- 单独支撑 verified verdict (must be corroborated by L1-L4)
- 单独支撑 conflicting_evidence (must be corroborated, OR explicitly flagged as L5-contradiction-clue in Column 8)

**Specific examples that are valid L5 use**:
- 财经媒体引用监管原文 (L5 + L1 indirect)
- 行业数据汇编 (L5 + L2/L3)
- KOL 反向爆料 (L5 lead only, must trigger L1-L4 verification)

**Specific examples that are invalid L5 use**:
- 自媒体观点文章无源 (L5 only, no L1-L4)
- KOL 推荐/踩雷 (L5 only)
- 推特/雪球个人发言

### 1.5 D verified baseline — frozen per session

```
每个 Session 必须保留 ≥1 verified baseline assertion
类比 D (Session 1)
```

**Why**:
- 防止系统退化为"找雷系统"
- 让 Verdict 分布不偏向 `conflicting_evidence`
- 校准 L1-L5 ordering in non-conflict scenarios

**P0a.5a Definition of Consistency** must include this rule.

---

## 2. What This Means for Session 1

### 2.1 Per-Assertion L1-L5 Annotation

| Assertion | Primary Source | Strength | Override 应用? |
|---|---|---|---|
| A 关联客户 | MB-2025-AR-PARTIAL-REPLY + 媒体 | L1 + L5 | L1 wins, L5 = lead (公司 deferred 之后媒体跟进) |
| B 资金流 | MB-2025-AR-PARTIAL-REPLY problem 1 | L1 | N/A |
| C 扩产减值 | MB-2023-AR-REPLY + MB-2025-AR-PARTIAL-REPLY | L1 + L1 | N/A (regulator × 2) |
| D 2023 baseline | MB-2023-AR-REPLY | L1 (载体) + L2 (数据) | L1 (regulator ref) 主导, L2 数据可信 |

### 2.2 Session 1 Verdict Derivation

For each assertion, Verifier (LLM agent) applies:
1. L1-L5 ordinal to compare conflicting sources
2. If issue type = 财务真实性, apply L3 > L2 override
3. If L5 is the only counter-evidence, treat as L5-contradiction-clue, not standalone conflict
4. If multiple L1s disagree, escalate to manual review (out of Session 1 scope)

### 2.3 Session 1 现场决策点更新

- B 的 Verdict (`tolerance_unresolved` vs `conflicting_evidence`): 取决于是否 L1 已经包含 sufficient evidence
- 任何 L5-only contradiction: 必须标 `L5-contradiction-clue` in Column 8 Notes, 不能 standalone
- 任何 L3 vs L2 冲突: 先问 "is this 财务真实性 issue?" 再决定 override

---

## 3. What This Means for L0 v0.1 (post-Session-1)

L0 v0.1 backlog task #11 item 4 must include:
- L1-L5 ordinal enumeration (default + override)
- L5 use scope (lead / catalyst / contradiction clue, NOT verified basis)
- L3 conditional override rule
- L5-contradiction-clue 标注意义 (Column 8 Notes)
- D-pattern requirement (≥1 verified baseline per session)

---

## 4. What This Means for P0a.5a (Definition of Consistency)

P0a.5a must include:
- D-pattern rule (≥1 verified baseline per session)
- Evidence Strength 作为 Verifier 输入 (verdict derivation 必须显式用 L1-L5)
- IssueType classification 决定是否 apply L3 override

---

## 5. What This Means for P0d (Verdict Contract)

P0d must include:
- Verdict derivation algorithm: L1-L5 ordinal comparison + L3 override + L5-contradiction-clue handling
- IssueType enum (for L3 override trigger)
- Aggregation rules (currently deferred, but P0d will define the framework)

---

## 6. What C / 我 不该再重新讨论

```
❌ L1-L5 是否需要 (已冻结: 必须有)
❌ 是否 numerical (已冻结: ordinal)
❌ L5 是否完全排除 (已冻结: 不完全排除, 限定 lead/catalyst/contradiction clue)
❌ D 是否需要 (已冻结: 必保留)
```

## 7. What 还可以讨论 (Session 1+ / P0a.5a 阶段)

```
- IssueType 详细枚举 (什么算 财务真实性)
- L5-contradiction-clue 的具体标注格式 (Column 8 Notes 怎么写)
- L4 内部 sub-tier 是否需要 (大行 vs 中小行)
- L1-L5 之间的相对强度是否需要 numerical fallback (e.g., 案例足够多后)
```

---

## 8. Changelog

- 2026-06-08: v0 design freeze。基于 C 反馈 + G lock-in。5 条决策全部冻结 (ordinal / L3 override / L5 scope / D pattern / aggregation deferral)。Session 1 现场按此执行, 不再重新讨论。
