# FS-MCP-TRUST-GATE-PRE2-READINESS

**执行者：** CC002 / MAC-002  
**日期：** 2026-11-18  
**模式：** STRICT_READ_ONLY  
**实施授权：** NO  
**前置：** `FS_MCP_TOOL_IDENTITY_PRE1.md`  
**NEXT_GATE：** OWNER_REVIEW

---

## 完成状态矩阵

| Gate | 结论 |
|---|---|
| GATE_A (准入语义) | PASS（库语义完备），但 MCP 路径未触发 |
| GATE_B (调用路径) | FAIL — wind_query 全部 5 个返回分支绕过 enforcer |
| GATE_C (接线兼容性) | PASS — 契约兼容，stock_analysis 已提供验证模板 |
| GATE_D (负控设计) | PARTIAL — enforcer 层有覆盖，wind_query 路径层缺失 |
| GATE_E (生产差异) | INSUFFICIENT_EVIDENCE — 生产身份 NOT_REPINNED |
| MCP_BYPASS_CODE_PATH | CONFIRMED — wind_query 主路径 + connect + 空结果 + 异常 4 个出口均无 gate |
| PRODUCTION_GATE_STATUS | ABSENT — 生产走 HTTP `/api/analyze` 非 MCP；Trust Gate 架构性缺失 |
| PRE2_IMPLEMENTATION_READY | CONDITIONAL — 库层 ready，路径层 NOT ready |
| FINAL_STATUS | BLOCKED（待 Owner 授权接线） |

---

## Gate A：准入语义

### A.1 库层语义（`research_runtime/evidence_bundle.py`）

| 语义要素 | 实现 | 证据 |
|---|---|---|
| `_qc.status` 解析 | `_status()` L50-51，降级为 failure 默认 | evidence_bundle.py:50 |
| `blocked_fields` 计算 | `_runtime_blocked_fields()` L129-148，failure→`BLOCK_ALL` | evidence_bundle.py:129 |
| `allowed_use` 计算 | `_allowed_use()` L85-126，按 status/data_type/ProviderClass 分级 | evidence_bundle.py:85 |
| PARTIAL 限制 | L106-108 quote partial→`["fundamental_overview"]`；L123-124 FALLBACK→仅 overview/historical | evidence_bundle.py:106,123 |
| BLOCKED 拒绝 | `BlockedEvidence` L205-213，F1 invariant：空 admitted evidence 必须 fail-closed | evidence_bundle.py:205 |
| reason 优先级 | P1(qc_failure)>P2(no_allowed_use)>P3(no_admitted_evidence) L194-203，FROZEN | evidence_bundle.py:194 |

**准入发生在 LLM 上下文之前：** 是（库层）。`_run_trust_gate` L266-364 对 `kind=gateway_*` 的 evidence 先 `build_evidence_bundle`，产出 `EvidenceBundle`（允许）或 `BlockedEvidence`（拒绝），`generate_section_body` L225-237 只接受 `EvidenceBundle` 类型，`BlockedEvidence` 无法进入。

### A.2 MCP `wind_query` 路径

**准入判断未发生。** `wind_query`(mcp_server.py:977-1178) 不调用 `build_evidence_bundle`、`_run_trust_gate`、`enforce_wind_query` 中的任何一个。LLM 直接消费 `_wrap_response(qc, formatted)` 的原始输出。

**Gate A 结论：** 库语义 PASS；MCP 路径准入未触发，语义对 wind_query 不生效。

---

## Gate B：调用路径

### wind_query 全部返回分支（mcp_server.py:977-1178）

| # | 分支 | 行 | 返回 | 经过 enforcer？ |
|---|---|---|---|---|
| B1 | `action == "connect"` | L1060 | `_wrap_response(qc, json.dumps(result))` | NO |
| B2 | `not code` | L1063 | `_make_error_response(...)` | NO（错误路径，gate 无输入） |
| B3 | 全部 provider 失败 `not result` | L1160 | `_wrap_response(qc, "")` (failure qc) | NO |
| B4 | 成功 | L1174 | `_wrap_response(qc, formatted)` | NO |
| B5 | 顶层异常 | L1178 | `_make_error_response(...)` | NO |

**5 个出口均不调用 `enforce_wind_query`。** B1/B3/B4 是数据出口（evidence 进入 LLM），均绕过 gate。B2/B5 是错误出口，gate 无输入数据可检查，但即使错误响应也未标注 gate 状态。

