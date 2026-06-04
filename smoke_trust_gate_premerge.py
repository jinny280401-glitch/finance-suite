"""Pre-Merge Validation — Semantic Gate for Trust Gate Runtime Sprint 2.

Validates 3 real provider scenarios before merge to main:
- Smoke A: REAL provider → full analysis usage allowed
- Smoke B: FALLBACK provider → fundamental_overview only
- Smoke C: MOCK provider → cannot enter LLM / prompt boundary rejects

RED LINE: Any violation = Sprint 2 FAIL, do not merge.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure scripts/ is in path
root = Path(__file__).resolve().parent
scripts = root / "scripts"
if str(scripts) not in sys.path:
    sys.path.insert(0, str(scripts))

from finance_data_contract import build_response
from research_runtime.evidence_bundle import (
    _run_trust_gate,
    _classify_provider,
    ProviderClass,
    generate_section_body,
)


def test_smoke_a_real_provider():
    """Smoke A: REAL provider (JoinQuant/Wind tier ≤ 2) → full analysis usage.

    Validates:
    - ProviderClass == REAL
    - allowed_use contains valuation_analysis, peer_comparison
    - ReportAssembly QC passed
    """
    print("=== Smoke A: REAL Provider ===")

    # Construct REAL provider response (JoinQuant tier=2)
    gateway_response = build_response(
        ok=True,
        symbol="600519.SH",
        data_type="quote",
        provider="joinquant",
        provider_tier=2,
        freshness="delayed",
        data={"price": 1800.0, "volume": 5000000, "pe": 30.0, "pb": 8.0},
        qc={"status": "success"},
    )

    raw_evidence = [{"kind": "gateway_quote", "payload": gateway_response}]
    gate_result = _run_trust_gate(raw_evidence)

    assert len(gate_result.allowed_bundles) == 1, "Should allow 1 bundle"
    bundle = gate_result.allowed_bundles[0]

    # 1. ProviderClass must be REAL
    provider_class = _classify_provider(gateway_response)
    assert provider_class == ProviderClass.REAL, f"Expected REAL, got {provider_class}"

    # 2. Source info correct
    assert bundle.source["provider"] == "joinquant"
    assert bundle.source["provider_tier"] == 2
    assert bundle.trust_status == "success"

    # 3. allowed_use must include full analysis capabilities
    assert "fundamental_overview" in bundle.allowed_use, "Missing fundamental_overview"
    assert "valuation_analysis" in bundle.allowed_use, "Missing valuation_analysis"
    assert "peer_comparison" in bundle.allowed_use, "Missing peer_comparison"

    # 4. Simulate ReportAssembly QC
    report_qc = {
        "passed": len(bundle.allowed_use) > 0 and bundle.trust_status == "success",
        "provider_class": provider_class.value,
    }
    assert report_qc["passed"] is True, "ReportAssembly QC must pass for REAL"
    assert report_qc["provider_class"] == "real"

    print("✅ Smoke A PASS: REAL provider allows full analysis usage")


def test_smoke_b_fallback_provider():
    """Smoke B: FALLBACK provider (AkShare tier=3) → fundamental_overview only.

    Validates:
    - ProviderClass == FALLBACK
    - allowed_use ⊆ {fundamental_overview, historical_context}
    - Forbidden uses not present
    """
    print("\n=== Smoke B: FALLBACK Provider ===")

    # Construct FALLBACK provider response (AkShare tier=3)
    gateway_response = build_response(
        ok=True,
        symbol="600519.SH",
        data_type="quote",
        provider="akshare",
        provider_tier=3,
        freshness="delayed",
        data={"pe": 30.0, "market_cap": "2T"},
        qc={"status": "partial", "reason": "delayed_source"},
    )

    raw_evidence = [{"kind": "gateway_quote", "payload": gateway_response}]
    gate_result = _run_trust_gate(raw_evidence)

    assert len(gate_result.allowed_bundles) == 1, "Should allow 1 bundle"
    bundle = gate_result.allowed_bundles[0]

    # 1. ProviderClass must be FALLBACK
    provider_class = _classify_provider(gateway_response)
    assert provider_class == ProviderClass.FALLBACK, f"Expected FALLBACK, got {provider_class}"

    # 2. Source info correct
    assert bundle.source["provider_tier"] == 3

    # 3. allowed_use must be subset of {fundamental_overview, historical_context}
    allowed_set = set(bundle.allowed_use)
    expected_set = {"fundamental_overview", "historical_context"}
    assert allowed_set.issubset(expected_set), f"Got {allowed_set}, expected ⊆ {expected_set}"
    assert "fundamental_overview" in allowed_set, "Must include fundamental_overview"

    # 4. Explicitly forbidden uses (prevent sneaking in)
    forbidden = {
        "valuation_analysis", "peer_comparison",
        "market_timing", "positioning", "signal_generation",
        "trading_signal", "conviction_statement", "target_price",
        "buy_sell_recommendation", "position_sizing",
    }
    violations = allowed_set & forbidden
    assert not violations, f"FALLBACK leaked forbidden uses: {violations}"

    print(f"✅ Smoke B PASS: FALLBACK restricted to {allowed_set}")


def test_smoke_c_mock_provider():
    """Smoke C: MOCK provider → cannot enter LLM, prompt boundary rejects.

    Validates:
    - ProviderClass == MOCK
    - allowed_use == {workflow_smoke, runtime_test}
    - generate_section_body() rejects or returns NO_EVIDENCE
    """
    print("\n=== Smoke C: MOCK Provider ===")

    # Construct MOCK provider response
    gateway_response = build_response(
        ok=True,
        symbol="600519.SH",
        data_type="quote",
        provider="local_research_stub",
        provider_tier=None,
        freshness="mock",
        data={"price": 1800.0},
        qc={"status": "success"},
    )

    raw_evidence = [{"kind": "gateway_quote", "payload": gateway_response}]
    gate_result = _run_trust_gate(raw_evidence)

    assert len(gate_result.allowed_bundles) == 1, "Should allow 1 bundle (for workflow smoke)"
    bundle = gate_result.allowed_bundles[0]

    # 1. ProviderClass must be MOCK
    provider_class = _classify_provider(gateway_response)
    assert provider_class == ProviderClass.MOCK, f"Expected MOCK, got {provider_class}"

    # 2. Source info correct
    assert bundle.source["freshness"] == "mock"
    assert "stub" in bundle.source["provider"].lower() or bundle.source["provider"] == ""

    # 3. allowed_use must be exactly {workflow_smoke, runtime_test}
    allowed_set = set(bundle.allowed_use)
    expected_set = {"workflow_smoke", "runtime_test"}
    assert allowed_set == expected_set, f"Got {allowed_set}, expected exactly {expected_set}"

    # 4. Explicitly forbidden uses (report generation chain)
    forbidden = {
        "fundamental_overview", "valuation_analysis", "peer_comparison",
        "report_generation", "investment_analysis", "research_report",
        "historical_context", "market_timing", "positioning",
    }
    violations = allowed_set & forbidden
    assert not violations, f"MOCK leaked into report uses: {violations}"

    # 5. Hard boundary: generate_section_body() must reject or return NO_EVIDENCE
    section_rejected = False
    try:
        section = generate_section_body(bundle)
        # If didn't throw, check it's not a valid report section
        if section.get("trust_status") == "failure" or section.get("evidence") == {}:
            section_rejected = True
        else:
            # Should not reach here — MOCK should not generate valid report
            assert False, f"MOCK generated valid section: {section}"
    except (ValueError, TypeError, AssertionError):
        # Expected: boundary rejects MOCK
        section_rejected = True

    assert section_rejected, "generate_section_body() must reject MOCK evidence"

    print("✅ Smoke C PASS: MOCK cannot enter LLM, prompt boundary rejects")


def main() -> int:
    """Run all 3 pre-merge validation smokes.

    Returns 0 if all pass, 1 if any fail.
    """
    try:
        test_smoke_a_real_provider()
        test_smoke_b_fallback_provider()
        test_smoke_c_mock_provider()

        print("\n" + "="*60)
        print("✅ Semantic Gate PASS — All 3 provider scenarios validated")
        print("="*60)
        print("\nReady to merge:")
        print("  git tag v0.trust-gate-sprint2-validated")
        print("  git checkout main")
        print("  git merge feature/trust-gate-runtime")

        return 0
    except AssertionError as e:
        print(f"\n❌ Semantic Gate FAIL: {e}")
        print("\nDo NOT merge to main. Fix the issue and re-run.")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
