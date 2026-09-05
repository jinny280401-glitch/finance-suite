# Finance Suite 扩展开发指南

> 面向产品经理和开发者，说明如何在重构后的系统上新增场景和业务功能

---

## 一、系统能力边界

### 1.1 系统做什么

```
用户输入（股票代码/行业关键词/视频链接/文本）
  → 自动采集数据（AkShare + 搜索引擎）
  → 喂给 AI（通义千问）+ 写作模板（Prompt）
  → 输出一份 Markdown 分析报告
```

**一句话：换一套数据 + 换一个 Prompt 模板 = 换一个分析场景。**

### 1.2 系统不做什么

- 不做实时行情推送（数据是请求时拉取的）
- 不做交易执行（只分析，不下单）
- 不做用户自定义策略（场景是预定义的）

---

## 二、产品层面：新增一个场景

### 2.1 你需要回答的 5 个问题

| # | 问题 | 示例（以"基金分析"为例） |
|---|---|---|
| 1 | 用户输入什么？ | 基金代码（如 110011） |
| 2 | 需要哪些数据？ | 净值走势、持仓明细、基金经理、同类排名 |
| 3 | 报告长什么样？ | 6 章节：业绩概览、持仓分析、经理评估、同类对比、风险评估、投资建议 |
| 4 | 数据从哪来？ | AkShare 基金接口 + 搜索引擎补充 |
| 5 | 缓存多久？ | 10 分钟（600秒） |

### 2.2 场景定义清单

新增场景需要产出 3 个文件（+1 个可选），放在 `backend/scenarios/<场景名>/` 目录下：

```
scenarios/fund_analysis/
├── config.yaml      ← 元数据 + 数据维度 + 缓存 + QC 配置
├── prompt.md        ← AI 写作模板（系统指令）
├── page.html        ← 前端页面
└── qc_rules.yaml    ← 质检规则（可选，当前未消费）
```

---

## 三、开发层面：新增一个场景

### 3.1 Step 1 — config.yaml

```yaml
# === 必填：展示信息 ===
name: 基金分析
description: 输入基金代码，获取深度分析报告
icon: M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h6
color: from-indigo-500 to-blue-500

# === 必填：路由标识 ===
# 决定 analyze_service 走哪个数据获取分支
# 可选值：stock / macro / auction / industry / extract / null
search_type: stock    # 复用股票数据获取逻辑；全新逻辑需改 analyze_service

# === 可选：数据维度（仅 search_type=stock 时生效）===
dimensions:
  - financials        # 财报
  - price_history     # K线
  - fund_flow         # 资金流
  - news              # 新闻
  - dividends         # 分红
  - valuation         # 估值

# === 可选：缓存 ===
cache:
  ttl: 600            # 秒，默认 600

# === 可选：QC 时效阈值（天）===
qc:
  dimensions:
    financials: { stale_days: 90 }
    price_history: { stale_days: 3 }
    fund_flow: { stale_days: 3 }
    news: { stale_days: 7 }
```

**config.yaml 字段消费对照**：

| 字段 | 被谁消费 | 作用 |
|---|---|---|
| `name/description/icon/color` | ScenarioRegistry → 前端 | 展示 |
| `search_type` | analyze_service | 路由分支 |
| `dimensions` | stock_skill.get_stock_full_data() | 控制获取维度 |
| `cache.ttl` | cache_set() | 缓存有效期 |
| `qc.dimensions.*.stale_days` | build_report_qc() | 时效阈值 |
| `prompt.md` | LLM system prompt | 写作模板 |

### 3.2 Step 2 — prompt.md

写 LLM 系统指令，Markdown 格式。定义报告的结构和写作要求。

```markdown
# 基金分析报告

你是一位专业的基金分析师，请根据以下数据撰写分析报告。

## 报告结构

### 一、核心结论
- 基金评级（推荐/中性/谨慎）
- 一句话总结

### 二、业绩表现
- 近1年/3年/5年收益率
- 同类排名百分位

### 三、持仓分析
...

## 写作要求
1. 所有数字必须来自提供的数据，不得编造
2. 不得给出具体买卖建议或目标价
3. 使用 Markdown 格式
```

### 3.3 Step 3 — page.html

复制现有场景的 `page.html`（如 `stock/page.html`），修改：

1. **skill_type**：`{ skill_type: 'fund_analysis', query }`
2. **页面标题**：`<title>基金分析 - 天玑</title>`
3. **超时设置**：保持 `timeout = 180000`（180秒）

### 3.4 Step 4 — 注册前端路由

在 `backend/app/routers/pages.py` 的 `scenario_pages` dict 添加映射：

```python
scenario_pages = {
    "stock.html": "backend/scenarios/stock/page.html",
    "fund_analysis.html": "backend/scenarios/fund_analysis/page.html",  # 新增
    ...
}
```

### 3.5 不需要改的