```
wind_query 调用路径图：
  action=connect ───────────────────────────────► _wrap_response ─► LLM  [B1 绕过]
  not code ─────────────────────────────────────► _make_error ────► LLM  [B2]
  for source in chain:
    candidate = runners[source]()
    if candidate: result, source_used, break
  not result ──────────────────────────────────► _wrap_response ─► LLM  [B3 绕过]
  result exists ─► qc={status:success,...} ──────► _wrap_response ─► LLM  [B4 绕过]
  except ───────────────────────────────────────► _make_error ────► LLM  [B5]

  enforce_wind_query / format_trust_gate_envelope / build_evidence_bundle
    ↑ 三个函数在 wind_query 作用域内零引用（grep 验证，HEAD 与工作树一致）
```

**Gate B 结论：FAIL。** 数据出口 B1/B3/B4 全部绕过 enforcer，存在多条 bypass 路径。

---

## Gate C：接线兼容性

### C.1 输入输出契约

`enforce_wind_query` 签名（enforcer.py:60-67）：
```python
enforce_wind_query(action, code, result, source_used, chain, retrieved_at) -> TrustGateDecision
```
wind_query 作用域内可用变量：`action`✓ `code`✓ `result`✓ `source_used`✓ `chain`✓（局部 L1078）。`retrieved_at` 缺省为 `datetime.now()`（enforcer.py:88-89），可不传。

`format_trust_gate_envelope(decision, original_response)` 签名（enforcer.py:137-140）：接收 `TrustGateDecision` + 原始 `_wrap_response` 字符串，返回带 `_trust_gate` 注入的信封。

**契约兼容：YES。**

### C.2 错误传播

`enforce_wind_query` 内部 try/except（enforcer.py:97-123）：任何 enforcement 异常 → `BoundaryResult(BLOCK, GATE_ENFORCEMENT_ERROR)` → `TrustGateDecision.from_boundaries` 产生 BLOCK。**fail-closed，不抛异常给调用方。** 接线后 wind_query 无需额外 try/except 包裹 enforcer。

### C.3 `_wrap_response` 调用顺序

正确顺序（参考 stock_analysis L453-479 模板）：
```
1. result, source_used 取得（现有逻辑）
2. qc = {...}（现有逻辑）
3. formatted = json.dumps({source, code, action, data: result}, ...)（现有 L1171）
4. raw = _wrap_response(qc, formatted)                    ← 先构造原始响应
5. decision = enforce_wind_query(action, code, result, source_used, chain)
6. return format_trust_gate_envelope(decision, raw)        ← gate 包裹
```

`format_trust_gate_envelope` 在 PASS 时保留原始 envelope + content（enforcer.py:168-174），在 BLOCK 时重建 envelope 从 allowlist（enforcer.py:176-204）。两者都不与 `_wrap_response` 产生重复 QC——`_wrap_response` 产生 `_qc`，`format_trust_gate_envelope` 只注入 `_trust_gate`（PASS）或重建 `_qc` 从 allowlist（BLOCK，无新增字段）。

### C.4 重复 QC 风险

PASS 路径：`_qc`（来自 _wrap_response）+ `_trust_gate`（新增）= 无重复。  
BLOCK 路径：`_qc` 从原始 allowlist 重建（enforcer.py:184-189），原始 `_qc` 被丢弃 = 无重复，但**原始 _qc 中的非 allowlist 字段会丢失**（这是设计意图，F-02）。

### C.5 "先返回后检查" 风险

当前 wind_query 在 L1174 直接 `return _wrap_response(...)`，无任何后续检查。接线必须将 return 移到 gate 调用之后（见 C.3 步骤 5-6）。不存在"检查在 return 之后"的现有代码，但接线时必须保证 gate 在 return 之前。

### C.6 已验证模板

`stock_analysis`(mcp_server.py:453-479) 已验证此接线模式：
```python
bundle = _admit_for_stock_analysis(data, qc=qc)            # build_evidence_bundle
if isinstance(bundle, BlockedEvidence):
    return _make_error_response(...)                       # BLOCK → error
if not authorize_task(requested_use, bundle.allowed_use):
    return _make_error_response(...)                         # 未授权 → error
formatted = format_stock_analysis_from_bundle(bundle, ...)  # 格式化
return _wrap_response(qc, formatted, incremental)           # 返回
```
wind_query 接线可复用此结构，区别在于 wind_query 用 `enforce_wind_query` + `format_trust_gate_envelope`（G2/G3 边界），stock_analysis 用 `build_evidence_bundle`（workflow 准入）。

