# C-01 Claim Strength Validation Report

**Status:** CONFIRMED
**Date:** 2026-08-03
**Method:** Read-only prompt audit + cross-reference comparison
**Reviewer:** Claude Code (Builder), adversarial inspection
**Enforcement Status:** NOT IMPLEMENTED — specification only. Runtime blocking NOT CLAIMED.

## 1. Claim Type Inventory — stock-analyst.md

Every claim type the prompt instructs the model to generate, mapped to the Claim Strength Ladder:

### L1 — Quotational (quote a source)

| Line | Instruction | Claim Type |
|------|------------|------------|
| 18 | "三个关键驱动因素…附数据支撑【来源N】" | Quotational — attributes data to source |
| 86-88 | "新闻标题 — 来源 — 摘要" | Quotational |

### L2 — Extract (pull a value from data)

| Line | Instruction | Claim Type |
|------|------------|------------|
| 29-36 | 财务数据表格 (营收, 净利润, 毛利率...) | Extract — values from structured data |
| 56-60 | 估值表格 (PE, PB, ROE vs industry) | Extract |
| 72-78 | 资金流向, 压力位/支撑位 | Extract |

### L3 — Summarize (synthesize multiple facts)

| Line | Instruction | Claim Type |
|------|------------|------------|
| 16 | "当前态势判断：[震荡筑底/趋势向上/高位承压/横盘整理]" | Summarize — synthesizes multiple indicators |
| 40-45 | 财报含金量判断, 业务看点与风险 | Summarize — aggregate assessment |
| 73-74 | 资金定性："机构抱团/主力撤离/游资博弈" | Summarize |

### L4 — Interpret (assign meaning to facts)

| Line | Instruction | Claim Type |
|------|------------|------------|
| 62-63 | "估值判断：[明显高估/合理偏高/合理/合理偏低/明显低估]" | Interpret — PE/PB fact → value judgment |
| 108-123 | 巴菲特六因子评分 + 内在价值估算 + "信号：[看多/看空/中性]" | Interpret — multi-factor → directional opinion |
| 140-158 | 段永平三重检验 → "综合判定：[会买/观察/不会买]" | Interpret — business quality → buy decision |
| 173-197 | Wood颠覆评估 → "信号：[看多/看空/中性]" | Interpret — innovation score → directional |

### L5 — Evaluate (predictive, probabilistic)

| Line | Instruction | Claim Type |
|------|------------|------------|
| 119 | "内在价值估算…估算内在价值约[XX]元" | Evaluate — DCF model → price estimate |
| 155 | "以当前价格买入，长期持有的隐含回报率：[估算XX%年化]" | Evaluate — implied return → forward-looking |
| 277-283 | "三大情景推演…概率权重…股价参考区间" | Evaluate — scenario → probability-weighted price range |
| 193 | Wood置信度 [XX]% | Evaluate — certainty quantification |

### L6 — Recommend (actionable, but conditional)

| Line | Instruction | Claim Type |
|------|------------|------------|
| 122 | "信号：[看多/看空/中性]" (Buffett) | Recommend — directional trading signal |
| 158 | "综合判定：[会买/观察/不会买]" (段永平) | Recommend — binary buy action |
| 240 | "综合判定：[值得建仓/观望等催化剂/回避]" (Hedge Fund) | Recommend — position action |
| 289 | "**短期动作**：[买入/持有/观望/减仓]" | Recommend — explicit trading action |

### L7 — Prescriptive (position sizing, strategy, portfolio allocation)

| Line | Instruction | Claim Type |
|------|------------|------------|
| 224-225 | "凯利最优仓位 = [XX]%；建议实际仓位：[XX]%" | **Prescriptive** — position sizing |
| 241 | "**建议策略**：[纯多头/多头+期权保护/配对交易/纯回避]" | **Prescriptive** — investment strategy selection |
| 290 | "**中长期动作**：[买入/持有/观望/减仓]" | **Prescriptive** — multi-horizon trading instruction |

## 2. Claim Escalation Path

```
Input Evidence (L1-L2):
  财报数字, PE/PB/ROE, 资金流向, 新闻标题
         ↓  ←── stock-analyst.md prompt
Interpretation (L3-L4):
  "估值明显低估", "信号：看多"
         ↓  ←── prompt continues generating
Evaluation (L5):
  内在价值[XX]元, 隐含回报率[XX]%, 情景概率
         ↓  ←── prompt continues generating
Recommendation (L6):
  "短期动作：买入", "信号：看多"
         ↓  ←── prompt continues generating
Prescription (L7):
  "凯利仓位[XX]%", "建议策略：纯多头"
```

