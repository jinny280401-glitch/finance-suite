# Finance Data Gateway v1 Contract

日期：2026-06-04

## 1. 核心原则

Finance Data Gateway v1 先冻结契约，不急着扩数据类型。

12 级信源不是一条 fallback 链，而是 Source Taxonomy。真实执行顺序必须由功能域的 Route Policy 决定，再进入 QC 与 Trust Gate。

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

禁止让 Provider 直接把原始数据送进 LLM，再由 LLM 输出后补 QC。这会重新制造“事后 QC”的架构倒挂。

## 2. FinanceDataResponse

统一返回结构：

```json
{
  "ok": true,
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
    "provider": "joinquant",
    "provider_tier": 2,
    "freshness": "delayed",
    "completeness": 0,
    "partial": true,
    "dimension_sources": {
      "quote": "joinquant"
    },
    "missing_fields": ["price", "volume", "amount"],
    "attempted_sources": [],
    "provider_chain": []
  }
}
```

兼容要求：v0 的 `qc` 字段暂时保留，内容与 `_qc` 相同。新消费端优先读取 `_qc`。

## 3. Trust Contract

`_qc` 是 Trust Contract，不只是调试字段。

必备字段：

| 字段 | 含义 |
|---|---|
| `status` | `success` / `partial` / `failure` |
| `reason` | `partial` 或 `failure` 的机器可读原因 |
| `provider` | 最终主 provider |
| `provider_tier` | 信源组层级，不等于执行顺序 |
| `freshness` | `realtime` / `daily` / `delayed` / `cached` / `stale` / `unavailable` |
| `completeness` | 0 到 1 的字段完整度 |
| `partial` | 是否只能作为部分结果展示 |
| `dimension_sources` | 每个维度的实际来源 |
| `missing_fields` | 缺字段列表，不能把 null 当作 success |
| `attempted_sources` | 实际尝试过的 provider |
| `provider_chain` | 本次 route policy 使用的候选链 |

前端、报告、Research Runtime 都应以 `_qc.status` 和 `_qc.dimension_sources` 作为可信度闸门。HTTP 200 不代表数据可信。

`partial` 必须说明原因，不能只给状态。当前保留原因：

| reason | 含义 |
|---|---|
| `delayed_source` | provider 有数据，但不是当前实时口径 |
| `missing_fields` | 核心字段缺失 |
| `unsupported_data_type` | Gateway 尚未支持该数据类型 |
| `missing_symbol` | 请求缺少必需标的 |
| `all_providers_failed` | 本次 route policy 内所有 provider 均失败或为空 |

## 4. Source Taxonomy

| Tier | Provider group | 说明 |
|---|---|---|
| 1 | Wind / iFinD / Choice | 商业终端级强源，可信度同组，差异在授权、API 能力、成本、额度 |
| 2 | Tushare / JoinQuant / JQData | 标准化与策略研究源 |
| 3 | AkShare / 东方财富公开 | 免费公开源与兜底源 |
| 4 | 雪球 / 新浪 / Barchart | 市场讨论、快讯、海外补充 |
| 5 | Tavily / Brave / 公开 Web | 搜索、新闻、政策、网页交叉校验 |
| 6 | LLM / OpenRouter / 规则 fallback | 脱水、表达、结构化，不产生硬事实 |

Tier 是信源地图，不是执行顺序。Wind 挂了不代表默认批量打 iFinD。

## 5. Provider Metadata

Provider Registry 后续应至少包含：

```json
{
  "ifind": {
    "provider_tier": 1,
    "cost_level": "high",
    "quota_sensitive": true,
    "allowed_usage": ["connect", "single_symbol_smoke", "interactive_quote"],
    "disallowed_usage": ["default_batch_scan"]
  }
}
```

iFinD HTTP 是 Tier 1 强源，但 quota-sensitive。批量任务默认应绕开 iFinD，或先走缓存。

## 6. Route Policy 示例

```yaml
quote:
  primary:
    - wind
    - ifind
    - tushare
    - akshare
  batch:
    - tushare
    - joinquant
    - akshare
    - cache

financials:
  primary:
    - wind
    - ifind
    - choice
    - tushare

factor:
  primary:
    - joinquant
    - trading_system
    - wind

news:
  primary:
    - tavily
    - brave

research:
  primary:
    - internal_digest
    - llm
```

每个功能域可以有自己的 `primary`、`batch`、`smoke`、`cache_first` 策略。Gateway 负责选择策略，QC 负责解释结果，Trust Gate 负责决定是否允许进入 Evidence。

## 7. Sprint 顺序

Sprint 1：冻结 Gateway Contract、QC Contract、Trust Gate Contract。

Sprint 2：实现 Provider Registry：`WindProvider`、`IFindProvider`、`ChoiceProvider`、`TushareProvider`、`JoinQuantProvider`、`AkShareProvider`。

Sprint 3：迁移 `stock_analysis`、`wind_query`、`market_pulse`、`macro_snapshot` 到 Gateway。

Sprint 4：Research Runtime 接入 Gateway + Trust Gate，只消费通过 QC 的 Evidence。
