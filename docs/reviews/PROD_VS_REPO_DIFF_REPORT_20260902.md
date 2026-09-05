# 仓库 vs 生产 完整差异对比报告

> **对比基准**
> - **仓库**：`github.com/jinny280401-glitch/finance-suite` (main 分支，2026-09-02 拉取)
> - **生产**：`/Users/huxuan/Downloads/finance-suite-web` (从生产服务器下载，2026-09-02)
>
> **图例说明**
> - 🔴 **影响运行** — 差异会导致功能缺失、接口报错或页面异常
> - 🟡 **需注意** — 差异不影响当前运行，但涉及功能演进方向
> - 🟢 **无影响** — 纯格式/注释/代码风格差异，不影响任何功能

---

## 一、架构级差异概览

| 维度 | 仓库 (GitHub) | 生产 (finance-suite-web) |
|------|-------------|----------------------|
| **后端框架** | 无后端，纯静态 + `serve_local.py` 本地开发 | **FastAPI 应用** (`app/main.py`)，含完整路由体系 |
| **前端路径** | `app/*.html` | `static/app/*.html` |
| **模板系统** | 无 | Jinja2 模板 (`templates/`)，含 login/register/admin/dashboard |
| **数据库** | 无 | SQLite (`finance_suite.db`) + SQLAlchemy ORM |
| **认证体系** | 前端 localStorage 简单守卫 | JWT + bcrypt 完整认证 (`app/auth.py`, `app/database.py`) |
| **依赖管理** | MCP + 数据源导向 | FastAPI + Web 应用导向 |

---

## 二、前端 HTML/JS/CSS 文件差异

### 2.1 `stock.html` — 767 行差异 🔴

| 差异类别 | 生产（有） | 仓库（无） | 影响 |
|---------|-----------|-----------|------|
| **Trust Presentation Layer CSS** | `.trust-panel`, `.trust-disclosure`, `.trust-disclosure-stack`, `.availability-grid`, `.availability-item`, `.availability-status`, `.section-data-note` 等约 140 行 CSS | 不存在 | 🔴 生产页面展示可信度面板、数据完整性摘要；仓库无此功能，部署到生产会**丢失 Trust 展示** |
| **Truth Guard 组件** | `.truth-guard` 样式 + DOM 元素 `#presentationTruthGuard` | 不存在 | 🔴 生产有数据真实性守卫提示条，仓库缺失 |
| **Loading 阶段指示** | `.loading-stage`, `.loading-timeout-note` + 分阶段加载文字（"正在匹配股票"→"正在获取财报"→…） | 仅显示"正在分析中，请稍候..." | 🟡 用户体验差异，不影响功能 |
| **Trust JS 逻辑** | `renderTrustPresentation()`, `normalizeAvailabilityItems()`, `injectSectionDataNotes()`, `getSectionUsage()` 等函数 | 不存在 | 🔴 生产根据后端返回的 `trust_presentation` / `data_availability` 字段动态渲染数据可用性说明，仓库完全缺失 |

**结论**：仓库的 `stock.html` 缺少整个 Trust Presentation 层，如果直接替换生产版本，用户将**看不到数据可信度信息**。

---

### 2.2 `deep-research.html` — 637 行差异 🔴

| 差异类别 | 生产（有） | 仓库（无） | 影响 |
|---------|-----------|-----------|------|
| **Markdown 报告渲染** | 完整的 markdown → HTML 渲染管线（`formatResult` 中正则转换标题/粗体/列表等），含 `.md-body` 样式 | 仅 `<pre>${JSON.stringify(data)}</pre>` 原始 JSON 输出 | 🔴 **仓库版本会把分析报告显示为原始 JSON 而非格式化的 Markdown**，严重影响用户可读性 |
| **PDF 导出功能** | `.pdf-action-bar` + `exportToPdf()` 按钮 + 相关逻辑 | 不存在 | 🔴 **仓库缺失 PDF 导出按钮**，生产用户可导出报告 |
| **Loading 阶段指示** | 分阶段文字 + 超时提示 | 简单"正在分析中" | 🟡 UX 差异 |
| **Trust 展示层** | `.trust-panel`, `.availability-grid`, `renderTrustPresentation()`, `renderAvailabilityItem()` 等 | 不存在 | 🔴 同 stock.html，缺失可信度面板 |
| **QC 质检徽章** | `qcBadge` 渲染（事实覆盖率、幻觉风险、缺失维度） | 不存在 | 🔴 生产展示质检摘要条，仓库缺失 |
| **数据值清洗** | `normalizeDisplayValue()`, `sanitizeTrustText()`, `sanitizeRenderedHtml()` — 将 NaN/null/none 统一显示为"暂不可用" | 不存在 | 🟡 生产对脏数据有容错处理，仓库直接显示原始值 |

