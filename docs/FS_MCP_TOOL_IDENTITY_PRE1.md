# FS-MCP-TOOL-IDENTITY-PRE1

**执行者：** CC002 / MAC-002  
**日期：** 2026-11-18  
**模式：** STRICT_READ_ONLY  
**状态：** RESEARCH_COMPLETE / IMPLEMENTATION_NOT_AUTHORIZED  
**NEXT_GATE：** OWNER_REVIEW

---

## 完成状态矩阵

| 维度 | 状态 | 证据定位 |
|---|---|---|
| TOOL_IDENTITY_BINDING | **NOT_IMPLEMENTED** | MCP 注册仅靠函数名；无独立身份绑定机制 |
| PROVIDER_VERIFICATION | **NOT_IMPLEMENTED** | G1 合同在 4 处代码中标注 "planned, not yet implemented" |
| EVIDENCE_PROVENANCE | **PARTIAL** | `source_used` 字符串被传入 `_qc`；但为提供方自报，无加密绑定 |
| TRUST_GATE_INTEGRATION | **NOT_IMPLEMENTED** | `wind_query` 从不调用 `enforce_wind_query`；Trust Gate 是库代码，未接入 MCP 路径 |
| NEGATIVE_TEST_COVERAGE | **NOT_IMPLEMENTED** | 无任何工具名冲突、提供方欺骗、跨服务器身份混淆的测试 |
| IMPLEMENTATION_AUTHORIZATION | NO | — |

---

## 1. 当前调用链结构

### MCP 路径（主路径）

```
Agent (Claude Code / OpenClaw)
  ↓  MCP stdio 协议
mcp_server.py  FastMCP("finance-suite")
  ↓  @mcp.tool() 装饰器注册（函数名即工具名）
wind_query(action, code, max_peers)   [mcp_server.py:977]
  ↓  for source in chain: runners[source]()
  wind_data / tushare_data / joinquant_data / akshare   [mcp_server.py:1131-1145]
  ↓  source_used = source  （提供方自报字符串）
  _wrap_response(qc, formatted)        [mcp_server.py:1174]
  ↓  返回 {"_qc": {...}, "source": source_used, ...}
LLM（直接消费 MCP 工具返回值）
```

**关键缺口：Trust Gate enforcer 存在但未接入。**  
`trust_gate/enforcer.py` 中 `enforce_wind_query()` 注释写道：  
> "This is THE single entry point for wind_query Trust Gate enforcement.  
>  No wind_query response reaches LLM context without passing through here."

这是 **契约级断言**，不是实现事实。`mcp_server.py` 对 `enforce_wind_query` 和
`format_trust_gate_envelope` 的调用次数均为 **零**（grep 验证）。

### research_runtime 路径（workflow 路径，非 MCP 直接路径）

```
workflow.py → _run_trust_gate(raw_evidence)
  ↓  build_evidence_bundle(payload)   [evidence_bundle.py:160]
  ↓  EvidenceBundle / BlockedEvidence
LLM（通过 Research Runtime）
```

此路径有 Trust Gate 接入，但不覆盖 MCP 直接工具调用。

### 其他入口

- `server_scripts/`（HTTP API）：独立于 MCP，使用不同的信任边界，不在本次核验范围。
- `scripts/finance_data_gateway.py`：独立网关脚本，有自己的 QC 逻辑，不经过 `mcp_server.py`。

---

## 2. 工具身份与提供方绑定机制

### 2.1 MCP 工具注册层

```python
mcp = FastMCP("finance-suite", ...)   # mcp_server.py:68

@mcp.tool()
def wind_query(action: str, ...) -> str:   # mcp_server.py:976
```

- 工具名由 Python 函数名派生（`wind_query`）。
- 服务器名 `"finance-suite"` 通过 stdio 协议声明；MCP 客户端（Claude Code）将其写入
  `.mcp.json` / `claude_desktop_config.json` 配置，并以此路由进程。
- **协议层面无加密身份绑定**：任何以相同名称注册的进程，在运行时与合法进程不可区分。

### 2.2 提供方身份（provider identity）

