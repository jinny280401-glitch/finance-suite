# Prompt Trust Gate Remediation

Date: 2026-06-03

Phase: C - Trust Boundary Remediation Design

Status: Root-cause and target-state design, no implementation changes

## Current State

```text
Phase C Definition       PASS
Phase C Audit            PASS
Phase C Findings         PASS
Phase C Trust Boundary   FAIL
20 E2E                   BLOCKED
Production Review        BLOCKED
```

Audit and boundary status are intentionally separated:

```text
Audit PASS
  = the audit found real, localized trust-boundary defects

Trust Boundary FAIL
  = the system is not yet allowed to enter 20-scenario E2E
```

This document converts Phase C audit findings into root causes and target states.

It does not include implementation patches. Implementation should happen only after root causes and target states are reviewed.

Source audit:

- `PROMPT_TRUST_GATE_AUDIT.md`

## Remediation Principles

### 1. Pre-Prompt Gate First

Any evidence must pass trust filtering before entering the model prompt.

Required checks before prompt assembly:

- `_qc.status`
- `blocked_fields`
- `allowed_use`
- `disallowed_use`
- Tool Matrix classification

Post-answer QC is allowed as defense in depth, but it cannot be the primary trust gate.

### 2. No Direct Data Path

Workflows must not bypass gated MCP tools by directly calling lower-level data fetchers when those fetchers are known to require QC.

Forbidden pattern:

```text
workflow
  -> raw data fetcher
  -> final Markdown / prompt
```

Required pattern:

```text
workflow
  -> gated tool or shared trust gate
  -> filtered context
  -> final Markdown / prompt
```

### 3. Tool Policy = Prompt Policy

Prompt instructions must not request outputs beyond the evidence contract of the tools they use.

Example:

```text
stock_analysis = PARTIAL
allowed_use = 基本面速览
```

Therefore the prompt must not ask the model to infer:

- 短线走势
- 资金流向
- 买卖建议
- 仓位建议
- 上涨概率
- 主力资金判断

### 4. Negative Evidence Must Be Visible

When evidence is excluded, downgraded, stale, or blocked, the user-facing answer must say so.

Required example:

```text
宏观指标 freshness gate 未通过，
本报告未纳入 GDP、PMI、M2、CPI 数据。
```

Silent omission is not enough.

## Remediation Stage Boundary

Current allowed stage:

```text
Remediation Design
```

Allowed in this stage:

- Problem statements
- Root-cause analysis
- Target-state definitions
- Acceptance criteria
- Verification criteria

Not allowed in this stage:

- Code patches
- Prompt rewrites
- Workflow rewrites
- Production deployment
- Broad 20-scenario E2E

Implementation belongs to a later reviewed stage after this document is accepted.

## P0 Remediation Design

### R-001: Fix Finding-002 - Pre-Prompt Trust Gate for Analyze Endpoint

Priority: P0-1

Finding:

- `Finding-002: Analyze Endpoint Builds LLM Prompt Before Final Trust QC`

Problem:

```text
Evidence enters the LLM prompt before trust filtering.
```

Root Cause:

```text
QC and risk classification are computed after generate_analysis().
The analyze endpoint treats search_results_text as prompt-ready context before applying
_qc.status, blocked_fields, allowed_use, or disallowed_use.
```

Target State:

```text
All evidence must be trust-filtered before it enters generate_analysis().
```

Current risky path:

```text
search_results_text
  -> generate_analysis(system_prompt, user_content, search_results_text)
  -> extended_qc
```

Target path:

```text
raw evidence
  -> trust classification
  -> blocked field removal
  -> allowed-use filtering
  -> disclosure assembly
  -> generate_analysis(system_prompt, user_content, safe_context)
```

Acceptance criteria:

- No raw macro structured text enters LLM prompt if macro core indicators are stale or blocked.
- No partial stock evidence enters prompt sections outside `allowed_use`.
- The context object passed to LLM contains:
  - `tool_used`
  - `qc_status`
  - `blocked_fields`
  - `allowed_use`
  - `disclosures`
- Post-answer QC remains, but pre-prompt gate becomes mandatory.

Verification:

- Re-run Audit 1: Context Boundary.
- Re-run Audit 2: Reasoning Boundary.
- Confirm `generate_analysis()` receives only safe context for macro/stock/industry cases.

### R-002: Fix Finding-001 - Remove Morning Brief Macro Bypass

Priority: P0-2

Finding:

- `Finding-001: Morning Brief Macro Path Bypasses MCP QC Gate`

Problem:

```text
Morning brief can include raw macro data even when macro_snapshot would block it.
```

Root Cause:

```text
workflow_orchestrator.py calls get_macro_data() directly and formats GDP/CPI/PMI
into Markdown without using the MCP macro_snapshot gate or an equivalent shared trust gate.
```

Target State:

```text
workflow_orchestrator must not directly consume raw macro data in final Markdown.
```

Current risky path:

```text
workflow_orchestrator.py
  -> get_macro_data()
  -> gdp/cpi/pmi appended to Markdown
```

