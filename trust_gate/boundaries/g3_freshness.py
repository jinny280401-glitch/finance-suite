"""G3: Phase-aware Freshness.

Verifies that provider data is fresh enough for the requested action,
distinguishing data_timestamp from retrieved_at, and evaluating
market phase compatibility.

C findings covered: F-03, R-01. Tests: T-01, T-02, T-11.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any

from trust_gate.decision import BoundaryResult, GateVerdict


# Per-action max data age in seconds.
# WARNING (Finding 2, Phase 1a): These are Phase 1a defaults for wind_query only.
# They are NOT global freshness rules. Future phases must support per-action
# freshness SLA driven by config, not hardcoded. Specifically:
#   - 集合竞价 data needs minute-level freshness (not 24h)
#   - 实时行情 needs minute-level freshness (not 24h)
#   - 财报分析 can tolerate quarterly-level freshness
#   - 公司介绍 can tolerate day-level freshness
# The current stock=24h works for EOD snapshots but is too loose for
# real-time trading data. Do NOT copy-paste this table to other tools.
#
# - stock: EOD snapshot via wind_query (not intraday). 24h allows
#   yesterday's EOD. Real-time intraday requires T0 elsewhere.
# - financials: quarterly, max 120 days
# - consensus: analyst estimates, max 30 days
# - peers: comparable companies, max 7 days
# - valuation: percentile data, max 7 days
# - shareholders: quarterly filings, max 120 days
# - calendar: earnings schedule, max 30 days
# - connect: connection status, max 5 minutes
MAX_DATA_AGE_SECONDS: dict[str, int] = {
    "stock": 86400,         # 24h (EOD snapshot: today + yesterday OK, T+2 stale)
    "daily_price": 86400,   # 24h (EOD snapshot, same rule as stock)
    "financials": 10368000,  # 120 days
    "consensus": 2592000,    # 30 days
    "peers": 604800,         # 7 days
    "valuation": 604800,     # 7 days
    "shareholders": 10368000, # 120 days
    "calendar": 2592000,     # 30 days
    "connect": 300,          # 5 minutes
}

# Actions that REQUIRE a data_timestamp in the provider response.
# Without a timestamp we cannot verify freshness — BLOCK.
# These are NOT necessarily real-time/intraday actions; they are actions
# where staleness cannot be inferred from retrieved_at alone.
# - stock: EOD snapshot via wind_query (max 24h). Requires timestamp
#   because we must distinguish today's EOD from last week's.
TIMESTAMP_REQUIRED_ACTIONS = {"stock", "daily_price"}

# Known timestamp field names in provider responses
TIMESTAMP_FIELDS = [
    "data_timestamp",
    "provider_timestamp",
    "as_of",
    "trade_date",
    "date",
    "report_date",
    "update_time",
    "timestamp",
]


def _parse_timestamp(value: Any) -> datetime | None:
    """Attempt to parse a timestamp from various formats."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        return None

    # Try common formats
    formats = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%Y%m%d",
    ]
    is_date_only = False
    for fmt in formats:
        try:
            dt = datetime.strptime(value.strip(), fmt)
            if fmt in ("%Y-%m-%d", "%Y%m%d"):
                # Date-only: use end-of-day (23:59:59 local) so that
                # today's EOD data isn't penalized as "midnight age"
                is_date_only = True
                dt = dt.replace(hour=23, minute=59, second=59)
                dt = dt.replace(tzinfo=timezone(timedelta(hours=8)))
            elif "T" in fmt and "+" not in fmt and dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, AttributeError):
            continue
    return None