**结论**：这是差异最大的文件。仓库版本**无法渲染 Markdown 报告、无 PDF 导出、无 Trust 展示**，直接替换会导致深度研究页面严重退化。

---

### 2.3 `auction.html` — 207 行差异 🔴

| 差异类别 | 生产（有） | 仓库（无） | 影响 |
|---------|-----------|-----------|------|
| **Markdown 报告卡片渲染** | `.report-card`, `.report-meta` CSS + `renderMarkdown()` 函数（按 `###` 分节渲染为卡片）+ `md()` 使用 `marked.min.js` | 直接 `JSON.stringify(data, null, 2)` 输出 | 🔴 **仓库版本将分析报告显示为原始 JSON 而非分节卡片** |
| **Report Meta 信息条** | `renderReportMeta()` — 显示数据日期、完整度、信源、模型推断占比 | 不存在 | 🔴 缺失报告元信息 |
| **trace_token 机制** | `crypto.randomUUID()` 生成 `traceToken`，附加到 API URL | 无 trace_token | 🟡 生产有请求追踪能力，仓库缺失 |
| **空状态语义化** | 消费后端 `candidate_filtering.candidate_conclusion` 字段，区分 `healthy_inputs_zero_matches` / `indeterminate` / `pre_auction_observation` 等不同状态显示不同颜色提示 | 统一显示"当前无可展示的强势候选数据" | 🔴 **仓库无法区分"无候选"和"数据异常"和"竞价进行中"三种状态** |
| **QC 面板扩展字段** | `allowed_use`, `forbidden_use`, `blocked_fields` 三个额外 QC 字段 | 不存在 | 🟡 生产 QC 面板信息更完整 |
| **XSS 防护** | `escapeHtml(data)` 包裹字符串结果 | `<pre>${data}</pre>` 直接插入 | 🔴 **仓库存在 XSS 风险**，字符串结果未经转义直接渲染 |

**结论**：仓库版本缺失 Markdown 渲染、状态区分和 XSS 防护。

---

### 2.4 `macro.html` / `meeting.html` / `video.html` — 各 370+ 行差异 🟢

这三个文件的差异**绝大部分是 CSS 代码格式差异**：

- **生产**：CSS 属性压缩为单行（如 `position: fixed; top: 0; left: 0; right: 0; height: 52px;`）
- **仓库**：CSS 属性展开为多行（每个属性一行）

功能上完全一致，无 Trust 层差异。

| 文件 | 实质差异 | 影响 |
|------|---------|------|
| `macro.html` | 纯 CSS 格式化 | 🟢 无影响 |
| `meeting.html` | 纯 CSS 格式化 | 🟢 无影响 |
| `video.html` | 纯 CSS 格式化 | 🟢 无影响 |

---

### 2.5 `market-temperature-mini.js` — 101 行差异 🔴

