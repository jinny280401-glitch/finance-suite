"""G2: Field Integrity (Phase 1a naming — maps to Contract G2).

Verifies that all critical dimensions for a given wind_query action
are present and non-empty in the provider response.

Contract mapping:
  - Contract G2 = Field Integrity = "Every requested field is present,
    no silent omission, field types correct"
  - This implementation checks field presence (not yet type/shape)

Note: Contract G1 (Source Identity) is planned but not yet implemented
in Phase 1a. The original filename g1_completeness.py was a naming error.

C findings covered: F-01. Tests: T-03, T-04.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from trust_gate.decision import BoundaryResult, GateVerdict


# Per-action critical dimensions.
# Each dimension maps to a field path in the provider response dict.
# A dimension is "present" if the field exists AND the value is not None, not [],
# not {}, not "" (empty string), not 0 (zero is valid for prices/market_cap).
CRITICAL_DIMENSIONS: dict[str, dict[str, str]] = {
    "stock": {
        "price": "price",
        "pe": "pe",
        "pb": "pb",
        "market_cap": "market_cap",
        "roe": "roe",
    },
    "financials": {
        "revenue": "revenue",
        "net_profit": "net_profit",
        "gross_margin": "gross_margin",
        "roe": "roe",
    },
    "consensus": {
        "eps_forecast": "eps_forecast",
        "target_price": "target_price",
        "rating": "rating",
    },
    "peers": {
        "peer_list": "peer_list",
    },
    "valuation": {
        "pe_percentile": "pe_percentile",
        "pb_percentile": "pb_percentile",
    },
    "shareholders": {
        "top_10_shareholders": "top_10_shareholders",
    },
    "daily_price": {
        "trade_date": "trade_date",
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
    },
    "calendar": {
        "earnings_dates": "earnings_dates",
    },
    "connect": {
        "wind": "wind",
        "tushare": "tushare",
        "joinquant": "joinquant",
        "akshare": "akshare",
    },
}

# Special: "stock" action via tushare may use alternate field names
TUSHARE_STOCK_ALIASES: dict[str, list[str]] = {
    "price": ["price", "close", "latest_price"],
    "pe": ["pe", "pe_ttm"],
    "pb": ["pb"],
    "market_cap": ["market_cap", "total_mv", "total_market_value"],
    "roe": ["roe", "roe_ttm"],
}


def _is_present(value: Any) -> bool:
    """Check if a value is meaningfully present (not null/empty)."""
    if value is None:
        return False
    if isinstance(value, (list, dict, str)) and len(value) == 0:
        return False
    return True


def _resolve_field(result: dict[str, Any], dim_key: str, aliases: list[str] | None = None) -> tuple[bool, str | None]:
    """Resolve a dimension in the result dict, trying primary key then aliases.

    Returns (present, matched_field_name).
    """
    # Try primary key first
    if dim_key in result and _is_present(result[dim_key]):
        return True, dim_key

    # Try aliases
    if aliases:
        for alias in aliases:
            if alias in result and _is_present(result[alias]):
                return True, alias

    return False, None


def _extract_nested(result: dict[str, Any], dim_key: str) -> Any:
    """Extract a possibly nested field from result.

    Handles cases like result["data"]["price"] where the provider wraps
    the actual fields one level deep.
    """
    # Direct lookup
    if dim_key in result:
        return result[dim_key]

    # One level deep (common pattern: result["data"][field])
    inner = result.get("data")
    if isinstance(inner, dict) and dim_key in inner:
        return inner[dim_key]

    # List result (e.g. financials returns a list of periods)
    if isinstance(result.get("financials"), list) and len(result["financials"]) > 0:
        latest = result["financials"][0]
        if isinstance(latest, dict) and dim_key in latest:
            return latest[dim_key]

    return None


def check_g2_field_integrity(
    action: str,
    result: dict[str, Any] | None,
    source_used: str = "",
) -> BoundaryResult:
    """Check that all critical dimensions for `action` are present in `result`.

    Args:
        action: wind_query action (stock, financials, etc.)
        result: Provider response dict (may be None if all providers failed)
        source_used: Actual provider that returned data (for alias selection)

    Returns:
        BoundaryResult with PASS if all critical dimensions present, BLOCK otherwise.
    """
    evaluated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # No result at all → BLOCK
    if not result:
        return BoundaryResult(
            boundary_id="G2",
            boundary_label="Field Integrity",
            verdict=GateVerdict.BLOCK,
            reason_code="G2_NO_RESULT",
            detail=f"No provider returned data for action={action}",
            evidence={"action": action, "result": None},
            evaluated_at=evaluated_at,
        )

    required = CRITICAL_DIMENSIONS.get(action)
    if required is None:
        # Unknown action — can't verify completeness → BLOCK (fail-closed)
        return BoundaryResult(
            boundary_id="G2",
            boundary_label="Field Integrity",
            verdict=GateVerdict.BLOCK,
            reason_code="G2_UNKNOWN_ACTION",
            detail=f"No completeness dimensions defined for action={action}",
            evidence={"action": action, "known_actions": list(CRITICAL_DIMENSIONS.keys())},
            evaluated_at=evaluated_at,
        )

    # Select aliases based on source
    aliases_map: dict[str, list[str]] = {}
    if source_used == "tushare" and action == "stock":
        aliases_map = TUSHARE_STOCK_ALIASES

    missing: list[str] = []
    present: list[str] = []
    evidence_fields: dict[str, Any] = {}

    for dim_key, dim_label in required.items():
        aliases = aliases_map.get(dim_key)
        # Try nested extraction first, then direct lookup with aliases
        value = _extract_nested(result, dim_key)
        found_field: str | None = None

        if _is_present(value):
            found_field = dim_key
        elif aliases:
            # Try aliases against both result root and nested data
            for alias in aliases:
                v = _extract_nested(result, alias)
                if _is_present(v):
                    found_field = alias
                    value = v
                    break

        if found_field:
            present.append(dim_label)
            evidence_fields[dim_label] = {"found": True, "field": found_field}
        else:
            missing.append(dim_label)
            evidence_fields[dim_label] = {"found": False}

    if missing:
        return BoundaryResult(
            boundary_id="G2",
            boundary_label="Field Integrity",
            verdict=GateVerdict.BLOCK,
            reason_code="G2_CRITICAL_DIMENSION_MISSING",
            detail=f"Action={action} missing critical dimensions: {missing}",
            evidence={
                "action": action,
                "source_used": source_used,
                "required_dimensions": list(required.values()),
                "present_dimensions": present,
                "missing_critical": missing,
                "fields": evidence_fields,
            },
            evaluated_at=evaluated_at,
        )

    return BoundaryResult(
        boundary_id="G2",
        boundary_label="Field Integrity",
        verdict=GateVerdict.PASS,
        reason_code="G2_ALL_CRITICAL_PRESENT",
        detail=f"All {len(required)} critical dimensions present for action={action}",
        evidence={
            "action": action,
            "source_used": source_used,
            "required_dimensions": list(required.values()),
            "present_dimensions": present,
            "fields": evidence_fields,
        },
        evaluated_at=evaluated_at,
    )
