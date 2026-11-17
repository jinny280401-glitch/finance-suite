# FS_TO_VERA_ENGINEERING_HANDOFF

**日期：** 2026-11-18  
**FROM：** Finance Suite CC002  
**TO：** Vera C002 / Agent 编排程序员  
**RE：** Finance Suite MCP Trust Gate 能力交接

---

## 1. Finance Suite MCP 架构与工具清单

Finance Suite 是金融数据与研究能力底座，通过 MCP stdio 协议向 Agent 暴露 17 个工具。同时保留独立网站（HTTP `/api/analyze`），但**本轮 Handoff 仅覆盖 MCP 路径**，HTTP 路径 Trust Gate 架构性缺失（F-PROD-BOUNDARY-01），不在交接范围。

启动方式：
```bash
/Users/Zhuanz/finance-suite/.venv/bin/python3.12 /Users/Zhuanz/finance-suite/mcp_server.py
```

完整工具清单与参数见 `FS_MCP_TOOL_CAPABILITY_MATRIX.md`。Vera 应重点关注的工具：
- `wind_query`（Trust Gate 已接线，2026-11-18）
- `stock_analysis`（Trust Gate PARTIAL 接线）
- `watchlist_manage`（元数据操作，无 Trust Gate）
- 其余工具：无 Trust Gate，使用时须由 Vera 自行做来源校验

---

## 2. 已实现和未实现的能力

### 已实现

| 能力 | 状态 |
|---|---|
| wind_query G2 Field Integrity | IMPLEMENTED — `_enforce_trust_gate_or_block` 已接入所有数据出口 |
| wind_query G3 Freshness | IMPLEMENTED — phase-aware，含 connect 豁免 |
| wind_query BLOCK 信封数据剥离 | IMPLEMENTED — F-02 allowlist 重建，provider 数据不泄漏 |
| wind_query fail-closed | IMPLEMENTED — gate 不可用 → GATE_UNAVAILABLE BLOCK |
| wind_query 决策记录审计 | IMPLEMENTED — `decision_id` 格式 `tg-wind_query-{ts}-{hex}`，唯一 |
| stock_analysis Evidence Admission | PARTIAL — `build_evidence_bundle` + `authorize_task` 已接入 |
| stock_analysis Task Authorization | PARTIAL — `requested_use ⊆ allowed_use` 检查 |

### 未实现

| 能力 | 状态 |
|---|---|
| G1 Source Identity | NOT_IMPLEMENTED — `source_used` 为自报字符串，无加密绑定 |
| wind_query→生产部署 | NOT_AUTHORIZED — 本地工作树已接线，生产未部署 |
| HTTP `/api/analyze` Trust Gate | ABSENT — 架构性缺失，独立 Sprint |
| 非 wind_query/stock_analysis 工具 Trust Gate | NOT_IMPLEMENTED |
| `_qc_stock` derived valuation cap | NOT_IMPLEMENTED — OD-4/OD-5，派生数据可能升级 QC status |

---

## 3. REAL / FALLBACK / MOCK 状态

Provider 状态（运行时连接未验证，标注 NOT_PROVEN）：

| Provider | 类别 | 实时连接 | 数据时点 |
|---|---|---|---|
| Wind | REAL（付费订阅） | NOT_PROVEN | EOD snapshot |
| Tushare Pro | REAL（500元/年） | NOT_PROVEN | EOD + 季报 |
| JQData 聚宽 | FALLBACK（试用账号） | NOT_PROVEN（延迟） | 历史延迟 |
| AkShare | REAL（免费公开 API） | PROVEN（公开） | EOD + 财报 |

**Vera 注意：** `source_used` 字符串由 wind_query 内部循环赋值，无独立验证（G1 未实现）。Vera 不应仅凭 `source_used="wind"` 断定数据来自 Wind 真实接口。

---

## 4. Trust Gate 前置准入契约

### wind_query（本轮重点）

Vera 调用 `wind_query` 后，必须按以下顺序处理返回值：

```
1. 解析响应：raw.split("\n\n", 1) → envelope_json + content
2. json.loads(envelope_json)
3. 检查 _trust_gate.overall_verdict
   - "PASS" → 可消费 content（provider 数据）
   - "BLOCK" → 不得消费 content；读 _trust_gate.boundaries[].reason_code 决定处理
4. PASS 时：可消费 content，但受 allowed_use 约束（见 §5）
5. BLOCK 时：返回给用户"数据不可用"，不得将 content 传给 LLM
```

