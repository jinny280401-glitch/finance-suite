# Finance Suite 系统分析报告

> 生成日期：2026-09-05 | 最后更新：2026-09-05（重构后架构更新）  
> 基于生产代码逐行审计 + 完整重构执行验证

---

## 一、系统底层逻辑

### 1.1 一句话概括

**这套系统本质上就是一个"喂数据给 AI 写报告"的机器。**

核心逻辑极其简单：

```
        数据进来          喂给 AI          报告出去
        ────────→    ┌──────────┐    ────────→
        各种渠道       │  通义千问  │      Markdown
        AkShare       │  (LLM)   │      分析报告
        Tavily        │          │
        Brave         └──────────┘
```

**LLM 是引擎，数据是燃料，Prompt 是模具。** 换一套数据 + 换一个 Prompt 模板 = 换一个分析场景。

### 1.2 三件事流水线

整个系统只做三件事：

```
   用户输入
     │
     ▼
   ┌──────────┐
   │ 1. 找数据 │  AkShare + 搜索引擎
   │  (采集)   │  不同场景找不同的数据组合
   └────┬─────┘
        │ 一堆文本
        ▼
   ┌──────────┐
   │ 2. 写报告 │  LLM + Prompt 模板
   │  (分析)   │  不同场景换不同模板
   └────┬─────┘
        │ Markdown 报告
        ▼
   ┌──────────┐
   │ 3. 查质量 │  QC + Trust + 发布控制
   │  (质检)   │  拦截幻觉/冲突/违规
   └────┬─────┘
        │
        ▼
   返回用户

   新增场景 = 换数据 + 换模板 + 换质检规则，框架本身不用动
```

### 1.3 找数据的两个渠道

| 渠道 | 干什么用 | 类比 |
|------|---------|------|
| **AkShare**（东方财富数据） | 拿到精确的行情、财报、资金流等**结构化数字** | 查账本 |
| **Tavily/Brave**（搜索引擎） | 拿到新闻、分析、讨论等**文字信息** | 看报纸 |

不同场景，找不同的数据组合：
- **看票** → 查账本（K线/财报/资金）+ 看报纸（5个维度搜）
- **宏观** → 查账本（GDP/CPI/PMI）+ 看报纸（限定官方源）
- **竞价** → 查账本（涨停池/异动）+ 不搜报纸
- **视频** → 提字幕 + 看报纸（补充背景）
- **会议纪要** → 啥也不找，用户自己贴进来

### 1.4 写报告的原理

数据找齐了，拼成一段长文本，连同一套 Prompt 模板，一起发给通义千问：

```
系统指令（Prompt 模板）：
  "你是一个股票分析师，按以下结构写报告：
   一、核心结论...  二、财报分析...  三、估值..."

用户输入：
  "用户查询：贵州茅台

   以下是搜索到的参考资料：
   === 贵州茅台(600519) 东方财富结构化数据 ===
   【实时行情】最新价：1450元...
   【财报指标】营收：834亿...

   === 搜索引擎补充 ===
   【来源1】茅台2026年中报... "

→ AI 输出一份 4000 字的 Markdown 分析报告
```

**不同的分析场景 = 不同的 Prompt 模板。** 代码里 `skills.py` 那 640 行，本质上就是 7 套"写作模板"。

### 1.5 查质量的四层关卡

AI 写完的报告不能直接给用户，因为 AI 会"编"：

```
AI 报告
  │
  ├─ 第1层：数据够不够？ → 不够就返回"资料不足"
  │
  ├─ 第2层：信源对不对得上？ → 搜了3条新闻，报告引用了几条？
  │
  ├─ 第3层：有没有幻觉？ → 没结构化数据+信源少 = 高风险
  │
  ├─ 第4层：宏观一致性 → AI说"未证实"但官方已确认？拦截！
  │
  └─ 第5层：发布安全 → 报告里有没有写"目标价XX元"？标记！
```

---

## 二、业务功能架构

### 2.1 产品定位

**天玑 (Finance Suite)** — 面向个人投资者的金融数据分析平台，提供 AI 驱动的多维度分析报告。

- 域名：`touziagent.com` (www + api 双子域)
- 用户体系：免费层 (3次/天) + VIP (无限) + 管理员

