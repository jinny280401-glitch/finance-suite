# Finance Suite 系统重构方案

> **状态：✅ 已完成**（2026-09-05 全部 Phase 执行完毕，150 测试通过）
> 
> 基于系统分析报告，面向可迭代场景引擎的重构设计

---

## 一、重构目标

| 目标 | 现状问题 | 重构后 |
|------|---------|--------|
| **底层架构稳定** | 新场景要改 if-elif 核心代码 | 引擎框架不变，场景即插即用 |
| **业务功能清晰** | 前后端混杂，数据层双轨 | 前端/后端/数据/引擎 四层分离 |
| **工程结构明确** | app/ 混入 HTML/JS/CSS/Python | 按职责分目录，一眼看懂 |
| **场景可迭代复用** | Prompt 和业务逻辑耦合在 640 行文件 | 每个场景独立目录，复制即新增 |
| **用户/管理功能分离** | 用户 API 和管理 API 混在同一路由 | user_api / admin_api 完全隔离 |
| **管理端支持新场景开发** | 无管理后台 | 管理端可创建/编辑/测试场景 |

---

## 二、核心设计理念：场景引擎

### 2.1 一句话

**框架是发动机，场景是燃料盒。换场景不换框架。**

```
┌──────────────────────────────────────────────────────────────┐
│                     场景引擎 (Engine)                         │
│                                                              │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│   │ 数据采集  │ →  │ 质量检查  │ →  │ LLM 分析 │ → 输出报告  │
│   └──────────┘    └──────────┘    └──────────┘             │
│        ↑               ↑               ↑                   │
│        │               │               │                   │
│   Scenario 声明:    Scenario 声明:    Scenario 声明:        │
│   providers=[...]   qc_rules=[...]   prompt="..."          │
│                                                              │
│   引擎读取 Scenario 配置，自动编排整个流程                     │
│   新增场景 = 新增一个 Scenario 目录，不动引擎代码              │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 场景 = 配置 + 模板 + 规则

每个场景就是一个目录，包含三样东西：

```
scenarios/
└── stock/
    ├── config.yaml          # 声明：用哪些数据源、什么搜索策略
    ├── prompt.md            # LLM 写作模板（系统指令）
    └── qc_rules.yaml        # 质量检查规则（完整性阈值、必需维度等）
```

**config.yaml 示例：**
```yaml
name: 看票分析
description: 输入股票代码或名称，获取深度分析报告
icon: chart-bar
color: blue

# 数据源声明
providers:
  - type: akshare_stock
    config:
      include: [kline, financials, fund_flow, news, dividends]
    concurrency: 5

  - type: search
    config:
      strategy: stock_multi_dimension   # 5维度并发搜索
      primary: tavily
      fallback: brave

# 缓存策略
cache:
  enabled: true
  ttl: 600

# 质量门控
qc:
  min_completeness: 0.8
  min_sources: 2
  require_structured: true
  hallucination_check: true
