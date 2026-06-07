# Market Temperature GitHub Benchmark

日期：2026-06-07

## 1. 结论

Finance Suite 的“市场温度计”不应该做成单一情绪分数，也不应该做成交易信号。

更合适的形态是：

```text
市场温度
↓
结构解释
↓
三类驱动因子
↓
数据可信度 / 不足提示
```

推荐方向：

```text
温度分数 = 市场活跃度 + 市场广度 + 风险偏好 + 主线集中度
```

不推荐方向：

```text
温度分数 = AI 情绪打分
```

原因：GitHub 上常见的 sentiment dashboard 很容易把新闻/社媒/LLM 情绪直接变成“市场判断”，这和 Finance Suite 最近 Trust Gate 的方向相冲突。市场温度计应先走结构化硬指标，再用情绪/新闻做旁证。

## 2. 对标样本

| 项目 | 类型 | 可借鉴点 | 不建议照搬 |
|---|---|---|---|
| [xang1234/stock-screener](https://github.com/xang1234/stock-screener) | 多市场 stock screener + breadth dashboard | StockBee-style breadth、上涨/下跌家数、强势股数量、多周期趋势 | 功能太重，不适合 Sidebar；需要拆成 Market Context 的轻量摘要 |
| [DidierRLopes/fear-greed-index](https://github.com/DidierRLopes/fear-greed-index) | CNN Fear & Greed wrapper | 多因子情绪模型：VIX、put/call、momentum、breadth、safe haven demand | 直接抓 CNN 不适合 A 股；“fear/greed”语言容易被理解成交易建议 |
| [OnePunchMonk/AgentQuant](https://github.com/OnePunchMonk/AgentQuant) | regime detection / quant agent | 用 VIX trailing percentile + momentum 做 regime，而非硬编码阈值 | 偏美股/策略研究，不能直接用于 A 股短线温度 |
| [awsdataarchitect/financial-signals-dashboard](https://github.com/awsdataarchitect/financial-signals-dashboard) | Streamlit AI signals dashboard | gauge、trend、sentiment tab 的可视化组织 | 有 BUY/SELL/HOLD、position size，Finance Suite 不能照搬 |
| [shirosaidev/stocksight](https://github.com/shirosaidev/stocksight) | Twitter/news sentiment + Kibana | 情绪数据可作为独立 panel；适合“观点/舆情”层 | 社媒情绪不能进入硬数据温度主分 |
| [dbogdanm/MarketSentiment](https://github.com/topics/us-stocks-api) | news + AI sentiment + Fear & Greed + VIX | 将 VIX 与 Fear & Greed 放在同一 market sentiment 页面 | 低 star、小项目，只能作为形态参考 |
| [IndexFusion](https://indexfusion.org/) | 投资 dashboard 产品 | “market posture / volatility / rates / sentiment / headlines” 的一屏组织 | 非 GitHub 项目；只参考信息架构，不作为实现对标 |

## 3. 关键观察

### 3.1 Breadth 比单一情绪分数更适合 Finance Suite

`xang1234/stock-screener` 的 README 明确突出 “real-time market breadth analysis”，并展示 StockBee-style advance/decline、daily movers、多周期趋势。这类指标更接近 Finance Suite 当前已有的：

- 涨停数量
- 开板比例
- 昨停今表现
- 连板占比
- 最高连板
- 主线集中度
- 板块扩散

建议：市场温度计第一版优先吃这些结构化指标，而不是新闻 sentiment。

### 3.2 Fear & Greed 的价值在“多维拆解”，不是名字

`DidierRLopes/fear-greed-index` 展示了 CNN Fear & Greed 的典型维度：junk bond demand、market volatility、put/call options、market momentum、stock price strength、stock price breadth、safe haven demand。

可借鉴的是多维拆解：

```text
风险偏好
波动压力
市场动量
市场广度
避险需求
```

不建议直接叫 “Fear & Greed”。A 股语境里更稳的名字是：

```text
市场温度
风险偏好
市场结构热度
```

### 3.3 Regime 应使用相对阈值

`OnePunchMonk/AgentQuant` 对 VIX regime 的说明值得借鉴：它不使用固定的 VIX > 20 / > 30，而使用过去 252 个交易日的分位数，并结合 3 个月 momentum。

这对 Finance Suite 的启发：

```text
不要把 80 个涨停、40 个涨停永远写死成强/弱
应逐步迁移到滚动分位数
```

第一版可以保留当前硬阈值，但 contract 要预留：

```json
{
  "score_method": "static_threshold_v0",
  "future_method": "rolling_percentile_v1"
}
```

### 3.4 AI sentiment dashboard 容易越界

`awsdataarchitect/financial-signals-dashboard` 的可视化很完整，有 sentiment score gauge、7-day trend、social radar、news sentiment bars；但同一项目也包含 BUY/SELL/HOLD、confidence、risk-reward、position size。

Finance Suite 不能照搬这条路线。市场温度计只能解释市场结构，不输出：

- 买入/卖出
- 仓位建议
- 短线判断
- 上涨概率
- target price

### 3.5 社媒/新闻情绪适合做旁证，不适合做主温度

`stocksight` 这类项目把 Twitter/news headline 存入 Elasticsearch/Kibana，再做 sentiment 分析。这类链路适合 Finance Suite 的 Market Intel 或 Research Runtime 观点层，但不应主导 Market Temperature。

建议口径：

```text
硬数据温度：涨跌、涨停、开板、连板、扩散、成交
观点旁证：新闻、社媒、研报、搜索热度
AI 脱水：只负责解释，不负责造分
```

## 4. 推荐 Finance Suite v0 结构

### 4.1 页面输出

保持现有 Market Context 边界：

```text
一句话市场结构
+
三个关键因子
+
一个详情入口
```

市场温度计只提供一个 compact block：

```json
{
  "temperature": {
    "score": 62,
    "label": "偏热",
    "trend": "rising",
    "as_of": "2026-06-07 10:30:00",
    "_qc": {
      "status": "partial",
      "reason": "missing_macro_or_volume_fields",
      "freshness": "intraday",
      "provider": "market_context",
      "missing_fields": []
    }
  }
}
```

### 4.2 分数组成

第一版建议 4 维，不超过 100 分：

| 维度 | 权重 | 数据候选 | 说明 |
|---|---:|---|---|
| 活跃度 | 30 | 涨停数、强势股数、成交额变化 | 市场是否有热度 |
| 广度 | 25 | 上涨家数占比、板块扩散、昨日涨停正反馈 | 热度是否扩散 |
| 风险偏好 | 25 | 开板比例、连板高度、昨日涨停承接 | 风险资金是否愿意接力 |
| 主线集中度 | 20 | top sector share、主题集中度 | 热度是否集中在少数主线 |

### 4.3 标签

建议五档：

```text
0-20   冷
21-40  偏冷
41-60  中性
61-80  偏热
81-100 过热
```

注意：`过热` 也不是卖出建议，只是结构状态描述。

### 4.4 因子解释

每次输出最多三个因子：

```json
{
  "drivers": [
    {
      "name": "涨停数量",
      "value": 86,
      "direction": "positive",
      "explain": "活跃样本较多"
    },
    {
      "name": "开板比例",
      "value": "28%",
      "direction": "negative",
      "explain": "分歧有所抬升"
    },
    {
      "name": "主线集中度",
      "value": "高",
      "direction": "mixed",
      "explain": "热度集中在少数方向"
    }
  ]
}
```

不要输出“买/卖/持有/加仓/减仓”。

## 5. 数据与 Trust Gate 约束

市场温度计必须走现有 Contract First 方向。

```text
Provider
↓
Gateway / Market Context Fetcher
↓
QC
↓
Trust Gate
↓
Market Temperature
```

如果 `_qc.status=partial`：

- 允许输出温度区间或局部维度
- 必须显示 `missing_fields`
- 不允许输出确定性结论
- 不允许进入交易建议

如果 `_qc.status=failure`：

- 温度显示 “数据不足，暂不下结论”
- score 应为 `null`
- drivers 应为空或只显示失败原因

### 5.1 allowed_use

市场温度 Evidence 的建议 `allowed_use`：

```json
{
  "allowed_use": [
    "market_structure_overview",
    "risk_preference_context",
    "theme_concentration_context"
  ]
}
```

禁止：

```json
{
  "blocked_fields": [
    "buy_sell_recommendation",
    "position_sizing",
    "short_term_signal",
    "target_price"
  ]
}
```

## 6. 不建议照搬的设计

1. 不做 `BUY/SELL/HOLD` gauge。
2. 不做仓位建议。
3. 不把 LLM sentiment 当主分。
4. 不做复杂多 tab dashboard。
5. 不把温度计做成“市场预测器”。
6. 不让 HTTP 200 或 `ok=true` 绕过 `_qc.status`。

## 7. 建议实施顺序

### Step 1：文档冻结

先冻结：

```text
MarketTemperatureContract
score / label / drivers / _qc / allowed_use / blocked_fields
```

### Step 2：只接现有 Market Context 数据

只使用当前已有：

- `scripts/market_context.py`
- 涨停池
- 强势池
- 昨停今表现
- top sectors

不修 `macro_data`，不接新 provider。

### Step 3：smoke

只做三条：

1. 数据完整：输出 score/label/drivers。
2. 数据 partial：输出 partial + missing_fields，不输出确定性结论。
3. 数据 failure：score=null，显示“数据不足，暂不下结论”。

## 8. 对 Finance Suite 的最终建议

市场温度计 v0 应是 Market Context 的一个指标块，不是新页面大系统。

推荐文案：

```text
市场温度：偏热
主线集中度：高
风险偏好：中高
板块扩散：适中
```

推荐底线：

```text
本模块呈现市场结构温度，不含操作建议。
```

这能和现有产品边界保持一致：

```text
Finance Suite explains the market context before action.
```

## 9. 参考链接

- [xang1234/stock-screener](https://github.com/xang1234/stock-screener)
- [DidierRLopes/fear-greed-index](https://github.com/DidierRLopes/fear-greed-index)
- [OnePunchMonk/AgentQuant](https://github.com/OnePunchMonk/AgentQuant)
- [awsdataarchitect/financial-signals-dashboard](https://github.com/awsdataarchitect/financial-signals-dashboard)
- [shirosaidev/stocksight](https://github.com/shirosaidev/stocksight)
- [GitHub topic: us-stocks-api](https://github.com/topics/us-stocks-api)
- [IndexFusion](https://indexfusion.org/)