### 2.2 功能模块总览

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Finance Suite 业务架构                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │
│  │  用户中心    │  │  分析引擎    │  │  市场情报    │                │
│  │             │  │             │  │             │                │
│  │ • 注册/登录  │  │ • 股票深度   │  │ • 雪球热门   │                │
│  │ • JWT 认证   │  │ • 宏观内参   │  │ • 热门讨论   │                │
│  │ • 用量管理   │  │ • 竞价分析   │  │ • 热股排行   │                │
│  │ • 分级权限   │  │ • 视频解读   │  │ • 自选异动   │                │
│  │             │  │ • 行业研报   │  │ • 脱水研报   │                │
│  │             │  │ • 会议纪要   │  │ • 黄金坑扫描  │                │
│  │             │  │ • 麦肯锡报告  │  │ • 市场画像   │                │
│  └─────────────┘  └─────────────┘  └─────────────┘                │
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │
│  │  自选股管理  │  │  报告导出    │  │  管理后台    │                │
│  │ • 添加/删除  │  │ • PDF 导出   │  │ • 用户管理   │                │
│  │ • 股票列表   │  │ • HTML 清理  │  │ • 系统监控   │                │
│  └─────────────┘  └─────────────┘  └─────────────┘                │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    MCP Server (AI Agent 接口)                │   │
│  │  • 股票分析工具    • 宏观分析工具    • 搜索工具              │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.3 技能定义矩阵

| 技能 | 名称 | 数据源 | Prompt 模板 | 输出 |
|------|------|--------|------------|------|
| stock | 看票分析 | AkShare 5路 + Tavily 5维度 | 9章节报告 | 深度分析报告 |
| macro | 宏观内参 | AkShare 5路 + Tavily(限定域) + 事件预检 | 4章节模板 | 宏观简报 |
| auction | 集合竞价 | AkShare 6路涨停数据 | 5章节模板 | 盘面速览 |
| industry | 行业报告 | AkShare板块 + Tavily | 6章节模板 | 行业研报 |
| video | 视频拆解 | Supadata/B站字幕 + 搜索补充 | 5章节模板 | 知识拆解 |
| mckinsey | 麦肯锡报告 | 无（用户输入） | 4章节模板 | 咨询报告 |
| meeting | 会议纪要 | 无（用户输入） | 4章节模板 | 结构化纪要 |

---

## 三、技术架构

### 3.1 部署架构

```
                    ┌─────────────────────┐
                    │   Cloudflare CDN    │
                    │  (静态资源加速)       │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │      Nginx          │
                    │  (SSL + 反向代理)    │
                    │                     │
                    │  www.touziagent.com │
                    │  /app/ → 静态HTML    │
                    │  /static/ → 文件    │
                    │  /api/ → FastAPI    │
                    │                     │
                    │  api.touziagent.com │
                    │  / → FastAPI (CORS) │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Uvicorn (4 worker) │
                    │   FastAPI App        │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
    ┌─────────▼─────┐  ┌──────▼──────┐  ┌──────▼──────┐
    │   SQLite DB   │  │  LLM API    │  │ Search APIs │
    │  (用户/用量)   │  │  (Qwen)     │  │ Tavily/Brave│
    └───────────────┘  └─────────────┘  └─────────────┘
```

### 3.2 技术栈

| 层次 | 技术 | 说明 |
|------|------|------|
| Web 框架 | FastAPI + Uvicorn | 异步 HTTP，4 worker |
| 模板引擎 | Jinja2 | 服务端渲染登录/注册/管理页 |
| 数据库 | SQLite + SQLAlchemy | 用户/用量/自选股持久化 |
| 认证 | JWT (Bearer + Cookie) | 24h 过期，分级权限 |
| LLM | 阿里通义千问 (qwen-plus) | DashScope API |
| 搜索 | Tavily (10 Key) + Brave (3 Key) | 多 Key 轮询 |
| 行情数据 | AkShare | 底层数据源全部来自东方财富 |
| 视频字幕 | Supadata (YouTube) + B站 API | 多语言字幕提取 |
| 前端 | 纯 HTML + Vanilla JS | 无框架，内联脚本 |
| AI Agent | MCP Server | Model Context Protocol |