```

**新增场景只需三步：**
1. 复制一个现有场景目录
2. 修改 config.yaml（数据源）、prompt.md（写作模板）、qc_rules.yaml（质检规则）
3. 如果有新数据源，写一个 Provider 文件（继承基类）

**引擎代码零修改。**

---

## 三、目标工程结构

```
finance-suite/
│
├── engine/                          # 🔧 引擎层（稳定，很少改动）
│   ├── __init__.py
│   ├── pipeline.py                  # 主编排管线：采集→QC→LLM→输出
│   ├── registry.py                  # 场景/Provider 注册中心
│   ├── cache.py                     # TTLCache 封装
│   │
│   ├── providers/                   # 数据提供层（可插拔）
│   │   ├── __init__.py
│   │   ├── base.py                  # BaseProvider 抽象基类
│   │   ├── akshare_provider.py      # AkShare 统一封装
│   │   ├── search_provider.py       # Tavily + Brave 搜索
│   │   ├── video_provider.py        # YouTube/B站字幕
│   │   └── user_input_provider.py   # 用户直接输入（会议纪要等）
│   │
│   ├── quality/                     # 质量检查层（统一入口）
│   │   ├── __init__.py
│   │   ├── gate.py                  # QualityGate 统一门控
│   │   ├── rules.py                 # 内置规则集
│   │   ├── event_facts.py           # 宏观事件事实预检
│   │   └── publication.py           # 发布安全控制
│   │
│   └── llm/                         # LLM 调用层
│       ├── __init__.py
│       ├── client.py                # Qwen API 调用
│       └── prompts.py               # Prompt 加载器（从 .md 文件读取）
│
├── scenarios/                       # 📦 场景定义层（频繁改动，复制即新增）
│   │                                  每个场景 = 配置 + 模板 + 规则 + 前端页面
│   │                                  复制整个目录即可新增完整场景
│   ├── stock/
│   │   ├── config.yaml              # 数据源 + 缓存 + QC 配置
│   │   ├── prompt.md                # LLM 系统指令（写作模板）
│   │   ├── qc_rules.yaml            # 质量检查规则
│   │   └── page.html                # 前端页面（stock.html）
│   ├── macro/
│   │   ├── config.yaml
│   │   ├── prompt.md
│   │   ├── qc_rules.yaml
│   │   └── page.html                # 前端页面（macro.html）
│   ├── auction/
│   │   ├── config.yaml
│   │   ├── prompt.md
│   │   ├── qc_rules.yaml
│   │   └── page.html                # 前端页面（auction.html）
│   ├── industry/
│   │   ├── config.yaml
│   │   ├── prompt.md
│   │   ├── qc_rules.yaml
│   │   └── page.html                # 前端页面（deep-research.html）
│   ├── video/
│   │   ├── config.yaml
│   │   ├── prompt.md
│   │   ├── qc_rules.yaml
│   │   └── page.html                # 前端页面（video.html）
│   ├── mckinsey/
│   │   ├── config.yaml
│   │   ├── prompt.md
│   │   ├── qc_rules.yaml
│   │   └── page.html                # 前端页面
│   └── meeting/
│       ├── config.yaml
│       ├── prompt.md
│       ├── qc_rules.yaml
│       └── page.html                # 前端页面（meeting.html）
│
│   ★ 新增场景完整流程：
│     cp -r scenarios/stock scenarios/fund_analysis
│     修改 config.yaml / prompt.md / qc_rules.yaml / page.html
│     引擎代码零修改，前端自动注册新入口
│
├── app/                             # 🌐 后端应用层
│   ├── __init__.py
│   ├── main.py                      # FastAPI 入口
│   │                                  包含: lifespan（DB初始化 + 默认管理员创建
│   │                                  + 股票缓存预热）、GET /api/health、
│   │                                  401异常处理器、StaticFiles 挂载策略
│   ├── config.py                    # 环境变量 + 配置中心
│   │
│   ├── models/                      # 数据模型
│   │   ├── __init__.py
│   │   ├── user.py                  # 用户模型
│   │   ├── usage.py                 # 用量模型
│   │   └── watchlist.py             # 自选股模型
│   │
│   ├── auth/                        # 认证模块
│   │   ├── __init__.py
│   │   ├── jwt_handler.py           # JWT 签发/验证
│   │   ├── password.py              # 密码哈希
│   │   └── dependencies.py          # FastAPI Depends (get_current_user 等)
│   │
│   ├── api/                         # 用户 API（面向终端用户）
│   │   ├── __init__.py
│   │   ├── analyze.py               # POST /api/analyze
│   │   ├── intel.py                 # GET /api/intel/*
│   │   ├── watchlist.py             # /api/watchlist/*
│   │   ├── export.py                # POST /api/export-pdf
│   │   └── auth.py                  # /api/register, /api/login, etc.
│   │
│   ├── admin/                       # 管理 API（面向管理员）
│   │   ├── __init__.py
│   │   ├── scenarios.py             # 场景 CRUD（创建/编辑/测试场景）
│   │   ├── users.py                 # 用户管理
│   │   ├── providers.py             # Provider 状态监控
│   │   ├── quality.py               # QC 规则管理
│   │   └── system.py                # 系统监控（日志/健康检查/DB池）
│   │
│   ├── pages/                       # 页面路由（Jinja2 模板渲染）
│   │   ├── __init__.py
│   │   └── routes.py                # /, /login, /register, /dashboard, /admin
│   │
│   └── database/                    # 数据库
│       ├── __init__.py
│       ├── engine.py                # SQLAlchemy engine + session
│       └── init.py                  # 建表 + 默认管理员
│
├── frontend/                        # 🎨 共享前端资源（非场景页面）
│   ├── shared/                      # 共享组件
│   │   ├── sidebar-registry.js      # 侧栏卡片注册
│   │   ├── header.js                # 公共头部
│   │   └── auth-guard.js            # 登录守卫
│   ├── pages/                       # 非场景页面（平台级页面）
│   │   ├── index.html               # 工作台首页（入口导航）
│   │   ├── workbench-config.html    # 工作台配置
│   │   ├── xueqiu-hot.html          # 雪球热门（市场情报）
│   │   ├── market-snapshot.html     # 市场快照（市场情报）
│   │   ├── market-context.html      # 市场画像（市场情报）
│   │   ├── market-temperature-mini.html
│   │   ├── weekly-recap.html
│   │   ├── d13_close_brief.html
│   │   └── d13_midday_pulse.html
│   ├── scripts/                     # 市场情报页面 JS
│   │   ├── market-temperature-mini.js
│   │   ├── market-snapshot-valuation.js
│   │   ├── market-valuation-snapshot.js
│   │   ├── pe-band-chart.js
│   │   └── market-temperature-fixture.js
│   ├── styles/                      # 共享 CSS
│   │   └── market-temperature-mini.css
│   └── lib/                         # 第三方库
│       └── marked.min.js
│
├── templates/                       # Jinja2 模板（服务端渲染）
│   ├── base.html
│   ├── index.html                   # 营销首页
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── admin/                       # 管理后台模板
│   │   ├── base.html
│   │   ├── scenarios.html           # 场景管理页
│   │   ├── scenario_edit.html       # 场景编辑器
│   │   ├── users.html
│   │   └── system.html
│   ├── pricing.html
│   └── skill.html
│
├── mcp/                             # MCP Server（AI Agent 接口，独立产品线）
│   ├── __init__.py
│   ├── server.py                    # MCP 主入口（瘦适配器，调用 engine/）
│   ├── tools/                       # MCP 工具定义
│   │   ├── analysis.py              # stock_analysis / macro_snapshot / market_pulse
│   │   ├── search.py                # search（多源搜索）
│   │   ├── video.py                 # video_extract
│   │   ├── watchlist.py             # watchlist_manage
│   │   ├── factor.py                # factor_scan
│   │   ├── market_intel.py          # market_intel
│   │   └── research.py              # research_reports / research_digest
│   ├── providers/                   # MCP 独有数据源（Web 应用不使用的）
│   │   ├── wind_provider.py         # Wind 万得（多源降级）
│   │   ├── tushare_provider.py      # Tushare Pro（Wind 降级第二层）
│   │   ├── jqdata_provider.py       # JQData 聚宽
│   │   ├── ths_provider.py          # 同花顺 iFinD
│   │   ├── emquant_provider.py      # 东方财富 Choice
│   │   ├── xueqiu_provider.py       # 雪球（autocli）
│   │   ├── zhihu_provider.py        # 知乎（autocli）
│   │   ├── sinafinance_provider.py  # 新浪财经快讯
│   │   ├── barchart_provider.py     # Barchart 期权
│   │   └── observability.py         # Fetch Receipt 可观测性（JSONL 日志）
│   └── trust_gate.py                # Wind Trust Gate 执行器
│
├── tests/                           # 测试
│   ├── conftest.py
│   ├── test_engine/                 # 引擎层测试
│   ├── test_scenarios/              # 场景测试
│   ├── test_api/                    # API 测试
│   └── test_admin/                  # 管理 API 测试
│
├── data/                            # 数据文件
│   ├── watchlist.json
│   ├── finance_suite.db
│   └── weekly-recap-latest.json     # 周报 mock 数据（迁移自 app/）
│
├── deploy/                          # 部署配置
│   ├── nginx/
│   │   └── finance-suite.conf       # Nginx 反向代理配置
│   ├── deploy.sh                    # 前端 CDN 部署（GitHub raw 拉取）
│   ├── deploy-backend.sh            # 后端 ECS 部署
│   └── healthcheck.sh               # 链路健康检查（464行）
│
├── ops/                             # 运维
│   ├── monitor_sources.py           # 数据源监控
│   └── production/                  # 生产运维脚本 + systemd
│
├── docs/                            # 文档
│
├── .env
├── requirements.txt
├── pytest.ini
└── README.md
```

---

## 四、分层职责与依赖规则

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│   frontend/          纯静态资源，不依赖任何 Python 代码           │
│   (HTML/JS/CSS)      通过 Nginx 直接服务                         │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│   app/               HTTP 入口，只做请求转发                      │
│   (api/admin/pages)  依赖 → engine, models, auth                 │
│                      禁止 → 直接调用 AkShare/Tavily              │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│   engine/            核心引擎，场景无关的通用逻辑                  │
│   (pipeline/quality/ 依赖 → scenarios(配置), providers(数据)      │
│    llm/providers)    禁止 → 依赖 app/, frontend/                 │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│   scenarios/         场景定义，纯配置 + 文本                      │
│   (yaml/md)          零 Python 代码，非程序员可编辑               │
│                      被 engine/ 读取                            │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│   mcp_server.py      瘦适配器                                    │
│                      依赖 → engine/ (与 app/ 平级)              │
│                      禁止 → 自己实现数据获取逻辑                  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘

依赖方向:  frontend → app/ → engine/ → scenarios/
                              ↓
                          providers/ (数据)
```

