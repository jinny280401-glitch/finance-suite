"""Task Authorization Boundary — unit tests.

Contract under test (Owner AdJ 2026-09-29):
    requested_use × allowed_use → AUTHORIZED | BLOCKED

Fail-closed semantics:
    - requested_use undetermined (None/empty/non-str) → BLOCKED
    - allowed_use empty/malformed                       → BLOCKED
    - requested_use ∉ allowed_use                       → BLOCKED
    - requested_use ∈ allowed_use                       → AUTHORIZED

The decision is exact set membership — never substring / fuzzy / embedding.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from research_runtime.task_authorization import authorize_task


# ============================================================
# AUTHORIZED — requested_use ∈ allowed_use
# ============================================================

def test_subset_membership_authorized():
    assert authorize_task("fundamental_overview", ["fundamental_overview"]) is True


def test_membership_among_multiple_authorized():
    allowed = ["fundamental_overview", "valuation_analysis", "peer_comparison"]
    assert authorize_task("peer_comparison", allowed) is True


# ============================================================
# BLOCKED — requested_use ∉ allowed_use (exceeds authorization)
# ============================================================

def test_superset_request_blocked_syn010():
    # SYN-010: PARTIAL QC + position_sizing request, allowed_use only
    # fundamental_overview → BLOCK (the canonical production-gap case).
    assert authorize_task("position_sizing", ["fundamental_overview"]) is False


def test_superset_request_blocked_syn011():
    # SYN-011: target_price request against descriptive-only allowed_use.
    assert authorize_task("target_price", ["fundamental_overview", "event_extraction"]) is False


def test_trading_decision_fields_never_authorized():
    allowed = ["fundamental_overview", "valuation_analysis"]
    for field in ("short_term_signal", "fund_flow", "position_sizing", "buy_sell_recommendation"):
        assert authorize_task(field, allowed) is False, f"{field} must never be authorized"


# ============================================================
# BLOCKED — empty allowed_use
# ============================================================

def test_empty_allowed_use_blocked():
    assert authorize_task("fundamental_overview", []) is False


# ============================================================
# BLOCKED — requested_use undetermined (fail closed)
# ============================================================

def test_none_requested_use_fail_closed():
    assert authorize_task(None, ["fundamental_overview"]) is False


def test_empty_string_requested_use_fail_closed():
    assert authorize_task("", ["fundamental_overview"]) is False


def test_whitespace_only_requested_use_fail_closed():
    assert authorize_task("   ", ["fundamental_overview"]) is False


def test_non_str_requested_use_fail_closed():
    assert authorize_task(123, ["fundamental_overview"]) is False
    assert authorize_task(["fundamental_overview"], ["fundamental_overview"]) is False


# ============================================================
# BLOCKED — malformed allowed_use (fail closed, no substring trap)
# ============================================================

def test_none_allowed_use_fail_closed():
    assert authorize_task("fundamental_overview", None) is False


def test_str_allowed_use_not_substring_matched():
    # allowed_use must be a collection; a bare string must not be treated as
    # substring-matchable (that would be fuzzy, not exact membership).
    assert authorize_task("fundamental", "fundamental_overview") is False


# ============================================================
# Normalization — whitespace only, no case folding
# ============================================================

def test_whitespace_stripped():
    assert authorize_task("  fundamental_overview  ", ["fundamental_overview"]) is True


def test_case_sensitive_exact():
    # Exact membership: a case-mismatched value is not the same TaskUse.
    assert authorize_task("Fundamental_Overview", ["fundamental_overview"]) is False


# ============================================================
# Integration — real bundle.allowed_use shape (SYN-010 semantics)
# ============================================================

def test_integration_real_allowed_use_blocks_position_sizing():
    from research_runtime.evidence_bundle import build_evidence_bundle

    bundle = build_evidence_bundle({
        "ok": True,
        "data_type": "stock_analysis",
        "provider": "wind",
        "provider_tier": 1,
        "freshness": "stale",
        "data": {"realtime": {"price": 100.0}},
        "_qc": {"status": "partial", "reason": None},
    })
    # PARTIAL stock_analysis → allowed_use == ["fundamental_overview"]
    assert bundle.allowed_use == ["fundamental_overview"]
    assert authorize_task("fundamental_overview", bundle.allowed_use) is True
    assert authorize_task("position_sizing", bundle.allowed_use) is False


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
