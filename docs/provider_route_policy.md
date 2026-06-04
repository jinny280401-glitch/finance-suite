# Provider Route Policy

日期：2026-06-04

## 1. 目的

Provider Registry 不等于 Route Policy。

Provider Registry 只回答“系统有哪些 provider、各自成本/权限/额度/能力是什么”。Route Policy 回答“某个功能域、某种使用场景下，应该按什么顺序调用哪些 provider”。

这份文档先冻结路由口径，不实现策略引擎，也不扩展 Gateway data_type。

## 2. 基本原则

1. Source Taxonomy 不是 fallback chain。
2. Tier 1 表示商业终端级强源组，不表示所有场景都优先批量调用。
3. iFinD 是 Tier 1 强源，但 `quota_sensitive=true`，默认不进入批量扫描链。
4. Route Policy 必须按功能域和调用模式定义，例如 `realtime`、`delayed`、`batch`、`smoke`。
5. Gateway 输出必须记录实际 `provider_chain`、`attempted_sources`、`provider`、`freshness`、`_qc.reason`。

## 3. Provider Registry 示例

```yaml
providers:
  wind:
    provider_tier: 1
    cost_level: high
    quota_sensitive: false
    allowed_usage:
      - realtime_quote
      - financials
      - consensus

  ifind:
    provider_tier: 1
    cost_level: high
    quota_sensitive: true
    allowed_usage:
      - connect
      - single_symbol_smoke
      - interactive_quote
      - financials
      - consensus
    disallowed_usage:
      - default_batch_scan

  choice:
    provider_tier: 1
    cost_level: high
    quota_sensitive: true
    allowed_usage:
      - financials
      - consensus
    availability: optional

  tushare:
    provider_tier: 2
    cost_level: medium
    quota_sensitive: false

  joinquant:
    provider_tier: 2
    cost_level: medium
    quota_sensitive: false
    caveats:
      - trial_accounts_may_be_delayed

  akshare:
    provider_tier: 3
    cost_level: low
    quota_sensitive: false
```

## 4. Route Policy v1

```yaml
quote:
  realtime:
    - wind
    - ifind
    - akshare

  delayed:
    - tushare
    - joinquant
    - akshare

  batch:
    - tushare
    - joinquant
    - akshare
    - cache

  smoke:
    - wind
    - ifind

financials:
  primary:
    - wind
    - ifind
    - choice
    - tushare

  batch:
    - tushare
    - joinquant

consensus:
  primary:
    - wind
    - ifind
    - choice

factor:
  primary:
    - trading_system
    - joinquant
    - wind

market_pulse:
  batch:
    - akshare
    - eastmoney_public
    - cache

  validation:
    - wind
    - ifind

news:
  primary:
    - tavily
    - brave

research:
  primary:
    - internal_digest
    - tavily
    - brave
    - llm
```

## 5. Trust Gate 读取规则

Trust Gate 后续至少读取：

```json
{
  "_qc": {
    "status": "partial",
    "reason": "delayed_source",
    "provider": "joinquant",
    "provider_tier": 2,
    "freshness": "delayed",
    "dimension_sources": {
      "quote": "joinquant"
    },
    "missing_fields": ["price", "volume", "amount"]
  }
}
```

`status=partial` 时必须有 `reason`。Market Context、Research Runtime、Deep Research 不能只看 `ok=true` 或 HTTP 200。

## 6. 当前代码边界

当前 `finance_data_gateway.py` 仍是 v0 quote-only 包装层。Provider Route Policy v1 先作为设计契约冻结，Sprint 2 再实现 Provider Registry 与策略选择。
