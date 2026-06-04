# Finance Suite Source Taxonomy + Gateway Trust Contract v2 分工稿

日期：2026-06-04

## 0. 当前判断

旧手册的四层链路仍然成立，但已经不够表达当前系统。现在 Finance Suite 同时存在：

- 机构/准机构金融数据：Wind、同花顺 iFinD HTTP、东方财富 Choice、Tushare、JoinQuant/JQData、AkShare/东方财富公开页。
- 市场情报与舆情：雪球、知乎、新浪财经、Barchart、Tavily、Brave。
- 研报与知识层：东方财富研报、手动维护投行研报、IMA/知识库、LLM 脱水。
- 统一出口雏形：`finance_data_gateway.py` v0，只覆盖 quote，链路仍是 Wind -> Tushare -> JoinQuant -> AkShare -> cache。

因此下一阶段不应只把旧四层扩成一条 12 层直线。12 级/多级信源是 Source Taxonomy，不是 fallback chain。真实执行必须采用：

```text
全局信源地图
+
按功能域定义 route policy
+
统一 Gateway Contract / QC Contract / Trust Gate Contract
```

正确链路：

```text
Provider -> Gateway -> QC -> Trust Gate -> Evidence -> LLM
```

禁止链路：

```text
Provider -> LLM -> QC
```

重要约束：同花顺 HTTP 已接通，但 THS_TOKEN/额度应作为稀缺资源使用。除 smoke test 外，不做高频或批量实测；优先用 refresh token 续 token，用缓存降低调用。

## 1. 建议的 Source Taxonomy

| Tier | 信源组 | 定位 | 当前状态 | 主要进入功能 |
|---|---|---|---|---|
| Tier 1 | Wind / 同花顺 iFinD HTTP / 东方财富 Choice | 商业终端级强源 | Wind 已集成；iFinD HTTP 已接通；Choice 环境需复核 | 行情、财务、一致预期、估值、股东、日历 |
| Tier 2 | Tushare Pro / JoinQuant / JQData | 标准化与策略研究源 | 已集成；JQData 试用数据可能延迟 | 日频行情、财务、交易日历、估值分位、因子验证 |
| Tier 3 | AkShare / 东方财富公开 | 免费公开源与兜底源 | 已广泛使用 | 行情、财报指标、集合竞价、板块、人气榜 |
| Tier 4 | 雪球 / 新浪财经 / Barchart | 市场讨论、快讯、海外补充 | MCP 工具已接 | 热门讨论、热股、7x24 快讯、美股、期权 |
| Tier 5 | Tavily / Brave / 公开 Web | 搜索、新闻、政策、网页交叉校验 | 已接 | 新闻、政策、研报、URL 提取 |
| Tier 6 | LLM / OpenRouter / 规则 fallback | 脱水、表达、结构化 | 规则 fallback 已有；LLM key 待稳定 | 研报摘要、市场语言、上下文注入 |

说明：Tier 4-Tier 6 不应参与硬数据计算，只能进入“观点、情报、解释、引用”层。报告里必须区分硬数据、市场观点、AI 脱水。

## 2. 按功能域的 Route Policy

### 2.1 个股行情 / 快照

推荐策略：

```text
primary: Wind -> iFinD HTTP -> Tushare -> AkShare
batch:   Tushare -> JoinQuant/JQData -> AkShare/Eastmoney -> cache
smoke:   iFinD HTTP(connect + 单标的)
```

当前差距：

- `finance_data_gateway.py` 仍是 `Wind -> Tushare -> JoinQuant -> AkShare -> cache`。
- `stock_analysis` 仍主要走 `stock_data.py` 的 Wind/AkShare，加 JQData 兜底。
- iFinD 已接通但未进入主 route policy。

验收：

- `quote` 统一出口记录 `provider_chain`、`attempted_sources`、`provider`、`freshness`。
- iFinD 是 Tier 1 强源，但 `quota_sensitive=true`，只做少量 smoke 和按需交互调用，避免 token/额度被打空。

### 2.2 财务 / 一致预期 / 估值

推荐策略：

```text
Wind -> Choice -> iFinD HTTP -> Tushare -> JoinQuant/JQData -> AkShare
```

排序原因：