---

## 五、引擎管线设计

### 5.1 pipeline.py — 核心编排（伪代码）

```python
class AnalysisPipeline:
    """
    核心管线：读取场景配置 → 采集数据 → 质量检查 → LLM 分析 → 后处理
    这段代码是稳定的，新增场景不需要修改。
    """

    async def run(self, scenario: ScenarioConfig, query: str, extra: str = "") -> dict:

        # ── Step 1: 数据采集 ──
        provider_results = {}
        for provider_cfg in scenario.providers:
            provider = ProviderRegistry.get(provider_cfg.type)
            provider_results[provider_cfg.type] = await provider.fetch(
                query=query,
                config=provider_cfg.config,
            )

        # 合并数据为文本
        search_results_text = self._merge_provider_outputs(provider_results)
        sources = self._extract_sources(provider_results)
        has_structured = self._has_structured_data(provider_results)

        # ── Step 2: 质量检查（数据阶段）──
        qc_result = QualityGate.check_data(
            scenario=scenario,
            provider_results=provider_results,
            has_structured=has_structured,
            source_count=len(sources),
        )
        if qc_result.blocked:
            return self._insufficient_data_response(qc_result)

        # ── Step 3: LLM 分析 ──
        prompt = PromptLoader.load(scenario.name)  # 从 prompt.md 读取
        if scenario.skip_llm:
            result = search_results_text  # 直接用数据（如竞价 QC 不通过时）
        else:
            result = await LLMClient.generate(
                system_prompt=prompt,
                user_content=f"用户查询：{query}\n\n参考资料：\n{search_results_text}",
            )

        # ── Step 4: 后处理 ──
        result = self._sanitize(result, sources)
        trust = self._build_trust_contract(provider_results)
        publication = self._check_publication_safety(result, scenario)

        return {
            "success": True,
            "result": result,
            "sources": sources,
            "_qc": qc_result.to_dict(),
            "trust": trust,
            "publication": publication,
        }
```

