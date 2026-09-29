"""Smoke tests for Trust Gate Runtime v0."""
from __future__ import annotations

import sys

from research_runtime.evidence_bundle import (
    BlockedEvidence,
    build_evidence_bundle,
    generate_section_body,
)


def _gateway_response(status: str, *, data_type: str = "quote", reason: str | None = None, data: dict | None = None, missing_fields: list[str] | None = None) -> dict:
    return {
        "ok": status != "failure",
        "symbol": "600519.SH",
        "data_type": data_type,
        "provider": "joinquant",
        "provider_tier": 2,
        "freshness": "delayed" if reason == "delayed_source" else "realtime",
        "as_of": "2026-03-01",
        "data": data or {},
        "_qc": {
            "status": status,
            "reason": reason,
            "missing_fields": missing_fields or [],
        },
    }


def test_full_quote() -> None:
    bundle = build_evidence_bundle(_gateway_response(
        "success",
        data={"price": 123.4, "volume": 10, "amount": 1000, "pe": 20},
    ))
    assert "valuation_analysis" in bundle.allowed_use
    assert bundle.evidence["price"] == 123.4


def test_partial_quote() -> None:
    bundle = build_evidence_bundle(_gateway_response(
        "partial",
        reason="delayed_source",
        data={"price": 123.4, "volume": 10, "amount": 1000, "pe": 20},
        missing_fields=["price", "volume", "amount"],
    ))
    assert bundle.allowed_use == ["fundamental_overview"]
    assert set(["price", "volume", "amount"]).issubset(bundle.blocked_fields)
    assert "price" not in bundle.evidence
    assert "volume" not in bundle.evidence
    assert "amount" not in bundle.evidence


def test_failure_blocks_all() -> None:
    """F1 (v0.3): failure + empty evidence → BlockedEvidence (no_admitted_evidence).

    Frozen reason precedence: P1 qc_failure > P2 no_allowed_use > P3 no_admitted_evidence.
    For status="failure", the upstream failure reason wins; here it surfaces as
    "qc_failure" (or bundle.reason from _qc.reason). BlockedEvidence is the
    canonical admission class — equivalent to the prior EvidenceBundle(empty=...)
    contract but with the new semantics.
    """
    bundle = build_evidence_bundle(_gateway_response(
        "failure",
        reason="all_providers_failed",
        data={"price": 123.4},
    ))
    assert isinstance(bundle, BlockedEvidence), (
        f"Expected BlockedEvidence for status=failure + empty evidence; "
        f"got {type(bundle).__name__}"
    )
    assert bundle.gate_status == "blocked"
    assert bundle.trust_status == "failure"
    assert bundle.blocked_fields == ["all"]
    # Reason precedence: P1 wins because trust_status=failure
    assert bundle.reason == "all_providers_failed"


def test_stock_analysis_partial_blocks_trading_decisions() -> None:
    bundle = build_evidence_bundle(_gateway_response(
        "partial",
        data_type="stock_analysis",
        reason="missing_fields",
        data={"business": "baijiu", "fund_flow": "inflow", "position_sizing": "high"},
        missing_fields=["fund_flow"],
    ))
    assert bundle.allowed_use == ["fundamental_overview"]
    for blocked in ["short_term_signal", "fund_flow", "position_sizing", "buy_sell_recommendation"]:
        assert blocked in bundle.blocked_fields
    assert "fund_flow" not in bundle.evidence
    assert "position_sizing" not in bundle.evidence


def test_research_report_prompt_boundary() -> None:
    gateway_response = _gateway_response(
        "partial",
        reason="delayed_source",
        data={"price": 123.4, "company": "Kweichow Moutai"},
        missing_fields=["price"],
    )
    bundle = build_evidence_bundle(gateway_response)
    prompt_input = generate_section_body(bundle)
    assert "company" in prompt_input["evidence"]
    assert "price" not in prompt_input["evidence"]
    try:
        generate_section_body(gateway_response)  # type: ignore[arg-type]
    except TypeError:
        return
    raise AssertionError("raw Gateway response must not be accepted by prompt boundary")


def main() -> int:
    tests = [
        test_full_quote,
        test_partial_quote,
        test_failure_blocks_all,
        test_stock_analysis_partial_blocks_trading_decisions,
        test_research_report_prompt_boundary,
    ]
    for test in tests:
        test()
        print(f"{test.__name__}: passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
