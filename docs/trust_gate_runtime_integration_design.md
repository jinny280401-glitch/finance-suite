# Trust Gate Runtime Integration Design

日期：2026-06-04

## 1. 结论

Finance Data Gateway v1 已 PASS。下一阶段不是 Provider Expansion，而是 Trust Gate Runtime Integration。

Sprint 2 的目标不是“接 iFinD financials / consensus”，而是验证：

```text
Provider Registry
↓
Route Policy
↓
Trust Contract
```

是否足以承载 `financials` / `consensus`。如果不够，优先修 Contract，不硬接 Provider。

## 2. 必须守住的链路

Research Runtime 不能把 `ok=true`、HTTP 200、provider 返回 `success` 当事实入口。

唯一允许进入 prompt 的，是通过 Trust Gate 过滤后的 Evidence。

```text
Provider
↓
Gateway
↓
QC
↓
Trust Gate
↓
Evidence
↓
LLM
```

禁止倒挂链路：

```text
Provider
↓
Prompt
↓
LLM
↓
QC
```

## 3. Evidence Contract

进入 LLM 前的 Evidence 必须是经过 Trust Gate 过滤后的对象，而不是 provider 原始响应。

最小结构：

```json
{
  "evidence_id": "quote:600519.SH:2026-06-04",
  "symbol": "600519.SH",
  "data_type": "quote",
  "provider": "joinquant",
  "provider_tier": 2,
  "freshness": "delayed",
  "as_of": "2026-03-01",
  "data": {},
  "_qc": {
    "status": "partial",
    "reason": "delayed_source",
    "missing_fields": ["price", "volume", "amount"],
    "blocked_fields": ["short_term_signal", "fund_flow", "position_sizing"],
    "allowed_use": ["fundamental_overview"]
  }
}
```

Evidence 与 provider response 的区别：

| 对象 | 位置 | 是否可进 prompt |
|---|---|---|
| Provider response | Gateway 之前 | 不允许 |
| Gateway response | Gateway/QC 之后 | 不直接允许 |
| Evidence | Trust Gate 之后 | 允许 |

## 4. Trust Gate 输入

Trust Gate 至少读取：

| 字段 | 用途 |
|---|---|
| `_qc.status` | 判断 `success` / `partial` / `failure` |
| `_qc.reason` | 判断 partial/failure 的具体原因 |
| `_qc.missing_fields` | 判断哪些事实不能使用 |
| `_qc.dimension_sources` | 判断每个维度来源 |
| `_qc.freshness` | 判断 realtime/delayed/stale/cached |
| `_qc.provider_tier` | 判断信源等级 |
| `_qc.blocked_fields` | 判断禁止进入 prompt 的字段 |
| `_qc.allowed_use` | 判断 Evidence 允许用于哪些任务 |

当前 Gateway v1 已有 `status/reason/missing_fields/dimension_sources/freshness/provider_tier`。Sprint 2 应补齐 `blocked_fields/allowed_use` 的规范与默认映射，再接 Runtime。

## 5. Trust Gate 输出

Trust Gate 输出两类结果。

允许进入 prompt：

```json
{
  "gate_status": "allowed",
  "allowed_use": ["fundamental_overview"],
  "evidence": {}
}
```

禁止进入 prompt：

```json
{
  "gate_status": "blocked",
  "reason": "qc_failure",
  "blocked_fields": ["all"],
  "evidence": null
}
```

`_qc.status=failure` 默认整体阻断。`_qc.status=partial` 默认只允许白名单用途。

## 6. allowed_use / blocked_fields 初始规则

```yaml
quote:
  success:
    allowed_use:
      - realtime_snapshot
      - fundamental_overview
      - valuation_context
    blocked_fields: []

  partial:
    reason: delayed_source
    allowed_use:
      - fundamental_overview
      - historical_context
    blocked_fields:
      - realtime_snapshot
      - short_term_signal
      - fund_flow
      - position_sizing

  partial_missing_realtime_fields:
    missing_fields:
      - price
      - volume
      - amount
    allowed_use:
      - fundamental_overview
    blocked_fields:
      - realtime_snapshot
      - short_term_signal
      - fund_flow
      - position_sizing

financials:
  partial:
    allowed_use:
      - business_overview
      - historical_financial_context
    blocked_fields:
      - earnings_revision
      - forward_estimate

consensus:
  partial:
    allowed_use:
      - expectation_context
    blocked_fields:
      - rating_summary
      - target_price
```

特别规则：

`stock_analysis=PARTIAL` 时，只能用于基本面速览，不能推导短线、资金流、仓位建议。

## 7. Pre-Prompt Gate 执行位置

Research Runtime 的 prompt 构建前必须有一个明确的 gate。

```text
retrieve_gateway_data()
↓
normalize_qc()
↓
trust_gate.filter()
↓
build_evidence()
↓
build_prompt()
↓
call_llm()
```

禁止在 `build_prompt()` 内部临时判断 `_qc`。Gate 必须是 prompt 之前的独立阶段，并且写入 runtime events。

建议事件：

```text
trust_gate_started
evidence_allowed
evidence_blocked
trust_gate_completed
prompt_context_built
```

验收时必须能看到：多少 Evidence 被允许、多少 Evidence 被阻断、阻断原因是什么。

## 8. Sprint 2 验收口径

不做：

- 不接新 provider。
- 不扩 iFinD。
- 不迁移更多业务工具。
- 不把 provider response 直接塞进 prompt。

只做：

- 写清 Evidence Contract。
- 写清 `allowed_use` / `blocked_fields`。
- 写清 pre-prompt gate 的执行位置。
- 验证 Research Runtime 只消费 Trust Gate 之后的 Evidence。

通过条件：

1. `ok=true` 但 `_qc.status=partial` 的 Gateway response 不会直接进入 prompt。
2. `_qc.status=failure` 的 Gateway response 被整体阻断。
3. `_qc.status=partial` 且 `reason=delayed_source` 的 quote 只允许 `fundamental_overview` / `historical_context`。
4. 缺 `price/volume/amount` 时，不能生成 `realtime_snapshot`、`short_term_signal`、`fund_flow`、`position_sizing`。
5. Runtime events 能展示 Trust Gate 的 allow/block 结果。

## 9. 阶段标签

```text
Finance Data Gateway v1
PASS

Contract First 阶段完成

下一阶段：
Trust Gate Runtime Integration
不是 Provider Expansion
```