### 3.3 外部系统对接

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              外 部 系 统                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐     │
│  │ 阿里通义千问       │  │ Tavily Search    │  │ Brave Search     │     │
│  │ (Qwen LLM)       │  │ (10 Key 轮询)     │  │ (3 Key 轮询)     │     │
│  │ dashscope API    │  │ api.tavily.com   │  │ api.search.brave │     │
│  │ qwen-plus 模型   │  │ /search /extract │  │ .com /web /news  │     │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘     │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                AkShare (Python SDK → 东方财富)                  │    │
│  │                                                                │    │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐  │    │
│  │  │ 股票行情类      │  │ 涨停/竞价类     │  │ 宏观经济类      │  │    │
│  │  │ stock_zh_a_hist│  │ stock_zt_pool  │  │ macro_china_gdp│  │    │
│  │  │ stock_financial│  │ stock_zt_pool  │  │ macro_china_cpi│  │    │
│  │  │ stock_fund_flow│  │ _strong_em     │  │ macro_china_pmi│  │    │
│  │  │ stock_news_em  │  │ stock_zt_pool  │  │ macro_china    │  │    │
│  │  │ stock_history  │  │ _previous_em   │  │ _money_supply  │  │    │
│  │  │ _dividend      │  │ stock_changes  │  │ macro_china_lpr│  │    │
│  │  │ stock_zh_a_spot│  │ stock_hot_rank │  │ rate_interbank │  │    │
│  │  │ stock_board    │  │ stock_hot_up   │  │                │  │    │
│  │  └────────────────┘  └────────────────┘  └────────────────┘  │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌──────────────────┐  ┌──────────────────┐                           │
│  │ Supadata API      │  │ B站 API          │                           │
│  │ (YouTube字幕)     │  │ (B站视频信息)     │                           │
│  └──────────────────┘  └──────────────────┘                           │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.4 内部存储/缓存

| 存储 | 类型 | 用途 | 读写方式 |
|------|------|------|---------|
| `finance_suite.db` | SQLite | users 表 + usages 表 | SQLAlchemy ORM |
| `watchlist.json` | JSON 文件 | 自选股列表 | 直接文件读写 |
| TTLCache (内存) | 内存缓存 | 分析结果缓存，50条/10min | cachetools 库 |
| `_stock_cache` (内存) | 内存缓存 | 全市场行情快照，2h刷新 | 启动时加载 |
| `fetch_receipts.jsonl` | JSONL 日志 | 每次AkShare调用记录 | 追加写入 |
| `pool_instrument.log` | 文本日志 | DB连接池事件 | 追加写入 |

---

## 四、完整数据流程图

### 4.1 主分析流程 — POST /api/analyze

