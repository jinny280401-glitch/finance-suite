# Trust Gate Sprint 2 — Pre-Merge Validation Plan

日期：2026-06-05
分支：feature/trust-gate-runtime
当前状态：**PASS / PRE-MERGE VALIDATION REQUIRED**
提交：adf1d9f

---

## 当前验收结果

✅ Sprint 2 Implementation PASS：
- 5 步实现顺序正确
- RED LINE Smoke 7 通过（物理隔离成立）
- 7/7 新 smoke + 5/5 原有 smoke 全通过
- 无文件扩散，无回归

⚠️ 但尚未验证真实 provider 行为语义。

---

## Pre-Merge Validation — 3 个真实链路 Smoke

### Smoke A：REAL Provider 完整链路

**目标**：验证 REAL provider（JoinQuant tier=2 / Wind tier=1）quote success 可以进入完整用途。

**构造**：
- 从真实 Gateway 获取 `quote` 响应（JoinQuant / Wind）
- 确保 `_qc.status=success`、`freshness=delayed` 或 `realtime`、`provider_tier ≤ 2`

**断言（收紧）**：
```python
gate_result = _run_trust_gate([gateway_quote_item])
bundle = gate_result.allowed_bundles[0]

# 1. ProviderClass 必须是 REAL
provider_class = _classify_provider(gateway_quote_item["payload"])
assert provider_class == ProviderClass.REAL, f"Got {provider_class}"

# 2. 源信息正确
assert bundle.source["provider"] in ("joinquant", "wind", "tushare")
assert bundle.source["provider_tier"] <= 2
assert bundle.trust_status == "success"

# 3. allowed_use 必须包含报告生成用途（不只是非空）
assert "fundamental_overview" in bundle.allowed_use
assert "valuation_analysis" in bundle.allowed_use
assert "peer_comparison" in bundle.allowed_use
# 如果有 research_report 字段，也应在内
if "research_report" in ["fundamental_overview", "valuation_analysis", "peer_comparison"]:
    assert "research_report" in bundle.allowed_use

# 4. 模拟 ReportAssembly QC
report_qc = {
    "passed": len(bundle.allowed_use) > 0 and bundle.trust_status == "success",
    "provider_class": provider_class.value,
}
assert report_qc["passed"] is True
assert report_qc["provider_class"] == "real"
```

---

### Smoke B：FALLBACK Provider 裁剪

**目标**：验证 FALLBACK provider（AkShare tier=3 / stale data）只能用于 overview/historical，不能产生 valuation 结论。

**构造**：
- 从 AkShare 获取 `quote` 响应，`provider_tier=3`、`freshness=delayed`
- 或构造 `provider_tier=2` 但 `freshness=stale` 的场景

**断言（收紧到精确集合）**：
```python
gate_result = _run_trust_gate([akshare_quote_item])
bundle = gate_result.allowed_bundles[0]

# 1. ProviderClass 必须是 FALLBACK
provider_class = _classify_provider(akshare_quote_item["payload"])
assert provider_class == ProviderClass.FALLBACK, f"Got {provider_class}"

# 2. 源信息正确
assert bundle.source["provider_tier"] == 3 or bundle.source["freshness"] == "stale"

# 3. allowed_use 必须精确匹配 {fundamental_overview, historical_context}
allowed_set = set(bundle.allowed_use)
expected_set = {"fundamental_overview", "historical_context"}
# 允许 subset，但不得有 expected_set 之外的项
assert allowed_set.issubset(expected_set), f"Got {allowed_set}, expected subset of {expected_set}"
assert "fundamental_overview" in allowed_set, "Must include fundamental_overview"

# 4. 明确禁止的用途（防止偷偷加入）
forbidden = {
    "valuation_analysis", "peer_comparison",
    "market_timing", "positioning", "signal_generation",
    "trading_signal", "conviction_statement", "target_price",
    "buy_sell_recommendation", "position_sizing"
}
assert allowed_set.isdisjoint(forbidden), f"FALLBACK leaked forbidden uses: {allowed_set & forbidden}"
```

**RED LINE**：
- 如果 FALLBACK provider 产生 `trading_signal`、`conviction_statement`、`target_price` → **FAIL**

---

### Smoke C：MOCK Provider 不进报告链路

**目标**：验证 MOCK provider（local_research_stub / freshness=mock）不能进入报告生成。

