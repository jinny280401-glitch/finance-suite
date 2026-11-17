# FS_MCP_TOOL_CAPABILITY_MATRIX

**日期：** 2026-11-18  
**版本：** v0.1 (GAP-1/GAP-4 closeout)  
**说明：** 本矩阵以代码静态分析为基础。Provider 实时连接状态未在本轮核验，标注 NOT_PROVEN 处需运行时验证。  
**未验证项统一标记：** NOT_PROVEN

---

## 一、工具总览

| # | 工具名 | 主 Provider | Trust Gate | Vera 可调用 | 进第三方 LLM |
|---|---|---|---|---|---|
| 1 | stock_analysis | Wind/AkShare/JQData | PARTIAL (build_evidence_bundle + authorize_task) | 条件可用 | 条件可用 |
| 2 | wind_query | Wind/Tushare/JQData/AkShare | **WIRED (GAP-1, 2026-11-18)** | 条件可用 | 条件可用 |
| 3 | macro_snapshot | AkShare | QC only，无 Trust Gate | 条件可用（仅参考） | 条件可用（仅参考）|
| 4 | market_pulse | AkShare | QC only，无 Trust Gate | 条件可用（仅参考） | 条件可用（仅参考）|
| 5 | search | Tavily/Brave | QC only，Trust Gate 未接入 MCP 路径 | 条件可用 | 条件可用 |
| 6 | factor_scan | JQData/AkShare | QC only | 暂不可用（实时数据不可靠） | 暂不可用 |
| 7 | watchlist_manage | 本地 SQLite | 无 Trust Gate | 可用（元数据操作）| 不适用 |
| 8 | video_extract | YouTube/Bilibili 字幕 | 无 Trust Gate | 条件可用 | 条件可用 |
| 9 | zhihu_fetch | 知乎 autocli | 无 Trust Gate | 暂不可用（需 Chrome 登录）| 暂不可用 |
| 10 | sinafinance_fetch | 新浪财经公开 API | QC only | 条件可用（新闻参考）| 条件可用 |
| 11 | barchart_fetch | Barchart autocli | 无 Trust Gate | 暂不可用（需 Chrome 扩展）| 暂不可用 |
| 12 | research_reports | 本地知识库/IMA | 无 Trust Gate | 条件可用（链接参考）| 条件可用 |
| 13 | research_digest | 东方财富/AkShare + LLM | 无 Trust Gate | 条件可用 | 条件可用 |
| 14 | market_intel | 聚合（多工具） | 无 Trust Gate | 暂不可用（内部聚合）| 暂不可用 |
| 15 | jqdata_query | JQData 聚宽 | 无 Trust Gate | 条件可用（延迟数据）| 条件可用 |
| 16 | ths_query | 同花顺 iFinD | 无 Trust Gate | 条件可用 | 条件可用 |
| 17 | emquant_query | 东方财富 Choice | 无 Trust Gate | 条件可用 | 条件可用 |

---

## 二、工具详情

### Tool-01: stock_analysis