### 5.2 Provider 基类 — 可插拔数据源

```python
class BaseProvider(ABC):
    """所有数据源的基类。新增数据源只需继承并实现 fetch()。"""

    @abstractmethod
    async def fetch(self, query: str, config: dict) -> ProviderResult:
        """
        获取数据。
        返回 ProviderResult(text: str, sources: list, has_structured: bool)
        """
        ...

    def validate(self, result: ProviderResult) -> QCResult:
        """数据质量自检（可选覆盖）。"""
        return QCResult(passed=True)


class AkShareStockProvider(BaseProvider):
    """股票数据：K线+财报+资金+新闻+分红"""
    async def fetch(self, query, config):
        include = config.get("include", ["kline", "financials", "fund_flow", "news"])
        # ... 并发调用 akshare 接口 ...
        return ProviderResult(text=formatted, sources=sources, has_structured=True)


class SearchProvider(BaseProvider):
    """搜索引擎：Tavily + Brave，多策略"""
    async def fetch(self, query, config):
        strategy = config.get("strategy", "general")
        # ... 按策略调用 tavily/brave ...
        return ProviderResult(text=formatted, sources=sources, has_structured=False)


class VideoProvider(BaseProvider):
    """视频字幕：YouTube/B站"""
    ...


class UserInputProvider(BaseProvider):
    """用户直接输入（会议纪要/麦肯锡报告）"""
    async def fetch(self, query, config):
        return ProviderResult(text=query, sources=[], has_structured=False)
```

### 5.3 场景加载 — 从目录自动发现

```python
class ScenarioRegistry:
    """自动扫描 scenarios/ 目录，加载所有场景配置。"""

    def __init__(self, scenarios_dir: Path):
        self.scenarios = {}
        for scenario_dir in scenarios_dir.iterdir():
            if scenario_dir.is_dir() and (scenario_dir / "config.yaml").exists():
                config = yaml.safe_load((scenario_dir / "config.yaml").read_text())
                prompt = (scenario_dir / "prompt.md").read_text()
                qc_rules = yaml.safe_load((scenario_dir / "qc_rules.yaml").read_text())
                self.scenarios[scenario_dir.name] = ScenarioConfig(
                    name=scenario_dir.name,
                    config=config,
                    prompt=prompt,
                    qc_rules=qc_rules,
                )

    def get(self, name: str) -> ScenarioConfig | None:
        return self.scenarios.get(name)

    def list(self) -> list[dict]:
        return [{"name": k, **v.config} for k, v in self.scenarios.items()]
```

**新增场景的完整流程：**

