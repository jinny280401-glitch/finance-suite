"""Trust Gate Enforcer — Phase 1a: wind_query single-tool.

Orchestrates G2 + G3 checks and produces a TrustGateDecision record.
Phase 1a active boundaries: G2 (Field Integrity) + G3 (Freshness).
Note: Contract G1 (Source Identity) is planned, not yet implemented.

Contract:
- Input: wind_query parameters + provider response
- Output: TrustGateDecision (immutable, inspectable)
- Fail-closed: any error or timeout during enforcement = BLOCK
- Non-bypass: decision record is always produced, even on error
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from trust_gate.decision import TrustGateDecision, BoundaryResult, GateVerdict
from trust_gate.boundaries.g2_field_integrity import check_g2_field_integrity
from trust_gate.boundaries.g3_freshness import check_g3_freshness


def _normalize_result(
    action: str,
    result: Any,
    source_used: str = "",
) -> dict[str, Any] | None:
    """Normalize provider result to dict format expected by Gate boundaries.

    Some providers (notably Tushare) return lists for certain actions
    (financials, peers) while the Gate expects dicts. This layer converts
    list responses to the dict shape that _extract_nested() already handles,
    without fabricating or transforming field values.

    Returns None for empty/unusable results.
    """
    if result is None:
        return None
    if isinstance(result, dict):
        return result
    if not isinstance(result, list):
        return None
    if len(result) == 0:
        return None

    # Tushare financials: list of period dicts → {"financials": [...]}
    # _extract_nested() already handles this shape (line 122-125 in g2_field_integrity.py)
    if action == "financials":
        return {"financials": result}

    # Tushare peers: list of peer dicts → {"peer_list": [...]}
    if action == "peers":
        return {"peer_list": result}

    # Generic: wrap as {"data": [...]} for other list results
    return {"data": result}


def enforce_wind_query(
    action: str,
    code: str,
    result: dict[str, Any] | None,
    source_used: str = "",
    chain: list[str] | None = None,
    retrieved_at: str | None = None,
) -> TrustGateDecision:
    """Enforce Trust Gate boundaries on a wind_query result.

    This is THE single entry point for wind_query Trust Gate enforcement.
    No wind_query response reaches LLM context without passing through here.

    Args:
        action: wind_query action (stock, financials, consensus, etc.)
        code: Stock code (e.g. "600519.SH")
        result: Provider response (dict or list), or None if all providers failed
        source_used: Which provider actually returned data
        chain: Fallback chain attempted (for evidence, not used in G1/G3)
        retrieved_at: ISO8601 timestamp of query (defaults to now)

    Returns:
        TrustGateDecision with PASS or BLOCK verdict and per-boundary details.

    Fail-closed guarantee:
        Any exception during enforcement is caught and converted to a BLOCK
        decision. The Gate never fails open.
    """
    if retrieved_at is None:
        retrieved_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Normalize provider result shape before Gate evaluation.
    # Some providers return lists (Tushare financials/peers); Gate expects dicts.
    normalized = _normalize_result(action, result, source_used)

    boundaries: list[BoundaryResult] = []

    try:
        # G2: Field Integrity (Phase 1a naming — maps to Contract G2)
        # Note: Contract G1 (Source Identity) is planned but not yet in Phase 1a
        g2 = check_g2_field_integrity(action, normalized, source_used)
        boundaries.append(g2)

        # G3: Phase-aware Freshness
        g3 = check_g3_freshness(action, normalized, source_used, retrieved_at)
        boundaries.append(g3)

    except Exception as exc:
        # Fail-closed: enforcement exception = BLOCK
        error_boundary = BoundaryResult(
            boundary_id="GATE",
            boundary_label="Trust Gate Enforcement",
            verdict=GateVerdict.BLOCK,
            reason_code="GATE_ENFORCEMENT_ERROR",
            detail=f"Trust Gate enforcement failed with exception: {exc}",
            evidence={
                "action": action,
                "code": code,
                "error": str(exc),
                "error_type": type(exc).__name__,
            },
            evaluated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
        boundaries.append(error_boundary)

    # Build decision from boundaries
    decision = TrustGateDecision.from_boundaries(
        action=action,
        code=code,
        source_used=source_used,
        retrieved_at=retrieved_at,
        boundaries=boundaries,
    )

    return decision


def format_trust_gate_envelope(
    decision: TrustGateDecision,
    original_response: str,
) -> str:
    """Embed Trust Gate decision into the MCP response envelope.

    PASS: original response passes through with _trust_gate annotation added.
    BLOCK: envelope is REBUILT from a metadata allowlist. Provider data values
           from the original envelope are NEVER retained under BLOCK.

    Format (PASS):
        {original envelope + "_trust_gate": {...}}\\n\\n{original content}

    Format (BLOCK):
        {"_qc": {safe metadata only}, "_trust_gate": {...}}\\n\\n数据不可用: <reasons>
    """
    import json

    # Parse the original response
    parts = original_response.split("\n\n", 1)
    envelope_str = parts[0]
    original_content = parts[1] if len(parts) > 1 else ""

    try:
        original_envelope = json.loads(envelope_str)
    except json.JSONDecodeError:
        original_envelope = {}

    # Inject trust gate decision
    tg_dict = decision.to_dict()

    if decision.passed:
        # PASS: original envelope + _trust_gate, content unchanged
        original_envelope["_trust_gate"] = tg_dict
        result = json.dumps(original_envelope, ensure_ascii=False)
        if original_content:
            result += "\n\n" + original_content
        return result

    # BLOCK: REBUILD envelope from metadata allowlist.
    # Explicitly DO NOT reuse original_envelope — it may contain
    # provider data values in _qc or other keys.
    original_qc = original_envelope.get("_qc") if isinstance(original_envelope.get("_qc"), dict) else {}

    # Allowlist: only safe structural metadata, NO provider data values.
    # `error` is deliberately excluded — provider error messages may contain
    # data values (e.g. "query failed for price=999.99").
    safe_qc = {}
    for key in ("status", "completeness", "sources", "fallback_source",
                "missing_dimensions", "stale_data",
                "source_chain", "source_type"):
        if key in original_qc:
            safe_qc[key] = original_qc[key]

    block_envelope = {
        "_qc": safe_qc,
        "_trust_gate": tg_dict,
    }

    result = json.dumps(block_envelope, ensure_ascii=False)

    # Block message — reason codes only, no provider data
    block_reasons = []
    for b in decision.boundaries:
        if b.verdict.value == "BLOCK":
            block_reasons.append("%s: %s" % (b.boundary_id, b.detail))
    block_msg = "数据不可用 (Trust Gate BLOCK): %s" % "; ".join(block_reasons)
    result += "\n\n" + block_msg

    return result