**BLOCK 原因码速查：**
| reason_code | 含义 | Vera 处理 |
|---|---|---|
| G2_CRITICAL_DIMENSION_MISSING | 关键字段缺失 | 提示数据不完整，不可分析 |
| G2_NO_RESULT | 无 provider 返回 | 提示数据源全失败 |
| G3_DATA_STALE | 数据过期 | 提示数据陈旧 |
| G3_TIMESTAMP_MISSING_REQUIRED | stock 无时间戳 | 提示数据无法验证新鲜度 |
| G3_FUTURE_TIMESTAMP | 未来时间戳 | 提示时钟异常 |
| GATE_UNAVAILABLE | Trust Gate 模块缺失 | fail-closed，提示系统错误 |
| GATE_ENFORCEMENT_ERROR | gate 执行异常 | fail-closed，提示系统错误 |

### stock_analysis

Vera 调用 `stock_analysis` 时必须传 `requested_use` 参数（如 `"fundamental_overview"`）。工具内部会检查 `requested_use ⊆ bundle.allowed_use`，不满足则 fail-closed 拒绝（返回 `_make_error_response`）。

**OD-4/OD-5 限制：** 修复前，`stock_analysis` 的 `_qc_stock` 对 derived valuation 不 cap status。当 Wind 不可用、PE/PB 从 AkShare 推算时，status 可能误升为 "success"。Vera 应额外检查 `valuation.valuation_source.type`：
- `"real_provider"` → 可信
- `"derived"` → 降级处理，仅作参考

---

## 5. QC 字段与 allowed_use 规则

### `_qc` 字段（所有工具）

| 字段 | 含义 |
|---|---|
| status | success / partial / failure |
| completeness | 0.0 - 1.0 |
| sources | 实际使用的 provider 列表 |
| fallback_source | 降级备源（未降级为 None） |
| missing_dimensions | 缺失维度 |
| stale_data | 陈旧数据条目 |

### `allowed_use`（stock_analysis / EvidenceBundle）

由 `build_evidence_bundle._allowed_use` 根据 status + data_type + ProviderClass 决定：

| 条件 | allowed_use |
|---|---|
| MOCK provider | `["workflow_smoke", "runtime_test"]` |
| status=failure | `[]` |
| quote/stock_analysis partial | `["fundamental_overview"]` |
| quote/stock_analysis success | `["fundamental_overview", "valuation_analysis", "peer_comparison"]` |
| FALLBACK provider | 仅 `["fundamental_overview", "historical_context"]` 子集 |

**Vera 不得使用以下用途，除非 allowed_use 明确包含：**
- `position_sizing` — 仓位建议
- `buy_sell_recommendation` — 买卖建议
- `fund_flow` — 资金流分析
- `short_term_signal` — 短线信号

---

## 6. Evidence ID 和来源追溯

### wind_query

`_trust_gate.decision_id`（格式 `tg-wind_query-{YYYYMMDDTHHMMSSffffff}-{8hex}`）是唯一审计 ID。Vera 若需追溯某次准入决策，grep 此 ID 可定位日志。

### stock_analysis

`AdmissionRecord.admitted_evidence_identity` = SHA256(canonical_json(evidence))。由 `derive_admitted_evidence_identity` 计算（`research_runtime/task_authorization.py:122`）。`AdmissionRecord.admission_decision_id` 格式 `adm-{n}`。

---

## 7. 五项遗留缺陷及其影响

详见 `FS_TRUST_GATE_OPEN_DEFECTS.md`。Vera 需特别注意：

| 缺陷 | 对 Vera 的影响 |
|---|---|
| OD-4/OD-5（P0）| stock_analysis derived valuation 时 status 误升，Vera 须手动检查 valuation_source.type |
| OD-1（P1）| wind_query 未来 date-only 时间戳可能 PASS，Vera 若需严格时间校验须自行检查 trade_date <= today |
| OD-2（P2）| daily_price 契约不一致，Vera 不应依赖 TIMESTAMP_REQUIRED_ACTIONS |
| OD-3（P3）| 仅测试问题，不影响 Vera |

---

## 8. Vera 可以调用和暂不可调用的工具

### 可以调用（条件可用）

| 工具 | 条件 |
|---|---|
| wind_query | 读 `_trust_gate.overall_verdict=="PASS"` 后消费；BLOCK 时不消费 |
| stock_analysis | 传 `requested_use="fundamental_overview"`；检查 valuation_source.type |
| watchlist_manage | 元数据操作，无数据准入问题 |
| macro_snapshot | 宏观参考，不做交易信号 |
| market_pulse | 盘面参考，不做仓位建议 |
| search | 研究/新闻参考 |
| sinafinance_fetch | 新闻参考 |
| research_reports | 研报链接列表 |
| research_digest | 脱水研报参考 |

