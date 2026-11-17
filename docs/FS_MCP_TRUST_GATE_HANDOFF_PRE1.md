# FS_MCP_TRUST_GATE_HANDOFF_PRE1

**日期：** 2026-11-18  
**执行者：** CC002 / MAC-002  
**阶段：** GAP-1 + GAP-4 Closeout Handoff  
**状态：** HANDOFF_READY（待 Owner 审查）

---

## 一、本轮成果摘要

### Git 资产

| 项目 | 值 |
|---|---|
| 目标 commit | `1324662811937e41c64d690d83c54a0c6962cc41` |
| 分支 | `feature/trust-gate-mcp-wiring-gap1-gap4` |
| 父提交 | `b3774a8765415c434ac45c8c9c3be606776b885d` |
| 修改文件 | `mcp_server.py`，`tests/test_wind_query_mcp_gate.py` |
| 凭据扫描 | CLEAN（grep 无 password/token/secret/api_key/sk-）|
| Commit 对象 | VERIFIED（`git cat-file -t` = commit）|
| Detached HEAD | 已解决（切换至 `feature/trust-gate-mcp-wiring-gap1-gap4`）|
| Commit 保全风险 | OPEN → MITIGATED（已创建分支）|
| 远端推送 | 待 Owner 授权后执行 |

### 验收结果

| 指标 | 结果 |
|---|---|
| GAP1_MCP_WIRING | PROVEN — C-02/C-03/C-04 全部 PASS |
| GAP4_PATH_NEGATIVE_TESTS | PASS — 10/10 |
| BLOCKED_EVIDENCE_REACHES_LLM | FALSE |
| FALLBACK_BYPASS | FALSE |
| FULL_SUITE | 52/57 PASS |
| OPEN_DEFECTS | 5（见 FS_TRUST_GATE_OPEN_DEFECTS.md）|
| PRODUCTION_DEPLOYMENT | NOT_AUTHORIZED |
| G1_SOURCE_IDENTITY | DEFERRED |

---

## 二、架构说明

### 整体架构

```
Agent (Vera / Claude Code / OpenClaw)
  ↓  MCP stdio 协议
mcp_server.py  FastMCP("finance-suite")
  ↓  @mcp.tool() 注册（函数名 = 工具名）
wind_query / stock_analysis / ...
  ↓  _enforce_trust_gate_or_block()   ← GAP-1 新增，wind_query 专用
     enforce_wind_query()             ← G2 Field Integrity + G3 Freshness
     format_trust_gate_envelope()     ← PASS/BLOCK 信封格式化
  ↓
LLM（消费 EvidenceBundle 或处理 BLOCK 消息）
```

### wind_query 接线前后对比

| 路径 | 接线前 | 接线后 |
|---|---|---|
| B1 connect | `_wrap_response` 直接返回 | 经 `_enforce_trust_gate_or_block`（G3_CONNECT_EXEMPT）|
| B3 空结果 | `_wrap_response(qc,"")` 直接返回 | 经 choke point → G2_NO_RESULT BLOCK |
| B4 成功 | `_wrap_response(qc,formatted)` 直接返回 | 经 choke point → G2+G3 决策 |
| B2 no-code | `_make_error_response` | 不变（无 evidence）|
| B5 异常 | `_make_error_response` | 不变（无 evidence）|

### stock_analysis 接线（本轮前已存在，供参考）

```
stock_analysis
  ↓  _admit_for_stock_analysis(data, qc)
     → build_evidence_bundle(gateway_response)
     → EvidenceBundle / BlockedEvidence
  ↓  authorize_task(requested_use, bundle.allowed_use)
  ↓  format_stock_analysis_from_bundle(bundle)
  ↓  _wrap_response(qc, formatted)
```

---

## 三、关键接口

### `_enforce_trust_gate_or_block` 签名