**Gate C 结论：PASS。** 契约兼容，错误 fail-closed，顺序明确，模板已验证。

---

## Gate D：负控设计

### D.1 现有覆盖（enforcer 层）

| 测试 | 文件 | 覆盖 |
|---|---|---|
| `test_f02_block_envelope_no_data_leak` | test_trust_gate_phase1a.py:469 | BLOCK 不泄漏 provider 数据到 LLM |
| `test_crosscutting_fail_closed` | :376 | result=None → BLOCK（空结果不自动成功）|
| `test_vc01_completeness_missing_critical` | :95 | 关键维度缺失 → BLOCK |
| `test_c03_all_return_paths_gated` | :972 | 所有返回路径经 gate |
| `test_f03_decision_record_integrity` | :559 | 决策记录不可变 |
| `test_f04_future_timestamp_rejected` | :650 | 未来时间戳 → BLOCK |
| `test_lv01_replay_tushare_t3` | :288 | Tushare T3 降级重放 |

### D.2 任务要求的 6 项负控 vs 现状

| # | 要求 | 现状 | 缺口 |
|---|---|---|---|
| D1 | BLOCKED evidence 不得进入 LLM | enforcer 层 F-02 覆盖；**wind_query 路径未覆盖**（gate 未接线，无从测试） | wind_query 集成测试缺失 |
| D2 | PARTIAL 不得用于未授权用途 | `authorize_task` 单元覆盖；wind_query 不调用 authorize_task | wind_query 路径无 authorize_task |
| D3 | blocked_fields 不得进入 Prompt | `_strip_blocked_fields` 单元覆盖；wind_query 不剥离字段 | wind_query 路径不剥离 |
| D4 | fallback 不得绕过 Gate | **未覆盖** — 无测试验证 fallback source 仍经 gate | 完全缺失 |
| D5 | 空结果不得自动视为成功 | `test_crosscutting_fail_closed` 覆盖 enforcer；wind_query B3 分支 `status:"failure"` 但未经 gate | enforcer 覆盖，路径未覆盖 |
| D6 | 工具身份未知不得宣称已验证 | G1 未实现，无法测试；边界为"不实现 G1 不宣称" | G1 缺失（本轮不要求实现） |

### D.3 接线后须补充的负控（设计，不实现）

1. **wind_query 集成测试**：mock provider 返回 incomplete result，验证 `enforce_wind_query` 被调用且返回 BLOCK envelope。
2. **fallback gate 测试**：wind 降级到 tushare 成功，验证 tushare 结果仍经 `enforce_wind_query`。
3. **connect 分支豁免测试**：connect 不携带时敏数据，但应明确豁免规则（G3 已有 `G3_CONNECT_EXEMPT`，需集成验证）。
4. **空结果路径测试**：B3 分支 `not result` 应产生 gate BLOCK 而非仅 `_qc.status:"failure"`。

**Gate D 结论：PARTIAL。** enforcer 库层负控充分；wind_query 路径层负控完全缺失，须在接线时同步补充。

---

## Gate E：生产差异

### E.1 本地工作树 vs Git HEAD

```
git HEAD = b3774a8765415c434ac45c8c9c3be606776b885d
工作树修改：M mcp_server.py（仅删除 xueqiu_fetch 工具，未触及 wind_query gate 接线）
```
`git show HEAD:mcp_server.py | grep -c enforce_wind_query` = 0  
`grep -c enforce_wind_query mcp_server.py`（工作树）= 0  
**HEAD 与工作树在 wind_query gate 接线上等价：均未接线。**

### E.2 生产部署版本

根据 `reference_finance_suite_production_layout` / 688775 disposition (2026-10-13) / recon consolidated (2026-09-29)：

- 生产**不走 MCP**。生产消费路径为 HTTP `POST /api/analyze`（`app/routers/api.py`）。
- 生产 stock 路径：`RAW → formatter → LLM → post-LLM QC → display "Trust Gate"`（F-STOCK-01）。
- 生产 Trust Gate **架构性缺失**（F-PROD-BOUNDARY-01，PENDING C 复审）：`api.py:870-940` 无 `_qc`/`allowed_use`/`evidence_bundle`/`authorize_task`。
- 生产 MCP `mcp_server.py` 是否含 `trust_gate/` 模块：**last production pin = absent**（recon consolidated）。
- 生产身份：**NOT_REPINNED**（recon consolidated L26）。

