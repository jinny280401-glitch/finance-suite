# Finance Suite MCP Server - 13 个金融工具完整清单

## 📊 数据源架构

```
┌─────────────────────────────────────────────┐
│         Finance Suite MCP Server            │
│         13 个金融工具 + 质检层               │
└──────────────┬──────────────────────────────┘
               ↓
    ┌──────────────────────────┐
    │   三层数据源降级策略      │
    └──────────────────────────┘
               ↓
    Wind API → Tushare Pro → AkShare
    (免费版)   (500元/年)    (免费)
               +
    投行研报库（IMA 订阅）
```

---

## 🛠️ 13 个金融工具详解

### 1. stock_analysis - 个股全维度数据

**功能**：获取个股的完整分析数据

**数据维度**：
- 实时行情（价格、涨跌幅、成交量）
- 财报指标（营收、净利润、ROE、毛利率）
- 资金流向（主力资金、散户资金）
- K线数据（日线、周线、月线）
- 个股新闻（最新资讯）
- 分红记录（历史分红）

**数据源**：AkShare（东方财富）

**使用示例**：
```python
stock_analysis(code="600519")  # 贵州茅台
```

**返回格式**：
```json
{
  "_qc": {
    "status": "success",
    "completeness": 0.95,
    "sources": ["akshare"],
    "missing_dimensions": [],
    "stale_data": []
  },
  "realtime": {...},
  "financials": {...},
  "fund_flow": {...},
  "price_history": [...],
  "news": [...],
  "dividends": [...]
}
```

---

### 2. macro_snapshot - 宏观经济数据

**功能**：获取中国宏观经济指标

**数据维度**：
- GDP（国内生产总值）
- CPI（消费者物价指数）
- PMI（采购经理人指数）
- M2（货币供应量）
- LPR（贷款市场报价利率）

**数据源**：AkShare（国家统计局）

**使用示例**：
```python
macro_snapshot()
```

**返回格式**：
```json
{
  "_qc": {...},
  "gdp": {...},
  "cpi": {...},
  "pmi": {...},
  "m2": {...},
  "lpr": {...}
}
```

---

### 3. market_pulse - 集合竞价与盘面数据

**功能**：获取市场盘面数据和异动信息

**数据维度**：
- 涨停池（今日涨停股票）
- 强势股（连续上涨股票）
- 盘中异动（大单、急涨急跌）
- 人气排行（关注度排名）

**数据源**：AkShare（东方财富）

**使用示例**：
```python
market_pulse()
```

**返回格式**：
```json
{
  "_qc": {...},
  "limit_up": [...],
  "strong_stocks": [...],
  "unusual_activity": [...],
  "popularity": [...]
}
```

---

### 4. search - 多源搜索

**功能**：多维度金融信息搜索

**搜索类型**：
- stock：股票搜索
- macro：宏观经济搜索
- industry：行业搜索
- news：新闻搜索
- url：URL 提取

**数据源**：Tavily + Brave 搜索引擎

**使用示例**：
```python
search(query="贵州茅台 估值", search_type="stock")
```

**返回格式**：
```json
{
  "_qc": {...},
  "results": [
    {
      "title": "...",
      "url": "...",
      "snippet": "...",
      "score": 0.95
    }
  ]
}
```

---

### 5. video_extract - 视频内容提取

**功能**：提取 YouTube/B站 视频字幕

**支持平台**：
- YouTube（通过 Supadata API）
- B站（通过官方 API）

**数据源**：Supadata API + B站 API

**使用示例**：
```python
video_extract(url="https://www.bilibili.com/video/BV1xx411c7mD")
```

**返回格式**：
```json
{
  "_qc": {...},
  "title": "视频标题",
  "author": "作者",
  "duration": 1234,
  "subtitles": "完整字幕文本..."
}
```

---

### 6. watchlist_manage - 自选股管理

**功能**：管理自选股列表和研究记录

**操作类型**：
- add：添加自选股
- remove：移除自选股
- list：查看自选股列表
- update：更新研究记录

**数据源**：本地 JSON 文件

**使用示例**：
```python
watchlist_manage(action="add", code="600519", note="白酒龙头")
```

**返回格式**：
```json
{
  "_qc": {...},
  "watchlist": [
    {
      "code": "600519",
      "name": "贵州茅台",
      "added_at": "2026-05-04",
      "note": "白酒龙头",
      "last_research_timestamp": "2026-05-04T23:00:00"
    }
  ]
}
```

---

### 7. factor_scan - 因子选股信号

**功能**：量化因子选股扫描

**因子类型**：
- 技术因子（均线、MACD、RSI）
- 基本面因子（PE、PB、ROE）
- 资金因子（主力资金、北向资金）

**数据源**：trading-system（外部量化系统）

**使用示例**：
```python
factor_scan()
```

**返回格式**：
```json
{
  "_qc": {...},
  "signals": [
    {
      "code": "600519",
      "name": "贵州茅台",
      "signal": "买入",
      "score": 85,
      "factors": {...}
    }
  ]
}
```

