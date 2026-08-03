# C-01 Claim Strength — Candidate Registry

**Status:** INCIDENT DISCOVERY (not yet a governance case)
**Date:** 2026-08-03
**Method:** Prompt audit + session evidence

## Candidate 1: Stock Analyst Prescriptive Output Pipeline 🔴 STRONGEST

**Source:** `Linmeimei-Agent/skills/finance-suite/prompts/stock-analyst.md`
**Scope:** All stock analysis generated for Finance Suite users

### Claim Escalation Path

```
Evidence (Level 1-2):
  财务指标 (PE/PB/ROE), 资金流向, 行情数据
         ↓  ←── prompt explicitly generates escalation
Interpretation (Level 3-4):
  隐含回报率估算, 凯利公式仓位计算, 情景概率
         ↓
Prediction (Level 5):
  股价区间推演, 概率加权情景
         ↓
Prescription (Level 6):
  短期动作: [买入/持有/观望/减仓]
  中长期动作: [买入/持有/观望/减仓]
  建议策略: [纯多头/多头+期权保护/配对交易]
  建议实际仓位: [XX]%
```

### System Inconsistency

Same codebase, same skill directory:

| Prompt | Prescriptive Output |
|---|---|
| `stock-analyst.md` | ✅ Generates: 仓位建议, 买卖方向, 策略选择 |
| `deep-research.md` | ❌ Blocks: "不对单一公司做投资建议", "无买入/卖出/持有评级" |

Two prompts in the same skill produce opposite claim strength governance. This is not a hallucination — it's a design-level boundary that was never harmonized.

### Governance Gap

The `stock-analyst.md` disclaimer says:

> "不构成投资建议。投资有风险，决策需谨慎。"

But this is a **legal overlay, not a governance control.** The output IS a trade recommendation regardless of the disclaimer appended. Claim strength escalation already occurred in the body of the output before the disclaimer appears.

### Cross-Reference Evidence

Session `1f81e655` (2026-06-25) contains explicit user constraint:

> "不能说'建议买入/2成仓/目标价'"

This proves the user has already observed and attempted to block prescriptive output — but the fix was a prompt instruction, not a governance rule. Prompt instructions are bypassable, not enforceable.

### Incident Qualification

Per §10.2 criteria:

| Criterion | Status |
|---|---|
| Real production behavior | ✅ — prompt has generated prescriptive output since at least 2026-06 |
| Fact → interpretation → recommendation | ✅ — PE/PB evidence → 凯利仓位 → 买入/持有/卖出 |
| Defined allowed vs blocked | ✅ — deep-research prompt already defines the boundary |
| Acceptance test feasible | ✅ — "does this stock analysis contain 买入/卖出/仓位/策略建议?" |

## Candidate 2: Morning Brief Investment Signal Escalation

**Source:** `prompts/morning-brief.md` + D13 automation pipeline
**Scope:** Daily morning brief generation

### Claim Escalation Path

```
Evidence:
  集合竞价数据 (涨跌幅, 封单量)
  黄金坑扫描结果 (signal → composite_score)
         ↓
Interpretation:
  "市场情绪偏多", "资金活跃度高"
         ↓
Prediction:
  "今日有望..."
         ↓
Prescription:
  "可关注XX板块", "建议回避YY"
```

### Status

Weaker than Candidate 1. Morning brief templates explicitly block `建议` (advice) language per D13 template rules. But edge cases may exist in automated generation.

## Candidate 3: Sector/Industry Report → Stock Selection

**Source:** `prompts/industry-report.md`, `prompts/deep-research.md`
**Scope:** Industry analysis → implicit stock preference

### Claim Path

```
Evidence:
  行业景气度指标, 政策方向
         ↓
Interpretation:
  "XX子行业受益于政策"
         ↓
Prescription (implicit):
  "龙头公司包括: A, B, C" ← presented as factual list,
  but reader interprets as buy candidates
```

### Status

Weakest. Claim boundary here is implicit — the output is technically factual but the presentation structure creates recommendation framing. Harder to define a clean acceptance test.

## Recommendation

**Promote Candidate 1 to C-01.** The evidence is strongest, the claim escalation path is explicit in the prompt code, the system inconsistency (stock-analyst vs deep-research) provides a clear governance boundary, and acceptance testing is mechanically verifiable.

**Next step:** Incident write-up, then §10.2 template.
