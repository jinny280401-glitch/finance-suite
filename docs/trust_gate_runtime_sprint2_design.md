# Trust Gate Runtime Integration — Sprint 2 Design

日期：2026-06-05
分支：feature/trust-gate-runtime
状态：Design Only — 无代码变更，无生产影响

---

## 1. Runtime 入口拦截点

当前 `run_research_workflow()` 在 `EVIDENCE_RETRIEVAL` 之后直接进入 `CONTEXT_BUILDING`，
Gateway 的原始响应（`payload` 字段）直接存入 `session.evidence`，没有经过 Trust Gate。

```
当前链路（v0.2，有问题）：

EVIDENCE_RETRIEVAL
    _retrieve_evidence() → [{ "kind": "gateway_quote", "payload": gateway_response }]
↓
CONTEXT_BUILDING
    _build_context() → { "evidence_count": ..., ... }  ← 未经过 Trust Gate
↓
QC
↓
prompt / LLM（未来）
```

Sprint 2 在 `EVIDENCE_RETRIEVAL` 和 `CONTEXT_BUILDING` 之间插入新阶段：

```
新链路（Sprint 2 目标）：

EVIDENCE_RETRIEVAL
    _retrieve_evidence() → raw_evidence_items（gateway_response 原始响应）
↓
TRUST_GATE                          ← 新增阶段
    _run_trust_gate()
    → allowed_bundles: list[EvidenceBundle]
    → blocked_items: list[BlockedEvidence]
    → 写入 trust_gate_started / evidence_allowed / evidence_blocked 事件
↓
CONTEXT_BUILDING
    _build_context() 只接收 allowed_bundles，不再接触 gateway_response
↓
QC
↓
prompt（未来）← 只接收 EvidenceBundle，不接收 gateway_response
```

**拦截函数**：`_run_trust_gate(raw_evidence: list[dict]) -> TrustGateResult`

位置：`research_runtime/workflow.py`，在 `_retrieve_evidence()` 调用之后、`_build_context()` 之前。

---

## 2. Trust Gate 输入

### 2a. 来源

`_retrieve_evidence()` 返回 `raw_evidence_items`，每一项结构：

```python
{
    "kind": "gateway_quote",          # or "research_scope", "skeleton"
    "source": "finance_data_gateway",
    "ok": True,                        # 已有字段
    "as_of": "2026-06-05T...",
    "payload": {                       # ← 这是 build_response() 产物
        "ok": True,
        "symbol": "600519.SH",
        "data_type": "quote",
        "provider": "joinquant",
        "provider_tier": 2,
        "freshness": "delayed",
        "as_of": "...",
        "data": { ... },
        "_qc": {
            "status": "partial",
            "reason": "delayed_source",
            "missing_fields": ["price", "volume", "amount"],
            ...
        }
    }
}
```

### 2b. 进入 Trust Gate 的字段

Trust Gate 读取 `payload`，使用以下字段（来自 `finance_data_contract.build_response()`）：

| 字段 | 用途 |
|---|---|
| `payload._qc.status` | success / partial / failure 判断 |
| `payload._qc.reason` | partial/failure 具体原因 |
| `payload._qc.missing_fields` | 缺失字段推导 blocked_fields |
| `payload._qc.freshness` | realtime / delayed / stale / cached |
| `payload.provider` | 标注 source 来源 |
| `payload.provider_tier` | 标注信源等级 |
| `payload.data_type` | quote / stock_analysis / financials / consensus |
| `payload.data` | 原始数据，Trust Gate 执行后剥离 blocked_fields |

### 2c. 不进入 Trust Gate 的 evidence

`kind` 不是 `gateway_*` 的 item（如 `research_scope`、`skeleton`）直接透传，不经过 gate。
它们不包含 `_qc`，不是 financial data，无需 Trust Gate 过滤。

---

## 3. Trust Gate 输出

### 3a. 允许 Evidence（`allowed_bundles`）

每个通过 gate 的 item 转换为 `EvidenceBundle`（已由 `evidence_bundle.py` 定义）：

```python
EvidenceBundle(
    evidence={...},          # 剥离 blocked_fields 后的数据
    allowed_use=["fundamental_overview"],
    blocked_fields=["short_term_signal", "fund_flow", "position_sizing", ...],
    trust_status="partial",
    reason="delayed_source",
    source={
        "symbol": "600519.SH",
        "data_type": "quote",
        "provider": "joinquant",
        "provider_tier": 2,
        "freshness": "delayed",
        "as_of": "...",
    }
)
```