```python
def _enforce_trust_gate_or_block(
    action: str,          # wind_query action
    code: str,            # 股票代码（connect 为 ""）
    result: dict | None,  # provider 返回数据（None = 全部失败）
    source_used: str,     # 实际使用的 provider 名称
    raw_response: str,    # _wrap_response 构造的原始响应字符串
    chain: list[str] | None = None,   # 降级链（用于 GATE_UNAVAILABLE audit）
    retrieved_at: str | None = None,  # ISO8601 查询时间
) -> str                  # 带 _trust_gate 注入的信封字符串
```

**返回格式（PASS）：**
```json
{"_qc": {...}, "_trust_gate": {"overall_verdict": "PASS", "decision_id": "...", ...}}

{"source": "wind", "code": "...", "action": "stock", "data": {...}}
```

**返回格式（BLOCK）：**
```json
{"_qc": {safe metadata only}, "_trust_gate": {"overall_verdict": "BLOCK", ...}}

数据不可用 (Trust Gate BLOCK): G2: ...
```

### Trust Gate 决策字段

| 字段 | 含义 |
|---|---|
| `_trust_gate.overall_verdict` | "PASS" 或 "BLOCK" |
| `_trust_gate.decision_id` | 格式 `tg-wind_query-{ts}-{hex}`，可 grep 审计 |
| `_trust_gate.blocked_boundaries` | BLOCK 时为 `["G2"]`/`["G3"]`/`["GATE"]` 等 |
| `_trust_gate.boundaries[].reason_code` | 机器可读原因码（G2_CRITICAL_DIMENSION_MISSING 等）|
| `_trust_gate.tool` | 始终为 "wind_query" |

---

## 四、已知限制

1. **G1 Source Identity = NOT_IMPLEMENTED**：`source_used` 是提供方自报字符串，无加密绑定。工具名称与提供方身份无独立验证机制。
2. **Wind/Tushare 实际连接 NOT_PROVEN**：所有测试使用 mock/stub 数据，真实连接需运行时验证。
3. **生产路径（HTTP /api/analyze）Trust Gate 缺失**：F-PROD-BOUNDARY-01（架构性缺失），本轮不修改。
4. **OD-4/OD-5（派生估值 P3）open**：`stock_analysis` 的 `_qc_stock` 对 derived valuation 不 cap status，可能使派生数据获得完整 allowed_use。
5. **非 wind_query 工具无 Trust Gate**：除 stock_analysis（PARTIAL）外，其余工具均无 Trust Gate 接入。

---

## 五、测试命令

```bash
# 运行 GAP-1 验收测试
cd /Users/Zhuanz/finance-suite
.venv/bin/python -m pytest tests/test_trust_gate_phase1a.py::test_c02_gate_unavailable_field_parity \
  tests/test_trust_gate_phase1a.py::test_c03_all_return_paths_gated \
  tests/test_trust_gate_phase1a.py::test_c04_gate_unavailable_unique_ids -v

# 运行 GAP-4 负控测试
.venv/bin/python -m pytest tests/test_wind_query_mcp_gate.py -v

# 运行完整套件（含 5 项预期失败）
.venv/bin/python -m pytest tests/test_trust_gate_phase1a.py tests/test_evidence_provenance.py \
  tests/test_admission_authenticity.py tests/test_wind_query_mcp_gate.py -v
# 预期：52/57 PASS，5 FAIL（OD-1~5，pre-existing）
```

---

## 六、NEXT_GATE

| 下一步 | 负责方 |
|---|---|
| Owner 审查本分支并批准 push | Owner |
| 修复 OD-4/OD-5（P0，派生估值 QC 升级）| Owner 授权后 CC |
| 修复 OD-1（P1，未来时间戳）| Owner 授权后 CC |
| 实现 G1 Source Identity | 独立 Sprint，Owner 授权 |
| 修复生产 HTTP 路径 Trust Gate 缺失（F-PROD-BOUNDARY-01）| 独立 Sprint |
| Vera 集成测试 | Vera 团队基于本 Handoff |