```
用户请求
  │
  │  POST /api/analyze
  │  Body: { skill_type, query, extra_content? }
  │  Header: Authorization: Bearer <JWT>
  │
  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  ROUTER 层  (routers/api.py)                                           │
│                                                                         │
│  ① normalize_skill_type(skill_type)                                     │
│     "deep-research" → "industry"                                        │
│                                                                         │
│  ② get_skill(skill_type) → SKILLS[type]                                │
│     不存在 → 400 "未知的分析技能"                                         │
│                                                                         │
│  ③ check_usage_allowed(db, user_id, tier)                               │
│     ┌──────────────────────────────────────────────┐                   │
│     │ READ  finance_suite.db → usages 表            │                   │
│     │ tier=free: limit=3,  used≥3 → 429 拒绝       │                   │
│     │ tier=vip:  limit=None → 始终放行              │                   │
│     └──────────────────────────────────────────────┘                   │
│                                                                         │
│  ④ get_cached_result(skill_type, query)                                │
│     ┌──────────────────────────────────────────────┐                   │
│     │ READ  TTLCache (内存)                         │                   │
│     │ 命中 → 直接返回 (跳过数据采集+LLM)             │                   │
│     │ 注: macro/auction 不缓存                      │                   │
│     └──────────────────────────────────────────────┘                   │
│                                                                         │
│  ⑤ run_analysis(skill_type, query, extra_content)                      │
│     → 进入 SERVICE 层                                                   │
│                                                                         │
│  ⑥ WRITE  finance_suite.db → usages 表 (记录用量)                      │
│                                                                         │
│  ⑦ 返回 JSON response                                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.2 数据采集分支 — 按 skill_type 路由

```
run_analysis() 内部
  │
  ├─── skill_type == "stock" ──────────────────────────────────────────────┐
  │                                                                        │
  │   Step 1: 股票解析 resolve_stock_detail(query)                        │
  │   ┌────────────────────────────────────────────────────────────┐      │
  │   │ 优先级:                                                     │      │
  │   │ 1. QUICK_MAP 硬编码 (40+ 常见股票名/代码)                   │      │
  │   │ 2. _stock_cache 内存缓存 → 精确匹配 → 模糊匹配             │      │
  │   │ 3. 都匹配不上 → None (用原始输入搜索)                       │      │
  │   │ 输出: {code, name, resolver_source}                        │      │
  │   └────────────────────────────────────────────────────────────┘      │
  │                                                                        │
  │   Step 2: 并发数据采集 (asyncio.gather)                               │
  │   ┌────────────────────────────────────────────────────────────┐      │
  │   │  AkShare (线程池, 5路并发)          │  Tavily                │      │
  │   │  ┌─ stock_zh_a_hist → K线30日       │  multi_search_stock    │      │
  │   │  ├─ stock_financial_analysis → 财报  │  5维度并发:            │      │
  │   │  ├─ stock_individual_fund_flow       │  ① 财报(中文源域名)    │      │
  │   │  ├─ stock_news_em → 新闻8条          │  ② 资金面              │      │
  │   │  └─ stock_history_dividend → 分红    │  ③ 估值对比            │      │
  │   │  + realtime: 从_stock_cache取        │  ④ 新闻(Brave News)    │      │
  │   │                                      │  ⑤ 管理层/分红         │      │
  │   └────────────────────────────────────────────────────────────┘      │
  │                                                                        │
  │   输出: {search_results_text, sources[], kline_data[],                │
  │          has_structured=True, final_dispatch_trace}                   │
  │                                                                        │
  ├─── skill_type == "macro" ──────────────────────────────────────────────┐
  │                                                                        │
  │   并发数据采集 (asyncio.gather, 3路)                                  │
  │   ┌────────────────────────────────────────────────────────────┐      │
  │   │  AkShare (线程池)                   │  Tavily               │      │
  │   │  ┌─ macro_china_gdp → 最近8期       │  unified_search       │      │
  │   │  ├─ macro_china_cpi → 最近12期      │  search_type="news"   │      │
  │   │  ├─ macro_china_pmi → 最近12期      │  +                    │      │
  │   │  ├─ macro_china_money_supply → M2   │  fetch_macro_event    │      │
  │   │  └─ macro_china_lpr → LPR利率       │  _facts(query)        │      │
  │   │  数据源: 国家统计局/央行              │  (事件事实预检)        │      │
  │   └────────────────────────────────────────────────────────────┘      │
  │                                                                        │
  │   输出: {search_results_text, sources[], macro_event_facts,           │
  │          has_structured=bool}                                         │
  │                                                                        │
  ├─── skill_type == "auction" ────────────────────────────────────────────┐
  │                                                                        │
  │   时间窗口判定 market_phase()                                          │
  │   ┌────────────────────────────────────────────────────────────┐      │
  │   │ pre_open / auction_in_progress / auction_complete          │      │
  │   │ morning_session / lunch_break / afternoon_session          │      │
  │   │ closing_auction / post_market / non_trading_day            │      │
  │   └────────────────────────────────────────────────────────────┘      │
  │                                                                        │
  │   AkShare 并发采集                                                    │
  │   ┌────────────────────────────────────────────────────────────┐      │
  │   │  ┌─ stock_zt_pool_em → 涨停池(封板资金/连板数)              │      │
  │   │  ├─ stock_zt_pool_strong_em → 强势股池                      │      │
  │   │  ├─ stock_zt_pool_previous_em → 昨日涨停今日表现            │      │
  │   │  ├─ stock_changes_em → 异动(大笔买入/封涨停/破涨停)         │      │
  │   │  ├─ stock_hot_rank_em → 人气排行                           │      │
  │   │  └─ stock_hot_up_em → 连续上涨                             │      │
  │   │  内置 QC: AuctionDataQualityError → 可能跳过 LLM           │      │
  │   └────────────────────────────────────────────────────────────┘      │
  │                                                                        │
  │   输出: {search_results_text, auction_skip_llm, has_structured=True}  │
  │                                                                        │
  ├─── skill_type == "industry" ───────────────────────────────────────────┐
  │   AkShare: stock_board_industry_name_em → 匹配行业板块 Top5           │
  │   Tavily: unified_search(type="industry", topic="general")            │
  │   输出: {search_results_text, sources[], has_structured=bool}         │
  │                                                                        │
  ├─── skill_type == "video" ──────────────────────────────────────────────┐
  │   平台检测:                                                            │
  │   ┌────────────────────────────────────────────────────────────┐      │
  │   │ youtube.com → Supadata API (字幕, zh-Hans→zh→en→auto)     │      │
  │   │              → 失败 fallback: noembed (仅标题+作者)        │      │
  │   │ bilibili.com → B站 API: pagelist → player/v2 → subtitle   │      │
  │   │              → 无字幕: 返回视频标题+UP主(标注 partial)      │      │
  │   │ 其他 URL    → unsupported_platform                        │      │
  │   └────────────────────────────────────────────────────────────┘      │
  │   补充搜索: unified_search(video_url, "news")                         │
  │   输出: {search_results_text, sources[], has_structured=False}        │
  │                                                                        │
  └─── 其他 (mckinsey/meeting) ────────────────────────────────────────────┐
      search_type=None → 不搜索, 仅用用户提供的文本                         │
      输出: {search_results_text="", sources=[], has_structured=False}     │
