# Finance Suite 重构成果

> 分支：release-1.0 | 测试：150 passed | 日期：2026-09-05

---

## 一、架构总览

### 三层架构：Provider → Skill → Scenario

```
┌─────────────────────────────────────────────────────────────────────┐
│                        用户 / AI Agent                               │
└─────────────┬─────────────────────────────────┬─────────────────────┘
              │ Web (FastAPI)                    │ MCP (FastMCP)
              ▼                                  ▼
┌─────────────────────────┐     ┌──────────────────────────────────────┐
│  app/  (Web 后端)        │     │  mcp_tools/  (MCP 产品线)             │
│  114 行路由 + 788 行编排  │     │  18 个工具，13 个文件                  │
└──────────┬───────────────┘     └──────────────┬───────────────────────┘
           │                                    │
           ▼                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     engine/  (共享引擎)                               │
│                                                                     │
│  providers/ ──→ skills/ ──→ quality/ ──→ llm/                      │
│  (纯API调用)     (业务编排)    (QC质检)     (LLM调用)                │
│                                                                     │
│  registry.py (场景注册)    cache.py (缓存)                           │
└─────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     scenarios/  (场景定义)                            │
│                                                                     │
│  每个场景 = config.yaml + prompt.md + page.html + qc_rules.yaml    │
│  新增场景：复制目录 → 修改配置 → 自动注册，引擎代码零修改            │
└─────────────────────────────────────────────────────────────────────┘
```

### 依赖规则

| 层 | 可以依赖 | 禁止依赖 |
|---|---|---|
| Provider | 外部库（AkShare/Tavily） | Skill、app/ |
| Skill | Provider、engine/cache | app/ |
| Scenario | 无（纯配置） | 无 |
| app/ | engine/ | 禁止直接调 AkShare |
| mcp_tools/ | engine/ | 禁止自己实现数据获取 |

---

## 二、当前能力

### 2.1 七个分析场景

| 场景 | 数据源 | LLM | 配置驱动字段 |
|---|---|---|---|
| **stock** 看票 | AkShare 6维度 + Tavily 5维度 | ✅ | dimensions / cache.ttl / qc.stale_days |
| **macro** 宏观 | AkShare 5路 + Tavily(限定域) | ✅ | prompt.md |
| **auction** 竞价 | AkShare 6路涨停 | ⚠️ 条件 | prompt.md |
| **industry** 行业 | AkShare板块 + Tavily | ✅ | cache.ttl |
| **video** 视频 | Supadata/B站字幕 + 搜索 | ✅ | cache.ttl |
| **meeting** 纪要 | 用户输入 | ✅ | prompt.md |
| **mckinsey** 报告 | 用户输入 | ✅ | prompt.md |

### 2.2 配置驱动

config.yaml 每个字段的消费方：

| 字段 | 消费方 | 作用 |
|---|---|---|
| `name/description/icon/color` | ScenarioRegistry → 前端 | 展示 |
| `search_type` | analyze_service | 路由分支 |
| `dimensions` | stock_skill.get_stock_full_data() | 控制获取维度 |
| `cache.ttl` | cache_set() | 缓存有效期 |
| `qc.dimensions.*.stale_days` | build_report_qc() | 时效阈值 |
| `prompt.md` | LLM system prompt | 写作模板 |

### 2.3 质量检查

| QC 维度 | 实现方式 |
|---|---|
| 数据完整性 | 按维度检查 available/missing，completeness = 可用维度比例 |
| 数据时效 | 按 qc.dimensions.*.stale_days 阈值检测 |
| 幻觉风险 | 基于结构化数据覆盖度（有数据=low，无数据=high） |
| 报告数字校验 | K线收盘价 vs 报告数字，偏差>10% 标记 |
| 发布安全 | 检查禁止结论（目标价/买卖信号） |

### 2.4 可观测性

| 日志标记 | 含义 | 示例 |
|---|---|---|
| `[FLOW]` | 数据流关键节点 | 请求入口/股票解析/数据采集/LLM/完成 |
| `[PROVIDER]` | 数据源调用 | domain=capital_flow outcome=SUCCESS elapsed=0.5s |

### 2.5 MCP 工具（18 个）

| 类别 | 工具 | 文件 |
|---|---|---|
| 分析（复用 engine） | stock_analysis / macro_snapshot / market_pulse | tools/analysis.py |
| 搜索 | search | tools/search.py |
| 视频 | video_extract | tools/video.py |
| 数据源（MCP 独有） | wind_query / jqdata_query / ths_query / emquant_query | tools/wind.py / jqdata.py / ths.py / emquant.py |
| 社交 | xueqiu / zhihu / sina | tools/social.py |
| 业务 | watchlist / factor_scan / research / market_intel | tools/watchlist.py / factor.py / research.py / market_intel.py |
| 期权 | barchart | tools/barchart.py |

---

## 三、量化指标

| 指标 | 重构前 | 重构后 |
|---|---|---|
| 新增场景改动 | 3-5 个核心文件 | 1 个新目录（4 文件） |
| 前后端分离 | ❌ 混杂 | ✅ 完全分离 |
| 数据层 | ❌ 双实现 | ✅ 单一源头 |
| 死代码 | ~4500 行 | 0 |
| MCP Server | 1887 行单文件 | 模块化 13 文件 |
| 配置驱动 | ❌ 死字段 | ✅ 全字段消费 |
| 测试用例 | 121 | 150 |
| 非程序员新增场景 | ❌ 需改 Python | ✅ YAML + Markdown + HTML |

---

## 四、关键文件

| 文件 | 行数 | 职责 |
|---|---|---|
| `app/routers/api.py` | 114 | HTTP 入口 |
| `app/services/analyze_service.py` | 788 | 核心编排 |
| `engine/skills/stock_skill.py` | 1214 | 6维度并发+降级链 |
| `engine/registry.py` | 334 | 场景注册+元数据 |
| `engine/providers/akshare_client.py` | - | AkShare 封装 |
| `engine/providers/search_provider.py` | - | 多源搜索 |
| `app/logging_config.py` | 125 | 集中日志 |
| `engine/cache.py` | 78 | 缓存 |

---

## 五、已知限制

| 限制 | 解除条件 |
|---|---|
| Skill 选择硬编码 | 新增 skill 时需动态路由 |
| Provider 选择硬编码 | 需 Provider 注册机制 |
| qc_rules.yaml 未消费 | 需 QC 规则引擎 |
| 报告 QC 为输入侧代理 | 需 NLP 校验能力 |