```bash
# 1. 复制现有场景
cp -r scenarios/stock scenarios/fund_analysis

# 2. 修改配置
vim scenarios/fund_analysis/config.yaml    # 改数据源
vim scenarios/fund_analysis/prompt.md      # 改写作模板
vim scenarios/fund_analysis/qc_rules.yaml  # 改质检规则

# 3. 如果需要新数据源，写一个 Provider
vim engine/providers/akshare_fund_provider.py

# 4. 在 config.yaml 里声明使用新 Provider
# providers:
#   - type: akshare_fund    ← 自动注册

# 完成。引擎代码零修改。
```

---

## 六、用户 API vs 管理 API 分离

### 6.1 用户 API（app/api/）— 面向终端用户

```
POST /api/analyze              # 分析（核心功能）
GET  /api/intel/*              # 市场情报
GET  /api/watchlist/*          # 自选股
POST /api/export-pdf           # PDF 导出
POST /api/register             # 注册
POST /api/login                # 登录
GET  /api/check-auth           # 检查登录状态
GET  /api/usage                # 查询用量
```

特点：
- 需要 JWT 认证
- 受用量限制（free=3次/天）
- 只读/分析操作
- 响应速度优先

### 6.2 管理 API（app/admin/）— 面向管理员

```
# ── 场景管理（核心：支持新场景开发）──
GET    /api/admin/scenarios              # 场景列表
POST   /api/admin/scenarios              # 创建新场景
GET    /api/admin/scenarios/{name}       # 场景详情
PUT    /api/admin/scenarios/{name}       # 编辑场景配置
DELETE /api/admin/scenarios/{name}       # 删除场景
POST   /api/admin/scenarios/{name}/test  # 测试运行场景（dry-run）
POST   /api/admin/scenarios/{name}/duplicate  # 复制场景

# ── Provider 管理 ──
GET    /api/admin/providers              # Provider 列表 + 状态
GET    /api/admin/providers/{name}/health # Provider 健康检查

# ── QC 规则管理 ──
GET    /api/admin/quality/rules          # QC 规则列表
PUT    /api/admin/quality/rules          # 更新规则

# ── 用户管理 ──
GET    /api/admin/users                  # 用户列表
PUT    /api/admin/users/{id}/tier        # 修改用户等级
DELETE /api/admin/users/{id}             # 禁用用户

# ── 系统监控 ──
GET    /api/admin/system/health          # 系统健康
GET    /api/admin/system/logs            # 日志查看
GET    /api/admin/system/providers       # 数据源状态面板
```

特点：
- 需要 admin 角色
- 不受用量限制
- 可写操作（创建/编辑/删除）
- 支持场景开发全流程

### 6.3 管理后台前端

```
templates/admin/
├── base.html            # 管理后台基础模板（侧栏+顶栏）
├── dashboard.html       # 管理首页（概览：用户数/分析次数/Provider状态）
├── scenarios.html       # 场景列表（卡片式，显示状态/用量/最后运行时间）
├── scenario_edit.html   # 场景编辑器
│   ├── 左侧：config.yaml 编辑器（YAML 高亮）
│   ├── 中间：prompt.md 编辑器（Markdown 预览）
│   ├── 右侧：qc_rules.yaml 编辑器
│   └── 底部：测试运行按钮 → 实时显示结果
├── users.html           # 用户管理表格
└── system.html          # 系统监控面板
```

---

## 七、迁移路径

### Phase 1：清理 + 分层（1-2天，零风险）

```
1. 删除死代码 (~4500行)
   - 删除 server_scripts/ 全部
   - 删除 scripts/ 中与 app/ 重复的文件
   - 删除 scripts/ 中零引用的文件
   - 删除根目录重复的 index.html

2. 前端资源迁移
   场景页面 → 跟随场景进入 scenarios/
   - app/stock.html   → scenarios/stock/page.html
   - app/macro.html   → scenarios/macro/page.html
   - app/auction.html → scenarios/auction/page.html
   - app/video.html   → scenarios/video/page.html
   - app/meeting.html → scenarios/meeting/page.html
   - app/deep-research.html → scenarios/industry/page.html

   平台级页面 → frontend/
   - app/index.html → frontend/pages/index.html
   - app/xueqiu-hot.html → frontend/pages/xueqiu-hot.html
   - app/market-snapshot.html → frontend/pages/market-snapshot.html
   - app/*.js → frontend/scripts/ 或 frontend/shared/
   - app/*.css → frontend/styles/
   - app/marked.min.js → frontend/lib/

3. 更新 deploy.sh 和 nginx 配置中的路径
```

### Phase 2：引擎抽取（2-3天，需测试验证）

```
1. 创建 engine/ 目录
   - 从 analyze_service.py 抽取 pipeline.py
   - 从 stock_data.py/macro_data.py 等抽取 providers/
   - 从 report_qc.py/event_facts.py 抽取 quality/
   - 从 llm.py 抽取 llm/client.py

2. 创建 scenarios/ 目录
   - 从 skills.py 拆出 7 个场景目录
   - 每个目录包含 config.yaml + prompt.md + qc_rules.yaml + page.html

3. 改造 analyze_service.py → 调用 engine/pipeline.py
   - 删除 if-elif 分支
   - 改为读取 ScenarioRegistry
```

