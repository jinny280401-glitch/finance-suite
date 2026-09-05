# Finance Suite 最终重构方案

> 综合生产代码实况、PPT 功能声称、工程讨论结论

---

## 一、现状诊断

### 1.1 生产代码实况（`/Users/huxuan/Downloads/finance-suite-web/`）

```
app/routers/api.py (1454行) — 一个函数干所有事
├── analyze() 近 500 行：数据获取 → LLM → QC → Trust → 发布控制
├── 6 个场景的 if/elif 分支，每个分支直接 import 数据模块
├── industry 场景没有独立数据模块，ak. 调用直接内联
└── QC/Trust/发布控制全部硬编码，不读配置

skills.py (640行) — 场景元数据 + prompt 全部内嵌
├── 6 个场景，prompt 最长 6660 字符（stock）
└── 没有 QC 规则、没有维度配置、没有降级链配置

app/stock_data.py (519行) — 只有 AkShare，没有多源降级
app/macro_data.py (183行)
app/auction_data.py (769行) — 最完善的模块，有 L1/L2/L3 分级
app/video_data.py (204行)
app/search.py (334行) — Tavily + Brave 多源搜索
```

### 1.2 仓库重构进度（`/Users/huxuan/Data/WorkSpace/python/finance-suite/`）

```
已完成：
  ✅ scenarios/*/ 目录结构（7 个场景，含 config.yaml + prompt.md + qc_rules.yaml）
  ✅ engine/providers/akshare_client.py — 纯 API 封装层
  ✅ engine/skills/stock_skill.py — 降级链 + 数据转换（1085行）
  ✅ engine/registry.py — ScenarioRegistry + ProviderRegistry
  ✅ engine/pipeline.py — AnalysisPipeline（但只委托给 analyze_service）

未完成：
  ❌ pipeline.py 没有真正编排，只是 delegate 给 analyze_service.py
  ❌ scenarios/*/config.yaml 没有被任何代码读取和执行
  ❌ app/stock_data.py 和 engine/skills/stock_skill.py 双实现并存
  ❌ QC 的 stale_data / missing_dimensions 从未正确填充
  ❌ 生产代码没有多源降级链（只有 AkShare）
```

### 1.3 PPT 声称 vs 代码实现差距

| PPT 声称（现有能力） | 生产代码 | 仓库代码 | 差距 |
|---|---|---|---|
| Wind→Tushare→JQ→AkShare 降级链 | ❌ 只有 AkShare | ✅ stock_skill.py 有降级链 | 仓库有，生产没有 |
| _qc 质检信封（6 个字段） | ⚠️ 字段在，stale_data 永远为空 | 同生产 | 壳在内容空 |
| 缺失维度显式标注 | ❌ 标注的是搜索信源数，不是维度 | 同生产 | 逻辑错误 |
| Trust 合约 + 发布控制 | ✅ 完整实现 | — | 已实现 |
| 集合竞价 L1/L2/L3 | ✅ 完整实现 | — | 已实现 |

---

## 二、目标架构

### 2.1 三层架构（用户定义）

```
Scenario（编排配置）— 做什么、怎么组合、prompt 是什么
  ↓ 读取 config.yaml 决定调用哪些 Skill
Skill（公共能力层）— 降级链、数据转换、取数逻辑
  ↓ 调用 Provider 获取原始数据
Provider（纯 API 层）— 调外部接口，返回 DataFrame
  ↓ 调用 AkShare/Wind/Tushare API
Data Source（外部数据源）
```

### 2.2 两个入口共享同一套管线

```
Web 入口：POST /api/analyze
  → app/routers/api.py（薄路由）
    → engine/pipeline.py（编排）
      → engine/skills/*（数据获取）
      → engine/quality/*（QC）
      → app/llm.py（LLM 调用）
      → engine/quality/*（报告 QC + Trust + 发布控制）

MCP 入口：@mcp.tool stock_analysis()
  → mcp_tools/tools/analysis.py（薄适配）
    → engine/pipeline.py（同一套编排）
      → engine/skills/*（同一套数据获取）
```

### 2.3 场景驱动，不是代码驱动

```
新增场景 = 复制 scenarios/stock/ → 改 config.yaml + prompt.md
           零代码修改（引擎代码不动）
```

---

## 三、分阶段实施

### Phase 1：统一数据层（消除双实现）

**目标**：`app/stock_data.py` 不再独立实现，改为调用 `engine/skills/`

**改动范围**：

```
app/stock_data.py (519行)
  改前：自己实现 _fetch_financials、_fetch_price_history 等
  改后：委托给 engine/skills/stock_skill.py

  def get_stock_full_data(code):
      from engine.skills.stock_skill import get_stock_full_data as _impl
      return await _impl(code)

  def format_stock_data(data, stock_name="", stock_code=""):
      from engine.skills.stock_skill import format_stock_data as _impl
      return _impl(data, stock_name, stock_code)

  # resolve_stock 等工具函数同理
```

