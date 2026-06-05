"""Smoke test: ResearchSession.add_evidence_bundle() rejects raw gateway dicts.

This test validates that raw Gateway Response payloads cannot bypass Trust Gate
and enter session.evidence directly.
"""
from __future__ import annotations

import sys

from research_runtime.session import ResearchSession
from research_runtime.evidence_bundle import build_evidence_bundle


def _raw_gateway_response() -> dict:
    """Simulate a raw Gateway Response dict with _qc field."""
    return {
        "ok": True,
        "symbol": "600519.SH",
        "data_type": "quote",
        "provider": "joinquant",
        "provider_tier": 2,
        "freshness": "realtime",
        "as_of": "2026-06-06",
        "data": {"price": 1850.0, "volume": 5000000, "pe": 30.0},
        "_qc": {
            "status": "success",
            "completeness": 1.0,
        },
    }


def test_raw_dict_rejected() -> None:
    """Test that add_evidence_bundle rejects raw gateway dict."""
    session = ResearchSession(symbol="600519.SH")
    raw_dict = _raw_gateway_response()

    try:
        session.add_evidence_bundle(raw_dict)  # type: ignore[arg-type]
        raise AssertionError("add_evidence_bundle must reject raw dict")
    except TypeError as e:
        assert "EvidenceBundle" in str(e), f"Error message should mention EvidenceBundle: {e}"
        print("test_raw_dict_rejected: passed (TypeError raised as expected)")


def test_evidence_bundle_accepted() -> None:
    """Test that add_evidence_bundle accepts EvidenceBundle."""
    session = ResearchSession(symbol="600519.SH")
    raw_gateway = _raw_gateway_response()
    bundle = build_evidence_bundle(raw_gateway)

    session.add_evidence_bundle(bundle)

    assert len(session.evidence) == 1, "Should add 1 evidence item"
    evidence_item = session.evidence[0]
    assert isinstance(evidence_item, dict), "Evidence should be serialized to dict"
    assert "trust_status" in evidence_item, "Evidence must have trust_status"
    assert "allowed_use" in evidence_item, "Evidence must have allowed_use"
    assert "_qc" not in str(evidence_item), "_qc must not survive into evidence"
    print("test_evidence_bundle_accepted: passed")


def test_direct_assignment_still_possible() -> None:
    """Test that direct assignment bypasses guard (known limitation).

    This documents that session.evidence is still a list field, so direct
    assignment (session.evidence = [...]) bypasses add_evidence_bundle().
    The workflow must use add_evidence_bundle() consistently.
    """
    session = ResearchSession(symbol="600519.SH")
    raw_dict = _raw_gateway_response()

    # Direct assignment still works (limitation of dataclass field)
    session.evidence = [raw_dict]

    assert len(session.evidence) == 1
    assert "_qc" in str(session.evidence[0]), "Direct assignment bypasses guard"
    print("test_direct_assignment_still_possible: passed (documents known limitation)")


def main() -> int:
    tests = [
        test_raw_dict_rejected,
        test_evidence_bundle_accepted,
        test_direct_assignment_still_possible,
    ]
    for test in tests:
        test()
    print("\nAll session guard smoke tests passed.")
    print("Note: add_evidence_bundle() guards the API, but direct assignment remains possible.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