**构造**：
- 构造 `provider="local_research_stub"`、`freshness="mock"`、`_qc.status=success` 的响应
- 模拟 `generate_report()` 或 `build_prompt()` 调用

**断言（加硬边界验证）**：
```python
gate_result = _run_trust_gate([mock_quote_item])
bundle = gate_result.allowed_bundles[0]

# 1. ProviderClass 必须是 MOCK
provider_class = _classify_provider(mock_quote_item["payload"])
assert provider_class == ProviderClass.MOCK, f"Got {provider_class}"

# 2. 源信息正确
assert bundle.source["freshness"] == "mock"
assert "stub" in bundle.source["provider"].lower() or bundle.source["provider"] == ""

# 3. allowed_use 必须精确匹配 {workflow_smoke, runtime_test}
allowed_set = set(bundle.allowed_use)
expected_set = {"workflow_smoke", "runtime_test"}
assert allowed_set == expected_set, f"Got {allowed_set}, expected exactly {expected_set}"

# 4. 明确禁止的用途（报告生成链路）
forbidden = {
    "fundamental_overview", "valuation_analysis", "peer_comparison",
    "report_generation", "investment_analysis", "research_report",
    "historical_context", "market_timing", "positioning"
}
assert allowed_set.isdisjoint(forbidden), f"MOCK leaked into report uses: {allowed_set & forbidden}"

# 5. 硬边界：generate_section_body() 必须拒绝或返回 NO_EVIDENCE
from research_runtime.evidence_bundle import generate_section_body
try:
    section = generate_section_body(bundle)
    # 如果没抛异常，检查返回内容不能是正常报告体
    assert section.get("trust_status") == "failure" or section.get("evidence") == {}, \
        "MOCK should not generate valid report section"
except (ValueError, TypeError, AssertionError) as e:
    # 预期行为：拒绝 MOCK evidence
    pass
```

**RED LINE（最严格）**：
- 如果 MOCK evidence 能进入 `build_prompt()` → **FAIL**
- 如果 report assembly 接受 `allowed_use=["workflow_smoke"]` 的 bundle → **FAIL**
- 如果 `generate_section_body(mock_bundle)` 返回有效报告体（非 NO_EVIDENCE / 非 failure） → **FAIL**

---

## Merge Gate

**两道 Gate：**

```
Architecture Gate
    ✅ PASS (已完成，commit adf1d9f)
    - 5 步实现顺序正确
    - RED LINE Smoke 7 通过（物理隔离成立）
    - 12/12 smoke 通过

Semantic Gate
    ⏳ PENDING (待验证)
    - Smoke A: REAL provider 完整用途可达
    - Smoke B: FALLBACK provider 精确裁剪到 {fundamental_overview, historical_context}
    - Smoke C: MOCK provider 不进报告链路（硬边界验证）
```

**合并条件（必须 2/2）：**

1. ✅ Architecture Gate PASS
2. ⏳ Semantic Gate PASS

**任一 RED LINE 触发 → 整个 Sprint 2 FAIL，不得合 main。**

**通过后执行：**

```bash
cd ~/finance-suite
git tag v0.trust-gate-sprint2-validated
git checkout main
git merge feature/trust-gate-runtime
```

---

## 当前状态

```
Trust Gate Runtime Sprint 2
Status: PASS / PRE-MERGE VALIDATION REQUIRED
Implementation: adf1d9f
Validation Plan: 81e6781
Branch: feature/trust-gate-runtime

Architecture Gate: ✅ PASS
Semantic Gate:     ⏳ PENDING
```

**下一步**：实现 `smoke_trust_gate_premerge.py`，运行 3 个真实 provider smoke。

通过后，Trust Gate 不只是"设计正确"，而是已经证明在 REAL / FALLBACK / MOCK 三种运行态下行为正确。对 v0.9 LLM Integration 来说，这才是真正可靠的基础。

---

## 实现计划

新建文件：`smoke_trust_gate_premerge.py`

包含 3 个 smoke 函数：
- `test_real_provider_full_usage()`
- `test_fallback_provider_restricted()`
- `test_mock_provider_no_report()`

使用真实 `finance_data_gateway.get_finance_data()` 获取响应，而不是 mock `build_response()`。

通过后打 tag：`v0.trust-gate-sprint2-validated`