`gate_status = "allowed"` 条件：`trust_status in ("success", "partial")` 且 `allowed_use` 非空。

### 3b. 阻断 Evidence（`blocked_items`）

```python
@dataclass(frozen=True)
class BlockedEvidence:
    gate_status: str = "blocked"       # 固定值
    reason: str                        # qc_failure / all_providers_failed / unsupported_data_type
    blocked_fields: list[str]          # ["all"] 表示整体阻断
    source: dict[str, Any]             # symbol / data_type / provider / as_of
    trust_status: str                  # 来自 _qc.status
```

`gate_status = "blocked"` 条件：`trust_status == "failure"` 或 `allowed_use == []`。

### 3c. TrustGateResult 聚合

```python
@dataclass
class TrustGateResult:
    allowed_bundles: list[EvidenceBundle]
    blocked_items: list[BlockedEvidence]
    gate_events: list[dict]     # 供 RuntimeEventLog 写入
    
    @property
    def has_any_allowed(self) -> bool:
        return len(self.allowed_bundles) > 0
```

---

## 4. LLM 前的硬边界

以下规则必须在 `_run_trust_gate()` 内强制执行，不允许在 `build_prompt()` 内临时绕过：

### 规则 1：`gate_status=blocked` 不得进入 prompt

```python
# 进入 prompt 的唯一路径
def build_prompt(allowed_bundles: list[EvidenceBundle]) -> str:
    # 函数签名只接受 EvidenceBundle，不接受 gateway_response / raw dict
    ...
```

如果 `allowed_bundles` 为空（全部阻断），workflow 进入 `NO_EVIDENCE` 状态，不调用 LLM。

### 规则 2：`partial` 只能用于 `allowed_use` 白名单用途

| `allowed_use` | 允许生成 | 禁止生成 |
|---|---|---|
| `fundamental_overview` | 基本面概览、历史数据描述 | 短线信号、资金流、仓位建议、买卖建议 |
| `valuation_analysis` | PE/PB/市值分析 | 目标价、评级摘要 |
| `expectation_context` | 分析师预期描述 | 评级汇总、目标价 |

`stock_analysis=PARTIAL` 时：`allowed_use=["fundamental_overview"]`，`blocked_fields` 包含全部 `TRADING_DECISION_FIELDS`。

### 规则 3：`provider=fallback` / `confidence=mock` 不得对外宣称 `real`

Gateway `freshness` 字段的允许传播规则：

| freshness 值 | 允许对 LLM 说的描述 | 禁止说的描述 |
|---|---|---|
| `realtime` | "实时数据" | — |
| `delayed` | "延迟数据"、"截至 {as_of}" | "实时数据" |
| `stale` | "历史数据"、"截至 {as_of}" | "实时数据"、"延迟数据" |
| `mock` / `cached` | "模拟数据，仅用于测试" | "实时数据"、"延迟数据" |

如果 `source.provider` 是 mock/stub，`EvidenceBundle.source["freshness"]` 必须保留原值，
不得在 prompt 模板中被替换为 `realtime`。

---

## 5. Smoke 计划

新增文件：`smoke_trust_gate_workflow_v1.py`

所有 smoke 的驱动方式：构造 `build_response()` 产物作为 mock gateway response，
传入 `_run_trust_gate()`，断言 `TrustGateResult` 的内容。不调用真实 provider，不调用 LLM。

### Smoke 1：`quote success` — 全量 Evidence 允许

```python
gateway_response = build_response(
    ok=True, symbol="600519.SH", data_type="quote",
    provider="joinquant", provider_tier=2, freshness="delayed",
    data={"price": 1800.0, "volume": 5000000},
    qc={"status": "success"}
)
result = _run_trust_gate([{"kind": "gateway_quote", "payload": gateway_response}])

assert len(result.allowed_bundles) == 1
assert result.blocked_items == []
assert "fundamental_overview" in result.allowed_bundles[0].allowed_use
assert result.allowed_bundles[0].trust_status == "success"
```

### Smoke 2：`quote partial` — PARTIAL 只允许 fundamental_overview，阻断 trading 字段