| 差异类别 | 生产（有） | 仓库（无） | 影响 |
|---------|-----------|-----------|------|
| **API 实时数据获取** | `hydrateMarketTemperature()` — 调用 `/api/intel/market-context` 获取实时市场语境数据 | 不存在，仅使用静态 fixture 数据 | 🔴 **仓库版本的市场温度卡片始终显示静态假数据**，不接后端 API |
| **数据归一化** | `normalizeMarketContext()` — 处理后端返回的 metrics/themes/qc 结构 | 不存在 | 🔴 无法解析后端数据结构 |
| **降级状态处理** | `emptyFallbackState()` — API 失败时优雅降级 | 不存在 | 🔴 仓库无降级逻辑 |
| **链接更新** | 两个链接：`weekly-recap.html` + `market-snapshot.html` | 一个链接：`href="#"` 占位 | 🔴 仓库缺少"本周复盘"入口，"市场画像"链接指向 `#` |
| **hydrate 调用** | `hydrate: function(el) { hydrateMarketTemperature(el); }` | `hydrate: function(el) { renderMarketTemperature(global.marketTemperatureFixture, el); }` | 🔴 仓库 hydrate 阶段仍渲染 fixture 而非实时数据 |

**结论**：仓库版本市场温度卡片是**纯静态展示**，生产已接入实时 API。

---

### 2.6 `market-temperature-mini.html` — 60 行差异 🔴

| 差异类别 | 生产 | 仓库 | 影响 |
|---------|------|------|------|
| **DOM 构建方式** | `createElement` + `textContent` 安全构建 | `innerHTML` 模板字符串拼接 | 🔴 **仓库版本存在 XSS 风险**（`${item.label}`, `${item.value}` 未转义直接拼入 HTML） |
| **escapeHtml 函数** | 定义了 `escapeHtml()` 工具函数 | 不存在 | 🔴 仓库缺少 HTML 转义工具 |
| **链接区域** | 同 JS 差异（两个链接） | 一个占位链接 | 🔴 同上 |

---

### 2.7 `market-temperature-mini.css` — 7 行差异 🟢

生产多了 `.mt-mini-links` 样式（用于 flex 布局的链接容器），仓库没有。

| 影响 | 因为仓库 HTML 中没有 `.mt-mini-links` 容器，所以此 CSS 差异无实际效果 |
|------|------|
| 🟢 | 无影响 |

---

### 2.8 `sidebar-registry.js` — 10 行差异 🟡

仓库比生产多了一个 `morning_brief` 条目：

```js
morning_brief: {
  key: 'morning_brief',
  title: '今日简报',
  description: 'D13 Morning Brief · 09:25 自动产出',
  enabled: true, order: 40, renderable: true,
  template: 'morning_brief'
}
```

| 影响 | 仓库新增了"今日简报"侧边栏入口，但生产没有。如果仓库前端部署到生产，该入口会显示但**可能无对应后端接口** |
|------|------|
| 🟡 | 需注意：需确认后端是否已支持 `morning_brief` 模板 |

---

### 2.9 前端文件差异汇总

| 文件 | 差异行数 | 影响等级 | 核心差异 |
|------|---------|---------|---------|
| `stock.html` | 767 | 🔴 | 缺失 Trust Presentation 层 |
| `deep-research.html` | 637 | 🔴 | 缺失 Markdown 渲染 + PDF 导出 + Trust 层 |
| `macro.html` | 372 | 🟢 | 纯 CSS 格式化 |
| `meeting.html` | 377 | 🟢 | 纯 CSS 格式化 |
| `video.html` | 376 | 🟢 | 纯 CSS 格式化 |
| `auction.html` | 207 | 🔴 | 缺失 Markdown 渲染 + XSS 防护 + 状态语义化 |
| `market-temperature-mini.js` | 101 | 🔴 | 未接入实时 API |
| `market-temperature-mini.html` | 60 | 🔴 | innerHTML XSS 风险 |
| `market-temperature-mini.css` | 7 | 🟢 | 无影响 |
| `sidebar-registry.js` | 10 | 🟡 | 新增 morning_brief 入口 |
| `index.html` | 0 | 🟢 | 完全一致 |
| `workbench-config.html` | 0 | 🟢 | 完全一致 |
| `market-temperature-fixture.js` | 0 | 🟢 | 完全一致 |

---

## 三、后端脚本文件差异

### 3.1 `scripts/auction_data.py` — 32 行差异 🔴