**验证**：
- 生产 `app/routers/api.py` 的 `_fetch_stock_data()` import 路径不变
- 实际执行路径变为：api.py → app/stock_data.py → engine/skills/stock_skill.py → engine/providers/akshare_client.py
- 150 个测试全部通过

**风险**：低。只是加一层委托，不改变逻辑。

---

### Phase 2：QC 做实（兑现 PPT 承诺）

**目标**：`_qc` 信封的每个字段都有真实内容

**2.1 missing_dimensions — 按维度检查**

```python
# 改前（api.py L1193）：
"missing_dimensions": [] if completeness >= 0.8 else ["补充数据源"]

# 改后：
missing = []
dimension_status = {}
for dim in ["financials", "price_history", "fund_flow", "news", "dividends", "realtime"]:
    data = akshare_data.get(dim)
    has_data = data is not None and (len(data) > 0 if isinstance(data, (list, dict)) else False)
    dimension_status[dim] = "available" if has_data else "missing"
    if not has_data:
        missing.append(dim)

# _qc 字段：
"missing_dimensions": missing,
"dimension_status": dimension_status,  # 新增：每个维度的状态
```

**2.2 stale_data — 真正检测数据时效**

```python
# 在 Skill 层记录数据时间
def _fetch_price_history(code):
    df = ak_client.stock_zh_a_hist(...)
    if df is not None and len(df) > 0:
        latest_date = df["日期"].max()  # ← 数据最新日期
        return {"data": df.to_dict(...), "data_date": str(latest_date)}

# 在 QC 层检测时效
stale_data = []
for dim, info in dimension_info.items():
    if info.get("data_date"):
        days_old = (today - parse(info["data_date"])).days
        if days_old > 7:  # K线超过7天算过期
            stale_data.append(f"{dim}: {info['data_date']} ({days_old}天前)")

"stale_data": stale_data,
```

**2.3 hallucination_risk — 加入报告内容检查**

```python
# 改前：只看输入侧（搜索信源数量）
# 改后：对比 prompt 中的结构化数据 vs LLM 报告中的数字

def _check_report_numbers(report_text: str, structured_data: dict) -> dict:
    """提取报告中的关键数字，与结构化数据比对"""
    # 从 structured_data 提取关键数字（营收、净利润、PE 等）
    expected_numbers = extract_key_numbers(structured_data)
    # 从 report_text 中提取数字
    reported_numbers = extract_numbers_from_text(report_text)
    # 比对
    mismatches = []
    for key, expected in expected_numbers.items():
        reported = reported_numbers.get(key)
        if reported and abs(reported - expected) / expected > 0.1:  # 10% 偏差
            mismatches.append(f"{key}: 数据={expected}, 报告={reported}")
    return {"mismatches": mismatches, "checked_count": len(expected_numbers)}
```

**验证**：
- 用一个已知数据的股票（如比亚迪），检查报告中的数字是否与 AkShare 返回的一致
- `stale_data` 在非交易时段应该能检测到 K 线数据日期

---

### Phase 3：Pipeline 真正编排（场景配置驱动）

**目标**：`pipeline.py` 不再委托给 `analyze_service.py`，自己编排流程

**3.1 Pipeline 读取 Scenario 配置**

```python
class AnalysisPipeline:
    async def run(self, skill_type, query, extra_content=""):
        scenario = self.registry.get(skill_type)

        # 1. 数据获取：根据 config.yaml 的 providers 配置
        provider_results = {}
        for provider_config in scenario.providers:
            if provider_config.type == "search":
                provider_results["search"] = await self._fetch_search(query, provider_config)
            else:
                provider_results["structured"] = await self._fetch_structured(query, provider_config)

        # 2. 数据 QC：根据 config.yaml 的 qc 配置
        qc_result = self._run_qc(provider_results, scenario.qc)

        # 3. LLM 调用（如果场景不跳过）
        if not scenario.skip_llm and qc_result.passed:
            prompt = scenario.prompt  # ← 从 prompt.md 读取
            report = await generate_analysis(prompt, query, provider_results)
        else:
            report = provider_results.get("formatted_text", "")

        # 4. 报告 QC
        report_qc = self._run_report_qc(report, provider_results, scenario)

        # 5. Trust + 发布控制
        response = self._build_response(report, provider_results, report_qc, scenario)
        response = apply_trust_contract(response)
        response = apply_publication_containment(response)

        return response
```

**3.2 场景配置扩展**