### 暂不可调用

| 工具 | 原因 |
|---|---|
| factor_scan | JQData 试用账号延迟，实时信号不可靠 |
| zhihu_fetch | 需 Chrome 登录态，非服务器环境 |
| barchart_fetch | 需 Chrome 扩展，非服务器环境 |
| market_intel | 内部聚合工具，非 Vera 直接调用设计 |
| video_extract | 内容研究用，非数据准入 |

---

## 9. 最小端到端集成建议

Vera 调用 Finance Suite 的最小路径：

```
1. Vera 通过 MCP 调用 wind_query(action="connect", code="")
   → 确认 provider 连接状态

2. Vera 调用 wind_query(action="stock", code="600519.SH")
   → 检查 _trust_gate.overall_verdict
   - PASS → 提取 content 中的 price/pe/pb 等
   - BLOCK → 返回"数据不可用"给用户，不传 LLM

3. Vera 调用 stock_analysis(query="贵州茅台", requested_use="fundamental_overview")
   → 检查返回中 valuation.valuation_source.type
   - "real_provider" → 正常分析
   - "derived" → 标注"估值由推算得出，仅供参考"

4. Vera 将通过准入的 evidence 组装进研究报告，保留 decision_id / admission_decision_id 用于审计
```

---

## 10. Git 分支、commit、测试命令和验收结果

| 项目 | 值 |
|---|---|
| 仓库 | `https://github.com/jinny280401-glitch/finance-suite.git` |
| 分支 | `feature/trust-gate-mcp-wiring-gap1-gap4` |
| Code commit | `1324662811937e41c64d690d83c54a0c6962cc41` |
| Handoff commit | （本轮文档提交后生成，见下方）|
| 远端 main | `2aaa766684e7def4acf574770e99e7e3fb157fbf` |
| 分支基点 | 从 main 祖先派生，无冲突 |

### 测试命令

```bash
cd /Users/Zhuanz/finance-suite

# GAP-1 验收
.venv/bin/python -m pytest tests/test_trust_gate_phase1a.py::test_c02_gate_unavailable_field_parity \
  tests/test_trust_gate_phase1a.py::test_c03_all_return_paths_gated \
  tests/test_trust_gate_phase1a.py::test_c04_gate_unavailable_unique_ids -v
# 预期：3/3 PASS

# GAP-4 负控
.venv/bin/python -m pytest tests/test_wind_query_mcp_gate.py -v
# 预期：10/10 PASS

# 完整套件
.venv/bin/python -m pytest tests/test_trust_gate_phase1a.py tests/test_evidence_provenance.py \
  tests/test_admission_authenticity.py tests/test_wind_query_mcp_gate.py -v
# 预期：52/57 PASS，5 FAIL（OD-1~5，pre-existing，非本轮引入）
```

### 验收结果

```
GAP1_MCP_WIRING              = PROVEN (3/3)
GAP4_PATH_NEGATIVE_TESTS     = PASS (10/10)
BLOCKED_EVIDENCE_REACHES_LLM = FALSE
FALLBACK_BYPASS              = FALSE
FULL_SUITE                   = 52/57 PASS
OPEN_DEFECTS                 = 5（已登记 FS_TRUST_GATE_OPEN_DEFECTS.md）
PRODUCTION_DEPLOYMENT        = NOT_AUTHORIZED
G1_SOURCE_IDENTITY           = DEFERRED
```

---

## 跨项目边界

- **Finance Suite** = 金融数据与研究能力底座 + 独立网站。本轮只交接 MCP 路径。
- **Vera** = Agent 编排、证据归档与研报生成入口。通过 MCP 调用 Finance Suite 受控能力。
- **本轮不修改 Vera。** 本 Handoff 是接入契约，Vera 侧集成由 Vera 团队执行。
- **生产部署不授权。** 本轮成果在 `feature/trust-gate-mcp-wiring-gap1-gap4` 分支，未推送至 main，未部署生产。

---

**Vera 集成时的首要约束：** 不得把 wind_query 负控通过等同于 Wind 实时数据接入成功。所有 Trust Gate 测试使用 mock 数据，真实 provider 连接状态 NOT_PROVEN。Vera 集成测试须包含真实 provider 连接验证（独立于 Trust Gate 测试）。