### Phase 3：管理功能（2-3天，新功能）

```
1. 创建 app/admin/ 路由
   - 场景 CRUD API
   - 用户管理 API
   - 系统监控 API

2. 创建管理后台模板
   - templates/admin/*.html

3. 场景测试运行功能
   - POST /api/admin/scenarios/{name}/test
   - 输入测试查询 → 调用 pipeline → 返回结果（不计用量）
```

### Phase 4：MCP Server 重构（2天）

MCP Server 不是 Web 应用的附属品，而是一条独立产品线。
它面向 AI Agent（Claude Code / OpenClaw 等），提供 15 个工具，
能力范围远大于 Web 应用的 7 个分析场景。

```
MCP Server 工具清单（15 个）：

┌─ 分析工具（复用 engine/，与 Web 共享）──────────────┐
│  stock_analysis    个股全维度数据                    │
│  macro_snapshot    宏观经济数据                      │
│  market_pulse      集合竞价盘面数据                  │
│  search            多源搜索                          │
│  video_extract     视频字幕提取                      │
└──────────────────────────────────────────────────────┘

┌─ MCP 独有数据源（Web 应用不使用的）──────────────────┐
│  wind_query        Wind 万得（多源降级到 Tushare/JQ）  │
│  jqdata_query      JQData 聚宽数据                   │
│  ths_query         同花顺 iFinD                      │
│  emquant_query     东方财富 Choice                    │
│  xueqiu_fetch      雪球（autocli 抓包）              │
│  zhihu_fetch       知乎（autocli 抓包）              │
│  sinafinance_fetch 新浪财经 7x24 快讯                │
│  barchart_fetch    Barchart 期权数据                  │
└──────────────────────────────────────────────────────┘

┌─ 业务工具（MCP 独有）───────────────────────────────┐
│  watchlist_manage  自选股管理（增删改查/监控）         │
│  factor_scan       量化因子选股扫描                  │
│  research_reports  投行研报链接管理                  │
│  research_digest   A股卖方研报脱水                   │
│  market_intel      市场情报聚合                      │
└──────────────────────────────────────────────────────┘

重构策略：
1. 分析工具 → 瘦身为调用 engine/pipeline.py
2. MCP 独有数据源 → 迁入 mcp/providers/（独立维护）
3. 业务工具 → 迁入 mcp/tools/（独立维护）
4. 1887 行单文件 → 拆分为 mcp/ 目录（模块化）
```

---

## 八、重构前后对比

```
重构前:                                    重构后:

app/                                       engine/          ← 稳定引擎
├── stock_data.py    ← 数据+业务混杂      ├── pipeline.py   ← 统一管线
├── macro_data.py                          ├── providers/    ← 可插拔数据源
├── auction_data.py                        ├── quality/      ← 统一QC
├── search.py                              └── llm/          ← LLM封装
├── skills.py        ← 640行混杂
├── services/        ← 部分业务            scenarios/       ← 场景定义（含前端）
│   ├── analyze_service.py                 ├── stock/        ← 复制即新增
│   ├── report_qc.py                       │   ├── config.yaml
│   └── event_facts.py                     │   ├── prompt.md
├── routers/                               │   ├── qc_rules.yaml
│   ├── api.py                             │   └── page.html  ← 前端跟场景走
│   ├── intel.py                           ├── macro/
│   └── watchlist.py                       └── ...
├── *.html           ← 前端混在Python里
├── *.js                                   app/             ← 后端应用
└── *.css                                  ├── api/          ← 用户API
                                         ├── admin/        ← 管理API
scripts/             ← 重复/死代码         ├── auth/         ← 认证模块
server_scripts/      ← Flask遗留         └── models/       ← 数据模型
mcp_server.py        ← 1887行单文件       frontend/        ← 平台级前端
                                         ├── pages/        ← 非场景HTML
                                         ├── shared/       ← 共享组件
                                         └── styles/       ← CSS

                                         templates/       ← 服务端模板
                                         mcp/             ← MCP 独立产品线
                                         ├── server.py     ← 瘦入口
                                         ├── tools/        ← 18个工具
                                         └── providers/    ← MCP独有数据源

                                         deploy/          ← 部署脚本
                                         ops/             ← 运维脚本
```