**参数：** `query: str`（股票名/代码），`requested_use: str | None`  
**返回：** `{"_qc": {...}, "_incremental": {...}}` + 格式化股票分析文本  
**Provider 链：** Wind（优先）→ AkShare → JQData（备用）  
**Provider 状态：** Wind=NOT_PROVEN（需运行时验证）；AkShare=REAL（公开API）；JQData=FALLBACK（试用账号有延迟）  
**数据时点：** 实时行情 NOT_PROVEN；财报=最新季报；K线=EOD  
**来源许可：** AkShare 公开数据，仅供个人参考；Wind 需订阅授权 NOT_PROVEN  
**QC 字段：** `_qc.status`(success/partial/failure)，`completeness`(0-1)，`missing_dimensions`，`stale_data`，`sources`，`fallback_source`  
**Trust Gate 状态：** PARTIAL — `build_evidence_bundle` + `authorize_task` 已接入（mcp_server.py:572-587）；G2/G3 boundary 未接入（使用 `_admit_for_stock_analysis` 而非 `enforce_wind_query`）  
**OD-4/OD-5 影响：** `_qc_stock` 对 derived valuation 不 cap status，completeness>=0.8 时 status=success → allowed_use 可能错误升级  
**allowed_use：** 由 `build_evidence_bundle` 根据 status/data_type/ProviderClass 决定。partial → `["fundamental_overview"]`；success → `["fundamental_overview","valuation_analysis","peer_comparison"]`；failure → `[]`  
**blocked_fields：** MOCK provider → 全阻断；FALLBACK + partial → TRADING_DECISION_FIELDS 阻断  
**Evidence ID：** `AdmissionRecord.admitted_evidence_identity`（SHA256 of evidence dict）  
**Vera 可调用：** 条件可用。`requested_use="fundamental_overview"` 时；不得传 `position_sizing`/`buy_sell_recommendation`；OD-4 修复前不可用于基本面以外判断  
**进第三方 LLM：** 条件可用，仅限 `allowed_use` 范围内；OD-4 修复前需手动确认 status 非 derived 升级

---

### Tool-02: wind_query

**参数：** `action: str`（connect/stock/financials/consensus/peers/valuation/shareholders/calendar），`code: str`，`max_peers: int=10`  
**返回：** `{"_qc": {...}, "_trust_gate": {...}}` + provider 数据（PASS）或 BLOCK 消息（BLOCK）  
**Provider 链：**  
- stock: Wind → Tushare → JQData  
- financials: Tushare → JQData → AkShare  
- consensus/peers: Wind → Tushare  
- valuation: Wind → JQData → Tushare → AkShare  
- shareholders/calendar: Wind 单源  

**Provider 状态：** Wind=NOT_PROVEN；Tushare=NOT_PROVEN；JQData=FALLBACK（试用延迟）；AkShare=REAL  
**数据时点：** stock EOD（24h freshness）；financials 120d；consensus 30d；peers 7d；valuation 7d；shareholders 120d；calendar 30d  
**来源许可：** 同 stock_analysis  
**QC 字段：** 同上 + `_trust_gate.overall_verdict`(PASS/BLOCK)，`_trust_gate.blocked_boundaries`，`_trust_gate.boundaries[]`  
**Trust Gate 状态：** **WIRED (GAP-1, 2026-11-18)** — 所有数据出口经 `_enforce_trust_gate_or_block()`；G2(Field Integrity)+G3(Freshness) 激活；G1(Source Identity)=NOT_IMPLEMENTED（DEFERRED）  
**allowed_use：** 由 `format_trust_gate_envelope` 注入 `_trust_gate`；消费方应读 `_trust_gate.overall_verdict` 决定是否消费  
**blocked_fields：** BLOCK 时 `_qc` 从 allowlist 重建，provider 数据值不出现在响应中（F-02 保证）  
**Evidence ID：** `_trust_gate.decision_id`（格式 `tg-wind_query-{ts}-{suffix}`）  
**Vera 可调用：** 条件可用。读 `_trust_gate.overall_verdict=="PASS"` 再消费数据；fallback action（shareholders/calendar 仅 Wind 单源）连接失败时 BLOCK，Vera 须处理 BLOCK 响应  
**进第三方 LLM：** 条件可用，仅限 PASS 且 `_trust_gate.overall_verdict=="PASS"` 时  
**重要限制：** wind_query 负控通过 ≠ Wind 实时数据接入成功。测试使用 mock 数据，Wind/Tushare 实际连接 NOT_PROVEN

---

### Tool-03: macro_snapshot

**参数：** 无  
**返回：** `{"_qc": {...}}` + GDP/CPI/PMI/M2/LPR 数据  
**Provider：** AkShare（REAL，公开 API）  
**Trust Gate：** QC only，无 Trust Gate 接入  
**allowed_use：** NOT_DEFINED（无 Trust Gate）  
**Vera 可调用：** 条件可用，宏观参考仅，不得用于交易信号  
**进第三方 LLM：** 条件可用（公开宏观数据）

