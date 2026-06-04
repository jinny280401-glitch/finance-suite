"""Smoke tests for Trust Gate Runtime Integration v1."""
from __future__ import annotations

import json
import sys

from research_runtime.session import ResearchSession
from research_runtime.workflow import _run_trust_gate


def _gateway_item(status: str = "partial") -> dict:
    return {
        "kind": "gateway_quote",
        "source": "joinquant",
        "payload": {
            "ok": status != "failure",
            "symbol": "600519.SH",
            "data_type": "quote",
            "provider": "joinquant",
            "provider_tier": 2,
            "freshness": "delayed",
            "as_of": "2026-03-01",
            "data": {
                "price": 123.4,
                "volume": 100,
                "amount": 1000,
                "pe": 20,
            },
            "_qc": {
                "status": status,
                "reason": "delayed_source" if status == "partial" else "all_providers_failed",
                "missing_fields": ["price", "volume", "amount"] if status == "partial" else [],
            },
        },
    }


def test_raw_gateway_response_does_not_survive_gate() -> None:
    session = ResearchSession(symbol="600519.SH")
    result = _run_trust_gate([_gateway_item("partial")], session)
    assert result["has_any_allowed"] is True
    assert result["blocked_count"] == 0
    evidence = result["evidence"][0]
    serialized = json.dumps(evidence, ensure_ascii=False)
    assert "_qc" not in serialized
    assert "payload" not in serialized
    assert "price" not in evidence["evidence"]
    assert evidence["allowed_use"] == ["fundamental_overview"]
    assert set(["price", "volume", "amount"]).issubset(evidence["blocked_fields"])


def test_failure_gateway_response_is_blocked() -> None:
    session = ResearchSession(symbol="600519.SH")
    result = _run_trust_gate([_gateway_item("failure")], session)
    assert result["has_any_allowed"] is False
    assert result["allowed_count"] == 0
    assert result["blocked_count"] == 1
    assert result["evidence"] == []
    assert result["blocked_items"][0]["blocked_fields"] == ["all"]


def test_events_show_allow_and_block() -> None:
    session = ResearchSession(symbol="600519.SH")
    _run_trust_gate([_gateway_item("partial"), _gateway_item("failure")], session)
    event_types = [event.type for event in session.events]
    assert "trust_gate_started" in event_types
    assert "evidence_allowed" in event_types
    assert "evidence_blocked" in event_types
    assert "trust_gate_completed" in event_types


def main() -> int:
    tests = [
        test_raw_gateway_response_does_not_survive_gate,
        test_failure_gateway_response_is_blocked,
        test_events_show_allow_and_block,
    ]
    for test in tests:
        test()
        print(f"{test.__name__}: passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