def _extract_data_timestamp(result: dict[str, Any]) -> datetime | None:
    """Extract the best available data timestamp from a provider response.

    Priority: data_timestamp > provider_timestamp > as_of > trade_date > date
    Also checks nested data (result["data"]["trade_date"] etc.)
    """
    # Check root level
    for field in TIMESTAMP_FIELDS:
        val = result.get(field)
        if val is not None:
            dt = _parse_timestamp(val)
            if dt:
                return dt

    # Check nested data
    inner = result.get("data")
    if isinstance(inner, dict):
        for field in TIMESTAMP_FIELDS:
            val = inner.get(field)
            if val is not None:
                dt = _parse_timestamp(val)
                if dt:
                    return dt

    # Check list result (e.g. financials[0]["报告期"])
    for list_key in ("financials", "data"):
        items = result.get(list_key)
        if isinstance(items, list) and len(items) > 0:
            first = items[0]
            if isinstance(first, dict):
                for field in TIMESTAMP_FIELDS:
                    val = first.get(field)
                    if val is not None:
                        dt = _parse_timestamp(val)
                        if dt:
                            return dt

    return None


def check_g3_freshness(
    action: str,
    result: dict[str, Any] | None,
    source_used: str = "",
    retrieved_at: str = "",
) -> BoundaryResult:
    """Check that provider data is fresh enough for the requested action.

    Args:
        action: wind_query action
        result: Provider response dict (may be None)
        source_used: Actual provider
        retrieved_at: ISO8601 when the query was made

    Returns:
        BoundaryResult with PASS if data is fresh, BLOCK if stale or timestamp missing.
    """
    evaluated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # No result → BLOCK
    if not result:
        return BoundaryResult(
            boundary_id="G3",
            boundary_label="Phase-aware Freshness",
            verdict=GateVerdict.BLOCK,
            reason_code="G3_NO_RESULT",
            detail="No provider data to evaluate freshness",
            evidence={"action": action, "result": None},
            evaluated_at=evaluated_at,
        )

    # Connect action doesn't carry time-sensitive market data
    if action == "connect":
        return BoundaryResult(
            boundary_id="G3",
            boundary_label="Phase-aware Freshness",
            verdict=GateVerdict.PASS,
            reason_code="G3_CONNECT_EXEMPT",
            detail="connect action is a status check, no data freshness requirement",
            evidence={"action": "connect"},
            evaluated_at=evaluated_at,
        )

    max_age_seconds = MAX_DATA_AGE_SECONDS.get(action)
    if max_age_seconds is None:
        # Unknown action → BLOCK (fail-closed)
        return BoundaryResult(
            boundary_id="G3",
            boundary_label="Phase-aware Freshness",
            verdict=GateVerdict.BLOCK,
            reason_code="G3_UNKNOWN_ACTION",
            detail=f"No max age defined for action={action}",
            evidence={"action": action, "known_actions": list(MAX_DATA_AGE_SECONDS.keys())},
            evaluated_at=evaluated_at,
        )

    # Extract data timestamp
    data_ts = _extract_data_timestamp(result)

    # Parse retrieved_at
    retrieved_dt: datetime | None = None
    if retrieved_at:
        retrieved_dt = _parse_timestamp(retrieved_at)

    if data_ts is None:
        # Timestamp missing → BLOCK for intraday actions, warn for others
        if action in TIMESTAMP_REQUIRED_ACTIONS:
            return BoundaryResult(
                boundary_id="G3",
                boundary_label="Phase-aware Freshness",
                verdict=GateVerdict.BLOCK,
                reason_code="G3_TIMESTAMP_MISSING_REQUIRED",
                detail=f"Action={action} requires a data timestamp but none found in response",
                evidence={
                    "action": action,
                    "source_used": source_used,
                    "retrieved_at": retrieved_at,
                    "searched_fields": TIMESTAMP_FIELDS,
                    "max_age_seconds": max_age_seconds,
                },
                evaluated_at=evaluated_at,
            )

        # For non-intraday actions, missing timestamp is a warning not a block
        # We still check if retrieved_at is reasonable
        if retrieved_dt is None:
            return BoundaryResult(
                boundary_id="G3",
                boundary_label="Phase-aware Freshness",
                verdict=GateVerdict.BLOCK,
                reason_code="G3_NO_TIMESTAMP_REFERENCE",
                detail="No data timestamp or retrieval timestamp available for freshness check",
                evidence={
                    "action": action,
                    "source_used": source_used,
                    "max_age_seconds": max_age_seconds,
                },
                evaluated_at=evaluated_at,
            )

    # Use data timestamp if available, otherwise retrieved_at
    reference_ts = data_ts or retrieved_dt
    if reference_ts is None:
        return BoundaryResult(
            boundary_id="G3",
            boundary_label="Phase-aware Freshness",
            verdict=GateVerdict.BLOCK,
            reason_code="G3_NO_TIMESTAMP_REFERENCE",
            detail="No usable timestamp for freshness calculation",
            evidence={"action": action, "source_used": source_used},
            evaluated_at=evaluated_at,
        )

    # Calculate age
    now = datetime.now(timezone.utc)
    if reference_ts.tzinfo is None:
        # Assume UTC for naive timestamps
        reference_ts = reference_ts.replace(tzinfo=timezone.utc)
    age_seconds = (now - reference_ts).total_seconds()

    # F-04: Reject future timestamps beyond a reasonable tolerance.
    # Date-only timestamps get converted to end-of-day (23:59:59), which
    # can appear "in the future" during the trading day. A timestamp up to
    # 25 hours ahead is a date-only/timezone artifact, not fabricated data.
    # Only BLOCK if the timestamp is more than 25 hours (90000s) in the future.
    if age_seconds < -90000:
        return BoundaryResult(
            boundary_id="G3",
            boundary_label="Phase-aware Freshness",
            verdict=GateVerdict.BLOCK,
            reason_code="G3_FUTURE_TIMESTAMP",
            detail=(
                f"Data timestamp {reference_ts.isoformat()} is in the future "
                f"(now={now.isoformat()}, offset={-age_seconds:.0f}s)"
            ),
            evidence={
                "action": action,
                "source_used": source_used,
                "data_timestamp": data_ts.isoformat() if data_ts else None,
                "retrieved_at": retrieved_at,
                "data_age_seconds": int(age_seconds),
                "max_age_seconds": max_age_seconds,
                "reference_timestamp": reference_ts.isoformat(),
                "now": now.isoformat(),
            },
            evaluated_at=evaluated_at,
        )

    if age_seconds > max_age_seconds:
        age_hours = age_seconds / 3600
        max_hours = max_age_seconds / 3600
        return BoundaryResult(
            boundary_id="G3",
            boundary_label="Phase-aware Freshness",
            verdict=GateVerdict.BLOCK,
            reason_code="G3_DATA_STALE",
            detail=(
                f"Data age {age_hours:.1f}h exceeds max {max_hours:.1f}h "
                f"for action={action}"
            ),
            evidence={
                "action": action,
                "source_used": source_used,
                "data_timestamp": data_ts.isoformat() if data_ts else None,
                "retrieved_at": retrieved_at,
                "data_age_seconds": int(age_seconds),
                "max_age_seconds": max_age_seconds,
                "reference_timestamp": reference_ts.isoformat(),
                "is_intraday": False,
            },
            evaluated_at=evaluated_at,
        )

    age_str = f"{age_seconds:.0f}s" if age_seconds < 3600 else f"{age_seconds/3600:.1f}h"
    return BoundaryResult(
        boundary_id="G3",
        boundary_label="Phase-aware Freshness",
        verdict=GateVerdict.PASS,
        reason_code="G3_FRESH",
        detail=f"Data age {age_str} within max for action={action}",
        evidence={
            "action": action,
            "source_used": source_used,
            "data_timestamp": data_ts.isoformat() if data_ts else None,
            "retrieved_at": retrieved_at,
            "data_age_seconds": int(age_seconds),
            "max_age_seconds": max_age_seconds,
        },
        evaluated_at=evaluated_at,
    )