---

### 8. wind_query - 金融数据查询（三层降级）⭐ **核心工具**

**功能**：查询金融数据，支持三层数据源降级

**数据源优先级**：
1. **Wind API**（免费版）→ 基础行情
2. **Tushare Pro**（500元/年）→ 财报、一致预期
3. **AkShare**（免费）→ 补充数据

**查询类型**：
- connect：检查数据源连接状态
- stock：个股快照（价格、市值、PE/PB/ROE）
- financials：完整三大报表（近4期）
- consensus：卖方一致预期（净利润/EPS/ROE）
- peers：同行业可比公司对比
- valuation：历史估值分位（PE/PB 10年百分位）
- shareholders：前十大股东及持股变动
- calendar：财报披露日期

**使用示例**：
```python
# 检查连接状态
wind_query(action="connect")

# 获取个股快照
wind_query(action="stock", code="600519.SH")

# 获取财报数据
wind_query(action="financials", code="600519.SH")

# 获取一致预期
wind_query(action="consensus", code="600519.SH")
```

**返回格式**：
```json
{
  "_qc": {
    "status": "success",
    "completeness": 1.0,
    "sources": ["wind"],  // 或 ["tushare"] 或 ["akshare"]
    "fallback_source": "tushare",  // 降级数据源
    "missing_dimensions": [],
    "stale_data": []
  },
  "source": "wind",  // 实际使用的数据源
  "code": "600519.SH",
  "data": {...}
}
```

**三层降级策略**：
```
尝试 Wind API
  ↓ 失败
尝试 Tushare Pro
  ↓ 失败
尝试 AkShare
  ↓ 失败
返回错误
```

---

### 9. xueqiu_fetch - 雪球数据抓取

**功能**：抓取雪球社区数据

**数据类型**：
- hot：雪球热门动态
- hot-stock：雪球热门股票榜
- stock：个股实时行情
- watchlist：自选股列表（需登录）
- feed：关注动态（需登录）
- search：搜索股票
- earnings-date：财报发布日期

**数据源**：雪球网（通过 autocli）

**使用示例**：
```python
xueqiu_fetch(command="hot-stock", limit=10)
```

**返回格式**：
```json
{
  "_qc": {...},
  "stocks": [
    {
      "symbol": "SH600519",
      "name": "贵州茅台",
      "current": 1384.79,
      "percent": -0.27,
      "followers": 123456
    }
  ]
}
```

---

### 10. zhihu_fetch - 知乎数据抓取

**功能**：抓取知乎热榜和搜索结果

**数据类型**：
- hot：知乎热榜
- search：搜索问题
- question：问题详情

**数据源**：知乎网（通过 autocli）

**使用示例**：
```python
zhihu_fetch(command="search", keyword="贵州茅台")
```

**返回格式**：
```json
{
  "_qc": {...},
  "questions": [
    {
      "title": "如何看待贵州茅台的估值？",
      "url": "https://www.zhihu.com/question/...",
      "answer_count": 123,
      "follower_count": 456
    }
  ]
}
```

---

### 11. sinafinance_fetch - 新浪财经实时快讯

**功能**：获取新浪财经 7x24 实时快讯

**数据类型**：
- 实时财经新闻
- 市场快讯
- 政策解读

**数据源**：新浪财经（通过 autocli）

**使用示例**：
```python
sinafinance_fetch(limit=20)
```

**返回格式**：
```json
{
  "_qc": {...},
  "news": [
    {
      "title": "央行降准 50 个基点",
      "time": "2026-05-04 14:30",
      "content": "...",
      "source": "新浪财经"
    }
  ]
}
```

---

### 12. barchart_fetch - Barchart 期权数据

**功能**：抓取美股期权和行情数据

**数据类型**：
- quote：股票行情（含 PE、EPS、均量）
- options：期权链（含 Greeks、IV、成交量）
- greeks：期权 Greeks 总览
- flow：异常期权流（大单、异常活动）

**数据源**：Barchart（通过 autocli）

**使用示例**：
```python
barchart_fetch(command="options", symbol="AAPL")
```

**返回格式**：
```json
{
  "_qc": {...},
  "options": [
    {
      "strike": 150,
      "type": "call",
      "expiry": "2026-06-20",
      "iv": 0.25,
      "delta": 0.65,
      "volume": 1234
    }
  ]
}
```

---

### 13. research_reports - 投行研报管理 ⭐ **新增工具**

**功能**：管理顶级投行研报链接

**数据来源**：IMA 订阅的投行研报（高盛、摩根大通、桥水等）

**查询类型**：
- list：获取最新研报列表
- by-stock：按股票代码查询相关研报
- by-industry：按行业查询相关研报
- by-tag：按标签查询相关研报
- search：关键词搜索研报