---

### Tool-04: market_pulse

**参数：** 无  
**返回：** `{"_qc": {...}}` + 涨停池/强势股/大笔买入/热股等盘面数据  
**Provider：** AkShare（REAL，单源）  
**Trust Gate：** QC only，无 Trust Gate  
**OD 关联：** 无  
**Vera 可调用：** 条件可用，盘面参考仅，不得用于仓位建议  
**进第三方 LLM：** 条件可用（盘面参考）

---

### Tool-05: search

**参数：** `query: str`，`search_type: str`，`url: str | None`  
**返回：** `{"_qc": {...}}` + 搜索结果  
**Provider：** Tavily/Brave（需 API key）  
**Trust Gate：** `docs/findings/finding_search_evidence_trust_gate_bypass_p0.md` 记录 Bypass P0 OPEN  
**Vera 可调用：** 条件可用（新闻/研究参考）  
**进第三方 LLM：** 条件可用

---

### Tool-06: factor_scan

**参数：** `date: str=""`  
**返回：** JQData 因子选股信号  
**Provider：** JQData（FALLBACK，试用账号有历史延迟）  
**Trust Gate：** QC only  
**Vera 可调用：** 暂不可用（JQData 试用账号数据延迟，不可用于实时信号）  
**进第三方 LLM：** 暂不可用

---

### Tool-07: watchlist_manage

**参数：** `action: str`，`code/name/note/tag` 等  
**返回：** 自选股操作结果  
**Provider：** 本地 SQLite（无外部依赖）  
**Trust Gate：** 不适用（元数据操作）  
**Vera 可调用：** 可用（持仓/研究记录管理）  
**进第三方 LLM：** 不适用（操作类）

---

### Tool-08: video_extract

**参数：** `url: str`  
**返回：** 视频字幕/内容  
**Provider：** YouTube/Bilibili 公开字幕  
**Trust Gate：** 无  
**Vera 可调用：** 条件可用（内容研究）  
**进第三方 LLM：** 条件可用

---

### Tool-09 ~ Tool-17（简表）

| 工具 | Provider | Trust Gate | Vera 可调用 |
|---|---|---|---|
| zhihu_fetch | 知乎 autocli（需 Chrome） | 无 | 暂不可用 |
| sinafinance_fetch | 新浪公开 API | QC only | 条件可用（新闻参考）|
| barchart_fetch | Barchart autocli（需 Chrome 扩展）| 无 | 暂不可用 |
| research_reports | 本地 JSON/IMA | 无 | 条件可用（链接列表）|
| research_digest | 东方财富+LLM | 无 | 条件可用 |
| market_intel | 多工具聚合 | 无 | 暂不可用（内部聚合）|
| jqdata_query | JQData | 无 Trust Gate | 条件可用（延迟）|
| ths_query | 同花顺 iFinD | 无 Trust Gate | 条件可用 |
| emquant_query | 东方财富 Choice | 无 Trust Gate | 条件可用 |

---

## 三、关键约束

1. **stock_analysis = PARTIAL 时**：只能用于基本面速览（`fundamental_overview`），不得推导短线信号、资金流分析或仓位建议。
2. **wind_query 负控通过 ≠ Wind 实时数据接入**：所有负控使用 mock/stub 数据，Wind/Tushare 真实连接未在本轮验证（NOT_PROVEN）。
3. **G1 Source Identity = NOT_IMPLEMENTED**：工具名称与提供方身份绑定未实现，`source_used` 为自报字符串，无加密绑定。
4. **OD-4/OD-5 open**：派生估值在修复前，`stock_analysis` 返回的 status=success 可能来自派生数据，消费方须检查 `valuation_source.type`。
5. **生产部署**：Trust Gate 接线当前仅在本地工作树，生产 `/api/analyze` 路径架构性缺失 Trust Gate（F-PROD-BOUNDARY-01），未修复。