`wind_query` 内部：

```python
for source in chain:                    # mcp_server.py:1138
    candidate = runners[source]()
    if candidate:
        result = candidate
        source_used = source            # 1143: 字符串赋值，提供方自报
        break

qc = {
    "sources": [source_used],           # 1166
    ...
}
```

`source_used` 是循环变量字符串（`"wind"` / `"tushare"` / `"joinquant"` / `"akshare"`），
由执行代码自己赋值，**没有任何独立于名称的验证机制**。

### 2.3 G1 合同状态

以下 4 处代码明确标注 G1 未实现：

| 文件 | 行 | 原文 |
|---|---|---|
| `trust_gate/enforcer.py` | 5 | "Contract G1 (Source Identity) is planned, not yet implemented." |
| `trust_gate/enforcer.py` | 99 | "Note: Contract G1 (Source Identity) is planned but not yet in Phase 1a" |
| `trust_gate/__init__.py` | 5 | "Contract G1 (Source Identity): planned, not yet implemented." |
| `trust_gate/boundaries/__init__.py` | 7 | "Contract G1 (Source Identity): planned, not yet implemented in Phase 1a." |
| `trust_gate/boundaries/g2_field_integrity.py` | 11 | "Note: Contract G1 (Source Identity) is planned but not yet implemented" |

---

## 3. Trust Gate 入口检查结果

### 3.1 Phase 1a 实现边界

当前 Trust Gate（`trust_gate/enforcer.py`）只激活两个边界：

| 边界 | 检查内容 | 状态 |
|---|---|---|
| G2 Field Integrity | 关键维度是否存在且非空 | IMPLEMENTED（库代码） |
| G3 Freshness | 时间戳是否过期 | IMPLEMENTED（库代码） |
| **G1 Source Identity** | **提供方身份是否可信** | **NOT_IMPLEMENTED** |

### 3.2 MCP 路径未调用 Trust Gate

```
mcp_server.py grep "enforce_wind_query"    → 0 matches
mcp_server.py grep "format_trust_gate_envelope" → 0 matches
mcp_server.py grep "build_evidence_bundle"      → 0 matches
```

`wind_query`（mcp_server.py:977-1178）直接返回 `_wrap_response(qc, formatted)`，
绕过了全部 Trust Gate 逻辑。LLM 收到的是原始 `{"_qc": {...}, "source": ..., "data": ...}`，
而非 `EvidenceBundle`。

### 3.3 `stock_analysis` 的 `authorize_task` 调用

```python
from research_runtime.task_authorization import authorize_task   # mcp_server.py:460
```

`stock_analysis` 工具确实调用了 `authorize_task(required_use_set, allowed_use)` 做
用途集合子集检查，这是 Task Authorization 的简化路径。但：

1. 这是 `task_authorization.py` 中的顶层函数（集合运算），**不是** 完整的
   `AdmissionAuthority` / `AuthorizationAuthority` 路径。
2. `task_authorization.py` 自注明：  
   > "NOT wired into production caller plumbing (Unit 2)."
3. `wind_query` 不调用 `authorize_task`。

---

## 4. 风险矩阵及证据定位

### Q1：工具名称是否可能被其他提供方复用或覆盖？

**结论：POSSIBLE（配置层）**

MCP 工具路由依赖 `.mcp.json` / `claude_desktop_config.json` 中的进程绑定。如果配置
被修改指向不同进程，该进程只需声明服务器名 `"finance-suite"` 并暴露同名工具，即可在
运行时接管调用链。协议层无进程签名或证书验证。这是 MCP 协议本身的设计约束，非代码缺陷，
但系统未在运行时做任何补偿措施。

**证据：** `mcp_server.py:68` — `FastMCP("finance-suite")` 名称为纯字符串声明。

### Q2：工具提供方身份是否具有独立于工具名称的验证机制？

**结论：NOT_IMPLEMENTED**

无。`source_used` 字符串由工具函数内部循环赋值（提供方自报）。G1 未实现。
没有加密签名、进程证书、或可信路径绑定。