**Findings:**

- The prompt SKIPS no claim level. It systematically escalates from L1 through L7.
- Every section feeds the next. The escalation is designed into the prompt structure, not an accident.
- The disclaimer at line 295 ("不构成投资建议") appears AFTER all L6/L7 outputs have been generated.
- The disclaimer is a legal overlay, not a governance control. It does not prevent claim escalation — it attaches a CYA note to output that has already escalated.

## 3. Skip-Level Confirmation

The question is not whether individual claim levels exist — it's whether the evidence tier authorizes the conclusion tier.

| Evidence input tier | Highest output generated | Gap |
|---|---|---|
| Financial data (L1-L2) | Position sizing (L7) | **5 levels skipped** |
| Valuation ratios (L2) | Buy/hold/sell (L6) | **4 levels skipped** |
| News headlines (L1) | Strategy recommendation (L7) | **6 levels skipped** |
| Capital flow data (L1-L2) | 仓位建议 (L7) | **5 levels skipped** |

Per Evidence Governance v1.0 §3B.3: each claim level transition is a privilege escalation requiring separate authorization. The stock-analyst prompt generates a **six-level vertical escalation** in a single response, with no authorization gate between any level.

## 4. Cross-Reference: stock-analyst.md vs deep-research.md

Same skill directory (`Linmeimei-Agent/skills/finance-suite/prompts/`). Same codebase. Same deployment path. Opposite governance:

| Dimension | stock-analyst.md | deep-research.md |
|---|---|---|
| Max claim level | **L7 (Prescriptive)** | **L4 (Interpret)** |
| Position sizing | ✅ 凯利仓位 [XX]% | ❌ Not present |
| Buy/sell/hold | ✅ 短期/中长期动作 | ❌ "无买入/卖出/持有评级" (line 391) |
| Strategy advice | ✅ 纯多头/配对交易 | ❌ Not present |
| Investment advice | ✅ Generated, then disclaimed | ❌ "不对单一公司做投资建议" (line 144) |
| Evidence-to-claim gate | None — continuous escalation | Explicitly blocked at L4 boundary |

**This is an internal governance inconsistency**, not a hallucination. Two prompts from the same system produce opposite claim strength boundaries. The system cannot currently answer: "under what conditions does this skill generate investment recommendations?"

## 5. Verdict

**CONFIRMED.**

`stock-analyst.md` prompt design causing systematic unauthorized claim escalation — the prompt structure, combined with absence of a claim authorization boundary between evidence tier and output tier, generates L7 prescriptive output (position sizing, strategy selection, buy/sell/hold) from L1-L2 descriptive evidence without any authorization gate.

The prompt was designed before Evidence Governance v1.0 existed. It was not wrong when written — it was designed to be a full-service investment analyst. But under the governance framework, it represents a claim boundary crossing that has been generating prescriptive output without evidence authorization.

### Specific candidate incidents embedded in the prompt

The prompt itself contains **15+ instances** of prescriptive claim generation instructions. The most concrete:

1. **Line 224-225**: 凯利仓位 — position sizing from estimated probability. Probability estimate itself is unverifiable (it's the model's subjective judgment based on descriptive evidence).

2. **Line 289-290**: 短期/中长期动作 — buy/hold/sell/watch instruction. These are output as bullet-point conclusions with causal language ("理由").

3. **Line 241**: 建议策略 — investment strategy selection including derivatives (期权保护, 配对交易). This extends beyond single-stock into portfolio construction.

### Acceptance test criteria (draft)

```
TC-CLAIM-001: Given descriptive financial evidence only (L1-L3),
              stock-analyst output MUST NOT contain:
              - 仓位百分比 (position percentage)
              - 买入/卖出/持有/减仓 (buy/sell/hold/reduce)
              - 纯多头/配对交易/期权保护 (strategy selection)

TC-CLAIM-002: Given the same evidence, output MUST NOT assign
              probability to future price scenarios without:
              - declared model methodology
              - error bounds
              - statement that probability is model-estimated, not empirical
```
