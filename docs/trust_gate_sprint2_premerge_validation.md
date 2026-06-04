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

**断言**：
```python
gate_result = _run_trust_gate([gateway_quote_item])
bundle = gate_result.allowed_bundles[0]

assert bundle.source["provider"] in ("joinquant", "wind", "tushare")
assert bundle.source["provider_tier"] <= 2
assert bundle.trust_status == "success"
assert "fundamental_overview" in bundle.allowed_use
assert "valuation_analysis" in bundle.allowed_use
assert "peer_comparison" in bundle.allowed_use
# REAL provider 不应被 ProviderClass.FALLBACK 裁剪
```

---

### Smoke B：FALLBACK Provider 裁剪

**目标**：验证 FALLBACK provider（AkShare tier=3 / stale data）只能用于 overview/historical，不能产生 valuation 结论。

**构造**：
- 从 AkShare 获取 `quote` 响应，`provider_tier=3`、`freshness=delayed`
- 或构造 `provider_tier=2` 但 `freshness=stale` 的场景

**断言**：
```python
gate_result = _run_trust_gate([akshare_quote_item])
bundle = gate_result.allowed_bundles[0]

assert bundle.source["provider_tier"] == 3 or bundle.source["freshness"] == "stale"
assert bundle.allowed_use == ["fundamental_overview"]
# ProviderClass.FALLBACK 应裁剪掉 valuation_analysis / peer_comparison
assert "valuation_analysis" not in bundle.allowed_use
assert "peer_comparison" not in bundle.allowed_use
```

**RED LINE**：
- 如果 FALLBACK provider 产生 `trading_signal`、`conviction_statement`、`target_price` → **FAIL**

---

### Smoke C：MOCK Provider 不进报告链路

**目标**：验证 MOCK provider（local_research_stub / freshness=mock）不能进入报告生成。

**构造**：
- 构造 `provider="local_research_stub"`、`freshness="mock"`、`_qc.status=success` 的响应
- 模拟 `generate_report()` 或 `build_prompt()` 调用

**断言**：
```python
gate_result = _run_trust_gate([mock_quote_item])
bundle = gate_result.allowed_bundles[0]

assert bundle.source["freshness"] == "mock"
assert bundle.allowed_use == ["workflow_smoke", "runtime_test"]
# MOCK 不得包含任何报告生成用途
assert "fundamental_overview" not in bundle.allowed_use
assert "valuation_analysis" not in bundle.allowed_use
assert "report_generation" not in bundle.allowed_use
```

**RED LINE**：
- 如果 MOCK evidence 能进入 `build_prompt()` → **FAIL**
- 如果 report assembly 接受 `allowed_use=["workflow_smoke"]` 的 bundle → **FAIL**

---

## Merge Gate

通过条件（3/3）：

1. ✅ Smoke A：REAL provider 完整用途可达
2. ✅ Smoke B：FALLBACK provider 裁剪生效，不产生 trading signal / valuation conclusion
3. ✅ Smoke C：MOCK provider 不进报告链路

**任一 RED LINE 触发 → 整个 Sprint 2 FAIL，不得合 main。**

---

## 实现计划

新建文件：`smoke_trust_gate_premerge.py`

包含 3 个 smoke 函数：
- `test_real_provider_full_usage()`
- `test_fallback_provider_restricted()`
- `test_mock_provider_no_report()`

使用真实 `finance_data_gateway.get_finance_data()` 获取响应，而不是 mock `build_response()`。

通过后打 tag：`v0.trust-gate-sprint2-validated`