```

### 4.3 搜索 API 选择逻辑 — unified_search 内部路由

```
unified_search(query, search_type)
  │
  ├── "stock"  → Tavily(topic="finance", 限定中文财经域名)
  │            + Brave News
  │            域名: eastmoney/10jqka/xueqiu/sina/cninfo/cls/caixin/qq
  │
  ├── "macro"  → Tavily(topic="news", 限定官方域名)
  │            + Brave Search (web)
  │            域名: xinhuanet/gov.cn/pbc.gov.cn/ndrc/reuters/bloomberg/wsj
  │
  ├── "industry" → Tavily(topic="general", month)
  │              + Brave Search (web)
  │
  ├── "news"   → Brave News (优先)
  │            → 空则 fallback → Tavily(topic="news")
  │
  ├── "extract" → Tavily Extract API (URL→正文提取)
  │
  └── 全局兜底 (任何类型结果为空):
      Brave Search → Tavily (general)
  去重: 按 URL 去重
  输出: list[{title, url, content}]
```

### 4.4 质量检查 + LLM + 后处理完整管线

```
search_results_text + sources[] + has_structured
  │
  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  质量检查层 (QC)                                                         │
│                                                                         │
│  ① QualityGate (quality_gate/core.py)                                  │
│     触发: skill_type ∈ {stock, macro, industry}                         │
│     检查: completeness ≥ 0.8 + sources ≥ 2 + status ≠ "failure"        │
│     输出: QualityResult{passed, score, reject_reasons}                  │
│                                                                         │
│  ② 宏观事件事实预检 (event_facts.py)                                    │
│     触发: skill_type == "macro"                                         │
│     流程: 优化搜索词 → 新闻搜索 → 逐条判定信源可信度                      │
│           官方源+确认词 → confirmed (0.95)                              │
│           官方源无确认词 → official (0.82)                               │
│           非官方源 → unverified                                         │
│     输出: {confirmed, context, sources[], debug}                        │
│                                                                         │
│  ③ 报告 QC (report_qc.py)                                              │
│     触发: 所有技能                                                      │
│     幻觉风险:                                                           │
│       has_structured=True  + matched≥3 → "low"                         │
│       has_structured=True  + matched<3 → "medium"                      │
│       has_structured=False + matched≥3 → "medium"                      │
│       has_structured=False + matched<3 → "high"                        │
│     输出: {status, hallucination_risk, matched_count}                   │
│                                                                         │
│  关键决策:                                                              │
│  • status=="insufficient_data" 或 risk=="high" → 用安全文本替代          │
│  • auction + skip_llm=True → 直接返回结构化数据速览                      │
└─────────────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  LLM 调用层 (llm.py)                                                    │
│                                                                         │
│  POST {QWEN_API_URL}  model=qwen-plus  temperature=0.5  max_tokens=6000│
│  messages: [system=Prompt模板, user=查询+参考资料]                       │
│  timeout: 180s                                                          │
│  输出: Markdown 报告文本                                                │
└─────────────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  后处理层                                                                │
│                                                                         │
│  ① 宏观一致性冲突检查 (仅 macro)                                        │
│     已确认事件 + 报告含"未证实/假消息" → 拦截!                           │
│                                                                         │
│  ② 报告清理: 删除LLM自写日期行 → 替换为系统生成的 report_as_of          │
│                                                                         │
│  ③ Trust 合约: 添加 data_availability 维度                              │
│     {fundamental, realtime, news, research, market_context}             │
│                                                                         │
│  ④ 发布控制: 检查禁止结论 (DCF目标价/日内买卖信号)                       │
│                                                                         │
│  ⑤ 缓存写入 TTLCache (非 macro/auction)                                │
└─────────────────────────────────────────────────────────────────────────┘
  │
  ▼