| 差异类别 | 生产 | 仓库 | 影响 |
|---------|------|------|------|
| **top_gainers 超时控制** | `asyncio.wait_for(..., timeout=_TOP_GAINERS_TIMEOUT_SECONDS)` — AkShare 全市场接口有超时保护，超时后保留其他数据 | 同步调用 `_fetch_spot_sorted()`，无超时保护 | 🔴 **仓库版本可能因 AkShare 接口慢而阻塞整个竞价数据获取链路** |
| **include_top_gainers 参数** | `get_auction_data(include_top_gainers: bool = True)` — 支持跳过涨幅排行 | `get_auction_data()` — 无参数，总是获取 | 🟡 生产更灵活，可按需跳过慢接口 |
| **超时环境变量** | `MARKET_CONTEXT_TOP_GAINERS_TIMEOUT` 可配置 | 不存在 | 🟡 生产支持运行时调参 |

---

### 3.2 `scripts/macro_data.py` — 89 行差异 🔴

| 差异类别 | 生产 | 仓库 | 影响 |
|---------|------|------|------|
| **时间解析与排序** | `_parse_period()`, `_record_period()`, `_latest_records()` — 智能解析 AkShare 混合时间格式（"2024Q1"、"2024年3月"、"第1季度"等），按时间排序取最新 N 条 | 不存在，直接取原始数据 | 🔴 **仓库版本无法正确解析和排序宏观数据的时间维度**，可能返回过期数据而非最新数据 |

---

### 3.3 `scripts/ifind_data.py` — 220 行差异 🟡

| 差异类别 | 生产 | 仓库 | 影响 |
|---------|------|------|------|
| **HTTP 优先模式** | 优先使用 `THS_TOKEN` / `THS_REFRESH_TOKEN` HTTP REST API，失败再降级到 SDK | 优先 SDK，再降级到静态 HTTP token | 🟡 优先级策略不同，生产更合理（SDK 依赖本地安装） |
| **Token 刷新** | `_refresh_access_token()` — 自动用 refresh_token 换取新 access_token | 不存在 | 🟡 生产支持 token 自动续期，仓库需要手动更换静态 token |
| **dotenv 加载** | `load_dotenv()` 自动加载 `.env` | 不存在 | 🟢 不影响功能（环境变量可通过其他方式设置） |

---

### 3.4 脚本文件差异汇总

| 文件 | 差异行数 | 影响等级 | 核心差异 |
|------|---------|---------|---------|
| `scripts/auction_data.py` | 32 | 🔴 | 缺失超时保护，可能阻塞数据获取 |
| `scripts/macro_data.py` | 89 | 🔴 | 缺失时间解析，可能返回过期数据 |
| `scripts/ifind_data.py` | 220 | 🟡 | 优先级策略不同，无 token 自动续期 |

---

## 四、核心配置文件差异

### 4.1 `requirements.txt` — 完全不同 🔴

| 生产 | 仓库 | 说明 |
|------|------|------|
| `fastapi==0.115.0`（精确版本） | `fastapi>=0.115.0`（最低版本） | 🔴 生产锁定版本，仓库可能安装不兼容的新版 |
| `sqlalchemy==2.0.35`, `pyjwt==2.9.0`, `bcrypt==4.2.0`, `jinja2==3.1.4`, `python-multipart==0.0.9` | 不存在 | 🔴 **仓库缺少生产运行必需的 ORM/JWT/密码加密/模板引擎依赖** |
| `reportlab>=4.0.0`, `weasyprint>=62.0` | 不存在 | 🔴 **仓库无法生成 PDF**（对应 deep-research 的 PDF 导出） |
| `mcp>=1.27.0`, `flask>=3.0.0`, `akshare>=1.18.0`, `tushare>=1.4.0`, `jqdatasdk>=1.9.8` 等 | 存在 | 🟢 仓库有更多数据源依赖，但生产未使用 |

**结论**：仓库的 `requirements.txt` 面向 MCP Server 场景，**无法直接用于部署生产 FastAPI 应用**。

---

### 4.2 `mcp_server.py` — 574 行差异（生产 1325 行，仓库 1700 行） 🟡

