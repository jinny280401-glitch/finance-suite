"""GAP-4: wind_query MCP entry-level Trust Gate integration tests.

Owner-authorized negative controls (GAP-4, 2026-11-18):
  NC-1  BLOCKED evidence does not reach LLM (data stripped from BLOCK envelope)
  NC-2  PARTIAL evidence not used for unauthorized purpose (allowed_use gating)
  NC-3  blocked_fields do not appear in BLOCK envelope
  NC-4  fallback source still goes through gate (not bypassed)
  NC-5  empty / None result does not auto-pass (→ BLOCK)
  NC-6  Connect exemption is explicit (G3_CONNECT_EXEMPT) + non-connect without
        timestamp BLOCKs (not silently passes)

Scope: mcp_server._enforce_trust_gate_or_block() + _TRUST_GATE_AVAILABLE flag.
No real provider calls. No production smoke.
"""
from __future__ import annotations

import json
import sys
import os
from datetime import datetime, timezone, timedelta

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import mcp_server
from trust_gate.enforcer import enforce_wind_query, format_trust_gate_envelope
from trust_gate.decision import GateVerdict


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _fresh_stock() -> dict:
    """Minimal complete+fresh stock snapshot that passes G2+G3."""
    return {
        "price": 1850.5,
        "pe": 32.5,
        "pb": 12.1,
        "market_cap": 22000,
        "roe": 28.3,
        "trade_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }


def _raw_response(qc: dict, data: dict) -> str:
    return json.dumps({"_qc": qc}) + "\n\n" + json.dumps(data)


# ============================================================
# NC-1: BLOCKED evidence does not reach LLM
# ============================================================

def test_nc1_blocked_evidence_stripped():
    """NC-1: When enforce_wind_query returns BLOCK, provider data values must not
    appear in the returned string — they must not reach the LLM.
    """
    # Incomplete stock: missing pe, pb, market_cap, roe → G2_CRITICAL_DIMENSION_MISSING
    incomplete = {"price": 9999.88}
    qc = {"status": "success", "completeness": 0.2, "sources": ["wind"],
          "fallback_source": None, "missing_dimensions": [], "stale_data": []}
    raw = _raw_response(qc, incomplete)

    result = mcp_server._enforce_trust_gate_or_block(
        action="stock", code="600519.SH",
        result=incomplete, source_used="wind", raw_response=raw,
    )
    envelope = json.loads(result.split("\n\n", 1)[0])

    # Must be BLOCK
    assert envelope["_trust_gate"]["overall_verdict"] == "BLOCK", (
        "NC-1: incomplete stock must BLOCK"
    )
    # Provider data value must not appear anywhere
    assert "9999.88" not in result, (
        "NC-1: provider data value 9999.88 must not appear in BLOCK output"
    )
    # _trust_gate must be present for audit
    assert "_trust_gate" in envelope, "NC-1: _trust_gate must be in envelope"


# ============================================================
# NC-2: PARTIAL evidence not used for unauthorized purpose
# ============================================================

def test_nc2_partial_allowed_use_restricted():
    """NC-2: build_evidence_bundle with partial status restricts allowed_use
    to ['fundamental_overview'], blocking position_sizing and valuation_analysis.
    """
    from research_runtime.evidence_bundle import build_evidence_bundle, EvidenceBundle, BlockedEvidence

    gateway_response = {
        "data_type": "stock_analysis",
        "data": {"price": 100.0, "pe": 15.0},
        "_qc": {
            "status": "partial",
            "reason": "delayed_source",
            "missing_fields": ["fund_flow"],
        },
        "provider": "tushare",
        "provider_tier": 2,
        "freshness": "delayed",
        "symbol": "600519.SH",
    }

    bundle = build_evidence_bundle(gateway_response)
    assert isinstance(bundle, EvidenceBundle), "NC-2: partial status should produce EvidenceBundle"
    assert "fundamental_overview" in bundle.allowed_use, (
        "NC-2: partial should allow fundamental_overview"
    )
    assert "position_sizing" not in bundle.allowed_use, (
        "NC-2: partial must NOT allow position_sizing"
    )
    assert "valuation_analysis" not in bundle.allowed_use, (
        "NC-2: partial must NOT allow valuation_analysis"
    )


# ============================================================
# NC-3: blocked_fields do not appear in BLOCK envelope
# ============================================================

def test_nc3_blocked_fields_not_in_envelope():
    """NC-3: When gate BLOCKs, the BLOCK envelope must not contain any
    provider-data values that were in blocked_fields.
    """
    # Stale stock: complete fields but old timestamp → G3 BLOCK
    old_date = (datetime.now(timezone.utc) - timedelta(days=10)).strftime("%Y-%m-%d")
    stale = {
        "price": 7777.77,
        "pe": 32.5,
        "pb": 12.1,
        "market_cap": 22000,
        "roe": 28.3,
        "trade_date": old_date,
    }
    qc = {"status": "success", "completeness": 1.0, "sources": ["wind"],
          "fallback_source": None, "missing_dimensions": [], "stale_data": []}
    raw = _raw_response(qc, stale)

    result = mcp_server._enforce_trust_gate_or_block(
        action="stock", code="600519.SH",
        result=stale, source_used="wind", raw_response=raw,
        retrieved_at=_now_iso(),
    )
    envelope = json.loads(result.split("\n\n", 1)[0])

    # G3 stale → BLOCK
    assert envelope["_trust_gate"]["overall_verdict"] == "BLOCK", (
        "NC-3: stale data (10d old) must BLOCK"
    )
    # Provider data value must not appear
    assert "7777.77" not in result, (
        "NC-3: blocked price value must not appear in BLOCK output"
    )


# ============================================================
# NC-4: fallback source still goes through gate (not bypassed)
# ============================================================

def test_nc4_fallback_not_bypass_gate():
    """NC-4: A fallback provider result (tushare after wind fails) still goes
    through _enforce_trust_gate_or_block — the gate is not skipped for fallbacks.
    """
    # Incomplete fallback result (missing critical G2 dimensions)
    fallback_incomplete = {"price": 1850.5}  # only price, missing pe/pb/market_cap/roe
    qc = {"status": "partial", "completeness": 0.2, "sources": ["tushare"],
          "fallback_source": "joinquant", "missing_dimensions": ["pe", "pb"], "stale_data": []}
    raw = _raw_response(qc, fallback_incomplete)

    result = mcp_server._enforce_trust_gate_or_block(
        action="stock", code="600519.SH",
        result=fallback_incomplete, source_used="tushare", raw_response=raw,
        chain=["wind", "tushare", "joinquant"],
    )
    envelope = json.loads(result.split("\n\n", 1)[0])

    # Must have _trust_gate — gate was invoked, not bypassed
    assert "_trust_gate" in envelope, (
        "NC-4: fallback result must have _trust_gate (gate not bypassed)"
    )
    # Incomplete fallback → BLOCK (G2_CRITICAL_DIMENSION_MISSING)
    assert envelope["_trust_gate"]["overall_verdict"] == "BLOCK", (
        "NC-4: incomplete fallback result must BLOCK"
    )
    # Provider data not leaked
    assert "1850.5" not in result, "NC-4: provider data must not appear in fallback BLOCK"


def test_nc4_complete_fallback_passes_gate():
    """NC-4b: A complete, fresh fallback result passes gate (gate not bypassed,
    just PASS rather than BLOCK).
    """
    complete_fallback = _fresh_stock()
    qc = {"status": "success", "completeness": 1.0, "sources": ["tushare"],
          "fallback_source": "joinquant", "missing_dimensions": [], "stale_data": []}
    raw = _raw_response(qc, complete_fallback)

    result = mcp_server._enforce_trust_gate_or_block(
        action="stock", code="600519.SH",
        result=complete_fallback, source_used="tushare", raw_response=raw,
        chain=["wind", "tushare"],
        retrieved_at=_now_iso(),
    )
    envelope = json.loads(result.split("\n\n", 1)[0])

    assert "_trust_gate" in envelope, "NC-4b: complete fallback must have _trust_gate"
    assert envelope["_trust_gate"]["overall_verdict"] == "PASS", (
        "NC-4b: complete+fresh fallback must PASS gate"
    )
    # Data preserved on PASS
    assert "1850.5" in result, "NC-4b: PASS must preserve provider data"


# ============================================================
# NC-5: empty / None result does not auto-pass
# ============================================================

def test_nc5_empty_result_blocks():
    """NC-5: None result (all providers failed) must produce a BLOCK decision,
    not silently pass as success.
    """
    qc = {"status": "failure", "completeness": 0, "sources": [],
          "fallback_source": "akshare", "missing_dimensions": ["stock"], "stale_data": []}
    raw = json.dumps({"_qc": qc}) + "\n\n"

    result = mcp_server._enforce_trust_gate_or_block(
        action="stock", code="600519.SH",
        result=None, source_used="", raw_response=raw,
        chain=["wind", "tushare", "joinquant"],
    )
    envelope = json.loads(result.split("\n\n", 1)[0])

    assert "_trust_gate" in envelope, "NC-5: None result must have _trust_gate"
    assert envelope["_trust_gate"]["overall_verdict"] == "BLOCK", (
        "NC-5: None result must BLOCK, not auto-pass"
    )
    # Verify G2_NO_RESULT reason code
    boundaries = envelope["_trust_gate"]["boundaries"]
    g2_blocks = [b for b in boundaries if b["boundary_id"] == "G2" and b["verdict"] == "BLOCK"]
    assert g2_blocks, "NC-5: G2 must BLOCK with G2_NO_RESULT"
    assert g2_blocks[0]["reason_code"] == "G2_NO_RESULT", (
        f"NC-5: expected G2_NO_RESULT, got {g2_blocks[0]['reason_code']}"
    )


def test_nc5_empty_dict_result_blocks():
    """NC-5b: Empty dict result also BLOCKs (no fields = no critical dimensions)."""
    qc = {"status": "failure", "completeness": 0, "sources": [],
          "fallback_source": None, "missing_dimensions": [], "stale_data": []}
    raw = json.dumps({"_qc": qc}) + "\n\n{}"

    result = mcp_server._enforce_trust_gate_or_block(
        action="stock", code="000001.SZ",
        result={}, source_used="", raw_response=raw,
    )
    envelope = json.loads(result.split("\n\n", 1)[0])

    assert envelope["_trust_gate"]["overall_verdict"] == "BLOCK", (
        "NC-5b: empty dict result must BLOCK"
    )


# ============================================================
# NC-6: Connect exemption is explicit (G3_CONNECT_EXEMPT)
# ============================================================

def test_nc6_connect_exempt_explicit():
    """NC-6a: connect action is explicitly exempt from freshness (G3_CONNECT_EXEMPT),
    not silently exempt. The exemption must appear in the decision boundaries.
    """
    # connect action has its own dimension set in G2 (wind/tushare/joinquant/akshare keys)
    conn_result = {
        "wind": True, "tushare": True, "joinquant": False, "akshare": True,
        "connected": True, "priority": "Wind → Tushare → JoinQuant → AkShare",
    }
    qc = {"status": "success", "completeness": 1.0, "sources": ["wind", "tushare", "akshare"],
          "fallback_source": None, "missing_dimensions": [], "stale_data": []}
    raw = _raw_response(qc, conn_result)

    result = mcp_server._enforce_trust_gate_or_block(
        action="connect", code="",
        result=conn_result, source_used="", raw_response=raw,
    )
    envelope = json.loads(result.split("\n\n", 1)[0])

    assert "_trust_gate" in envelope, "NC-6a: connect must have _trust_gate"
    # G3 must explicitly record the exemption
    boundaries = envelope["_trust_gate"]["boundaries"]
    g3_boundaries = [b for b in boundaries if b["boundary_id"] == "G3"]
    assert g3_boundaries, "NC-6a: connect must have a G3 boundary"
    assert g3_boundaries[0]["reason_code"] == "G3_CONNECT_EXEMPT", (
        f"NC-6a: G3 must have G3_CONNECT_EXEMPT, got {g3_boundaries[0]['reason_code']}"
    )
    assert g3_boundaries[0]["verdict"] == "PASS", (
        "NC-6a: G3 must PASS with explicit exemption for connect"
    )


def test_nc6_non_connect_missing_timestamp_blocks():
    """NC-6b: Non-connect action (stock) without any timestamp BLOCKs on G3
    (G3_TIMESTAMP_MISSING_REQUIRED), not silently passes.
    """
    # Complete fields but NO timestamp
    no_ts = {
        "price": 100.0, "pe": 15.0, "pb": 2.1,
        "market_cap": 5000, "roe": 20.0,
        # deliberately no trade_date / data_timestamp
    }
    qc = {"status": "success", "completeness": 1.0, "sources": ["wind"],
          "fallback_source": None, "missing_dimensions": [], "stale_data": []}
    raw = _raw_response(qc, no_ts)

    result = mcp_server._enforce_trust_gate_or_block(
        action="stock", code="600519.SH",
        result=no_ts, source_used="wind", raw_response=raw,
        retrieved_at=_now_iso(),
    )
    envelope = json.loads(result.split("\n\n", 1)[0])

    assert envelope["_trust_gate"]["overall_verdict"] == "BLOCK", (
        "NC-6b: stock without timestamp must BLOCK (G3_TIMESTAMP_MISSING_REQUIRED)"
    )
    boundaries = envelope["_trust_gate"]["boundaries"]
    g3_boundaries = [b for b in boundaries if b["boundary_id"] == "G3"]
    assert g3_boundaries, "NC-6b: G3 boundary must be present"
    assert g3_boundaries[0]["reason_code"] == "G3_TIMESTAMP_MISSING_REQUIRED", (
        f"NC-6b: expected G3_TIMESTAMP_MISSING_REQUIRED, got {g3_boundaries[0]['reason_code']}"
    )


# ============================================================
# Integration smoke: wired path produces _trust_gate on PASS
# ============================================================

def test_integration_complete_fresh_pass():
    """Positive control: complete+fresh stock data passes gate and preserves data."""
    complete = _fresh_stock()
    qc = {"status": "success", "completeness": 1.0, "sources": ["wind"],
          "fallback_source": "tushare", "missing_dimensions": [], "stale_data": []}
    raw = _raw_response(qc, complete)

    result = mcp_server._enforce_trust_gate_or_block(
        action="stock", code="600519.SH",
        result=complete, source_used="wind", raw_response=raw,
        retrieved_at=_now_iso(),
    )
    envelope = json.loads(result.split("\n\n", 1)[0])

    assert "_trust_gate" in envelope, "positive: PASS must annotate _trust_gate"
    assert envelope["_trust_gate"]["overall_verdict"] == "PASS"
    assert "1850.5" in result, "positive: PASS must preserve provider data"