最终 JSON 响应:
  { success, result(Markdown), sources[], kline[], report_as_of,
    _qc{status, hallucination_risk, data_availability},
    qa_result{passed, score}, dispatch_trace, event_summary,
    usage_used, usage_limit }
```

### 4.5 市场情报流程 — /api/intel/* (不走 LLM)

```
前端 Sidebar / 情报页面
  │  GET /api/intel/{module}
  │  Header: Authorization: Bearer <JWT>
  │
  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  routers/intel.py — 纯数据层, 不调用 LLM                                │
│                                                                         │
│  /xueqiu-hot     → 雪球 API (requests.get) → 热门讨论列表              │
│  /discussions    → 聚合 xueqiu-hot → 统一契约格式                      │
│  /hot-stocks     → AkShare stock_hot_rank_em → 热股排行                │
│  /golden-pit     → 涨停池 + PE/PB/市值过滤 → 候选标的                  │
│  /market-context → 并发(hot_stocks + news + auction), timeout=10s      │
│  /all            → 四板块聚合 (discussions+hot_stocks+alerts+research) │
│                                                                         │
│  统一 QC 信封: {_qc: {status, sources[], completeness}, data, count}   │
│  失败时: HTTP 200 + _qc.status="failure" (不返回 500)                  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.6 自选股流程 — /api/watchlist/*

```
GET  /list   → READ watchlist.json → 返回 {stocks[], count}
POST /add    → AkShare 解析代码/名称 → READ watchlist.json 查重
             → AkShare 获取 add_price → WRITE watchlist.json 追加
POST /remove → READ watchlist.json → 移除匹配项 → WRITE watchlist.json
```

### 4.7 认证流程

```
注册: POST /api/register
  → READ users表(查重) → WRITE users表(bcrypt密码) → 返回 JWT

登录: POST /api/login
  → READ users表 → bcrypt验证 → 返回 JWT + Set-Cookie

鉴权: 每个 /api/* 请求
  → 解码 JWT(HS256+SECRET_KEY) → READ users表 → 返回 User 对象

用量: GET /api/usage
  → READ usages表(COUNT today) → 返回 {used, limit, tier, allowed}
```

### 4.8 数据源选择决策矩阵

| skill_type | 结构化数据源 (AkShare) | 搜索数据源 | 事件事实预检 | LLM |
|------------|----------------------|-----------|-------------|-----|
| **stock** | K线+财报+资金+新闻+分红 (5路并发) | Tavily×5维度 + Brave News | ✗ | ✅ |
| **macro** | GDP+CPI+PMI+M2+LPR (5路并发) | Tavily(news,限定域) + Brave(web) | ✅ | ✅ |
| **auction** | 涨停池+强势股+昨日+异动+人气+连涨 | ✗ | ✗ | ⚠️ 条件 |
| **industry** | 行业板块匹配 | Tavily(general) + Brave(web) | ✗ | ✅ |
| **video** | ✗ | Brave News (补充) | ✗ | ✅ |
| **mckinsey** | ✗ | ✗ (仅用户输入) | ✗ | ✅ |
| **meeting** | ✗ | ✗ (仅用户输入) | ✗ | ✅ |

---

## 五、代码架构（重构后）

### 5.1 目录结构

```
finance-suite/
│
├── engine/                       # 🟢 场景引擎（稳定层，新增场景不改此目录）
│   ├── pipeline.py               # 核心分析管线：采集 → QC → LLM → 后处理
│   ├── registry.py               # ScenarioRegistry + ProviderRegistry
│   ├── cache.py                  # 引擎级缓存
│   ├── data_access.py            # MCP 数据访问抽象层
│   ├── providers/                # 可插拔数据源
│   │   ├── akshare_provider.py   # AkShare（股票/宏观/竞价/行业）
│   │   ├── search_provider.py    # 搜索引擎
│   │   ├── video_provider.py     # 视频字幕
│   │   └── user_input_provider.py # 用户输入（会议/麦肯锡）
│   ├── quality/                  # 统一质量门控
│   │   └── gate.py               # QC 规则引擎
│   └── llm/                      # LLM 调用封装
│       └── client.py             # 通义千问 API
│
├── scenarios/                    # 🟢 场景定义（每个场景 = 1 个目录，复制即新增）
│   ├── stock/                    # config.yaml + prompt.md + qc_rules.yaml + page.html
│   ├── macro/
│   ├── auction/
│   ├── industry/
│   ├── meeting/
│   ├── video/
│   └── mckinsey/
│
├── app/                          # 🟢 Web 后端应用
│   ├── main.py                   # FastAPI 入口 + lifespan
│   ├── config.py                 # 配置中心（Settings 类）
│   ├── auth.py                   # JWT 认证
│   ├── database.py               # SQLite ORM（User/Usage 模型）
│   ├── skills.py                 # 技能元数据定义
│   ├── search.py                 # 搜索聚合（Tavily + Brave）
│   ├── stock_data.py             # Web 端股票数据
│   ├── macro_data.py             # Web 端宏观数据
│   ├── auction_data.py           # Web 端竞价数据
│   ├── video_data.py             # Web 端视频数据
│   ├── llm.py                    # Web 端 LLM 调用
│   ├── routers/                  # HTTP 路由层
│   │   ├── pages.py              # 页面路由 + /app/* 前端文件服务
│   │   ├── api.py                # POST /api/analyze
│   │   ├── auth_routes.py        # 注册/登录/登出/鉴权
│   │   ├── export.py             # PDF 导出
│   │   ├── intel.py              # 市场情报（9 个端点）
│   │   ├── watchlist.py          # 自选股 CRUD
│   │   └── admin.py              # 管理后台
│   ├── services/                 # 业务编排层
│   │   ├── analyze_service.py    # 分析编排（数据获取 → LLM → QC → Trust）
│   │   ├── report_qc.py          # 报告质检 + Trust 合约 + 发布控制
│   │   └── event_facts.py        # 宏观事件事实预检
│   └── quality_gate/             # 质量门控实现
│       ├── core.py               # QualityGate 引擎
│       └── rules.py              # 质检规则集
│
├── frontend/                     # 🟢 平台级前端（非场景页面 + 共享组件）
│   ├── pages/                    # 9 个平台页面（index/d13_*/market-*/xueqiu-hot 等）
│   ├── scripts/                  # 5 个独立 JS（图表/估值/温度等）
│   ├── styles/                   # CSS
│   ├── shared/                   # 共享组件（sidebar-registry.js）
│   └── lib/                      # 第三方库（marked.min.js）
│
├── mcp_tools/                    # 🟢 MCP 独立产品线（AI Agent 接口）
│   ├── server.py                 # MCP 核心（FastMCP 实例 + 工具函数）
│   └── tools/                    # 18 个工具，按职责分组
│       ├── analysis.py           # stock/macro/market_pulse（调用 engine.data_access）
│       ├── search.py             # 多源搜索
│       ├── video.py              # 视频提取
│       ├── watchlist.py          # 自选股管理
│       ├── factor.py             # 因子选股
│       ├── wind.py               # Wind 万得
│       ├── jqdata.py             # JQData 聚宽
│       ├── ths.py                # 同花顺 iFinD
│       ├── emquant.py            # 东方财富 Choice
│       ├── social.py             # 雪球 + 知乎 + 新浪
│       ├── barchart.py           # Barchart 期权
│       ├── research.py           # 研报管理
│       └── market_intel.py       # 市场情报聚合
│
├── scripts/                      # 🟢 MCP 数据源（10 个活跃文件）
│   ├── stock_data.py             # 个股数据（Wind + AkShare + JQData 降级）
│   ├── macro_data.py             # 宏观数据
│   ├── auction_data.py           # 竞价数据
│   ├── video_data.py             # 视频字幕
│   ├── watchlist.py              # 自选股
│   ├── factor_scan.py            # 因子扫描
│   ├── wind_data.py              # Wind API
│   ├── tushare_data.py           # Tushare API
│   ├── emquant_data.py           # EmQuant API
│   └── ifind_data.py             # iFinD API
│
├── templates/                    # Jinja2 服务端模板（8 个）
├── tests/                        # 测试套件（150 用例）
├── deploy/                       # 部署配置
│   ├── nginx/                    # Nginx 配置 + 静态着陆页
│   ├── deploy.sh                 # 前端部署脚本
│   ├── deploy-backend.sh         # 后端部署脚本
│   └── healthcheck.sh            # 健康检查
├── docs/                         # 文档
│   ├── SYSTEM_DESIGN.md          # 本文档
│   ├── RESTRUCTURE_PLAN.md       # 重构方案（✅ 已完成）
│   ├── MCP_TOOLS_GUIDE.md        # MCP 工具使用指南
│   ├── guides/                   # 用户指南
│   ├── deployment/               # 部署文档
│   └── reviews/                  # 架构评审
│
├── mcp_server.py                 # MCP 瘦入口（12 行，委托 mcp_tools/server.py）
├── requirements.txt              # Python 依赖
├── pytest.ini                    # 测试配置
└── .env.example                  # 环境变量模板
```

### 5.2 架构分层

```
┌─────────────────────────────────────────────────────────────────────┐
│                        用户 / AI Agent                               │
└─────────────┬─────────────────────────────────┬─────────────────────┘
              │ Web 浏览器                       │ MCP 协议 (stdio)
              ▼                                  ▼