| 指标 | 重构前 | 重构后 |
|------|--------|--------|
| 新增场景改动文件数 | 3-5 个核心文件 | 1 个新目录（4个文件，含前端） |
| 引擎代码改动频率 | 每次新增场景都改 | 几乎不改 |
| 前后端分离 | ❌ 混杂 | ✅ 完全分离 |
| 场景前端归属 | ❌ 散落在 app/ | ✅ 跟随场景目录 |
| 死代码 | ~4500 行 | 0 |
| 管理后台 | ❌ 无 | ✅ 场景开发/测试/用户管理 |
| MCP Server | ❌ 1887行单文件 | ✅ 模块化，18个工具分类，分析工具复用引擎 |
| 非程序员可新增场景 | ❌ 需要改 Python | ✅ 编辑 YAML + Markdown + HTML |

---

## 九、功能覆盖审计

### 9.1 API 端点覆盖（28 个）

| 类别 | 端点 | 重构后归属 |
|------|------|-----------|
| 健康检查 | `GET /api/health` | `app/main.py` |
| 分析 | `POST /api/analyze` | `app/api/analyze.py` |
| 认证 | `POST /api/register, /api/login, /api/logout` | `app/api/auth.py` |
| 认证 | `GET /api/check-auth, /api/usage` | `app/api/auth.py` |
| 认证 | `POST /api/auth/refresh, /api/auth/cookie-fix` | `app/api/auth.py` |
| 导出 | `POST /api/export-pdf` | `app/api/export.py` |
| 情报 | `GET /api/intel/*` (9个端点) | `app/api/intel.py` |
| 自选股 | `GET/POST /api/watchlist/*` (3个) | `app/api/watchlist.py` |
| 管理 | `GET /api/admin/users, /api/admin/stats` | `app/admin/users.py` + `system.py` |
| 管理 | `POST /api/admin/upgrade` | `app/admin/users.py` |
| 页面 | `GET /, /login, /register, /dashboard` | `app/pages/routes.py` |
| 页面 | `GET /skill/{type}, /pricing, /admin` | `app/pages/routes.py` |
| 全局 | `@app.exception_handler(401)` | `app/main.py` |
| 全局 | `StaticFiles mount /static` | `app/main.py` |
| 全局 | `lifespan()` DB init + admin + 缓存预热 | `app/main.py` |

### 9.2 MCP 工具覆盖（18 个）

| 类别 | 工具 | 重构后归属 |
|------|------|-----------|
| 分析(复用engine) | `stock_analysis` | `mcp/tools/analysis.py` |
| 分析(复用engine) | `macro_snapshot` | `mcp/tools/analysis.py` |
| 分析(复用engine) | `market_pulse` | `mcp/tools/analysis.py` |
| 分析(复用engine) | `search` | `mcp/tools/search.py` |
| 分析(复用engine) | `video_extract` | `mcp/tools/video.py` |
| MCP独有数据源 | `wind_query` | `mcp/tools/` + `mcp/providers/wind_provider.py` |
| MCP独有数据源 | `jqdata_query` | `mcp/tools/` + `mcp/providers/jqdata_provider.py` |
| MCP独有数据源 | `ths_query` | `mcp/tools/` + `mcp/providers/ths_provider.py` |
| MCP独有数据源 | `emquant_query` | `mcp/tools/` + `mcp/providers/emquant_provider.py` |
| MCP独有数据源 | `xueqiu_fetch` | `mcp/tools/` + `mcp/providers/xueqiu_provider.py` |
| MCP独有数据源 | `zhihu_fetch` | `mcp/tools/` + `mcp/providers/zhihu_provider.py` |
| MCP独有数据源 | `sinafinance_fetch` | `mcp/tools/` + `mcp/providers/sinafinance_provider.py` |
| MCP独有数据源 | `barchart_fetch` | `mcp/tools/` + `mcp/providers/barchart_provider.py` |
| 业务工具 | `watchlist_manage` | `mcp/tools/watchlist.py` |
| 业务工具 | `factor_scan` | `mcp/tools/factor.py` |
| 业务工具 | `research_reports` | `mcp/tools/research.py` |
| 业务工具 | `research_digest` | `mcp/tools/research.py` |
| 业务工具 | `market_intel` | `mcp/tools/market_intel.py` |

### 9.3 前端页面覆盖（15 HTML + 7 JS + 1 CSS）

