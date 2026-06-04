# Trust Gate Contract

日期：2026-06-05

## 1. 一句话目标

LLM 永远不直接消费 Provider Output，只消费 Evidence。

Trust Gate v0 不改 Provider、Gateway、QC。它只负责：

```text
Gateway Response
↓
Trust Gate
↓
Evidence Bundle
↓
LLM
```

## 2. 输入：Gateway Response

Trust Gate 的输入是 Gateway Response，而不是 Provider Output。

最小输入：

```json
{
  "data": {
    "price": 123.4,
    "pe": 20
  },
  "_qc": {
    "status": "partial",
    "reason": "delayed_source",
    "provider": "joinquant",
    "freshness": "delayed",
    "missing_fields": ["price", "volume"]
  }
}
```

`ok=true`、HTTP 200、provider success 都不能单独作为事实入口。

## 3. 输出：Evidence Bundle

Trust Gate 的输出进入 Runtime 语义，不再叫 `_qc`。

最小输出：

```json
{
  "evidence": {
    "pe": 20
  },
  "allowed_use": ["fundamental_overview"],
  "blocked_fields": ["price", "volume"],
  "trust_status": "partial"
}
```

Runtime 和 Prompt 只能读取 `Evidence Bundle`。

## 4. allowed_use

`allowed_use` 是 prompt 的权限白名单。Prompt 不需要理解 provider、freshness、partial，只看 `allowed_use`。

FULL:

```json
{
  "allowed_use": [
    "fundamental_overview",
    "valuation_analysis",
    "peer_comparison"
  ]
}
```

PARTIAL:

```json
{
  "allowed_use": ["fundamental_overview"]
}
```

FAILURE:

```json
{
  "allowed_use": []
}
```

## 5. blocked_fields

`blocked_fields` 是字段级删除规则。Trust Gate 必须直接从 Evidence 删除阻断字段，而不是保留字段再告诉模型不要用。

示例：

```json
{
  "blocked_fields": ["price", "volume", "amount", "fund_flow"]
}
```

如果 Gateway Response 里有：

```json
{
  "price": 123.4
}
```

那么 Evidence Bundle 里不能再出现 `price`。

## 6. Runtime Rule

Research Runtime 只能拿：

```text
evidence_bundle.evidence
```

不能拿：

```text
gateway_response.data
```

接口层面应该只允许：

```python
generate_section_body(evidence_bundle)
```

不允许：

```python
generate_section_body(gateway_response)
```

## 7. stock_analysis=PARTIAL

`stock_analysis=PARTIAL` 只能用于：

```text
fundamental_overview
```

必须禁止：

```text
short_term_signal
fund_flow
position_sizing
buy_sell_recommendation
```

这条规则对应之前 Trust Gate Audit 发现的 P0：不能让部分可信数据被 LLM 扩写成短线、资金流、仓位或买卖建议。
