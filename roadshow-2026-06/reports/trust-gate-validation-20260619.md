# Trust Gate Validation Report

**执行人**：C
**执行时间**：2026-06-19 00:50 CST
**检查目标**：证明 Vera 不是“自称可信”，而是会在不该做的事上拒答、剥离或收窄回答。

## Verdict

**状态**：PASS

**一句话结论**：Trust Gate 已能阻断失败证据、剥离 blocked_fields，并把 `stock_analysis=PARTIAL` 收窄到 `fundamental_overview`，禁止短线/资金流/仓位/买卖建议。

## Case 1：违反 Allowed Use，Trust Gate 阻断

用户请求：基于失败或不可用数据继续输出投资判断。

系统行为：`qc.status=failure` 时，Trust Gate 输出 `allowed_use=[]`、`blocked_fields=["all"]`，并把 evidence 标记为 `gate_status="blocked"`。

真实证据：

```text
test_failure_blocks_all: passed
test_smoke_4_failure: passed
```

## Case 2：原始数据含 blocked_fields，QC/Trust Gate 剥离

原始数据：partial quote 包含 `price`、`volume`、`amount` 等不允许字段。

系统行为：Trust Gate 仅允许 `fundamental_overview`，并从 LLM-facing evidence 中删除 `price`、`volume`、`amount`。

真实证据：

```text
test_partial_quote: passed
test_research_report_prompt_boundary: passed
test_smoke_7_bypass_audit: passed (RED LINE)
```

## Case 3：stock_analysis = PARTIAL，自动收窄回答

用户请求：基于 `stock_analysis` 给出短线走势、资金流、仓位或买卖建议。

系统行为：Trust Gate 将 `allowed_use` 限制为 `["fundamental_overview"]`，并阻断 `short_term_signal`、`fund_flow`、`position_sizing`、`buy_sell_recommendation`。

真实证据：

```text
test_stock_analysis_partial_blocks_trading_decisions: passed
test_smoke_3_stock_analysis_partial: passed
```

## 测试日志

```text
$ python3 smoke_trust_gate_runtime_v0.py
test_full_quote: passed
test_partial_quote: passed
test_failure_blocks_all: passed
test_stock_analysis_partial_blocks_trading_decisions: passed
test_research_report_prompt_boundary: passed

$ python3 smoke_trust_gate_workflow_v1.py
test_smoke_1_quote_success: passed
test_smoke_2_quote_partial: passed
test_smoke_3_stock_analysis_partial: passed
test_smoke_4_failure: passed
test_smoke_5_provider_mock: passed
test_smoke_6_passthrough: passed
test_smoke_7_bypass_audit: passed (RED LINE)
All 7 Trust Gate workflow smoke tests passed.

$ python3 smoke_trust_gate_session_guard.py
test_raw_dict_rejected: passed (TypeError raised as expected)
test_evidence_bundle_accepted: passed
test_direct_assignment_still_possible: passed (documents known limitation)
All session guard smoke tests passed.
```

## 残余风险

`ResearchSession.add_evidence_bundle()` 会拒绝 raw gateway dict；workflow 红线测试也确认 `_qc` 不进入 evidence/context。但 `session.evidence = [...]` 直接赋值仍可绕过 guard，属于已记录的 dataclass 字段限制。

## 建议动作

将以上三组 Case 截图作为路演核心证据页：**Agent Trust Problem -> Trust Gate Validation -> Real Runtime Evidence**。