### E.3 差异判定

| 维度 | 本地工作树 | Git HEAD | 生产（只读证据） |
|---|---|---|---|
| wind_query gate 接线 | 未接线 | 未接线 | 未接线（MCP 生产 pin=absent）|
| 生产 stock HTTP gate | N/A（本地无生产 api.py） | N/A | 架构性缺失（F-PROD-BOUNDARY-01）|
| trust_gate/ 模块存在 | 存在（库代码） | 存在 | absent（last pin）|

**Gate E 结论：INSUFFICIENT_EVIDENCE。** 本地与 HEAD 等价可核验；生产身份 NOT_REPINNED，无法将本地实现状态认定为生产状态。生产 MCP 与生产 HTTP 均无 gate，但生产路径与本地 MCP 是不同入口，不可直接类比。

---

## MCP_BYPASS_CODE_PATH

**CONFIRMED。** wind_query 5 个返回分支中，3 个数据出口（B1 connect / B3 空结果 / B4 成功）直接返回 `_wrap_response` 给 LLM，未经过 `enforce_wind_query`。2 个错误出口（B2/B5）返回 `_make_error_response`，亦无 gate 标注。

这是 PRE1 Q6 答案（YES）的代码层证实：MCP wind_query 路径即"工具身份未验证、QC 通过后仍允许 evidence 进入 LLM"的实际路径。

---

## PRODUCTION_GATE_STATUS

**ABSENT。** 两层证据：

1. **MCP 生产路径**：生产 `mcp_server.py` 的 `trust_gate/` 模块 last production pin = absent（recon consolidated）。即使本地已实现 trust_gate 库，生产 MCP 未部署该模块。
2. **HTTP 生产路径**：生产 `/api/analyze` stock 分支架构性缺失 Trust Gate（F-PROD-BOUNDARY-01，688775 disposition §3）。

生产环境两个入口（MCP + HTTP）均无 gate。本地 trust_gate 库实现不等于生产 gate 状态。

---

## PRE2_IMPLEMENTATION_READY

**CONDITIONAL。**

| 前置条件 | 状态 |
|---|---|
| enforcer 库实现完备（G2/G3 + fail-closed + 决策记录） | ✅ PASS |
| 接线契约兼容（签名/错误传播/顺序） | ✅ PASS（Gate C） |
| 已验证接线模板（stock_analysis L453-479） | ✅ PASS |
| wind_query 路径当前无 gate（需接线） | ❌ FAIL（Gate B） |
| wind_query 路径负控测试 | ❌ 缺失（Gate D） |
| 生产部署授权 | ❌ NOT_AUTHORIZED |
| G1 实现（本轮不要求） | ❌ NOT_IMPLEMENTED（独立 Sprint） |

库层 ready；路径层 NOT ready（需接线 + 负控补充）。接线本身是低风险（enforcer 已实现，stock_analysis 模板已验证），但**须 Owner 授权**且**须同步补充路径层负控**。

---

## FINAL_STATUS

```
BLOCKED
```

**理由：** 库层 Trust Gate 实现完备且接线契约兼容，但 wind_query 主路径全部数据出口绕过 enforcer（Gate B FAIL），路径层负控缺失（Gate D PARTIAL），生产状态不可核验（Gate E INSUFFICIENT_EVIDENCE）。

**解除阻塞条件（待 Owner 裁决）：**
1. 授权 GAP-1 接线：wind_query 5 个返回分支接入 `enforce_wind_query` + `format_trust_gate_envelope`（参考 stock_analysis L453-479 模板）。
2. 授权 GAP-4 负控补充：wind_query 集成测试 + fallback gate 测试 + connect 豁免测试 + 空结果路径测试。
3. 明确本轮不实现 G1（Source Identity），G1 作为独立后续 Sprint。
4. 生产部署授权独立于本轮（生产 MCP + HTTP 双路径均无 gate，是更大范围的独立议题）。

**本轮严格遵守执行限制：** 未修改代码、配置、测试；未部署、未提交 Git、未执行生产调用；未新增 G1 实现；未修改 Engram。完成研究，等待 Owner 裁决。
