# Trust Gate Runtime v0

日期：2026-06-05

## 1. 边界

Trust Gate Runtime v0 只做 Gateway Response 到 Evidence Bundle 的转换。

不做：

- 不接新 Provider。
- 不扩 iFinD。
- 不改 Gateway。
- 不改 QC。
- 不接真实 LLM。

## 2. 执行位置

Trust Gate 必须在 prompt 构建前执行。

```text
retrieve_gateway_data()
↓
build_evidence_bundle()
↓
generate_section_body(evidence_bundle)
↓
call_llm()
```

禁止让 `generate_section_body()` 接受 raw Gateway Response。

## 3. v0 实现

实现文件：

```text
research_runtime/evidence_bundle.py
```

核心对象：

```python
EvidenceBundle(
    evidence={},
    allowed_use=[],
    blocked_fields=[],
    trust_status="partial",
    reason="delayed_source",
)
```

核心函数：

```python
build_evidence_bundle(gateway_response)
generate_section_body(evidence_bundle)
```

其中 `generate_section_body()` 是 prompt boundary 的最小替身，用于验证接口不接受 raw Gateway Response。

## 4. 5 个验收样例

Smoke 文件：

```text
smoke_trust_gate_runtime_v0.py
```

用例 1：FULL Quote

- `allowed_use` 包含 `valuation_analysis`
- `price` 可见

用例 2：PARTIAL Quote

- missing `price/volume/amount`
- `allowed_use=["fundamental_overview"]`
- `blocked_fields` 包含 `price/volume/amount`
- Evidence 删除 `price/volume/amount`

用例 3：FAILURE

- `allowed_use=[]`
- `blocked_fields=["all"]`
- LLM 不收到数据

用例 4：`stock_analysis=PARTIAL`

- 只允许 `fundamental_overview`
- 禁止短线判断、资金流判断、仓位建议、买卖建议

用例 5：Research Report Prompt Boundary

- Evidence 进入 prompt
- Gateway raw data 不进入 prompt
- raw Gateway Response 传给 prompt boundary 会抛 `TypeError`

## 5. Sprint 2 验收口径

Sprint 2 的目标不是接 iFinD financials / consensus，而是证明：

```text
Registry + Route Policy + Trust Contract
```

足以承载新数据能力。如果不够，优先修 Contract，不硬接 Provider。

通过 Trust Gate Runtime v0 后，Research Runtime 的下一步才是把真实 section workflow 改为只消费 Evidence Bundle。

## 6. v1 Integration 红线

Trust Gate Runtime Integration v1 只检查一件事：

```text
现有 Research Runtime / Workflow / Market Context 是否还有路径能绕过 EvidenceBundle 直接进入 LLM
```

验收红线：

- raw provider data 进入 prompt：FAIL
- raw gateway response 进入 prompt：FAIL
- `ok=true` response 直接进入 prompt：FAIL
- HTTP 200 response 直接进入 prompt：FAIL
- `_qc.status=partial` 未过滤数据进入 prompt：FAIL

Runtime 的 gateway evidence 必须先经过 `build_evidence_bundle()`；`session.evidence` 中不应保留 raw `_qc` 或 raw `payload`。