| 差异类别 | 说明 | 影响 |
|---------|------|------|
| **工具数量** | 生产 12 个工具，仓库 13+ 个（新增 `research_digest`, `market_intel`, `jqdata_query`, `ths_query`, `emquant_query`） | 🟡 仓库 MCP 工具更丰富 |
| **数据源架构描述** | 生产："Wind → Tushare → AkShare 三层降级" | 仓库："Wind → Tushare → JoinQuant → AkShare 多源降级" | 🟡 仓库加入了 JoinQuant 层 |
| **financials 过期检查** | 不存在 | 仓库增加报告期超 180 天标记为 stale | 🟡 仓库 QC 更严格 |
| **dotenv 加载** | 无 | 仓库有 `load_dotenv()` | 🟢 不影响核心功能 |

---

### 4.3 `server_scripts/manage_users.py` — 61 行差异 🔴

| 差异类别 | 生产 | 仓库 | 影响 |
|---------|------|------|------|
| **DEFAULT_USERS 账号列表** | 内置 12 个默认账号（含密码） | 不存在 | 🔴 **仓库无法通过 `sync-defaults` 批量恢复账号** |
| **upsert_user()** | 支持 upsert（存在则更新，不存在则插入） | 不存在 | 🔴 仓库缺少幂等账号同步能力 |
| **sync-defaults 命令** | `python manage_users.py sync-defaults` | 不存在 | 🔴 仓库部署时无法一键初始化账号 |

---

### 4.4 `server_scripts/import_accounts.sh` — 30 行差异 🔴

| 差异类别 | 生产 | 仓库 | 影响 |
|---------|------|------|------|
| **执行方式** | 调用 `manage_users.py sync-defaults`（幂等） | 逐条 `add` 命令（不可重复执行，已存在会报错） | 🔴 **仓库脚本重复执行会出错** |

---

## 五、生产独有文件（仓库完全缺失）

### 5.1 后端核心模块 🔴

| 文件 | 说明 | 影响 |
|------|------|------|
| `app/main.py` | FastAPI 应用入口 | 🔴 **仓库无 Web 服务入口** |
| `app/config.py` | 环境变量配置（Qwen/Tavily/Brave/JWT） | 🔴 仓库无配置管理 |
| `app/database.py` | SQLAlchemy 数据库模型 | 🔴 仓库无数据库层 |
| `app/auth.py` | JWT 认证逻辑 | 🔴 仓库无服务端认证 |
| `app/llm.py` | LLM 调用封装 | 🔴 仓库无 LLM 集成 |
| `app/skills.py` | 技能调度 | 🔴 仓库无技能系统 |
| `app/search.py` | 搜索功能 | 🔴 仓库无搜索 |
| `app/api.py` | 旧版 API 模块 | 🟡 可能已废弃 |

### 5.2 路由体系 🔴

| 文件 | 说明 | 影响 |
|------|------|------|
| `app/routers/__init__.py` | 路由初始化 | 🔴 |
| `app/routers/api.py` | 核心 API 路由 | 🔴 |
| `app/routers/intel.py` | 情报/数据接口 | 🔴 |
| `app/routers/admin.py` | 管理后台 | 🔴 |
| `app/routers/pages.py` | 页面渲染 | 🔴 |
| `app/routers/watchlist.py` | 自选股 | 🔴 |

### 5.3 质量门控 🔴

| 文件 | 说明 | 影响 |
|------|------|------|
| `app/quality_gate/__init__.py` | 模块初始化 | 🔴 |
| `app/quality_gate/core.py` | 门控核心逻辑 | 🔴 |
| `app/quality_gate/rules.py` | 门控规则定义 | 🔴 |
| `app/quality_gate/test_quality_gate.py` | 门控测试 | 🟡 |
| `app/quality_gate/README.md` | 文档 | 🟢 |

### 5.4 模板页面 🔴

| 文件 | 说明 | 影响 |
|------|------|------|
| `templates/base.html` | 基础模板 | 🔴 |
| `templates/index.html` | 首页模板 | 🔴 |
| `templates/login.html` | 登录页 | 🔴 |
| `templates/register.html` | 注册页 | 🔴 |
| `templates/admin.html` | 管理后台 | 🔴 |
| `templates/dashboard.html` | 仪表盘 | 🔴 |
| `templates/pricing.html` | 定价页 | 🔴 |
| `templates/skill.html` | 技能页 | 🔴 |
| `templates/login-test.html` | 登录测试 | 🟡 |