- Wind/Choice 在财报与一致预期口径上更强。
- iFinD HTTP 已通，但 `basic_data_service` 财务指标需要补超级命令参数，否则容易 null。
- Tushare 可做标准财务表兜底。
- JoinQuant 更适合估值分位和策略校验，不适合当实时财务主源。

当前差距：

- `wind_query.financials` 当前链路是 `tushare -> joinquant -> akshare`，没有 Wind/Choice/iFinD。
- `ths_query.financials/consensus` 能通 HTTP endpoint，但参数映射不完整。

验收：

- 对每个字段给出 `field_source` 和报告期。
- `_qc.missing_dimensions` 必须列出缺失字段，不允许用 null 伪装完整。

### 2.3 因子扫描 / 策略验证

推荐链：

```text
trading_system -> JoinQuant/JQData -> Wind -> Tushare -> AkShare -> empty_safe_result
```

当前状态：

- `factor_scan` 已接近这个设计。

下一步：

- 明确 JoinQuant 试用延迟进入 `stale_data`。
- 统一 `fallback_chain` 与 `finance_data_gateway` 的命名。

### 2.4 市场脉搏 / 热股 / 集合竞价

推荐链：

```text
东方财富/AkShare -> iFinD HTTP(仅关键校验) -> 雪球热股 -> 新浪快讯 -> cache
```

原则：

- 不用 Wind/iFinD 做大批量盘面榜单主源，成本和额度不划算。
- iFinD 只用于关键指数/核心标的交叉校验。

### 2.5 研究 / 舆情 / 资讯

推荐链：

```text
东方财富研报 -> research_reports 手动精选 -> Tavily -> Brave -> 雪球/知乎 -> 新浪快讯 -> LLM/规则脱水
```

原则：

- 新闻和观点不能覆盖硬数据。
- LLM 只负责脱水、聚类、表达，不负责创造事实。

### 2.6 Market Context Layer

推荐输入：

```text
market_pulse(东方财富/AkShare)
+ research_digest(东方财富研报)
+ discussions(雪球/知乎/新浪)
+ quote/index spot(iFinD/Wind 少量校验)
+ macro_snapshot(AkShare/Choice)
```

输出仍保持产品边界：

```text
一句话市场结构 + 三个关键因子 + 详情入口
```

不要把 Market Context 做成交易建议。

## 3. 分工

### A. 架构与契约 Owner：Codex

目标：先把 Source Taxonomy、Gateway Contract、QC Contract、Trust Gate Contract 变成代码可执行的统一契约。

任务：

1. 冻结 `FinanceDataResponse`：
   - `ok/provider/provider_tier/freshness/as_of/data/_qc`。
   - 兼容旧 `qc`，新消费端优先读 `_qc`。
2. 冻结 `_qc` Trust Contract：
   - 增加 `dimension_sources`、`partial`、`missing_fields`、`attempted_sources`、`provider_chain`。
   - 不允许把 null/空字符串当作 `success 1.0`。
3. 更新 MCP 顶部说明，不再写“四层”作为总架构；MCP 只是 Gateway 的消费端之一。

交付：

- `finance_data_gateway.py` v1
- `finance_data_contract.py` v1
- `docs/data_gateway_v1_contract.md`
- smoke tests

### B. iFinD / Choice 新源 Owner：CC

目标：把新接入源从“独立工具”变成“可参与降级链的 provider”。

任务：

1. iFinD HTTP：
   - 冻结 `THS_TOKEN/THS_REFRESH_TOKEN` 使用策略：connect/小样本 smoke 可以，批量走缓存。
   - 补 `basic_data_service` 超级命令参数映射。
   - 先覆盖字段：quote、pe_ttm、pb_lf、market_cap、target_price、rating、report_date。
2. Choice / EmQuant：
   - 复核服务器 SDK 连接状态。
   - 如果 SDK 仍需激活，明确状态为 `configured_but_unavailable`，不要进入主链。
3. 给每个字段提供 normalize 函数，输出统一字段名。

交付：

- `scripts/ifind_data.py` 参数映射补丁
- `scripts/emquant_data.py` 健康检查补丁
- `tests/test_ifind_emquant_provider.py`

### C. 旧源整合 Owner：Codex + CC

目标：把 Wind/Tushare/JoinQuant/AkShare 的旧逻辑接入新 gateway。

任务：