```python
gateway_response = build_response(
    ok=True, symbol="600519.SH", data_type="quote",
    provider="akshare", provider_tier=3, freshness="delayed",
    data={"pe": 30.0},
    qc={"status": "partial", "reason": "delayed_source",
        "missing_fields": ["price", "volume", "amount"]}
)
result = _run_trust_gate([{"kind": "gateway_quote", "payload": gateway_response}])

bundle = result.allowed_bundles[0]
assert bundle.allowed_use == ["fundamental_overview"]
assert "short_term_signal" in bundle.blocked_fields
assert "fund_flow" in bundle.blocked_fields
assert "position_sizing" in bundle.blocked_fields
assert "price" in bundle.blocked_fields
```

### Smoke 3：`stock_analysis partial` — 禁止交易建议

```python
gateway_response = build_response(
    ok=True, symbol="300750.SZ", data_type="stock_analysis",
    provider="akshare", provider_tier=3, freshness="delayed",
    data={"pe": 25.0, "revenue_growth": "12%"},
    qc={"status": "partial"}
)
result = _run_trust_gate([{"kind": "gateway_quote", "payload": gateway_response}])

bundle = result.allowed_bundles[0]
assert bundle.allowed_use == ["fundamental_overview"]
for field in ["short_term_signal", "fund_flow", "position_sizing", "buy_sell_recommendation"]:
    assert field in bundle.blocked_fields, f"{field} must be blocked"
```

### Smoke 4：`failure` — 全阻断

```python
gateway_response = build_response(
    ok=False, symbol="000001.SZ", data_type="quote",
    provider=None, provider_tier=None, freshness="stale",
    qc={"status": "failure", "reason": "all_providers_failed"}
)
result = _run_trust_gate([{"kind": "gateway_quote", "payload": gateway_response}])

assert result.allowed_bundles == []
assert len(result.blocked_items) == 1
assert result.blocked_items[0].gate_status == "blocked"
assert result.blocked_items[0].blocked_fields == ["all"]
assert not result.has_any_allowed
```

### Smoke 5：`provider=mock/stub` — 不得宣称 real

```python
gateway_response = build_response(
    ok=True, symbol="600519.SH", data_type="quote",
    provider="local_research_stub", provider_tier=None, freshness="mock",
    data={"price": 1800.0},
    qc={"status": "success"}
)
result = _run_trust_gate([{"kind": "gateway_quote", "payload": gateway_response}])

bundle = result.allowed_bundles[0]
assert bundle.source["freshness"] == "mock"
assert bundle.source["provider"] == "local_research_stub"
# freshness 字段不得被 override 为 realtime/delayed
assert bundle.source["freshness"] not in ("realtime", "delayed", "stale")
```

### Smoke 6：`non-gateway evidence 透传` — skeleton/scope 不经过 gate

```python
raw_items = [
    {"kind": "research_scope", "source": "local_research_stub", "payload": {...}},
    {"kind": "skeleton", "source": "research_editorial_layer", "payload": {...}},
]
result = _run_trust_gate(raw_items)

# 非 gateway_* 的 item 直接透传，不经过 EvidenceBundle 转换
assert result.allowed_bundles == []
assert result.blocked_items == []
assert len(result.passthrough_items) == 2
```

---

## 6. 明确不做

- 不接真实 LLM（`generate_section_body()` 保持当前 stand-in 实现）
- 不改前端（`app/` 不触碰）
- 不改 provider（`scripts/ifind_data.py`、`scripts/macro_data.py` 等不触碰）
- 不合 main（本分支保持独立直到 Sprint 2 验收）
- 不碰 iFinD 分支遗留文件（`mcp_server.py` 工作区修改不 add 不 commit）
- 不做 `blocked_fields` 的 prompt 模板层执行（prompt builder 是 Sprint 3 的工作）
- 不添加新 provider（iFinD financials/consensus 是 Sprint 3 之后的事）

---

## 7. Sprint 2 验收口径

通过条件（全部 6 条 smoke PASS）：

1. `gate_status=blocked` 的 evidence 不进入 `allowed_bundles`
2. `_qc.status=partial` 的 quote 只允许 `fundamental_overview`
3. `stock_analysis=PARTIAL` 的 `blocked_fields` 包含全部 `TRADING_DECISION_FIELDS`
4. `_qc.status=failure` 产出 `blocked_items`，`has_any_allowed=False`
5. `provider=mock/stub` 的 `freshness` 原值保留，不被覆盖
6. 非 gateway evidence 透传，不进入 `allowed_bundles` 也不进入 `blocked_items`

完成后打 tag：`v0.trust-gate-runtime-sprint2`