| 文件 | 重构后归属 |
|------|-----------|
| stock.html | `scenarios/stock/page.html` |
| macro.html | `scenarios/macro/page.html` |
| auction.html | `scenarios/auction/page.html` |
| video.html | `scenarios/video/page.html` |
| meeting.html | `scenarios/meeting/page.html` |
| deep-research.html | `scenarios/industry/page.html` |
| index.html | `frontend/pages/index.html` |
| xueqiu-hot.html | `frontend/pages/xueqiu-hot.html` |
| market-snapshot.html | `frontend/pages/market-snapshot.html` |
| market-context.html | `frontend/pages/market-context.html` |
| market-temperature-mini.html | `frontend/pages/market-temperature-mini.html` |
| weekly-recap.html | `frontend/pages/weekly-recap.html` |
| workbench-config.html | `frontend/pages/workbench-config.html` |
| d13_close_brief.html | `frontend/pages/d13_close_brief.html` |
| d13_midday_pulse.html | `frontend/pages/d13_midday_pulse.html` |
| 7 JS + 1 CSS | `frontend/shared/` + `frontend/scripts/` + `frontend/styles/` |

### 9.4 服务层函数覆盖（23 个核心函数）

| 原始模块 | 重构后归属 | 状态 |
|---------|-----------|------|
| analyze_service.py (9个函数) | `engine/pipeline.py` + `engine/providers/*` | ✅ |
| report_qc.py (9个函数) | `engine/quality/gate.py` + `publication.py` | ✅ |
| event_facts.py (5个函数) | `engine/quality/event_facts.py` | ✅ |
| quality_gate/core.py (3个类) | `engine/quality/gate.py` + `rules.py` | ✅ |
| llm.py (4个函数) | `engine/llm/client.py` + `engine/cache.py` | ✅ |

### 9.5 scripts/ 去重策略

scripts/ 目录有 4 个文件与 app/ 同名重复，且被 mcp_server.py import：

| 重复文件 | 被谁 import | 去重策略 |
|---------|-----------|----------|
| `scripts/stock_data.py` | mcp_server.py | 统一为 `engine/providers/akshare_provider.py`，MCP 调用 engine/ |
| `scripts/macro_data.py` | mcp_server.py | 同上 |
| `scripts/auction_data.py` | mcp_server.py | 同上 |
| `scripts/video_data.py` | mcp_server.py | 同上 |

**原则：scripts/ 重复文件全部删除，MCP Server 统一调用 engine/ 层。**

scripts/ 中被 MCP 独有引用的文件迁移到 `mcp/providers/`：

| 文件 | 迁移目标 |
|------|----------|
| `scripts/wind_data.py` | `mcp/providers/wind_provider.py` |
| `scripts/tushare_data.py` | `mcp/providers/tushare_provider.py` |
| `scripts/ifind_data.py` | `mcp/providers/ths_provider.py` |
| `scripts/emquant_data.py` | `mcp/providers/emquant_provider.py` |
| `scripts/factor_scan.py` | `mcp/tools/factor.py` |
| `scripts/watchlist.py` | `mcp/tools/watchlist.py` |

### 9.6 服务器端外部模块（需纳入版本控制）

以下模块仅存在于生产服务器，不在 repo 中，是重大风险点：

| 模块 | 被谁 import | 处理策略 |
|------|-----------|----------|
| `news_providers` | mcp search 工具 | 纳入 `mcp/providers/` 或 `engine/providers/` |
| `research_reports` | mcp research 工具 | 纳入 `mcp/tools/research.py` |
| `research_digest` | mcp research 工具 | 纳入 `mcp/tools/research.py` |
| `market_intel` | mcp market_intel 工具 | 纳入 `mcp/tools/market_intel.py` |
| `joinquant_data` | factor_scan / wind_query | 纳入 `mcp/providers/jqdata_provider.py` |
| `jqdata_fetch` | jqdata_query / stock_analysis | 纳入 `mcp/providers/jqdata_provider.py` |
| `trust_gate.enforcer` | mcp_server.py 顶层 | 纳入 `mcp/trust_gate.py` |

### 9.7 部署脚本迁移

| 脚本 | 当前路径 | 重构后路径 | 需更新内容 |
|------|---------|-----------|----------|
| `deploy.sh` | 根目录 | `deploy/deploy.sh` | GitHub raw 拉取路径全部更新（app/*.html → scenarios/*/page.html + frontend/pages/） |
| `deploy-backend.sh` | 根目录 | `deploy/deploy-backend.sh` | 无路径变化，仅移动位置 |
| `healthcheck.sh` | 根目录 | `deploy/healthcheck.sh` | 无路径变化，仅移动位置 |
| `serve_local.py` | 根目录 | 根目录保留 | 静态文件路径更新 |

### 9.8 待清理文件

| 文件 | 处理 |
|------|------|
| `templates/login-test.html` | ❌ 删除（测试遗留） |
| `app/weekly-recap-latest.json` | → `data/weekly-recap-latest.json` |
| `index.html`（根目录） | 与 `templates/index.html` 重复，确认后删除一个 |
| `database.py` CC Phase 1 pool instrumentation | 清理观测代码，保留核心 |