| 文件/目录 | 为什么不用改 |
|---|---|
| `engine/` 所有代码 | 引擎是稳定的，新增场景不改引擎 |
| `analyze_service.py` | 复用 stock 数据获取逻辑时不需要改 |
| `registry.py` | 自动扫描 scenarios/ 目录，新目录自动注册 |
| `api.py` | 薄路由，不包含业务逻辑 |

---

## 四、进阶：需要新数据源时

### 4.1 新增 Provider（纯 API 封装）

当需要对接新的外部数据源时：

```python
# backend/engine/providers/fund_provider.py
# 职责：纯 API 调用，3-5 行函数体，无业务逻辑

import akshare as ak

def fund_nav_history(fund_code: str):
    """获取基金净值历史"""
    return ak.fund_open_fund_info_em(symbol=fund_code, indicator="单位净值走势")

def fund_portfolio(fund_code: str):
    """获取基金持仓"""
    return ak.fund_portfolio_hold_em(symbol=fund_code)
```

**依赖规则**：只能依赖外部库，不能依赖 Skill 层或 app/

### 4.2 新增 Skill（业务编排）

当新场景需要全新的数据获取逻辑（不能复用 stock_skill）时：

```python
# backend/engine/skills/fund_skill.py
# 职责：编排数据获取、降级链、超时控制、数据转换

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=4)

async def get_fund_full_data(code: str, dimensions: list[str] | None = None):
    """并发获取基金数据"""
    loop = asyncio.get_event_loop()
    fetch_dims = dimensions or ["nav", "portfolio", "manager", "ranking"]
    
    tasks = {}
    if "nav" in fetch_dims:
        tasks["nav"] = loop.run_in_executor(_executor, _fetch_nav, code)
    if "portfolio" in fetch_dims:
        tasks["portfolio"] = loop.run_in_executor(_executor, _fetch_portfolio, code)
    # ...
    
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)
    return dict(zip(tasks.keys(), results))

def _fetch_nav(code: str):
    from backend.engine.providers import fund_provider
    return fund_provider.fund_nav_history(code)
```

然后在 `analyze_service.py` 添加新的路由分支。

### 4.3 新增 analyze_service 路由分支

当 `search_type` 不是 stock/macro/auction/industry/video 时，需要在 `analyze_service.py` 的 `run_analysis()` 中添加新的 `elif` 分支：

```python
elif search_type == "fund":
    data = await _fetch_fund_data(query, search_query, scenario_config=scenario_config)
```

---

## 五、开发检查清单

### 新增场景

| 检查项 | 要求 |
|---|---|
| 场景目录 | `backend/scenarios/<name>/` |
| config.yaml | 只写被代码消费的字段 |
| prompt.md | Markdown 格式，定义报告结构 |
| page.html | 超时 180000ms，skill_type 正确 |
| pages.py 路由 | 添加 filename → path 映射 |
| 测试 | 添加对应测试用例 |

### 新增 Provider

| 检查项 | 要求 |
|---|---|
| 文件位置 | `backend/engine/providers/` |
| 函数体 | 3-5 行，纯 API 调用 |
| 依赖方向 | 只能依赖外部库，不能依赖 Skill/app |
| 异常处理 | 返回 None 而非抛异常 |

### 新增 Skill

| 检查项 | 要求 |
|---|---|
| 文件位置 | `backend/engine/skills/` |
| 并发获取 | asyncio.gather + ThreadPoolExecutor |
| 降级链 | Wind → AkShare → Tushare（按优先级） |
| 超时控制 | 每个维度独立超时 |
| 日志 | `logger.info("[FLOW] ...")` 标记关键节点 |
| 依赖方向 | 只能依赖 Provider 和 engine/cache |

---

## 六、快速参考

### 文件位置速查

| 要找什么 | 去哪看 |
|---|---|
| 场景配置 | `backend/scenarios/<name>/config.yaml` |
| 写作模板 | `backend/scenarios/<name>/prompt.md` |
| 前端页面 | `backend/scenarios/<name>/page.html` |
| 数据获取逻辑 | `backend/engine/skills/` |
| API 封装 | `backend/engine/providers/` |
| 分析编排 | `backend/app/services/analyze_service.py` |
| 路由入口 | `backend/app/routers/api.py` |
| 日志配置 | `backend/app/logging_config.py` |

### 依赖方向（严格遵守）

```
app/routers → app/services → engine/skills → engine/providers → 外部 API
                                    ↓
                              engine/cache
                              
禁止反向依赖：Provider 不能依赖 Skill，Skill 不能依赖 app/
```

### 日志规范

```python
import logging
logger = logging.getLogger(__name__)

# 数据流关键节点
logger.info("[FLOW] ===== 分析请求开始 =====")
logger.info("[FLOW] 数据采集完成: elapsed=%.2fs sources=%d", elapsed, count)

# Provider 调用（自动记录，不需要手动写）
# 使用 provider_observability.log_provider_call()

# 普通日志用 %s 格式化（延迟求值，性能更好）
logger.info("查询股票: %s", code)          # ✅
logger.info(f"查询股票: {code}")           # ❌
```