┌─────────────────────────┐     ┌──────────────────────────────────────┐
│  app/  (Web 后端)        │     │  mcp_tools/  (MCP 产品线)             │
│  FastAPI + Jinja2        │     │  FastMCP + 18 个工具                  │
│                          │     │                                      │
│  routers/ → services/   │     │  tools/ → engine.data_access         │
│  → app/*_data.py         │     │       → scripts/*                    │
└──────────┬───────────────┘     └──────────────┬───────────────────────┘
           │                                    │
           ▼                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     engine/  (场景引擎)                               │
│                                                                     │
│  pipeline.py ──→ providers/ ──→ quality/ ──→ llm/                  │
│  (管线编排)       (数据源)       (QC 质检)     (LLM 调用)            │
│                                                                     │
│  data_access.py ──→ scripts/ (MCP 数据源)                          │
└─────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     scenarios/  (场景定义)                            │
│                                                                     │
│  每个场景 = config.yaml + prompt.md + qc_rules.yaml + page.html    │
│  新增场景：复制目录 → 修改配置 → 自动注册，引擎代码零修改            │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.3 设计原则

| 原则 | 实现方式 |
|------|----------|
| **场景引擎化** | 框架是发动机，场景是燃料盒。新增场景不改引擎代码 |
| **前后端分离** | 前端在 `frontend/` + `scenarios/*/page.html`，后端在 `app/` |
| **双入口统一引擎** | Web (`app/`) 和 MCP (`mcp_tools/`) 共享 `engine/` |
| **数据源可插拔** | Provider 注册制，声明式配置，支持降级 |
| **质量内建** | QC 贯穿全流程：数据 QC → 报告 QC → Trust 合约 → 发布控制 |

### 5.4 重构成果

| 指标 | 重构前 | 重构后 |
|------|--------|--------|
| 新增场景改动文件数 | 3-5 个核心文件 | 1 个新目录（4 个文件） |
| 引擎代码改动频率 | 每次新增场景都改 | 几乎不改 |
| 前后端分离 | ❌ app/ 混杂 HTML/JS/CSS | ✅ 完全分离 |
| 数据层重复 | ❌ scripts/ 与 app/ 4 组同名 | ✅ 职责清晰，scripts/ 服务 MCP |
| 死代码 | ~4500 行 | 0 |
| MCP Server | ❌ 1887 行单文件 | ✅ 模块化，18 个工具分 13 个文件 |
| 测试用例 | 121 | 150 |
| 非程序员可新增场景 | ❌ 需改 Python | ✅ 编辑 YAML + Markdown + HTML |