### 5.5 前端独有页面 🟡

| 文件 | 说明 | 影响 |
|------|------|------|
| `static/app/d13_close_brief.html` | 收盘简报 | 🟡 仓库缺失此功能页面 |
| `static/app/market-context.html` | 市场语境 | 🟡 仓库缺失 |
| `static/app/market-snapshot.html` | 市场快照 | 🟡 仓库缺失 |
| `static/app/weekly-recap.html` | 周度复盘 | 🟡 仓库缺失 |
| `static/app/pe-band-chart.js` | PE 波段图 | 🟡 仓库缺失 |
| `static/app/market-snapshot-valuation.js` | 市场估值快照 | 🟡 仓库缺失 |
| `static/app/market-valuation-snapshot.js` | 市场估值快照 | 🟡 仓库缺失 |
| `static/app/marked.min.js` | Markdown 渲染库 | 🔴 **仓库 auction/deep-research 的 Markdown 渲染依赖此库** |
| `static/app/weekly-recap-latest.json` | 周度复盘数据 | 🟡 仓库缺失 |

### 5.6 测试套件 🟡

| 文件 | 说明 |
|------|------|
| `tests/test_auction_cache_bypass.py` | 竞价缓存绕过测试 |
| `tests/test_auction_gate_before_prompt.py` | 竞价门控测试 |
| `tests/test_auction_l2_enforcement.py` | L2 强制执行测试 |
| `tests/test_auction_semantic_p0.py` | 竞价语义 P0 测试 |
| `tests/test_auction_temporal_provenance.py` | 竞价时间溯源测试 |
| `tests/test_fetch_receipts.py` | 数据获取凭证测试 |

### 5.7 运行时文件 🔴

| 文件 | 说明 | 影响 |
|------|------|------|
| `.env` | 生产环境变量（含密钥） | 🔴 仓库仅有 `.env.example` |
| `finance_suite.db` | SQLite 数据库 | 🔴 仓库无数据库文件 |
| `skills.py` / `skill.html` | 技能系统入口 | 🟡 仓库无此功能 |
| `CONTRIBUTING.md` | 贡献指南 | 🟢 文档差异 |

---

## 六、仓库独有文件（生产不存在）

| 文件/目录 | 说明 | 影响 |
|----------|------|------|
| `research_runtime/` | Vera 研究运行时（Session/Evidence Bundle/Workflow/Events） | 🟡 仓库有完整设计但生产未集成 |
| `prompts/` | 19 个分析提示词模板 | 🟡 仓库有但生产未使用 |
| `scripts/stock_data.py` | 个股数据脚本 | 🟡 生产已将数据逻辑移入 `app/` 模块 |
| `scripts/video_data.py` | 视频数据脚本 | 🟡 同上 |
| `scripts/watchlist.py` | 自选股脚本 | 🟡 同上 |
| `scripts/emquant_data.py` | 东方财富 Choice 数据 | 🟡 生产未集成 |
| `scripts/tushare_data.py` | Tushare 数据 | 🟡 生产未直接使用 |
| `scripts/wind_data.py` | Wind 数据 | 🟡 生产未直接使用 |
| `scripts/factor_scan.py` | 因子扫描 | 🟡 生产未集成 |
| `scripts/finance_data_contract.py` | 数据合约 | 🟡 生产未集成 |
| `scripts/finance_data_gateway.py` | 数据网关 | 🟡 生产未集成 |
| `scripts/research_demo_api.py` | 研究演示 API | 🟡 生产未集成 |
| `scripts/research_reports.py` | 研报管理 | 🟡 生产未集成 |
| `scripts/search.py` | 搜索脚本 | 🟡 生产未集成 |
| `scripts/site_smoke_check.py` | 站点冒烟检查 | 🟢 仅运维用 |
| `scripts/smoke_data_gateway.py` | 网关冒烟测试 | 🟢 仅验证用 |
| `scripts/workflow_orchestrator.py` | 工作流编排 | 🟡 生产未集成 |
| `app/xueqiu-hot.html` | 雪球热点页面 | 🟡 仓库有此页面，生产无 |
| `serve_local.py` | 本地开发服务器 | 🟢 仅本地开发用 |
| `smoke_*.py` (10 个) | Smoke 测试脚本 | 🟡 仓库有验证体系，生产未纳入 |
| `docs/` 大量治理文档 | governance/evidence/incidents/reviews | 🟢 文档不影响运行 |
| `prompts/` 提示词目录 | 19 个分析提示词 | 🟡 生产未使用 |
| `references/` 参考文档 | 设计参考 | 🟢 不影响运行 |
| `deploy/` 部署配置 | nginx 配置 + 部署脚本 | 🟡 生产部署方式不同 |
| `ops/` 运维脚本 | 健康检查、备份等 | 🟡 生产可能有自己的运维体系 |