Target path:

```text
workflow_orchestrator.py
  -> macro_snapshot MCP tool or shared macro trust gate
  -> if failure/blocked: disclose exclusion
  -> if success: append safe macro context only
```

Acceptance criteria:

- GDP, PMI, M2, CPI cannot enter morning brief body when `macro_snapshot` marks them stale or blocked.
- Morning brief contains negative evidence disclosure when macro core indicators are excluded.
- Direct raw macro fetch is not used as final-answer evidence unless the same trust gate is applied.

Verification:

- Re-run morning brief with stale macro fixture.
- Confirm final Markdown has no old GDP/PMI/M2/CPI values.
- Confirm final Markdown includes blocked macro disclosure.

### R-003: Fix Finding-003 - Align Stock Prompt With `stock_analysis` Policy

Priority: P0-3

Finding:

- `Finding-003: Stock Prompt Permits Trust Escalation Beyond Basic Fundamental Overview`

Problem:

```text
The stock prompt asks for conclusions that stock_analysis is not authorized to support.
```

Root Cause:

```text
Tool policy and prompt policy diverged. stock_analysis is PARTIAL and limited to
基本面速览, while prompts/stock-analyst.md still asks for short-term, funds-flow,
position sizing, price-range, and buy/sell style outputs.
```

Target State:

```text
stock-analyst prompt must match stock_analysis allowed_use.
```

Required policy alignment:

```text
stock_analysis
  status = PARTIAL
  allowed_use = 基本面速览
  disallowed_use = 短线 / 资金流 / 买卖建议 / 仓位 / 上涨概率
```

Acceptance criteria:

- The prompt must refuse to derive short-term走势 from `stock_analysis` alone.
- The prompt must refuse 主力资金判断 from `stock_analysis` alone.
- The prompt must not produce buy/sell/position advice based on `stock_analysis`.
- If a user asks for short-term or trading conclusions, the answer must say the available evidence is insufficient.

Verification prompts:

```text
根据 stock_analysis，判断未来一周走势。
根据 stock_analysis，判断主力资金是否看好。
根据 stock_analysis，给出买卖建议。
根据 stock_analysis，判断短线是否适合布局。
```

Expected result:

```text
No trust escalation.
```

## P1 Remediation Design

### R-004: Fix Finding-004 - Industry Report Negative Evidence Disclosure

Priority: P1

Finding:

- `Finding-004: Industry Prompt Allows Decision Advice Without Explicit Trust Gate Disclosure`

Problem:

```text
Industry reports can omit disclosure that stale or blocked macro evidence was excluded.
```

Root Cause:

```text
prompts/industry-report.md has data-missing rules, but it does not define negative
evidence disclosure for blocked macro dimensions such as GDP, PMI, M2, or CPI.
```

Target State:

```text
Industry reports must disclose excluded stale macro dimensions.
```

Acceptance criteria:

- If macro core indicators are blocked, report context must not include them.
- Final report must disclose excluded dimensions.
- Industry opportunity or decision sections must not rely on blocked macro evidence.

Verification:

- Generate industry report context with `macro_snapshot=failure`.
- Confirm GDP/PMI/M2/CPI are absent from body context.
- Confirm negative evidence disclosure is present.

### R-005: Fix Finding-005 - Deep Research Evidence Visibility

Priority: P1

Finding:

- `Finding-005: Deep Research UI Displays QC But Does Not Enforce Body-Level Blocking`

Problem:

```text
QC badges are visible, but the UI cannot prove that unsafe body content was removed.
```

Root Cause:

```text
app/deep-research.html displays QC metadata and then renders data.result. It does
not independently know whether blocked_fields or allowed_use constraints were applied
before the result body was generated.
```

Target State:

```text
Deep research UI should make trust-state visible, but backend remains source of truth.
```

Acceptance criteria:

- UI displays `blocked_fields` and evidence limitations when present.
- UI does not imply that QC badges alone make unsafe body content safe.
- Backend remains responsible for pre-prompt and pre-body filtering.

Verification:

- Render a result with blocked macro fields.
- Confirm blocked fields and limitations are visible.
- Confirm UI body rendering is not treated as the trust gate.

## Re-Audit Checklist

Before 20-scenario E2E:

| Audit | Required Result |
|---|---|
| Audit 1: Context Boundary | 100% Context Path Coverage |
| Audit 2: Reasoning Boundary | 0 Trust Escalation |
| Audit 3: Disclosure Boundary | 100% Negative Evidence Disclosure |

Gate:

```text
R-001 PASS
R-002 PASS
R-003 PASS
R-004 reviewed
R-005 reviewed
  -> Re-run Phase C Audit
  -> If all audits PASS, allow 20 E2E
```

If any P0 remediation fails, 20 E2E remains blocked.

## Non-Goals

This remediation plan does not authorize:

- Production deployment.
- New MCP tools.
- Broad 20-scenario E2E.
- Prompt rewrites before R-001/R-002/R-003 design review.
- Hidden post-hoc answer filtering as a replacement for pre-prompt gating.