**证据：** `mcp_server.py:1143`；`trust_gate/enforcer.py:5,99`。

### Q3：工具身份验证失败时，系统是否 fail-closed？

**结论：NOT_APPLICABLE**

因为 G1 不存在，"身份验证失败" 这个事件无法发生。G2/G3 失败时 Trust Gate 确实
fail-closed（`enforcer.py:107-123` 的异常处理路径产生 BLOCK 决策）——但这个路径
在 MCP 主调用链中从未被触发（见 3.2）。

### Q4：Evidence Bundle 是否能追溯到实际执行工具及其提供方？

**结论：PARTIAL**

- `evidence_bundle.py:build_evidence_bundle()` 从 gateway_response 中提取 `provider`、
  `provider_tier`、`freshness`、`as_of` 写入 `source` 字段（`evidence_bundle.py:184-191`）。
- 但这些字段来自 gateway_response 本身，是提供方自报的值，没有独立验证。
- `wind_query` 直接返回原始 JSON，不走 `build_evidence_bundle`；LLM 收到的 `source_used`
  字符串可追溯性依赖代码逻辑的诚实性，而非任何加密或身份绑定。

### Q5：当前 Trust Gate 能否阻断来源身份不可信的 evidence？

**结论：NOT_IMPLEMENTED**

Trust Gate 只检查字段完整性（G2）和时间戳新鲜度（G3）。没有 G1，Trust Gate
对提供方身份完全透明——只要数据字段齐全且不过时，来源不可信的数据也会通过。

**证据：** `trust_gate/boundaries/` 目录只有 `g2_field_integrity.py` 和 `g3_freshness.py`，
无 `g1_*.py`。

### Q6：是否存在工具身份未验证、但 QC 通过后仍允许 evidence 进入 LLM 的路径？

**结论：YES，主路径（MCP `wind_query`）即是此路径**

```
任意实现了 wind_data / tushare_data 接口的提供方进程
  ↓  声明 FastMCP("finance-suite") + def wind_query(...)
  ↓  字段齐全（G2 准则）+ 时间戳合理（G3 准则）
  ↓  mcp_server.py _wrap_response(qc, formatted)
  ↓  Trust Gate 从未被调用
LLM 收到数据，无任何来源身份验证
```

这不是假设场景；这是当前 `mcp_server.py:977-1178` 的实际执行路径。

---

## 5. 现有测试覆盖情况

### 已覆盖

| 测试文件 | 覆盖内容 | 评价 |
|---|---|---|
| `test_trust_gate_phase1a.py` | G2 字段完整性、G3 新鲜度、决策记录不可变性、BLOCK 时不泄漏数据 | 对 Trust Gate 库逻辑覆盖良好 |
| `test_admission_authenticity.py` | AdmissionAuthority 对象身份认证（A/B/C/D/E...P 轴）、伪造记录拒绝、跨权威隔离 | 对 task_authorization 单元覆盖充分 |
| `test_evidence_provenance.py` | P1 source_chain 在 BLOCK 时保留、P2 衍生估值标注、P3 衍生数据不升级 QC 状态 | 对 evidence provenance 语义有针对性覆盖 |
| `test_search_gate_integration.py` | 搜索路径的 Trust Gate 集成 | 覆盖搜索工具路径 |

### 未覆盖（本研究发现的缺口）

| 缺口 | 风险 |
|---|---|
| `wind_query` MCP 路径绕过 Trust Gate | 无测试检验 `enforce_wind_query` 是否实际被调用 |
| 工具名称冲突 / 同名服务器注册 | 无任何负控测试 |
| 提供方身份欺骗（伪造 `source_used`） | G1 不存在，测试无法验证的东西 |
| `task_authorization` 完整路径未接入生产 | `AdmissionAuthority` 路径有单元测试但无集成测试 |
| `stock_analysis` 的 `authorize_task` 调用是否实际阻断了非法用途 | 有单元覆盖，但 `wind_query` 路径完全缺失 |

---

## 6. 缺口与最小修复建议（仅设计，不授权实现）

### GAP-1（高风险）：`wind_query` MCP 路径绕过 Trust Gate