---

## 七、关键风险矩阵

| 优先级 | 差异 | 风险描述 |
|--------|------|---------|
| **P0** | `deep-research.html` 缺失 Markdown 渲染 + PDF 导出 | 报告页面完全不可用（显示原始 JSON） |
| **P0** | `auction.html` 缺失 Markdown 渲染 + XSS 防护 | 报告不可读 + 安全风险 |
| **P0** | `market-temperature-mini.js` 未接入 API | 市场温度卡片显示假数据 |
| **P0** | `market-temperature-mini.html` innerHTML XSS | 安全风险 |
| **P0** | 整个后端体系缺失（main.py/routers/auth/database） | 仓库无法作为 Web 服务部署 |
| **P0** | `requirements.txt` 不匹配 | 仓库依赖列表无法启动生产应用 |
| **P1** | `stock.html` / `deep-research.html` 缺失 Trust 展示层 | 用户无法看到数据可信度信息 |
| **P1** | `auction.html` 缺失空状态语义化 | 无法区分"无候选"与"数据异常" |
| **P1** | `scripts/macro_data.py` 缺失时间解析 | 宏观数据可能返回过期值 |
| **P1** | `scripts/auction_data.py` 缺失超时保护 | 慢接口可能阻塞整条链路 |
| **P1** | `manage_users.py` 缺失 sync-defaults | 部署时无法幂等恢复账号 |
| **P2** | `sidebar-registry.js` 新增 morning_brief | 需确认后端是否支持 |
| **P2** | `ifind_data.py` 优先级策略不同 | 生产 HTTP 优先更合理 |
| **P3** | `macro.html` / `meeting.html` / `video.html` CSS 格式 | 纯风格差异，无影响 |
| **P3** | `market-temperature-mini.css` 7 行 | 无影响 |

---

## 八、核心结论

1. **两套代码已严重分叉** — 生产是一套完整的 FastAPI 全栈应用（含路由/数据库/认证/模板/质量门控），仓库更偏向静态前端 + MCP 脚本工具集 + 治理文档。

2. **前端差异集中在 Trust 层和渲染管线** — 生产 HTML 比仓库多了：
   - Trust Presentation Layer（可信度面板、数据完整性摘要、章节数据注释）
   - Markdown 报告渲染（deep-research / auction）
   - PDF 导出功能
   - XSS 防护（escapeHtml）
   - 实时 API 数据接入（market-temperature）

3. **仓库有但生产没用** — `research_runtime`、`prompts/`、大量数据源脚本、smoke tests、治理文档均未部署到生产。

4. **生产有但仓库缺失** — 后端路由体系、模板系统、数据库、认证、quality_gate、多个前端页面（market-snapshot、weekly-recap 等）。

5. **如果要将仓库代码同步到生产**，需要重点补齐：
   - Trust Presentation 层（CSS + JS）
   - Markdown 渲染管线（依赖 `marked.min.js`）
   - API 实时数据接入（market-temperature hydrate）
   - XSS 防护（escapeHtml）
   - 后端路由体系 + 数据库 + 认证
   - `requirements.txt` 合并

---

*报告生成时间：2026-09-02*
