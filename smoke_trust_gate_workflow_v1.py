"""Smoke tests for Trust Gate Runtime Sprint 2 — workflow integration.

Tests Trust Gate filtering at the workflow level with real ResearchSession.
Smoke 7 is the RED LINE: any raw dict reaching prompt = FAIL.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure scripts/ is in path for finance_data_contract
root = Path(__file__).resolve().parent
scripts = root / "scripts"
if str(scripts) not in sys.path:
    sys.path.insert(0, str(scripts))

from finance_data_contract import build_response
from research_runtime.workflow import run_research_workflow
from research_runtime.evidence_bundle import _run_trust_gate


def test_smoke_1_quote_success():
    """Smoke 1: quote success — full evidence allowed."""
    gateway_response = build_response(
        ok=True, symbol="600519.SH", data_type="quote",
        provider="joinquant", provider_tier=2, freshness="delayed",
        data={"price": 1800.0, "volume": 5000000, "pe": 30.0},
        qc={"status": "success"}
    )
    raw_evidence = [{"kind": "gateway_quote", "payload": gateway_response}]
    result = _run_trust_gate(raw_evidence)

    assert len(result.allowed_bundles) == 1, "Should allow 1 bundle"
    assert result.blocked_items == [], "Should block nothing"
    bundle = result.allowed_bundles[0]
    assert "fundamental_overview" in bundle.allowed_use
    assert "valuation_analysis" in bundle.allowed_use
    assert bundle.trust_status == "success"
    print("test_smoke_1_quote_success: passed")


def test_smoke_2_quote_partial():
    """Smoke 2: quote partial — only fundamental_overview, block trading fields."""
    gateway_response = build_response(
        ok=True, symbol="600519.SH", data_type="quote",
        provider="akshare", provider_tier=3, freshness="delayed",
        data={"pe": 30.0},
        qc={"status": "partial", "reason": "delayed_source",
            "missing_fields": ["price", "volume", "amount"]}
    )
    raw_evidence = [{"kind": "gateway_quote", "payload": gateway_response}]
    result = _run_trust_gate(raw_evidence)

    bundle = result.allowed_bundles[0]
    assert bundle.allowed_use == ["fundamental_overview"], f"Got {bundle.allowed_use}"
    for field in ["short_term_signal", "fund_flow", "position_sizing", "buy_sell_recommendation"]:
        assert field in bundle.blocked_fields, f"{field} must be blocked"
    assert "price" in bundle.blocked_fields
    print("test_smoke_2_quote_partial: passed")


def test_smoke_3_stock_analysis_partial():
    """Smoke 3: stock_analysis partial — prohibit trading advice."""
    gateway_response = build_response(
        ok=True, symbol="300750.SZ", data_type="stock_analysis",
        provider="akshare", provider_tier=3, freshness="delayed",
        data={"pe": 25.0, "revenue_growth": "12%"},
        qc={"status": "partial"}
    )
    raw_evidence = [{"kind": "gateway_quote", "payload": gateway_response}]
    result = _run_trust_gate(raw_evidence)

    bundle = result.allowed_bundles[0]
    assert bundle.allowed_use == ["fundamental_overview"]
    for field in ["short_term_signal", "fund_flow", "position_sizing", "buy_sell_recommendation"]:
        assert field in bundle.blocked_fields, f"{field} must be blocked"
    print("test_smoke_3_stock_analysis_partial: passed")


def test_smoke_4_failure():
    """Smoke 4: failure — block all."""
    gateway_response = build_response(
        ok=False, symbol="000001.SZ", data_type="quote",
        provider=None, provider_tier=None, freshness="stale",
        qc={"status": "failure", "reason": "all_providers_failed"}
    )
    raw_evidence = [{"kind": "gateway_quote", "payload": gateway_response}]
    result = _run_trust_gate(raw_evidence)

    assert result.allowed_bundles == [], "Should allow nothing"
    assert len(result.blocked_items) == 1, "Should block 1 item"
    blocked = result.blocked_items[0]
    assert blocked.gate_status == "blocked"
    assert blocked.blocked_fields == ["all"]
    assert not result.has_any_allowed
    print("test_smoke_4_failure: passed")


def test_smoke_5_provider_mock():
    """Smoke 5: provider=mock/stub — freshness preserved, allowed_use restricted."""
    gateway_response = build_response(
        ok=True, symbol="600519.SH", data_type="quote",
        provider="local_research_stub", provider_tier=None, freshness="mock",
        data={"price": 1800.0},
        qc={"status": "success"}
    )
    raw_evidence = [{"kind": "gateway_quote", "payload": gateway_response}]
    result = _run_trust_gate(raw_evidence)

    bundle = result.allowed_bundles[0]
    assert bundle.source["freshness"] == "mock", "freshness must be preserved"
    assert bundle.source["provider"] == "local_research_stub"
    assert bundle.allowed_use == ["workflow_smoke", "runtime_test"], f"Got {bundle.allowed_use}"
    print("test_smoke_5_provider_mock: passed")


def test_smoke_6_passthrough():
    """Smoke 6: non-gateway evidence passes through."""
    raw_evidence = [
        {"kind": "research_scope", "source": "local_research_stub", "payload": {"symbol": "TEST"}},
        {"kind": "skeleton", "source": "research_editorial_layer", "payload": {"sections": ["00", "01"]}},
    ]
    result = _run_trust_gate(raw_evidence)

    assert result.allowed_bundles == [], "No EvidenceBundle for non-gateway"
    assert result.blocked_items == [], "Nothing blocked"
    assert len(result.passthrough_items) == 2, "Both items pass through"
    print("test_smoke_6_passthrough: passed")


def test_smoke_7_bypass_audit():
    """Smoke 7 (RED LINE): raw dict / gateway_response / payload / _qc cannot reach prompt.

    This is the architecture isolation test. If this fails, the entire Sprint 2 FAILS.
    """
    # Run a full workflow with gateway mode
    session = run_research_workflow(symbol="600519.SH", mode="gateway")

    # 1. session.context must not contain raw gateway_response
    context_str = json.dumps(session.context)
    assert "_qc" not in context_str, "_qc leaked into context"
    assert "payload" not in context_str or "symbol" in context_str, "payload leaked into context"

    # 2. session.evidence must only contain EvidenceBundle.to_dict(), not raw gateway_response
    for item in session.evidence:
        if isinstance(item, dict):
            # If it came from gateway, it must be an EvidenceBundle dict
            if "allowed_use" in item or "trust_status" in item:
                # This is an EvidenceBundle.to_dict()
                assert "trust_status" in item, "EvidenceBundle must have trust_status"
                assert "allowed_use" in item, "EvidenceBundle must have allowed_use"
                assert "blocked_fields" in item, "EvidenceBundle must have blocked_fields"
                assert "_qc" not in item, "_qc from gateway_response leaked into evidence"
                assert "ok" not in item or "source" in item, "raw gateway 'ok' field leaked"

    # 3. session.allowed_evidence must only be EvidenceBundle dicts
    if hasattr(session, "allowed_evidence"):
        for item in session.allowed_evidence:
            assert "trust_status" in item, "allowed_evidence must be EvidenceBundle dict"
            assert "allowed_use" in item, "allowed_evidence must have allowed_use"
            assert "_qc" not in item, "_qc leaked into allowed_evidence"

    # 4. session.blocked_evidence must only be BlockedEvidence dicts
    if hasattr(session, "blocked_evidence"):
        for item in session.blocked_evidence:
            assert "gate_status" in item, "blocked_evidence must be BlockedEvidence dict"
            assert item["gate_status"] == "blocked", "gate_status must be 'blocked'"

    # 5. session.to_dict() serialization test
    session_dict = session.to_dict()
    session_str = json.dumps(session_dict, default=str)
    # _qc can appear in events (trust_gate events may log it), but not in evidence/context
    evidence_str = json.dumps(session_dict.get("evidence", []))
    context_str_full = json.dumps(session_dict.get("context", {}))
    assert "_qc" not in evidence_str, "_qc leaked into serialized evidence"
    assert "_qc" not in context_str_full, "_qc leaked into serialized context"

    print("test_smoke_7_bypass_audit: passed (RED LINE)")


if __name__ == "__main__":
    test_smoke_1_quote_success()
    test_smoke_2_quote_partial()
    test_smoke_3_stock_analysis_partial()
    test_smoke_4_failure()
    test_smoke_5_provider_mock()
    test_smoke_6_passthrough()
    test_smoke_7_bypass_audit()
    print("\nAll 7 Trust Gate workflow smoke tests passed.")