**现状：** `mcp_server.py:wind_query` 直接返回 `_wrap_response`，从未调用 `enforce_wind_query`。  
**设计方向：**
```python
# 在 _wrap_response 之前插入（伪代码）：
decision = enforce_wind_query(action, code, result, source_used, chain, retrieved_at)
return format_trust_gate_envelope(decision, _wrap_response(qc, formatted))
```
`enforce_wind_query` 和 `format_trust_gate_envelope` 已存在于 `trust_gate/enforcer.py`，
接线成本低；主要工作是决定 G2/G3 阻断时 `wind_query` 的回退行为。

### GAP-2（高风险）：G1（Source Identity）合同未实现

**现状：** 4 处 "planned, not yet implemented"。  
**设计方向：** 最小 G1 可以是：
1. 在 `mcp_server.py` 启动时将允许的提供方集合写入 Trust Gate 配置。
2. `enforce_wind_query` 检查 `source_used` 是否在配置的白名单内，否则 BLOCK。
3. 不需要加密签名即可覆盖最主要的配置错误场景（工具注册错误提供方名称）。

更严格的 G1 需要进程身份或 MCP 层面的签名机制，超出当前架构范围。

### GAP-3（中风险）：`task_authorization` 完整路径（Unit 2）未接入

**现状：** `AdmissionAuthority` 单元完整，但 `task_authorization.py` 自注明
"NOT wired into production caller plumbing (Unit 2)"。  
**设计方向：** Unit 2 接线需要明确谁是合法的 `AdmissionIssuerCapability` 持有者，
并在 MCP tool handler 中用 `AdmissionRecord` 替代当前的简单 `authorize_task` 调用。
这是架构级决策，须 Owner 授权后进入单独 Sprint。

### GAP-4（低风险）：负控测试缺失

**设计方向：** 至少需要：
1. 一个测试验证 `wind_query` 的返回值经过了 `enforce_wind_query`（可以通过 mock 注入）。
2. 一个测试验证伪造 `source_used="wind"` 的响应不能以 `source_type="primary"` 通过。

---

## 7. 是否建议进入 PRE2

**建议：YES，但需先关闭 GAP-1**

| 条件 | 状态 |
|---|---|
| 研究证据完整 | ✅ |
| 风险已定性 | ✅ |
| GAP-1（Trust Gate 未接入 MCP 主路径）已记录 | ✅ |
| GAP-2（G1 未实现）已记录 | ✅ |
| GAP-1 修复设计已存在（enforcer.py 已实现，仅需接线） | ✅ |
| Owner 授权实现 | ❌ 待 PRE2 授权 |

PRE2 建议范围：
1. 授权 GAP-1 接线（`wind_query` → `enforce_wind_query`），不引入新的 G1 实现。
2. 授权 GAP-4 负控测试补充。
3. G1 实现和 Unit 2 接线作为独立后续 Sprint，不阻塞 PRE2。

---

## 附：逐层标注汇总

```
Tool Name (工具名)
  ↓
  注册机制：FastMCP 函数名派生 → NOT_PROVEN（无身份绑定）
Provider Identity (提供方身份)
  ↓
  G1 合同：NOT_IMPLEMENTED（4 处代码标注）
Tool Authorization (工具调用权限)
  ↓
  stock_analysis: authorize_task() 调用 → PARTIAL（简化路径，非完整 Unit 2）
  wind_query: 无任何授权检查 → NOT_IMPLEMENTED
Evidence Provenance (证据来源字段)
  ↓
  source_used 字符串传入 _qc → PARTIAL（自报，无加密绑定）
  build_evidence_bundle source 字段 → PARTIAL（workflow 路径，非 MCP 路径）
Trust Gate Admission (Trust Gate 准入)
  ↓
  workflow 路径（_run_trust_gate）→ PARTIAL（有 G2/G3，无 G1）
  MCP wind_query 路径 → NOT_IMPLEMENTED（从未调用 enforce_wind_query）
LLM
  ↓
  当前：直接消费 mcp_server _wrap_response 输出（Trust Gate 旁路）
```