**使用示例**：
```python
# 按股票查询
research_reports(action="by-stock", code="600519.SH")

# 按行业查询
research_reports(action="by-industry", industry="白酒")

# 关键词搜索
research_reports(action="search", keyword="茅台")

# 最新研报
research_reports(action="list", limit=10)
```

**返回格式**：
```json
{
  "_qc": {
    "status": "success",
    "completeness": 1.0,
    "sources": ["research_reports"],
    "fallback_source": null,
    "missing_dimensions": [],
    "stale_data": []
  },
  "action": "by-stock",
  "count": 2,
  "reports": [
    {
      "id": 1,
      "title": "高盛：白酒行业深度报告 - 茅台估值分析",
      "date": "2026-04-28",
      "source": "Goldman Sachs",
      "url": "https://ima.xxx/goldman-baijiu-maotai",
      "related_stocks": ["600519.SH", "000568.SZ"],
      "industries": ["白酒", "消费"],
      "tags": ["估值", "白酒", "茅台"],
      "summary": "深度分析贵州茅台估值水平，对比五粮液、洋河等竞品"
    }
  ]
}
```

**与其他工具的互补**：
- `stock_analysis`：提供实时数据 + 研报提供深度分析
- `wind_query`：提供财报数据 + 研报提供行业趋势
- `macro_snapshot`：提供宏观数据 + 研报提供政策解读

---

## 🎯 质检层（_qc）说明

所有工具返回值都包含 `_qc` 质检元数据：

```json
{
  "_qc": {
    "status": "success" | "partial" | "failure",
    "completeness": 0.95,  // 数据完整性 (0-1)
    "sources": ["wind", "tushare"],  // 数据来源
    "fallback_source": "akshare",  // 降级数据源
    "missing_dimensions": ["新闻"],  // 缺失维度
    "stale_data": [  // 过期数据
      {
        "field": "K线",
        "last_date": "2026-04-30",
        "delay_days": 4
      }
    ]
  }
}
```

**质检规则**：
- `completeness >= 0.8` → 通过 ✅
- `completeness < 0.8` → 封驳 ❌，需要补充数据

---

## 📊 数据源对比

| 数据源 | 成本 | 数据质量 | 覆盖范围 | 稳定性 |
|--------|------|---------|---------|--------|
| **Wind API** | 免费（现有账号） | ⭐⭐⭐⭐⭐ | 基础行情 | ⭐⭐⭐⭐ |
| **Tushare Pro** | 500元/年 | ⭐⭐⭐⭐⭐ | 财报、一致预期 | ⭐⭐⭐⭐⭐ |
| **AkShare** | 免费 | ⭐⭐⭐⭐ | 全面 | ⭐⭐⭐⭐ |
| **投行研报** | IMA 订阅 | ⭐⭐⭐⭐⭐ | 深度分析 | ⭐⭐⭐⭐⭐ |

---

## 🚀 启动方式

```bash
# 设置环境变量
export TUSHARE_TOKEN="ac6471c66535d4aa49516341175ae6d7a7ba763682fad2b4559a05b3"

# 启动 MCP Server
/Users/Zhuanz/finance-suite/.venv/bin/python3.12 /Users/Zhuanz/finance-suite/mcp_server.py
```

---

## 📝 使用建议

### 个股分析流程

1. **基础数据**：`stock_analysis(code="600519")` - 获取实时行情和财报
2. **深度数据**：`wind_query(action="financials", code="600519.SH")` - 获取完整财报
3. **一致预期**：`wind_query(action="consensus", code="600519.SH")` - 获取分析师预测
4. **同行对比**：`wind_query(action="peers", code="600519.SH")` - 获取可比公司
5. **研报参考**：`research_reports(action="by-stock", code="600519.SH")` - 获取投行研报

### 宏观分析流程

1. **宏观数据**：`macro_snapshot()` - 获取 GDP/CPI/PMI 等
2. **市场情绪**：`market_pulse()` - 获取涨停池、异动
3. **新闻快讯**：`sinafinance_fetch(limit=20)` - 获取实时快讯
4. **研报解读**：`research_reports(action="by-tag", tag="宏观经济")` - 获取宏观研报

---

## 🎉 总结

Finance Suite MCP Server 提供了 **13 个金融工具**，覆盖：
- ✅ 实时行情数据
- ✅ 财报数据
- ✅ 宏观经济数据
- ✅ 市场情绪数据
- ✅ 社交媒体数据
- ✅ 投行研报数据
- ✅ 美股期权数据

**核心优势**：
1. **三层数据源降级**：Wind → Tushare → AkShare，确保数据可用性
2. **质检层**：每个工具返回 _qc 元数据，显式标注数据质量
3. **多维度覆盖**：从实时行情到深度研报，全方位支持投资决策

**适用场景**：
- 个股分析
- 宏观研究
- 量化选股
- 投资决策
- 研究报告生成

---

_更新时间：2026-05-04 23:30_
_维护者：Claude Sonnet 4.6_