1. 把 `wind_query` 的 action chain 改成引用 gateway provider chain。
2. 把 `stock_analysis` 从 `stock_data.py` 的隐式 Wind/AkShare，迁移到 gateway quote + financials。
3. 保留 `stock_data.py` 作为 AkShare/缓存 provider，而不是上层业务入口。

交付：

- `wind_query` 兼容旧 action，但内部走 gateway。
- `stock_analysis` 输出增加 `dimension_sources`。

### D. Research / Market Intel Owner：CC

目标：把“硬数据链”和“观点链”分开，但在 Market Context 合并。

任务：

1. `research_digest` 保持东方财富研报主源，不参与硬数据链。
2. `market_intel` 顶层 `_qc` 要写清楚每个 panel 的来源。
3. `market_context` 只消费摘要级指标，不直接触发昂贵 provider 批量请求。

交付：

- `market_intel` 聚合 `_qc` 完整化
- `market_context` 输入来源表

### E. 前端与报告展示 Owner：前端/产品

目标：用户看得到“备用数据源”和“不完整维度”，但不被复杂链路干扰。

任务：

1. 行情卡片展示：更新时间、provider、freshness。
2. 财务分析展示：报告期、币种、合并口径、dimension_sources。
3. 报告页脚展示：硬数据源、观点源、AI 脱水源三类来源。
4. 当 `_qc.status=partial/failure` 时，前端必须降级展示，不允许按完整报告渲染。

### F. 运维 / 行政

目标：保证关键源权限、额度、IP 白名单稳定。

任务：

1. 维护 iFinD HTTP refresh token、服务器 IP 白名单、额度状态。
2. 维护 Wind/Choice/Tushare/JQData 凭据。
3. 建一个“信源健康表”，每天只跑 connect + 单标的小样本，不跑批量。

## 4. Sprint 拆法

### Sprint 1：冻结 Contract，不大改业务

范围：

- 写 `data_gateway_v1_contract` 文档。
- 冻结 `FinanceDataResponse`、`_qc` Trust Contract、Trust Gate 输入边界。
- v0 只做兼容升级：新增 `_qc/provider_tier/dimension_sources/partial/missing_fields`，保留旧 `qc`。
- 不改前端。

验收：

- smoke 仍通过。
- 返回同时包含 `_qc` 和旧 `qc`。
- 文档明确：12 级是 Source Taxonomy，不是执行顺序。

### Sprint 2：Provider Registry + iFinD/Choice provider 化

范围：

- 实现 `WindProvider`、`IFindProvider`、`ChoiceProvider`、`TushareProvider`、`JoinQuantProvider`、`AkShareProvider`。
- 给 provider 增加 `provider_tier/cost_level/quota_sensitive/allowed_usage/disallowed_usage`。
- 补 iFinD 超级命令参数映射。
- 复核 Choice 是否可用。
- iFinD 只做 connect + 单标的小样本 smoke；批量绕开或走缓存。

验收：

- `connect all` + `600519 quote` smoke 通过。
- 无字段时进入 `missing_fields`，不报 success 1.0。

### Sprint 3：迁移业务工具

范围：

- `wind_query` 内部改用 gateway。
- `stock_analysis` 接入 gateway。
- `market_pulse`、`macro_snapshot` 接入 gateway。
- `factor_scan` 做命名对齐。

验收：

- 旧 MCP action 不破坏。
- `_qc` 多出新字段但旧字段保持。

### Sprint 4：Research Runtime / Market Context 融合

范围：

- Research Runtime 只消费通过 Gateway/QC/Trust Gate 的 Evidence。
- Market Context 引入硬数据/观点数据分层。
- 报告与前端展示 provider/freshness。

验收：

- 页面可解释“今天市场是什么状态”，但不输出交易建议。

## 5. 风险与原则

1. 不能把 Source Taxonomy 做成固定直线。不同功能域的最优 route policy 不同。
2. Wind/iFinD/Choice 是 Tier 1 Group，主要差异是授权、API 能力、成本、额度，不是可信度。
3. iFinD HTTP 是强源，但 token/额度敏感，不适合全量扫描主源。
4. Choice 如果 SDK 激活不稳定，应保持 optional，不应阻塞主链。
5. 搜索、雪球、知乎、新浪、LLM 不能参与硬数据结论，只能做情报和解释。
6. `_qc.status` 比 HTTP 200 更重要；`200 + _qc.status=failure` 仍是失败。