```yaml
# scenarios/stock/config.yaml
name: stock
display_name: 看票分析
search_type: stock

# Skill 映射：告诉 pipeline 调哪个 Skill
skill: stock_skill

# 数据维度（Skill 按这个列表获取数据）
dimensions:
  - financials    # 财报
  - realtime      # 实时行情
  - price_history # K线
  - fund_flow     # 资金流
  - news          # 新闻
  - dividends     # 分红

# 搜索配置
search:
  strategy: stock_multi_dimension
  primary: tavily
  fallback: brave

# 缓存
cache:
  enabled: true
  ttl: 600

# QC 规则（场景级别）
qc:
  min_completeness: 0.8
  min_sources: 2
  require_structured: true
  # 维度级 QC
  dimensions:
    financials: { required: true, stale_days: 90 }
    price_history: { required: true, stale_days: 3 }
    fund_flow: { required: false, stale_days: 3 }
    news: { required: false, stale_days: 7 }
    dividends: { required: false }
    realtime: { required: true, stale_days: 1 }
```

**验证**：
- Pipeline 跑 stock/macro/auction 三个场景，结果与当前生产一致
- 修改 config.yaml 的 dimensions 列表，输出维度随之变化
- 新增场景只需复制目录 + 改配置

---

### Phase 4：生产同步（仓库 → 生产）

**目标**：把重构后的代码部署到生产

**4.1 文件迁移清单**

```
仓库 → 生产：
  engine/                     → 整个目录复制到生产
  scenarios/                  → 整个目录复制到生产
  app/stock_data.py           → 替换为委托版本（Phase 1 产出）
  app/routers/api.py          → 瘦身后版本（Phase 3 产出）
  app/services/analyze_service.py → 删除（逻辑迁入 pipeline.py）

生产保留不动：
  app/auth.py, app/database.py     — 认证系统，仓库没有
  app/routers/intel.py             — 市场情报，仓库没有
  app/routers/watchlist.py         — 自选股，仓库没有
  templates/                       — Jinja2 模板，仓库没有
  static/                          — 前端静态文件
  quality_gate/                    — 合并到 engine/quality/
```

**4.2 灰度策略**

```
Step 1: 只切换数据层（Phase 1）
  app/stock_data.py → engine/skills/stock_skill.py
  验证：所有场景返回数据一致

Step 2: 切换 QC（Phase 2）
  新的维度级 QC 替换旧的搜索信源 QC
  验证：stale_data 和 missing_dimensions 有真实内容

Step 3: 切换 Pipeline（Phase 3）
  api.py analyze() 改为调用 pipeline.run()
  验证：端到端流程一致
```

---

## 四、PPT 功能补齐清单

| PPT 声称 | 当前状态 | 需要做什么 | 归属 Phase |
|---|---|---|---|
| 多源降级链 | 仓库有，生产没有 | Phase 1 统一数据层后自动上生产 | Phase 1 |
| _qc 维度级标注 | 壳在内容空 | Phase 2 做实 missing_dimensions | Phase 2 |
| stale_data 检测 | 从未填充 | Phase 2 加数据时效检测 | Phase 2 |
| 报告数字校验 | 不存在 | Phase 2 加 _check_report_numbers | Phase 2 |
| 场景配置驱动 | config 不被读取 | Phase 3 pipeline 读配置 | Phase 3 |
| 研报脱水 | 只有列表没有脱水 | 新增 research_skill.py | Phase 3+ |
| 自选股历史研究 | 空数组 | 新增 research_log 模块 | 后续 |
| 价格提醒 | 不存在 | 新增 alert_skill.py | 后续 |

---

## 五、不做的事

1. **不重构认证系统** — 生产 auth/database 稳定运行，仓库不需要有
2. **不迁移 research_runtime/** — PPT 已标注"实验能力 NOT PROVEN"，不急于上生产
3. **不实现 BYOR** — PPT 已标注"规划能力"
4. **不实现投资复盘** — PPT 已标注"规划能力"
5. **不实现私有化部署** — PPT 已标注"规划能力"
6. **不改前端** — 前端 Trust Presentation Layer 在生产稳定运行

---

## 六、执行顺序与依赖关系

```
Phase 1（统一数据层）
  ↓ 无依赖，可立即开始
  ↓ 产出：app/stock_data.py 委托版本
  ↓ 验证：150 测试通过 + 数据一致性
  ↓
Phase 2（QC 做实）
  ↓ 依赖 Phase 1（数据层统一后才能加维度检测）
  ↓ 产出：维度级 QC + stale_data + 报告数字校验
  ↓ 验证：stale_data 有内容 + missing_dimensions 按维度
  ↓
Phase 3（Pipeline 编排）
  ↓ 依赖 Phase 1 + 2（数据和 QC 都就位后编排才有意义）
  ↓ 产出：pipeline.py 真正编排 + 场景配置驱动
  ↓ 验证：端到端流程一致 + 新增场景零代码
  ↓
Phase 4（生产同步）
  ↓ 依赖 Phase 3（全部完成后统一部署）
  ↓ 灰度：数据层 → QC → Pipeline 分步切换
```

---

## 七、一句话总结

**Phase 1 让数据层只有一个源头，Phase 2 让 QC 兑现 PPT 承诺，Phase 3 让场景配置真正驱动编排，Phase 4 把仓库能力同步到生产。**
